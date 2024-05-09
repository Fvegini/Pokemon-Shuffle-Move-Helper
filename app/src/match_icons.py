from typing import List
import cv2
import numpy as np
from pathlib import Path
from src.adb_utils import get_coordinates_from_board_index
from src.custom_utils import capture_board_screensot
from src.embed import loaded_embedder
from src import constants, custom_utils
from src import config_utils
from src.execution_variables import execution_variables
from src import socket_utils, shuffle_config_files
from src.classes import Icon, Match, Pokemon, MatchResult, ShuffleBoard
import statistics
from datetime import datetime
from src import adb_utils
import math
from src.board_utils import current_board
from src import log_utils

log = log_utils.get_logger()


fake_barrier_active = False

custom_board_image = None
last_pokemon_board_sequence: list[str] = []
loaded_icons_cache: dict[str, Icon] = {}
mega_activated_this_round = False
metal_icon = Icon("Metal", Path("Metal.png"), False)
metal_match = Match(None, None, metal_icon)
last_execution_swiped = False
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
        if has_barriers:
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
    

def add_barrier_layer(original_image, custom_border=None):
    layer = np.zeros_like(original_image)

    # Fill the layer with a color (white in this example)
    layer[:] = (255, 255, 240)  # White color
    alpha = 0.6

    image = cv2.addWeighted(original_image, 1 - alpha, layer, alpha, 0)
    
    if custom_border:
        final_image = cut_borders(image, custom_border)
    else:
        final_image = cut_borders(image)

    final_image = custom_utils.resize_cv2_image(final_image, constants.downscale_res)
    return final_image

def cut_borders(image, border_size=15):
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
    if has_barriers:
        fake_barrier_img = custom_utils.resize_cv2_image(cut_borders(original_image), constants.downscale_res)
    best_cosine = None
    full_match_list_tmp = []
    for icon in icons_list:
        if not icon.barrier_type == constants.BARRIER_TYPE_FAKE:
            match = Match(original_image, embed, icon)
        else: 
            match = Match(fake_barrier_img, embed, icon)
        full_match_list_tmp.append(match)
        if not best_cosine or best_cosine.cosine_similarity < match.cosine_similarity:
            best_cosine = match
    return best_cosine

def calculate_percentage_difference(num1, num2):
    average = (num1 + num2) / 2
    percentage_difference = abs((num1 - num2) / average) * 100
    return percentage_difference

def predict(original_image, icons_list, has_barriers) -> Match:
    resized = cv2.resize(original_image, constants.downscale_res)
    return compare_with_list(resized, icons_list, has_barriers)

def make_cell_list(forced_board_image=None):
    if forced_board_image is None:
        img = capture_board_screensot()
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
    global last_pokemon_board_sequence, mega_activated_this_round, last_execution_swiped
    icons_list = load_icon_classes(pokemon_list, has_barriers)
    cell_list = make_cell_list(forced_board_image)
    original_image = cv2.imread(constants.LAST_SCREEN_IMAGE_PATH)
    current_screen_image = cv2.imread(constants.LAST_SCREEN_IMAGE_PATH)
    combo_is_running = False
    if source != "manual":
        if not is_on_stage(current_screen_image):
            if should_auto_next_stage():
                click_buttons(current_screen_image)
            else:
                log.debug("Stage isn't active and next stage is disabled")
            mega_activated_this_round = False
            last_execution_swiped = False
            return MatchResult()
        combo_is_running = verify_active_combo(current_screen_image)
    else:
        mega_activated_this_round = False
        last_execution_swiped = False
    match_list = match_cell_with_icons(icons_list, cell_list, has_barriers, combo_is_running)
    #adb_utils.click_button_if_visible(original_image, "No")
    if not adb_utils.has_board_active(original_image):
        print("No Board Active")
        adb_utils.check_hearts(original_image)
        adb_utils.check_buttons_to_click(original_image)
        return MatchResult()
        
    for idx, cell in enumerate(cell_list):
        result = predict(cell, icons_list, has_barriers)
        if result.name in ["Fog", "_Fog", "Pikachu_a"]:
            result = update_fog_match(result, icons_list, has_barriers, idx)
        match_list.append(result)

    # new_list = match_list.copy()    
    # new_list = custom_utils.sort_by_class_attribute(new_list, "cosine_similarity", False)
    # metrics = get_metrics(new_list)
    
    extra_supports_list = [pokemon.name for pokemon in pokemon_list if pokemon.stage_added]
    sequence_names_list = [match.name for match in match_list]
    original_complete_names_list = [icon.name for icon in icons_list]
    pokemon_board_sequence = [match.name for match in match_list]
    if skip_shuffle_move:
        return MatchResult(match_list=match_list)
    current_board = ShuffleBoard(match_list, pokemon_list, icons_list)
    shuffle_config_files.create_board_files(current_board, source)
    if source != "manual" and not config_utils.config_values.get("fast_swipe") and not config_utils.config_values.get("timed_stage") and (last_execution_swiped or combo_is_running):
        last_execution_swiped = False
        if config_utils.config_values.get("tapper"):
            execute_tapper(current_board)
        return MatchResult()
    # if pokemon_board_sequence != last_pokemon_board_sequence or source != "loop":
    current_score = adb_utils.get_current_score(original_image)
    moves_left = adb_utils.get_moves_left(original_image)
    stage_name = adb_utils.get_current_stage(original_image)
    if stage_name.isnumeric():
        execution_variables.current_stage = stage_name
    if stage_name == '037':
        execution_variables.current_strategy = '037MeowthEarlyGame'
        if int(moves_left) <= 2:
            execution_variables.current_strategy = '037MeowthEndGame'
        shuffle_config_files.update_gradingModes_file("self", False)

    shuffle_config_files.update_preferences(current_score, moves_left)
    shuffle_config_files.create_board_files(sequence_names_list, original_complete_names_list, extra_supports_list, source)
    last_pokemon_board_sequence = pokemon_board_sequence
    result = socket_utils.loadNewBoard()
    swiped = adb_utils.execute_play(result, current_board, last_execution_swiped)
    if swiped:
        last_execution_swiped = True
    result_image = None
    if create_image:
        result_image = custom_utils.make_match_image_comparison(result, match_list)
    return MatchResult(result=result, match_image=result_image, match_list=match_list)

def verify_active_combo(current_screen_image):
    return adb_utils.has_match(current_screen_image, constants.COMBO_IMAGE)

def execute_tapper(current_board: ShuffleBoard):
    global mega_activated_this_round
    if True or mega_activated_this_round or current_board.has_mega:
        log.debug("Executing crazy Tapper Logic")
        mega_activated_this_round = True
        interest_list = ["Frozen", "Metal", "Fog", "Wood"]
        final_sequence = [process_tap_match(match, current_board.extra_supports_list) for match in current_board.match_sequence]
        tapper_dict = custom_utils.split_list_to_dict(final_sequence, interest_list)
        tapper_dict["Frozen"] = [idx for idx, value in enumerate(current_board.frozen_list) if value == 'true' and final_sequence[idx] != "None"]
        list_of_tuples = [(key, value) for key in interest_list for value in tapper_dict[key]]
        if len(list_of_tuples) < 5:
            list_of_tuples.extend(fixed_tuple_positions)
        for icon, index in list_of_tuples[:5]:
            x, y = adb_utils.click_on_board_index(index)
            log.debug(f"Tapped on {icon} at {x}, {y}")

def process_tap_match(match: Match, stage_added_list: list[str]):
    if match.cosine_similarity < 0.6:
        return "None"
    if match.name in stage_added_list:
        return "Stage_Added"
    return match.name

def click_buttons(current_screen_image):
    adb_utils.check_hearts(current_screen_image)
    adb_utils.check_buttons_to_click(current_screen_image)

def match_cell_with_icons(icons_list, cell_list, has_barriers, combo_is_running=False) -> List[Match]:
    global last_execution_swiped
    match_list: List[Match] = []
    is_timed_stage = check_is_timed_stage()
    for idx, cell in enumerate(cell_list):
        result = predict(cell, icons_list, has_barriers)
        if not is_timed_stage and not combo_is_running and not last_execution_swiped and result.name in ["Fog", "_Fog", "Pikachu_a"]:
            result = update_fog_match(result, icons_list, has_barriers, idx)
        match_list.append(result)
    if is_timed_stage:
        mask_already_existant_matches(match_list)
    return match_list

def mask_already_existant_matches(match_list: List[Match]) -> List[Match]:
    match_list = custom_utils.replace_all_3_matches_indices(match_list, metal_match)
    return match_list

def check_is_timed_stage():
    return config_utils.config_values.get("timed_stage")

def is_on_stage(original_image):
    return adb_utils.has_match(original_image, constants.ACTIVE_BOARD_IMAGE)

def should_auto_next_stage():
    return config_utils.config_values.get("auto_next_stage")

def start_from_bot(pokemon_list: list[Pokemon], has_barriers, image, current_stage, source="bot", create_image=False):
    icons_list = load_icon_classes(pokemon_list, has_barriers)
    match_list: List[Match] = []
    cell_list = custom_utils.make_cell_list_from_img(image)
    for cell in cell_list:
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)
    current_board = ShuffleBoard(match_list, pokemon_list, icons_list)
    shuffle_config_files.create_board_files(current_board, source, current_stage)
    result = socket_utils.loadNewBoard()
    result_image = None
    if create_image:
        result_image = custom_utils.make_match_image_comparison(result, match_list)
    return MatchResult(result=result, match_image=result_image, match_list=match_list)

def update_fog_match(result, icons_list, has_barriers, idx):
    # row, column = [int(coordinate) for coordinate in custom_utils.index_to_coordinates(idx)]
    row, column = custom_utils.index_to_coordinates(idx)
    resolution = adb_utils.get_screen_resolution()
    r = constants.RESOLUTIONS[resolution]["Board"]
    board_top_left = (r[0], r[1])
    board_bottom_right = (r[2], r[3])

    board_x = board_top_left[0]
    board_y = board_top_left[1]
    board_w = (board_bottom_right[0] - board_top_left[0]) / 6
    board_h = (board_bottom_right[1] - board_top_left[1]) / 6

    cell_x0 =  math.floor(board_x + (board_w * (column - 1)))
    cell_y0 =  math.floor(board_y + (board_h * (row - 1)))
    cell_x1 =  math.floor(board_x + (board_w * (column)))
    cell_y1 =  math.floor(board_y + (board_h * (row)))

    
    new_img = adb_utils.update_fog_image(cell_x0, cell_y0, cell_x1, cell_y1, board_w, board_h)
    new_img = adb_utils.update_fog_image(idx)
    new_result = predict(new_img, icons_list, has_barriers)
    if new_result.name == "Fog":
        return predict(new_img, [metal_icon], False)
    return new_result