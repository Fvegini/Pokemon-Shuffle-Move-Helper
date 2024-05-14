import tkinter as tk
from tkinter import Button
import cv2
import numpy as np
import pyautogui
from src import match_icons, config_utils, custom_utils, constants, screen_utils
from src.adb_utils import get_label_with_tuple
from pathlib import Path
from src import log_utils

log = log_utils.get_logger()

class BoardPositionSelectorApp():

    def __init__(self, master, selector_app=None):
        self.master = master
        self.keep_open = False
        self.scale = 0.9
        self.selector_app = selector_app
        self.master.update()
        limit_width = int(self.master.winfo_screenwidth() * 0.9)
        limit_height = int(self.master.winfo_screenheight() * 0.9)

        # Capture the screen
        original_frame = custom_utils.capture_screen_screenshot()

        frame = custom_utils.resize_image_to_fit(original_frame, limit_width, limit_height)
        
        self.scale = frame.shape[0] / original_frame.shape[0]

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
                self.keep_open = False
                break
            elif cv2.getWindowProperty('Select Rectangle', cv2.WND_PROP_VISIBLE) < 1:
                self.keep_open = False
                break

        cv2.destroyAllWindows()
        self.master.after(500, self.selector_app.show_current_board)

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
            
            config_utils.update_config("board_top_left", top_left)
            config_utils.update_config("board_bottom_right", bottom_right)
            # screen_utils.update_screen()
            
            log.debug(f"Top-Left Position: {top_left}")
            log.debug(f"Bottom-Right Position: {bottom_right}")
            
            self.keep_open = False
            cv2.destroyAllWindows()

class IconCaptureApp():

    def __init__(self, master, selector_app=None, filename=None):
        self.master = master
        self.keep_open = False
        self.scale = 0.9
        self.selector_app = selector_app
        self.master.update()
        self.filename = filename
        limit_width = int(self.master.winfo_screenwidth() * 0.9)
        limit_height = int(self.master.winfo_screenheight() * 0.9)

        # Capture the screen
        self.original_frame = custom_utils.capture_screen_screenshot()

        # Convert the screenshot to an OpenCV image

        frame = custom_utils.resize_image_to_fit(self.original_frame, limit_width, limit_height)
        
        self.scale = frame.shape[0] / self.original_frame.shape[0]

        # Create a window and set the callback function for mouse events
        cv2.namedWindow("Select New Stage")
        cv2.setMouseCallback("Select New Stage", self.on_mouse, param=frame)

        self.rect_start, self.rect_end, self.drawing = (-1, -1), (-1, -1), False

        self.keep_open = True

        while self.keep_open:
            # Display the current frame
            current_frame = frame.copy()
            if self.drawing:
                cv2.rectangle(current_frame, self.rect_start, self.rect_end, (0, 255, 0), 2)
            cv2.imshow("Select New Stage", current_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.keep_open = False
                break
            elif cv2.getWindowProperty('Select New Stage', cv2.WND_PROP_VISIBLE) < 1:
                self.keep_open = False
                break

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
            
            top_left = tuple([int(point / self.scale) for point in self.rect_start])
            bottom_right = tuple([int(point / self.scale) for point in self.rect_end])
           
            log.info(f"top_left: {top_left}")
            log.info(f"bottom_right: {bottom_right}")
            log.info(f"{top_left + bottom_right}")
            log.info(f"Label: {get_label_with_tuple(self.original_frame, (top_left + bottom_right))}")
           
            cropped_image = self.original_frame[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
            
            if self.filename:
                cv2.imwrite(self.filename, cropped_image)
            else:
                # custom_filename = custom_utils.get_next_filename_number_on_start(constants.ADB_AUTO_FOLDER, "new.png")
                # custom_filepath = Path(constants.ADB_AUTO_FOLDER, custom_filename).as_posix()
                cv2.imwrite(Path(constants.ADB_IMAGE_FOLDER, "new.png").as_posix(), cropped_image)
            
            self.keep_open = False
            cv2.destroyAllWindows()