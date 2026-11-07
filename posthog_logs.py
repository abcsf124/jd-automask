"""Isolated OpenTelemetry log export for PostHog operational records."""

import atexit
import logging
import os
import sys


posthog_log_logger = logging.getLogger("posthog.operational")
posthog_log_logger.setLevel(logging.INFO)
posthog_log_logger.propagate = False
posthog_log_logger.addHandler(logging.NullHandler())


def _warn_missing_configuration(variable_name):
    print(
        "WARNING: {0} variable required by PostHog is missing or un-configured, "
        "this causes events to be silently missed. This error stops appearing "
        "once {0} is configured".format(variable_name),
        file=sys.stderr,
    )


def _shutdown_logger_provider(logger_provider):
    try:
        logger_provider.shutdown(timeout_millis=3000)
    except Exception:
        pass


def _initialize_posthog_logs():
    project_token = os.getenv("POSTHOG_PROJECT_TOKEN")
    host = os.getenv("POSTHOG_HOST")

    if not project_token:
        _warn_missing_configuration("POSTHOG_PROJECT_TOKEN")
        return
    if not host:
        _warn_missing_configuration("POSTHOG_HOST")
        return

    try:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    except ImportError:
        print(
            "WARNING: OpenTelemetry packages required by PostHog log capture are "
            "not installed; PostHog operational logs will not be exported",
            file=sys.stderr,
        )
        return

    try:
        logger_provider = LoggerProvider()
        exporter = OTLPLogExporter(
            endpoint="{}/i/v1/logs".format(host.rstrip("/")),
            headers={"Authorization": "Bearer {}".format(project_token)},
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
        posthog_log_logger.addHandler(LoggingHandler(logger_provider=logger_provider))
        atexit.register(_shutdown_logger_provider, logger_provider)
    except Exception:
        print(
            "WARNING: PostHog log capture could not be initialized; operational "
            "logs will not be exported",
            file=sys.stderr,
        )


_initialize_posthog_logs()
