#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Jan 13 15:25:52 2022

@author: Nacriema

Refs:

"""
from pathlib import Path

# Project and source files
PROJECT_PATH = Path(__file__).parent.parent.parent    # /VegetSeg_2
CONFIGS_PATH = PROJECT_PATH / 'configs'
DATASETS_PATH = PROJECT_PATH / 'datasets'
RAW_DATA_PATH = PROJECT_PATH / 'raw_data'
RESULTS_PATH = PROJECT_PATH / 'results'
MODELS_PATH = PROJECT_PATH / 'models'
