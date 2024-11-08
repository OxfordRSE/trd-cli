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
