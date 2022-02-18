#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 15 09:42:43 2022

@author: Nacriema

Refs:

"""
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from .custom_widgets import StoppableThread
from .. import FIELDS
import os
from PIL import Image
from vegseg.calibration import process, visualization
import time
import simplejson


class CalibrationTab(Frame):
    def __init__(self, master=None, mother=None, **kw):
        Frame.__init__(self, master, **kw)

        self.mother = mother

        # Values for Options in Option menus, I set it as the list
        self.entry_values = ['0',
                             '1',
                             '2',
                             '3',
                             '4',
                             '5',
                             '6',
                             '7',
                             '8']
        self._init_ui()

    def _init_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        camera_frame = ttk.LabelFrame(master=self,
                                      text="Camera calibration field",
                                      border=1,
                                      relief=SUNKEN)
        camera_frame.grid(row=1, column=1, padx=(20, 10), pady=(20, 10), sticky='news')

        camera_frame.columnconfigure(0, weight=1)
        camera_frame.columnconfigure(1, weight=4)
        camera_frame.columnconfigure(2, weight=4)
        camera_frame.columnconfigure(3, weight=1)
        camera_frame.rowconfigure(0, weight=1)
        camera_frame.rowconfigure(1, weight=1)
        camera_frame.rowconfigure(2, weight=1)

        self.option_menu_list = ["", "Line 1", "Line 2", "Line 3", "Line 4", "Ref point 1 pixel", "Ref point 2 pixel",
                                 "Ref point 1 3D pos", "Ref point 2 3D pos"]
        self.current_choice = StringVar(value=self.option_menu_list[1])

        ttk.OptionMenu(camera_frame,
                                     self.current_choice,
                                     *self.option_menu_list,
                                     command=self._option_menu_trigger).grid(row=1, column=1, padx=(20, 10), pady=(20, 10), sticky='news')

        Label(camera_frame,
              text="Choose instance:",
              font=("Arial", 12)).grid(row=0, column=1, padx=(20, 10), pady=(20, 10), sticky='nws')

        self.entry = ttk.Entry(camera_frame)

        Label(camera_frame,
              text="Value:",
              font=("Arial", 12)).grid(row=0, column=2, padx=(20, 10), pady=(20, 10), sticky='nws')

        # The insertion is just insert the string to the field
        self.entry.insert(0, "Entry")
        self.entry.grid(row=1, column=2, padx=(20, 10), pady=(20, 10), sticky='news')

        # The button which handle processing
        group_button_box = Frame(self)
        group_button_box.grid(row=1, column=2, padx=(10, 20), pady=(10, 20), sticky='news')

        group_button_box.columnconfigure(0, weight=1)
        group_button_box.columnconfigure(1, weight=4)
        group_button_box.columnconfigure(2, weight=1)

        group_button_box.rowconfigure(0, weight=1)
        group_button_box.rowconfigure(1, weight=4)
        group_button_box.rowconfigure(2, weight=4)
        group_button_box.rowconfigure(3, weight=1)

        add_property_box = ttk.Button(group_button_box,
                                      text="Add property",
                                      command=self._update_entry)
        add_property_box.grid(row=1, column=1, padx=(10, 20), pady=(10, 20), sticky='ew')

        self.calibration_button = ttk.Button(group_button_box,
                                             text="Run Calibration",
                                             style="Accent.TButton",
                                             command=self._start_calibrate)
        self.calibration_button.grid(row=2, column=1, padx=(10, 20), pady=(10, 20), sticky='ew')

    def _option_menu_trigger(self, *args):
        self.mother.logger.log(f"Option has changed, current option is {self.current_choice.get()}")
        self.entry.delete(0, END)
        self.entry.insert(0, self.entry_values[self.option_menu_list.index(self.current_choice.get())])

    def _process_3d_coordinate_input(self, userinput):
        print(f'User input 3D coord: {userinput}')
        lst_float = [float(x) for x in userinput.split()]
        print(f'Input after process: {lst_float}')
        return lst_float

    def _update_entry(self):
        print(f'Goto _update_entry')
        current_idx = self.option_menu_list.index(self.current_choice.get())
        if current_idx == 5 or current_idx == 6:
            temp = self.mother.viewer.get_interaction_coord()
            print(f'Temp value: {temp}')
            self.entry_values[current_idx] = temp[:2]
            print(f'self.entry_values[current_idx] = {self.entry_values[current_idx]}')
        elif current_idx == 7 or current_idx == 8:
            print(f'Index 7 or 8 is choosed !!!!')
            print(f'User input type: {type(self.entry.get())}')
            print(f'User input: {self.entry.get()}')
            lst_float = self._process_3d_coordinate_input(self.entry.get())
            self.entry_values[current_idx] = lst_float
        else:
            rect = self.mother.viewer.get_interaction_coord()
            self.entry_values[current_idx] = rect

        # Update this value to the UI to view
        self.entry.delete(0, END)
        self.entry.insert(0, self.entry_values[self.option_menu_list.index(self.current_choice.get())])
        print(f'Debug self.entry_values = {self.entry_values}')

    def _start_calibrate(self):
        print(f'Go to _start_calibrate')
        if not self.mother.paths:
            messagebox.showerror("Error", "No image has been loaded!")
            return
        if not self.mother.running:
            self.mother.running = True
            self.mother.thread = StoppableThread(target=self._calibrate)
            self.mother.thread.daemon = True
            self.mother.thread.start()
            self.calibration_button.configure(state='disabled')

    def _calibrate(self):
        print(f'Go to _calibrate !!!')

        path = self.mother.paths[self.mother.pathidx]
        self.mother.logger.clear()
        self.mother.logger.log("Calibrate from '{}'...\n".format(path))
        self.mother.logger.log("Please wait ...")

        if path.split('.')[-1].lower() in ['jpg', 'png', 'jpeg']:
            image_rgb = Image.open(path)

            # Start process the image
            v1_left, v1_right, v2_left, v2_right = self.entry_values[1], self.entry_values[2], self.entry_values[3], \
                                                   self.entry_values[4]
            corres_point_left, corres_point_right = self.entry_values[5], self.entry_values[6]
            pylon_left, pylon_right = self.entry_values[7], self.entry_values[8]

            result, pp_x, pp_y, v1, v2, v3, v1_left_0, v1_left_bot, v1_right_0, v1_right_bot, v2_left_bot, v2_right_bot = \
                process(image_rgb, v1_left, v1_right, v2_left, v2_right, corres_point_left, corres_point_right,
                        pylon_left,
                        pylon_right)

            # Save the result, same as
            visualization(image_rgb, pp_x, pp_y, v1, v2, v3, v1_left_0, v1_left_bot, v1_right_0, v1_right_bot,
                          v2_left_bot,
                          v2_right_bot, corres_point_left, corres_point_right)

            # 1. Save the blend_img in the same folder
            new_img_path = path.split('.')[0] + time.strftime("-%Y%m%d-%H%M%S") + '.jpg'
            image_rgb.save(new_img_path)

            # 2. Append this string into the self.paths at the next position of the current image,
            # change the index as well
            self.mother.paths = self.mother.paths[:self.mother.pathidx + 1] + [new_img_path] + self.mother.paths[self.mother.pathidx + 1:]
            self.mother.pathidx += 1

            # 3. Update the viewer
            self.calibration_button.configure(state='normal')
            self.mother.running = False

            self.mother.load_file()
            self.mother.logger.log(simplejson.dumps(result, indent=2, sort_keys=True))
            self.mother.logger.log('DONE')
