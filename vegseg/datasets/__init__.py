#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Jan 13 15:45:42 2022

@author: Nacriema

Refs:

"""
from .segmentation import AbstractSegDataset


def get_dataset(dataset_name):
    class Dataset(AbstractSegDataset):
        name = dataset_name

    return Dataset
