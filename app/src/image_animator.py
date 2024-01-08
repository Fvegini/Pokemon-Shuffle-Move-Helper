from PIL import Image, ImageDraw, ImageSequence
import tkinter as tk
from tkinter import ttk
import customtkinter

class ImageAnimator:
    def __init__(self, master, image_list):
        self.master = master
        self.image_list = image_list
        self.current_frame = 0

        self.label = ttk.Label(self.master)
        self.label.pack()

        self.load_images()
        self.animate_images()

    def load_images(self):
        self.frames = [customtkinter.CTkImage(img) for img in self.image_list]

    def animate_images(self):
        self.label.config(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.master.after(500, self.animate_images)  # Adjust the delay as needed