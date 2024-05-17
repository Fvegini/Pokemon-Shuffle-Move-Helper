import logging
import os
import sys

import tkinter as tk
import logging
from collections import deque

class LogHandler(logging.Handler):
    def __init__(self, widget, max_lines=50):
        super().__init__()
        self.widget = widget
        self.max_lines = max_lines
        self.log_lines = deque(maxlen=max_lines)
        self.setFormatter(logging.Formatter(f'%(asctime)s.%(msecs)03d %(levelname)s - %(filename)s - %(message)s', "%Y-%m-%d %H:%M:%S"))

    def emit(self, record):
        msg = self.format(record)
        # self.log_lines.append(msg)
        self.log_lines.appendleft(msg)
        self.update_widget()

    def update_widget(self):
        # self.widget.config(state=tk.NORMAL)
        self.widget.delete(1.0, tk.END)
        self.widget.insert(tk.END, '\n'.join(self.log_lines))
        # self.widget.config(state=tk.DISABLED)


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





def insert_new_handler(custom_handler):
    global log
    log.addHandler(custom_handler)


def get_logger():
    return log
