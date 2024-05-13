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
from src import screen_utils
from src.screen_utils import get_screen
from pathlib import Path
from src import log_utils
import re

log = log_utils.get_logger()
adb_shell_command = "adb shell"
angry_mode_active = False
time_pattern = re.compile(r"\b(\d{1,2})\s*:\s*(\d{1,2})\b")


def configure_adb():
    global adb_shell_command
    pipe = subprocess.Popen(f"{adb_shell_command} wm size",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    output = str(pipe.stdout.read()) #type: ignore
    if output.startswith("b'Physical size"):
        log.info(output)
        return
    else:
        pipe = subprocess.Popen("adb kill-server",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output = str(pipe.stdout.read()) #type: ignore
        pipe = subprocess.Popen("adb connect localhost:5555",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output = str(pipe.stdout.read()) #type: ignore
        adb_shell_command = "adb -s localhost:5555 shell"
        pipe = subprocess.Popen(f"{adb_shell_command} wm size",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output = str(pipe.stdout.read()) #type: ignore
        log.info(output)
        return

def configure_screen():
    global adb_shell_command
    pipe = subprocess.Popen(f"{adb_shell_command} wm size",stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    response = str(pipe.stdout.read()).strip() #type: ignore
    resolution = re.findall(r"\b\d{2,4}\s*x\s*\d{2,4}\b", response)[0]
    screen_utils.update_screen(constants.RESOLUTIONS[resolution])
    

configure_adb()
configure_screen()
thread_sleep_timer = None
hearts_loop_counter = 0
last_button_clicked = None

def get_screenshot():
    global adb_shell_command
    pipe = subprocess.Popen(f"{adb_shell_command} screencap -p", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n') #type: ignore
    img = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR) #type: ignore
    cv2.imwrite(constants.LAST_SCREEN_IMAGE_PATH, img)
    return img

def crop_board(img):
    img = img[get_screen().board_top_left[1]:get_screen().board_bottom_right[1], get_screen().board_top_left[0]:get_screen().board_bottom_right[0]].copy()
    cv2.imwrite(constants.LAST_BOARD_IMAGE_PATH, img)
    return img

def execute_play(result, board_results, last_execution_swiped):
    global adb_shell_command
    try:
        adb_move = config_utils.config_values.get("adb_move")
        if result and adb_move:
            timed_play = custom_utils.is_timed_stage()
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

                from_x = math.floor(get_screen().board_x + (get_screen().board_w * red_column) - (get_screen().board_w / 2))
                from_y = math.floor(get_screen().board_y + (get_screen().board_h * red_row) - (get_screen().board_w / 2))
                to_x = math.floor(get_screen().board_x + (get_screen().board_w * blue_column) - (get_screen().board_w / 2))
                to_y = math.floor(get_screen().board_y + (get_screen().board_h * blue_row) - (get_screen().board_w / 2))

                #The Idea of this one is to move not to the center of the cell, but a little more to the "end" of it, to
                #increase the chances that the swipe input will move to the correct cell and not one before it.
                new_to_x, new_to_y = move_second_point(from_x, from_y, to_x, to_y, get_screen().board_w/2.5, get_screen().board_h/2.5)

                subprocess.Popen(f"{adb_shell_command} input swipe {from_x} {from_y} {new_to_x} {new_to_y} 350", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                time.sleep(1.0)
                return True
    except Exception as ex:
        log.error(f"Error on execute_play: {ex}")
    return False

def move_second_point(x0_initial, y0_initial, x1_initial, y1_initial, x_offset, y_offset):
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

def check_if_close_to_same_color(pixel1, pixel2, threshold=10):
  diff = np.subtract(pixel1, pixel2)
  return np.all(np.abs(diff) < threshold)

def check_hearts(original_image):
    global thread_sleep_timer, hearts_loop_counter, adb_shell_command
    try:
        hearts_number_unfiltered = get_label(original_image, "Hearts", '--psm 6 --oem 3 -c tessedit_char_whitelist="0123456789"')
        hearts_number_str = re.sub(r'\D', '', hearts_number_unfiltered)
        if hearts_number_str == "7":
            hearts_timer = get_label(original_image, "HeartTimer")
            minutes, seconds = process_time(hearts_timer)
            if minutes or seconds:
                hearts_number_str = "1"
        hearts_loop_counter+= 1
        if not hearts_number_str.isnumeric():
            log.debug(f"Current Hearts amount is Unknown")
            return
        hearts_number = int(hearts_number_str)
        log.debug(f"Current Hearts amount is: {hearts_number}")
        if not is_escalation_battle() and hearts_number == 0:
            wait_until_next_heart(original_image)
        elif hearts_number >= 5 or hearts_loop_counter > 20:
            log.debug("Hearts maxed, small click test") #Try to skip the daily login bonus screen
            subprocess.Popen(f"{adb_shell_command} input tap {get_screen().get_position('Hearts')[0]} {get_screen().get_position('Hearts')[1]}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        elif is_escalation_battle() and is_angry_active():
            if hearts_number == 0:
                wait_until_next_heart(original_image)
        elif is_escalation_battle() and hearts_number <= 1:
            #The idea here is wait until has 1 life and 5 minutes waiting for the next.. then play the stage
            #On the next cycle, if the angry mode is activated it will wait until the next life, play and repeat.
            hearts_timer = get_label(original_image, "HeartTimer")
            minutes, seconds = process_time(hearts_timer)
            seconds_to_next_heart = int(minutes) * 60 + int(seconds) + 5
            seconds_to_5_minutes_until_next_heart = seconds_to_next_heart - 540
            time_to_wait = seconds_to_5_minutes_until_next_heart
            if hearts_number == 0:
                time_to_wait+= 1800
            time_to_wait = max(time_to_wait, 0) # Avoid negative number when there's less than 5 minutes to next life.
            thread_sleep_timer = int(time_to_wait)
            log.debug(f"Hearts Ended, waiting for {thread_sleep_timer} seconds - ESCALATION BATTLE TEST")
            time.sleep(thread_sleep_timer)
            log.debug("Sleep ended, continuing")
            thread_sleep_timer = None       
    except Exception as ex:
        log.debug(f"Error checking hearts number: {ex}")
        return

def process_time(mystring):
    try:
        return re.findall(time_pattern, mystring)[0]
    except:
        log.error(f"Hearts Timer problem, original string: {mystring}")
        return None, None

def is_angry_active():
    global angry_mode_active
    return angry_mode_active

def wait_until_next_heart(original_image):
    global thread_sleep_timer
    hearts_timer = get_label(original_image, "HeartTimer")
    minutes, seconds = process_time(hearts_timer)
    thread_sleep_timer = int(minutes) * 60 + int(seconds) + 5
    log.debug(f"Hearts Ended, waiting for {thread_sleep_timer} seconds")
    time.sleep(thread_sleep_timer)
    thread_sleep_timer = None

def is_escalation_battle():
    return config_utils.config_values.get("escalation_battle")

def check_buttons_to_click(original_image, non_stage_count):
    global hearts_loop_counter
    was_clicked = False
    
    if custom_utils.is_timed_stage():
        timeout_increase = 3
    else:
        timeout_increase = 0

    if non_stage_count > 60:
        click_return_buttons(original_image, timeout_increase)

    if has_icon_match(original_image, constants.CURRENT_STAGE_IMAGE, extra_timeout=1+timeout_increase, click=True):
        was_clicked = True
        original_image = get_screenshot()
    if was_clicked and is_escalation_battle():
        verify_angry_mode(original_image, double_try=True)
    if has_text_match(original_image, "To Map", extra_timeout=1+timeout_increase):
        was_clicked = True
        original_image = get_screenshot()
    if has_text_match(original_image, "Continue", extra_timeout=1+timeout_increase):
        was_clicked = True
        original_image = get_screenshot()
    if has_text_match(original_image, "Start!", 4):
        was_clicked = True
        original_image = get_screenshot()
    if has_text_match(original_image, "Next", 4):
        was_clicked = True
        original_image = get_screenshot()
    if config_utils.config_values.get("coin_stage"):
        if has_text_match(original_image, "CoinStage", custom_click="CoinStageYes", custom_search_text="need to spend"):
            was_clicked = True
            original_image = get_screenshot()
    if has_text_match(original_image, "No", extra_timeout=1+timeout_increase):
        was_clicked = True
        original_image = get_screenshot()
    if has_text_match(original_image, "No2", extra_timeout=1+timeout_increase, custom_search_text="No"):
        was_clicked = True
        original_image = get_screenshot()
    if not was_clicked:
        return click_return_buttons(original_image, timeout_increase)
    if was_clicked:
        hearts_loop_counter = 0
    return

def click_return_buttons(original_image, timeout_increase):
    return not has_icon_match(original_image, constants.OK_BUTTON_IMAGE, extra_timeout=1+timeout_increase, click=True) \
                and not has_icon_match(original_image, constants.OK_BUTTON2_IMAGE, extra_timeout=1+timeout_increase, click=True) \
                and not has_icon_match(original_image, constants.RETURN_FLAG_IMAGE, extra_timeout=1+timeout_increase, click=True) \
                and not has_icon_match(original_image, constants.RETURN_FLAG2_IMAGE, extra_timeout=1+timeout_increase, click=True)
def verify_angry_mode(original_image, double_try=False):
    global angry_mode_active
    is_angry = has_icon_match(original_image, constants.ANGRY_ICON_IMAGE) or has_icon_match(original_image, constants.ANGRY_ICON2_IMAGE)
    if is_angry:
        angry_mode_active = True
        log.info("Angry Mode is ACTIVE")
        return
    elif double_try:
        time.sleep(5)
        original_image = get_screenshot()
        is_angry = has_icon_match(original_image, constants.ANGRY_ICON_IMAGE) or has_icon_match(original_image, constants.ANGRY_ICON2_IMAGE)
        if is_angry:
            angry_mode_active = True
            log.info("Angry Mode is ACTIVE")
            return
    return
    
def has_icon_match(original_image, icon_path, position="CompleteScreen", extra_timeout=1.0, click=True, min_point=10, debug=False):
    global adb_shell_command
    try:
        r = get_screen().get_position(position)
        img = original_image.copy()
        img = img[r[1]:r[3], r[0]:r[2]]
        template = cv2.imread(icon_path)
        image_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        sift = cv2.SIFT_create() #type: ignore
        kp1, des1 = sift.detectAndCompute(template_gray,None)
        kp2, des2 = sift.detectAndCompute(image_gray,None)
        MIN_MATCH_COUNT = min_point
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        search_params = dict(checks = 50)
        flann = cv2.FlannBasedMatcher(index_params, search_params) #type: ignore
        matches = flann.knnMatch(des1,des2,k=2)
        # store all the good matches as per Lowe's ratio test.
        good = []
        for m,n in matches:
            if m.distance < 0.7*n.distance:
                good.append(m)
        if len(good)<MIN_MATCH_COUNT:
            log.debug(f"Image not visible: {Path(icon_path).stem} - {len(good)} point found")
            return False
        log.debug(f"Image Found with points: {Path(icon_path).stem} - {len(good)}")
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2) #type: ignore
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2) #type: ignore
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        h,w = template_gray.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2) #type: ignore
        dst = cv2.perspectiveTransform(pts,M)
        box = np.int0(cv2.boxPoints(cv2.minAreaRect(np.int32(dst)))) #type: ignore

        if debug:
            template_gray = cv2.polylines(template_gray,[np.int32(dst)], True,(255, 0, 0), 3) #type: ignore
            matchesMask = mask.ravel().tolist()
            draw_params = dict(matchColor = (0,255,0), # draw matches in green color
                singlePointColor = None,
                matchesMask = matchesMask, # draw only inliers
                flags = 2)
            cv2.drawContours(image_gray,[box],0,(0,0,255),2)
            img3 = cv2.drawMatches(template_gray,kp1,image_gray,kp2,good,None,**draw_params) #type: ignore
            cv2.imwrite(constants.STAGE_FLANN_IMAGE_PATH, img3)

        debug_image_path = Path(constants.ADB_IMAGE_FOLDER, "debug", Path(icon_path).name)
        if not debug_image_path.exists():
            new_box = box + np.array([r[0], r[1]])
            final_img = original_image.copy()
            cv2.drawContours(final_img,[new_box],0,(0,0,255),4)
            debug_image_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(debug_image_path.as_posix(), final_img)

        if click:
            box_center_x = int((box[0][0] + box[2][0]) / 2)
            box_center_y = int((box[0][1] + box[2][1]) / 2)
            subprocess.Popen(f"{adb_shell_command} input tap {r[0] + box_center_x} {r[1] + box_center_y}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            if extra_timeout > 0:
                time.sleep(extra_timeout)
        return True
    except:
        return False

def text_visible(original_image, text, custom_click=None, custom_search_text=None):
    global adb_shell_command
    r = get_screen().get_position(text)
    img = original_image.copy()
    img = img[r[1]:r[3], r[0]:r[2]]
    img = 255 - cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = pytesseract.image_to_string(img, lang='eng').strip()
    result2 = pytesseract.image_to_string(img, lang='eng', config='--psm 6').strip()
    if custom_click:
        r = get_screen().get_position(custom_click)
    if custom_search_text:
        found_text, postition = (custom_search_text.upper() in result.upper(), r)
    else:
        found_text, postition = (text.upper() in result.upper(), r)
    if found_text:
        if custom_search_text:
            log.debug(f"Text Found for {custom_search_text} -> {result.strip()} - alternative {result2.strip()}")
        else:
            log.debug(f"Text Found for {text}: {result.strip()} - alternative {result2.strip()}")
    return found_text, postition

def has_text_match(original_image, text, extra_timeout=1.0, click=True, custom_click=None, custom_search_text=None):
    visible, r = text_visible(original_image, text, custom_click, custom_search_text)
    if visible and click:

        debug_image_path = Path(constants.ADB_IMAGE_FOLDER, "debug", f"{text}.png")
        if not debug_image_path.exists():
            final_img = original_image.copy()
            cv2.rectangle(final_img, (r[0], r[1]), (r[2], r[3]), (0, 0, 255), 4)
            debug_image_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(debug_image_path.as_posix(), final_img)

        subprocess.Popen(f"{adb_shell_command} input tap {math.floor((r[0] + r[2])/2)} {math.floor((r[1] + r[3])/2)}", stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        if extra_timeout:
            time.sleep(extra_timeout)
    return visible
    

def search_template(main_image, template):
    result = cv2.matchTemplate(main_image, template, cv2.TM_CCOEFF_NORMED)

    min_val, max_probability, min_loc, max_loc = cv2.minMaxLoc(result)

    top_left = max_loc
    bottom_right = (top_left[0] + template.shape[1], top_left[1] + template.shape[0])

    return top_left, bottom_right, max_probability

def get_current_stage(original_image):
    v = get_label(original_image, "Stage")
    if v.isnumeric():
        v = "{:03}".format(int(v))
    return v

def get_current_stage2(original_image):
    v = get_label(original_image, "StageName")
    if v.isnumeric():
        v = "{:03}".format(int(v))
    return v

def get_moves_left(original_image):
    return get_label(original_image, "MovesLeft")

def get_current_score(original_image):
    return get_label(original_image, "Score")

def get_label(original_image, label, config=""):
    r = get_screen().get_position(label)
    return get_label_with_tuple(original_image, r, config)

def get_label_with_tuple(original_image, r, config=""):
    img = original_image.copy()
    img = img[r[1]:r[3], r[0]:r[2]]
    img = 255 - cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = pytesseract.image_to_string(img, lang='eng', config="").strip()
    if not result:
        result = pytesseract.image_to_string(img, lang='eng',config='--psm 6').strip()
    return result

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

    cell_x0 =  math.floor(get_screen().board_x + (get_screen().board_w * (column - 1)))
    cell_y0 =  math.floor(get_screen().board_y + (get_screen().board_h * (row - 1)))
    cell_x1 =  math.floor(get_screen().board_x + (get_screen().board_w * (column)))
    cell_y1 =  math.floor(get_screen().board_y + (get_screen().board_h * (row)))
    return cell_x0,cell_y0,cell_x1,cell_y1
    