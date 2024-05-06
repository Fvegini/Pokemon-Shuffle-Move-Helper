import logging
import os
import sys

log = logging.getLogger("custom")
try:
    log_level = os.getenv("LOG_LEVEL", "DEBUG")
    logging_level = logging.getLevelName(log_level)
    log.setLevel(logging_level)
except:
    log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(f'%(asctime)s.%(msecs)03d %(levelname)s - %(filename)s - %(message)s', "%Y-%m-%d %H:%M:%S"))
log.addHandler(handler)
log.propagate = False


def get_logger():
    return log
