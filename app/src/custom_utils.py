from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def find_matching_files(directory, prefix, suffix):
    # Create a Path object for the directory
    directory_path = Path(directory)

    # Construct the search pattern
    search_pattern1 = f"{prefix}_*[0-9]{suffix}"
    search_pattern2 = f"{prefix}{suffix}"

    # Use glob to find matching files
    matching_files = list(directory_path.glob(search_pattern1)) + list(directory_path.glob(search_pattern2))

    return matching_files

def resize_cv2_image(image, target_size):
    try:
        return cv2.resize(image, target_size)
    except:
        return None

def open_and_resize_np_image(image_path, image_size):
    if type(image_path) == str:
        image_path = Path(image_path)
    np_img = np.array(Image.open(image_path.as_posix()).convert('RGB'))
    np_img = resize_cv2_image(np_img,image_size)
    return np_img

def merge_pil_images(image1, image2):
    # Get the width and height of each image
    width1, height1 = image1.size
    width2, height2 = image2.size

    # Calculate the width and height of the new image
    new_width = width1 + width2
    new_height = max(height1, height2)

    # Create a new image with the calculated size
    merged_image = Image.new("RGB", (new_width, new_height))

    # Paste the first image on the left
    merged_image.paste(image1, (0, 0))

    # Paste the second image on the right
    merged_image.paste(image2, (width1, 0))

    # Save the merged image
    return merged_image

def merge_pil_images_list(image_list):
    # Get the total width and maximum height
    total_width = sum(img.width for img in image_list)
    max_height = max(img.height for img in image_list)

    # Create a new blank image with the calculated dimensions
    merged_image = Image.new("RGB", (total_width, max_height))

    # Paste each image horizontally
    current_x = 0
    for img in image_list:
        merged_image.paste(img, (current_x, 0))
        current_x += img.width

    return merged_image


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
        taskbar_size = taskbar_info.bottom - taskbar_info.top

        return taskbar_size
    except:
        return 0
    
def show_list_images(images):
    concatenated_image = concatenate_list_images(images)
    show_cv2_img(concatenated_image)

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

def show_cv2_img(cv2_img, shift_colors=False):
    if shift_colors:
        Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)).show()
    else:
        Image.fromarray(cv2_img).show()

def create_blank_square(height, width):
    return np.ones((height, width, 3), dtype=np.uint8) * 255

def insert_in_middle(lst, new_value):
    new_list = []
    for index, item in enumerate(lst):
        new_list.append(item)
        if index+1 < len(lst):
            new_list.append(new_value)
    return new_list


def sort_by_class_attribute(obj_list, attribute_name):
    try:
        # Use the getattr function to dynamically get the attribute value
        sorted_list = sorted(obj_list, key=lambda x: getattr(x, attribute_name))
        return sorted_list
    except AttributeError:
        print(f"Attribute '{attribute_name}' not found in the class.")
        return obj_list

def concatenate_cv2_images(image_list, grid_size=(6, 6), spacing=10):
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