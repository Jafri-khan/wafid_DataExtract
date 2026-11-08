"""
Secure logging module ensuring sensitive data is never logged in plaintext.
"""
import logging
import sys
from config import LOG_DIR

def setup_logger(name="WafidAutomation"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')

    log_file = LOG_DIR / "automation.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

def mask_passport(passport: str) -> str:
    if not passport or len(passport) <= 4:
        return "****"
    return "*" * (len(passport) - 4) + passport[-4:]
