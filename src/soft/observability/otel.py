"""OpenTelemetry observability setup and instrumentation."""

import os
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from functools import wraps

from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

# Global tracer and meter
tracer = None
meter = None

def init_observability(service_name: str = "smartlinks-autopilot"):
    """Initialize OpenTelemetry observability."""
    global tracer, meter
    
    # Resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Initialize tracing
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    
    # OTLP exporter for traces (optional)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Initialize metrics with Prometheus exporter
    prometheus_reader = PrometheusMetricReader()
    metric_provider = MeterProvider(
        resource=resource,
        metric_readers=[prometheus_reader]
    )
    metrics.set_meter_provider(metric_provider)
    
    # Get tracer and meter
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)
    
    return tracer, meter

def instrument_fastapi(app):
    """Instrument FastAPI application."""
    FastAPIInstrumentor.instrument_app(app)

def instrument_sqlalchemy(engine):
    """Instrument SQLAlchemy engine."""
    SQLAlchemyInstrumentor().instrument(engine=engine)

class SmartLinksMetrics:
    """SmartLinks-specific metrics."""
    
    def __init__(self, meter):
        self.meter = meter
        
        # Counters
        self.actions_counter = meter.create_counter(
            "autopilot_actions_total",
            description="Total number of autopilot actions",
            unit="1"
        )
        
        self.rcp_evaluations_counter = meter.create_counter(
            "rcp_evaluations_total",
            description="Total number of RCP evaluations",
            unit="1"
        )
        
        self.policy_rollbacks_counter = meter.create_counter(
            "policy_rollbacks_total",
            description="Total number of policy rollbacks",
            unit="1"
        )
        
        # Histograms
        self.run_duration_histogram = meter.create_histogram(
            "autopilot_run_duration_ms",
            description="Duration of autopilot runs",
            unit="ms"
        )
        
        self.rcp_evaluation_duration_histogram = meter.create_histogram(
            "rcp_evaluation_duration_ms",
            description="Duration of RCP evaluations",
            unit="ms"
        )
        
        # Gauges
        self.risk_cost_gauge = meter.create_up_down_counter(
            "autopilot_risk_cost",
            description="Current risk cost",
            unit="1"
        )
        
        self.active_policies_gauge = meter.create_up_down_counter(
            "rcp_active_policies",
            description="Number of active RCP policies",
            unit="1"
        )
    
    def record_action(self, state: str, algo_key: str, action_type: str):
        """Record an action with state (allowed/modified/blocked)."""
        self.actions_counter.add(1, {
            "state": state,
            "algo_key": algo_key,
            "action_type": action_type
        })
    
    def record_rcp_evaluation(self, algo_key: str, policies_applied: int, 
                             blocked_count: int, duration_ms: float):
        """Record RCP evaluation metrics."""
        self.rcp_evaluations_counter.add(1, {
            "algo_key": algo_key,
            "policies_applied": str(policies_applied)
        })
        
        self.rcp_evaluation_duration_histogram.record(duration_ms, {
            "algo_key": algo_key
        })
    
    def record_run_duration(self, algo_key: str, duration_ms: float, success: bool):
        """Record algorithm run duration."""
        self.run_duration_histogram.record(duration_ms, {
            "algo_key": algo_key,
            "success": str(success)
        })
    
    def record_policy_rollback(self, policy_id: str, reason: str):
        """Record policy rollback."""
        self.policy_rollbacks_counter.add(1, {
            "policy_id": policy_id,
            "reason": reason
        })
    
    def update_risk_cost(self, algo_key: str, risk_cost: float):
        """Update current risk cost."""
        self.risk_cost_gauge.add(risk_cost, {"algo_key": algo_key})
    
    def update_active_policies(self, count: int):
        """Update active policies count."""
        self.active_policies_gauge.add(count)

# Global metrics instance
smartlinks_metrics = None

def get_metrics() -> SmartLinksMetrics:
    """Get SmartLinks metrics instance."""
    global smartlinks_metrics
    if smartlinks_metrics is None and meter is not None:
        smartlinks_metrics = SmartLinksMetrics(meter)
    return smartlinks_metrics

@contextmanager
def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Context manager for creating spans."""
    if tracer is None:
        yield None
        return
    
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        yield span

def trace_function(span_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator to trace function execution."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"
            with trace_span(name, attributes) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    if span:
                        span.set_attribute("success", "true")
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("success", "false")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    if span:
                        span.set_attribute("duration_ms", duration_ms)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = span_name or f"{func.__module__}.{func.__name__}"
            with trace_span(name, attributes) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    if span:
                        span.set_attribute("success", "true")
                    return result
                except Exception as e:
                    if span:
                        span.set_attribute("success", "false")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    if span:
                        span.set_attribute("duration_ms", duration_ms)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class TracedRCPEvaluator:
    """RCP Evaluator with tracing instrumentation."""
    
    def __init__(self, base_evaluator):
        self.base_evaluator = base_evaluator
        self.metrics = get_metrics()
    
    @trace_function("rcp.evaluate")
    async def evaluate_action_list(self, actions, context):
        """Evaluate actions with tracing."""
        start_time = time.time()
        
        with trace_span("rcp.evaluate", {
            "actions_count": len(actions),
            "algo_key": context.get("algo_key", "unknown")
        }) as span:
            
            # Get applicable policies
            policies = await self._get_applicable_policies(context)
            if span:
                span.set_attribute("policies_applied", len(policies))
            
            # Evaluate
            result = await self.base_evaluator.evaluate_action_list(actions, context)
            
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            algo_key = context.get("algo_key", "unknown")
            
            if self.metrics:
                self.metrics.record_rcp_evaluation(
                    algo_key=algo_key,
                    policies_applied=len(policies),
                    blocked_count=len(result.blocked),
                    duration_ms=duration_ms
                )
                
                # Record individual actions
                for action in result.allowed:
                    self.metrics.record_action("allowed", algo_key, action.action_type)
                for action in result.modified:
                    self.metrics.record_action("modified", algo_key, action.action_type)
                for action in result.blocked:
                    self.metrics.record_action("blocked", algo_key, action.action_type)
                
                # Update risk cost
                self.metrics.update_risk_cost(algo_key, result.risk_cost)
            
            if span:
                span.set_attribute("allowed_count", len(result.allowed))
                span.set_attribute("modified_count", len(result.modified))
                span.set_attribute("blocked_count", len(result.blocked))
                span.set_attribute("risk_cost", result.risk_cost)
            
            return result
    
    async def _get_applicable_policies(self, context):
        """Get applicable policies (mock for now)."""
        return []  # Would call actual policy repository

class TracedAlgorithmRunner:
    """Algorithm runner with tracing instrumentation."""
    
    def __init__(self, base_runner):
        self.base_runner = base_runner
        self.metrics = get_metrics()
    
    @trace_function("algo.run")
    async def run_algorithm(self, algo_key: str, context: Dict[str, Any]):
        """Run algorithm with tracing."""
        start_time = time.time()
        success = False
        
        with trace_span("algo.run", {
            "algo_key": algo_key,
            "settings_version": context.get("settings_version", "unknown")
        }) as span:
            
            try:
                # Run algorithm
                result = await self.base_runner.run_algorithm(algo_key, context)
                success = True
                
                if span:
                    span.set_attribute("actions_generated", len(result.get("actions", [])))
                
                return result
                
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                if self.metrics:
                    self.metrics.record_run_duration(algo_key, duration_ms, success)
                
                if span:
                    span.set_attribute("duration_ms", duration_ms)
                    span.set_attribute("success", str(success))

def create_dashboard_links():
    """Create links to observability dashboards."""
    base_url = os.getenv("GRAFANA_BASE_URL", "http://localhost:3000")
    
    return {
        "grafana": f"{base_url}/d/smartlinks-overview/smartlinks-overview",
        "metrics": f"{base_url}/d/smartlinks-metrics/smartlinks-metrics",
        "traces": f"{base_url}/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Tempo%22,%7B%7D%5D",
        "prometheus": "http://localhost:9090/targets"
    }
