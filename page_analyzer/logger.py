import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def logger(name):
    """ write down info about app """
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        filename=log_dir / 'flask_app.log',
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )

    if logger.handlers:
        return logger

    # Формат сообщений
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    return logger
