from PIL import Image
import tkinter as tk
from src import match_icons
from pathlib import Path
import os
from src import constants, custom_utils
import customtkinter
import cv2
class BoardIconSelector(tk.Toplevel):
     
    def __init__(self, master = None, root = None, folder = ""):
         
        super().__init__(master = master)
        self.title(f"Select a Icon to be Saved as a new {folder} type")
        self.root = root
        self.folder = folder
        self.selected_image = None
        self.image_widgets = []
        self.create_widgets()

    def create_widgets(self):
        num_columns = 6
        row_index = 0
        col_index = 0

        icons_list = match_icons.make_cell_list()
        for image in icons_list:
            image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            tk_image = customtkinter.CTkImage(image, size=image.size)
            self.image_widgets.append(tk_image)

            label = customtkinter.CTkLabel(self, image=tk_image, text="", cursor="hand2")
            label.image = tk_image  # Keep a reference to avoid garbage collection
            label.bind("<Button-1>", lambda event, custom_image=image: self.on_image_click(custom_image))
            label.grid(row=row_index, column=col_index, padx=10, pady=10)

            col_index += 1
            if col_index >= num_columns:
                col_index = 0
                row_index += 1
    
    def on_image_click(self, image):
        # image.show()
        self.selected_image = image
        self.root.open_app_register_screen()
        self.destroy()

class AppIconSelector(tk.Toplevel):
     
    def __init__(self, master = None, root = None, action = None):
         
        super().__init__(master = master)
        self.title("Select The Pokemon That the New Icon will be Saved")
        self.root = root
        self.action = action
        self.selected_image = None
        self.create_widgets()

    def create_widgets(self):
        num_columns = 6
        row_index = 0
        col_index = 0

        widgets_list = self.root.get_selected_images_widgets_list()
        for widgets in widgets_list:
            image = Image.open(Path(constants.IMAGES_PATH, widgets[0].cget("text")))
            tk_image = customtkinter.CTkImage(image, size=image.size)

            label = customtkinter.CTkLabel(self, image=tk_image, text="", cursor="hand2")
            label.image = tk_image  # Keep a reference to avoid garbage collection
            label.bind("<Button-1>", lambda event, image_name=widgets[0].cget("text"): self.on_image_click(image_name))
            label.grid(row=row_index, column=col_index, padx=10, pady=10)

            col_index += 1
            if col_index >= num_columns:
                col_index = 0
                row_index += 1
    
    def on_image_click(self, image_name):
        self.selected_image_name = image_name
        if self.action == "Remove_Barrier":
            # remove_icon(Path(constants.IMAGES_BARRIER_PATH, image_name))
            ExtraIconSelector(root=self.root, selected_image = image_name, action=self.action)
        elif self.action == "Remove_Extra":
            ExtraIconSelector(root=self.root, selected_image = image_name, action=self.action)
        else:
            save_new_icon(self.root.board_image_selector.selected_image, image_name, self.root.board_image_selector.folder)
        self.root.reveal_or_hide_barrier_img()
        self.destroy()


class ExtraIconSelector(tk.Toplevel):
     
    def __init__(self, master = None, root = None, selected_image = None, action = None):
         
        super().__init__(master = master)
        self.title("Select The Extra Icon that you want to remove")
        self.root = root
        self.action = action
        self.selected_image = selected_image
        self.create_widgets()
        
    def create_widgets(self):
        num_columns = 6
        row_index = 0
        col_index = 0

        if self.action == "Remove_Extra":
            images_path = custom_utils.find_matching_files(constants.IMAGES_EXTRA_PATH, Path(self.selected_image).stem, ".*")
        else:
            images_path = custom_utils.find_matching_files(constants.IMAGES_BARRIER_PATH, Path(self.selected_image).stem, ".*")

        for image_path in images_path:
            image_path = Path(image_path)
            image = Image.open(Path(image_path))
            tk_image = customtkinter.CTkImage(image, size=image.size)

            label = customtkinter.CTkLabel(self, image=tk_image, text="", cursor="hand2")
            label.image = tk_image  # Keep a reference to avoid garbage collection
            label.bind("<Button-1>", lambda event, image_path=image_path: self.on_image_click(image_path))
            label.grid(row=row_index, column=col_index, padx=10, pady=10)

            col_index += 1
            if col_index >= num_columns:
                col_index = 0
                row_index += 1

    def on_image_click(self, image_path):
        self.image_path = image_path
        remove_icon(image_path)
        self.root.reveal_or_hide_barrier_img()
        self.destroy()

def remove_icon(image_path):
    if os.path.exists(image_path):
        # print(f"Teria removido {image_path}")
        os.remove(image_path)
        print(f"Eliminado o Arquivo: {image_path}")

def save_new_icon(image, image_name, folder):
    if folder == "barrier":
        os.makedirs(constants.IMAGES_BARRIER_PATH, exist_ok=True)
        image_path = Path(constants.IMAGES_BARRIER_PATH, image_name)
        image_path = get_next_filename(image_path)
    else:
        os.makedirs(constants.IMAGES_EXTRA_PATH, exist_ok=True)
        image_path = Path(constants.IMAGES_EXTRA_PATH, image_name)
        image_path = get_next_filename(image_path)
    image = image.resize(match_icons.downscale_res)
    image.save(image_path)
    
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