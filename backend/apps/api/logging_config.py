"""Structured logging configuration for RazorFlow."""

import logging
import sys

from packages.common.context import get_request_id


class RequestIdFilter(logging.Filter):
    """Injects current request ID from ContextVar into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"  # type: ignore[attr-defined]
        return True


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """Configures structured console logging."""
    numeric_level = getattr(
        logging.LogLevel if hasattr(logging, "LogLevel") else logging,
        log_level.upper(),
        logging.INFO,
    )

    log_format = "%(asctime)s [%(levelname)s] [req_id=%(request_id)s] %(name)s: %(message)s"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers = [handler]

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
