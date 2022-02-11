#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 11 12:17:25 2022

@author: Nacriema

Refs:

This is the GUI part for Segmentation task, I placed here to break the code in segmentor into small pieces

Make this is TOO COMPLICATED !!!! so I stop this and move to the first idea.

"""
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from .custom_widgets import HoverButton, MenuBox, Logger, StoppableThread
from .. import FIELDS
import os

from PIL import Image

# TODO: Import things for process the images
import torch
from ..models import load_model_from_path
from ..utils import coerce_to_path_and_check_exist
from ..utils.path import MODELS_PATH
from ..utils.constant import MODEL_FILE, LABEL_TO_COLOR_MAPPING
from ..utils.image import LabeledArray2Image
import numpy as np


class SegmentationTab(Frame):
    def __init__(self, master=None, segmentor=None, background='#f7f7f7', checkbox_color='#f7f7f7', border_color='#c7c7c7', **kw):
        Frame.__init__(self, master, **kw)

        # Some init properties
        self.background = background
        self.checkbox_color = checkbox_color
        self.border_color = border_color

        self.checkboxes = {}
        self.running = False
        self.thread = None

        # TODO: HANDLE self.paths values through main scene to child
        self.segmentor = segmentor  # This is the instance of Class Segmentor, use this to access the properties as well as the method in that instance

        self._init_ui()

    def _init_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # Segmentation Button
        self.start_button = HoverButton(self,
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

        field_frame = ttk.LabelFrame(master=self,
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

    def _extract(self):
        path = self.segmentor.paths[self.segmentor.pathidx]

        self.segmentor.logger.clear()
        self.segmentor.logger.log("Segmenting from '{}'...\n".format(path))
        self.segmentor.logger.log("Please wait ...")

        temp = None
        # TODO: Add model for processing here !!!

        if path.split('.')[-1].lower() in ['jpg', 'png', 'jpeg']:
            image = Image.open(path)

            # Start to loading the pretrained model here
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            TAG = 'Full_data_Soft_Dice_Loss_V2'
            model_path = coerce_to_path_and_check_exist(MODELS_PATH / TAG / MODEL_FILE)

            self.segmentor.logger.log("Loading model ...")
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

            # Retrieve good color mapping and transform to image
            restricted_colors = [LABEL_TO_COLOR_MAPPING[l] for l in restricted_labels]
            label_idx_color_mapping = {restricted_labels.index(l) + 1: c for l, c in
                                       zip(restricted_labels, restricted_colors)}
            pred_img = LabeledArray2Image.convert(pred, label_idx_color_mapping)
            # Blend predictions with original image
            mask = Image.fromarray((np.array(pred_img) == (0, 0, 0)).all(axis=-1).astype(np.uint8) * 127 + 128)
            blend_img = Image.composite(image, pred_img, mask)

            # TODO: Save the blend image as the result and then add to same image folder and path then update the index
            #  and view it !

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
