from typing import List
import cv2
import numpy as np
from pathlib import Path
from src.custom_utils import is_meowth_stage
from src.embed import loaded_embedder
from src import constants, custom_utils, config_utils, socket_utils, shuffle_config_files, adb_utils, log_utils, file_utils
from src.execution_variables import current_run
from src.classes import Icon, Match, Pokemon, MatchResult, Board
import statistics
import time

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
        if has_barriers and not current_run.fake_barrier_active:
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
    if has_barriers and current_run.fake_barrier_active:
        fake_barrier_img = custom_utils.resize_cv2_image(cut_borders(original_image), constants.downscale_res)
        is_frozen = has_white_border(fake_barrier_img)
        if is_frozen:
            best_match.name = f"{constants.BARRIER_PREFIX}{best_match.name}" #type: ignore
    return best_match

def has_white_border(image, threshold=190, border_size=10, debug=False):
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

    
def start_from_helper(pokemon_list: list[Pokemon], has_barriers, root=None, source=None, create_image=False, skip_shuffle_move=False, forced_board_image=None) -> MatchResult:
    icons_list = load_icon_classes(pokemon_list, has_barriers)
    cell_list = make_cell_list(forced_board_image)
    original_image = cv2.imread(constants.LAST_SCREEN_IMAGE_PATH)
    current_screen_image = cv2.imread(constants.LAST_SCREEN_IMAGE_PATH)
    is_combo_active = False
    
    if source == "loop":
        if is_on_stage(current_screen_image):
            is_combo_active = verify_active_combo(current_screen_image)
        else:
            if should_auto_next_stage():
                click_buttons(current_screen_image)
            else:
                log.debug("Stage isn't active and next stage is disabled")
            return MatchResult()
    else:
        current_run.mega_activated_this_round = False
        current_run.last_execution_swiped = False
    match_list = match_cell_with_icons(icons_list, cell_list, has_barriers, is_combo_active)
    if skip_shuffle_move:
        return MatchResult(match_list=match_list)
    current_board = Board(match_list, pokemon_list, icons_list)
    if not custom_utils.is_timed_stage():
        current_board.moves_left = adb_utils.get_moves_left(original_image)
        if is_meowth_stage():
            current_board.current_score = adb_utils.get_current_score(original_image)
        if custom_utils.is_survival_mode():
            current_board.stage_name = adb_utils.get_current_stage2(original_image)
        # current_board.current_score = adb_utils.get_current_score(original_image)
    shuffle_config_files.create_board_files(current_board, source, is_meowth_stage=is_meowth_stage())
    if source == "loop" and custom_utils.is_tapper_active() and current_board.has_mega and has_mega_match_active(current_board):
        execute_tapper(current_board)
        return MatchResult()
    elif source == "loop" and not custom_utils.is_fast_swipe() and not custom_utils.is_timed_stage() and is_combo_active:
        return MatchResult()
    result = socket_utils.loadNewBoard()
    swiped = adb_utils.execute_play(result, current_board)
    if swiped:
        current_run.last_execution_swiped = True
    result_image = None
    if create_image:
        result_image = custom_utils.make_match_image_comparison(result, match_list)
    return MatchResult(result=result, match_image=result_image, match_list=match_list)


def  verify_active_combo(current_screen_image):
    return adb_utils.has_icon_match(current_screen_image, constants.COMBO_IMAGE, "Combo", extra_timeout=0, click=False, min_point=30)

def execute_tapper(current_board: Board):
    if True or current_run.mega_activated_this_round or current_board.has_mega:
        current_run.mega_activated_this_round = True
        if not has_mega_match_active(current_board):
            return
        log.debug("Executing crazy Tapper Logic")
        interest_list = ["Frozen", "Metal", "Fog", "Stage_Added", "Wood"]
        final_sequence = [process_tap_match(match, current_board.extra_supports_list) for match in current_board.match_sequence]
        tapper_dict = custom_utils.split_list_to_dict(final_sequence, interest_list)
        tapper_dict["Frozen"] = [idx for idx, value in enumerate(current_board.frozen_list) if value == 'true' and final_sequence[idx] != "None"]
        list_of_tuples = [(key, value) for key in interest_list for value in tapper_dict[key]]
        if len(list_of_tuples) < 5:
            list_of_tuples.extend(fixed_tuple_positions)
        for icon, index in list_of_tuples[:5]:
            x, y = adb_utils.click_on_board_index(index)
            log.debug(f"Tapped on {icon} at {x}, {y}")
        return

def has_mega_match_active(current_board: Board):
    return custom_utils.has_match_of_3(current_board.match_sequence, f"Mega_{current_board.mega_name}")

def process_tap_match(match: Match, stage_added_list: list[str]):
    if match.cosine_similarity < 0.6:
        return "None"
    if match.name in stage_added_list:
        return "Stage_Added"
    return match.name

def click_buttons(current_screen_image):
    current_run.non_stage_count+= 1
    if adb_utils.is_escalation_battle():
        adb_utils.verify_angry_mode(current_screen_image)
    adb_utils.check_hearts(current_screen_image)
    adb_utils.check_buttons_to_click(current_screen_image)

def match_cell_with_icons(icons_list, cell_list, has_barriers, combo_is_running=False) -> List[Match]:
    match_list: List[Match] = []
    timed_stage = custom_utils.is_timed_stage()
    for idx, cell in enumerate(cell_list):
        result = predict(cell, icons_list, has_barriers)
        if not timed_stage and not combo_is_running and not current_run.last_execution_swiped and result.name in ["Fog", "_Fog", "Pikachu_a"]:
            result = update_fog_match(result, icons_list, has_barriers, idx)
        match_list.append(result)
    if timed_stage:
        mask_already_existant_matches(match_list)
    return match_list

def mask_already_existant_matches(match_list: List[Match]) -> List[Match]:
    match_list = custom_utils.replace_all_3_matches_indices(match_list, current_run.metal_match)
    return match_list

def is_on_stage(original_image):
    on_stage = adb_utils.has_icon_match(original_image, constants.ACTIVE_BOARD_IMAGE, "StageMenu", extra_timeout=0, click=False, min_point=8)
    if on_stage:
        current_run.angry_mode_active = False
        current_run.non_stage_count = 0
    if not on_stage:
        current_run.mega_activated_this_round = False
        current_run.last_execution_swiped = False
        current_run.stage_timer = None
    elif on_stage and current_run.stage_timer is None:
        current_run.stage_timer = time.time()
    elif on_stage and custom_utils.time_difference_in_seconds(current_run.stage_timer) > 60:
        adb_utils.has_text_match(original_image, "NoOutOfTime", custom_search_text="No")
        current_run.stage_timer = None
    return on_stage

def should_auto_next_stage():
    return config_utils.config_values.get("auto_next_stage")

def start_from_bot(pokemon_list: list[Pokemon], has_barriers, image, current_stage, source="bot", create_image=False):
    icons_list = load_icon_classes(pokemon_list, has_barriers)
    match_list: List[Match] = []
    cell_list = custom_utils.make_cell_list_from_img(image)
    for cell in cell_list:
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)
    current_board = Board(match_list, pokemon_list, icons_list)
    shuffle_config_files.create_board_files(current_board, source, current_stage)
    result = socket_utils.loadNewBoard()
    result_image = None
    if create_image:
        result_image = custom_utils.make_match_image_comparison(result, match_list)
    return MatchResult(result=result, match_image=result_image, match_list=match_list)

def update_fog_match(result, icons_list, has_barriers, idx):
    new_img = adb_utils.update_fog_image(idx)
    new_result = predict(new_img, icons_list, has_barriers)
    if new_result.name == "Fog":
        return predict(new_img, [current_run.metal_icon], False)
    return new_result