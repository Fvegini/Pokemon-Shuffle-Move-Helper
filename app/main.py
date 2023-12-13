import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from src import match_icons
from pathlib import Path
from pynput import mouse
from src.board_image_selector import BoardImageSelector, AppImageSelector
from src import constants, custom_utils, load_from_shuffle
import pickle

last_team_to_execute = None
LAST_TEAM_PKL = "last_team.pkl"

class ImageSelectorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Selector")
        self.create_app_menu()
        self.create_left_app_screen()
        self.create_right_app_screen()
        
        self.update_image_list()
        self.configure_initial_geometry()
        self.load_last_team()

    def create_app_menu(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        menu1 = tk.Menu(self.menubar, tearoff=0)
        menu1.add_command(label="Configure Positions", command=self.show_popup)
        menu1.add_command(label="Load Team from Shufle Move", command=self.load_team)
        menu1.add_command(label="Register Barrier Icon", command=self.open_barrier_register_screen)
        menu1.add_command(label="Remove Barrier Icon", command=lambda: self.open_app_register_screen(action="Remove"))
        menu1.add_command(label="Register Extra Icon", command=self.open_extra_register_screen)
        # menu1.add_command(label="Execute with Selected Images", command=self.execute_selected_images)
        self.menubar.add_cascade(label="Menu 1", menu=menu1)

        menu2 = tk.Menu(self.menubar, tearoff=0)
        self.has_barrier_check = tk.BooleanVar()
        self.keep_loop_check = tk.BooleanVar()
        self.screen_capture_activated = tk.BooleanVar()
        menu2.add_checkbutton(label="Has Barrier", variable=self.has_barrier_check, command=self.reveal_or_hide_barrier_img)
        menu2.add_checkbutton(label="Activate Auto Get Images", variable=self.keep_loop_check, command=self.check_function)
        menu2.add_checkbutton(label="Activate Screen Capture", variable=self.screen_capture_activated, command=self.screen_capture_mode)
        self.menubar.add_cascade(label="Menu 2", menu=menu2)

        self.menubar.add_command(label="Execute", command=self.execute_selected_images)
        self.menubar.add_command(label="Debug", command=self.show_last_move)
        

    def create_left_app_screen(self):
        self.images_frame = tk.Frame(self.master, background="lightblue")
        self.images_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_image_list)
        
        self.search_entry = tk.Entry(self.images_frame, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=0, sticky='we', padx=(25, 0))

        self.magnifier_label = tk.Label(self.images_frame, text="🔍", font=("Arial", 12))
        self.magnifier_label.grid(row=1, column=0, sticky="w", padx=(0, 5))


        self.image_listbox = tk.Listbox(self.images_frame, selectmode=tk.SINGLE)
        self.image_listbox.grid(row=2, column=0, padx=(5,0), pady=5)

        self.image_preview = tk.Label(self.images_frame)
        self.image_preview.grid(row=2, column=1, padx=5, pady=5)

    def create_right_app_screen(self):
        self.selected_images_frame = tk.Frame(self.master, background="aqua")
        self.selected_images_frame.pack(side=tk.LEFT, padx=10, pady=2, expand=1)
        self.selected_images_frame.rowconfigure((0,1), weight=1)
        

        self.selected_images = []
        self.selected_images_canvas = tk.Canvas(self.selected_images_frame, background="aquamarine1", width=1200, height=150)
        self.selected_images_canvas.pack(side=tk.TOP, fill=tk.BOTH)

        self.selected_images_scrollbar = tk.Scrollbar(self.selected_images_frame, orient=tk.HORIZONTAL, command=self.selected_images_canvas.xview)
        self.selected_images_scrollbar.pack(side=tk.TOP, fill=tk.X)
        self.selected_images_canvas.config(xscrollcommand=self.selected_images_scrollbar.set)

        self.selected_images_container = tk.Frame(self.selected_images_canvas, background="azure")
        self.selected_images_canvas.create_window((0, 0), window=self.selected_images_container, anchor=tk.NW, height=150)

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

    def preview_image(self, event):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_file = self.image_listbox.get(selected_index)
            image_path = os.path.join(constants.IMAGES_PATH, selected_file) 
            image = Image.open(image_path)
            image.thumbnail((50, 50))
            photo = ImageTk.PhotoImage(image)

            self.image_preview.config(image=photo)
            self.image_preview.image = photo

    def update_image_list(self, *args):
        search_term = self.search_var.get().lower()
        search_term = search_term.replace(" ", "_")
        self.image_listbox.delete(0, tk.END)

        folder_path = constants.IMAGES_PATH  # Change this to the path of your folder
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")) and search_term in f.lower()]
        image_files = sorted(image_files, key=lambda word: (word[0] != '_', word))

        for image_file in image_files:
            self.image_listbox.insert(tk.END, image_file)

        self.image_listbox.bind("<<ListboxSelect>>", self.preview_image)
        self.image_listbox.bind("<Double-Button-1>", self.select_image)

    def select_image(self, event=None):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_file = self.image_listbox.get(selected_index)
            self.insert_image_widget(selected_file)
    
    def insert_image_widget(self, selected_file, forced_shortcut=None):
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
        selected_image_frame.pack(fill=tk.BOTH, side=tk.RIGHT, padx=5)

        selected_image_label = tk.Label(selected_image_frame, image=photo, text=selected_file, compound=tk.TOP)
        selected_image_label.photo = photo # Keep a reference to avoid garbage collection issues
        selected_image_label.pack()

        options = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'del', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        combobox = ttk.Combobox(selected_image_frame, values=options)
        if forced_shortcut:
            combobox.set(forced_shortcut)
        elif Path(image_path).stem == "_Empty":
            combobox.set("del")
        else:
            combobox.set(str(len(self.selected_images)))
        combobox.pack()

        remove_button = tk.Button(selected_image_frame, text="Remove", command=lambda: self.remove_selected_image(selected_image_frame, image_path))
        remove_button.pack()


        # selected_image_frame2 = tk.Frame(self.selected_images_container2, width=selected_image_frame.winfo_width())
        # selected_image_frame2.pack(side=tk.RIGHT, padx=5, expand=1, fill=tk.BOTH)

        # selected_image_label2 = tk.Label(selected_image_frame2, image=photo, compound=tk.TOP)
        # # selected_image_label2.photo = photo
        # selected_image_label2.pack(expand=1, fill=tk.BOTH)

        
        if self.has_barrier_check.get():
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
                    if len(image_widgets) == 3 and isinstance(image_widgets[1], ttk.Combobox):
                        widget_list.append(image_widgets)
        return widget_list

    def execute_selected_images(self):
        global last_team_to_execute
        values_to_execute = []
        for image_widgets in self.get_selected_images_widgets_list():
            values_to_execute.append((Path(constants.IMAGES_PATH, image_widgets[0].cget("text")), image_widgets[1].get()))
        if last_team_to_execute != values_to_execute:
            last_team_to_execute = values_to_execute
            with open(LAST_TEAM_PKL, 'wb') as file:
                pickle.dump(values_to_execute, file)
        
        match_icons.start(values_to_execute, self.has_barrier_check.get(), screen_record=self.screen_capture_activated.get())
        # print("Executing with selected images:", values_to_execute)

    def show_popup(self):
        self.popup = tk.Toplevel(self.master)
        self.popup.title("Click Recorder")
        label = tk.Label(self.popup, text="Click on the first cell of Shuffle Move")
        label.pack(pady=10)
        self.mouse_listener = mouse.Listener(on_click=self.record_click)
        self.mouse_listener.start()

    def record_click(self, x, y, button, pressed):
        if pressed:
            match_icons.shuffle_move_first_square_position = (x, y)
            self.mouse_listener.stop()
            self.popup.destroy()

    def check_function(self):
        if not self.keep_loop_check.get():
            return
        else:
            if os.path.exists(constants.DROPBOX_IMAGE_PATH):
                self.execute_selected_images()
            self.check_job = self.master.after(1000, self.check_function)  # Schedule next check after 2000 milliseconds (2 seconds)

    def screen_capture_mode(self):
        return

    def reveal_or_hide_barrier_img(self):
        if not self.has_barrier_check.get():
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
            for pokemon, shortcut in loaded_variable:
                self.insert_image_widget(pokemon.name, shortcut)
        except:
            pass
        

    def load_team(self):
        load_from_shuffle.TeamLoader(root=self)
        # self.app_image_selector = AppImageSelector(root=self, action=action)
        

if __name__ == "__main__":    
    root = tk.Tk()    
    app = ImageSelectorApp(root)
    root.mainloop()