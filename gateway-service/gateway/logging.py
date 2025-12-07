import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"

try:
    LOGS_DIR.mkdir(exist_ok=True, mode=0o755)
except (OSError, PermissionError) as e:
    print(f"Warning: Could not create logs directory {LOGS_DIR}: {e}", file=sys.stderr)
    LOGS_DIR = None

logger = logging.getLogger('gateway')
logger.setLevel(logging.INFO)
logger.propagate = False

if logger.handlers:
    logger.handlers.clear()

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
                            datefmt="%Y-%m-%d %H:%M:%S")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

if LOGS_DIR:
    try:
        log_file = LOGS_DIR / "gateway.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        logger.warning(f"Could not create file handler: {e}. Logging to console only.")
        print(f"Warning: Could not write to log file: {e}", file=sys.stderr)
