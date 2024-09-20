import os
import math
import cv2
from src import constants, icon_register, sleep_utils
from src.adb_commands import adb_run_screenshot, adb_run_swipe, adb_run_tap, update_adb_connection
from src.execution_variables import current_run
import numpy as np
import math
from src import config_utils
from src import custom_utils
import pyautogui
import time
import pytesseract
from src.screen_utils import get_screen
from pathlib import Path
from src import log_utils, file_utils
import re
log = log_utils.get_logger()


def get_new_screenshot():
    try:
        pil_screenshot = adb_run_screenshot()
        img = custom_utils.pil_to_cv2(pil_screenshot)

        cv2.imwrite(constants.LAST_SCREEN_IMAGE_PATH, img)
        current_run.abd_not_found_count = 0
        return img
    except:
        current_run.abd_not_found_count+= 1
        if current_run.abd_not_found_count >= 20:
            log.debug("Disabling Loop because adb wasn't found")
            custom_utils.send_telegram_message("Disabling Loop because adb wasn't found")
            current_run.disable_loop = True
        update_adb_connection(reconfigure_screen=True)
        raise


def crop_board(img):
    if not get_screen().loaded:
        update_adb_connection(True)
    img = img[get_screen().board_top_left[1]:get_screen().board_bottom_right[1], get_screen().board_top_left[0]:get_screen().board_bottom_right[0]].copy()
    cv2.imwrite(constants.LAST_BOARD_IMAGE_PATH, img)
    return img

def execute_play(result, board_results):
    try:
        adb_move = config_utils.config_values.get("adb_move")
        if result and adb_move:
            timed_play = custom_utils.is_timed_stage()
            wrong_board = "Wrong Board" in result
            zero_result = "0,0" in result
            if timed_play and (wrong_board or zero_result) and not current_run.last_execution_swiped:
                log.debug("Runing find_slot_to_mega crazy function")
                new_result = custom_utils.find_slot_to_mega(board_results)
                log.debug(f"Changing result from: {result}")
                log.debug(f"Changing result to: {new_result}")
                result = new_result
                wrong_board = False
                zero_result = False
            if not wrong_board and not zero_result:
                current_run.bad_board_count = 0
                red_row, red_column, blue_row, blue_column = custom_utils.extract_result_position(result)

                from_x = math.floor(get_screen().board_x + (get_screen().board_w * red_column) - (get_screen().board_w / 2))
                from_y = math.floor(get_screen().board_y + (get_screen().board_h * red_row) - (get_screen().board_w / 2))
                to_x = math.floor(get_screen().board_x + (get_screen().board_w * blue_column) - (get_screen().board_w / 2))
                to_y = math.floor(get_screen().board_y + (get_screen().board_h * blue_row) - (get_screen().board_w / 2))

                #The Idea of this one is to move not to the center of the cell, but a little more to the "end" of it, to
                #increase the chances that the swipe input will move to the correct cell and not one before it.
                new_to_x, new_to_y = move_second_point(from_x, from_y, to_x, to_y, get_screen().board_w/2.5, get_screen().board_h/2.5)
                adb_run_swipe(from_x, from_y, new_to_x, new_to_y, 350)
                current_run.last_swipe_timer = time.time()
                current_run.last_execution_swiped = True
                return True
            else:
                current_run.bad_board_count+= 1
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
    try:
        if custom_utils.is_coin_stage():
            log.debug("Coin Stage, skipping Hearts check")
            return
        if current_run.awakened_from_sleep:
            test_timer_out_of_sync()
            original_image = get_new_screenshot()
        hearts_number_str = get_hearts_number(original_image)
        current_run.hearts_loop_counter+= 1
        if not hearts_number_str.isnumeric():
            log.debug(f"Current Hearts amount is Unknown")
            return
        hearts_number = int(hearts_number_str)
        log.debug(f"Current Hearts amount is: {hearts_number}")
        if current_run.hearts_loop_counter > 20:
            log.debug("loop at 20, small click test") #Try to skip the daily login bonus screen
            adb_run_tap(get_screen().get_position('Hearts')[0], get_screen().get_position('Hearts')[1])
            current_run.hearts_loop_counter = 0
        if is_escalation_battle():
            escalation_hearts_processing(original_image, hearts_number)
        elif hearts_number < config_utils.config_values.get("stage_hearts", 1):
            wait_until_fill_hearts(original_image, hearts_number)
    except Exception as ex:
        log.debug(f"Error checking hearts number: {ex}")
        return

def test_timer_out_of_sync():
    current_stage_hearts = config_utils.config_values.get("stage_hearts", 1)
    log.info("Starting the check timer out of sync logic")
    while current_run.awakened_from_sleep:
        try:
            new_image = get_new_screenshot()
            hearts_number = int(get_hearts_number(new_image))
            hearts_timer = get_label(new_image, "HeartTimer")
            minutes, seconds = process_time(hearts_timer)
            current_sleep_counter = ((30 - int(minutes)) * 60) + int(seconds) + (hearts_number * 1800)
            if current_sleep_counter >= current_run.awakened_expected_counter and hearts_number >= current_stage_hearts:
                current_run.awakened_from_sleep = False
                log.info("Hearts ok, exitting")
                return
            log.info("Hearts number not ok, clicking on info and return icons")
            if has_icon_match(new_image, constants.INFO_ICON_IMAGE, extra_timeout=4, click=True, log_not_found=True):
                new_image = get_new_screenshot()
            if click_return_buttons(new_image, timeout_increase=4):
                new_image = get_new_screenshot()
            if click_ok_buttons(new_image, timeout_increase=4):
                new_image = get_new_screenshot()
            if has_text_match(new_image, "No", extra_timeout=4):
                new_image = get_new_screenshot()
            if has_text_match(new_image, "No2", extra_timeout=4, custom_search_text="No"):
                new_image = get_new_screenshot()
        except:
            pass


def get_hearts_number(original_image) -> str:
    hearts_number_unfiltered = get_label(original_image, "Hearts", '--psm 6 --oem 3 -c tessedit_char_whitelist="0123456789"')
    hearts_number_str = re.sub(r'\D', '', hearts_number_unfiltered)
    if hearts_number_str in ["7", "1"]:
        hearts_timer = get_label(original_image, "HeartTimer")
        minutes, seconds = process_time(hearts_timer)
        if minutes or seconds:
            hearts_number_str = "1"
    return hearts_number_str

def escalation_hearts_processing(original_image, hearts_number):
    if is_angry_active():
        if hearts_number == 0:
            wait_until_fill_hearts(original_image, hearts_number, 1)
        else:
            return
    elif hearts_number > 1:
        return
    else:
        verify_angry_mode(original_image, max_retries=1)
        if is_angry_active():
            return escalation_hearts_processing(original_image, hearts_number)

        start_with_n_minutes = 7
        
        if custom_utils.is_timed_stage():
            start_with_n_minutes = 10

        #The idea here is wait until has 1 life and 7 minutes waiting for the next.. then play the stage
        #On the next cycle, if the angry mode is activated it will wait until the next life, play and repeat.
        hearts_timer = get_label(original_image, "HeartTimer")
        minutes, seconds = process_time(hearts_timer)
        seconds_to_next_heart = int(minutes) * 60 + int(seconds) + 5
        seconds_to_n_minutes_until_next_heart = seconds_to_next_heart - (start_with_n_minutes * 60 )
        time_to_wait = seconds_to_n_minutes_until_next_heart
        if hearts_number == 0:
            time_to_wait+= 1800
        time_to_wait = max(time_to_wait, 0) # Avoid negative number when there's less than 5 minutes to next life.
        current_run.thread_sleep_timer = int(time_to_wait)
        log.debug(f"Escalation Hearts Management: Waiting until {time.strftime('%H:%M:%S', time.localtime(time.time() + current_run.thread_sleep_timer))} ({current_run.thread_sleep_timer / 60}) minutes")
        current_run.awakened_expected_counter = 1800 + ((30 - 7) * 60)
        sleep_utils.make_it_sleep(current_run.thread_sleep_timer, hearts_number)
        log.debug("Escalation sleep ended, continuing")
        current_run.thread_sleep_timer = 0

def process_time(mystring):
    try:
        return re.findall(custom_utils.time_pattern, mystring)[0]
    except:
        log.error(f"Hearts Timer problem, original string: {mystring}")
        return 0, 0

def is_angry_active():
    return current_run.angry_mode_active

def wait_until_fill_hearts(original_image, current_hearts, aimed_hearts=2):
    hearts_timer = get_label(original_image, "HeartTimer")
    minutes, seconds = process_time(hearts_timer)
    current_run.thread_sleep_timer = (int(minutes) * 60) + int(seconds) + 5 + ((aimed_hearts - current_hearts - 1) * 30 * 60)
    log.debug(f"Hearts Ended, waiting until {time.strftime('%H:%M:%S', time.localtime(time.time() + current_run.thread_sleep_timer))} ({current_run.thread_sleep_timer / 60}) minutes")

    current_run.awakened_expected_counter = aimed_hearts * 1800
    sleep_utils.make_it_sleep(current_run.thread_sleep_timer, current_hearts)
    current_run.thread_sleep_timer = 0

def is_escalation_battle():
    return config_utils.config_values.get("escalation_battle")

def check_buttons_to_click(original_image):
    was_clicked = False
    
    if custom_utils.is_timed_stage():
        timeout_increase = 5
    else:
        timeout_increase = 0

    if (current_run.non_stage_count % 5 == 0):
        click_ok_buttons(original_image, timeout_increase)
        click_return_buttons(original_image, timeout_increase)

    if current_run.non_stage_count > 5:
        run_capture_logic_test(original_image)

    current_stage_image_path = constants.CURRENT_STAGE_IMAGE
    if custom_utils.is_meowth_stage():
        current_stage_image_path = constants.MEOWTH_STAGE_IMAGE
    elif custom_utils.is_survival_mode():
        current_stage_image_path = constants.SURVIVAL_MODE_STAGE_IMAGE
    if has_icon_match(original_image, current_stage_image_path, extra_timeout=1+timeout_increase, click=True, min_point=40, log_not_found=True):
        was_clicked = True
        original_image = get_new_screenshot()
    if has_text_match(original_image, "To Map", extra_timeout=1+timeout_increase):
        if custom_utils.is_meowth_stage():
            os.makedirs(constants.MEOWTH_DEBUG_IMAGE_FOLDER, exist_ok=True)
            cv2.imwrite(os.path.join(constants.MEOWTH_DEBUG_IMAGE_FOLDER,f"{time.strftime('%Y_%m_%d_%H_%M')}.png") ,original_image)
        was_clicked = True
        original_image = get_new_screenshot()
    if has_text_match(original_image, "Continue", extra_timeout=1+timeout_increase):
        was_clicked = True
        original_image = get_new_screenshot()
    if has_text_match(original_image, "Start!", 1):
        was_clicked = True
        original_image = get_new_screenshot()
    if has_text_match(original_image, "Next", extra_timeout=1):
        was_clicked = True
        original_image = get_new_screenshot()
    if custom_utils.is_coin_stage() or config_utils.config_values.get("stage_hearts",1) == 2:
        if has_text_match(original_image, "CoinStage", custom_click="CoinStageYes", extra_timeout=1, custom_search_text="need to spend"):
            was_clicked = True
            original_image = get_new_screenshot()
    if custom_utils.is_survival_mode():
        if has_text_match(original_image, "CoinStage", custom_click="CoinStageYes", extra_timeout=1, custom_search_text="challenging survival"):
            was_clicked = True
            original_image = get_new_screenshot()  
    if has_text_match(original_image, "No", extra_timeout=1+timeout_increase):
        was_clicked = True
        original_image = get_new_screenshot()
    if has_text_match(original_image, "No2", extra_timeout=1+timeout_increase, custom_search_text="No"):
        was_clicked = True
        original_image = get_new_screenshot()
    if click_ok_buttons(original_image, timeout_increase):
        was_clicked = True
        original_image = get_new_screenshot()
    if has_text_match(original_image, "Close", extra_timeout=1+timeout_increase):
        was_clicked = True
        original_image = get_new_screenshot()
        return click_return_buttons(original_image, timeout_increase)
    if has_text_match(original_image, "Close2", extra_timeout=1+timeout_increase, custom_search_text="Close"):
        was_clicked = True
        original_image = get_new_screenshot()
        return click_return_buttons(original_image, timeout_increase)
    if not was_clicked:
        return click_return_buttons(original_image, timeout_increase)
    if was_clicked:
        current_run.hearts_loop_counter = 0
    return

def click_ok_buttons(original_image, timeout_increase):
    if has_icon_match(original_image, constants.OK_BUTTON_IMAGE, extra_timeout=1+timeout_increase, click=True, log_not_found=True):
        return True
    if has_icon_match(original_image, constants.OK_BUTTON2_IMAGE, extra_timeout=1+timeout_increase, click=True, log_not_found=True):
        return True
    return False

def click_return_buttons(original_image, timeout_increase):
    if has_icon_match(original_image, constants.RETURN_FLAG_IMAGE, extra_timeout=1+timeout_increase, click=True, log_not_found=True):
        return True
    if has_icon_match(original_image, constants.RETURN_FLAG2_IMAGE, extra_timeout=1+timeout_increase, click=True, log_not_found=True):
        return True

def verify_angry_mode(original_image, retry_count=0, max_retries=0):
    if current_run.angry_mode_active:
        return
    
    if current_run.last_stage_had_anger:
        log.info("Since the last stage was already angered, the current one can't be. This is a test to avoid false positives on the stage cleared screen.")
        return
    
    is_angry = has_icon_match(original_image, constants.ANGRY_ICON_IMAGE, log_not_found=True) or has_icon_match(original_image, constants.ANGRY_ICON2_IMAGE, log_not_found=True)
    is_angry_text = has_text_match(original_image, "Angry", custom_search_text="grew angry")
    
    if is_angry or is_angry_text:
        current_run.angry_mode_active = True
        log.info("Angry Mode is ACTIVE")
        custom_utils.send_telegram_message("Angry Mode is ACTIVE")
        return
    
    if retry_count < max_retries:
        time.sleep(5)
        new_image = get_new_screenshot()
        verify_angry_mode(new_image, retry_count + 1, max_retries)
    return

def run_capture_logic_test(original_image):
    try:
        if get_moves_left(original_image) == "0":
            if has_icon_match(original_image, constants.POKEBALL_CAPTURE_IMAGE, "Pokeball Capture", min_point=30, log_not_found=True):
                time.sleep(4)
                log.info("found_capture_icon and clicked")
                current_run.non_stage_count = 0
            else:
                log.info("capture_pokeball_not_found, checking for Great Ball")
                if custom_utils.use_great_ball():
                    has_text_match(original_image, "Greatball", custom_click="GreatballYes", custom_search_text="Do you want to use 3500 Coins")
                    time.sleep(4)
                else:
                    has_text_match(original_image, "Greatball", custom_click="GreatballNo", custom_search_text="Do you want to use 3500 Coins")
                    time.sleep(4)
    except Exception as ex:
        log.error(f"Erro: {ex}")
        pass

def has_icon_match(original_image, icon_path, position="CompleteScreen", extra_timeout=1.0, click=True, min_point=10, debug=False, double_checked=False, log_not_found=False):
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
            if log_not_found:
                log.debug(f"Image not visible: {Path(icon_path).stem} - {len(good)} points found")
            return False
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2) #type: ignore
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2) #type: ignore
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        h,w = template_gray.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2) #type: ignore
        dst = cv2.perspectiveTransform(pts,M)
        box = np.intp(cv2.boxPoints(cv2.minAreaRect(np.int32(dst)))) #type: ignore

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

        if click and not double_checked:
            return has_icon_match(get_new_screenshot(), icon_path, position, extra_timeout, click, min_point, debug, double_checked=True, log_not_found=log_not_found) #Add a double-check with a new ScreenShot before the click
        if double_checked:
            log.debug(f"Image Found with points: {Path(icon_path).stem} - {len(good)}")
        if click and double_checked:
            box_center_x = int((box[0][0] + box[2][0]) / 2)
            box_center_y = int((box[0][1] + box[2][1]) / 2)
            adb_run_tap(r[0] + box_center_x ,r[1] + box_center_y)
            if extra_timeout > 0:
                time.sleep(extra_timeout)
        return True
    except:
        return False

def text_visible(original_image, text, custom_click=None, custom_search_text=None, should_print=True):
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
    if found_text and should_print:
        if custom_search_text:
            log.debug(f"Text Found for {custom_search_text} -> {result.strip()} - alternative {result2.strip()}")
        else:
            log.debug(f"Text Found for {text}: {result.strip()} - alternative {result2.strip()}")
    return found_text, postition

def has_text_match(original_image, text, extra_timeout=1.0, click=True, custom_click=None, custom_search_text=None, double_checked=False):
    visible, r = text_visible(original_image, text, custom_click, custom_search_text, should_print=double_checked)
    if visible and click:
        debug_image_path = Path(constants.ADB_IMAGE_FOLDER, "debug", f"{text}.png")
        if not debug_image_path.exists():
            final_img = original_image.copy()
            cv2.rectangle(final_img, (r[0], r[1]), (r[2], r[3]), (0, 0, 255), 4)
            debug_image_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(debug_image_path.as_posix(), final_img)
        if not double_checked:
            has_text_match(get_new_screenshot(), text, extra_timeout, click, custom_click, custom_search_text, double_checked=True)
        else:
            adb_run_tap(math.floor((r[0] + r[2])/2), math.floor((r[1] + r[3])/2))
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

def get_current_stage_name(original_image):
    v = get_label(original_image, "StageName")
    if v.isnumeric():
        v = "{:03}".format(int(v))
    return v

def get_end_stage_score(original_image):
    v = get_label(original_image, "EndStageScore")
    if v.isnumeric():
        v = "{:03}".format(int(v))
    return v

def get_end_stage_coins(original_image):
    v = get_label(original_image, "EndStageCoins")
    if v.isnumeric():
        v = "{:03}".format(int(v))
    return v

def get_moves_left(original_image):
    moves = get_label(original_image, "MovesLeft")
    if ":" in moves:
        _, seconds = process_time(moves)
        seconds = int(seconds)
        if seconds == 0:
            moves = "0"
        if seconds <= 3:
            moves = "1"
        elif seconds <= 10:
            moves = "3"
        elif seconds > 10:
            moves = str(seconds)
        else:
            moves = "0"
    return moves

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
    adb_run_swipe(center_x, center_y, center_x, center_y, 1000)
    time.sleep(0.5)
    screenshot_data = adb_run_screenshot()
    screenshot_array = np.frombuffer(screenshot_data, np.uint8)
    img = cv2.imdecode(screenshot_array, cv2.IMREAD_COLOR)
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
    adb_run_tap(center_x, center_y)
    time.sleep(0.1)
    return center_x, center_y

def get_coordinates_from_board_index(idx):
    row, column = custom_utils.index_to_coordinates(idx)

    cell_x0 =  math.floor(get_screen().board_x + (get_screen().board_w * (column - 1)))
    cell_y0 =  math.floor(get_screen().board_y + (get_screen().board_h * (row - 1)))
    cell_x1 =  math.floor(get_screen().board_x + (get_screen().board_w * (column)))
    cell_y1 =  math.floor(get_screen().board_y + (get_screen().board_h * (row)))
    return cell_x0,cell_y0,cell_x1,cell_y1

def check_if_has_drops(original_image):
    return has_icon_match(original_image, constants.DROP_IMAGE, "Drops", extra_timeout=0, click=False, min_point=8)
