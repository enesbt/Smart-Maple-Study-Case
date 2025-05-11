import logging
import logging.config
import os
from pathlib import Path

def setup_logging(log_level=logging.INFO):
    base_dir = Path(__file__).parents[2]
    logs_dir = base_dir / "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = logs_dir / "app.log"
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': log_level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': log_level,
                'formatter': 'detailed',
                'class': 'logging.FileHandler',
                'filename': str(log_file),
                'mode': 'a',
                'encoding': 'utf-8'
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': True
            },
            'src': {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False
            },
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    root_logger = logging.getLogger()
    root_logger.info(f"Logging initialized at level: {logging.getLevelName(log_level)}")
    root_logger.info(f"Log file: {log_file}")
    
    return root_logger

def get_logger(name):
    return logging.getLogger(name)