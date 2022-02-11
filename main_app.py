#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 09 16:02:15 2022

@author: Nacriema

Refs:

This is the entrance of the application
"""
from tkinter import Tk
from vegseg.gui.segmentor import Segmentor


def main():
    root = Tk()

    # Set the theme
    root.tk.call("source", "sun-valley.tcl")
    root.tk.call("set_theme", "light")

    Segmentor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
