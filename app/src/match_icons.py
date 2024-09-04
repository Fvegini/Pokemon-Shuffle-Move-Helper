from typing import List
import cv2
import numpy as np
from pathlib import Path
from src.embed import loaded_embedder
from src import constants, custom_utils, config_utils, socket_utils, shuffle_config_files, adb_utils, log_utils, file_utils, tapper_utils
from src.execution_variables import current_run
from src.classes import Icon, Match, Pokemon, MatchResult, Board
import statistics
import time
import os
import shutil

log = log_utils.get_logger()

loaded_icons_cache: dict[str, Icon] = {}
fixed_tuple_positions = [("None", 7), ("None", 10)]

def load_icon_classes(values_to_execute: list[Pokemon], has_barriers):
    icons_list = []
    if not loaded_icons_cache:
        log.debug("Icons Cache is Empty, starting a new one")
    for pokemon in values_to_execute:
        if pokemon.disabled:
            continue
        if pokemon.name in loaded_icons_cache:
            icons_list.append(loaded_icons_cache.get(pokemon.name))
        else:
            new_icon = Icon(pokemon.name, pokemon.path, False)
            icons_list.append(new_icon)
            loaded_icons_cache[new_icon.name] = new_icon
        if has_barriers and not custom_utils.is_fake_barrier_active():
            pokemon_barrier_name = f"{constants.BARRIER_PREFIX}{pokemon.name}"
            if pokemon_barrier_name in loaded_icons_cache:
                icons_list.append(loaded_icons_cache.get(pokemon_barrier_name))
            else:
                new_icon = Icon(pokemon.name, pokemon.path, True)
                icons_list.append(new_icon)
                loaded_icons_cache[new_icon.name] = new_icon
    return icons_list


def change_filename_in_path(original_path, new_filename="", suffix="", prefix=""):
    if isinstance(original_path, str):
        custom_path = Path(original_path)
    elif isinstance(original_path, Path):
        custom_path = original_path
    else:
        raise Exception("Incorrect Path")
    filename_without_extension = custom_path.stem
    if new_filename:
        return custom_path.with_name(f"{new_filename}{custom_path.suffix}")
    else:
        if suffix:
            return  custom_path.with_name(f"{filename_without_extension}{suffix}{custom_path.suffix}")
        if prefix:
            return custom_path.with_name(f"{prefix}{filename_without_extension}{custom_path.suffix}")
    

def cut_borders(image, border_size=5):
    # Get image dimensions
    height, width = image.shape[:2]

    # Specify the region to keep (excluding the border)
    top = border_size
    bottom = height - border_size
    left = border_size
    right = width - border_size

    # Crop the image
    cropped_image = image[top:bottom, left:right]

    return cropped_image


def compare_with_list(original_image, icons_list: List[Icon], has_barriers):
    embed = loaded_embedder.create_embed_from_np(original_image)
    best_match = None
    full_match_list_tmp = []
    for icon in icons_list:
        match = Match(original_image, embed, icon)
        full_match_list_tmp.append(match)
        if not best_match or best_match.cosine_similarity < match.cosine_similarity:
            best_match = match
    if has_barriers and custom_utils.is_fake_barrier_active():
        fake_barrier_img = custom_utils.resize_cv2_image(cut_borders(original_image), constants.downscale_res)
        is_barrier = has_white_border(fake_barrier_img)
        if is_barrier:
            best_match.name = f"{constants.BARRIER_PREFIX}{best_match.name}" #type: ignore
            best_match.match_icon = custom_utils.add_transparent_image(best_match.match_icon) #type: ignore
    return best_match

def has_white_border(image, threshold=170, border_size=10, debug=False):
    # height, width = image.shape[:2]
    if debug:
        top_border_img = image[:border_size, :]
        bottom_border_img = image[-border_size:, :]
        left_border_img = image[:, :border_size]
        right_border_img = image[:, -border_size:]

        top_border_mean = np.mean(top_border_img)
        bottom_border_mean = np.mean(bottom_border_img)
        left_border_mean = np.mean(left_border_img)
        right_border_mean = np.mean(right_border_img)
        
        log.debug(top_border_mean, bottom_border_mean, left_border_mean, right_border_mean)
        
        file_utils.show_cv2_as_pil(top_border_img)
        file_utils.show_cv2_as_pil(bottom_border_img)
        file_utils.show_cv2_as_pil(left_border_img)
        file_utils.show_cv2_as_pil(right_border_img)

    top_border = np.mean(image[:border_size, :])  > threshold
    bottom_border = np.mean(image[-border_size:, :]) > threshold
    left_border = np.mean(image[:, :border_size]) > threshold
    right_border = np.mean(image[:, -border_size:]) > threshold

    return [top_border, bottom_border, left_border, right_border].count(True) >= 3 


def calculate_percentage_difference(num1, num2):
    average = (num1 + num2) / 2
    percentage_difference = abs((num1 - num2) / average) * 100
    return percentage_difference

def predict(original_image, icons_list, has_barriers) -> Match:
    resized = cv2.resize(original_image, constants.downscale_res)
    return compare_with_list(resized, icons_list, has_barriers)

def make_cell_list(forced_board_image=None):
    if forced_board_image is None:
        img = custom_utils.capture_board_screensot()
        return custom_utils.make_cell_list_from_img(img)
    else:
        return custom_utils.make_cell_list_from_img(forced_board_image)

def get_metrics(match_list):
    numbers_list = [match.cosine_similarity for match in match_list]
    return {
    "maximum": max(numbers_list),
    "minimum": min(numbers_list),
    "median": statistics.median(numbers_list),
    "variance": statistics.variance(numbers_list),
    }

def handle_skip_shuffle_move(icons_list, forced_board_image, has_barriers):
    return MatchResult(match_list=match_cell_with_icons(icons_list, make_cell_list(forced_board_image), has_barriers, True))

def verify_or_enter_stage(current_screen_image):
    if is_on_stage(current_screen_image):
        current_run.is_combo_active = verify_active_combo(current_screen_image)
    else:
        if should_auto_next_stage():
            click_buttons_to_enter_new_stage(current_screen_image)
        else:
            current_run.auto_disabled_count+= 1
            log.debug("Stage isn't active and next stage is disabled")
            if current_run.auto_disabled_count > 20:
                log.debug("Disabling Loop because auto next stage is disabled")
                current_run.disable_loop = True
        return MatchResult()
    return None

def initialize_run_flags():
    current_run.mega_activated_this_round = False
    current_run.last_execution_swiped = False

def verify_and_execute_tapper(source, current_board: Board):
    if custom_utils.is_tapper_active() and int(current_board.moves_left) > 0:
        executed_tapper = execute_tapper(current_board, source)
        return executed_tapper
    return False

def update_board_with_stage_parameters(current_screen_image, current_board):
    current_board.moves_left = adb_utils.get_moves_left(current_screen_image)
    log.debug(f"Stage Moves Left: {current_board.moves_left}")
    if not custom_utils.is_timed_stage():
        if custom_utils.is_meowth_stage():
            current_board.current_score = adb_utils.get_current_score(current_screen_image)
        if custom_utils.is_survival_mode():
            current_board.stage_name = adb_utils.get_current_stage_name(current_screen_image)

def save_debug_objects(result="", match_list=[], is_manual=False):
    try:
        if is_manual:
            session_folder = Path(constants.DEBUG_STAGES_IMAGE_FOLDER, "manual")
            os.makedirs(session_folder, exist_ok=True)
            current_move = custom_utils.get_next_filename_number_on_start(session_folder, "match_image.png")[0:2]
        elif not current_run.id:
            return
        else:
            session_folder = Path(constants.DEBUG_STAGES_IMAGE_FOLDER, current_run.id)
            current_run.move_number+= 1
            current_move = f"{current_run.move_number:02d}"
        id_folder = Path(session_folder, "configs", f"{current_move}")
        match_folder = Path(session_folder, "matches")
        boards_folder = Path(id_folder, "boards")
        os.makedirs(session_folder, exist_ok=True)
        os.makedirs(id_folder, exist_ok=True)
        os.makedirs(match_folder, exist_ok=True)
        os.makedirs(boards_folder, exist_ok=True)

        match_image = custom_utils.make_match_image_comparison(result, match_list)
        screen_image = custom_utils.add_result_to_screen(result, cv2.imread(constants.LAST_SCREEN_IMAGE_PATH))

        custom_utils.compress_image_and_save(match_image, Path(match_folder, f"match_{current_move}.jpeg").as_posix())
        custom_utils.compress_image_and_save(screen_image, Path(session_folder, f"screen_{current_move}.jpeg").as_posix())
        shutil.copy(shuffle_config_files.PREFERENCES_PATH, id_folder)
        shutil.copy(shuffle_config_files.GRADING_MODES_PATH, id_folder)
        shutil.copy(shuffle_config_files.BOARD_PATH, boards_folder)
    except Exception as ex:
        log.error(f"Error on save_debug_objects: {ex}")
        return

def is_swipe_enabled(source):
    if source == "manual":
        return True
    if custom_utils.is_fast_swipe() or custom_utils.is_timed_stage():
        log.debug("Fast Swipe or Timed Stage Enabled")
        return True
    elif current_run.is_combo_active:
        log.debug("Can't Swipe because of active Combo")
        return False
    elif not current_run.last_swipe_timer:
        log.debug("Swipe enabled, last swipe timer don't exists")
        return True
    last_swipe_time = custom_utils.time_difference_in_seconds(current_run.last_swipe_timer)
    if current_run.last_swipe_timer and custom_utils.is_meowth_stage() and last_swipe_time < 8:
        log.debug(f"Meowth stage, waiting until last_swipe was 8 seconds")
        time.sleep(abs(last_swipe_time - 8))
        return True
    if current_run.last_swipe_timer and last_swipe_time > 2:
        log.debug(f"Swipe enabled, last swipe was {last_swipe_time} seconds")
        return True
    else:
        log.debug(f"Can't Swipe, last swipe was {last_swipe_time} seconds")
        log.debug("Can't Swipe, no options selected")
        return False

def verify_active_combo(current_screen_image):
    return adb_utils.has_icon_match(current_screen_image, constants.COMBO_IMAGE, "Combo", extra_timeout=0, click=False, min_point=30)

def execute_tapper(current_board: Board, source):
    if current_board.has_mega:
        mega_position_list = get_mega_match_active(current_board)
        if len(mega_position_list) == 0:
            return False
        interest_list = ["Barrier", "Metal", "Fog", "Stage_Added"]
        final_sequence = [process_tap_match(match, current_board.extra_supports_list) for match in current_board.match_sequence]
        for idx in mega_position_list:
            final_sequence[idx] = "Air"
        tapper_dict = custom_utils.split_list_to_dict(final_sequence, interest_list)
        tapper_dict["Barrier"] = [idx for idx, value in enumerate(current_board.barrier_list) if value == 'true' and final_sequence[idx] != "None"]
        list_of_tuples = [(key, value) for key in interest_list for value in tapper_dict[key]]

        if current_board.mega_name in ["Charizard_sx", "Pinsir", "Camerupt", "Rayquaza_s"]:
            shape="cross"
            num_points=2
        elif current_board.mega_name in ["Tyranitar", "Aggron"]:
            shape="cross"
            num_points=3
        elif current_board.mega_name in ["Beedrill"]:
            shape="square"
            num_points=1
        else:
            shape="cross"
            num_points=2
        logic = ""
        results_idx = []
        if len(tapper_dict["Barrier"]) > 0 or len(list_of_tuples) > 2:
            results_idx = tapper_utils.find_taps_to_clear_more_disruptions(final_sequence, shape, num_points)
            logic = "make extra matches"
        else:
            results_idx = tapper_utils.find_taps_to_make_extra_matches(final_sequence, shape, num_points)
            logic = "clear more disruptions"
            if len(results_idx) == 0:
                results_idx = tapper_utils.find_taps_to_clear_more_disruptions(final_sequence, shape, num_points)
                logic = "make extra matches because no good play was found"
        for index in results_idx:
            if custom_utils.is_adb_move_enabled() and not source == "manual":
                x, y = adb_utils.click_on_board_index(index)
                x, y = adb_utils.click_on_board_index(index)
                x, y = adb_utils.click_on_board_index(index)
                log.debug(f"Tapping at cell {index+1} - {x}, {y} with the {logic} logic")             
        return True

def get_mega_match_active(current_board: Board):
    if current_board.has_mega:
        return custom_utils.find_matches_of_3(current_board.match_sequence, current_board.mega_name, also_mega=True)

def process_tap_match(match: Match, stage_added_list: list[str]):
    if match.cosine_similarity < 0.3:
        return "None"
    if any([True if (stage_added_name in match.name) else False for stage_added_name in stage_added_list]):
        if "Barrier" in match.name:
            return "Barrier_Stage_Added"
        else:
            return "Stage_Added"
    return match.name

def click_buttons_to_enter_new_stage(current_screen_image):
    log.debug("Starting Click Buttons Check")
    current_run.non_stage_count+= 1
    if adb_utils.is_escalation_battle():
        adb_utils.verify_angry_mode(current_screen_image)
    adb_utils.check_hearts(current_screen_image)
    if current_run.disable_loop or current_run.awakened_from_sleep: #Cancel Current loop run.
        return
    adb_utils.check_buttons_to_click(current_screen_image)
    log.debug("Finished Click Buttons Check")

def match_cell_with_icons(icons_list, cell_list, has_barriers, combo_is_running=False) -> List[Match]:
    match_list: List[Match] = []
    timed_stage = custom_utils.is_timed_stage()
    for idx, cell in enumerate(cell_list):
        result = predict(cell, icons_list, has_barriers)
        if not timed_stage and not combo_is_running and not current_run.last_execution_swiped and result.name in ["Fog", "_Fog"]:
            result = update_fog_match(result, icons_list, has_barriers, idx)
        elif timed_stage and result.name in ["Fog", "_Fog"]:
            result = current_run.metal_match
        match_list.append(result)
    if timed_stage:
        mask_already_existant_matches(match_list, icons_list)
    if current_run.bad_board_count > 10:
        mask_already_existant_matches(match_list, icons_list)
    return match_list

def mask_already_existant_matches(match_list: List[Match], icons_list) -> List[Match]:
    if len(current_run.fake_matches) == 0:
        current_run.load_fake_matchs([icon.name for icon in icons_list])
    match_list = custom_utils.replace_all_3_matches_indices_and_air(match_list, current_run.metal_match, current_run)
    return match_list

def is_on_stage(original_image):
    on_stage = adb_utils.has_icon_match(original_image, constants.ACTIVE_BOARD_IMAGE, "StageMenu", extra_timeout=0, click=False, min_point=8)
    if on_stage:
        current_run.non_stage_count = 0
        current_run.first_move = False
        if not current_run.id:
            current_run.id = time.strftime('%Y_%m_%d_%H_%M')
            stage_text = adb_utils.get_current_stage(original_image)
            if custom_utils.is_stage_pause():
                if True:
                    time.sleep(2)
                    original_image = adb_utils.get_new_screenshot()
                    stage_text = adb_utils.get_current_stage(original_image)
            custom_utils.send_telegram_message(f"Started a new Stage - {stage_text}")
            current_run.first_move = True
            current_run.stage_timer = time.time()
            current_run.move_number = 0
            if current_run.last_stage_had_anger:
                log.warning("Last Stage Had Anger Active, forcing clear the angry mode")
                current_run.last_stage_had_anger = False
                current_run.angry_mode_active = False
            if current_run.angry_mode_active:
                log.warning("Starting a stage with angry mode, setting the last_stage_variable to test")
                current_run.angry_mode_active = False
                current_run.last_stage_had_anger = True
    if not on_stage:
        if current_run.id is not None:
            if custom_utils.is_debug_mode_active():
                save_debug_objects()
            stage_text = adb_utils.get_end_stage_score(original_image)
            if custom_utils.is_stage_pause():
                time.sleep(2)
                original_image = adb_utils.get_new_screenshot()
                stage_text = adb_utils.get_end_stage_score(original_image)
            if current_run.has_drops:
                stage_text+= ". And had drops"
            custom_utils.send_telegram_message(f"Ended Stage With Score {stage_text}")
            current_run.clear_stage_variables()
    elif on_stage and not current_run.stage_timer:
        current_run.stage_timer = time.time()
    elif on_stage and custom_utils.time_difference_in_seconds(current_run.stage_timer) > 60:
        adb_utils.has_text_match(original_image, "NoOutOfTime", custom_search_text="No")
        current_run.stage_timer = None
    return on_stage

def should_auto_next_stage():
    return config_utils.config_values.get("auto_next_stage")

def update_fog_match(result, icons_list, has_barriers, idx):
    new_img = adb_utils.update_fog_image(idx)
    new_result = predict(new_img, icons_list, has_barriers)
    if new_result.name == "Fog":
        return predict(new_img, [current_run.metal_icon], False)
    return new_result

def start_from_bot(pokemon_list: list[Pokemon], has_barriers, image, current_stage, source="bot", create_image=False):
    icons_list = load_icon_classes(pokemon_list, has_barriers)
    match_list: List[Match] = []
    cell_list = custom_utils.make_cell_list_from_img(image)
    for cell in cell_list:
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)
    current_board = Board(match_list, pokemon_list, icons_list)
    shuffle_config_files.update_shuffle_move_files(current_board, source, current_stage)
    result = socket_utils.loadNewBoard()
    result_image = None
    if create_image:
        result_image = custom_utils.make_match_image_comparison(result, match_list)
    return MatchResult(result=result, match_image=result_image, match_list=match_list)

def start_from_helper(pokemon_list: list[Pokemon], has_barriers, root=None, source=None, create_image=False, skip_shuffle_move=False, forced_board_image=None, forced_swipe_skip=False) -> MatchResult:
    try:
        log.debug(f"Starting a new {source} execution")
        icons_list = load_icon_classes(pokemon_list, has_barriers)
        can_swipe = is_swipe_enabled(source)
        current_screen_image = adb_utils.get_new_screenshot()
        current_run.is_combo_active = False
        
        if skip_shuffle_move:
            return handle_skip_shuffle_move(icons_list, forced_board_image, has_barriers)

        if source == "loop":
            result = verify_or_enter_stage(current_screen_image)
            if result is not None:
                return result
        can_swipe = can_swipe and not forced_swipe_skip and is_swipe_enabled(source)
        verify_drops_logic(current_screen_image)
        if not can_swipe and (custom_utils.is_meowth_stage() or not custom_utils.is_tapper_active()):
            return
        initialize_run_flags()

        cell_list = make_cell_list(adb_utils.crop_board(current_screen_image))
        match_list = match_cell_with_icons(icons_list, cell_list, has_barriers, current_run.is_combo_active)
        current_board = Board(match_list, pokemon_list, icons_list)
        update_board_with_stage_parameters(current_screen_image, current_board)
        shuffle_config_files.update_shuffle_move_files(current_board, source)

        if verify_and_execute_tapper(source, current_board):
            return MatchResult()
        
        result = socket_utils.loadNewBoard()

        if can_swipe and int(current_board.moves_left) > 0:
            swiped = adb_utils.execute_play(result, current_board)
            if custom_utils.is_debug_mode_active() and swiped:
                save_debug_objects(result, match_list, source == "manual")

        result_image = None

        if create_image:
            result_image = custom_utils.make_match_image_comparison(result, match_list)

        return MatchResult(result=result, match_image=result_image, match_list=match_list)
    except Exception as ex:
        log.error(f"Unknown Error in main loop: {ex}")
        return MatchResult()

def verify_drops_logic(current_screen_image):
    if not current_run.has_drops and custom_utils.is_check_drops_enabled():
        if adb_utils.check_if_has_drops(current_screen_image):
            current_run.has_drops = True