import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import match_icons
from pathlib import Path
from pynput import mouse

IMAGES_PATH = r"images\icons_final"

class ImageSelectorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Selector")

        # Images panel
        self.images_frame = tk.Frame(master)
        self.images_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_image_list)
        
        self.search_entry = tk.Entry(self.images_frame, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=0, sticky='we', padx=(25, 0))

        self.magnifier_label = tk.Label(self.images_frame, text="🔍", font=("Arial", 12))
        self.magnifier_label.grid(row=1, column=0, sticky="w", padx=(0, 5))


        self.image_listbox = tk.Listbox(self.images_frame, selectmode=tk.SINGLE)
        self.image_listbox.grid(row=2, column=0, padx=(5,0), pady=5)

        self.image_preview_label = tk.Label(self.images_frame)
        self.image_preview_label.grid(row=1, column=1, padx=5, pady=5)

        # self.select_button = tk.Button(self.images_frame, text="Select Image", command=self.select_image)
        # self.select_button.grid(row=2, column=0, columnspan=2, pady=2)

        # Selected images panel with scrollbar
        self.selected_images_frame = tk.Frame(master)
        self.selected_images_frame.pack(side=tk.RIGHT, padx=10, pady=2)

        self.selected_images = []
        self.selected_images_canvas = tk.Canvas(self.selected_images_frame, height=300, width=500)
        self.selected_images_canvas.pack(side=tk.TOP, fill=tk.BOTH)

        self.selected_images_scrollbar = tk.Scrollbar(self.selected_images_frame, orient=tk.HORIZONTAL, command=self.selected_images_canvas.xview)
        self.selected_images_scrollbar.pack(side=tk.TOP, fill=tk.X)
        self.selected_images_canvas.config(xscrollcommand=self.selected_images_scrollbar.set)

        self.selected_images_container = tk.Frame(self.selected_images_canvas)
        self.selected_images_canvas.create_window((0, 0), window=self.selected_images_container, anchor=tk.NW)

        # Load the image list on startup
        self.update_image_list()

        #Controller of Screen Position Buttons
        self.popup = None
        self.click_positions = []
        self.click_counter = 1
        self.positions_button = tk.Button(self.images_frame, text="Configure Positions", command=self.show_popup)
        self.positions_button.grid(row=0, column=0, columnspan=2, pady=2)

        # Execute button
        self.execute_button = tk.Button(self.images_frame, text="Execute with Selected Images", command=self.execute_selected_images)
        self.execute_button.grid(row=3, column=0, columnspan=2, pady=2)

        # Create a Tkinter variable to hold the checkbox state (checked or unchecked)
        self.check_var = tk.BooleanVar()

        # Create a Checkbutton widget
        self.checkbox = tk.Checkbutton(self.images_frame, text="Check me", variable=self.check_var)
        self.checkbox.grid(row=4, column=0, columnspan=2, pady=2)


    def update_image_list(self, *args):
        search_term = self.search_var.get().lower()
        self.image_listbox.delete(0, tk.END)

        folder_path = IMAGES_PATH  # Change this to the path of your folder
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")) and search_term in f.lower()]

        for image_file in image_files:
            self.image_listbox.insert(tk.END, image_file)

        self.image_listbox.bind("<Double-Button-1>", self.select_image)

    def select_image(self, event=None):
        selected_index = self.image_listbox.curselection()
        if selected_index:
            selected_file = self.image_listbox.get(selected_index)
            image_path = os.path.join(IMAGES_PATH, selected_file)  # Change this to the path of your folder

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
            selected_image_label.photo = photo
            selected_image_label.pack()

            options = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'del', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                        'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
            combobox = ttk.Combobox(selected_image_frame, values=options)
            if Path(image_path).stem == "Air":
                combobox.set("del")
            else:
                combobox.set(str(len(self.selected_images)))
            combobox.pack()

            remove_button = tk.Button(selected_image_frame, text="Remove", command=lambda: self.remove_selected_image(selected_image_frame, image_path))
            remove_button.pack()

            # Update the scroll region of the canvas
            self.master.update_idletasks()
            self.selected_images_canvas.config(scrollregion=self.selected_images_canvas.bbox(tk.ALL))

    def remove_selected_image(self, frame, image_path):
        frame.destroy()
        # Remove the image from the selected images list
        self.selected_images = [(path, name) for path, name in self.selected_images if path != image_path]

        # Update the scroll region of the canvas
        self.master.update_idletasks()
        self.selected_images_canvas.config(scrollregion=self.selected_images_canvas.bbox(tk.ALL))

    def execute_selected_images(self):
        # This is a placeholder for your function to execute with selected images

        values_to_execute = []
        for frame in self.selected_images_canvas.winfo_children():
            if isinstance(frame, tk.Frame):
                image_frames = frame.winfo_children()
                for image_frame in image_frames:
                    image_widgets = image_frame.winfo_children()
                    if len(image_widgets) == 3 and isinstance(image_widgets[1], ttk.Combobox):
                        values_to_execute.append((Path(IMAGES_PATH, image_widgets[0].cget("text")), image_widgets[1].get()))

        match_icons.start(values_to_execute, self.check_var.get())
        # print("Executing with selected images:", values_to_execute)

    def show_popup(self):
        print("enter show popup")

        if self.click_counter <= 3:
            self.popup = tk.Toplevel(self.master)
            self.popup.title("Click Recorder")
        
            if self.click_counter == 1:
                label = tk.Label(self.popup, text="Click on the top left corner of the board")
            elif self.click_counter == 2:
                label = tk.Label(self.popup, text="Click on the lower right corner of the board")
            elif self.click_counter == 3:
                label = tk.Label(self.popup, text="Click on the first cell of Shuffle Move")

            label.pack(pady=10)

            self.mouse_listener = mouse.Listener(on_click=self.record_click)
            self.mouse_listener.start()
        else:
            print("erro")

    def record_click(self, x, y, button, pressed):
        if pressed:
            if self.click_counter == 1:
                match_icons.board_top_left = (x ,y)
                print(f"recorded first click at - {match_icons.board_top_left}")
            elif self.click_counter == 2:
                match_icons.board_bottom_right = (x, y)
                print(f"recorded second click at - {match_icons.board_bottom_right}")
            elif self.click_counter == 3:
                match_icons.shuffle_move_first_square_position = (x, y)
                print(f"recorded third click at - {match_icons.shuffle_move_first_square_position}")
            self.click_positions.append((x, y))
            self.popup.destroy()
            self.mouse_listener.stop()
            if self.click_counter < 3:
                self.click_counter += 1
                self.show_popup()
            else:
                self.click_counter = 1

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSelectorApp(root)
    root.mainloop()
