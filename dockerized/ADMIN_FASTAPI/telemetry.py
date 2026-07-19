#!/usr/bin/env python3
# Author: skondla@me.com
# Purpose: Observability wiring — Prometheus /metrics, OpenTelemetry tracing
#          (OTLP), and structured JSON logging. Every integration is optional
#          and env-gated so the app runs identically with none of them:
#            ENABLE_METRICS=0                disables the /metrics endpoint
#            OTEL_EXPORTER_OTLP_ENDPOINT     enables tracing when set
#            LOG_FORMAT=json                 switches to JSON log lines
# -*- coding: utf-8 -*-

import json
import logging
import os

logger = logging.getLogger("telemetry")


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def configure_logging() -> None:
    """Structured JSON logs when LOG_FORMAT=json (for Loki/CloudWatch parsing)."""
    if os.environ.get("LOG_FORMAT", "").lower() != "json":
        return
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())


def configure_metrics(app) -> None:
    """Expose Prometheus metrics at /metrics (scraped by the Prometheus
    operator via the ServiceMonitor in kubernetes/observability/)."""
    if os.environ.get("ENABLE_METRICS", "1") == "0":
        return
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
    except ImportError:
        logger.info("prometheus-fastapi-instrumentator not installed — /metrics disabled")
        return
    Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/metrics"],
    ).instrument(app).expose(app, include_in_schema=False)
    logger.info("Prometheus metrics exposed at /metrics")


def configure_tracing(app, engine=None) -> None:
    """OpenTelemetry tracing via OTLP/HTTP. Activated only when the standard
    OTEL_EXPORTER_OTLP_ENDPOINT env var is set (e.g. an in-cluster collector)."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        logger.warning("OTEL_EXPORTER_OTLP_ENDPOINT set but opentelemetry "
                       "packages missing — tracing disabled")
        return

    service_name = os.environ.get("OTEL_SERVICE_NAME", "fastapi-admin-app")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider,
                                       excluded_urls="/metrics,/healthz")

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument(tracer_provider=provider)
    except ImportError:
        pass
    if engine is not None:
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=provider)
        except ImportError:
            pass
    logger.info("OpenTelemetry tracing enabled → %s (service=%s)", endpoint, service_name)


def configure_telemetry(app, engine=None) -> None:
    configure_logging()
    configure_metrics(app)
    configure_tracing(app, engine)
