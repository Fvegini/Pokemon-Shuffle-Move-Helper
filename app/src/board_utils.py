from src.classes import Board
from src import config_utils


current_board = Board(config_utils.config_values.get("board_top_left"), config_utils.config_values.get("board_bottom_right"))

def update_board():
    global current_board
    current_board = Board(config_utils.config_values.get("board_top_left"), config_utils.config_values.get("board_bottom_right"))