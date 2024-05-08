from pathlib import Path
import cv2
import numpy as np
from src.classes import Match
from typing import List
from src import adb_utils, constants, custom_utils
from PIL import Image
import pyautogui
from src.config_utils import config_values, read_config

def find_matching_files(directory, prefix, suffix):
    directory_path = Path(directory)
    search_pattern1 = f"{prefix}_[0-9]*{suffix}"
    search_pattern2 = f"{prefix}{suffix}"
    matching_files = list(directory_path.glob(search_pattern1)) + list(directory_path.glob(search_pattern2))
    return matching_files

def resize_cv2_image(image, target_size):
    try:
        return cv2.resize(image, target_size)
    except:
        return None

def resize_cv2_with_scale(image, scale_percent):
    # Get the current dimensions of the image
    height, width = image.shape[:2]

    # Calculate the new dimensions
    new_width = int(width * scale_percent / 100)
    new_height = int(height * scale_percent / 100)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))

    return resized_image

def resize_image_to_fit(image, screen_width, screen_height):
    image_height, image_width = image.shape[:2]

    # Calculate the aspect ratios
    screen_aspect_ratio = screen_width / screen_height
    image_aspect_ratio = image_width / image_height

    # Determine which dimension to scale by
    if screen_aspect_ratio > image_aspect_ratio:
        # Scale by height
        scale_factor = screen_height / image_height
    else:
        # Scale by width
        scale_factor = screen_width / image_width

    # Resize the image
    resized_image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor)

    return resized_image


def resize_and_save_np_image(image_path, np_image, image_size):
    resized = resize_cv2_image(np_image, image_size)
    if isinstance(image_path, str):
        cv2.imwrite(image_path, resized)
    else:
        cv2.imwrite(image_path.as_posix(), resized)

def open_and_resize_np_image(image_path, image_size):
    if type(image_path) == str:
        image_path = Path(image_path)
    np_img = open_cv2_image(image_path.as_posix())
    np_img = resize_cv2_image(np_img, image_size)
    return np_img

def open_cv2_image(image_path):
    np_img = cv2.imread(image_path)
    if np_img is not None:
        return np_img
    try:
        return cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    except:
        return None
      
def cv2_to_pil(cv2_image, image_size=None):
    if image_size:
        cv2_image = resize_cv2_image(cv2_image, image_size)
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_RGB2BGR))

def pil_to_cv2(pil_image):
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def show_cv2_as_pil(cv2_image):
    Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_RGB2BGR)).show()

def get_taskbar_size():
    try:
        import ctypes
        from ctypes import wintypes
        # Get the handle of the taskbar
        taskbar_handle = ctypes.windll.user32.FindWindowW("Shell_traywnd", None)

        # Get the taskbar information
        taskbar_info = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(taskbar_handle, ctypes.byref(taskbar_info))

        # Calculate the taskbar size
        taskbar_size = taskbar_info.bottom - taskbar_info.top #type: ignore

        return taskbar_size
    except:
        return 0
    
def show_list_images(images):
    concatenated_image = concatenate_list_images(images)
    show_img(concatenated_image)

def concatenate_list_images(images, blank_space=40):
    max_height = max(image.shape[0] for image in images)

    blank_square = create_blank_square(max_height, blank_space)
    # Create new images with the maximum height
    
    new_images_test = insert_in_middle(images, blank_square)
    new_images = [np.zeros((max_height, image.shape[1], 3), dtype=np.uint8) for image in new_images_test]

    # Copy the content of the original images to the new images
    for i, image in enumerate(new_images_test):
        new_images[i][:image.shape[0], :, :] = image

    # Concatenate all images side by side
    return np.concatenate(new_images, axis=1)

def show_img(cv2_img):
    cv2.imshow("", cv2_img)
    
def create_blank_square(height, width):
    return np.ones((height, width, 3), dtype=np.uint8) * 255

def insert_in_middle(lst, new_value):
    new_list = []
    for index, item in enumerate(lst):
        new_list.append(item)
        if index+1 < len(lst):
            new_list.append(new_value)
    return new_list


def sort_by_class_attribute(obj_list, attribute_name, reverse=False):
    try:
        # Use the getattr function to dynamically get the attribute value
        sorted_list = sorted(obj_list, key=lambda x: getattr(x, attribute_name), reverse=reverse)
        return sorted_list
    except AttributeError:
        print(f"Attribute '{attribute_name}' not found in the class.")
        return obj_list

def merge_cv2_images(img1, img2, spacing=10):
    max_height = max(img1.shape[0], img2.shape[0])
    total_width = img1.shape[1] + spacing + img2.shape[1]

    # Create a blank white image with the determined dimensions
    output_img = np.ones((max_height, total_width, 3), dtype=np.uint8) * 255

    # Calculate the coordinates to place the first image
    y_offset1 = (max_height - img1.shape[0]) // 2
    x_offset1 = 0
    y1, y2 = y_offset1, y_offset1 + img1.shape[0]
    x1, x2 = x_offset1, x_offset1 + img1.shape[1]

    # Calculate the coordinates to place the second image
    y_offset2 = (max_height - img2.shape[0]) // 2
    x_offset2 = img1.shape[1] + spacing
    y3, y4 = y_offset2, y_offset2 + img2.shape[0]
    x3, x4 = x_offset2, x_offset2 + img2.shape[1]

    # Copy the first image to the left portion of the output image
    output_img[y1:y2, x1:x2] = img1

    # Copy the second image to the right portion of the output image with the specified spacing
    output_img[y3:y4, x3:x4] = img2

    return output_img


def concatenate_cv2_list_as_full_grid(image_list, grid_size=(6, 6), spacing=10):
    # Get image dimensions
    image_height, image_width, _ = image_list[0].shape

    # Calculate the size of the final image
    grid_width = grid_size[1] * image_width + (grid_size[1] - 1) * spacing
    grid_height = grid_size[0] * image_height + (grid_size[0] - 1) * spacing

    # Create a blank white image as the background
    result_image = np.ones((grid_height, grid_width, 3), dtype=np.uint8) * 255

    # Paste each image into the result image
    for i in range(grid_size[0]):
        for j in range(grid_size[1]):
            if not image_list:
                break
            current_image = image_list.pop(0)
            x_coordinate = j * (image_width + spacing)
            y_coordinate = i * (image_height + spacing)
            result_image[y_coordinate:y_coordinate + image_height, x_coordinate:x_coordinate + image_width, :] = current_image

    return result_image


def make_cell_list_from_img(img):
    height, width = img.shape[:2]

    new_height = height - (height % 6)
    new_width = width - (width % 6)

    lower_size = min(new_height, new_width)

    # Resize the image to new dimensions
    img = cv2.resize(img, (lower_size, lower_size))
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

            smaller_images.append(square)
            
    return smaller_images

def add_text_to_image(image, text):
    image_with_text = image.copy()
    text = str(text)
    font=cv2.FONT_HERSHEY_SIMPLEX
    pos=(0, 0)
    font_scale=1
    font_thickness=2
    text_color=(0, 255, 0)
    text_color_bg=(0, 0, 0)
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    cv2.rectangle(image_with_text, pos, (0 + text_w, 0 + text_h), text_color_bg, -1)
    cv2.putText(image_with_text, text, (0, 0 + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)
    return image_with_text

def make_match_image_comparison(result, match_list: List[Match]):
    try:
        update_match_with_result(result, match_list)

        final_image1 = concatenate_cv2_list_as_full_grid([match.board_icon for match in match_list])
        final_image2 = concatenate_cv2_list_as_full_grid([match.match_icon for match in match_list])

        return concatenate_list_images([final_image1, final_image2])
    except:
        return None

def extract_result_idx(result):
    try:
       red = result.split(":")[0].split("->")[0].strip()
       red_idx = coordinates_to_index(*red.split(","))
       blue = result.split(":")[0].split("->")[1].strip()
       blue_idx = coordinates_to_index(*blue.split(","))
       if red == "0,0" or blue == "0,0":
           return None, None
       return red_idx, blue_idx
    except:
        return None, None

def extract_result_position(result):
    try:
        result_str_list = result.split(":")[0].split("->")
        if result_str_list[0] == "0,0" or result_str_list[1] == "0,0":
           return None, None, None, None
        red_row, red_column = [int(point) for point in result_str_list[0].strip().split(",")]
        blue_row, blue_column = [int(point) for point in result_str_list[1].strip().split(",")]
        return red_row, red_column, blue_row, blue_column
    except:
        return None, None, None, None

def update_match_with_result(result, match_list: List[Match]):
    try:
       red = result.split(":")[0].split("->")[0].strip()
       red_idx = coordinates_to_index(*red.split(","))
       blue = result.split(":")[0].split("->")[1].strip()
       blue_idx = coordinates_to_index(*blue.split(","))
       if red == "0,0" or blue == "0,0":
           return
       match_list[red_idx].match_icon = add_layer(match_list[red_idx].match_icon, "red")
       match_list[blue_idx].match_icon = add_layer(match_list[blue_idx].match_icon, "blue")
    except:
        red = None
        blue = None

def coordinates_to_index(x, y, width=6):
    return ((int(x) - 1) * width) + (int(y) - 1)

def index_to_coordinates(index, width=6):
    x = index // width + 1
    y = index % width + 1
    return x, y

def add_layer(image, color):
    square_size = image.shape[0]
    transparent_layer = np.zeros((square_size, square_size, 3), dtype=np.uint8)
    if color == "red":
        transparent_layer[:, :] = (0, 0, 255)  # Red color
    elif color == "blue":
        transparent_layer[:, :] = (255, 0, 0)  # Blue color
    else:
        raise Exception("Wrong color")
    return cv2.addWeighted(image, 0.5, transparent_layer, 0.5, 0)

FROZEN_IMAGE = cv2.imread(Path(constants.ASSETS_PATH, "frozen.png").as_posix(), cv2.IMREAD_UNCHANGED)

def add_transparent_image(background, foreground=FROZEN_IMAGE):
    foreground_resized = cv2.resize(foreground, (background.shape[1], background.shape[0]))

    # Split the foreground image into RGB and alpha channels
    foreground_rgb = foreground_resized[..., :3]
    alpha = foreground_resized[..., 3]

    # Convert alpha to a 3-channel image
    alpha = cv2.merge([alpha, alpha, alpha])

    # Convert alpha to a float in range [0, 1]
    alpha = alpha.astype(float) / 255.0

    # Multiply the foreground and background images by the alpha channel
    foreground_final = cv2.multiply(alpha, foreground_rgb.astype(float))
    background_final = cv2.multiply(1.0 - alpha, background.astype(float))

    # Add the two images together
    composite_image = cv2.add(foreground_final, background_final)

    # Convert back to uint8
    composite_image = composite_image.astype('uint8')
    
    return composite_image

def get_next_filename(filepath):
    path = Path(filepath)
    base_name = path.stem
    suffix = path.suffix
    directory = path.parent

    # Check if the file already exists
    while path.exists():
        # Extract the base name and sequence number (if any)
        base_name_parts = base_name.rsplit('_', 1)
        if len(base_name_parts) == 2 and base_name_parts[1].isdigit():
            sequence_number = int(base_name_parts[1])
            base_name = base_name_parts[0]
        else:
            sequence_number = 0

        # Increment the sequence number
        sequence_number += 1

        # Construct the new filename
        base_name = f"{base_name}_{sequence_number}"

        # Update the path
        path = directory / f"{base_name}{suffix}"

    return path

def verify_shuffle_file(file_path: Path):
    if not file_path.exists():
        print(f"File {file_path.as_posix()} not found")


def get_center_positions_list(left_position, right_position):
    
    x0 = left_position[0]
    y0 = left_position[1]
    x1 = right_position[0]
    y1 = right_position[1]

    # Calculate the width and height of each sub-square
    width = (x1 - x0) / 6
    height = (y1 - y0) / 6
    
    # List to store the center points
    center_points_list = []
    
    
    # Iterate through each row and column
    for i in range(6):
        for j in range(6):
            # Calculate the center point of the current sub-square
            center_x = x0 + (j + 0.5) * width
            center_y = y0 + (i + 0.5) * height
            center_points_list.append((center_x, center_y))
    
    # Return the list of center points
    return center_points_list


def capture_screen_screenshot():
    adb_board = read_config().get("adb_board")
    if adb_board:
        return adb_utils.get_screenshot()
    else:
        return pyautogui.screenshot()


def capture_board_screensot(save=True, return_type="cv2"):
    adb_board = read_config().get("adb_board")
    if adb_board:
        # adb_utils.get_screen_positions()
        img = adb_utils.crop_board(adb_utils.get_screenshot())
        if return_type == "cv2":
            return img
        else:
            return custom_utils.cv2_to_pil(img)
    else:
        resolution = adb_utils.get_screen_resolution()
        r = constants.RESOLUTIONS[resolution]["Board"]
        board_top_left = (r[0], r[1])
        board_bottom_right = (r[2], r[3])

        x0 = board_top_left[0]
        x1 = board_bottom_right[0] - board_top_left[0]
        y0 = board_top_left[1]
        y1 = board_bottom_right[1] - board_top_left[1]
        # print(f"Screenshot at: {datetime.now()}")
        img = pyautogui.screenshot(region=(x0, y0, x1, y1))
        if save:
            img.save(constants.LAST_BOARD_IMAGE_PATH)
        if return_type == "cv2":
            return custom_utils.pil_to_cv2(img)
        else:
            return img
        
def remove_sequences(matrix):
    rows = len(matrix)
    cols = len(matrix[0])
    sequence_found = True

    while sequence_found:
        sequence_found = False

        # Check rows
        for i in range(rows):
            j = 0
            while j < cols - 2:
                if matrix[i][j] != 0 and matrix[i][j] == matrix[i][j+1] == matrix[i][j+2]:
                    matrix[i][j] = matrix[i][j+1] = matrix[i][j+2] = 0
                    sequence_found = True
                    j += 3
                else:
                    j += 1

        # Check columns
        for j in range(cols):
            i = 0
            while i < rows - 2:
                if matrix[i][j] != 0 and matrix[i][j] == matrix[i+1][j] == matrix[i+2][j]:
                    matrix[i][j] = matrix[i+1][j] = matrix[i+2][j] = 0
                    sequence_found = True
                    i += 3
                else:
                    i += 1

    return matrix

# # Example usage
# matrix = [
#     [1, 2, 2, 2, 5, 6],
#     [1, 2, 2, 2, 5, 6],
#     [1, 2, 2, 2, 5, 6],
#     [1, 2, 2, 2, 5, 6],
#     [1, 2, 3, 4, 5, 6],
#     [1, 2, 3, 4, 5, 6]
# ]

# updated_matrix = remove_sequences(matrix)

# # Check columns after removing rows
# updated_matrix = list(map(list, zip(*updated_matrix)))

# updated_matrix = remove_sequences(updated_matrix)

# # Revert the matrix back to original orientation
# updated_matrix = list(map(list, zip(*updated_matrix)))

# for row in updated_matrix:
#     print(row)
