#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 09 16:06:41 2022

@author: Nacriema

Refs:

"""
import os
import subprocess
import tempfile
import re

# TODO: These imports should be removed !!!
import time
import pdfplumber

# TODO: Import things for process the images
import torch
from ..models import load_model_from_path
from ..utils import coerce_to_path_and_check_exist
from ..utils.path import MODELS_PATH
from ..utils.constant import MODEL_FILE, LABEL_TO_COLOR_MAPPING
from ..utils.image import LabeledArray2Image
import numpy as np

import simplejson
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from wand.exceptions import WandException

from .. import FIELDS
from .custom_widgets import MenuBox, HoverButton, Logger, StoppableThread
from .help_box import HelpBox
from .viewer import ImageViewer


class Segmentor(Frame):

    def __init__(self, master=None, **kw):
        Frame.__init__(self, master, **kw)
        self.background = '#f7f7f7'
        # '#303030'
        self.border_color = '#c7c7c7'
        self.checkbox_color = '#f7f7f7'  # Color for the Field check box, I set the same color as background color
        # self.highlight_color = '#558de8' # blue light
        self.highlight_color = '#e0e0e0'
        self.image = None
        self.paths = list()
        self.pathidx = -1
        self.checkboxes = {}
        self.thread = None
        self.running = False
        self.save_dir = '.'
        self._init_ui()

    def _init_ui(self):
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        h = hs - 100
        w = (int(h / 1.414) + 100) * 2
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.master.maxsize(w, h)
        self.master.minsize(w, h)
        self.master.title("Vegetation Segmentor")

        self.pack(fill=BOTH, expand=True)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)

        tool_frame = Frame(self, bg=self.background, bd=0, relief=SUNKEN)

        # TODO: Image Viewer is a bunch of items, contains interaction on top as well the canvas interaction (Display
        #  Canvas), see the custom Image Viewer class, and Display Canvas class  for more information
        self.viewer = ImageViewer(self)

        interface = Frame(self, bg=self.background, bd=0, relief=SUNKEN,
                          highlightbackground=self.border_color, highlightthickness=1)

        tool_frame.grid(row=0, column=0, sticky='news')
        self.viewer.grid(row=0, column=1, sticky='news')
        interface.grid(row=0, column=2, sticky='news')

        # Tool Frame
        tool_frame.columnconfigure(0, weight=1)
        tool_frame.rowconfigure(0, weight=0)
        tool_frame.rowconfigure(1, weight=1)
        tool_frame.rowconfigure(2, weight=0)
        tool_frame.rowconfigure(3, weight=2)

        # TODO: Options is the MenuBox
        options = MenuBox(tool_frame, image_path=r'widgets/options.png',
                          background=self.background,
                          highlight=self.highlight_color)

        options.grid(row=0, column=0)

        options.add_item('Open Files...', self._open_file)
        options.add_item('Open Directory...', self._open_dir, seperator=True)
        options.add_item('Set Save Directory...', self._set_save_path, seperator=True)
        options.add_item('Next File', self._next_file)
        options.add_item('Previous File', self._prev_file, seperator=True)
        options.add_item('Clear Page', self.viewer.clear)
        options.add_item('Search Text', self.viewer.search_text)
        options.add_item('Extract ...', self.viewer.extract_text)
        # options.add_item('Run OCR', self._run_ocr, seperator=True)
        options.add_item('Clear Image Queue', self._clear_queue, seperator=True)
        options.add_item('Help...', self._help, seperator=True)
        options.add_item('Exit', self.master.quit)

        tools = Frame(tool_frame, bg=self.background, bd=0, relief=SUNKEN)
        tools.grid(row=2, column=0)

        HoverButton(tools,
                    image_path=r'widgets/open_file.png',
                    command=self._open_file,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Open Files",
                    highlightthickness=0,
                    activebackground=self.highlight_color).pack(pady=2)

        HoverButton(tools,
                    image_path=r'widgets/open_dir.png',
                    command=self._open_dir,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Open Directory",
                    highlightthickness=0,
                    activebackground=self.highlight_color).pack(pady=2)

        HoverButton(tools,
                    image_path=r'widgets/save_as.png',
                    command=self._set_save_path,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Set Save Directory",
                    highlightthickness=0,
                    activebackground=self.highlight_color).pack(pady=2)

        HoverButton(tools,
                    image_path=r'widgets/clear_page.png',
                    command=self.viewer.clear,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Clear Current Image",
                    highlightthickness=0,
                    activebackground=self.highlight_color).pack(pady=2)

        HoverButton(tools,
                    image_path=r'widgets/search.png',
                    command=self.viewer.search_text,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0, tool_tip="Search Text",
                    highlightthickness=0,
                    activebackground=self.highlight_color).pack(pady=2)

        HoverButton(tools,
                    image_path=r'widgets/extract.png',
                    command=self.viewer.extract_text,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Extract Text",
                    highlightthickness=0,
                    activebackground=self.highlight_color).pack(pady=2)

        # HoverButton(tools, image_path=r'widgets/ocr.png', command=self._run_ocr,
        #             width=50, height=50, bg=self.background, bd=0, tool_tip="Run OCR",
        #             highlightthickness=0, activebackground=self.highlight_color).pack(pady=2)

        HoverButton(tools,
                    image_path=r'widgets/clear_all.png',
                    command=self._clear_queue,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Clear Image Queue",
                    highlightthickness=0,
                    activebackground=self.highlight_color).pack(pady=2)

        file_frame = Frame(tools, width=50, height=50, bg=self.background, bd=0, relief=SUNKEN)
        file_frame.pack(pady=2)

        file_frame.columnconfigure(0, weight=1)
        file_frame.columnconfigure(1, weight=1)

        HoverButton(file_frame,
                    image_path=r'widgets/prev_file.png',
                    command=self._prev_file,
                    width=25,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Previous File",
                    highlightthickness=0,
                    activebackground=self.highlight_color).grid(row=0, column=0)

        HoverButton(file_frame,
                    image_path=r'widgets/next_file.png',
                    command=self._next_file,
                    width=25,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Next File",
                    highlightthickness=0,
                    activebackground=self.highlight_color).grid(row=0, column=1)

        self.doc_label = Label(file_frame,
                               bg=self.background,
                               bd=0,
                               fg='black',
                               font=("Arial", 8),
                               text="0 of 0")
        self.doc_label.grid(row=1, column=0, columnspan=2, pady=4, sticky='news')

        HoverButton(tool_frame,
                    image_path=r'widgets/help.png',
                    command=self._help,
                    width=50,
                    height=50,
                    bg=self.background,
                    bd=0,
                    tool_tip="Help",
                    highlightthickness=0,
                    activebackground=self.highlight_color).grid(row=3, column=0, sticky='s')

        # Interface Frame
        interface.columnconfigure(0, weight=1)
        interface.rowconfigure(0, weight=0)
        interface.rowconfigure(1, weight=1)
        interface.rowconfigure(2, weight=1)

        # TODO: highlight thickness param is used to enable the border view of my GUI component, this is used when I
        #  build the application, in production we need to set them = 0 to hide it

        # TODO: Change the UI Structure !!!!

        logo_frame = Frame(interface, bg=self.background, bd=0, relief=SUNKEN,
                           highlightbackground=self.border_color, highlightthickness=1)
        param_frame = Frame(interface, bg=self.background, bd=0, relief=SUNKEN,
                            highlightbackground=self.border_color, highlightthickness=1)
        main_frame = Frame(interface, bg=self.background, bd=0, relief=SUNKEN,
                           highlightbackground=self.border_color, highlightthickness=1)

        logo_frame.grid(row=0, column=0, sticky='news')
        param_frame.grid(row=1, column=0, sticky='news')
        main_frame.grid(row=2, column=0, sticky='news')

        # Logo Frame
        logo_frame.columnconfigure(0, weight=1)
        logo_frame.columnconfigure(1, weight=0)
        logo_frame.columnconfigure(2, weight=0)
        logo_frame.columnconfigure(3, weight=1)
        logo_frame.rowconfigure(0, weight=1)

        self.logo_img = ImageTk.PhotoImage(Image.open(r'widgets/logo.png'))
        Label(logo_frame,
              bg=self.background,
              image=self.logo_img).grid(row=0, column=1, sticky='news', pady=10)

        Label(logo_frame,
              text="PMIS Vegetation Segmentor",
              bg=self.background,
              fg="black",
              font=("Arial", 24, "bold")).grid(row=0, column=2, sticky='news', padx=20, pady=10)

        # TODO: Config grid for param frame, this may be no need if we place the Notebook inside it
        # param_frame.rowconfigure(0, weight=1)
        # param_frame.columnconfigure(0, weight=1)

        # Add Note book, It contains 3 tab correspond with 3 tools I've made
        notebook = ttk.Notebook(param_frame)
        # notebook.grid(row=0, column=0)
        notebook.pack(fill='both', expand=True)

        # Create Segmentation tab, Line tracing tab, Camera calibration tab and then add to Notebook
        segmentation_tab = Frame(notebook,
                                 bg=self.background,
                                 bd=0,
                                 relief=SUNKEN,
                                 highlightbackground=self.border_color,
                                 highlightthickness=1)

        line_tracing_tab = Frame(notebook,
                                 bg=self.background,
                                 bd=0,
                                 relief=SUNKEN,
                                 highlightbackground=self.border_color,
                                 highlightthickness=1)

        camera_calibration_tab = Frame(notebook,
                                       bg=self.background,
                                       bd=0,
                                       relief=SUNKEN,
                                       highlightbackground=self.border_color,
                                       highlightthickness=1)

        vegetation_measurement_tab = Frame(notebook,
                                           bg=self.background,
                                           bd=0,
                                           relief=SUNKEN,
                                           highlightbackground=self.border_color,
                                           highlightthickness=1)

        # ORDER OF TABS HERE
        notebook.add(segmentation_tab, text="Segmentation Tool")
        notebook.add(camera_calibration_tab, text="Camera Calibration Tool")
        notebook.add(line_tracing_tab, text="Line Tracing Tool")
        notebook.add(vegetation_measurement_tab, text="Vegetation Measurement Tool")

        # BEGIN: Edit Segmentation Tab
        # segmentation_tab.grid(row=0, column=0, sticky='news')
        segmentation_tab.columnconfigure(0, weight=1)
        segmentation_tab.columnconfigure(1, weight=4)
        segmentation_tab.columnconfigure(2, weight=1)
        segmentation_tab.rowconfigure(0, weight=1)
        segmentation_tab.rowconfigure(1, weight=1)
        segmentation_tab.rowconfigure(2, weight=1)

        # Segmentation Button
        self.start_button = HoverButton(segmentation_tab,
                                        command=self._start,
                                        text='Run Segment',
                                        compound='center',
                                        font=("Arial", 10),
                                        bd=0,
                                        bg=self.background,
                                        fg='white',
                                        highlightthickness=0,
                                        image_path=r'widgets/begin.png',
                                        activebackground=self.background)

        self.start_button.grid(row=1, column=2, pady=10, padx=20, sticky='w')

        # TODO: Change theme here
        # Field Checkboxes
        # Old code
        # field_param = Frame(param_frame,
        #                     bg=self.background, bd=0,
        #                     relief=SUNKEN,
        #                     highlightbackground=self.border_color,
        #                     highlightthickness=1)
        #
        # field_param.grid(row=1, column=1, sticky='news')

        # field_frame = Frame(field_param,
        #                     bg=self.checkbox_color,
        #                     bd=0, relief=SUNKEN,
        #                     highlightbackground=self.border_color,
        #                     highlightthickness=1)
        #
        # field_frame.pack(expand=True, fill=BOTH)
        #
        # Label(field_frame,
        #       text="Segmentation field:",
        #       width=30,
        #       bg=self.checkbox_color,
        #       anchor='w',
        #       fg="black",
        #       font=("Arial", 12, "bold")).pack(side=TOP, fill=X, padx=5, pady=5)

        field_frame = ttk.LabelFrame(master=segmentation_tab,
                                     text="Segmentation field",
                                     border=1,
                                     relief=SUNKEN)

        field_frame.grid(row=1, column=1, padx=(20, 10), pady=(20, 10), sticky='news')

        # Check box_frame contain all the checkbox inside
        checkbox_frame = Frame(field_frame, bg=self.checkbox_color, bd=0, relief=SUNKEN,
                               highlightbackground=self.border_color, highlightthickness=0)
        checkbox_frame.pack(expand=True, fill=BOTH, side=BOTTOM)

        checkbox_frame.columnconfigure(0, weight=1)
        checkbox_frame.columnconfigure(1, weight=1)
        checkbox_frame.columnconfigure(2, weight=1)
        checkbox_frame.columnconfigure(3, weight=1)
        for i in range(len(FIELDS) // 2 + 1):
            checkbox_frame.rowconfigure(i, weight=1)

        FIELDS_FG_COLORS = ["#000000", "#c0c000", "#808000"]
        for idx, key in enumerate(FIELDS):
            self.checkboxes[key] = BooleanVar(checkbox_frame, value=False)
            state = False
            if os.path.exists('./models/invoicenet/'):
                state = key in os.listdir('./models/invoicenet/')
            state = True

            # Adjust the check button and color of the tick icon
            # Checkbutton(checkbox_frame,
            #             fg=FIELDS_FG_COLORS[idx],
            #             bg=self.checkbox_color,
            #             activebackground=self.checkbox_color,
            #             variable=self.checkboxes[key],
            #             state="normal" if state else "disabled",
            #             highlightthickness=0).grid(row=idx // 2, column=2 if idx % 2 else 0, sticky='news',
            #                                        padx=(10, 0))

            # TODO: Change Checkbutton style, use sun-valley theme design
            ttk.Checkbutton(checkbox_frame,
                            variable=self.checkboxes[key],
                            state="normal" if state else "disabled").grid(row=idx // 2, column=2 if idx % 2 else 0,
                                                                          sticky='news',
                                                                          padx=(10, 0))
            # This is label for Checkbutton
            Label(checkbox_frame,
                  text=key,
                  bg=self.checkbox_color,
                  fg=FIELDS_FG_COLORS[idx],
                  font=("Arial", 12)).grid(row=idx // 2, column=3 if idx % 2 else 1, sticky='nws')
        # END: Segmentation Tab

        # BEGIN: Edit Calibration Tab

        camera_calibration_tab.columnconfigure(0, weight=1)
        camera_calibration_tab.columnconfigure(1, weight=4)
        camera_calibration_tab.columnconfigure(2, weight=1)
        camera_calibration_tab.rowconfigure(0, weight=1)
        camera_calibration_tab.rowconfigure(1, weight=1)
        camera_calibration_tab.rowconfigure(2, weight=1)

        camera_frame = ttk.LabelFrame(master=camera_calibration_tab,
                                      text="Camera calibration field",
                                      border=1,
                                      relief=SUNKEN)
        camera_frame.grid(row=1, column=1, padx=(20, 10), pady=(20, 10), sticky='news')

        camera_frame.columnconfigure(0, weight=1)
        camera_frame.columnconfigure(1, weight=4)
        camera_frame.columnconfigure(2, weight=4)
        camera_frame.columnconfigure(3, weight=1)
        camera_frame.rowconfigure(0, weight=0)
        camera_frame.rowconfigure(1, weight=1)
        camera_frame.rowconfigure(2, weight=1)

        self.option_menu_list = ["", "Line 1", "Line 2", "Line 3", "Line 4", "Ref point 1 pixel", "Ref point 2 pixel",
                                 "Ref point 1 3D pos", "Ref point 2 3D pos"]
        self.var_4 = StringVar(value=self.option_menu_list[1])

        option_menu = ttk.OptionMenu(camera_frame,
                                     self.var_4,
                                     *self.option_menu_list)

        option_menu.grid(row=1, column=1, padx=(20, 10), pady=(20, 10), sticky='news')
        Label(camera_frame,
              text="Choose instance:",
              font=("Arial", 12)).grid(row=0, column=1, padx=(20, 10), pady=(20, 10), sticky='nws')
        # option_menu.pack(expand=True, fill=BOTH, side=BOTTOM)

        entry = ttk.Entry(camera_frame)
        Label(camera_frame,
              text="Value:",
              font=("Arial", 12)).grid(row=0, column=2, padx=(20, 10), pady=(20, 10), sticky='nws')

        # The insertion is just insert the string to the field
        entry.insert(0, "Entry")
        entry.grid(row=1, column=2, padx=(20, 10), pady=(20, 10), sticky='news')

        # The button which handle processing
        calibration_button = ttk.Button(camera_calibration_tab, text="Run Calibration", style="Accent.TButton")
        calibration_button.grid(row=1, column=2, padx=(10, 20), pady=(10, 20), sticky='w')

        # END: Calibration Tab

        # Main Frame
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)

        self.logger = Logger(main_frame, disable=False, height=18, bg=self.background, bd=0, relief=SUNKEN)
        self.logger.grid(row=1, column=1, sticky='news')

        button_frame = Frame(main_frame, bg=self.background, bd=0, relief=SUNKEN,
                             highlightbackground=self.border_color, highlightthickness=0)
        button_frame.grid(row=2, column=1, sticky='news')

        button_frame.rowconfigure(0, weight=1)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)
        button_frame.columnconfigure(3, weight=1)

        HoverButton(button_frame,
                    image_path=r'widgets/labels.png',
                    command=self._save_info,
                    text='Save Information',
                    compound='center',
                    font=("Arial", 10),
                    bd=0,
                    bg=self.background,
                    fg='white',
                    highlightthickness=0,
                    activebackground=self.background).grid(row=0, column=1, padx=10)

        HoverButton(button_frame,
                    image_path=r'widgets/labels.png',
                    command=self._load_labels,
                    text='Load Labels',
                    compound='center',
                    font=("Arial", 10),
                    bd=0,
                    bg=self.background,
                    fg='white',
                    highlightthickness=0,
                    activebackground=self.background).grid(row=0, column=2, padx=10)

    def _extract(self):
        path = self.paths[self.pathidx]

        self.logger.clear()
        self.logger.log("Segmenting from '{}'...\n".format(path))
        self.logger.log("Please wait ...")

        if path.split('.')[-1].lower() in ['jpg', 'png', 'jpeg']:
            image = Image.open(path)

            # Start to loading the pretrained model here
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            TAG = 'Full_data_Soft_Dice_Loss_V2'
            model_path = coerce_to_path_and_check_exist(MODELS_PATH / TAG / MODEL_FILE)

            self.logger.log("Loading model ...")
            model, (img_size, restricted_labels, normalize) = load_model_from_path(model_path, device=device,
                                                                                   attributes_to_return=[
                                                                                       'train_resolution',
                                                                                       'restricted_labels',
                                                                                       'normalize'])
            _ = model.eval()
            self.logger.log(f'Image size is: {image.size}')
            normalize = True
            inp = np.array(image, dtype=np.float32) / 255
            if normalize:
                inp = ((inp - inp.mean(axis=(0, 1))) / (inp.std(axis=(0, 1)) + 10 ** -7))
            inp = torch.from_numpy(inp.transpose(2, 0, 1)).float().to(device)

            with torch.no_grad():
                pred = model(inp.reshape(1, *inp.shape))[0].max(0)[1].cpu().numpy()

            # Retrieve color mapping and transform to image
            # TODO: I may get this value GLOBALY

            RGB_COLOR_FOR_FIELDS = [(0, 0, 0), (192, 192, 0), (128, 128, 0)]
            restricted_colors = []
            restricted_labels = []

            # Iterate through this variable and generate the restricted_colors, 'Background': 0
            for (key, value) in FIELDS.items():
                if self.checkboxes[key].get():
                    # Add the corresponding color to restricted_colors
                    restricted_colors.append(RGB_COLOR_FOR_FIELDS[value])
                    restricted_labels.append(value)

            label_idx_color_mapping = {l: c for l, c in
                                       zip(restricted_labels, restricted_colors)}

            pred_img = LabeledArray2Image.convert(pred, label_idx_color_mapping)
            mask = Image.fromarray((np.array(pred_img) == (0, 0, 0)).all(axis=-1).astype(np.uint8) * 127 + 128)
            blend_img = Image.composite(image, pred_img, mask)

            # 1. Save the blend_img in the same folder
            new_img_path = path.split('.')[0] + time.strftime("-%Y%m%d-%H%M%S") + '.jpg'
            blend_img.save(new_img_path)

            # 2. Append this string into the self.paths at the next position of the current image,
            # change the index as well
            self.paths = self.paths[:self.pathidx + 1] + [new_img_path] + self.paths[self.pathidx + 1:]
            self.pathidx += 1

            # 3. Update the viewer
            self._load_file()
            self.logger.log('DONE')

        #     pdf = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
        #     temp = tempfile.NamedTemporaryFile(suffix='.pdf')
        #     temp.write(pdf)
        #     path = temp.name
        #
        # predictions = {}
        # for key in FIELDS:
        #     if self.checkboxes[key].get():
        #         model = AttendCopyParse(field=key, restore=True)
        #         predictions[key] = model.predict(paths=[path])[0]

        # if temp is not None:
        #     temp.close()

        # TODO: Label, this can be customize for the Line tracing task
        # self.viewer.label(labels=predictions)

        # Fake data
        predictions = {
            'author': 'nacriema',
            'message': 'here'
        }

        self.logger.log(simplejson.dumps(predictions, indent=2, sort_keys=True))
        self.start_button.configure(state='normal')
        self.running = False

    def _start(self):
        if not self.paths:
            messagebox.showerror("Error", "No image has been loaded!")
            return

        # Variable used to check if any field is checked, if none of them is checked then allert
        selected = False
        for key in FIELDS:
            if self.checkboxes[key].get():
                selected = True
                break

        if not selected:
            messagebox.showerror("Error", "No fields were selected!")
            return

        if not self.running:
            self.running = True
            self.thread = StoppableThread(target=self._extract)
            self.thread.daemon = True
            self.thread.start()
            self.start_button.configure(state='disabled')

    def _load_labels(self):
        if self.image is None:
            messagebox.showerror("Error", "Load an image first!")
            return

        label_file = filedialog.askopenfile(filetypes=[('JSON files', '*.json'), ('all files', '.*')],
                                            initialdir=self.save_dir, title="Select label file")
        if label_file is None:
            return

        try:
            labels = simplejson.load(label_file)
        except simplejson.errors.JSONDecodeError:
            messagebox.showerror("Error", "JSON file is invalid!")
            return

        match = re.findall(r"[^{]*{([^}]+)}", self.logger.get())
        if match:
            log_data = simplejson.loads('{' + ''.join(match) + '}')
            for key in log_data.keys():
                if key not in labels:
                    labels[key] = log_data[key]

        self.viewer.label(labels=labels)
        self.logger.clear()
        self.logger.log("Extracting information from '{}'...\n".format(self.paths[self.pathidx]))
        self.logger.log(simplejson.dumps(labels, indent=2, sort_keys=True))
        self.logger.log("\nLoaded labels from '{}'".format(label_file.name))

    def _save_info(self):
        if self.image is None:
            messagebox.showerror("Error", "Load an image first!")
            return

        match = re.findall(r"[^{]*{([^}]+)}", self.logger.get())

        if not match:
            messagebox.showerror("Error", "Could not parse a valid dictionary!")
            return

        try:
            new_labels = simplejson.loads('{' + ''.join(match) + '}')
        except simplejson.errors.JSONDecodeError:
            messagebox.showerror("Error", "Could not parse a valid dictionary!")
            return

        path = os.path.join(self.save_dir, os.path.splitext(os.path.basename(self.paths[self.pathidx]))[0] + '.json')

        labels = {}
        if os.path.exists(path):
            with open(path, encoding="utf8") as fp:
                try:
                    labels = simplejson.load(fp)
                    self.logger.log("\n'{}' already exists, adding updated labels to this file".format(path))
                except simplejson.errors.JSONDecodeError:
                    pass

        for label in new_labels.keys():
            labels[label] = new_labels[label]

        try:
            with open(path, 'w') as out:
                out.write(simplejson.dumps(labels, indent=2, sort_keys=True))
        except simplejson.errors.JSONDecodeError:
            messagebox.showerror("Error", "Error occurred while writing JSON file!")
            return

        self.logger.log("\nWrote information to '{}'".format(path))

    def _set_save_path(self):
        path = filedialog.askdirectory(title='Set Save Directory', initialdir=self.save_dir)
        if path == '' or not path:
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "Invalid directory!")
            return
        self.save_dir = path
        self.logger.log("Information will now be saved in '{}'".format(self.save_dir))

    def _next_file(self):
        if self.pathidx == len(self.paths) - 1 or len(self.paths) == 0:
            return
        self.pathidx += 1
        self._load_file()

    def _prev_file(self):
        if self.pathidx == 0 or len(self.paths) == 0:
            return
        self.pathidx -= 1
        self._load_file()

    # TODO: This function here need to be renew for later task
    # def _run_ocr(self):
    #     if self.image is None:
    #         return
    #
    #     pdf_pages = list()
    #     for page in self.image.pages:
    #         image = page.to_image(resolution=100)
    #         pdf = pytesseract.image_to_pdf_or_hocr(image.original, extension='pdf')
    #         pdf_pages.append(pdf)
    #
    #     pdf_writer = PyPDF2.PdfFileWriter()
    #     for page in pdf_pages:
    #         pdf = PyPDF2.PdfFileReader(io.BytesIO(page))
    #         pdf_writer.addPage(pdf.getPage(0))
    #
    #     pdf = io.BytesIO()
    #     pdf_writer.write(pdf)
    #
    #     self.image = pdfplumber.load(pdf)
    #     self.viewer.display_pdf(self.image)

    # TODO: Change here, I not display pdf, display image instead !!!
    def _load_file(self):
        """
        This function use index in path index in self.paths variable to open image for view in canvas
        :return:
        """
        self.viewer.clear()
        path = self.paths[self.pathidx]
        filename = os.path.basename(path)
        try:
            if filename.split('.')[-1].lower() in ['jpg', 'png']:
                image = Image.open(path)
                # pdf = io.BytesIO(pytesseract.image_to_pdf_or_hocr(image, extension='pdf'))
                # self.image = pdfplumber.load(pdf)
                self.image = image
            else:
                # TODO: Avoid using pdfplumber !
                self.image = pdfplumber.open(path)
            self.viewer.display_image(self.image)
            self.doc_label.configure(text="{} of {}".format(self.pathidx + 1, len(self.paths)))
            self.logger.clear()
            self.logger.log("Showing image '{}'".format(path))
        except WandException:
            result = messagebox.askokcancel("Error",
                                            "ImageMagick Policy Error! Should InvoiceNet try to fix the error?")
            if result:
                result = self._fix_policy_error()
            if result:
                messagebox.showinfo("Policy Fixed!", "ImageMagick Policy Error fixed! Restart InvoiceNet.")
            else:
                messagebox.showerror("ImageMagick Policy Error",
                                     "Coud not fix ImageMagick policy. Rejecting the current pdf file!")
        except (IndexError, IOError, TypeError):
            pass

    def _open_file(self):
        paths = filedialog.askopenfilenames(filetypes=[('JPG files', '*.jpg'),
                                                       ('JPEG files', '*.jpeg'),
                                                       ('PNG files', '*.png'),
                                                       ('all files', '.*')],
                                            initialdir='.',
                                            title="Select files", multiple=True)
        if not paths or paths == '':
            return
        paths = [path for path in paths if os.path.basename(path).split('.')[-1].lower() in ['jpg', 'png', 'jpeg']]
        self.paths = self.paths[:self.pathidx + 1] + paths + self.paths[self.pathidx + 1:]

        print(f'self.paths = {self.paths}')
        self.pathidx += 1
        self._load_file()

    def _open_dir(self):
        dir_name = filedialog.askdirectory(initialdir='.', title="Select Directory Containing Invoices")
        if not dir_name or dir_name == '':
            return
        paths = os.listdir(dir_name)
        paths = [os.path.join(dir_name, path) for path in paths
                 if os.path.basename(path).split('.')[-1].lower() in ['pdf', 'jpg', 'png']]
        self.paths = self.paths[:self.pathidx + 1] + paths + self.paths[self.pathidx + 1:]
        if not self.paths:
            return
        self.pathidx += 1
        self._load_file()

    def _clear_queue(self):
        self.viewer.reset()
        self.logger.clear()
        self.image = None
        self.paths = list()
        self.pathidx = -1
        self.doc_label.configure(text="{} of {}".format(self.pathidx + 1, len(self.paths)))
        self.thread = None
        self.running = False

    def _help(self):
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        w, h = 600, 600
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        help_frame = Toplevel(self)
        help_frame.title("Help")
        help_frame.configure(width=w, height=h, bg=self.background, relief=SUNKEN)
        help_frame.geometry('%dx%d+%d+%d' % (w, h, x, y))
        help_frame.minsize(height=h, width=w)
        help_frame.maxsize(height=h, width=w)
        help_frame.rowconfigure(0, weight=1)
        help_frame.columnconfigure(0, weight=1)
        HelpBox(help_frame, width=w, height=h, bg=self.background, relief=SUNKEN).grid(row=0, column=0)

    @staticmethod
    def _fix_policy_error():
        policy_path = "/etc/ImageMagick-6/policy.xml"

        if not os.path.isfile(policy_path):
            policy_path = "/etc/ImageMagick/policy.xml"

        if not os.path.exists(policy_path):
            return False

        try:
            with open(policy_path, 'r') as policy_file:
                data = policy_file.readlines()
                new_data = []

                for line in data:
                    if 'MVG' in line:
                        line = '<!-- ' + line + ' -->'
                    elif 'PDF' in line:
                        line = '  <policy domain="coder" rights="read|write" pattern="PDF" />\n'
                    elif '</policymap>' in line:
                        new_data.append('  <policy domain="coder" rights="read|write" pattern="LABEL" />\n')
                    new_data.append(line)

                temp = tempfile.NamedTemporaryFile(mode='w', suffix='.xml')
                temp.writelines(new_data)
                subprocess.call(["sudo", "mv", temp.name, policy_path])
        except (IndexError, IOError, TypeError):
            return False
