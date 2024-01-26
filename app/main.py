import os
import tkinter as tk
from tkinter import filedialog
import customtkinter
from PIL import Image
import keyboard
from src import match_icons
from pathlib import Path
from pynput import mouse
from src.board_image_selector import BoardIconSelector, AppIconSelector
from src import constants, custom_utils, load_from_shuffle, config_utils
import pickle
import warnings
from CTkToolTip import CTkToolTip
warnings.filterwarnings("ignore", category=UserWarning, message="CTkButton Warning: Given image is not CTkImage but*")


customtkinter.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
# customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


# import cairosvg
last_team_to_execute = None
LAST_TEAM_PKL = "last_team.pkl"

class ImageSelectorApp():
    def __init__(self, master):
        
        self.master = master
        self.master.title("Image Selector")
        self.create_tab_menu()
        
        self.appview = customtkinter.CTkFrame(self.master)
        self.appview.pack(expand=1, fill=tk.X, pady=0, padx=0, anchor="nw")

        self.create_left_app_screen()
        self.create_right_app_screen()
        
        self.update_image_list()
        self.load_last_team()
        self.update_preview_image()
        self.configure_initial_geometry()

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
        tk.ttk.Separator(self.tab1, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        customtkinter.CTkLabel(frame1_1_bottom, text="Mouse Positions").pack(side=tk.BOTTOM, anchor=tk.S)

        icon = self.get_icon("mouse")

        btn1_1 = customtkinter.CTkButton(frame1_1_top, text="Top Left", command=lambda: self.show_click_popup(click_counter= 1), image=icon, **self.tab_button_style)
        btn1_2 = customtkinter.CTkButton(frame1_1_top, text="Bottom Right", command=lambda: self.show_click_popup(click_counter= 2), image=icon, **self.tab_button_style)
        btn1_3 = customtkinter.CTkButton(frame1_1_top, text="First Square", command=lambda: self.show_click_popup(click_counter= 3), image=icon, **self.tab_button_style)
        btn1_4 = customtkinter.CTkButton(frame1_1_top, text="Return Position", command=lambda: self.show_click_popup(click_counter= 4), image=icon, **self.tab_button_style)

        CTkToolTip(btn1_1, delay=0.5, message="Configure Board Top Left")
        CTkToolTip(btn1_2, delay=0.5, message="Configure Board Bottom Right")
        CTkToolTip(btn1_3, delay=0.5, message="Configure Shuffle Move First Square")
        CTkToolTip(btn1_4, delay=0.5, message="Configure Mouse Return Position")

        btn1_1.pack(side=tk.LEFT)
        btn1_2.pack(side=tk.LEFT)
        btn1_3.pack(side=tk.LEFT)
        btn1_4.pack(side=tk.LEFT)       

    def create_tab_2(self):
        frame2_1 = customtkinter.CTkFrame(self.tab2, fg_color="transparent")
        frame2_1_top = customtkinter.CTkFrame(frame2_1, fg_color="transparent")
        frame2_1_bottom = customtkinter.CTkFrame(frame2_1, fg_color="transparent")
        frame2_1.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame2_1_top.pack(side=tk.TOP)
        frame2_1_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab2, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        frame2_2 = customtkinter.CTkFrame(self.tab2, fg_color="transparent")
        frame2_2_top = customtkinter.CTkFrame(frame2_2, fg_color="transparent")
        frame2_2_bottom = customtkinter.CTkFrame(frame2_2, fg_color="transparent")
        frame2_2.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame2_2_top.pack(side=tk.TOP)
        frame2_2_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab2, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)


        frame2_3 = customtkinter.CTkFrame(self.tab2, fg_color="transparent")
        frame2_3_top = customtkinter.CTkFrame(frame2_3, fg_color="transparent")
        frame2_3_bottom = customtkinter.CTkFrame(frame2_3, fg_color="transparent")
        frame2_3.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame2_3_top.pack(side=tk.TOP)
        frame2_3_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab2, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)        


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
        tk.ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        customtkinter.CTkLabel(frame3_1_bottom, text="Board Capture Mode", bg_color="transparent").pack(side=tk.BOTTOM)
        
        
        frame3_1_top_1 = customtkinter.CTkFrame(frame3_1_top, fg_color="transparent")
        frame3_1_top_2 = customtkinter.CTkFrame(frame3_1_top, fg_color="transparent")
        frame3_1_top_1.pack(side=tk.LEFT)
        frame3_1_top_2.pack(side=tk.LEFT)
        
        self.board_capture_var = tk.BooleanVar(value=config_utils.config_values.get("board_capture_var")) 
        self.has_barrier_var = tk.BooleanVar(value=config_utils.config_values.get("has_barrier")) 
        self.control_loop_var = tk.BooleanVar(value=False)

        customtkinter.CTkSwitch(frame3_1_top_1, text="Print Screen Mode", variable=self.board_capture_var, onvalue=True, offvalue=False, command=self.update_board_capture_mode).pack(side=tk.TOP, anchor=tk.W, padx=5)
        customtkinter.CTkSwitch(frame3_1_top_1, text="Image File Mode", variable=self.board_capture_var, onvalue=False, offvalue=True, command=self.update_board_capture_mode).pack(side=tk.TOP, anchor=tk.W, padx=5)
       
        self.control_loop_switch = customtkinter.CTkSwitch(frame3_1_top_2, text="Capture Loop", variable=self.control_loop_var, onvalue=True, offvalue=False, command=lambda: self.control_loop_function())
        self.has_barrier_switch = customtkinter.CTkSwitch(frame3_1_top_2, text="Has Barriers", variable=self.has_barrier_var, command=self.reveal_or_hide_barrier_img)
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
        tk.ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        customtkinter.CTkLabel(frame3_2_bottom, text="").pack(side=tk.BOTTOM)

        btn3_2_1 = customtkinter.CTkButton(frame3_2_top, text="Execute", command=lambda: self.start_board_analysis(source="button"), image=self.get_icon("play-circle"), **self.tab_button_style)
        CTkToolTip(btn3_2_1, delay=0.5, message="Execute (F3)")
        btn3_2_1.pack(side=tk.LEFT)
        keyboard.add_hotkey('f2', lambda: self.start_board_analysis(source="shortcut"))
        
        btn2_1_1 = customtkinter.CTkButton(frame3_2_top, text="Load Team", command=self.load_team, image=self.get_icon("cloud-download-alt"), **self.tab_button_style)
        CTkToolTip(btn2_1_1, delay=0.5, message="Load Team From Shuffle Move Config File")
        btn2_1_1.pack(side=tk.LEFT, padx=5)
        customtkinter.CTkButton(frame3_2_top, text="View Last Board", command=self.show_last_move, image=self.get_icon("search"), **self.tab_button_style).pack(side=tk.LEFT)

        frame3_3 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_3_top = customtkinter.CTkFrame(frame3_3, fg_color="transparent")
        frame3_3_bottom = customtkinter.CTkFrame(frame3_3, fg_color="transparent")
        frame3_3.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_3_top.pack(side=tk.TOP)
        frame3_3_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        customtkinter.CTkLabel(frame3_3_bottom, text="").pack(side=tk.BOTTOM)
        self.update_search_dir_button = customtkinter.CTkButton(frame3_3_top, text="Update Search Directory", command=self.update_search_dir, image=self.get_icon("folder-open"), **self.tab_button_style)
        CTkToolTip(self.update_search_dir_button, delay=0.5, message="Execute (F3)")
        self.update_search_dir_button.pack(side=tk.TOP)

        self.update_board_capture_mode()

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


    def create_right_app_screen(self):
        self.selected_images = []
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

    def update_image_list(self, *args):
        search_term = self.search_var.get().lower()
        search_term = search_term.replace(" ", "_")
        self.image_listbox.delete(0, tk.END)

        folder_path = constants.IMAGES_PATH  # Change this to the path of your folder
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")) and search_term in f.lower()]
        image_files = sorted(image_files, key=lambda word: (word[0] != '_', word))

        for image_file in image_files:
            self.image_listbox.insert(tk.END, image_file)

        self.image_listbox.bind("<<ListboxSelect>>", self.update_preview_image)
        self.image_listbox.bind("<Double-Button-1>", self.select_image)

    def select_image(self, event=None):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_file = self.image_listbox.get(selected_index)
            self.insert_image_widget(selected_file)
    
    def insert_image_widget(self, selected_file, forced_shortcut=None, disabled=False, skip_barrier=False):
        image_path = os.path.join(constants.IMAGES_PATH, selected_file)  # Change this to the path of your folder

        if any([value for value in self.selected_images if value[1] == selected_file]):
            return

        # Display in the selected images panel
        selected_image_frame = customtkinter.CTkFrame(self.scrollable_frame)
        selected_image_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=5, anchor=tk.CENTER)
        selected_image_frame.original_fg_color = selected_image_frame._fg_color
        
        self.selected_images.append((image_path, selected_file))
        
        # Create a thumbnail for preview
        image = Image.open(image_path)
        image.thumbnail((50,50))
        photo = customtkinter.CTkImage(image, size=(50, 50))

        selected_image_label = customtkinter.CTkLabel(selected_image_frame, image=photo, text=selected_file, compound=tk.TOP)
        selected_image_label.pack()
        

        self.insert_extra_images_tooltip(image_path, selected_image_label)
        
        options = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'del', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        combobox = customtkinter.CTkComboBox(selected_image_frame, values=options, width=80)
        if forced_shortcut:
            combobox.set(forced_shortcut)
        elif Path(image_path).stem == "_Empty":
            combobox.set("del")
        else:
            combobox.set(str(len(self.selected_images)))
        combobox.pack(pady=5)

        disable_button = customtkinter.CTkButton(selected_image_frame, text="Remove", width=80, command=lambda: self.remove_selected_image(selected_image_frame, image_path))
        disable_button.pack(pady=5)

        checkbox_1 = customtkinter.CTkCheckBox(selected_image_frame, text="Disable", checkbox_width=12, checkbox_height=12, corner_radius=0, onvalue=True, offvalue=False, command=lambda: self.transparency_set(checkbox_1, selected_image_frame))
        checkbox_1.pack(padx=(25, 0))
        if disabled:
            checkbox_1.toggle()

        if self.has_barrier_var.get() and not skip_barrier:
            self.reveal_or_hide_barrier_img()

    def transparency_set(self, checkbox_1, selected_image_frame):
        if checkbox_1.get():
            selected_image_frame.configure(fg_color="gray")
        else:
            selected_image_frame.configure(fg_color=selected_image_frame.original_fg_color)

    def insert_extra_images_tooltip(self, image_path, selected_image_label):
        extra_image_list = []
        original_path = Path(image_path)
        images_path = [original_path] + custom_utils.find_matching_files(constants.IMAGES_EXTRA_PATH, original_path.stem, ".*") + custom_utils.find_matching_files(constants.IMAGES_BARRIER_PATH, original_path.stem, ".*")


        for extra_image_path in images_path:
            extra_image = Image.open(extra_image_path)
            extra_image.thumbnail((50,50))
            extra_image_list.append(extra_image)
        
        extra_complete_image = custom_utils.merge_pil_images_list(extra_image_list)
        extra_photo = customtkinter.CTkImage(extra_complete_image, size=extra_complete_image.size)
        CTkToolTip(selected_image_label, delay=0.5, message="", image=extra_photo)

    def destroy_selected_pokemons(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_images = []
        
    def remove_selected_image(self, frame, image_path):
        frame.destroy()
        # Remove the image from the selected images list
        self.selected_images = [(path, name) for path, name in self.selected_images if path != image_path]

    def open_create_register_screen(self, folder):
        self.board_image_selector = BoardIconSelector(root=self, folder=folder)
    
    def open_remove_register_screen(self, action=None):
        self.app_image_selector = AppIconSelector(root=self, action=action)

    def open_app_register_screen(self, action=None):
        self.app_image_selector = AppIconSelector(root=self, action=action)


    def get_selected_images_widgets_list(self):
        widget_list = []
        for frame in self.scrollable_frame.winfo_children():
            if isinstance(frame, customtkinter.CTkFrame):
                image_widgets = frame.winfo_children()
                widget_list.append(image_widgets)
        return widget_list

    def start_board_analysis(self, source=None):
        global last_team_to_execute
        values_to_execute = []
        for image_widgets in self.get_selected_images_widgets_list():
            values_to_execute.append((Path(constants.IMAGES_PATH, image_widgets[0].cget("text")), image_widgets[1].get(), image_widgets[3].get()))
        if last_team_to_execute != values_to_execute:
            last_team_to_execute = values_to_execute
            with open(LAST_TEAM_PKL, 'wb') as file:
                pickle.dump(values_to_execute, file)
        return match_icons.start(values_to_execute, self.has_barrier_var.get(), source=source)

    def show_click_popup(self, click_counter):
        self.popup = tk.Toplevel(self.master)
        self.popup.title("Click Recorder")
        self.click_counter = click_counter
        if self.click_counter == 1:
            label = tk.Label(self.popup, text="Click on the top left corner of the board")
        elif self.click_counter == 2:
            label = tk.Label(self.popup, text="Click on the lower right corner of the board")
        elif self.click_counter == 3:
            label = tk.Label(self.popup, text="Click on the first cell of Shuffle Move")
        elif self.click_counter == 4:
            label = tk.Label(self.popup, text="Click on the Execute button from the Shuffle Helper")
        label.pack(pady=10)
        self.mouse_listener = mouse.Listener(on_click=self.record_click)
        self.mouse_listener.start()

    def record_click(self, x, y, button, pressed):
        if pressed:
            if self.click_counter == 1:
                match_icons.board_top_left = (x ,y)
                config_utils.update_config("board_top_left", (x ,y))
                print(f"recorded click at - {match_icons.board_top_left}")
            elif self.click_counter == 2:
                match_icons.board_bottom_right = (x, y)
                config_utils.update_config("board_bottom_right", (x ,y))
                print(f"recorded click at - {match_icons.board_bottom_right}")
            elif self.click_counter == 3:
                match_icons.shuffle_move_first_square_position = (x, y)
                config_utils.update_config("shuffle_move_first_square_position", (x ,y))
                print(f"recorded click at - {match_icons.shuffle_move_first_square_position}")
            elif self.click_counter == 4:
                match_icons.mouse_after_shuffle_position = (x, y)
                config_utils.update_config("mouse_after_shuffle_position", (x ,y))
                print(f"recorded click at - {match_icons.mouse_after_shuffle_position}")
            self.mouse_listener.stop()
            self.popup.destroy()

    def control_loop_function(self):
        extra_delay = 0
        if not self.control_loop_var.get():
            return
        else:
            if not self.board_capture_var.get():
                if config_utils.config_values.get("board_image_path") and os.path.exists(config_utils.config_values.get("board_image_path")):
                    extra_delay = self.start_board_analysis(source="loop")
            else:
                extra_delay = self.start_board_analysis(source="loop")
            self.check_job = self.master.after(200 + extra_delay, self.control_loop_function)  # Schedule next check after 2000 milliseconds (2 seconds)

    def update_search_dir(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            config_utils.update_config("board_image_path", file_path)
            return

    def update_board_capture_mode(self):
        value = self.board_capture_var.get()
        self.control_loop_var.set(False)
        config_utils.update_config("board_capture_var", self.board_capture_var.get())
        if not value:
            self.update_search_dir_button.configure(state=tk.NORMAL)  # Enable the button
        else:
            self.update_search_dir_button.configure(state=tk.DISABLED)  # Disable the button

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
                image = custom_utils.merge_pil_images(image, image2)
                photo = customtkinter.CTkImage(image, size=image.size)
                label.configure(image=photo)
                label.photo = photo

    def show_last_move(self):
        image_frame = tk.Toplevel(self.master)
        image_frame.title("Image Frame")
        image = Image.fromarray(match_icons.last_image)
        photo = customtkinter.CTkImage(image, size=image.size)
        label = customtkinter.CTkLabel(image_frame, image=photo)
        label.image = photo
        label.pack()

    def load_last_team(self):
        try:
            self.destroy_selected_pokemons()
            with open(LAST_TEAM_PKL, 'rb') as file:
                loaded_variable = pickle.load(file)
            for pokemon, shortcut, disabled in loaded_variable:
                self.insert_image_widget(pokemon.name, shortcut, disabled, skip_barrier=True)
            if self.has_barrier_var.get():
                self.reveal_or_hide_barrier_img()
        except Exception as ex:
            print(ex)
            pass

    def load_team(self):
        load_from_shuffle.TeamLoader(root=self)

    def force_update_mouse_buttons(self):
        self.master.update()
        screen_width = self.master.winfo_screenwidth()
        if screen_width == 2560:
            print("Updating to Ultra Wide Positions")
            match_icons.board_top_left = (364, 488)
            match_icons.board_bottom_right = (914, 1031)
            match_icons.shuffle_move_first_square_position = (1496, 96)
            match_icons.mouse_after_shuffle_position = (2039, 443)
        elif screen_width == 1920:
            print("Updating to Full HD Positions")
            match_icons.board_top_left = (214, 488)
            match_icons.board_bottom_right = (741, 1010)
            match_icons.shuffle_move_first_square_position = (1045, 133)
            match_icons.mouse_after_shuffle_position = (1607, 487)
        else:
            return

if __name__ == "__main__":    
    root = customtkinter.CTk()
    app = ImageSelectorApp(root)
    root.mainloop()