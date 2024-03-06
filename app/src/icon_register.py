from PIL import Image
import tkinter as tk
from src import match_icons
from pathlib import Path
import os
from src import constants, custom_utils
import customtkinter
import cv2

from src.classes import MatchResult

custom_downscale = (96,96)

class IconRegister(customtkinter.CTkToplevel):
    def __init__(self, root = None):
         
        super().__init__()
        self.root = root
        self.geometry("250x250")
        self.selected_image = None
        self.image_widgets = []
        self.scrollable_frame = customtkinter.CTkScrollableFrame(master=self)
        self.scrollable_frame.pack(expand=True, fill="both")
        self.create_widgets()
        self.configure_initial_geometry()
    
    def configure_initial_geometry(self):
        self.update()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight() - ( 2 * custom_utils.get_taskbar_size())

        x = int(screen_width / 2)
        y = 0

        app_width = self.winfo_width()
        
        # Set window geometry
        self.geometry(f"{app_width}x{screen_height}+{x}+{y}")
        self.after(500, self.focus)

    def create_widgets(self):
        index = 0
        self.match_result: MatchResult = self.root.execute_board_analysis(create_image=False, skip_shuffle_move=True)
        if self.match_result.match_list:
            ordered_list = custom_utils.sort_by_class_attribute(self.match_result.match_list, "cosine_similarity", False)
            for match in ordered_list:
                
                board_icon = custom_utils.resize_cv2_image(match.board_icon, custom_downscale)
                match_icon = custom_utils.resize_cv2_image(match.match_icon, custom_downscale)
                
                image = custom_utils.merge_cv2_images(board_icon, match_icon)

                text = f"{match.cosine_similarity*100:.1f}%"
                image = custom_utils.add_text_to_image(image, text)
                
                image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
                tk_image = customtkinter.CTkImage(image, size=image.size)
                self.image_widgets.append(tk_image)

                label = customtkinter.CTkLabel(self.scrollable_frame, image=tk_image, text="", cursor="hand2")
                label.image = tk_image  # Keep a reference to avoid garbage collection
                label.bind("<Button-1>", lambda event, board_icon=match.board_icon: self.on_image_click(board_icon))
                label.grid(row=index, column=0, padx=10, pady=5)
                index+= 1

    def on_image_click(self, image):
        self.destroy()
        PokemonIconSelector(root=self.root, selected_image=image)
        

class PokemonIconSelector(customtkinter.CTkToplevel):
     
    def __init__(self, root = None, selected_image=None):
         
        super().__init__()
        self.title("Select The Pokemon That the New Icon will be Saved")
        self.root = root
        self.geometry("660x660")
        self.selected_image = selected_image
        self.scrollable_frame = customtkinter.CTkScrollableFrame(master=self)
        self.scrollable_frame.pack(expand=True, fill="both")
        self.create_widgets()
        self.configure_initial_geometry()
    
    def configure_initial_geometry(self):
        self.update()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight() - ( 2 * custom_utils.get_taskbar_size())

        x = int(screen_width / 2)
        y = 0

        app_width = self.winfo_width()
        
        # Set window geometry
        self.geometry(f"{app_width}x{screen_height}+{x}+{y}")
        self.after(500, self.focus)

    def create_widgets(self):
        num_columns = 6
        row_index = 1
        col_index = 0

        self.append_widget(Image.fromarray(cv2.cvtColor(self.selected_image, cv2.COLOR_RGB2BGR)), can_be_clicked=False, columnspan=num_columns)

        widgets_list = self.root.get_selected_images_widgets_list()
        for widgets in widgets_list:
            name = widgets[0].cget("text")
            original_image_cv2 = cv2.imread(Path(constants.IMAGES_PATH, widgets[0].cget("text")).as_posix())
            barrier_image_cv2 = custom_utils.add_transparent_image(original_image_cv2)
            self.append_widget(custom_utils.cv2_to_pil(original_image_cv2, custom_downscale), name, row_index, col_index, False)
            col_index, row_index = append_index(col_index, row_index, num_columns)
            self.append_widget(custom_utils.cv2_to_pil(barrier_image_cv2, custom_downscale), name, row_index, col_index, True)
            col_index, row_index = append_index(col_index, row_index, num_columns)
    
    def append_widget(self, image, image_name="", row_index=0, col_index=0, is_barrier=False, can_be_clicked=True, columnspan=1):
        tk_image = customtkinter.CTkImage(image, size=image.size)
        label = customtkinter.CTkLabel(self.scrollable_frame, image=tk_image, text="", cursor="hand2")
        label.image = tk_image  # Keep a reference to avoid garbage collection
        if can_be_clicked:
            label.bind("<Button-1>", lambda event, image_name=image_name, is_barrier=is_barrier: self.on_image_click(image_name, is_barrier))
        label.grid(row=row_index, column=col_index, padx=2, pady=2, columnspan=columnspan)
    
    def on_image_click(self, image_name, is_barrier):
        save_new_icon(self.selected_image, image_name, is_barrier)
        self.root.reveal_or_hide_barrier_img()
        self.root.clear_icons_cache()
        self.destroy()


def remove_icon(image_path):
    if os.path.exists(image_path):
        # print(f"Teria removido {image_path}")
        os.remove(image_path)
        print(f"Eliminado o Arquivo: {image_path}")

def save_new_icon(image, image_name, is_barrier):
    if is_barrier:
        os.makedirs(constants.IMAGES_BARRIER_PATH, exist_ok=True)
        image_path = Path(constants.IMAGES_BARRIER_PATH, image_name)
        image_path = custom_utils.get_next_filename(image_path)
    else:
        os.makedirs(constants.IMAGES_EXTRA_PATH, exist_ok=True)
        image_path = Path(constants.IMAGES_EXTRA_PATH, image_name)
        image_path = custom_utils.get_next_filename(image_path)
    custom_utils.resize_and_save_np_image(image_path, image, constants.downscale_res)
    
def append_index(col_index, row_index, num_columns=6):
    col_index += 1
    if col_index >= num_columns:
        col_index = 0
        row_index += 1
    return col_index, row_index