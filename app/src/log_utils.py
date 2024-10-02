import logging
from logging.handlers import RotatingFileHandler#, TimedRotatingFileHandler
import os
import sys

import tkinter as tk
import logging
from collections import deque
from pathlib import Path

class LogHandler(logging.Handler):
    def __init__(self, widget, max_lines=50):
        super().__init__()
        self.widget = widget
        self.max_lines = max_lines
        self.log_lines = deque(maxlen=max_lines)
        self.setFormatter(logging.Formatter(f'%(asctime)s.%(msecs)03d %(levelname)s - %(filename)s_%(lineno)d - %(message)s', "%Y-%m-%d %H:%M:%S"))

    def emit(self, record):
        msg = self.format(record)
        self.log_lines.append(msg)  # Append the message to the end
        self.update_widget()  # Pass only the new message

    def update_widget(self):
        self.widget.delete("1.0", tk.END)  # Clear the widget
        self.widget.insert(tk.END, '\n'.join(self.log_lines) + '\n')  # Insert the last `max_lines` lines
        self.widget.see(tk.END)  # Ensure the latest message is visible


log = logging.getLogger("custom")
try:
    log_level = os.getenv("LOG_LEVEL", "DEBUG")
    logging_level = logging.getLevelName(log_level)
    log.setLevel(logging_level)
except:
    log.setLevel(logging.DEBUG)


console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(f'%(asctime)s.%(msecs)03d %(levelname)s - %(filename)s_%(lineno)d - %(message)s', "%Y-%m-%d %H:%M:%S"))
log.addHandler(console_handler)

# # Create a file handler
# log_file = "debug/app.log"
# file_handler = logging.FileHandler(log_file)
# file_handler.setFormatter(logging.Formatter(f'%(asctime)s.%(msecs)03d %(levelname)s - %(filename)s_%(lineno)d - %(message)s', "%Y-%m-%d %H:%M:%S"))
# log.addHandler(file_handler)

# Create a rotating file handler (by size)
log_file_size = "debug/app_size.log"
Path(log_file_size).parent.mkdir(parents=True, exist_ok=True)
rotating_file_handler = RotatingFileHandler(log_file_size, maxBytes=10*1024*1024, backupCount=5)  # 10MB per file, keep 5 backups
rotating_file_handler.setFormatter(logging.Formatter(f'%(asctime)s.%(msecs)03d %(levelname)s - %(filename)s_%(lineno)d - %(message)s', "%Y-%m-%d %H:%M:%S"))
log.addHandler(rotating_file_handler)

# # Create a timed rotating file handler (by day)
# log_file_time = "app_time.log"
# timed_rotating_file_handler = TimedRotatingFileHandler(log_file_time, when="midnight", interval=1, backupCount=7)  # Rotate daily, keep 7 backups
# timed_rotating_file_handler.setFormatter(logging.Formatter(f'%(asctime)s.%(msecs)03d %(levelname)s - %(filename)s_%(lineno)d - %(message)s', "%Y-%m-%d %H:%M:%S"))
# log.addHandler(timed_rotating_file_handler)

log.propagate = False


def insert_new_handler(custom_handler):
    global log
    log.addHandler(custom_handler)


def get_logger():
    return log
