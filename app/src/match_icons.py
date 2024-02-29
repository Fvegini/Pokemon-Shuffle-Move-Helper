from itertools import chain
import shutil
from typing import List
import cv2
import os
# from image_similarity_measures.quality_metrics import rmse, ssim
import pyautogui
import numpy as np
# from PIL import Image
from pathlib import Path
import time
from src.embed import loaded_embedder
from src import constants, custom_utils, config_utils
from src.config_utils import config_values
from src import get_window, socket_utils, shuffle_config_files
from src.execution_variables import execution_variables
from src.classes import Icon, Match, Pokemon, MatchResult
import statistics



board_top_left = config_values.get("board_top_left")
board_bottom_right = config_values.get("board_bottom_right")
shuffle_move_name = config_values.get("shuffle_move_name")
airplay_app_name = config_values.get("airplay_app_name")
fake_barrier_active = False

custom_board_image = None
last_image = None
last_pokemon_board_sequence: list[str] = []



def load_icon_classes(values_to_execute: list[Pokemon], has_barriers):
    icons_list = []
    for pokemon in values_to_execute:
        if pokemon.disabled:
            continue
        icons_list.append(Icon(pokemon.name, False))
        if has_barriers:
            icons_list.append(Icon(pokemon.name, True))
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
    # Compare the input image with each image in the folder
    embed = loaded_embedder.create_embed_from_np(original_image)
    if has_barriers:
        fake_barrier_img = custom_utils.resize_cv2_image(cut_borders(original_image), constants.downscale_res)
    # best_rmse = None
    # best_ssim = None
    best_cosine = None
    # results_rmse = {}
    # results_ssim = {}
    # results_cosine = {}
    full_match_list_tmp = []
    for icon in icons_list:
        if not icon.barrier_type == constants.BARRIER_TYPE_FAKE:
            match = Match(original_image, embed, icon)
        else: 
            match = Match(fake_barrier_img, embed, icon)
        full_match_list_tmp.append(match)
        # results_rmse[match.name] = match.rmse
        # results_ssim[match.name] = match.ssim
        # results_cosine[match.name] = match.cosine_similarity
        # if not best_rmse or best_rmse.rmse > match.rmse:
            # best_rmse = match
        # if not best_ssim or best_ssim.ssim < match.ssim:
            # best_ssim = match
        if not best_cosine or best_cosine.cosine_similarity < match.cosine_similarity:
            best_cosine = match
    
    # Sort the results by similarity index
    # results_rmse = sorted(results_rmse.items(), key=lambda x: x[1], reverse=False)
    # results_ssim = sorted(results_ssim.items(), key=lambda x: x[1], reverse=True)
    # results_cosine = sorted(results_cosine.items(), key=lambda x: x[1], reverse=True)
    
    # percentage_rmse = calculate_percentage_difference(results_rmse[0][1], results_rmse[1][1])
    # percentage_ssim = calculate_percentage_difference(results_ssim[0][1], results_ssim[1][1])
    # percentage_cosine = calculate_percentage_difference(results_cosine[0][1], results_cosine[1][1])
    # if not best_rmse == best_ssim == best_cosine:
        # print(f"RMSE: {percentage_rmse:.2f} - {results_rmse}")
        # print(f"SSIM: {percentage_ssim:.2f} - {results_ssim}")
        # print(f"COS: {percentage_cosine:.2f} - {results_cosine}")
    # if percentage_ssim > 0: #Check a good number
    return best_cosine# else:
        # return best_rmse

def calculate_percentage_difference(num1, num2):
    average = (num1 + num2) / 2
    percentage_difference = abs((num1 - num2) / average) * 100
    return percentage_difference

def predict(original_image, icons_list, has_barriers) -> Match:
    resized = cv2.resize(original_image, constants.downscale_res)
    return compare_with_list(resized, icons_list, has_barriers)
    

def capture_board_screensot():
    global board_top_left, board_bottom_right
    x0 = board_top_left[0]
    x1 = board_bottom_right[0] - board_top_left[0]
    y0 = board_top_left[1]
    y1 = board_bottom_right[1] - board_top_left[1]
    img = pyautogui.screenshot(region=(x0, y0, x1, y1))
    img.save(constants.LAST_BOARD_IMAGE_PATH)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def make_cell_list():
    img = capture_board_screensot()
    return custom_utils.make_cell_list_from_img(img)

# def concatenate_PIL_images(image_list, grid_size=(6, 6), spacing=10):
#     # Calculate the size of the final image
#     image_width, image_height = image_list[0].size
#     grid_width = grid_size[1] * image_width + (grid_size[1] - 1) * spacing
#     grid_height = grid_size[0] * image_height + (grid_size[0] - 1) * spacing

#     # Create a blank white image as the background
#     result_image = Image.new('RGB', (grid_width, grid_height), (255, 255, 255))

#     # Paste each image into the result image
#     for i in range(grid_size[0]):
#         for j in range(grid_size[1]):
#             if not image_list:
#                 break
#             current_image = image_list.pop(0)
#             x_coordinate = j * (image_width + spacing)
#             y_coordinate = i * (image_height + spacing)
#             result_image.paste(current_image, (x_coordinate, y_coordinate))

#     return result_image

def has_airplay_on_screen():
    app_in_airplay_position = get_window.get_window_name_at_coordinate(board_top_left[0], y=board_top_left[1])
    has_airplay = any([name.lower() in app_in_airplay_position.lower() for name in airplay_app_name])
    if not has_airplay:
        print(f"App Found in AirPlay Position: {app_in_airplay_position} - In Position ({board_top_left[0]}, {board_top_left[1]})")
        print(f"List of possible app names is: {airplay_app_name}")

    return has_airplay

def get_metrics(match_list):
    numbers_list = [match.cosine_similarity for match in match_list]
    return {
    "maximum": max(numbers_list),
    "minimum": min(numbers_list),
    "median": statistics.median(numbers_list),
    "variance": statistics.variance(numbers_list),
    }

    

def start_from_helper(pokemon_list: list[Pokemon], has_barriers, root=None, source=None, create_image=False) -> MatchResult:
    global last_image, last_pokemon_board_sequence
    if source == "loop" and not has_airplay_on_screen():
        print("airplay not on screen, ignoring")
        if root:
            root.info_message.configure(text="Loop Mode: Airplay not on screen, ignoring")
        return MatchResult()
    icons_list = load_icon_classes(pokemon_list, has_barriers)
    match_list: List[Match] = []
    cell_list = make_cell_list()
    for idx, cell in enumerate(cell_list):
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)

    # new_list = match_list.copy()    
    # new_list = custom_utils.sort_by_class_attribute(new_list, "cosine_similarity", False)
    # metrics = get_metrics(new_list)
    
    extra_supports_list = [pokemon.name for pokemon in pokemon_list if pokemon.stage_added]
    sequence_names_list = [match.name for match in match_list]
    original_complete_names_list = [icon.name for icon in icons_list]
    pokemon_board_sequence = [match.name for match in match_list]
    if pokemon_board_sequence != last_pokemon_board_sequence or source != "loop":
        shuffle_config_files.create_board_files(sequence_names_list, original_complete_names_list, extra_supports_list, source)
        last_pokemon_board_sequence = pokemon_board_sequence
        result = socket_utils.loadNewBoard()
    else:
        if root:
            root.info_message.configure(text="Loop Mode: Same commands found")
    result_image = None
    if create_image:
        result_image = custom_utils.make_match_image_comparison(result, match_list)
    return MatchResult(result=result, match_image=result_image, match_list=match_list)

def start_from_bot(pokemon_list: list[Pokemon], has_barriers, image, current_stage, source="bot", create_image=False):
    icons_list = load_icon_classes(pokemon_list, has_barriers)
    match_list: List[Match] = []
    cell_list = custom_utils.make_cell_list_from_img(image)
    for cell in cell_list:
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)
    extra_supports_list = [pokemon.name for pokemon in pokemon_list if pokemon.stage_added]
    sequence_names_list = [match.name for match in match_list]
    original_complete_names_list = [icon.name for icon in icons_list]
    shuffle_config_files.create_board_files(sequence_names_list, original_complete_names_list, extra_supports_list, source, current_stage)
    result = socket_utils.loadNewBoard()
    result_image = None
    if create_image:
        result_image = custom_utils.make_match_image_comparison(result, match_list)
    return MatchResult(result=result, match_image=result_image, match_list=match_list)

