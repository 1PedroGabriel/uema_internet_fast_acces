import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    """
    Configura um logger rotativo em %APPDATA%/UEMA_FastAccess/app.log.
    Garante que o arquivo nunca passe de 1MB e mantém 2 backups.
    """
    appdata = os.getenv('APPDATA', os.path.expanduser('~'))
    log_dir = os.path.join(appdata, 'UEMA_FastAccess')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'app.log')

    logger = logging.getLogger("UEMAFastAccess")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024, # 1MB
            backupCount=2,
            encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
