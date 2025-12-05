"""
LLM Response Cache Utility

Implements caching for LLM responses to reduce API costs and improve performance.
Uses BigQuery as storage backend following constitution principles.
"""

import hashlib
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google.cloud import bigquery


class LLMCache:
    """
    BigQuery-backed cache for LLM responses.
    
    Reduces redundant API calls for identical content analysis.
    """
    
    def __init__(self, bigquery_client: bigquery.Client):
        self.client = bigquery_client
        self.dataset_id = os.getenv("BIGQUERY_DATASET", "brightdata_jobs")
        self.table_id = "llm_analysis_cache"
        self.default_ttl = int(os.getenv("LLM_CACHE_TTL", "3600"))  # 1 hour default
        self.logger = logging.getLogger(__name__)
        
    def _generate_cache_key(
        self,
        content: str,
        prompt_template_version: str,
        model_version: str,
        analysis_type: str
    ) -> str:
        """Generate unique cache key for content + configuration."""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        key_components = f"{content_hash}:{prompt_template_version}:{model_version}:{analysis_type}"
        return hashlib.md5(key_components.encode('utf-8')).hexdigest()
        
    async def get(
        self,
        content: str,
        prompt_template_version: str,
        model_version: str,
        analysis_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result if available and not expired.
        
        Args:
            content: Document content being analyzed
            prompt_template_version: Version of prompt template
            model_version: LLM model version
            analysis_type: Type of analysis (theme_extraction, voice_analysis, etc.)
            
        Returns:
            Cached result dict or None if not found/expired
        """
        cache_key = self._generate_cache_key(content, prompt_template_version, model_version, analysis_type)
        
        query = f"""
        SELECT 
            parsed_result,
            confidence_score,
            tokens_used,
            response_time_ms,
            created_at,
            access_count
        FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE cache_key = @cache_key
          AND expires_at > CURRENT_TIMESTAMP()
          AND NOT invalidated
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cache_key", "STRING", cache_key)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                row = results[0]
                
                # Update access tracking
                await self._update_access_count(cache_key)
                
                self.logger.info(f"Cache HIT for {analysis_type} - key: {cache_key[:8]}")
                
                return {
                    "result": json.loads(row.parsed_result) if isinstance(row.parsed_result, str) else row.parsed_result,
                    "confidence_score": row.confidence_score,
                    "tokens_used": row.tokens_used,
                    "response_time_ms": row.response_time_ms,
                    "cached": True,
                    "cache_age_hours": (datetime.now() - row.created_at.replace(tzinfo=None)).total_seconds() / 3600
                }
            else:
                self.logger.info(f"Cache MISS for {analysis_type} - key: {cache_key[:8]}")
                return None
                
        except Exception as e:
            self.logger.error(f"Cache retrieval error: {e}")
            return None
            
    async def set(
        self,
        content: str,
        prompt_template_version: str,
        model_version: str,
        analysis_type: str,
        llm_response: str,
        parsed_result: Dict[str, Any],
        confidence_score: float,
        tokens_used: int,
        response_time_ms: int,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Store analysis result in cache.
        
        Args:
            content: Document content analyzed
            prompt_template_version: Version of prompt used
            model_version: LLM model version
            analysis_type: Type of analysis performed
            llm_response: Raw LLM response text
            parsed_result: Structured analysis result
            confidence_score: Analysis confidence 0.0-1.0
            tokens_used: Token count for billing
            response_time_ms: LLM response time
            ttl_seconds: Custom TTL (uses default if None)
            
        Returns:
            True if successfully cached, False otherwise
        """
        cache_key = self._generate_cache_key(content, prompt_template_version, model_version, analysis_type)
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        ttl = ttl_seconds or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Insert new cache entry
        query = f"""
        INSERT INTO `{self.client.project}.{self.dataset_id}.{self.table_id}` (
            cache_key,
            content_hash,
            prompt_template_version,
            llm_model_version,
            analysis_type,
            llm_response,
            parsed_result,
            confidence_score,
            tokens_used,
            response_time_ms,
            expires_at,
            created_at,
            last_accessed_at,
            access_count
        ) VALUES (
            @cache_key,
            @content_hash,
            @prompt_template_version,
            @llm_model_version,
            @analysis_type,
            @llm_response,
            @parsed_result,
            @confidence_score,
            @tokens_used,
            @response_time_ms,
            @expires_at,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP(),
            1
        )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cache_key", "STRING", cache_key),
                bigquery.ScalarQueryParameter("content_hash", "STRING", content_hash),
                bigquery.ScalarQueryParameter("prompt_template_version", "STRING", prompt_template_version),
                bigquery.ScalarQueryParameter("llm_model_version", "STRING", model_version),
                bigquery.ScalarQueryParameter("analysis_type", "STRING", analysis_type),
                bigquery.ScalarQueryParameter("llm_response", "STRING", llm_response),
                bigquery.ScalarQueryParameter("parsed_result", "JSON", json.dumps(parsed_result)),
                bigquery.ScalarQueryParameter("confidence_score", "FLOAT64", confidence_score),
                bigquery.ScalarQueryParameter("tokens_used", "INT64", tokens_used),
                bigquery.ScalarQueryParameter("response_time_ms", "INT64", response_time_ms),
                bigquery.ScalarQueryParameter("expires_at", "TIMESTAMP", expires_at)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()  # Wait for completion
            
            self.logger.info(f"Cached {analysis_type} result - key: {cache_key[:8]} - TTL: {ttl}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache storage error: {e}")
            return False
            
    async def _update_access_count(self, cache_key: str) -> None:
        """Update access tracking for cache entry."""
        query = f"""
        UPDATE `{self.client.project}.{self.dataset_id}.{self.table_id}`
        SET 
            access_count = access_count + 1,
            last_accessed_at = CURRENT_TIMESTAMP()
        WHERE cache_key = @cache_key
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cache_key", "STRING", cache_key)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
        except Exception as e:
            self.logger.warning(f"Failed to update cache access count: {e}")
            
    async def invalidate_by_content(self, content: str) -> int:
        """
        Invalidate all cache entries for specific content.
        
        Args:
            content: Document content to invalidate
            
        Returns:
            Number of entries invalidated
        """
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        query = f"""
        UPDATE `{self.client.project}.{self.dataset_id}.{self.table_id}`
        SET 
            invalidated = TRUE,
            invalidation_reason = 'content_updated'
        WHERE content_hash = @content_hash AND NOT invalidated
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("content_hash", "STRING", content_hash)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            result = query_job.result()
            
            # Get count of updated rows
            count_query = f"SELECT {query_job.num_dml_affected_rows} as affected_rows"
            count_job = self.client.query(count_query)
            affected = list(count_job.result())[0].affected_rows
            
            self.logger.info(f"Invalidated {affected} cache entries for content hash {content_hash[:8]}")
            return affected
            
        except Exception as e:
            self.logger.error(f"Cache invalidation error: {e}")
            return 0
            
    async def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        query = f"""
        DELETE FROM `{self.client.project}.{self.dataset_id}.{self.table_id}`
        WHERE expires_at < CURRENT_TIMESTAMP() OR invalidated = TRUE
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()
            
            affected = query_job.num_dml_affected_rows
            self.logger.info(f"Cleaned up {affected} expired cache entries")
            return affected
            
        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")
            return 0