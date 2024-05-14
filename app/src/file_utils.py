from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def find_matching_files(directory, prefix, suffix):
    directory_path = Path(directory)
    search_pattern1 = f"{prefix}_[0-9]*{suffix}"
    search_pattern2 = f"{prefix}{suffix}"
    matching_files = list(directory_path.glob(search_pattern1)) + list(directory_path.glob(search_pattern2))
    return matching_files


def open_cv2_image(image_path):
    np_img = cv2.imread(image_path)
    if np_img is not None:
        return np_img
    try:
        return cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    except:
        return None
    



def open_and_resize_np_image(image_path, image_size):
    if type(image_path) == str:
        image_path = Path(image_path)
    np_img = open_cv2_image(image_path.as_posix())
    np_img = cv2.resize(np_img, image_size)
    return np_img

def show_cv2_as_pil(cv2_image):
    Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_RGB2BGR)).show()

def show_list_images(images):
    concatenated_image = concatenate_list_images(images)
    show_cv2_as_pil(concatenated_image)

def create_blank_square(height, width):
    return np.ones((height, width, 3), dtype=np.uint8) * 255

def insert_in_middle(lst, new_value):
    new_list = []
    for index, item in enumerate(lst):
        new_list.append(item)
        if index+1 < len(lst):
            new_list.append(new_value)
    return new_list


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