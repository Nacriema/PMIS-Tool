#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 09 16:05:01 2022

@author: Nacriema

Refs:

"""

# TODO: These field should be removed or change later

# FIELD_TYPES = {
#     "general": 0,
#     "optional": 1,
#     "amount": 2,
#     "date": 3
# }

FIELD_TYPES = {
    "void": 0,
    "vegetation_misc": 1,
    "tree": 2,
}

FIELDS = dict()

FIELDS["Background"] = FIELD_TYPES["void"]
FIELDS["Vegetation Misc"] = FIELD_TYPES["vegetation_misc"]

FIELDS["Tree"] = FIELD_TYPES["tree"]
