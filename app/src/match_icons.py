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
from src import constants, custom_utils


embedder = Embedder()
downscale_res = (128, 128)
shuffle_move_first_square_position = (1500, 90)
mouse_after_shuffle_position = (1420, 560)
# board_top_left = (390, 533) # Position for Airdroid Cast
# board_bottom_right = (890, 1028) # Position for Airdroid Cast
board_top_left = (11, 466) # Position for 5kPlayer
board_bottom_right = (573, 1027) # Position for 5kPlayer

custom_board_image = None
last_image = None

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
    shortcut: List[str]

    def __init__(self, path, shortcut, barrier):
        self.name = path.stem
        self.barrier = barrier
        self.barrier_type = None
        self.original_path = path
        if not self.barrier:
            self.shortcut = [shortcut]
        else:
            self.shortcut = [shortcut, "F"]
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
        if len(self.images_list) == 0 and self.barrier:
            original_img = custom_utils.open_and_resize_np_image(self.original_path, downscale_res)
            barrier_img = add_barrier_layer(original_img)
            self.images_list.append(CustomImage(barrier_img))
            self.barrier_type = constants.BARRIER_TYPE_FAKE

class Match():
    
    def __init__(self, board_icon, embed, icon: Icon):
        self.name = icon.name
        self.board_icon = board_icon
        self.shortcut = icon.shortcut
        cosine_tuples_list = [(embedder.cosine_similarity(embed, icon_image.embed), icon_image.image) for icon_image in icon.images_list]
        self.cosine_similarity, self.match_icon = max(cosine_tuples_list, key=lambda x: x[0])

    def __repr__(self):
        return self.name 
    
    def inspect_match(self):
        custom_utils.show_list_images([self.board_icon, self.match_icon])


def load_icon_classes(values_to_execute, has_barriers):
    icons_list = []
    for image_path, shortcut in values_to_execute:
        icons_list.append(Icon(image_path, shortcut, False))
        if has_barriers:
            icons_list.append(Icon(image_path, shortcut, True))
    return icons_list


# def old_load_icon_classes(values_to_execute, has_barriers):
#     images = []
#     for image_path, shortcut in values_to_execute:
        
#         np_img = custom_utils.resize_cv2_image(cv2.imread(image_path.as_posix()), downscale_res)
#         if np_img is not None:
#             np_img = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)
#         else:
#             np_img = np.array(Image.open(image_path.as_posix()).convert('RGB'))
#             np_img = custom_utils.resize_cv2_image(np_img,downscale_res)
#         images.append(Icon(image_path.stem, np_img, [shortcut], image_path))
#         if has_barriers:
            
#             barrier_img = add_barrier_layer(np_img)
#             barrier_path = change_filename_in_path(image_path, prefix=constants.BARRIER_PREFIX)
#             images.append(Icon(barrier_path.stem, barrier_img, [shortcut, "F"], barrier_path))
#     return images

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


# def compare_images(original_image, image_to_compare):
#     try:
#         return rmse(original_image, image_to_compare), ssim(original_image, image_to_compare)
#     except:
#         return None, None

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
    

def capture_board_screensot(screen_record):
    global board_top_left, board_bottom_right, custom_board_image
    if screen_record == "last":
        img = Image.open(constants.LAST_BOARD_IMAGE_PATH)
    if custom_board_image:
        return Image.open(custom_board_image)
    elif screen_record:
        x0 = board_top_left[0]
        x1 = board_bottom_right[0] - board_top_left[0]
        y0 = board_top_left[1]
        y1 = board_bottom_right[1] - board_top_left[1]
        img = pyautogui.screenshot(region=(x0, y0, x1, y1))
        img.save(constants.LAST_BOARD_IMAGE_PATH)
    elif os.path.exists(constants.DROPBOX_IMAGE_PATH):
        shutil.move(constants.DROPBOX_IMAGE_PATH, constants.LAST_BOARD_IMAGE_PATH)
        img = Image.open(constants.LAST_BOARD_IMAGE_PATH)
        img =  img.crop((10,600,740,1320)).convert('RGB')
        img.save(constants.LAST_BOARD_IMAGE_PATH)
    else:
        img = Image.open(constants.LAST_BOARD_IMAGE_PATH)
    return img

def make_cell_list(screen_record):
    img = capture_board_screensot(screen_record)
    cell_list = []
    cell_size = (img.size[0]/6, img.size[1]/6)
    for y in range(0, 6):
        for x in range(0, 6):
            cell_box = (x*cell_size[0], y*cell_size[1], (x+1)*cell_size[0], (y+1)*cell_size[1])
            cell_list.append(img.crop(cell_box))
    return cell_list
            
def start(request_values, has_barriers, show_debug=False, screen_record=False):
    global last_image
    icons_list = load_icon_classes(request_values, has_barriers)
    match_list: List[Match] = []
    cell_list = make_cell_list(screen_record)
    predict(cell_list[17], icons_list, has_barriers)
    for idx, cell in enumerate(cell_list):
        result = predict(cell, icons_list, has_barriers)
        match_list.append(result)
    
    # if show_debug:
    img1 = concatenate_images([match.board_icon for match in match_list])
    img2 = concatenate_images([match.match_icon for match in match_list])
    last_image = custom_utils.concatenate_list_images([img1, img2])
    
    commands_list = list(chain(*[match.shortcut for match in match_list]))
    
    execute_commands(commands_list)

def concatenate_images(images, num_columns=6):
    num_images = len(images)

    # Determine the number of rows needed based on the number of columns
    num_rows = -(-num_images // num_columns)  # Ceiling division

    # Determine the maximum height and width among all images
    max_height = max(image.shape[0] for image in images)
    max_width = max(image.shape[1] for image in images)

    # Create a blank canvas for the concatenated image
    canvas = np.zeros((num_rows * max_height, num_columns * max_width, 3), dtype=np.uint8)

    # Copy each image to the centered position on the canvas
    for i, image in enumerate(images):
        row = i // num_columns
        col = i % num_columns

        # Calculate the centering offsets
        y_offset = row * max_height + (max_height - image.shape[0]) // 2
        x_offset = col * max_width + (max_width - image.shape[1]) // 2

        canvas[y_offset:y_offset+image.shape[0], x_offset:x_offset+image.shape[1], :] = image

    return canvas
        
def execute_commands(command_sequence):
    global shuffle_move_first_square_position
    print(command_sequence)
    # screen_factor = 0.68
    # position = [el * screen_factor for el in position]
    # position
    pyautogui.click(shuffle_move_first_square_position[0], y=shuffle_move_first_square_position[1])
    time.sleep(0.2)
    with pyautogui.hold("ctrl"):
            pyautogui.press("del")
    time.sleep(0.2)
    pyautogui.click(x=shuffle_move_first_square_position[0], y=shuffle_move_first_square_position[1])
    time.sleep(0.2)
    for command in command_sequence:
            pyautogui.press(command)
            time.sleep(0.005)
    pyautogui.moveTo(x=mouse_after_shuffle_position[0], y=mouse_after_shuffle_position[1])


IMAGES_PATH = r"assets\icons_processed"
test_scenarios = {
    "0": {
        "board_image": r"test_cases\board_crystal.bmp",
        "values": ([(Path(IMAGES_PATH, 'Altaria.png'), '1'), (Path(IMAGES_PATH, 'Dragonair.png'), (Path(IMAGES_PATH, 'Dragonite.png'), '3'),  '2'), (Path(IMAGES_PATH, 'Zygarde-50.png'), '4'), (Path(IMAGES_PATH, '_metal.png'), '5'), (Path(IMAGES_PATH, '_empty.png'), 'del')], True)
    },
    "1": {
        "board_image": r"test_cases\board_mega_altaria.bmp",
        "values": ([(Path(IMAGES_PATH, 'Mega_Altaria.png'), '1'), (Path(IMAGES_PATH, 'Dragonair.png'), '2'), (Path(IMAGES_PATH, 'Dragonite.png'), '3'), (Path(IMAGES_PATH, 'Zygarde-50.png'), '4'), (Path(IMAGES_PATH, '_metal.png'), '5'), (Path(IMAGES_PATH, 'Goomy.png'), '7'), (Path(IMAGES_PATH, '_empty.png'), 'del')], True)
    }
}

if __name__ == "__main__":
    custom_board_image = test_scenarios.get("1").get("board_image")
    values = test_scenarios.get("1").get("values")
    start(*values, show_debug=True)