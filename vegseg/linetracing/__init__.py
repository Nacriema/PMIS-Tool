#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 17 18:08:45 2022

@author: Nacriema

Refs:

"""
from .utils import *


def compute_angle(line):
    """
    Return angle in Degree
    :param line:
    :return:
    """
    # Given line in list: user define this
    temp = np.abs(line[3] - line[1]) / np.abs(line[2] - line[0])
    return np.rad2deg(np.arctan(temp))


def process(image_rgb, init_points):
    """

    :param image_rgb: Image object returned by scipy.imread
    :param init_points:
    :return:
    """
    image = rgb2gray(image_rgb)
    x_grad = partial_dev_along_x_2(image)
    y_grad = partial_dev_along_y_2(image)

    '''
        Compute all gradients needed 
        Grad 1, 2, 3 stand for left side 
        Grad 4, 5, 6 stand for middle 
        Grad 7, 8, 9 stand for right side
        '''
    grad_1 = create_directional_image_derivatives(theta=(15 / 150) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)
    grad_2 = create_directional_image_derivatives(theta=(45 / 180) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)
    grad_3 = create_directional_image_derivatives(theta=(70 / 180) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)

    grad_4 = grad_3
    # grad_4 = create_directional_image_derivatives(theta=(15 / 150) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)
    grad_5 = create_directional_image_derivatives(theta=(90 / 180) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)
    grad_6 = create_directional_image_derivatives(theta=(105 / 180) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)

    grad_7 = create_directional_image_derivatives(theta=(105 / 150) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)
    grad_8 = create_directional_image_derivatives(theta=(135 / 180) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)
    grad_9 = create_directional_image_derivatives(theta=(165 / 180) * (2 * np.pi), grad_x=x_grad, grad_y=y_grad)

    grads_for_direction_1 = [grad_1, grad_2, grad_3]
    grads_for_direction_2 = [grad_4, grad_5, grad_6]
    grads_for_direction_3 = [grad_7, grad_8, grad_9]
    list_grads = [grads_for_direction_1, grads_for_direction_2, grads_for_direction_3]

    result_sets_curve_fit = []
    result_sets_raw = []

    # Type 0: / shape, 1: | shape, 2: \ shape
    for item in init_points:
        # TODO: USING V4
        result_set = line_tracing_v4(init_point=item[0], end_point=item[2], grads=list_grads[item[1]], type=item[1],
                                     k0=item[3])
        result_sets_raw.extend(result_set)
        # TODO: BUGS here, need feed type value !??? I disable this, Because this may cause interruption !!!
        # result_sets_curve_fit.extend(use_curve_fitting(result_set, type=0))
    # im_with_result_sets_curve_fit = create_image_with_mask(image_rgb, result_sets_curve_fit)
    im_with_result_sets_raw = create_image_with_mask(image_rgb, result_sets_raw, color='blue')
    return result_sets_raw, result_sets_curve_fit, im_with_result_sets_raw

