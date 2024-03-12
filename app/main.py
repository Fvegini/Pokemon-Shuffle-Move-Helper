import os
import tkinter as tk
from tkinter import ttk
from typing import Any
import customtkinter
from PIL import Image
import keyboard
from src import match_icons, shuffle_config_files
from pathlib import Path
from src.board_image_selector import BoardIconSelector, PokemonIconSelector
from src import constants, custom_utils, load_from_shuffle, config_utils, mouse_utils
from src.execution_variables import execution_variables
import warnings
from CTkToolTip import CTkToolTip
from src.classes import MatchResult, Pokemon
from src.icon_register import IconRegister
from src import embed
from src import version
from src import splash
import cv2
import numpy as np
warnings.filterwarnings("ignore", category=UserWarning, message="CTkButton Warning: Given image is not CTkImage but*")

# from viztracer.decorator import trace_and_save

customtkinter.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
# customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ImageSelectorApp():

    def __init__(self, master):
        
        self.master = master
        self.master.title(f"Pokemon Shuffle Helper {version.current_version}")
        self.create_tab_menu()
        
        self.appview = customtkinter.CTkFrame(self.master)
        self.appview.pack(expand=1, fill=tk.X, pady=0, padx=0, anchor="nw")

        self.create_left_app_screen()
        self.create_right_app_screen()
        self.create_bottom_message()
        
        self.update_image_list()
        self.set_mega_list()
        self.load_last_team()
        self.update_preview_image()
        self.configure_initial_geometry()
        splash.close_splash()
        version.verify_new_version()

    def create_tab_menu(self):
        self.tabview = customtkinter.CTkTabview(self.master, height=100)
        self.tabview.pack(expand=1, fill=tk.X, pady=0, padx=0, anchor="nw")
        
        self.tab1 = self.tabview.add("Configurations")
        self.tab2 = self.tabview.add("Icons")
        self.tab3 = self.tabview.add("Execute")
        self.tabview._segmented_button.grid(sticky="W")
        self.tabview.pack_propagate(True)
        self.tab_button_style = {
            'compound': 'top',
            'width': 0,
            'fg_color': 'transparent',
            'text_color': ('gray10', 'gray90'),
            'hover_color': ('gray70', 'gray30'),
        }
        self.tab_comboboxmenu_style = {
            # 'width': 0,
            # 'fg_color': 'dark_color',
            # 'text_color': ('gray10', 'gray90'),
            # 'dropdown_hover_color': ('gray70', 'gray30'),
        }
        
        self.create_tab_1()
        self.create_tab_2()
        self.create_tab_3()
        
        self.tabview.set("Execute")

        
    def create_tab_1(self):
        frame1_1 = customtkinter.CTkFrame(self.tab1, fg_color="transparent")
        frame1_1_top = customtkinter.CTkFrame(frame1_1, fg_color="transparent")
        frame1_1_bottom = customtkinter.CTkFrame(frame1_1, fg_color="transparent")
        
        frame1_1.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame1_1_top.pack(side=tk.TOP)
        frame1_1_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab1, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        customtkinter.CTkLabel(frame1_1_bottom, text="Mouse Positions").pack(side=tk.BOTTOM, anchor=tk.S)

        icon = self.get_icon("mouse")

        # btn1_1_1 = customtkinter.CTkButton(frame1_1_top, text="Top Left", command=lambda: self.show_click_popup(click_counter= 1), image=icon, **self.tab_button_style)
        # btn1_1_2 = customtkinter.CTkButton(frame1_1_top, text="Bottom Right", command=lambda: self.show_click_popup(click_counter= 2), image=icon, **self.tab_button_style)
        btn1_1_3 = customtkinter.CTkButton(frame1_1_top, text="Board Position", command=lambda: self.show_board_position_selector_app(), image=icon, **self.tab_button_style)
        # btn1_1_4 = customtkinter.CTkButton(frame1_1_top, text="Return Position", command=lambda: self.show_click_popup(click_counter= 4), image=icon, **self.tab_button_style)

        # CTkToolTip(btn1_1_1, delay=0.5, message="Configure Board Top Left")
        # CTkToolTip(btn1_1_2, delay=0.5, message="Configure Board Bottom Right")
        CTkToolTip(btn1_1_3, delay=0.5, message="Configure Shuffle Move First Square")
        # CTkToolTip(btn1_1_4, delay=0.5, message="Configure Mouse Return Position")

        # btn1_1_1.pack(side=tk.LEFT)
        # btn1_1_2.pack(side=tk.LEFT)
        btn1_1_3.pack(side=tk.LEFT)
        # btn1_1_4.pack(side=tk.LEFT)

        frame1_2 = customtkinter.CTkFrame(self.tab1, fg_color="transparent")
        frame1_2_top = customtkinter.CTkFrame(frame1_2, fg_color="transparent")
        frame1_2_bottom = customtkinter.CTkFrame(frame1_2, fg_color="transparent")
        frame1_2.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame1_2_top.pack(side=tk.TOP)
        frame1_2_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab1, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        
        customtkinter.CTkLabel(frame1_2_bottom, text="Execution").pack(side=tk.BOTTOM, anchor=tk.S)
        
        frame1_2_top_1 = customtkinter.CTkFrame(frame1_2_top, fg_color="transparent")
        frame1_2_top_2 = customtkinter.CTkFrame(frame1_2_top, fg_color="transparent")
        frame1_2_top_1.pack(side=tk.LEFT)
        frame1_2_top_2.pack(side=tk.LEFT)
        
        
        self.stage_combobox_var = customtkinter.StringVar(value="NORMAL")
        self.stage_combobox = customtkinter.CTkComboBox(frame1_2_top_1, values=constants.move_stages.values(),
                                     command=self.set_stage_var, variable=self.stage_combobox_var, state="readonly", **self.tab_comboboxmenu_style)
        
        self.strategy_combobox_var = customtkinter.StringVar(value="Total Blocks")
        self.strategy_combobox = customtkinter.CTkComboBox(frame1_2_top_1, values=constants.move_strategy.values(),
                                     command=self.set_strategy_var, variable=self.strategy_combobox_var, state="readonly", **self.tab_comboboxmenu_style)
        
        self.stage_combobox.pack(side=tk.BOTTOM)
        self.strategy_combobox.pack(side=tk.BOTTOM)

        customtkinter.CTkLabel(frame1_2_top_2, text="Stage Type").pack(side=tk.BOTTOM, anchor=tk.E)
        customtkinter.CTkLabel(frame1_2_top_2, text="Move Strategy").pack(side=tk.BOTTOM, anchor=tk.E)

    def set_stage_var(self, choice):
        execution_variables.current_stage = [k for k, v in constants.move_stages.items() if v == choice][0]
        execution_variables.has_modifications = True

    def set_strategy_var(self, choice):
        execution_variables.current_strategy = [k for k, v in constants.move_strategy.items() if v == choice][0]
        execution_variables.has_modifications = True

    def create_tab_2(self):
        frame2_1 = customtkinter.CTkFrame(self.tab2, fg_color="transparent")
        frame2_1_top = customtkinter.CTkFrame(frame2_1, fg_color="transparent")
        frame2_1_bottom = customtkinter.CTkFrame(frame2_1, fg_color="transparent")
        frame2_1.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame2_1_top.pack(side=tk.TOP)
        frame2_1_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab2, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        frame2_2 = customtkinter.CTkFrame(self.tab2, fg_color="transparent")
        frame2_2_top = customtkinter.CTkFrame(frame2_2, fg_color="transparent")
        frame2_2_bottom = customtkinter.CTkFrame(frame2_2, fg_color="transparent")
        frame2_2.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame2_2_top.pack(side=tk.TOP)
        frame2_2_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab2, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)


        frame2_3 = customtkinter.CTkFrame(self.tab2, fg_color="transparent")
        frame2_3_top = customtkinter.CTkFrame(frame2_3, fg_color="transparent")
        frame2_3_bottom = customtkinter.CTkFrame(frame2_3, fg_color="transparent")
        frame2_3.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame2_3_top.pack(side=tk.TOP)
        frame2_3_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab2, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)        


        #Block 1
        customtkinter.CTkLabel(frame2_1_bottom, text="Current Team").pack(side=tk.BOTTOM)
        btn2_1_1 = customtkinter.CTkButton(frame2_1_top, text="Load Team", command=self.load_team, image=self.get_icon("cloud-download-alt"), **self.tab_button_style)
        CTkToolTip(btn2_1_1, delay=0.5, message="Load Team From Shuffle Move Config File")
        btn2_1_1.pack(side=tk.LEFT, padx=5)
        
        
        #Block 2
        customtkinter.CTkLabel(frame2_2_bottom, text="Register Icons").pack(side=tk.BOTTOM)
        btn2_2_1 = customtkinter.CTkButton(frame2_2_top, text="Register Barrier", command=lambda: self.open_create_register_screen(folder="barrier"), image=self.get_icon("plus"), **self.tab_button_style)
        CTkToolTip(btn2_2_1, delay=0.5, message="Create or Substitute the Barrier Icon")
        btn2_2_1.pack(side=tk.LEFT, padx=5)
        btn2_2_2 = customtkinter.CTkButton(frame2_2_top, text="Register Extra", command=lambda: self.open_create_register_screen(folder="extra"), image=self.get_icon("plus"), **self.tab_button_style)
        CTkToolTip(btn2_2_2, delay=0.5, message="Insert a new Extra Icon")
        btn2_2_2.pack(side=tk.LEFT, padx=5)


        # #Block 3
        customtkinter.CTkLabel(frame2_3_bottom, text="Remove Icons").pack(side=tk.BOTTOM)
        btn2_3_1 = customtkinter.CTkButton(frame2_3_top, text="Remove Barrier", command=lambda: self.open_remove_register_screen(action="Remove_Barrier"), image=self.get_icon("trash-alt"), **self.tab_button_style)
        CTkToolTip(btn2_3_1, delay=0.5, message="Remove the Barrier Icon")
        btn2_3_1.pack(side=tk.LEFT, padx=5)
        btn2_3_2 = customtkinter.CTkButton(frame2_3_top, text="Remove Extra", command=lambda: self.open_remove_register_screen(action="Remove_Extra"), image=self.get_icon("trash-alt"), **self.tab_button_style)
        CTkToolTip(btn2_3_2, delay=0.5, message="Remove One of the Extra Icons")
        btn2_3_2.pack(side=tk.LEFT, padx=5)

    def create_tab_3(self):
        frame3_1 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_1_top = customtkinter.CTkFrame(frame3_1)
        frame3_1_bottom = customtkinter.CTkFrame(frame3_1)
        frame3_1.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_1_top.pack(side=tk.TOP)
        frame3_1_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        customtkinter.CTkLabel(frame3_1_bottom, text="Board Capture Mode", bg_color="transparent").pack(side=tk.BOTTOM)
        
        
        self.has_barrier_var = tk.BooleanVar(value=config_utils.config_values.get("has_barrier")) 
        self.control_loop_var = tk.BooleanVar(value=False)

       
        self.control_loop_switch = customtkinter.CTkSwitch(frame3_1_top, text="Capture Loop", variable=self.control_loop_var, onvalue=True, offvalue=False, command=lambda: self.control_loop_function())
        self.has_barrier_switch = customtkinter.CTkSwitch(frame3_1_top, text="Has Barriers", variable=self.has_barrier_var, command=self.reveal_or_hide_barrier_img)
        self.control_loop_switch.pack(side=tk.TOP, anchor=tk.W, padx=5)
        self.has_barrier_switch.pack(side=tk.TOP, anchor=tk.W, padx=5)
        
        keyboard.add_hotkey('f3', lambda:  self.control_loop_switch.toggle())
        keyboard.add_hotkey('f4', lambda: self.has_barrier_switch.toggle())
        
        frame3_2 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_2_top = customtkinter.CTkFrame(frame3_2, fg_color="transparent")
        frame3_2_bottom = customtkinter.CTkFrame(frame3_2, fg_color="transparent")
        frame3_2.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_2_top.pack(side=tk.TOP)
        frame3_2_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        customtkinter.CTkLabel(frame3_2_bottom, text="").pack(side=tk.BOTTOM)

        btn3_2_1 = customtkinter.CTkButton(frame3_2_top, text="Execute", command=lambda: self.execute_board_analysis(source="button"), image=self.get_icon("play-circle"), **self.tab_button_style)
        CTkToolTip(btn3_2_1, delay=0.5, message="Execute (F2)")
        btn3_2_1.pack(side=tk.LEFT)
        keyboard.add_hotkey('f2', lambda: self.execute_board_analysis(source="shortcut")) #type: ignore
        
        btn2_1_1 = customtkinter.CTkButton(frame3_2_top, text="Load Team", command=self.load_team, image=self.get_icon("cloud-download-alt"), **self.tab_button_style)
        CTkToolTip(btn2_1_1, delay=0.5, message="Load Team From Shuffle Move Config File")
        btn2_1_1.pack(side=tk.LEFT, padx=5)
        customtkinter.CTkButton(frame3_2_top, text="Current Board", command=self.show_current_board_with_matches, image=self.get_icon("search"), **self.tab_button_style).pack(side=tk.LEFT)

        frame3_3 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_3_top = customtkinter.CTkFrame(frame3_3, fg_color="transparent")
        frame3_3_bottom = customtkinter.CTkFrame(frame3_3, fg_color="transparent")
        frame3_3.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_3_top.pack(side=tk.TOP)
        frame3_3_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        
        customtkinter.CTkLabel(frame3_3_bottom, text="Register Icons").pack(side=tk.BOTTOM)
        btn3_3_1 = customtkinter.CTkButton(frame3_3_top, text="Register Icon", command=lambda: self.register_new_icon(), image=self.get_icon("plus"), **self.tab_button_style)
        CTkToolTip(btn3_3_1, delay=0.5, message="Register a New Icon")
        btn3_3_1.pack(side=tk.LEFT, padx=5)
        btn3_3_2 = customtkinter.CTkButton(frame3_3_top, text="Register Barrier", command=lambda: self.open_create_register_screen(folder="barrier"), image=self.get_icon("plus"), **self.tab_button_style)
        CTkToolTip(btn3_3_2, delay=0.5, message="Create or Substitute the Barrier Icon")
        btn3_3_2.pack(side=tk.LEFT, padx=5)
        btn3_3_3 = customtkinter.CTkButton(frame3_3_top, text="Register Extra", command=lambda: self.open_create_register_screen(folder="extra"), image=self.get_icon("plus"), **self.tab_button_style)
        CTkToolTip(btn3_3_3, delay=0.5, message="Insert a new Extra Icon")
        btn3_3_3.pack(side=tk.LEFT, padx=5)



        frame3_4 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_4_top = customtkinter.CTkFrame(frame3_4, fg_color="transparent")
        frame3_4_bottom = customtkinter.CTkFrame(frame3_4, fg_color="transparent")
        frame3_4.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_4_top.pack(side=tk.TOP)
        frame3_4_bottom.pack(side=tk.BOTTOM)
        ttk.Separator(self.tab1, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        
        customtkinter.CTkLabel(frame3_4_bottom, text="Execution").pack(side=tk.BOTTOM, anchor=tk.S)
        
        frame3_4_top_1 = customtkinter.CTkFrame(frame3_4_top, fg_color="transparent")
        frame3_4_top_2 = customtkinter.CTkFrame(frame3_4_top, fg_color="transparent")
        frame3_4_top_1.pack(side=tk.LEFT)
        frame3_4_top_2.pack(side=tk.LEFT)
        
        
        customtkinter.CTkComboBox(frame3_4_top_1, values=constants.move_stages.values(),
                                     command=self.set_stage_var, variable=self.stage_combobox_var, state="readonly", **self.tab_comboboxmenu_style).pack(side=tk.BOTTOM)
        
        customtkinter.CTkComboBox(frame3_4_top_1, values=constants.move_strategy.values(),
                                     command=self.set_strategy_var, variable=self.strategy_combobox_var, state="readonly", **self.tab_comboboxmenu_style).pack(side=tk.BOTTOM)
        
        customtkinter.CTkLabel(frame3_4_top_2, text="Stage Type").pack(side=tk.BOTTOM, anchor=tk.E)
        customtkinter.CTkLabel(frame3_4_top_2, text="Move Strategy").pack(side=tk.BOTTOM, anchor=tk.E)

    def create_left_app_screen(self):

        self.images_frame = customtkinter.CTkFrame(self.appview, corner_radius=0)
        self.images_frame.grid_rowconfigure(1, weight=1)
        self.images_frame.grid_columnconfigure(0, weight=1)

        self.images_frame.pack(side=tk.LEFT, padx=10, pady=10, anchor="nw")


        self.magnifier_label = customtkinter.CTkLabel(self.images_frame, text="🔍", font=("Arial", 16), compound="left")
        self.magnifier_label.grid(row=0, column=0, sticky="w", padx=(10, 0))


        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_image_list)
        
        self.search_entry = customtkinter.CTkEntry(self.images_frame, placeholder_text="Search...", textvariable=self.search_var, width=100)
        self.search_entry.grid(row=0, column=1, sticky='w', padx=(0, 0), pady=(5, 0))
        
        self.image_listbox = tk.Listbox(self.images_frame, selectmode=tk.SINGLE, width=20)
        self.image_listbox.grid(row=1, column=0, sticky='w', padx=(10, 0), pady=(10,10), columnspan=2)

        scrollbar = tk.Scrollbar(self.images_frame, orient="vertical")
        scrollbar.config(command=self.image_listbox.yview)
        scrollbar.grid(row=1, column=2, sticky='ns', padx=(0, 10), pady=(10,10))

        self.image_listbox.config(yscrollcommand=scrollbar.set)

        self.image_preview = customtkinter.CTkLabel(self.images_frame, text="")
        self.image_preview.grid(row=1, column=3, padx=5, pady=5, sticky='w')

    def create_bottom_message(self):
        self.info_message = customtkinter.CTkLabel(self.appview, text=f"Model: {embed.model_path.parent.name}")
        self.info_message.pack(side=tk.BOTTOM, fill=tk.X)

    def create_right_app_screen(self):
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.appview, width=200, height=200, orientation="horizontal")
        self.scrollable_frame.pack(side=tk.TOP, fill=tk.X)

    def configure_initial_geometry(self):
        self.master.update()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight() - custom_utils.get_taskbar_size()

        width = int(screen_width / 2)
        height = int(screen_height / 2)

        # Calculate window position at the bottom-right corner
        x = screen_width - width
        y = screen_height - height

        # Set window geometry
        self.master.geometry(f"{width}x{height}+{x}+{y}")
        self.master.update()
        if self.master.winfo_width() != width:
            scale_factor = self.master.winfo_width() / width
            self.master.geometry(f"{int(width*scale_factor)}x{int(height*scale_factor)}+{x}+{y}")
        self.check_current_position()
        if os.getenv("DEV_MODE") == "1":
            print("Dev Mode Activated")
            self.force_update_mouse_buttons()


    def check_current_position(self):
        self.master.update()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        app_width = self.master.winfo_width()
        app_height = self.master.winfo_height()
        screen_position_x = self.master.winfo_x()
        screen_position_y = self.master.winfo_y()
        print(f"The screen size is {screen_width}x{screen_height}, the app size is {app_width}x{app_height} and its position is ({screen_position_x}, {screen_position_y}).")

    def update_preview_image(self, event=None):
        try:
            selected_index = self.image_listbox.curselection()
            if not selected_index:
                selected_index = 1
            selected_file = self.image_listbox.get(selected_index)
            image_path = os.path.join(constants.IMAGES_PATH, selected_file) 
            image = Image.open(image_path)
            image.thumbnail((50, 50))
            photo = customtkinter.CTkImage(image, size=image.size)

            self.image_preview.configure(image=photo)
            self.image_preview.image = photo
        except:
            pass

    def set_mega_list(self):
        self.mega_list = []
        folder_path = constants.IMAGES_PATH
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")) and "mega_" in f.lower()]
        for image_file in image_files:
            if image_file.startswith("Mega_"):
             self.mega_list.append(image_file.split("Mega_")[1])

       

    def update_image_list(self, *args):
        search_term = self.search_var.get().lower()
        search_term = search_term.replace(" ", "_")
        self.image_listbox.delete(0, tk.END)

        folder_path = constants.IMAGES_PATH
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")) and search_term in f.lower()]
        image_files = sorted(image_files, key=lambda word: (word[0] != '_', word))

        for image_file in image_files:
            if not image_file.startswith("Mega_"):
                self.image_listbox.insert(tk.END, image_file)

        self.image_listbox.bind("<<ListboxSelect>>", self.update_preview_image)
        self.image_listbox.bind("<Double-Button-1>", self.select_image)

    def select_image(self, event=None):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_file = self.image_listbox.get(selected_index)
            self.insert_image_widget(selected_file)
    
    def insert_image_widget(self, selected_file, disabled=False, skip_barrier=False):
        image_path = Path(constants.IMAGES_PATH, selected_file)  # Change this to the path of your folder
        if not image_path.suffix:
            image_path = image_path.with_suffix('.png')
            selected_file = selected_file + ".png"

        if not image_path.exists():
            return

        if any([value for value in self.get_selected_images_widgets_list() if value[0].master.name == selected_file]):
            return

        execution_variables.has_modifications = True

        # Display in the selected images panel
        selected_image_frame = customtkinter.CTkFrame(self.scrollable_frame)
        selected_image_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=5, anchor=tk.CENTER)
        selected_image_frame.original_fg_color = selected_image_frame._fg_color
        selected_image_frame.name = selected_file

        # Create a thumbnail for preview
        image = Image.open(image_path)
        image.thumbnail((50,50))
        photo = customtkinter.CTkImage(image, size=(50, 50))

        selected_image_label = customtkinter.CTkLabel(selected_image_frame, image=photo, text=selected_file, compound=tk.TOP)
        selected_image_label.pack()
        
        self.insert_extra_images_tooltip(image_path, selected_image_label)
        
        remove_button = customtkinter.CTkButton(selected_image_frame, text="Remove", width=80, command=lambda: self.remove_selected_image(selected_image_frame, image_path))
        remove_button.pack(pady=5)

        checkbox_disable: customtkinter.CTkCheckBox = customtkinter.CTkCheckBox(selected_image_frame, text="Disable", checkbox_width=12, checkbox_height=12, corner_radius=0, onvalue=True, offvalue=False, command=lambda: self.checkbox_disable_clicked(checkbox_disable, selected_image_frame))
        checkbox_disable.pack(padx=(25, 0))

        checkbox_stage: customtkinter.CTkCheckBox = customtkinter.CTkCheckBox(selected_image_frame, text="Stage Add", checkbox_width=12, checkbox_height=12, corner_radius=0, onvalue=True, offvalue=False, command=lambda: self.checkbox_stage_add_clicked(checkbox_stage, selected_image_frame))
        checkbox_stage.pack(padx=(25, 0))

        selected_image_frame.pokemon = Pokemon(selected_image_frame.name, checkbox_disable.get(), checkbox_stage.get())

        if disabled:
            checkbox_disable.toggle()
          
        if selected_file in self.mega_list:
            checkbox_mega: Any = customtkinter.CTkCheckBox(selected_image_frame, text="Mega", checkbox_width=12, checkbox_height=12, corner_radius=0, onvalue=True, offvalue=False, command=lambda: self.checkbox_mega_click(checkbox_mega, selected_image_frame))
            checkbox_mega.pack(padx=(25, 0))
            selected_image_frame.megaed = False
            selected_image_frame.checkbox_mega = checkbox_mega


        if self.has_barrier_var.get() and not skip_barrier:
            self.reveal_or_hide_barrier_img()
            
        

    def checkbox_disable_clicked(self, checkbox, selected_image_frame):
        self.clear_icons_cache()
        if checkbox.get():
            selected_image_frame.configure(fg_color="gray")
            selected_image_frame.pokemon.disabled = True
        else:
            selected_image_frame.configure(fg_color=selected_image_frame.original_fg_color)
            selected_image_frame.pokemon.disabled = False

    def checkbox_stage_add_clicked(self, checkbox, selected_image_frame):
        self.clear_icons_cache()
        if checkbox.get():
            selected_image_frame.pokemon.stage_added = True
        else:
            selected_image_frame.pokemon.stage_added = False

    def checkbox_mega_click(self, checkbox, selected_image_frame):
        for widget in self.get_selected_images_widgets_list():
            if widget[0].master.name.startswith("Mega_"):
                widget[0].master.destroy()
                continue
            if hasattr(widget[0].master, "megaed") and widget[0].master.name != selected_image_frame.name:
                widget[0].master.checkbox_mega.deselect()
        if checkbox.get():
            self.insert_image_widget(f"Mega_{selected_image_frame.name}")
        return

    def insert_extra_images_tooltip(self, image_path, selected_image_label):
        image_list = []
        barrier_image_list = []
        original_path = Path(image_path)
        images_path_list = [original_path] + custom_utils.find_matching_files(constants.IMAGES_EXTRA_PATH, original_path.stem, ".png")
        barrier_images_path_list = custom_utils.find_matching_files(constants.IMAGES_BARRIER_PATH, original_path.stem, ".png")

        for image_path in images_path_list:
            icon_image = Image.open(image_path)
            icon_image.thumbnail((50,50))
            image_list.append(icon_image)

        for image_path in barrier_images_path_list:
            icon_image = Image.open(image_path)
            icon_image.thumbnail((50,50))
            barrier_image_list.append(icon_image)
        
        extra_complete_image = merge_tooltip_pil_images(image_list, barrier_image_list)
        extra_photo = customtkinter.CTkImage(extra_complete_image, size=extra_complete_image.size)
        CTkToolTip(selected_image_label, delay=0.5, message="", image=extra_photo)

    def destroy_selected_pokemons(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
    def remove_selected_image(self, frame, image_path):
        frame.destroy()
        # Remove the image from the selected images list

    def register_new_icon(self):
        self.disable_loop()
        img_list = []
        for i in range(0,6):
            img_list.append(match_icons.capture_board_screensot(save=False, return_type="PIL"))
        for idx, screen in enumerate(img_list):
            cv2_board = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            IconRegister(root=self, title=idx, forced_board_image=cv2_board)

    def open_create_register_screen(self, folder):
        self.disable_loop()
        self.board_image_selector = BoardIconSelector(root=self, folder=folder)
    
    def open_remove_register_screen(self, action=None):
        self.disable_loop()
        self.app_image_selector = PokemonIconSelector(root=self, action=action)

    def clear_icons_cache(self):
        match_icons.loaded_icons_cache = {}
        execution_variables.has_modifications = True

    def get_selected_images_widgets_list(self):
        widget_list = []
        for frame in self.scrollable_frame.winfo_children():
            if isinstance(frame, customtkinter.CTkFrame):
                image_widgets = frame.winfo_children()
                widget_list.append(image_widgets)
        return widget_list

    def execute_board_analysis(self, source=None, create_image=False, skip_shuffle_move=False, forced_board_image=None) -> MatchResult:
        pokemons_list = self.extract_pokemon_list()
        return match_icons.start_from_helper(pokemons_list, self.has_barrier_var.get(), root=self, source=source, create_image=create_image, skip_shuffle_move=skip_shuffle_move, forced_board_image=forced_board_image)

    def extract_pokemon_list(self):
        pokemons_list = []
        for image_widgets in self.get_selected_images_widgets_list():
            if hasattr(image_widgets[0].master, "pokemon"):
                pokemon = image_widgets[0].master.pokemon
                pokemons_list.append(pokemon)
        return pokemons_list

    def get_execution_values(self, image_widgets):
        try:
            return (Path(constants.IMAGES_PATH, image_widgets[0].cget("text")), image_widgets[2].get(), image_widgets[3].get())
        except:
            print(f"Error on widget: {image_widgets}")
            return None

    def show_board_position_selector_app(self):
        mouse_utils.BoardPositionSelectorApp(master=self.master, selector_app=self)

    def disable_loop(self):
        if self.control_loop_var.get():
            self.control_loop_switch.toggle()
        

    def control_loop_function(self):
        if not self.control_loop_var.get():
            return
        else:
            result = self.execute_board_analysis(source="loop")
            if not result:
                self.check_job = self.master.after(3000, self.control_loop_function)
            else:
                self.check_job = self.master.after(200, self.control_loop_function)

    def get_icon(self, icon_name):
        if customtkinter.get_appearance_mode() == "Dark":
            return customtkinter.CTkImage(Image.open(Path("assets", "fonts", f"{icon_name}-solid_w.png")), size=(25, 25))
        else:
            return customtkinter.CTkImage(Image.open(Path("assets", "fonts", f"{icon_name}-solid.png")), size=(25, 25))

    def reveal_or_hide_barrier_img(self):
        has_barrier = self.has_barrier_var.get()
        config_utils.update_config("has_barrier", has_barrier)
        if not has_barrier:
            for image_widgets in self.get_selected_images_widgets_list():
                if image_widgets[0].master.name in ["_Empty.png", "Air.png"]:
                    image_widgets[0].master.destroy()
                    continue
                label = image_widgets[0]
                image = Image.open(Path(constants.IMAGES_PATH, label.cget("text")))
                image.thumbnail((50, 50))
                photo = customtkinter.CTkImage(image, size=image.size)
                label.configure(image=photo)
                label.photo = photo
        else:
            self.insert_image_widget(f"_Empty.png")
            for image_widgets in self.get_selected_images_widgets_list():
                label = image_widgets[0]
                image_path = Path(constants.IMAGES_PATH, label.cget("text"))
                image2_path = Path(constants.IMAGES_BARRIER_PATH, label.cget("text"))
                image = Image.open(image_path)
                if os.path.exists(image2_path):
                    image2 = Image.open(image2_path)
                else:
                    image2 = Image.open(r"assets\x.png")
                image.thumbnail((50, 50))
                image2.thumbnail((50, 50))
                image = merge_pil_images(image, image2)
                photo = customtkinter.CTkImage(image, size=image.size)
                label.configure(image=photo)
                label.photo = photo

    def show_current_board(self):
        self.disable_loop()
        cv2_image = custom_utils.concatenate_cv2_list_as_full_grid(match_icons.make_cell_list())
        image_frame = tk.Toplevel(self.master)
        image_frame.title("Image Frame")
        image = Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_RGB2BGR))
        photo = customtkinter.CTkImage(image, size=image.size)
        label = customtkinter.CTkLabel(image_frame, image=photo)
        label.image = photo
        label.pack()

    def show_current_board_with_matches(self):
        self.disable_loop()
        result = self.execute_board_analysis(create_image=True)
        image_frame = tk.Toplevel(self.master)
        image_frame.title("Image Frame")
        image = Image.fromarray(cv2.cvtColor(result.match_image, cv2.COLOR_RGB2BGR))
        photo = customtkinter.CTkImage(image, size=image.size)
        label = customtkinter.CTkLabel(image_frame, image=photo)
        label.image = photo
        label.pack()

    def load_last_team(self):
        try:
            self.destroy_selected_pokemons()

            current_team, stage_name = shuffle_config_files.get_current_stage_and_team()

            execution_variables.current_stage = stage_name
            execution_variables.current_strategy = constants.GRADING_TOTAL_SCORE
            self.stage_combobox.set(constants.move_stages.get(execution_variables.current_stage))
            self.strategy_combobox.set(constants.move_strategy.get(execution_variables.current_strategy))
            for pokemon in current_team:
                if pokemon.name in load_from_shuffle.exception_list:
                    pokemon.name = f"_{pokemon.name}"
                self.insert_image_widget(pokemon.name, skip_barrier=True)
            if self.has_barrier_var.get():
                self.reveal_or_hide_barrier_img()
        except Exception as ex:
            print(ex)
            pass

    def load_team(self):
        self.disable_loop()
        load_from_shuffle.TeamLoader(root=self)

    def force_update_mouse_buttons(self):
        self.master.update()
        screen_width = self.master.winfo_screenwidth()
        if screen_width == 2560:
            print("Updating to Ultra Wide Positions")
            match_icons.board_top_left = (364, 488)
            match_icons.board_bottom_right = (914, 1031)
        elif screen_width == 1920:
            print("Updating to Full HD Positions")
            # match_icons.board_top_left = (214, 488)
            # match_icons.board_bottom_right = (741, 1010)
            match_icons.board_top_left = (208, 482)
            match_icons.board_bottom_right = (750, 1021)
        else:
            return

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

def merge_pil_images_horizontally(image_list):
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

def merge_pil_images_vertically(image_list):

    widths, heights = zip(*(i.size for i in image_list))

    max_width = max(widths)
    total_height = sum(heights)

    new_im = Image.new('RGB', (max_width, total_height), color=(0, 0, 0))

    y_offset = 0
    for im in image_list:
        new_im.paste(im, (0, y_offset))
        y_offset += im.size[1]

    return new_im
    

def merge_tooltip_pil_images(*args):
    
    horizontal_images_list = []
    
    for image_list in args:
        if len(image_list) > 0:
            horizontal_images_list.append(merge_pil_images_horizontally(image_list))

    final_image = merge_pil_images_vertically(horizontal_images_list)
    
    return final_image

if __name__ == "__main__":    
    root = customtkinter.CTk()
    app = ImageSelectorApp(root)
    root.mainloop()