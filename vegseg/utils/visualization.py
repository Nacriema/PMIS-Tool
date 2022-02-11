#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Jan 15 16:03:02 2022

@author: Nacriema

Refs:

"""
import matplotlib.pyplot as plt
from torchvision.utils import make_grid
import pandas as pd


def show_images(images, nmax=64):
    """ Tool to debug Dataloader.
    See: https://towardsdatascience.com/beginners-guide-to-loading-image-data-with-pytorch-289c60b7afec

    Args:
        images:
        nmax:

    Returns:

    """
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.imshow(make_grid((images.detach()[:nmax]), nrow=2).permute(1, 2, 0))


def show_batch(dl, nmax=64):
    for images in dl:
        # Show input images
        show_images(images[0], nmax)
        plt.show()
        # Show ground truth image, just can show when batch size is 1
        # show_images(images[1], nmax)
        # plt.show()
        break


def show_train_val_loss(train_file, val_file):
    """

    Args:
        train_file:
        val_file:

    Returns:

    """
    plt.figure(figsize=(8, 6), dpi=200)
    train_log = pd.read_csv(train_file, sep="\t")
    val_log = pd.read_csv(val_file, sep='\t')
    merge_log = pd.merge(train_log, val_log, on='iteration', how='inner')
    iteration = merge_log['iteration']
    train_loss = merge_log['train_loss']
    val_loss = merge_log['val_loss']
    plt.plot(iteration, train_loss, label='train_loss')
    plt.plot(iteration, val_loss, label='val_loss')
    plt.legend()
    plt.xlabel('Iterations')
    plt.ylabel('Error')
    plt.title('Training and Validation Loss Curve')
    plt.show()
