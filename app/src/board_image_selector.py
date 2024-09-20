from PIL import Image
import tkinter as tk
from src import match_icons
from pathlib import Path
import os
from src import constants, custom_utils
import customtkinter
import cv2
from src import log_utils
import src.file_utils

log = log_utils.get_logger()


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
        self.selected_image = image
        self.destroy()
        PokemonIconSelector(root=self.root, folder=self.folder)

class PokemonIconSelector(tk.Toplevel):
     
    def __init__(self, master = None, root = None, action = None, folder = None):
         
        super().__init__(master = master)
        self.title("Select The Pokemon That the New Icon will be Saved")
        self.root = root
        self.action = action
        self.folder=folder
        self.selected_image = None
        self.create_widgets()

    def create_widgets(self):
        num_columns = 6
        row_index = 0
        col_index = 0

        self.state('zoomed')

        # Create a Canvas and a Scrollbar
        canvas = tk.Canvas(self)
        scrollbar = customtkinter.CTkScrollbar(self, command=canvas.yview)
        
        # Create a frame inside the canvas that will contain the images
        scrollable_frame = tk.Frame(canvas)

        # Bind the scrollbar to the canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Add the scrollable frame inside the canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Configure the canvas to use the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add the scrollbar and canvas to the grid
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Ensure that the canvas expands to fill the available space
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Add the images to the scrollable frame
        widgets_list = self.root.get_selected_images_widgets_list()
        for widgets in widgets_list:
            if self.folder == "barrier":
                image_cv2 = custom_utils.open_cv2_image(custom_utils.verify_or_update_png_path(Path(constants.IMAGES_PATH, widgets[0].cget("text"))).as_posix())
                image_cv2 = custom_utils.add_transparent_image(image_cv2)
                image = Image.fromarray(cv2.cvtColor(image_cv2, cv2.COLOR_RGB2BGR))
            else:
                image = Image.open(custom_utils.verify_or_update_png_path(Path(constants.IMAGES_PATH, widgets[0].cget("text"))))
            tk_image = customtkinter.CTkImage(image, size=image.size)

            label = customtkinter.CTkLabel(scrollable_frame, image=tk_image, text="", cursor="hand2")
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
            images_path = src.file_utils.find_matching_files(constants.IMAGES_EXTRA_PATH, Path(self.selected_image).stem, ".png")
        else:
            images_path = src.file_utils.find_matching_files(constants.IMAGES_BARRIER_PATH, Path(self.selected_image).stem, ".png")

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
        self.root.clear_icons_cache()
        self.destroy()

def remove_icon(image_path):
    if os.path.exists(image_path):
        os.remove(image_path)
        log.info(f"Eliminado o Arquivo: {image_path}")

def save_new_icon(image, image_name, folder):
    if folder == "barrier":
        os.makedirs(constants.IMAGES_BARRIER_PATH, exist_ok=True)
        image_path = custom_utils.verify_or_update_png_path(Path(constants.IMAGES_BARRIER_PATH, image_name))
        image_path = custom_utils.get_next_filename(image_path)
    else:
        os.makedirs(constants.IMAGES_EXTRA_PATH, exist_ok=True)
        image_path = custom_utils.verify_or_update_png_path(Path(constants.IMAGES_EXTRA_PATH, image_name))
        image_path = custom_utils.get_next_filename(image_path)
    image = image.resize(constants.downscale_res)
    image_path = custom_utils.verify_or_update_png_path(image_path)
    image.save(image_path)
