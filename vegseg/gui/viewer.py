#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 09 16:18:14 2022

@author: Nacriema

Refs:

"""
import PIL.ImageQt
import numpy as np
import pdfplumber
from tkinter import *
from tkinter import simpledialog, messagebox

from .. import FIELDS
from .custom_widgets import HoverButton, DisplayCanvas


class ImageViewer(Frame):

    def __init__(self, master=None, background='#303030', highlight='#558de8', **kw):
        Frame.__init__(self, master, **kw)
        self.background = background
        self.highlight = highlight

        self.image = None
        self.original_width = None
        self.original_height = None

        self.page = None
        self.total_pages = 0
        self.pageidx = 0
        self.scale = 1.0
        self.rotate = 0
        self.field_colors = {field: tuple(np.random.choice(range(256), size=3)) + (100,) for field in FIELDS.keys()}
        self._init_ui()

    def _init_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        page_tools = Frame(self, bg=self.background, bd=0, relief=SUNKEN)
        canvas_frame = Frame(self, bg=self.background, bd=1, relief=SUNKEN)

        canvas_frame.grid(row=1, column=0, sticky='news')
        page_tools.grid(row=0, column=0, sticky='news')

        # Display Canvas
        self.canvas = DisplayCanvas(canvas_frame, cursor='cross')
        self.canvas.pack(fill=BOTH, expand=True)

        # Page Tools
        page_tools.rowconfigure(0, weight=1)
        page_tools.columnconfigure(0, weight=1)
        page_tools.columnconfigure(1, weight=0)
        page_tools.columnconfigure(2, weight=2)
        page_tools.columnconfigure(3, weight=0)
        page_tools.columnconfigure(4, weight=1)

        nav_frame = Frame(page_tools, bg=self.background, bd=0, relief=SUNKEN)
        nav_frame.grid(row=0, column=1, sticky='ns')

        HoverButton(nav_frame, image_path=r'widgets/first.png',
                    command=self._first_page, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=LEFT, expand=True)
        HoverButton(nav_frame, image_path=r'widgets/prev.png',
                    command=self._prev_page, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=LEFT, expand=True)

        self.page_label = Label(nav_frame, bg=self.background, bd=0, fg='white', font=('Arial', 8),
                                text="Page {} of {}".format(self.pageidx, self.total_pages))
        self.page_label.pack(side=LEFT, expand=True)

        HoverButton(nav_frame, image_path=r'widgets/next.png',
                    command=self._next_page, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=LEFT, expand=True)
        HoverButton(nav_frame, image_path=r'widgets/last.png',
                    command=self._last_page, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=LEFT, expand=True)

        zoom_frame = Frame(page_tools, bg=self.background, bd=0, relief=SUNKEN)
        zoom_frame.grid(row=0, column=3, sticky='ns')

        HoverButton(zoom_frame, image_path=r'widgets/rotate.png',
                    command=self._rotate, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=RIGHT, expand=True)
        HoverButton(zoom_frame, image_path=r'widgets/fullscreen.png',
                    command=self._fit_to_screen, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=RIGHT, expand=True)

        self.zoom_label = Label(zoom_frame, bg=self.background, bd=0, fg='white', font=('Arial', 8),
                                text="Zoom {}%".format(int(self.scale * 100)))
        self.zoom_label.pack(side=RIGHT, expand=True)

        HoverButton(zoom_frame, image_path=r'widgets/zoomout.png',
                    command=self._zoom_out, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=RIGHT, expand=True)
        HoverButton(zoom_frame, image_path=r'widgets/zoomin.png',
                    command=self._zoom_in, bg=self.background, bd=0,
                    highlightthickness=0, activebackground=self.highlight).pack(side=RIGHT, expand=True)

    def reset(self):
        self.canvas.reset()

        self.image = None
        self.original_width = None
        self.original_height = None

        self.page = None
        self.total_pages = 0
        self.pageidx = 0
        self.scale = 1.0
        self.rotate = 0
        self.page_label.configure(text="Page {} of {}".format(self.pageidx, self.total_pages))
        self.zoom_label.configure(text="Zoom {}%".format(int(self.scale * 100)))

    def _zoom_in(self):
        if self.image is None or self.scale >= 2.5:
            return
        self.scale += 0.1
        self._update_page()

    def _zoom_out(self):
        if self.image is None or self.scale < 0.2:
            return
        self.scale -= 0.1
        self._update_page()

    def _fit_to_screen(self):
        if self.image is None or self.scale == 1.0:
            return
        self.scale = 1.0
        self._update_page()

    def _rotate(self):
        if self.image is None:
            return
        self.rotate = (self.rotate - 90) % 360
        self._update_page()

    def _next_page(self):
        if self.image is None or self.pageidx == self.total_pages:
            return
        self.pageidx += 1
        self._update_page()

    def _prev_page(self):
        if self.image is None or self.pageidx == 1:
            return
        self.pageidx -= 1
        self._update_page()

    def _last_page(self):
        if self.image is None or self.pageidx == self.total_pages:
            return
        self.pageidx = self.total_pages
        self._update_page()

    def _first_page(self):
        if self.image is None or self.pageidx == 1:
            return
        self.pageidx = 1
        self._update_page()

    def _update_page(self):
        # TODO: Update code here, I use the current image instead

        # page = self.image.pages[self.pageidx - 1]
        # self.page = page.to_image(resolution=int(self.scale * 80))
        # image = self.page.original.rotate(self.rotate)

        # NOTE:
        # Use thumbnail function to resize the image in order to keep aspect ratio,
        # use self.scale to adjust the size of this image, also reference with the original image ratio
        # Notice, here I just manipulate with the COPY of the original image, because the thumbnail is the INPLACE
        # function !!!

        print('Update !!!')
        print(f'Scale {self.scale}')
        image = self.image.copy()
        image.thumbnail((self.original_width * self.scale, self.original_height * self.scale))

        # This applies a global rotation to the reference original PIl image, the rotate function return a copy
        image = image.rotate(self.rotate, PIL.Image.NEAREST, expand=1)

        self.canvas.update_image(image)
        self.page_label.configure(text="Page {} of {}".format(self.pageidx, self.total_pages))
        self.zoom_label.configure(text="Zoom {}%".format(int(self.scale * 100)))

    def _reproject_bbox(self, bbox):
        bbox = [self.page.decimalize(x) for x in bbox]
        x0, y0, x1, y1 = bbox
        px0, py0 = self.page.page.bbox[:2]
        rx0, ry0 = self.page.root.bbox[:2]
        _x0 = (x0 / self.page.scale) - rx0 + px0
        _y0 = (y0 / self.page.scale) - ry0 + py0
        _x1 = (x1 / self.page.scale) - rx0 + px0
        _y1 = (y1 / self.page.scale) - ry0 + py0
        return [_x0, _y0, _x1, _y1]

    def display_image(self, image):
        """
        Use to display image in the canvas
        :param image: an instance of image
        :type image: PIL image
        :return: Update this later ...
        """
        self.clear()
        try:
            self.image = image
            self.original_width, self.original_height = image.size
            self.total_pages = 1
            self.pageidx = 1
            self.scale = 1.0
            self.rotate = 0
            self._update_page()
        except (IndexError, IOError, TypeError):
            messagebox.showerror("Error", "Could not display Image !")

    def search_text(self, text=None, fill=(0, 0, 255, 50)):
        if self.image is None:
            return

        if text is None:
            text = simpledialog.askstring('Search Text', 'Enter text to search:')
            if text == '' or text is None:
                return

        page = self.image.pages[self.pageidx - 1]
        image = page.to_image(resolution=int(self.scale * 80))
        words = [w for w in page.extract_words() if text.lower() in w['text'].lower()]

        if words:
            image.draw_rects(words, fill=fill, stroke=(0, 0, 0, 200))
            image = image.annotated.rotate(self.rotate)
            self.canvas.update_image(image)

    def label(self, labels=None):
        if self.image is None or labels is None:
            return

        page = self.image.pages[self.pageidx - 1]
        image = page.to_image(resolution=int(self.scale * 80))

        for key in labels.keys():
            if labels[key]:
                words = [w for w in page.extract_words() if labels[key].strip().lower() in w['text'].lower()]
                if words:
                    image.draw_rects(words, fill=self.field_colors[key], stroke=(0, 0, 0, 200))

        image = image.annotated.rotate(self.rotate)
        self.canvas.update_image(image)

    def extract_text(self):
        if self.image is None:
            return
        rect = self.canvas.get_rect()
        if rect is None:
            return
        self.clear()
        rect = self._reproject_bbox(rect)
        page = self.image.pages[self.pageidx - 1]
        words = page.extract_words()
        min_x = 1000000
        bbox = None
        for word in words:
            diff = abs(float(word['x0'] - rect[0])) + abs(float(word['top'] - rect[1])) \
                   + abs(float(word['x1'] - rect[2])) + abs(float(word['bottom'] - rect[3]))
            if diff < min_x:
                min_x = diff
                bbox = word

        if bbox is None:
            messagebox.showerror("Error", "Could not extract text! Try after running OCR on this invoice.")
            return

        image = page.to_image(resolution=int(self.scale * 80))
        image.draw_rect(bbox)
        image = image.annotated.rotate(self.rotate)
        self.canvas.update_image(image)
        simpledialog.askstring("Extract Text", "Text Extracted:", initialvalue=bbox['text'])

    def clear(self):
        if self.image is None:
            return
        self.canvas.clear()
        self._update_page()
