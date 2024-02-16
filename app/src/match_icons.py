from itertools import chain
import shutil
from typing import List
import cv2
import os
# from image_similarity_measures.quality_metrics import rmse, ssim
import pyautogui
import numpy as np
from PIL import Image
from pathlib import Path
import time
from src.embed import Embedder
from src import constants, custom_utils, config_utils
from src.config_utils import config_values
from src import get_window, socket_utils, shuffle_config_files
from src.execution_variables import execution_variables
from src.classes import Pokemon
embedder = Embedder()
downscale_res = (128, 128)
shuffle_move_first_square_position = config_values.get("shuffle_move_first_square_position")
mouse_after_shuffle_position = config_values.get("mouse_after_shuffle_position")
board_top_left = config_values.get("board_top_left")
board_bottom_right = config_values.get("board_bottom_right")
shuffle_move_name = config_values.get("shuffle_move_name")
airplay_app_name = config_values.get("airplay_app_name")
fake_barrier_active = False

custom_board_image = None
last_image = None
last_board_commands = []



class CustomImage():
    
    def __init__(self, image):
        self.image = image
        self.embed = embedder.create_embed_from_np(image)

class Icon():

    name: str
    barrier: bool
    barrier_type: str
    original_path: Path
    images_list: List[CustomImage]

    def __init__(self, path, barrier):
        if isinstance(path, str):
            path = Path(path)
        if path.stem == "_Fog":
            self.name = "Pikachu_a"
        elif path.stem == "_Empty":
            self.name = "Air"
        elif path.stem.startswith("_"):
            self.name = path.stem[1:]
        else:
            self.name = path.stem
        self.barrier = barrier
        self.barrier_type = None
        self.original_path = path
        if self.barrier:
            self.name = f"{constants.BARRIER_PREFIX}{self.name}"
        self.populate_images()
        
    def __repr__(self):
        return self.name
    
    def populate_images(self):
        self.images_list = []
        if not self.barrier:
            directories = [constants.IMAGES_PATH, constants.IMAGES_EXTRA_PATH]
        else:
            directories = [constants.IMAGES_BARRIER_PATH]
            self.barrier_type = constants.BARRIER_TYPE_REAL
        matching_files = []
        for directory in directories:
            matching_files.extend(custom_utils.find_matching_files(directory, self.original_path.stem, ".*"))
        for image_path in matching_files:
            image = custom_utils.open_and_resize_np_image(image_path, downscale_res)
            self.images_list.append(CustomImage(image))
        if len(self.images_list) == 0 and self.barrier and fake_barrier_active:
            original_img = custom_utils.open_and_resize_np_image(self.original_path, downscale_res)
            barrier_img = add_barrier_layer(original_img)
            self.images_list.append(CustomImage(barrier_img))
            self.barrier_type = constants.BARRIER_TYPE_FAKE

class Match():
    
    def __init__(self, board_icon, embed, icon: Icon):
        self.name = icon.name
        self.board_icon = board_icon
        cosine_tuples_list = [(embedder.cosine_similarity(embed, icon_image.embed), icon_image.image) for icon_image in icon.images_list]
        if len(cosine_tuples_list) > 0:
            self.cosine_similarity, self.match_icon = max(cosine_tuples_list, key=lambda x: x[0])
        else:
            self.cosine_similarity, self.match_icon = (0, None)

    def __repr__(self):
        return self.name 
    
    def inspect_match(self):
        custom_utils.show_list_images([self.board_icon, self.match_icon])


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

    final_image = custom_utils.resize_cv2_image(final_image, downscale_res)
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
    embed = embedder.create_embed_from_np(original_image)
    if has_barriers:
        fake_barrier_img = custom_utils.resize_cv2_image(cut_borders(original_image), downscale_res)
    # best_rmse = None
    # best_ssim = None
    best_cosine = None
    # results_rmse = {}
    # results_ssim = {}
    results_cosine = {}
    full_match_list_tmp = []
    for icon in icons_list:
        if not icon.barrier_type == constants.BARRIER_TYPE_FAKE:
            match = Match(original_image, embed, icon)
        else: 
            match = Match(fake_barrier_img, embed, icon)
        full_match_list_tmp.append(match)
        # results_rmse[match.name] = match.rmse
        # results_ssim[match.name] = match.ssim
        results_cosine[match.name] = match.cosine_similarity
        # if not best_rmse or best_rmse.rmse > match.rmse:
            # best_rmse = match
        # if not best_ssim or best_ssim.ssim < match.ssim:
            # best_ssim = match
        if not best_cosine or best_cosine.cosine_similarity < match.cosine_similarity:
            best_cosine = match
    
    # Sort the results by similarity index
    # results_rmse = sorted(results_rmse.items(), key=lambda x: x[1], reverse=False)
    # results_ssim = sorted(results_ssim.items(), key=lambda x: x[1], reverse=True)
    results_cosine = sorted(results_cosine.items(), key=lambda x: x[1], reverse=True)
    
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
    img = original_image.resize(downscale_res, Image.BILINEAR)
    np_img = np.array(img)
    return compare_with_list(np_img, icons_list, has_barriers)
    

def capture_board_screensot():
    global board_top_left, board_bottom_right
    x0 = board_top_left[0]
    x1 = board_bottom_right[0] - board_top_left[0]
    y0 = board_top_left[1]
    y1 = board_bottom_right[1] - board_top_left[1]
    img = pyautogui.screenshot(region=(x0, y0, x1, y1))
    img.save(constants.LAST_BOARD_IMAGE_PATH)
    return img

def make_cell_list():
    img = capture_board_screensot()
    return make_cell_list_with_img(img)

def make_cell_list_with_img(img):
    if isinstance(img, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    cell_list = []
    cell_size = (img.size[0]/6, img.size[1]/6)
    for y in range(0, 6):
        for x in range(0, 6):
            cell_box = (x*cell_size[0], y*cell_size[1], (x+1)*cell_size[0], (y+1)*cell_size[1])
            cell_list.append(img.crop(cell_box))
    return cell_list

def make_cell_list_with_cv2_img(img, red=None, blue=None):
    height, width = img.shape[:2]

    new_height = height - (height % 6)
    new_width = width - (width % 6)

    # Resize the image to new dimensions
    img = cv2.resize(img, (new_width, new_height))
    height, width = img.shape[:2]
    # Check if the dimensions are divisible by 6
    if height % 6 != 0 or width % 6 != 0:
        raise ValueError("Image dimensions are not divisible by 6")

    # Initialize an empty list to store the smaller images
    smaller_images = []

    square_size = min(height, width) // int(36 ** 0.5)
    # Iterate through the image and split it into 6x6 smaller images
    for y in range(0, height, square_size):
        for x in range(0, width, square_size):
            # Extract the square region from the image
            square = img[y:y+square_size, x:x+square_size]
            # Append the square to the list


             # Add position text on top of the square with a black background
            square_with_text = square.copy()
            text = f"{y//square_size+1},{x//square_size+1}"
            # font_scale = min(square_size, 25) / 25  # Adjust font size based on square size
            # text_thickness = max(1, int(font_scale))  # Adjust text thickness based on font size
            # text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
            # text_x = (square_size - text_size[0]) // 2
            # text_y = (square_size + text_size[1]) // 2
            # bg_rect_size = (text_size[0] + 6, text_size[1] + 6)  # Fixed size for background rectangle
            # bg_rect_x = (square_size - bg_rect_size[0]) // 2
            # bg_rect_y = (square_size - bg_rect_size[1]) // 2
            # cv2.rectangle(square_with_text, (bg_rect_x, bg_rect_y), (bg_rect_x + bg_rect_size[0], bg_rect_y + bg_rect_size[1]), (0, 0, 0), cv2.FILLED)
            # cv2.putText(square_with_text, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), text_thickness)

            font=cv2.FONT_HERSHEY_SIMPLEX
            pos=(0, 0)
            font_scale=1
            font_thickness=2
            text_color=(0, 255, 0)
            text_color_bg=(0, 0, 0)

            text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
            text_w, text_h = text_size
            cv2.rectangle(square_with_text, pos, (0 + text_w, 0 + text_h), text_color_bg, -1)
            cv2.putText(square_with_text, text, (0, 0 + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)

            # cv2.imshow("",square_with_text)

            if text == red:
                red_transparent_layer = np.zeros((square_size, square_size, 3), dtype=np.uint8)
                red_transparent_layer[:, :] = (0, 0, 255)  # Red color
                overlay = cv2.addWeighted(square_with_text, 0.5, red_transparent_layer, 0.5, 0)
                smaller_images.append(overlay)
            elif text == blue:
                blue_transparent_layer = np.zeros((square_size, square_size, 3), dtype=np.uint8)
                blue_transparent_layer[:, :] = (255, 0, 0)  # Blue color
                overlay = cv2.addWeighted(square_with_text, 0.5, blue_transparent_layer, 0.5, 0)
                smaller_images.append(overlay)


            smaller_images.append(square_with_text)


    return smaller_images

def concatenate_PIL_images(image_list, grid_size=(6, 6), spacing=10):
    # Calculate the size of the final image
    image_width, image_height = image_list[0].size
    grid_width = grid_size[1] * image_width + (grid_size[1] - 1) * spacing
    grid_height = grid_size[0] * image_height + (grid_size[0] - 1) * spacing

    # Create a blank white image as the background
    result_image = Image.new('RGB', (grid_width, grid_height), (255, 255, 255))

    # Paste each image into the result image
    for i in range(grid_size[0]):
        for j in range(grid_size[1]):
            if not image_list:
                break
            current_image = image_list.pop(0)
            x_coordinate = j * (image_width + spacing)
            y_coordinate = i * (image_height + spacing)
            result_image.paste(current_image, (x_coordinate, y_coordinate))

    return result_image

def has_airplay_on_screen():
    global shuffle_move_first_square_position   

    # app_in_move_position = get_window.get_window_name_at_coordinate(shuffle_move_first_square_position[0], y=shuffle_move_first_square_position[1])
    # is_move = (shuffle_move_name in app_in_move_position.lower())
    app_in_airplay_position = get_window.get_window_name_at_coordinate(board_top_left[0], y=board_top_left[1])
    has_airplay = any([name.lower() in app_in_airplay_position.lower() for name in airplay_app_name])
    if not has_airplay:
        print(f"App Found in AirPlay Position: {app_in_airplay_position} - In Position ({board_top_left[0]}, {board_top_left[1]})")
        print(f"List of possible app names is: {airplay_app_name}")

    return has_airplay

def execute_commands(command_sequence, source=None):
    global shuffle_move_first_square_position

    if execution_variables.socket_mode:
        return socket_utils.loadNewBoard()
    focused_name = get_window.get_focused_window_name()
    behind_name = get_window.get_window_name_at_coordinate(shuffle_move_first_square_position[0], y=shuffle_move_first_square_position[1])
    move_is_focused = (shuffle_move_name in focused_name.lower())
    move_is_behind = (shuffle_move_name in behind_name.lower())
    mouse_click = False
    if source == "loop" and not move_is_focused and not move_is_behind:
        return
    elif source == "loop" and not move_is_focused and move_is_behind:
        mouse_click = True
    elif source == "loop":
        pass
    else:
        mouse_click = True
    if mouse_click:
        pyautogui.click(shuffle_move_first_square_position[0], y=shuffle_move_first_square_position[1])
        time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'l')


def start_from_helper(request_values: list[Pokemon], has_barriers, root=None, source=None):
    global last_image, last_board_commands
    if source == "loop" and not has_airplay_on_screen():
        print("airplay not on screen, ignoring")
        if root:
            root.info_message.configure(text="Loop Mode: Airplay not on screen, ignoring")
        return 2000
    icons_list = load_icon_classes(request_values, has_barriers)
    match_list: List[Match] = []
    cell_list = make_cell_list()
    for idx, cell in enumerate(cell_list):
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)
    
    # img1 = concatenate_cv2_images([match.board_icon for match in match_list])
    # img2 = concatenate_cv2_images([match.match_icon for match in match_list])
    # last_image = custom_utils.concatenate_list_images([img1, img2])

    extra_supports_list = [pokemon[0].name for pokemon in request_values if pokemon.stage_added]
    sequence_names_list = [match.name for match in match_list]
    original_complete_names_list = [icon.name for icon in icons_list]
    commands_list = [match.name for match in match_list]
    if commands_list != last_board_commands or source != "loop":
        shuffle_config_files.create_board_files(sequence_names_list, original_complete_names_list, extra_supports_list, source)
        last_board_commands = commands_list
        result = execute_commands(commands_list, source)
    else:
        if root:
            root.info_message.configure(text="Loop Mode: Same commands found")
    return 0

def start_from_bot(request_values, has_barriers, image, source="bot"):
    icons_list = load_icon_classes(request_values, has_barriers)
    match_list: List[Match] = []
    cell_list = make_cell_list_with_img(image)
    for cell in cell_list:
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)
    extra_supports_list = [pokemon[0].name for pokemon in request_values if pokemon.stage_added]
    sequence_names_list = [match.name for match in match_list]
    original_complete_names_list = [icon.name for icon in icons_list]
    shuffle_config_files.create_board_files(sequence_names_list, original_complete_names_list, extra_supports_list, source, stage="NONE")
    result = execute_commands(sequence_names_list)
    return result