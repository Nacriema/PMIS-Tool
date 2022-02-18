#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 17 18:56:55 2022

@author: Nacriema

Refs:

"""
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from .custom_widgets import StoppableThread

from PIL import Image
from skimage.io import imread
from vegseg.linetracing import process, compute_angle
import time
import simplejson


class LineTracingTab(Frame):
    def __init__(self, master=None, mother=None, **kw):
        Frame.__init__(self, master, **kw)

        self.mother = mother

        # Variables that handle this TAB, define later
        self.line_type_values = ['', 0, 1, 2]

        self.start_point_values = [
            '',
            'Start point for line no.1',
            'Start point for line no.2',
            'Start point for line no.3']

        self.angle_values = [
            '',
            'Angle for line no.1',
            'Angle for line no.2',
            'Angle for line no.3']

        self.end_point_values = [
            '',
            'End point for line no.1',
            'End point for line no.2',
            'End point for line no.3'
        ]

        self._init_ui()

    def _init_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        powerline_frame = ttk.LabelFrame(master=self,
                                         text="Line tracing field",
                                         border=1,
                                         relief=SUNKEN)

        powerline_frame.grid(row=1, column=1, padx=(20, 10), pady=(20, 10), sticky='news')

        powerline_frame.columnconfigure(0, weight=1)
        powerline_frame.columnconfigure(1, weight=4)
        powerline_frame.columnconfigure(2, weight=2)
        powerline_frame.columnconfigure(3, weight=2)
        powerline_frame.columnconfigure(4, weight=2)
        powerline_frame.columnconfigure(5, weight=2)
        powerline_frame.columnconfigure(6, weight=1)

        powerline_frame.rowconfigure(0, weight=1)
        powerline_frame.rowconfigure(1, weight=1)
        powerline_frame.rowconfigure(2, weight=1)

        self.lines = ["", "Line no.1", "Line no.2", "Line no.3"]
        self.line_current_choice = StringVar(value=self.lines[1])

        # Choose Line no.
        powerline_option_menu = ttk.OptionMenu(powerline_frame,
                                               self.line_current_choice,
                                               *self.lines,
                                               command=self._powerline_option_trigger)

        powerline_option_menu.grid(row=1, column=1, padx=(20, 10), pady=(20, 10), sticky='news')
        Label(powerline_frame,
              text="Choose instance:",
              font=("Arial", 12)).grid(row=0, column=1, padx=(20, 10), pady=(20, 10), sticky='nws')

        # Choose Line type
        self.line_types = ["", "/", "|", "\\"]
        self.line_types_current_choice = StringVar(value=self.line_types[1])
        powerline_type = ttk.OptionMenu(powerline_frame,
                                        self.line_types_current_choice,
                                        *self.line_types)

        powerline_type.grid(row=1, column=2, padx=(20, 10), pady=(20, 10), sticky='news')
        Label(powerline_frame,
              text="Choose line type:",
              font=("Arial", 12)).grid(row=0, column=2, padx=(20, 10), pady=(20, 10), sticky='nws')

        # Start point Entry
        self.start_point_entry = ttk.Entry(powerline_frame)
        self.start_point_entry.bind("<1>", lambda event, flag=0: self._update_entry(flag))

        Label(powerline_frame,
              text="Start point:",
              font=("Arial", 12)).grid(row=0, column=3, padx=(20, 10), pady=(20, 10), sticky='nws')
        self.start_point_entry.grid(row=1, column=3, padx=(20, 10), pady=(20, 10), sticky='news')

        # End Point Entry
        self.end_point_entry = ttk.Entry(powerline_frame)
        self.end_point_entry.bind("<1>", lambda event, flag=1: self._update_entry(flag))

        Label(powerline_frame,
              text="End point:",
              font=("Arial", 12)).grid(row=0, column=4, padx=(20, 10), pady=(20, 10), sticky='nws')
        self.end_point_entry.grid(row=1, column=4, padx=(20, 10), pady=(20, 10), sticky='news')

        # Angle Entry
        self.angle_entry = ttk.Entry(powerline_frame, width=7)
        Label(powerline_frame,
              text="Angle:",
              font=("Arial", 12)).grid(row=0, column=5, padx=(20, 10), pady=(20, 10), sticky='nws')
        self.angle_entry.grid(row=1, column=5, padx=(20, 10), pady=(20, 10), sticky='news')

        # Button group which handle processing
        powerline_group_button_box = Frame(self)
        powerline_group_button_box.grid(row=1, column=2, padx=(10, 20), pady=(10, 20), sticky='news')

        powerline_group_button_box.columnconfigure(0, weight=1)
        powerline_group_button_box.columnconfigure(1, weight=4)
        powerline_group_button_box.columnconfigure(2, weight=1)

        powerline_group_button_box.rowconfigure(0, weight=1)
        powerline_group_button_box.rowconfigure(1, weight=4)
        powerline_group_button_box.rowconfigure(2, weight=4)
        powerline_group_button_box.rowconfigure(3, weight=1)

        ttk.Button(powerline_group_button_box,
                   text="Add property",
                   command=self._update_data).grid(row=1, column=1, padx=(10, 20), pady=(10, 20), sticky='ew')
        # command=self._update_entry)

        self.line_tracing_button = ttk.Button(powerline_group_button_box,
                                              text="Run Line Tracing",
                                              style="Accent.TButton",
                                              command=self._start_line_tracing)
        # command=self._start_calibrate)

        self.line_tracing_button.grid(row=2, column=1, padx=(10, 20), pady=(10, 20), sticky='ew')

    def _powerline_option_trigger(self, *args):
        """
        Update UI when user change the Line instance
        :param args:
        """
        self.mother.logger.log(f'Option has changed, current option is {self.line_current_choice.get()}')

        # Update the line type Option Menu
        current_line_type = self.line_type_values[
            self.lines.index(self.line_current_choice.get())]  # This i int or sth 0, 1, 2
        # Then we update the current type by this index
        self.line_types_current_choice.set(self.line_types[current_line_type + 1])

        # Update entries
        self.start_point_entry.delete(0, END)
        self.start_point_entry.insert(0, self.start_point_values[self.lines.index(self.line_current_choice.get())])

        self.end_point_entry.delete(0, END)
        self.end_point_entry.insert(0, self.end_point_values[self.lines.index(self.line_current_choice.get())])

        self.angle_entry.delete(0, END)
        self.angle_entry.insert(0, self.angle_values[self.lines.index(self.line_current_choice.get())])

    def _update_entry(self, flag):
        """
        When user click on the entry, then the data autofill by getting the information from UI
        This is used to add property to the entry box, but not the database.
        The angle is the same
        I just update to the database when user click the Add Property button
        :return:
        """
        print("Entry is active !!!")

        # Get User input from UI
        rect = self.mother.viewer.get_interaction_coord()
        print(f"Rect value: {rect}")  # Ok it can get the rect

        if flag == 0:
            print('Start Entry is Clicked !')
            angle = compute_angle(rect)

            # UPDATE Start Entry and Angle Entry,NOT the DATABASE
            self.start_point_entry.delete(0, END)
            self.start_point_entry.insert(0, rect[:2])

            self.angle_entry.delete(0, END)
            self.angle_entry.insert(0, angle)

        if flag == 1:
            print('End Entry is Clicked !')

            # UPDATE End Entry, NOT the DATABASE
            self.end_point_entry.delete(0, END)
            self.end_point_entry.insert(0, rect[:2])

    def _process_entry_input(self, entry_input):
        """
        Process the entry input used in _update_data
        :return:
        """
        # TODO: IMPORTANT I just NEED to convert x, y when use the data to perform line tracing when Click Run Button
        print(f'Entry input: {entry_input}')
        lst_float = [int(float(x)) for x in entry_input.split()]
        return lst_float

    def _update_data(self):
        """
        This function is used to update data when user click on ADD PROPERTY button
        These data is got from Entry box and OptionBox
        """
        print(f'Go to Update Data Function')
        instance_idx = self.lines.index(self.line_current_choice.get())

        line_type_idx = self.line_types.index(self.line_types_current_choice.get())
        print(f'Instance index: {instance_idx}')  # In range: 1, 2, 3
        print(f'Line type index: {line_type_idx}')  # In range: 1, 2, 3

        # Update DATABASE

        # 1. Update self.angle_values
        print(f"Current Angle: {self.angle_entry.get()}")
        print(f"Current Angle Type: {type(self.angle_entry.get())}")
        self.angle_values[instance_idx] = float(self.angle_entry.get())

        # Set the first 2 index as start point
        print(f"Current Start Point: {self.start_point_entry.get()}")
        print(f"Current Start Point Type: {type(self.start_point_entry.get())}")
        self.start_point_values[instance_idx] = self._process_entry_input(self.start_point_entry.get())

        # Set data for self.line_type_values
        self.line_type_values[instance_idx] = line_type_idx - 1

        print(f"Current End Point: {self.end_point_entry.get()}")
        print(f"Current End Point Type: {type(self.end_point_entry.get())}")
        self.end_point_values[instance_idx] = self._process_entry_input(self.end_point_entry.get())

        # Update these to the UI view, call again the _powerline_option_trigger function to update
        self._powerline_option_trigger()

    def _start_line_tracing(self):
        print(f'Go to _start_calibrate')
        if not self.mother.paths:
            messagebox.showerror("Error", "No image has been loaded!")
            return
        if not self.mother.running:
            self.mother.running = True
            self.mother.thread = StoppableThread(target=self._line_tracing)
            self.mother.thread.daemon = True
            self.mother.thread.start()
            self.line_tracing_button.configure(state='disabled')

    def _prepare_data(self):
        """
        Convert our DATABASE into init_points format
        :return:
        """
        # [((1078, 1340), 2, (300, 1037), 67.), ...]
        init_points = []
        for idx in range(1, len(self.line_type_values)):
            start_point = tuple(self.start_point_values[idx][::-1])
            line_type = self.line_type_values[idx]
            end_point = tuple(self.end_point_values[idx][::-1])
            angle = self.angle_values[idx]
            init_points.append(tuple([start_point, line_type, end_point, angle]))

        print(f'Init point after process: {init_points}')
        return init_points

    def _line_tracing(self):
        # TODO: Change the x, y POSITION when creating the init_points from data above
        print(f'Go to _line_tracing !!!')
        path = self.mother.paths[self.mother.pathidx]
        self.mother.logger.clear()
        self.mother.logger.log("Line tracing from '{}' ...\n".format(path))
        self.mother.logger.log("Please wait ...")

        print(f'All data we have:')
        print(f'Line type: {self.line_type_values}')
        print(f'Start point: {self.start_point_values}')
        print(f'Angles: {self.angle_values}')
        print(f'End point: {self.end_point_values}')

        if path.split('.')[-1].lower() in ['jpg', 'png', 'jpeg']:
            # Open image using scipy library
            image_rgb = imread(path)

            # Prepare init_points
            init_points = self._prepare_data()

            _, _, im_with_result_sets_raw = process(image_rgb, init_points)

            result_im = Image.fromarray(im_with_result_sets_raw)

            new_img_path = path.split('.')[0] + time.strftime("-%Y%m%d-%H%M%S") + '.jpg'
            result_im.save(new_img_path)

            self.mother.paths = self.mother.paths[:self.mother.pathidx + 1] + [new_img_path] + self.mother.paths[
                                                                                               self.mother.pathidx + 1:]
            self.mother.pathidx += 1

            self.line_tracing_button.configure(state='normal')
            self.mother.running = False

            # Update result image into viewer
            self.mother.load_file()
            self.mother.logger.log('DONE')

