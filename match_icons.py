from itertools import chain
from typing import List
import cv2
import os
from image_similarity_measures.quality_metrics import rmse, ssim
import pyautogui
import numpy as np
from PIL import Image
from pathlib import Path
import time
from PIL import Image
    
downscale_res = (128, 128)
shuffle_move_first_square_position = (1500, 90)
# board_top_left = (390, 533) # Position for Airdroid Cast
# board_bottom_right = (890, 1028) # Position for Airdroid Cast
board_top_left = (11, 466) # Position for 5kPlayer
board_bottom_right = (573, 1027) # Position for 5kPlayer

custom_board_image = None
BARRIER_PREFIX = "Barrier_"

class Icon():
    
    def __init__(self, name, image, shortcut, path):
        self.name = name
        self.image = image
        self.path = path
        self.shortcut = shortcut
        
    def __repr__(self):
        return self.name 

class Match():
    
    def __init__(self, board_icon, icon: Icon):
        self.name = icon.name
        self.board_icon = board_icon
        self.match_icon = icon.image
        self.shortcut = icon.shortcut
        self.rmse, self.ssim = compare_images(board_icon, icon.image)

    def __repr__(self):
        return self.name 
    
    def inspect_match(self):
        show_list_images([self.board_icon, self.match_icon])

def create_blank_square(height, width):
    return np.ones((height, width, 3), dtype=np.uint8) * 255

def insert_in_middle(lst, new_value):
    new_list = []
    for index, item in enumerate(lst):
        new_list.append(item)
        if index+1 < len(lst):
            new_list.append(new_value)
    return new_list

def show_list_images(images):
    
    max_height = max(image.shape[0] for image in images)

    blank_square = create_blank_square(max_height, 40)
    # Create new images with the maximum height
    
    new_images_test = insert_in_middle(images, blank_square)
    
    new_images = [np.zeros((max_height, image.shape[1], 3), dtype=np.uint8) for image in new_images_test]

    

    # Copy the content of the original images to the new images
    for i, image in enumerate(new_images_test):
        new_images[i][:image.shape[0], :, :] = image



    # Concatenate all images side by side
    concatenated_image = np.concatenate(new_images, axis=1)
    show_cv2_img(concatenated_image)

def resize_image(image, target_size):
    try:
        return cv2.resize(image, target_size)
    except:
        return None

def load_icon_classes(values_to_execute, has_barriers):
    images = []
    for image_path, shortcut in values_to_execute:
        
        np_img = resize_image(cv2.imread(image_path.as_posix()), downscale_res)
        if np_img is not None:
            np_img = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)
        else:
            np_img = np.array(Image.open(image_path.as_posix()).convert('RGB'))
            np_img = resize_image(np_img,downscale_res)
        images.append(Icon(image_path.stem, np_img, [shortcut], image_path))
        if has_barriers:
            barrier_img = add_barrier_layer(np_img)
            barrier_path = change_filename_in_path(image_path, prefix=BARRIER_PREFIX)
            images.append(Icon(barrier_path.stem, barrier_img, [shortcut, "F"], barrier_path))
    return images

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
    

def show_cv2_img(cv2_img, shift_colors=False):
    if shift_colors:
        Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)).show()
    else:
        Image.fromarray(cv2_img).show()

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


def compare_images(original_image, image_to_compare):
    try:
        return rmse(original_image, image_to_compare), ssim(original_image, image_to_compare)
    except:
        return None, None

def compare_with_list(original_image, icons_list: List[Icon]):
    # Compare the input image with each image in the folder
    best_rmse = None
    best_ssim = None
    results_rmse = {}
    results_ssim ={}
    full_match_list_tmp = []
    for icon in icons_list:
        if icon.name.startswith(BARRIER_PREFIX):
            match = Match(cut_borders(original_image), icon)
        else:
            match = Match(original_image, icon)
        full_match_list_tmp.append(match)
        results_rmse[match.name] = match.rmse
        results_ssim[match.name] = match.ssim
        if not best_rmse or best_rmse.rmse > match.rmse:
            best_rmse = match
        if not best_ssim or best_ssim.ssim < match.ssim:
            best_ssim = match
    
    # Sort the results by similarity index
    results_rmse = sorted(results_rmse.items(), key=lambda x: x[1], reverse=False)
    results_ssim = sorted(results_ssim.items(), key=lambda x: x[1], reverse=True)
    
    percentage_rmse = calculate_percentage_difference(results_rmse[0][1], results_rmse[1][1])
    percentage_ssim = calculate_percentage_difference(results_ssim[0][1], results_ssim[1][1])
    if best_rmse != best_ssim:
        print(f"RMSE: {percentage_rmse:.2f} - {results_rmse}")
        print(f"SSIM: {percentage_ssim:.2f} - {results_ssim}")
    if percentage_ssim > 0: #Check a good number
        return best_ssim
    else:
        return best_rmse

def calculate_percentage_difference(num1, num2):
    average = (num1 + num2) / 2
    percentage_difference = abs((num1 - num2) / average) * 100
    return percentage_difference

def predict(original_image, icons_list) -> Match:
    img = original_image.resize(downscale_res, Image.BILINEAR)
    np_img = np.array(img)
    return compare_with_list(np_img, icons_list)
    

def capture_board_screensot():
    global board_top_left, board_bottom_right, custom_board_image
    if custom_board_image:
        return Image.open(custom_board_image)
    else:
        x0 = board_top_left[0]
        x1 = board_bottom_right[0] - board_top_left[0]
        y0 = board_top_left[1]
        y1 = board_bottom_right[1] - board_top_left[1]
        img = pyautogui.screenshot(region=(x0, y0, x1, y1))
        img.save('last_board.png')
    return img

def start(request_values, has_barriers):
    img = capture_board_screensot()
    icons_list = load_icon_classes(request_values, has_barriers)
    cell_size = (img.size[0]/6, img.size[1]/6)
    match_list: List[Match] = []
    for y in range(0, 6):
        for x in range(0, 6):
            cell_box = (x*cell_size[0], y*cell_size[1], (x+1)*cell_size[0], (y+1)*cell_size[1])
            cell = img.crop(cell_box)
            result = predict(cell, icons_list)
            match_list.append(result)
    
    # img1 = concatenate_images([match.board_icon for match in match_list])
    # img2 = concatenate_images([match.match_icon for match in match_list])
    # show_list_images([img1, img2])
    
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

IMAGES_PATH = r"images\icons_final_custom_zoom"
test_scenarios = {
    "0": {
        "board_image": r"test_cases\board_crystal.bmp",
        "values": ([(Path(IMAGES_PATH, 'Altaria.png'), '1'), (Path(IMAGES_PATH, 'Dragonair.png'), (Path(IMAGES_PATH, 'Dragonite.png'), '3'),  '2'), (Path(IMAGES_PATH, 'Zygarde-50.png'), '4'), (Path(IMAGES_PATH, 'Metal.png'), '5'), (Path(IMAGES_PATH, 'air.png'), 'del')], True)
    },
    "1": {
        "board_image": r"test_cases\board_mega_altaria.bmp",
        "values": ([(Path(IMAGES_PATH, 'Mega_Altaria_zoomed.png'), '1'), (Path(IMAGES_PATH, 'Dragonair.png'), '2'), (Path(IMAGES_PATH, 'Dragonite.png'), '3'), (Path(IMAGES_PATH, 'Zygarde-50.png'), '4'), (Path(IMAGES_PATH, 'Metal.png'), '5'), (Path(IMAGES_PATH, 'Goomy.png'), '7'), (Path(IMAGES_PATH, 'air.png'), 'del')], True)
    }
}
    

if __name__ == "__main__":
    # custom_board_image = test_scenarios.get("1").get("board_image")
    values = test_scenarios.get("1").get("values")
    start(*values)