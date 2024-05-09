import subprocess
import math
import cv2
from src import constants
import numpy as np
import subprocess
import math
from src import config_utils
from src import custom_utils
import pyautogui
import time
import pytesseract
from src.board_utils import current_board
from pathlib import Path
from src import log_utils

log = log_utils.get_logger()

pipe = subprocess.Popen("adb kill-server",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
output = str(pipe.stdout.read()) #type: ignore
pipe = subprocess.Popen("adb connect localhost:5555",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
output = str(pipe.stdout.read()) #type: ignore
thread_sleep_timer = None
hearts_loop_counter = 0
last_button_clicked = None

def get_screenshot():
    pipe = subprocess.Popen("adb shell screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n') #type: ignore
    img = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR) #type: ignore
    cv2.imwrite(constants.LAST_SCREEN_IMAGE_PATH, img)
    return img

def get_screen_resolution():
    pipe = subprocess.Popen("adb shell wm size",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    return str(pipe.stdout.read())[17:26]

def crop_board(img):
    resolution = get_screen_resolution()
    r = constants.RESOLUTIONS[resolution]["Board"]
    board_top_left = (r[0], r[1])
    board_bottom_right = (r[2], r[3])
    img = img[board_top_left[1]:board_bottom_right[1], board_top_left[0]:board_bottom_right[0]].copy()
    img = img[current_board.board_top_left[1]:current_board.board_bottom_right[1], current_board.board_top_left[0]:current_board.board_bottom_right[0]].copy()

    cv2.imwrite(constants.LAST_BOARD_IMAGE_PATH, img)
    return img

def execute_play(result, board_results, last_execution_swiped):
    try:
        adb_move = config_utils.config_values.get("adb_move")
        if result and adb_move:
            timed_play = config_utils.config_values.get("timed_stage")
            wrong_board = "Wrong Board" in result
            zero_result = "0,0" in result
            if timed_play and (wrong_board or zero_result) and not last_execution_swiped:
                log.debug("Runing find_slot_to_mega crazy function")
                new_result = custom_utils.find_slot_to_mega(board_results)
                log.debug(f"Changing result from: {result}")
                log.debug(f"Changing result to: {new_result}")
                result = new_result
                wrong_board = False
                zero_result = False
            if not wrong_board and not zero_result :
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
        log.error(f"Error on execute_play: {ex}")
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

# # Example usage
# x0_initial, y0_initial = 3, 4  # Initial coordinates of the first point
# x1_initial, y1_initial = 5, 6  # Initial coordinates of the second point
# x_offset, y_offset = 2, -1  # Amounts to move in the x and y directions
# x1_new, y1_new = move_second_point(x0_initial, y0_initial, x1_initial, y1_initial, x_offset, y_offset)
# print(f"New point coordinates: ({x1_new}, {y1_new})")

def check_if_close_to_same_color(pixel1, pixel2, threshold=10):
  diff = np.subtract(pixel1, pixel2)
  return np.all(np.abs(diff) < threshold)

def check_hearts(original_image):
    global thread_sleep_timer, hearts_loop_counter
    try:
        hearts_number = get_label(original_image, "Hearts")
        hearts_loop_counter+= 1
        if not hearts_number.isnumeric():
            log.debug(f"Current Hearts amount is Unknown")
            return
        hearts_number = int(hearts_number)
        log.debug(f"Current Hearts amount is: {hearts_number}")
        if hearts_number == 0:
            hearts_timer = get_label(original_image, "HeartTimer")
            thread_sleep_timer = int(hearts_timer[:2]) * 60 + int(hearts_timer[3:]) + 5 #add 5s to heart timer to be safe
            log.debug(f"Hearts Ended, waiting for {thread_sleep_timer} seconds")
            time.sleep(thread_sleep_timer)
            thread_sleep_timer = None
        elif hearts_number >= 5 or hearts_loop_counter > 20:
            log.debug("Hearts maxed, small click test") #Try to skip the daily login bonus screen
            subprocess.Popen(f"adb -s localhost:5555 shell input tap {top_left[0]} {top_left[1]}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    except Exception as ex:
        log.debug(f"Error checking hearts number: {ex}")
        return

# def check_buttons_to_click(original_image):
#     global hearts_loop_counter, last_button_clicked
#     original_image = get_full_screenshot()
#     some_button_was_clicked = False
#     for image in Path(constants.ADB_AUTO_FOLDER).glob("*.png"):
#         image_path = image.as_posix()
#         if "return" in image.stem and some_button_was_clicked:
#             continue
#         if last_button_clicked == image_path:
#             last_button_clicked = None
#             continue
#         if check_button_and_click(original_image, image_path):
#             hearts_loop_counter = 0
#             last_button_clicked = image_path
#             some_button_was_clicked = True
#             original_image = get_full_screenshot()
#     if not some_button_was_clicked:
#         last_button_clicked = None
#         log.debug("No buttons found to be clicked")
#     return some_button_was_clicked 
# 
# def check_button_and_click(original_image, image_path, confidence=0.7, extra_timeout=2.0, click=True):
#     try:
#         template_image = cv2.imread(image_path)
#         top_left, board_bottom_right, probability = search_template(original_image, template_image)
#         if probability < confidence:
#             top_left, board_bottom_right, probability = search_template(original_image, custom_utils.resize_cv2_with_scale(template_image,104))
#             if probability < confidence:
#                 log.debug(f"Not Found: {image_path}")
#                 return False
#             else:
#                 log.debug(f"Found: {image_path} after rescaling")
#         else:
#             log.debug(f"Found: {image_path}")
#         if click:
#             x = math.floor((top_left[0] + board_bottom_right[0]) / 2)
#             y = math.floor((top_left[1] + board_bottom_right[1]) / 2)
#             subprocess.Popen(f"adb -s localhost:5555 shell input tap {x} {y}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
#             time.sleep(1.7)
#             if extra_timeout > 0:
#                 time.sleep(extra_timeout)
#         return True
#     except Exception as ex:
#         log.debug(f"Not Found: {image_path}")
#         return False

def check_buttons_to_click(original_image):
    global hearts_loop_counter
    was_clicked = not click_button_if_visible(original_image, "To Map") \
        and not click_button_if_visible(original_image, "Continue") \
        and not click_button_if_visible(original_image, "Start!", 4) \
        and not click_button_if_visible(original_image, "No") \
        and not click_stage_if_visible(original_image, "STAGE 37")
    if not was_clicked:
        hearts_loop_counter = 0


def click_stage_if_visible(original_image, stage, extra_timeout=1.0):
    resolution = get_screen_resolution()
    r = constants.RESOLUTIONS[resolution]["StageSelectionArea"]
    s = constants.STAGE_TO_IMAGE[stage]
    img = original_image.copy()
    img = img[r[1]:r[3], r[0]:r[2]]
    template = cv2.imread(f"D:/Git/Shuffle-Move/src/main/resources/img/icons/{s}.png")
    image_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(template_gray,None)
    kp2, des2 = sift.detectAndCompute(image_gray,None)

    MIN_MATCH_COUNT = 10
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1,des2,k=2)
    # store all the good matches as per Lowe's ratio test.
    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)
    if len(good)<MIN_MATCH_COUNT:
        print(f"Stage image not visible.")
        return False
    src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
    dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
    h,w = template_gray.shape
    pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
    dst = cv2.perspectiveTransform(pts,M)
    box = np.int0(cv2.boxPoints(cv2.minAreaRect(np.int32(dst))))

    # can comment out next 6 lines if dont wanna save image for debugging
    template_gray = cv2.polylines(template_gray,[np.int32(dst)], True,(255, 0, 0), 3)
    matchesMask = mask.ravel().tolist()
    draw_params = dict(matchColor = (0,255,0), # draw matches in green color
        singlePointColor = None,
        matchesMask = matchesMask, # draw only inliers
        flags = 2)
    cv2.drawContours(image_gray,[box],0,(0,0,255),2)
    img3 = cv2.drawMatches(template_gray,kp1,image_gray,kp2,good,None,**draw_params)
    cv2.imwrite(constants.STAGE_FLANN_IMAGE_PATH, img3)


    subprocess.Popen(f"adb shell input tap {r[0] + box[0][0] + math.floor(w/2)} {r[1] + box[0][1] + math.floor(h/2)}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    if extra_timeout > 0:
        time.sleep(extra_timeout)
    return True

def button_visible(original_image, text):
    resolution = get_screen_resolution()
    r = constants.RESOLUTIONS[resolution][text]
    img = original_image.copy()
    img = img[r[1]:r[3], r[0]:r[2]]
    img = 255 - cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #cv2.imshow("", img)
    result = pytesseract.image_to_string(img, lang='eng',config='--psm 6 --oem 3 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ! "').strip()
    return (result.upper() == text.upper(), r)

def click_button_if_visible(original_image, text, extra_timeout=1.0):
    visible, r = button_visible(original_image, text)
    if visible:
        subprocess.Popen(f"adb shell input tap {math.floor((r[0] + r[2])/2)} {math.floor((r[1] + r[3])/2)}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        time.sleep(extra_timeout)
    return visible
    

def search_template(main_image, template):
    result = cv2.matchTemplate(main_image, template, cv2.TM_CCOEFF_NORMED)

    min_val, max_probability, min_loc, max_loc = cv2.minMaxLoc(result)

    top_left = max_loc
    bottom_right = (top_left[0] + template.shape[1], top_left[1] + template.shape[0])

    return top_left, bottom_right, max_probability

# def has_match(original_image, template_path):
#     return check_button_and_click(original_image, template_path, click=False)

def get_current_stage(original_image):
    v = get_label(original_image, "Stage")
    if v.isnumeric():
        v = "{:03}".format(int(v))
    return v

def get_moves_left(original_image):
    return get_label(original_image, "MovesLeft")

def get_current_score(original_image):
    return get_label(original_image, "Score")

def get_label(original_image, label):
    resolution = get_screen_resolution()
    r = constants.RESOLUTIONS[resolution][label]
    img = original_image.copy()
    img = img[r[1]:r[3], r[0]:r[2]]
    img = 255 - cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #cv2.imshow("", img)
    result = pytesseract.image_to_string(img, lang='eng',config='--psm 6 --oem 3 -c tessedit_char_whitelist=":0123456789SPEX"').strip()
    return result

def has_board_active(original_image):
    return not button_visible(original_image, "No")[0] \
        and get_moves_left(original_image).isnumeric() \
        and get_current_score(original_image).isnumeric() \
        and get_current_stage(original_image).isnumeric()

def update_fog_image(index):
    cell_x0, cell_y0, cell_x1, cell_y1 = get_coordinates_from_board_index(index)
    center_x = math.floor((cell_x0 + cell_x1) / 2)
    center_y = math.floor((cell_y0 + cell_y1) / 2)
    subprocess.Popen(f"adb shell input swipe {center_x} {center_y} {center_x} {center_y} 1000", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    time.sleep(0.5)
    pipe = subprocess.Popen("adb shell screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
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
    