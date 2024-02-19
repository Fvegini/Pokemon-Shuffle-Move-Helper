from pathlib import Path
import cv2
import numpy as np

def find_matching_files(directory, prefix, suffix):
    directory_path = Path(directory)
    search_pattern1 = f"{prefix}_*[0-9]{suffix}"
    search_pattern2 = f"{prefix}{suffix}"
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
    np_img = cv2.imread(image_path.as_posix())
    np_img = resize_cv2_image(np_img, image_size)
    return np_img

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


def make_cell_list_from_img(img, with_text=False, red=None, blue=None):
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

            if not with_text:
                smaller_images.append(square)
            else:
                square_with_text = square.copy()
                text = f"{y//square_size+1},{x//square_size+1}"
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
                else:
                    smaller_images.append(square_with_text)


    return smaller_images