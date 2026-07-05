import os
import logging
from logging.handlers import RotatingFileHandler

LOGS_DIR = "./logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# 5 MB max log file size, keep 5 backups
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

def _create_rotating_logger(name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Prevent duplicate handlers if re-imported
    if not logger.handlers:
        file_path = os.path.join(LOGS_DIR, filename)
        handler = RotatingFileHandler(
            file_path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Category-specific rotating loggers
app_logger = _create_rotating_logger("Application", "app.log")
auth_logger = _create_rotating_logger("Authentication", "auth.log")
chat_logger = _create_rotating_logger("Chat", "chat.log")
knowledge_logger = _create_rotating_logger("Knowledge", "knowledge.log")
medical_logger = _create_rotating_logger("Medical", "medical.log")
research_logger = _create_rotating_logger("Research", "research.log")
images_logger = _create_rotating_logger("Images", "images.log")
perf_logger = _create_rotating_logger("Performance", "performance.log")
error_logger = _create_rotating_logger("Errors", "errors.log")
api_logger = _create_rotating_logger("API_Calls", "api.log")

def log_err(msg: str, exc: Exception = None):
    if exc:
        msg = f"{msg} | Exception: {type(exc).__name__}: {exc}"
    error_logger.error(msg)
    app_logger.error(msg)
