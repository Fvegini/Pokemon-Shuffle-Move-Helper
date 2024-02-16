import tkinter as tk
from tkinter import Button
import cv2
import numpy as np
import pyautogui
from src import match_icons, config_utils, custom_utils

class BoardPositionSelectorApp():

    def __init__(self, master):
        self.master = master
        self.keep_open = False
        self.scale = 0.5

        self.master.update()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Capture the screen
        screenshot = pyautogui.screenshot()

        # Convert the screenshot to an OpenCV image
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Set the desired window size
        window_width, window_height = int(screen_width * self.scale), int(screen_height * self.scale)

        # Resize the frame
        frame = cv2.resize(frame, (window_width, window_height))

        # Create a window and set the callback function for mouse events
        cv2.namedWindow("Select Rectangle")
        cv2.setMouseCallback("Select Rectangle", self.on_mouse, param=frame)

        self.rect_start, self.rect_end, self.drawing = (-1, -1), (-1, -1), False

        self.keep_open = True

        while self.keep_open:
            # Display the current frame
            current_frame = frame.copy()
            if self.drawing:
                cv2.rectangle(current_frame, self.rect_start, self.rect_end, (0, 255, 0), 2)
            cv2.imshow("Select Rectangle", current_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Destroy the OpenCV window
        cv2.destroyAllWindows()

    def on_mouse(self, event, x, y, flags, param):
        frame = param

        if event == cv2.EVENT_LBUTTONDOWN:
            self.rect_start = (x, y)
            self.rect_end = (x, y)
            self.drawing = True

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.rect_end = (x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            self.rect_end = (x, y)
            self.drawing = False
            cv2.rectangle(frame, self.rect_start, self.rect_end, (0, 255, 0), 2)
            cv2.imshow("Select Rectangle", frame)
            
            top_left = tuple([int(point / self.scale) for point in self.rect_start])
            bottom_right = tuple([int(point / self.scale) for point in self.rect_end])
            
            match_icons.board_top_left = top_left
            config_utils.update_config("board_top_left", top_left)
            
            match_icons.board_bottom_right = bottom_right
            config_utils.update_config("board_bottom_right", bottom_right)
            
            print(f"Top-Left Position: {top_left}")
            print(f"Bottom-Right Position: {bottom_right}")
            
            self.keep_open = False
            cv2.destroyAllWindows()