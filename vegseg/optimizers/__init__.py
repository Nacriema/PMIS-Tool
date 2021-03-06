#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Jan 13 14:47:44 2022

@author: Nacriema

Refs:

"""
from torch.optim import SGD, Adam, ASGD, Adamax, Adadelta, Adagrad, RMSprop


def get_optimizer(name):
    if name is None:
        name = 'sgd'
    return {
        "sgd": SGD,
        "adam": Adam,
        "asgd": ASGD,
        "adamax": Adamax,
        "adadelta": Adadelta,
        "adagrad": Adagrad,
        "rmsprop": RMSprop,
    }[name]
