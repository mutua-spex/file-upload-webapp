import logging
import sys


def configure_logging() -> None:
    """Configure structured logging for the backend."""
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Uvicorn loggers are noisy by default in debug; keep them at INFO
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
