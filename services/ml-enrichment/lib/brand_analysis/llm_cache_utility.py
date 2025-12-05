"""
Cache Utility for LLM Analysis Results

Provides intelligent caching of analysis results to reduce costs
and improve response times per constitution principles.
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Protocol
from dataclasses import asdict

from ..domain.entities import LLMAnalysisResult, APICall


class BigQueryRepositoryProtocol(Protocol):
    """Protocol for BigQuery repository interface."""
    project_id: str
    dataset_id: str
    
    def execute_query(self, query: str, parameters: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        ...


class LLMCacheUtility:
    """
    Intelligent caching for LLM analysis results.
    
    Provides cache-first strategy with TTL management and
    invalidation support for cost optimization.
    """
    
    def __init__(self, bigquery_repo: BigQueryRepositoryProtocol, default_ttl_hours: int = 24):
        self.bigquery_repo = bigquery_repo
        self.default_ttl_hours = default_ttl_hours
        self.logger = logging.getLogger(__name__)
        
        # Cache configuration
        self.cache_config = {
            "theme_analysis": {"ttl_hours": 48, "version": "1.0"},
            "voice_analysis": {"ttl_hours": 72, "version": "1.0"}, 
            "narrative_analysis": {"ttl_hours": 168, "version": "1.0"}  # 1 week
        }
        
    def get_cached_result(self, content_hash: str, analysis_type: str) -> Optional[LLMAnalysisResult]:
        """
        Retrieve cached analysis result if valid.
        
        Args:
            content_hash: SHA-256 hash of input content
            analysis_type: Type of analysis (theme_analysis, voice_analysis, narrative_analysis)
            
        Returns:
            Cached result if found and valid, None otherwise
        """
        try:
            # Query cache table
            query = """
            SELECT 
                content_hash,
                analysis_type,
                result_data,
                created_at,
                ttl_hours,
                version
            FROM `{project}.{dataset}.llm_analysis_cache`
            WHERE content_hash = @content_hash 
                AND analysis_type = @analysis_type
                AND created_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ttl_hours HOUR)
                AND version = @version
            ORDER BY created_at DESC
            LIMIT 1
            """.format(
                project=self.bigquery_repo.project_id,
                dataset=self.bigquery_repo.dataset_id
            )
            
            version = self.cache_config.get(analysis_type, {}).get("version", "1.0")
            
            results = self.bigquery_repo.execute_query(
                query,
                parameters=[
                    {"name": "content_hash", "parameterType": {"type": "STRING"}, "parameterValue": {"value": content_hash}},
                    {"name": "analysis_type", "parameterType": {"type": "STRING"}, "parameterValue": {"value": analysis_type}},
                    {"name": "version", "parameterType": {"type": "STRING"}, "parameterValue": {"value": version}}
                ]
            )
            
            if results:
                result_data = json.loads(results[0]["result_data"])
                
                # Reconstruct LLMAnalysisResult
                cached_result = self._deserialize_analysis_result(result_data)
                
                self.logger.info(f"Cache hit for {analysis_type}: {content_hash[:8]}")
                return cached_result
                
            return None
            
        except Exception as e:
            self.logger.error(f"Cache retrieval error for {analysis_type}: {e}")
            return None
            
    def cache_result(self, content_hash: str, analysis_type: str, result: LLMAnalysisResult, 
                    api_call: APICall) -> bool:
        """
        Cache analysis result with metadata.
        
        Args:
            content_hash: SHA-256 hash of input content
            analysis_type: Type of analysis performed
            result: Analysis result to cache
            api_call: API call metadata for cost tracking
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            config = self.cache_config.get(analysis_type, {})
            ttl_hours = config.get("ttl_hours", self.default_ttl_hours)
            version = config.get("version", "1.0")
            
            # Serialize result data
            result_data = self._serialize_analysis_result(result)
            
            # Insert into cache table
            query = """
            INSERT INTO `{project}.{dataset}.llm_analysis_cache` (
                content_hash,
                analysis_type,
                result_data,
                created_at,
                ttl_hours,
                version,
                model_used,
                tokens_used,
                cost_estimate
            ) VALUES (
                @content_hash,
                @analysis_type,
                @result_data,
                CURRENT_TIMESTAMP(),
                @ttl_hours,
                @version,
                @model_used,
                @tokens_used,
                @cost_estimate
            )
            """.format(
                project=self.bigquery_repo.project_id,
                dataset=self.bigquery_repo.dataset_id
            )
            
            self.bigquery_repo.execute_query(
                query,
                parameters=[
                    {"name": "content_hash", "parameterType": {"type": "STRING"}, "parameterValue": {"value": content_hash}},
                    {"name": "analysis_type", "parameterType": {"type": "STRING"}, "parameterValue": {"value": analysis_type}},
                    {"name": "result_data", "parameterType": {"type": "STRING"}, "parameterValue": {"value": json.dumps(result_data)}},
                    {"name": "ttl_hours", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(ttl_hours)}},
                    {"name": "version", "parameterType": {"type": "STRING"}, "parameterValue": {"value": version}},
                    {"name": "model_used", "parameterType": {"type": "STRING"}, "parameterValue": {"value": api_call.model_used}},
                    {"name": "tokens_used", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(api_call.tokens_used)}},
                    {"name": "cost_estimate", "parameterType": {"type": "FLOAT64"}, "parameterValue": {"value": str(api_call.cost_estimate)}}
                ]
            )
            
            self.logger.info(f"Cached {analysis_type} result: {content_hash[:8]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache storage error for {analysis_type}: {e}")
            return False
            
    def invalidate_cache(self, content_hash: Optional[str] = None, 
                        analysis_type: Optional[str] = None) -> int:
        """
        Invalidate cached results by hash or type.
        
        Args:
            content_hash: Specific content hash to invalidate (optional)
            analysis_type: Analysis type to invalidate (optional)
            
        Returns:
            Number of records invalidated
        """
        try:
            where_conditions = ["created_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)"]  # Default cleanup
            parameters = []
            
            if content_hash:
                where_conditions.append("content_hash = @content_hash")
                parameters.append({
                    "name": "content_hash", 
                    "parameterType": {"type": "STRING"}, 
                    "parameterValue": {"value": content_hash}
                })
                
            if analysis_type:
                where_conditions.append("analysis_type = @analysis_type")
                parameters.append({
                    "name": "analysis_type", 
                    "parameterType": {"type": "STRING"}, 
                    "parameterValue": {"value": analysis_type}
                })
                
            query = """
            DELETE FROM `{project}.{dataset}.llm_analysis_cache`
            WHERE {where_clause}
            """.format(
                project=self.bigquery_repo.project_id,
                dataset=self.bigquery_repo.dataset_id,
                where_clause=" OR ".join(where_conditions)
            )
            
            result = self.bigquery_repo.execute_query(query, parameters=parameters)
            
            # Get affected rows count (would need to be tracked differently in actual implementation)
            affected_rows = 1 if result is not None else 0
            
            self.logger.info(f"Invalidated {affected_rows} cache entries")
            return affected_rows
            
        except Exception as e:
            self.logger.error(f"Cache invalidation error: {e}")
            return 0
            
    def cleanup_expired_cache(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of records cleaned up
        """
        try:
            query = """
            DELETE FROM `{project}.{dataset}.llm_analysis_cache`
            WHERE created_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL ttl_hours HOUR)
            """.format(
                project=self.bigquery_repo.project_id,
                dataset=self.bigquery_repo.dataset_id
            )
            
            self.bigquery_repo.execute_query(query)
            
            self.logger.info("Cleaned up expired cache entries")
            return 1  # Simplified return
            
        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")
            return 0
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache usage statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            query = """
            SELECT 
                analysis_type,
                COUNT(*) as total_entries,
                SUM(tokens_used) as total_tokens,
                SUM(cost_estimate) as total_cost,
                AVG(cost_estimate) as avg_cost,
                MIN(created_at) as oldest_entry,
                MAX(created_at) as newest_entry
            FROM `{project}.{dataset}.llm_analysis_cache`
            WHERE created_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            GROUP BY analysis_type
            ORDER BY total_entries DESC
            """.format(
                project=self.bigquery_repo.project_id,
                dataset=self.bigquery_repo.dataset_id
            )
            
            results = self.bigquery_repo.execute_query(query)
            
            stats = {
                "total_types": len(results) if results else 0,
                "by_type": results if results else [],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Cache stats error: {e}")
            return {"error": str(e), "generated_at": datetime.utcnow().isoformat()}
            
    def generate_content_hash(self, content: str, analysis_params: Dict[str, Any] = None) -> str:
        """
        Generate deterministic hash for content and parameters.
        
        Args:
            content: Input content
            analysis_params: Additional parameters affecting analysis
            
        Returns:
            SHA-256 hash string
        """
        # Create composite hash input
        hash_input = content
        
        if analysis_params:
            # Sort parameters for consistent hashing
            sorted_params = json.dumps(analysis_params, sort_keys=True)
            hash_input += sorted_params
            
        # Generate hash
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
    def _serialize_analysis_result(self, result: LLMAnalysisResult) -> Dict[str, Any]:
        """Serialize LLMAnalysisResult to dictionary."""
        return {
            "themes": [asdict(theme) for theme in result.themes] if result.themes else [],
            "voice_characteristics": asdict(result.voice_characteristics) if result.voice_characteristics else None,
            "narrative_arc": asdict(result.narrative_arc) if result.narrative_arc else None,
            "overall_confidence": result.overall_confidence,
            "analysis_metadata": result.analysis_metadata,
            "fallback_reason": result.fallback_reason
        }
        
    def _deserialize_analysis_result(self, data: Dict[str, Any]) -> LLMAnalysisResult:
        """Deserialize dictionary to LLMAnalysisResult."""
        from ...domain.entities import LLMThemeResult, LLMVoiceCharacteristics, LLMNarrativeArc
        
        # Reconstruct themes
        themes = []
        if data.get("themes"):
            themes = [LLMThemeResult(**theme_data) for theme_data in data["themes"]]
            
        # Reconstruct voice characteristics
        voice_characteristics = None
        if data.get("voice_characteristics"):
            voice_characteristics = LLMVoiceCharacteristics(**data["voice_characteristics"])
            
        # Reconstruct narrative arc
        narrative_arc = None
        if data.get("narrative_arc"):
            narrative_arc = LLMNarrativeArc(**data["narrative_arc"])
            
        return LLMAnalysisResult(
            themes=themes,
            voice_characteristics=voice_characteristics,
            narrative_arc=narrative_arc,
            overall_confidence=data.get("overall_confidence", 0.0),
            analysis_metadata=data.get("analysis_metadata", {}),
            fallback_reason=data.get("fallback_reason")
        )