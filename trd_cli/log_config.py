import os

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": "trd_cli.log",
            "mode": "w",
        }
    },
    "root": {"level": "INFO", "handlers": ["file"]},
}


def get_config(log_file: str) -> dict:
    """
    Return a dictionary of the logging configuration.
    """
    config = {**LOGGING_CONFIG}
    config["handlers"]["file"]["filename"] = log_file
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    return config
