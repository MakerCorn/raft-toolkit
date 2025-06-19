"""
Enhanced logging setup for RAFT Toolkit.

This module provides a flexible logging system that supports:
- Default structured logging with popular open source libraries
- Integration with external logging tools (Sentry, DataDog, etc.)
- CLI-specific formatting and handlers
- Environment-based configuration
- Progress tracking and contextual logging
"""

import json
import logging
import logging.config
import os
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

try:
    import structlog

    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

HAS_COLOREDLOGS = False

try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    HAS_OPENTELEMETRY = True
except ImportError:
    HAS_OPENTELEMETRY = False

HAS_TRACING_SUPPORT = True

# Global configuration
_logging_config = {
    "level": "INFO",
    "format": "standard",
    "output": "console",
    "structured": False,
    "external_handler": None,
    "progress_tracking": True,
    "tracing_enabled": True,
    "trace_sampling_rate": 1.0,
    "jaeger_endpoint": None,
    "trace_service_name": "raft-toolkit",
    "context": {},
}

# Global tracing state
_tracer = None
_trace_context = threading.local()


class ProgressLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that includes progress information in log records."""

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})
        self.progress = ""
        self.context = {}

    def set_progress(self, progress: str):
        """Set the current progress string."""
        self.progress = progress

    def set_context(self, **kwargs):
        """Set contextual information for logging."""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear all contextual information."""
        self.context.clear()

    def process(self, msg, kwargs):
        # Override the progress field in the record after creation
        # by modifying the message to include progress info
        if self.progress:
            msg = f"[{self.progress:>4}] {msg}"

        extra = kwargs.setdefault("extra", {})
        extra.update({"raft_progress": self.progress, "raft_context": self.context.copy()})
        if self.extra:
            extra.update(self.extra)
        return msg, kwargs


class TraceableLoggerAdapter(ProgressLoggerAdapter):
    """Enhanced logger adapter with distributed tracing capabilities."""

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra)
        self.operation_id = None
        self.trace_id = None
        self.span_id = None

    def start_operation(self, operation_name: str, **attributes):
        """Start a new traced operation."""
        if not _logging_config.get("tracing_enabled", False):
            return

        # Generate trace IDs
        if not HAS_OPENTELEMETRY:
            # Fallback to UUID-based tracing
            self.operation_id = operation_name
            self.trace_id = str(uuid.uuid4())[:8]
            self.span_id = str(uuid.uuid4())[:8]
        elif _tracer:
            # Use OpenTelemetry if available
            span = _tracer.start_span(operation_name, attributes=attributes)  # type: ignore
            span_context = span.get_span_context()
            self.trace_id = format(span_context.trace_id, "032x")[:8]
            self.span_id = format(span_context.span_id, "016x")[:8]
            self.operation_id = operation_name

            # Store span in thread-local storage
            if not hasattr(_trace_context, "spans"):
                _trace_context.spans = []
            _trace_context.spans.append(span)
        else:
            # OpenTelemetry available but no tracer configured
            self.operation_id = operation_name
            self.trace_id = str(uuid.uuid4())[:8]
            self.span_id = str(uuid.uuid4())[:8]

    def end_operation(self, status: str = "success", **attributes):
        """End the current traced operation."""
        if not _logging_config.get("tracing_enabled", False) or not self.operation_id:
            return

        if HAS_OPENTELEMETRY and hasattr(_trace_context, "spans") and _trace_context.spans:
            span = _trace_context.spans.pop()
            # Add final attributes
            span.set_attributes(attributes)
            if status == "error":
                span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.end()

        # Clear trace context
        self.operation_id = None
        self.trace_id = None
        self.span_id = None

    def add_trace_event(self, event_name: str, **attributes):
        """Add an event to the current trace span."""
        if not _logging_config.get("tracing_enabled", False):
            return

        if HAS_OPENTELEMETRY and hasattr(_trace_context, "spans") and _trace_context.spans:
            span = _trace_context.spans[-1]  # Get current span
            span.add_event(event_name, attributes)

    def process(self, msg, kwargs):
        # Include tracing information in logs
        if self.progress:
            msg = f"[{self.progress:>4}] {msg}"

        # Add trace context if available
        if self.trace_id and self.span_id:
            msg = f"[trace:{self.trace_id}] {msg}"

        extra = kwargs.setdefault("extra", {})
        extra.update(
            {
                "raft_progress": self.progress,
                "raft_context": self.context.copy(),
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "operation_id": self.operation_id,
            }
        )
        if self.extra:
            extra.update(self.extra)
        return msg, kwargs


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add progress if available
        if hasattr(record, "raft_progress") and record.raft_progress:
            log_obj["progress"] = record.raft_progress
        elif hasattr(record, "progress") and record.progress:
            log_obj["progress"] = record.progress

        # Add context if available
        if hasattr(record, "raft_context") and record.raft_context:
            log_obj["context"] = record.raft_context
        elif hasattr(record, "context") and record.context:
            log_obj["context"] = record.context

        # Add tracing information if available
        if hasattr(record, "trace_id") and record.trace_id:
            log_obj["trace_id"] = record.trace_id
        if hasattr(record, "span_id") and record.span_id:
            log_obj["span_id"] = record.span_id
        if hasattr(record, "operation_id") and record.operation_id:
            log_obj["operation_id"] = record.operation_id

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


class ColoredConsoleFormatter(logging.Formatter):
    """Enhanced colored formatter for console output."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colors = {
            "DEBUG": "\033[36m",  # Cyan
            "INFO": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "CRITICAL": "\033[35m",  # Magenta
            "RESET": "\033[0m",  # Reset
        }

    def format(self, record):
        # Format the time
        if self.datefmt:
            record.asctime = self.formatTime(record, self.datefmt)
        else:
            record.asctime = self.formatTime(record)

        if hasattr(record, "raft_progress") and record.raft_progress:
            progress_str = f"[{record.raft_progress:>4}] "
        elif hasattr(record, "progress") and record.progress:
            progress_str = f"[{record.progress:>4}] "
        else:
            progress_str = ""

        color = self.colors.get(record.levelname, "")
        reset = self.colors["RESET"]

        formatted = (
            f"{color}{record.asctime} {record.levelname:>8}{reset} {progress_str}{record.name}: {record.getMessage()}"
        )

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class ExternalLogHandler(logging.Handler):
    """Handler for integrating with external logging services."""

    def __init__(self, handler_func, level=logging.NOTSET):
        super().__init__(level)
        self.handler_func = handler_func

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.handler_func(log_entry, record)
        except Exception:
            self.handleError(record)


def setup_structlog():
    """Configure structlog if available."""
    if not HAS_STRUCTLOG:
        return None

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


def setup_tracing(
    service_name: Optional[str] = None,
    jaeger_endpoint: Optional[str] = None,
    sampling_rate: Optional[float] = None,
    console_export: bool = False,
) -> None:
    """
    Set up distributed tracing with OpenTelemetry.

    Args:
        service_name: Name of the service for tracing
        jaeger_endpoint: Jaeger collector endpoint
        sampling_rate: Sampling rate for traces (0.0 to 1.0)
        console_export: Whether to export traces to console
    """
    global _tracer

    if not HAS_OPENTELEMETRY:
        logging.warning("OpenTelemetry not available. Tracing will use fallback trace IDs.")
        return

    # Set up tracer provider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    # Add console exporter if requested
    if console_export:
        console_exporter = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(console_exporter)
        provider.add_span_processor(span_processor)

    # Add Jaeger exporter if endpoint provided
    if jaeger_endpoint and isinstance(jaeger_endpoint, str):
        try:
            jaeger_exporter = JaegerExporter(endpoint=jaeger_endpoint)
            span_processor = BatchSpanProcessor(jaeger_exporter)
            provider.add_span_processor(span_processor)
        except Exception as e:
            logging.warning(f"Failed to setup Jaeger exporter: {e}")

    # Instrument logging
    LoggingInstrumentor().instrument()

    # Get tracer
    service_name_str = service_name or _logging_config.get("trace_service_name", "raft-toolkit")
    if isinstance(service_name_str, str):
        _tracer = trace.get_tracer(__name__, service_name_str)
    else:
        _tracer = trace.get_tracer(__name__, "raft-toolkit")

    logging.info(
        f"Tracing initialized for service: {service_name_str if isinstance(service_name_str, str) else 'raft-toolkit'}"
    )


def configure_logging(
    level: Optional[str] = None,
    format_type: Optional[str] = None,
    output: Optional[str] = None,
    structured: Optional[bool] = None,
    external_handler: Any = None,
    progress_tracking: Optional[bool] = None,
    tracing_enabled: Optional[bool] = None,
    trace_sampling_rate: Optional[float] = None,
    jaeger_endpoint: Optional[str] = None,
    trace_service_name: Optional[str] = None,
    **context: Any,
) -> None:
    """
    Configure the logging system with flexible options.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Formatting style (standard, colored, json, minimal)
        output: Output destination (console, file, both)
        structured: Whether to use structured logging
        external_handler: External logging handler function
        progress_tracking: Enable progress tracking in logs
        tracing_enabled: Enable distributed tracing
        trace_sampling_rate: Sampling rate for traces (0.0 to 1.0)
        jaeger_endpoint: Jaeger collector endpoint
        trace_service_name: Service name for tracing
        **context: Additional context to include in all logs
    """

    # Update configuration
    if level is not None:
        _logging_config["level"] = level.upper()
    if format_type is not None:
        _logging_config["format"] = format_type
    if output is not None:
        _logging_config["output"] = output
    if structured is not None:
        _logging_config["structured"] = structured
    if external_handler is not None:
        _logging_config["external_handler"] = external_handler
    if progress_tracking is not None:
        _logging_config["progress_tracking"] = progress_tracking
    if tracing_enabled is not None:
        _logging_config["tracing_enabled"] = tracing_enabled
    if trace_sampling_rate is not None:
        _logging_config["trace_sampling_rate"] = trace_sampling_rate
    if jaeger_endpoint is not None:
        _logging_config["jaeger_endpoint"] = jaeger_endpoint
    if trace_service_name is not None:
        _logging_config["trace_service_name"] = trace_service_name
    if context and isinstance(_logging_config["context"], dict):
        _logging_config["context"].update(context)


def get_formatter(format_type: Optional[str] = None) -> logging.Formatter:
    """Get a formatter based on the specified type."""
    format_type = format_type or str(_logging_config["format"])

    if format_type == "json":
        return JSONFormatter()
    elif format_type == "colored" and HAS_COLOREDLOGS:
        return ColoredConsoleFormatter(
            fmt="%(asctime)s %(levelname)8s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    elif format_type == "minimal":
        return logging.Formatter("%(levelname)s: %(message)s")
    else:  # standard
        return logging.Formatter(
            "%(asctime)s %(levelname)8s [%(progress)4s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_handlers() -> List[logging.Handler]:
    """Set up logging handlers based on configuration."""
    handlers: List[logging.Handler] = []
    output = str(_logging_config["output"])
    level_name: str = str(_logging_config["level"])
    level = getattr(logging, level_name)

    # Console handler
    if output in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(get_formatter())
        handlers.append(console_handler)

    # File handler
    if output in ("file", "both"):
        log_dir = Path(os.getenv("RAFT_LOG_DIR", "./logs"))
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "raft.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for file
        file_handler.setFormatter(get_formatter("json" if _logging_config["structured"] else "standard"))
        handlers.append(file_handler)

    # External handler
    if _logging_config["external_handler"]:
        external_handler = ExternalLogHandler(_logging_config["external_handler"])
        external_handler.setLevel(level)
        external_handler.setFormatter(get_formatter("json"))
        handlers.append(external_handler)

    return handlers


def install_default_record_field(field: str, value: Any) -> None:
    """
    Install a default field in all log records.

    Args:
        field: The name of the field to add
        value: The default value for the field
    """
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        # Always set the field, but allow it to be overridden by extra
        setattr(record, field, value)
        return record

    logging.setLogRecordFactory(record_factory)


def log_setup() -> None:
    """
    Set up the logging system based on environment and configuration.

    This function is the main entry point for initializing logging.
    It reads configuration from environment variables and sets up
    appropriate handlers and formatters.
    """
    # Read configuration from environment
    level = os.getenv("RAFT_LOG_LEVEL", "INFO").upper()
    format_type = os.getenv("RAFT_LOG_FORMAT", "colored" if HAS_COLOREDLOGS else "standard")
    output = os.getenv("RAFT_LOG_OUTPUT", "console")
    structured = os.getenv("RAFT_LOG_STRUCTURED", "false").lower() == "true"

    # Read tracing configuration from environment
    tracing_enabled = os.getenv("RAFT_TRACING_ENABLED", "true").lower() == "true"
    trace_sampling_rate = float(os.getenv("RAFT_TRACE_SAMPLING_RATE", "1.0"))
    jaeger_endpoint = os.getenv("RAFT_JAEGER_ENDPOINT")
    trace_service_name = os.getenv("RAFT_TRACE_SERVICE_NAME", "raft-toolkit")
    trace_console_export = os.getenv("RAFT_TRACE_CONSOLE", "false").lower() == "true"

    # Configure logging
    configure_logging(
        level=level,
        format_type=format_type,
        output=output,
        structured=structured,
        tracing_enabled=tracing_enabled,
        trace_sampling_rate=trace_sampling_rate,
        jaeger_endpoint=jaeger_endpoint,
        trace_service_name=trace_service_name,
    )

    # Set up tracing if enabled
    if tracing_enabled:
        setup_tracing(
            service_name=trace_service_name,
            jaeger_endpoint=jaeger_endpoint,
            sampling_rate=trace_sampling_rate,
            console_export=trace_console_export,
        )

    # Set up basic logging
    root_logger = logging.getLogger()
    level_name: str = str(_logging_config["level"])
    root_logger.setLevel(getattr(logging, level_name))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handlers
    for handler in setup_handlers():
        root_logger.addHandler(handler)

    # Install default record fields
    if _logging_config["progress_tracking"]:
        install_default_record_field("progress", "")

    # Set up structlog if enabled and available
    if _logging_config["structured"] and HAS_STRUCTLOG:
        setup_structlog()

    # Configure third-party loggers
    configure_third_party_loggers()


def configure_third_party_loggers() -> None:
    """Configure logging levels for third-party libraries."""
    # Reduce noise from common libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langchain_community.utils.math").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """
    Get a configured logger with progress tracking and optional tracing capabilities.

    Args:
        name: The name of the logger

    Returns:
        A TraceableLoggerAdapter if tracing is enabled, otherwise ProgressLoggerAdapter,
        or a structlog logger if structured logging is enabled
    """
    base_logger = logging.getLogger(name)

    if _logging_config["structured"] and HAS_STRUCTLOG:
        # Return structlog logger if available and structured logging is enabled
        return structlog.get_logger(name)
    elif _logging_config.get("tracing_enabled", False):
        # Return traceable adapter with progress tracking and tracing
        return TraceableLoggerAdapter(base_logger, _logging_config["context"])
    else:
        # Return enhanced adapter with progress tracking only
        return ProgressLoggerAdapter(base_logger, _logging_config["context"])


def setup_external_logging(handler_func: Any, format_type: str = "json") -> None:
    """
    Set up integration with external logging services.

    Args:
        handler_func: Function to handle log entries. Should accept (log_entry, record)
        format_type: Format for the log entries sent to external service

    Example:
        def sentry_handler(log_entry, record):
            if record.levelno >= logging.ERROR:
                sentry_sdk.capture_message(log_entry)

        setup_external_logging(sentry_handler)
    """
    configure_logging(external_handler=handler_func)

    # Re-setup logging to include the external handler
    log_setup()


def setup_logging_from_config(config_path: Union[str, Path]) -> None:
    """
    Set up logging from a YAML or JSON configuration file.

    Args:
        config_path: Path to the configuration file
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Logging configuration file not found: {config_path}")

    if config_path.suffix.lower() == ".yaml" or config_path.suffix.lower() == ".yml":
        if not HAS_YAML:
            raise ImportError("PyYAML is required for YAML configuration files")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    else:
        with open(config_path, "r") as f:
            config = json.load(f)

    logging.config.dictConfig(config)


# Convenience functions for common external logging integrations


def setup_sentry_logging(dsn: str, **kwargs: Any) -> None:
    """
    Set up Sentry integration for error tracking.

    Args:
        dsn: Sentry DSN
        **kwargs: Additional Sentry configuration
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry_sdk.init(dsn=dsn, integrations=[sentry_logging], **kwargs)

        def sentry_handler(log_entry, record):
            if record.levelno >= logging.ERROR:
                sentry_sdk.capture_message(record.getMessage(), level=record.levelname.lower())

        setup_external_logging(sentry_handler)

    except ImportError:
        logging.warning("Sentry SDK not available. Install with: pip install sentry-sdk")


def setup_datadog_logging(api_key: str, service_name: str = "raft-toolkit") -> None:
    """
    Set up DataDog logging integration.

    Args:
        api_key: DataDog API key
        service_name: Service name for DataDog
    """
    try:
        from datadog import DogStatsdClient

        statsd = DogStatsdClient()

        def datadog_handler(log_entry, record):
            # Send metrics to DataDog
            statsd.increment(f"{service_name}.logs.{record.levelname.lower()}")

            if record.levelno >= logging.ERROR:
                statsd.increment(f"{service_name}.errors")

        setup_external_logging(datadog_handler)

    except ImportError:
        logging.warning("DataDog library not available. Install with: pip install datadog")
