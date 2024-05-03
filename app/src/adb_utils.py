import subprocess
import math
import cv2
from src import constants
import numpy as np
import subprocess
import math
from src.config_utils import read_config
from src import custom_utils
import pyautogui
import time
from src.board_utils import current_board
from pathlib import Path

pipe = subprocess.Popen("adb kill-server",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
output = str(pipe.stdout.read()) #type: ignore
pipe = subprocess.Popen("adb connect localhost:5555",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
output = str(pipe.stdout.read()) #type: ignore
thread_sleep_timer = None
hearts_loop_counter = 0
last_button_clicked = None

def get_screenshot():
    pipe = subprocess.Popen("adb -s localhost:5555 shell screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n') #type: ignore
    img = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR) #type: ignore
    cv2.imwrite(constants.LAST_SCREEN_IMAGE_PATH, img)
    return img

def crop_board(img):
    img = img[current_board.board_top_left[1]:current_board.board_bottom_right[1], current_board.board_top_left[0]:current_board.board_bottom_right[0]].copy()
    cv2.imwrite(constants.LAST_BOARD_IMAGE_PATH, img)
    return img

def execute_play(result):
    try:
        adb_move = read_config().get("adb_move")
        if result and "0,0" not in result and "Wrong Board" not in result and adb_move:

            red_row, red_column, blue_row, blue_column = custom_utils.extract_result_position(result)

            from_x = math.floor(current_board.board_x + (current_board.board_w * red_column) - (current_board.board_w / 2))
            from_y = math.floor(current_board.board_y + (current_board.board_h * red_row) - (current_board.board_w / 2))
            to_x = math.floor(current_board.board_x + (current_board.board_w * blue_column) - (current_board.board_w / 2))
            to_y = math.floor(current_board.board_y + (current_board.board_h * blue_row) - (current_board.board_w / 2))

            new_to_x, new_to_y = move_second_point(from_x, from_y, to_x, to_y, current_board.board_w/2.5, current_board.board_h/2.5)

            subprocess.Popen(f"adb -s localhost:5555 shell input swipe {from_x} {from_y} {new_to_x} {new_to_y} 250", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            time.sleep(1.0)
            return True
    except Exception as ex:
        print(f"Error on execute_play: {ex}")
    return False

def move_second_point(x0_initial, y0_initial, x1_initial, y1_initial, x_offset, y_offset):
    # Calculate the difference in position of the first point

    x1_new = x1_initial
    y1_new = y1_initial

    if x0_initial < x1_initial:
        x1_new = x1_initial + x_offset
    elif x0_initial > x1_initial:
        x1_new = x1_initial - x_offset

    if y0_initial < y1_initial:
        y1_new = y1_initial + y_offset
    elif y0_initial > y1_initial:
        y1_new = y1_initial - y_offset

    return math.floor(x1_new), math.floor(y1_new)

def check_hearts(original_image):
    global thread_sleep_timer, hearts_loop_counter
    try:
        max_probability = 0.0
        
        for template_path in constants.CURRENT_HEARTS_LIST:
            template_image = cv2.imread(template_path.as_posix())
            top_left, _, probability = search_template(original_image, template_image)
            if probability > max_probability:
                max_probability = probability
                best_image = template_path

        if max_probability < 0.7:
            print(f"Current Hearts amount is Unknown")
            return
        hearts_number = int(best_image.stem[-1])
        print(f"Current Hearts amount is: {hearts_number}")
        hearts_loop_counter+= 1
        if hearts_number == 0:
            print("Hearts Ended, waiting for 3600 seconds")
            thread_sleep_timer = 3600
            time.sleep(3600)
            thread_sleep_timer = None
        elif hearts_number >= 5 or hearts_loop_counter > 20:
            print("Hearts maxed, small click test") #Try to skip the daily login bonus screen
            subprocess.Popen(f"adb -s localhost:5555 shell input tap {top_left[0]} {top_left[1]}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except Exception as ex:
        print(f"Error checking hearts number: {ex}")
        return
    

def check_buttons_to_click(original_image):
    global hearts_loop_counter, last_button_clicked
    for image in Path(constants.ADB_AUTO_FOLDER).glob("*.png"):
        image_path = image.as_posix()
        if last_button_clicked == image_path:
            last_button_clicked = None
            continue
        if check_button_and_click(original_image, image_path):
            hearts_loop_counter = 0
            last_button_clicked = image_path
            return True
    last_button_clicked = None
    print("No buttons found to be clicked")
    return False 


def check_button_and_click(original_image, image_path, confidence=0.7, extra_timeout=2.0, click=True):
    try:
        template_image = cv2.imread(image_path)
        top_left, board_bottom_right, probability = search_template(original_image, template_image)
        if probability < confidence:
            return
        print(f"Found: {image_path}")
        if click:
            x = math.floor((top_left[0] + board_bottom_right[0]) / 2)
            y = math.floor((top_left[1] + board_bottom_right[1]) / 2)
            subprocess.Popen(f"adb -s localhost:5555 shell input tap {x} {y}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            if extra_timeout > 0:
                time.sleep(extra_timeout)
        return True
    except Exception as ex:
        return False

def search_template(main_image, template):
    result = cv2.matchTemplate(main_image, template, cv2.TM_CCOEFF_NORMED)

    min_val, max_probability, min_loc, max_loc = cv2.minMaxLoc(result)

    top_left = max_loc
    bottom_right = (top_left[0] + template.shape[1], top_left[1] + template.shape[0])

    return top_left, bottom_right, max_probability

def has_match(original_image, template_path):
    return check_button_and_click(original_image, template_path, click=False)

def update_fog_image(index):
    cell_x0, cell_y0, cell_x1, cell_y1 = get_coordinates_from_board_index(index)
    center_x = math.floor((cell_x0 + cell_x1) / 2)
    center_y = math.floor((cell_y0 + cell_y1) / 2)
    subprocess.Popen(f"adb -s localhost:5555 shell input swipe {center_x} {center_y} {center_x} {center_y} 1000", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    time.sleep(0.5)
    pipe = subprocess.Popen("adb -s localhost:5555 shell screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n') #type: ignore
    img = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR) #type: ignore
    new_img = expand_rectangle_and_cut_from_image(img, cell_x0, cell_y0, cell_x1, cell_y1, 0, 0)

    return new_img

def expand_rectangle_and_cut_from_image(img, x0, y0, x1, y1, width, height):
    # Expand the rectangle
    x0_new, y0_new = max(0, x0 - width), max(0, y0 - height)
    x1_new, y1_new = min(img.shape[1], x1 + width), min(img.shape[0], y1 + height)
    
    # Crop the expanded rectangle
    cropped_img = img[y0_new:y1_new, x0_new:x1_new]
    
    return cropped_img

def click_on_board_index(index):
    cell_x0, cell_y0, cell_x1, cell_y1 = get_coordinates_from_board_index(index)
    center_x = math.floor((cell_x0 + cell_x1) / 2)
    center_y = math.floor((cell_y0 + cell_y1) / 2)
    subprocess.Popen(f"adb -s localhost:5555 shell input tap {center_x} {center_y}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    time.sleep(0.1)
    return center_x, center_y

def get_coordinates_from_board_index(idx):
    row, column = custom_utils.index_to_coordinates(idx)

    cell_x0 =  math.floor(current_board.board_x + (current_board.board_w * (column - 1)))
    cell_y0 =  math.floor(current_board.board_y + (current_board.board_h * (row - 1)))
    cell_x1 =  math.floor(current_board.board_x + (current_board.board_w * (column)))
    cell_y1 =  math.floor(current_board.board_y + (current_board.board_h * (row)))
    return cell_x0,cell_y0,cell_x1,cell_y1
    