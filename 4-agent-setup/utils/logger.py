import logging
import sys
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init(autoreset=True)

# Custom logging formatter with colors and emojis
class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "🔍 %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "ℹ️ %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "⚠️ %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "❌ %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.MAGENTA + "🚨 %(message)s" + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger():
    """Setup and return a configured logger instance."""
    # Configure logging with custom formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )
    logger = logging.getLogger(__name__)

    # Log only essential environment info
    logger.info(f"Logger initialized")
    return logger

# Create a default logger instance for import
logger = setup_logger()
