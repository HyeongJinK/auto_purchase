import logging
import os
from datetime import datetime

def setup_logger(base_filename: str) -> logging.Logger:
    today = datetime.now().strftime("%Y%m%d")
    log_filename = f"{base_filename}_{today}.log"
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger(base_filename)
    logger.setLevel(logging.INFO)

    # 이미 핸들러가 추가된 경우 중복 추가 방지
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger