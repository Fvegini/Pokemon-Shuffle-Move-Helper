import os
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter
from PIL import Image, ImageTk
import keyboard
from src import match_icons
from pathlib import Path
from pynput import mouse
from src.board_image_selector import BoardImageSelector, AppImageSelector
from src import constants, custom_utils, load_from_shuffle, config_utils
import pickle
from tkfontawesome import icon_to_image
import warnings
from CTkToolTip import CTkToolTip
# from tktooltip import ToolTip
warnings.filterwarnings("ignore", category=UserWarning, message="CTkButton Warning: Given image is not CTkImage but*")


customtkinter.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


# import cairosvg
last_team_to_execute = None
LAST_TEAM_PKL = "last_team.pkl"

class ImageSelectorApp():
    def __init__(self, master):
        
        self.master = master
        self.master.title("Image Selector")
        # self.create_app_menu()
        
        self.create_tab_menu()
        
        self.appview = customtkinter.CTkFrame(self.master)
        self.appview.pack(expand=1, fill=tk.X, pady=0, padx=0, anchor="nw")

        self.create_left_app_screen()
        self.create_right_app_screen()
        
        self.update_image_list()
        self.configure_initial_geometry()
        self.load_last_team()
        self.update_preview_image()

    def create_tab_menu(self):
        self.tabview = customtkinter.CTkTabview(self.master, height=100)
        # self.tabview.pack(expand=1, fill=tkinter.X, pady=0, padx=0, anchor="n")
        self.tabview.pack(expand=1, fill=tk.X, pady=0, padx=0, anchor="nw")
        
        self.tab1 = self.tabview.add("Configurations")
        self.tab2 = self.tabview.add("Icons")
        self.tab3 = self.tabview.add("Execute")
        # self.tabview.tab("CTkTabview").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        # self.tabview.tab("Tab 2").grid_columnconfigure(0, weight=1)
        self.tabview._segmented_button.grid(sticky="W")
        self.tabview.pack_propagate(False)
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

        
    def create_tab_1(self):
        frame1_1 = customtkinter.CTkFrame(self.tab1, fg_color="transparent")
        frame1_1_top = customtkinter.CTkFrame(frame1_1, fg_color="transparent")
        frame1_1_bottom = customtkinter.CTkFrame(frame1_1, fg_color="transparent")
        
        frame1_1.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame1_1_top.pack(side=tk.TOP)
        frame1_1_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab1, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        customtkinter.CTkLabel(frame1_1_bottom, text="Mouse Positions", font=customtkinter.CTkFont(size=10), bg_color="white").pack(side=tk.BOTTOM, anchor=tk.S)

        icon = icon_to_image("mouse", fill="#ffffff", scale_to_width=25)

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
        btn2_1_1 = customtkinter.CTkButton(frame2_1_top, text="Load Team", command=self.load_team, image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style)
        CTkToolTip(btn2_1_1, delay=0.5, message="Load Team From Shuffle Move Config File")
        btn2_1_1.pack(side=tk.LEFT)
        
        
        #Block 2
        customtkinter.CTkLabel(frame2_2_bottom, text="Register Icons").pack(side=tk.BOTTOM)
        btn2_2_1 = customtkinter.CTkButton(frame2_2_top, text="Register Barrier", command=self.open_barrier_register_screen, image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style)
        CTkToolTip(btn2_2_1, delay=0.5, message="Create or Substitute the Barrier Icon")
        btn2_2_1.pack(side=tk.LEFT)
        btn2_2_2 = customtkinter.CTkButton(frame2_2_top, text="Register Extra", command=self.open_extra_register_screen, image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style)
        CTkToolTip(btn2_2_2, delay=0.5, message="Insert a new Extra Icon")
        btn2_2_2.pack(side=tk.LEFT)   


        # #Block 3
        customtkinter.CTkLabel(frame2_3_bottom, text="Remove Icons").pack(side=tk.BOTTOM)
        btn2_3_1 = customtkinter.CTkButton(frame2_3_top, text="Remove Barrier", command=lambda: self.open_app_register_screeat(action="Remove_Barrier"), image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style)
        CTkToolTip(btn2_3_1, delay=0.5, message="Remove the Barrier Icon")
        btn2_3_1.pack(side=tk.LEFT)
        btn2_3_2 = customtkinter.CTkButton(frame2_3_top, text="Remove Extra", command=lambda: self.open_app_register_screen(action="Remove_Extra"), image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style)
        CTkToolTip(btn2_3_2, delay=0.5, message="Remove One of the Extra Icons")
        btn2_3_2.pack(side=tk.LEFT)   


    def create_tab_3(self):
        frame3_1 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_1_top = customtkinter.CTkFrame(frame3_1)
        frame3_1_bottom = customtkinter.CTkFrame(frame3_1)
        frame3_1.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_1_top.pack(side=tk.TOP)
        frame3_1_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)
        
        
        customtkinter.CTkLabel(frame3_1_bottom, text="Board Capture Mode", bg_color="transparent").pack(side=tk.BOTTOM)
        
        self.board_capture_var = tk.BooleanVar(value=config_utils.config_values.get("board_capture_var")) 
        self.has_barrier = tk.BooleanVar(value=config_utils.config_values.get("has_barrier")) 
        self.control_loop_var = tk.BooleanVar(value=False)

        customtkinter.CTkSwitch(frame3_1_top, text="Print Screen Mode", variable=self.board_capture_var, onvalue=True, offvalue=False, command=self.update_board_capture_mode).pack(side=tk.TOP, anchor=tk.W)
        customtkinter.CTkSwitch(frame3_1_top, text="Capture Loop", variable=self.control_loop_var, onvalue=True, offvalue=False, command=lambda: self.control_loop_function(force_click=True)).pack(side=tk.TOP, anchor=tk.W)
        
        
        customtkinter.CTkSwitch(frame3_1_top, text="Has Barriers", variable=self.has_barrier, command=self.reveal_or_hide_barrier_img).pack(side=tk.TOP, anchor=tk.W)
        
        frame3_2 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_2_top = customtkinter.CTkFrame(frame3_2, fg_color="transparent")
        frame3_2_bottom = customtkinter.CTkFrame(frame3_2, fg_color="transparent")
        frame3_2.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_2_top.pack(side=tk.TOP)
        frame3_2_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        customtkinter.CTkLabel(frame3_2_bottom, text="").pack(side=tk.BOTTOM)
        btn3_2_1 = customtkinter.CTkButton(frame3_2_top, text="Execute", command=lambda: self.start_board_analysis(force_click=True), image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style)
        CTkToolTip(btn3_2_1, delay=0.5, message="Execute (F3)")
        btn3_2_1.pack(side=tk.LEFT)
        keyboard.add_hotkey('f3', lambda: self.start_board_analysis(force_click=True))
        customtkinter.CTkButton(frame3_2_top, text="View Last Board", command=self.show_last_move, image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style).pack(side=tk.LEFT)

        frame3_3 = customtkinter.CTkFrame(self.tab3, fg_color="transparent")
        frame3_3_top = customtkinter.CTkFrame(frame3_3, fg_color="transparent")
        frame3_3_bottom = customtkinter.CTkFrame(frame3_3, fg_color="transparent")
        frame3_3.pack(side=tk.LEFT, expand=False, fill=tk.Y, anchor=tk.W)
        frame3_3_top.pack(side=tk.TOP)
        frame3_3_bottom.pack(side=tk.BOTTOM)
        tk.ttk.Separator(self.tab3, orient='vertical').pack(side=tk.LEFT, fill='y', anchor=tk.W)

        customtkinter.CTkLabel(frame3_3_bottom, text="").pack(side=tk.BOTTOM)
        self.update_search_dir_button = customtkinter.CTkButton(frame3_3_top, text="Update Search Directory", command=self.update_search_dir, image=icon_to_image("mouse", fill="#ffffff", scale_to_width=25), **self.tab_button_style)
        CTkToolTip(self.update_search_dir_button, delay=0.5, message="Execute (F3)")
        self.update_search_dir_button.pack(side=tk.TOP)
        customtkinter.CTkSwitch(frame3_3_top, text="Image File Mode", variable=self.board_capture_var, onvalue=False, offvalue=True, command=self.update_board_capture_mode).pack(side=tk.TOP, anchor=tk.W)



        self.update_board_capture_mode()

    def create_app_menu(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        menu1 = tk.Menu(self.menubar, tearoff=0)
        menu1.add_command(label="Configure Board Top Left", command=lambda: self.show_click_popup(click_counter= 1))
        menu1.add_command(label="Configure Board Bottom Right", command=lambda: self.show_click_popup(click_counter= 2))
        menu1.add_command(label="Configure Shuffle Move First Square", command=lambda: self.show_click_popup(click_counter= 3))
        menu1.add_command(label="Configure Mouse Return Position", command=lambda: self.show_click_popup(click_counter= 4))
        menu1.add_command(label="Load Team from Shufle Move", command=self.load_team)
        menu1.add_command(label="Register Barrier Icon", command=self.open_barrier_register_screen)
        menu1.add_command(label="Remove Barrier Icon", command=lambda: self.open_app_register_screen(action="Remove"))
        menu1.add_command(label="Register Extra Icon", command=self.open_extra_register_screen)
        # menu1.add_command(label="Execute with Selected Images", command=self.execute_selected_images)
        self.menubar.add_cascade(label="Menu 1", menu=menu1)

        menu2 = tk.Menu(self.menubar, tearoff=0)
        self.has_barrier = tk.BooleanVar(value=True)
        # self.keep_loop_check = tk.BooleanVar(value=True)
        self.screen_capture_activated = tk.BooleanVar(value=True)
        menu2.add_checkbutton(label="Has Barrier", variable=self.has_barrier, command=self.reveal_or_hide_barrier_img)
        # menu2.add_checkbutton(label="Activate Auto Get Images", variable=self.keep_loop_check, command=self.check_function)
        menu2.add_checkbutton(label="Activate Screen Capture", variable=self.screen_capture_activated, command=self.update_board_capture_mode)
        self.menubar.add_cascade(label="Menu 2", menu=menu2)

        # self.menubar.add_command(label="Execute", command=self.start_board_analysis)
        self.menubar.add_command(label="Debug", command=self.show_last_move)

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
        
        self.image_preview = customtkinter.CTkLabel(self.images_frame, text="")
        self.image_preview.grid(row=1, column=2, padx=5, pady=5, sticky='w')


    def create_right_app_screen(self):
        self.selected_images_frame_master = tk.Frame(self.appview, background="aqua")
        # self.selected_images_frame.pack(side=tk.LEFT, padx=10, pady=2, expand=1)
        self.selected_images_frame_master.pack(padx=10, pady=2, expand=1, anchor="nw")
        # self.selected_images_frame.rowconfigure((0,1), weight=1)
        
        self.selected_images_frame = tk.Frame(self.selected_images_frame_master, background="aqua")
        # self.selected_images_frame.pack(side=tk.LEFT, padx=10, pady=2, expand=1)
        self.selected_images_frame.pack(padx=10, pady=2, expand=1, anchor="nw")

        self.selected_images = []
        self.selected_images_canvas = tk.Canvas(self.selected_images_frame, background="aquamarine1", width=1200, height=200)
        self.selected_images_canvas.pack(side=tk.TOP, fill=tk.X)

        self.selected_images_scrollbar = tk.Scrollbar(self.selected_images_frame, orient=tk.HORIZONTAL, command=self.selected_images_canvas.xview)
        self.selected_images_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.selected_images_canvas.config(xscrollcommand=self.selected_images_scrollbar.set)

        self.selected_images_container = tk.Frame(self.selected_images_canvas, background="azure")
        self.selected_images_canvas.create_window((0, 0), window=self.selected_images_container, anchor=tk.CENTER, height=200)

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
    
    def insert_image_widget(self, selected_file, forced_shortcut=None, disabled=False):
        image_path = os.path.join(constants.IMAGES_PATH, selected_file)  # Change this to the path of your folder

        if any([value for value in self.selected_images if value[1] == selected_file]):
            return

        # Create a thumbnail for preview
        image = Image.open(image_path)
        image.thumbnail((50, 50))
        photo = ImageTk.PhotoImage(image)

        # Add to the selected images list
        self.selected_images.append((image_path, selected_file))

        # Display in the selected images panel
        selected_image_frame = tk.Frame(self.selected_images_container)
        selected_image_frame.pack(fill=tk.BOTH, side=tk.RIGHT, padx=5, anchor=tk.CENTER)

        selected_image_label = tk.Label(selected_image_frame, image=photo, text=selected_file, compound=tk.TOP)
        selected_image_label.photo = photo # Keep a reference to avoid garbage collection issues
        selected_image_label.pack()

        options = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'del', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        combobox = customtkinter.CTkComboBox(selected_image_frame, values=options, width=80)
        if forced_shortcut:
            combobox.set(forced_shortcut)
        elif Path(image_path).stem == "_Empty":
            combobox.set("del")
        else:
            combobox.set(str(len(self.selected_images)))
        combobox.pack()

        # remove_button = tk.Button(selected_image_frame, text="Remove", command=lambda: self.remove_selected_image(selected_image_frame, image_path))
        disable_button = customtkinter.CTkButton(selected_image_frame, text="Remove", width=80, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=lambda: self.remove_selected_image(selected_image_frame, image_path))
        disable_button.pack()

        checkbox_1 = customtkinter.CTkCheckBox(selected_image_frame, text="Disable", checkbox_width=12, checkbox_height=12, corner_radius=0, onvalue=True, offvalue=False)
        checkbox_1.pack(padx=(25, 0))
        if disabled:
            checkbox_1.select()


        # disable_button = customtkinter.CTkButton(selected_image_frame, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"))
        # disable_button.pack()

        # selected_image_frame2 = tk.Frame(self.selected_images_container2, width=selected_image_frame.winfo_width())
        # selected_image_frame2.pack(side=tk.RIGHT, padx=5, expand=1, fill=tk.BOTH)

        # selected_image_label2 = tk.Label(selected_image_frame2, image=photo, compound=tk.TOP)
        # # selected_image_label2.photo = photo
        # selected_image_label2.pack(expand=1, fill=tk.BOTH)

        
        if self.has_barrier.get():
            self.reveal_or_hide_barrier_img()

        # Update the scroll region of the canvas
        self.master.update_idletasks()
        self.selected_images_canvas.config(scrollregion=self.selected_images_canvas.bbox(tk.ALL))

    def destroy_selected_pokemons(self):
        for widget in self.selected_images_container.winfo_children():
            widget.destroy()
        self.selected_images = []
        
    def remove_selected_image(self, frame, image_path):
        frame.destroy()
        # Remove the image from the selected images list
        self.selected_images = [(path, name) for path, name in self.selected_images if path != image_path]

        # Update the scroll region of the canvas
        self.master.update_idletasks()
        self.selected_images_canvas.config(scrollregion=self.selected_images_canvas.bbox(tk.ALL))

    def open_barrier_register_screen(self):
        self.board_image_selector = BoardImageSelector(root=self, folder="barrier")

    def open_extra_register_screen(self):
        self.board_image_selector = BoardImageSelector(root=self, folder="extra")
    
    def open_app_register_screen(self, action=None):
        self.app_image_selector = AppImageSelector(root=self, action=action)

    def get_selected_images_widgets_list(self):
        widget_list = []
        for frame in self.selected_images_canvas.winfo_children():
            if isinstance(frame, tk.Frame):
                image_frames = frame.winfo_children()
                for image_frame in image_frames:
                    image_widgets = image_frame.winfo_children()
                    widget_list.append(image_widgets)
        return widget_list

    def start_board_analysis(self, force_click=False):
        global last_team_to_execute
        values_to_execute = []
        for image_widgets in self.get_selected_images_widgets_list():
            values_to_execute.append((Path(constants.IMAGES_PATH, image_widgets[0].cget("text")), image_widgets[1].get(), image_widgets[3].get()))
        if last_team_to_execute != values_to_execute:
            last_team_to_execute = values_to_execute
            with open(LAST_TEAM_PKL, 'wb') as file:
                pickle.dump(values_to_execute, file)
        
        if force_click:
            force_click = True
        else:
            force_click = self.control_loop_var.get()
        
        match_icons.start(values_to_execute, self.has_barrier.get(), screen_record=self.board_capture_var.get(), force_click=force_click)
        # print("Executing with selected images:", values_to_execute)

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

    def control_loop_function(self, force_click=False):
        if not self.control_loop_var.get():
            return
        else:
            if not self.board_capture_var.get():
                if config_utils.config_values.get("board_image_path") and os.path.exists(config_utils.config_values.get("board_image_path")):
                    self.start_board_analysis(force_click)
            else:
                self.start_board_analysis(force_click)
            self.check_job = self.master.after(1000, self.control_loop_function)  # Schedule next check after 2000 milliseconds (2 seconds)

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



    def reveal_or_hide_barrier_img(self):
        has_barrier = self.has_barrier.get()
        config_utils.update_config("has_barrier", has_barrier)
        if not has_barrier:
            
            for image_widgets in self.get_selected_images_widgets_list():
                label = image_widgets[0]
                image = Image.open(Path(constants.IMAGES_PATH, label.cget("text")))
                image.thumbnail((50, 50))
                photo = ImageTk.PhotoImage(image)
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
                    # image2 = custom_utils.open_and_resize_np_image(image_path, match_icons.downscale_res)
                    # image2 = Image.fromarray(match_icons.add_barrier_layer(image2))
                    image2 = Image.open(r"assets\x.png")
                image.thumbnail((50, 50))
                image2.thumbnail((50, 50))
                image = custom_utils.merge_pil_images(image, image2)
                photo = ImageTk.PhotoImage(image)
                label.configure(image=photo)
                label.photo = photo

    def show_last_move(self):
        image_frame = tk.Toplevel(self.master)
        image_frame.title("Image Frame")
        photo = ImageTk.PhotoImage(Image.fromarray(match_icons.last_image))
        label = ttk.Label(image_frame, image=photo)
        label.image = photo
        label.pack()

    def load_last_team(self):
        try:
            self.destroy_selected_pokemons()
            with open(LAST_TEAM_PKL, 'rb') as file:
                loaded_variable = pickle.load(file)
            for pokemon, shortcut, disabled in loaded_variable:
                self.insert_image_widget(pokemon.name, shortcut, disabled)
            self.selected_images_scrollbar.set(0.0)
        except:
            pass
        

    def load_team(self):
        load_from_shuffle.TeamLoader(root=self)
        # self.app_image_selector = AppImageSelector(root=self, action=action)
        

if __name__ == "__main__":    
    root = customtkinter.CTk()
    app = ImageSelectorApp(root)
    root.mainloop()