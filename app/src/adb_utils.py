import subprocess
import math
import cv2
from src import constants
import numpy as np
import subprocess
import math
from src.config_utils import read_config
from src import custom_utils
from src.config_utils import config_values
import pyautogui
import time

pipe = subprocess.Popen("adb kill-server",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
output = str(pipe.stdout.read()) #type: ignore
pipe = subprocess.Popen("adb connect localhost:5555",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
output = str(pipe.stdout.read()) #type: ignore
thread_sleep_timer = None

def get_screenshot():
    pipe = subprocess.Popen("adb -s localhost:5555 shell screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n') #type: ignore
    img = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR) #type: ignore
    cv2.imwrite(constants.LAST_SCREEN_IMAGE_PATH, img)
    return img

def crop_board(img):
    board_top_left = config_values.get("board_top_left")
    board_bottom_right = config_values.get("board_bottom_right")
    img = img[board_top_left[1]:board_bottom_right[1], board_top_left[0]:board_bottom_right[0]].copy()
    cv2.imwrite(constants.LAST_BOARD_IMAGE_PATH, img)
    return img

def execute_play(result):
    try:
        adb_move = read_config().get("adb_move")
        if result and "0,0" not in result and "Wrong Board" not in result and adb_move:
            board_top_left = config_values.get("board_top_left")
            board_bottom_right = config_values.get("board_bottom_right")
            
            board_x = board_top_left[0]
            board_y = board_top_left[1]
            board_w = (board_bottom_right[0] - board_top_left[0]) / 6
            board_h = (board_bottom_right[1] - board_top_left[1]) / 6

            red_row, red_column, blue_row, blue_column = custom_utils.extract_result_position(result)

            from_x = math.floor(board_x + (board_w * red_column) - (board_w / 2))
            from_y = math.floor(board_y + (board_h * red_row) - (board_w / 2))
            to_x = math.floor(board_x + (board_w * blue_column) - (board_w / 2))
            to_y = math.floor(board_y + (board_h * blue_row) - (board_w / 2))

            new_to_x, new_to_y = move_second_point(from_x, from_y, to_x, to_y, board_w/2.5, board_h/2.5)

            subprocess.Popen("adb -s localhost:5555 shell input swipe %d %d %d %d %d" % (
                from_x, from_y, new_to_x, new_to_y, 250),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)


            # subprocess.Popen("adb -s localhost:5555 shell input swipe %d %d %d %d %d" % (
            #     from_x, from_y, new_to_x, new_to_y, 250),
            #     stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # print()
            # subprocess.Popen("adb -s localhost:5555 shell input swipe %d %d %d %d %d" % (
            #     math.floor(board_x + (board_w * x0) + (board_w / 2)), 
            #     math.floor(board_y + (board_h * y0) + (board_h / 2)), 
            #     math.floor(board_x + (board_w * x1) + (board_w / 2)), 
            #     math.floor(board_y + (board_h * y1) + (board_h / 2)), 
            #     250),
            #     stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # subprocess.Popen(f"adb -s localhost:5555 shell motionevent DOWN 86, 963", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        


            # subprocess.Popen("adb -s localhost:5555 shell motionevent DOWN %d %d" % (
            #     math.floor(board_x + (board_w * x0) + (board_w / 2)), 
            #     math.floor(board_y + (board_h * y0) + (board_h / 2))),
            #     stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            # subprocess.Popen("adb -s localhost:5555 shell motionevent MOVE %d %d " % (
            #     math.floor(board_x + (board_w * x1) + (board_w / 2)), 
            #     math.floor(board_y + (board_h * y1) + (board_h / 2))),
            #     stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            # subprocess.Popen("adb -s localhost:5555 shell motionevent UP %d %d " % (
            #     math.floor(board_x + (board_w * x1) + (board_w / 2)), 
            #     math.floor(board_y + (board_h * y1) + (board_h / 2))),
            #     stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

            # print()

    except Exception as ex:
        print(f"Error on execute_play: {ex}")
        pass

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

# # Example usage
# x0_initial, y0_initial = 3, 4  # Initial coordinates of the first point
# x1_initial, y1_initial = 5, 6  # Initial coordinates of the second point
# x_offset, y_offset = 2, -1  # Amounts to move in the x and y directions
# x1_new, y1_new = move_second_point(x0_initial, y0_initial, x1_initial, y1_initial, x_offset, y_offset)
# print(f"New point coordinates: ({x1_new}, {y1_new})")



def check_hearts(original_image):
    global thread_sleep_timer
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
        if hearts_number == 0:
            print("Hearts Ended, waiting for 3600 seconds")
            thread_sleep_timer = 3600
            time.sleep(3600)
            thread_sleep_timer = None
        elif hearts_number >= 5:
            print("Hearts maxed, small click test") #Try to skip the daily login bonus screen
            subprocess.Popen(f"adb -s localhost:5555 shell input tap {top_left[0]} {top_left[1]}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except Exception as ex:
        print(f"Error checking hearts number: {ex}")
        return
    

def check_buttons_to_click(original_image):
    found_list = []
    found_list.append(check_button(original_image, constants.CURRENT_STAGE_IMAGE))
    found_list.append(check_button(original_image, constants.OK_BUTTON_IMAGE, extra_timeout=4))
    found_list.append(check_button(original_image, constants.OK_BUTTON2_IMAGE, extra_timeout=4))
    found_list.append(check_button(original_image, constants.CONTINUE_IMAGE_IMAGE))
    found_list.append(check_button(original_image, constants.START_BUTTON_IMAGE))
    found_list.append(check_button(original_image, constants.TO_MAP_BUTTON_IMAGE))
    return any(found_list)


def check_button(original_image, image_path, confidence=0.7, extra_timeout=0.0, click=True):
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

def has_board_active(original_image):
    return check_button(original_image, constants.ACTIVE_BOARD_IMAGE, click=False)

def update_fog_image(cell_x0, cell_y0, cell_x1, cell_y1, board_w, board_h):
    center_x = math.floor((cell_x0 + cell_x1) / 2)
    center_y = math.floor((cell_y0 + cell_y1) / 2)
    subprocess.Popen(f"adb -s localhost:5555 shell input swipe {center_x} {center_y} {center_x} {center_y} 1000", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    time.sleep(0.5)
    pipe = subprocess.Popen("adb -s localhost:5555 shell screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n') #type: ignore
    img = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR) #type: ignore
    
    # expand_width = math.floor(board_w / 4)
    # expand_height = math.floor(board_h / 4)
    # expanded_img = expand_rectangle_and_cut_from_image(img, cell_x0, cell_y0, cell_x1, cell_y1, expand_width, expand_height)
    new_img = expand_rectangle_and_cut_from_image(img, cell_x0, cell_y0, cell_x1, cell_y1, 0, 0)

    return new_img

def expand_rectangle_and_cut_from_image(img, x0, y0, x1, y1, width, height):
    # Expand the rectangle
    x0_new, y0_new = max(0, x0 - width), max(0, y0 - height)
    x1_new, y1_new = min(img.shape[1], x1 + width), min(img.shape[0], y1 + height)
    
    # Crop the expanded rectangle
    cropped_img = img[y0_new:y1_new, x0_new:x1_new]
    
    return cropped_img