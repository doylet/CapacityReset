"""
API Call Tracking Utility for LLM Integration

Tracks API usage, costs, and performance metrics
for Vertex AI calls to enable monitoring and optimization.
"""

import logging
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from collections import defaultdict


class BigQueryRepositoryProtocol(Protocol):
    """Protocol for BigQuery repository interface."""
    project_id: str
    dataset_id: str
    
    def execute_query(self, query: str, parameters: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        ...


@dataclass
class APICallMetrics:
    """Metrics for a single API call."""
    model_used: str
    tokens_input: int
    tokens_output: int
    tokens_total: int
    cost_estimate: float
    latency_ms: int
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class APICallRecord:
    """Complete record of an API call for persistence."""
    call_id: str
    timestamp: datetime
    service: str
    operation: str
    metrics: APICallMetrics
    context: Dict[str, Any]


class APICallTracker:
    """
    Tracks LLM API calls for cost monitoring and performance analysis.
    
    Provides contextual tracking with automatic metrics collection
    and storage for analysis and alerting.
    """
    
    def __init__(self, bigquery_repo: BigQueryRepositoryProtocol):
        self.bigquery_repo = bigquery_repo
        self.logger = logging.getLogger(__name__)
        
        # In-memory metrics for quick access
        self._session_metrics = defaultdict(list)
        self._cost_totals = defaultdict(float)
        
        # Pricing configuration (per 1000 tokens)
        self.pricing_config = {
            "gemini-1.5-pro": {
                "input_cost_per_1k": 0.0025,    # $2.50 per 1M input tokens
                "output_cost_per_1k": 0.01      # $10.00 per 1M output tokens
            },
            "gemini-1.5-flash": {
                "input_cost_per_1k": 0.000125,  # $0.125 per 1M input tokens
                "output_cost_per_1k": 0.0005    # $0.50 per 1M output tokens
            },
            "gemini-1.0-pro": {
                "input_cost_per_1k": 0.0005,    # $0.50 per 1M input tokens
                "output_cost_per_1k": 0.0015    # $1.50 per 1M output tokens
            }
        }
        
    @contextmanager
    def track_call(self, service: str, operation: str, model: str, 
                   context: Dict[str, Any] = None):
        """
        Context manager for tracking API calls.
        
        Args:
            service: Service name (e.g., "vertex_ai")
            operation: Operation type (e.g., "theme_analysis")
            model: Model name used for the call
            context: Additional context for the call
            
        Yields:
            Tracker object for collecting metrics
        """
        call_id = f"{service}_{operation}_{int(time.time() * 1000)}"
        start_time = time.time()
        context = context or {}
        
        # Initialize tracking state
        tracker_state = {
            "call_id": call_id,
            "service": service,
            "operation": operation,
            "model": model,
            "context": context,
            "start_time": start_time,
            "tokens_input": 0,
            "tokens_output": 0,
            "success": False,
            "error_type": None,
            "error_message": None
        }
        
        try:
            self.logger.info(f"Starting API call: {call_id}")
            yield self._create_call_tracker(tracker_state)
            
            # Mark as successful if no exception
            tracker_state["success"] = True
            
        except Exception as e:
            # Record error details
            tracker_state["success"] = False
            tracker_state["error_type"] = type(e).__name__
            tracker_state["error_message"] = str(e)
            self.logger.error(f"API call failed: {call_id} - {e}")
            raise
            
        finally:
            # Calculate final metrics
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            
            # Create metrics record
            metrics = APICallMetrics(
                model_used=tracker_state["model"],
                tokens_input=tracker_state["tokens_input"],
                tokens_output=tracker_state["tokens_output"],
                tokens_total=tracker_state["tokens_input"] + tracker_state["tokens_output"],
                cost_estimate=self._calculate_cost(
                    tracker_state["model"],
                    tracker_state["tokens_input"],
                    tracker_state["tokens_output"]
                ),
                latency_ms=latency_ms,
                success=tracker_state["success"],
                error_type=tracker_state["error_type"],
                error_message=tracker_state["error_message"]
            )
            
            # Create full record
            record = APICallRecord(
                call_id=call_id,
                timestamp=datetime.now(timezone.utc),
                service=service,
                operation=operation,
                metrics=metrics,
                context=context
            )
            
            # Store metrics
            self._record_call(record)
            
            # Log completion
            if tracker_state["success"]:
                self.logger.info(f"API call completed: {call_id} - {latency_ms}ms - ${metrics.cost_estimate:.4f}")
            else:
                self.logger.error(f"API call failed: {call_id} - {tracker_state['error_type']}")
                
    def _create_call_tracker(self, state: Dict[str, Any]):
        """Create a call tracker object for the context manager."""
        class CallTracker:
            def __init__(self, tracking_state):
                self.state = tracking_state
                
            def record_tokens(self, input_tokens: int, output_tokens: int):
                """Record token usage for the call."""
                self.state["tokens_input"] = input_tokens
                self.state["tokens_output"] = output_tokens
                
            def add_context(self, key: str, value: Any):
                """Add additional context during the call."""
                self.state["context"][key] = value
                
        return CallTracker(state)
        
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for token usage."""
        if model not in self.pricing_config:
            # Default to most expensive model for safety
            model = "gemini-1.5-pro"
            
        config = self.pricing_config[model]
        
        input_cost = (input_tokens / 1000) * config["input_cost_per_1k"]
        output_cost = (output_tokens / 1000) * config["output_cost_per_1k"]
        
        return input_cost + output_cost
        
    def _record_call(self, record: APICallRecord):
        """Store API call record for analysis."""
        try:
            # Add to session metrics
            self._session_metrics[record.operation].append(record)
            self._cost_totals[record.operation] += record.metrics.cost_estimate
            
            # Persist to BigQuery (async)
            self._store_to_bigquery(record)
            
        except Exception as e:
            self.logger.error(f"Failed to record API call: {e}")
            
    def _store_to_bigquery(self, record: APICallRecord):
        """Store API call record in BigQuery."""
        try:
            query = """
            INSERT INTO `{project}.{dataset}.api_call_tracking` (
                call_id,
                timestamp,
                service,
                operation,
                model_used,
                tokens_input,
                tokens_output,
                tokens_total,
                cost_estimate,
                latency_ms,
                success,
                error_type,
                error_message,
                context_data
            ) VALUES (
                @call_id,
                @timestamp,
                @service,
                @operation,
                @model_used,
                @tokens_input,
                @tokens_output,
                @tokens_total,
                @cost_estimate,
                @latency_ms,
                @success,
                @error_type,
                @error_message,
                @context_data
            )
            """.format(
                project=self.bigquery_repo.project_id,
                dataset=self.bigquery_repo.dataset_id
            )
            
            self.bigquery_repo.execute_query(
                query,
                parameters=[
                    {"name": "call_id", "parameterType": {"type": "STRING"}, "parameterValue": {"value": record.call_id}},
                    {"name": "timestamp", "parameterType": {"type": "TIMESTAMP"}, "parameterValue": {"value": record.timestamp.isoformat()}},
                    {"name": "service", "parameterType": {"type": "STRING"}, "parameterValue": {"value": record.service}},
                    {"name": "operation", "parameterType": {"type": "STRING"}, "parameterValue": {"value": record.operation}},
                    {"name": "model_used", "parameterType": {"type": "STRING"}, "parameterValue": {"value": record.metrics.model_used}},
                    {"name": "tokens_input", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(record.metrics.tokens_input)}},
                    {"name": "tokens_output", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(record.metrics.tokens_output)}},
                    {"name": "tokens_total", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(record.metrics.tokens_total)}},
                    {"name": "cost_estimate", "parameterType": {"type": "FLOAT64"}, "parameterValue": {"value": str(record.metrics.cost_estimate)}},
                    {"name": "latency_ms", "parameterType": {"type": "INT64"}, "parameterValue": {"value": str(record.metrics.latency_ms)}},
                    {"name": "success", "parameterType": {"type": "BOOL"}, "parameterValue": {"value": str(record.metrics.success).lower()}},
                    {"name": "error_type", "parameterType": {"type": "STRING"}, "parameterValue": {"value": record.metrics.error_type or ""}},
                    {"name": "error_message", "parameterType": {"type": "STRING"}, "parameterValue": {"value": record.metrics.error_message or ""}},
                    {"name": "context_data", "parameterType": {"type": "STRING"}, "parameterValue": {"value": json.dumps(record.context)}}
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store API call to BigQuery: {e}")
            
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of API calls for current session."""
        summary = {
            "total_calls": sum(len(calls) for calls in self._session_metrics.values()),
            "total_cost": sum(self._cost_totals.values()),
            "by_operation": {},
            "error_rate": 0.0
        }
        
        total_calls = 0
        failed_calls = 0
        
        for operation, calls in self._session_metrics.items():
            op_calls = len(calls)
            op_failures = sum(1 for call in calls if not call.metrics.success)
            op_cost = self._cost_totals[operation]
            
            total_calls += op_calls
            failed_calls += op_failures
            
            summary["by_operation"][operation] = {
                "calls": op_calls,
                "failures": op_failures,
                "success_rate": ((op_calls - op_failures) / op_calls) if op_calls > 0 else 0.0,
                "total_cost": op_cost,
                "avg_cost": op_cost / op_calls if op_calls > 0 else 0.0
            }
            
        if total_calls > 0:
            summary["error_rate"] = failed_calls / total_calls
            
        return summary
        
    def get_cost_breakdown(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed cost breakdown by model and operation."""
        breakdown = {
            "by_model": defaultdict(lambda: {"calls": 0, "cost": 0.0, "tokens": 0}),
            "by_operation": defaultdict(lambda: {"calls": 0, "cost": 0.0, "tokens": 0}),
            "total_cost": 0.0,
            "total_tokens": 0
        }
        
        for op, calls in self._session_metrics.items():
            if operation and op != operation:
                continue
                
            for call in calls:
                model = call.metrics.model_used
                cost = call.metrics.cost_estimate
                tokens = call.metrics.tokens_total
                
                # By model
                breakdown["by_model"][model]["calls"] += 1
                breakdown["by_model"][model]["cost"] += cost
                breakdown["by_model"][model]["tokens"] += tokens
                
                # By operation
                breakdown["by_operation"][op]["calls"] += 1
                breakdown["by_operation"][op]["cost"] += cost
                breakdown["by_operation"][op]["tokens"] += tokens
                
                # Totals
                breakdown["total_cost"] += cost
                breakdown["total_tokens"] += tokens
                
        # Convert defaultdicts to regular dicts
        breakdown["by_model"] = dict(breakdown["by_model"])
        breakdown["by_operation"] = dict(breakdown["by_operation"])
        
        return breakdown
        
    def check_cost_threshold(self, threshold: float = 1.0) -> Dict[str, Any]:
        """Check if costs exceed threshold and return alert data."""
        total_cost = sum(self._cost_totals.values())
        
        alert = {
            "threshold_exceeded": total_cost > threshold,
            "current_cost": total_cost,
            "threshold": threshold,
            "percentage": (total_cost / threshold) * 100 if threshold > 0 else 0,
            "operations": []
        }
        
        # Get per-operation costs that are significant
        for operation, cost in self._cost_totals.items():
            if cost > threshold * 0.1:  # 10% of threshold
                alert["operations"].append({
                    "operation": operation,
                    "cost": cost,
                    "calls": len(self._session_metrics[operation])
                })
                
        return alert
        
    def reset_session_metrics(self):
        """Reset session tracking (useful for testing or periodic cleanup)."""
        self._session_metrics.clear()
        self._cost_totals.clear()
        self.logger.info("Session metrics reset")