#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 17 18:08:58 2022

@author: Nacriema

Refs:

"""
import numpy as np
import math
import scipy.ndimage as ndi
import matplotlib.pyplot as plt
from skimage import img_as_float
from skimage.io import imread, imsave
from skimage.color import rgb2gray
from math import ceil
from scipy.optimize import curve_fit


# TODO: Define 3 directions here
# CONSTANT
D = [[(0, 1), (-1, 1), (-1, 0)],
     [(-1, 1), (-1, 0), (-1, -1)],
     [(-1, 0), (-1, -1), (0, -1)]]


def imshow_all(*images, titles=None, cmap=None, ncols=3):
    images = [img_as_float(img) for img in images]
    if titles is None:
        titles = [''] * len(images)
    vmin = min(map(np.min, images))
    vmax = max(map(np.max, images))
    height = 5
    width = height * len(images)
    fig, axes = plt.subplots(nrows=ceil(len(images) / ncols), ncols=ncols, figsize=(width, height), dpi=96)
    for ax, img, label in zip(axes.ravel(), images, titles):
        ax.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_title(label)


def partial_dev_along_x_2(image):
    horizontal_kernel = np.array([
        [-1, 0, 1]
    ])
    gradient_horizontal = ndi.correlate(image.astype(float),
                                        horizontal_kernel)
    return gradient_horizontal


def partial_dev_along_y_2(image):
    vertical_kernel = np.array([
        [-1],
        [0],
        [1],
    ])
    gradient_vertical = ndi.correlate(image.astype(float),
                                      vertical_kernel)
    return gradient_vertical


def create_directional_image_derivatives(theta, grad_x, grad_y):
    """
    Compute the directional derivative with given the theta direction
    In matrix form, at the (0, 0) point for example:
                                   [cos(theta)
    [grad_x(0, 0) grad_y(0, 0)]. *
                                    sin(theta)]
    NOTICE: In this formula the coordinate as follow:
    ^y
    |   /
    |  /
    | /
    |/ theta
    . - - - - - ->x
     So when apply this function in image, give my result as the inversion of grad_45 and grad_neg_45, use it cautiously
     Just add the negative sign to the grad_y when calculate to fix it
    :param theta:
    :param grad_x:
    :param grad_y:
    :return: np array with shape like grad_x
    """
    return grad_x * np.cos(theta) - grad_y * np.sin(theta)


def direction_constrain_v4(init_h, init_w, curr_h, curr_w, type=0, k0=0.):
    """
    Upgrade version for direction_constrain, specified the type to detect 3 directions of lines, these need more consider
    :param init_h:
    :param init_w:
    :param curr_h:
    :param curr_w:
    :param type:
    :param k0: In degree
    :return:
    """
    # TODO: Ops, need more test here Special case:
    if curr_w == init_w:
        return True
    else:
        # Calculate slope k
        # TODO: NEED MORE CONSIDERATION, WELL THIS IS ALSO IMPACT WHEN CHOOSING SLOPE
        k = (curr_h - init_h) / math.fabs(curr_w - init_w)
        # TODO: NOT CONSIDER TYPE ANYMORE, INSTEAD WE USE THE THRESHOLD VALUE (IN RADIAN)
        # np.arctan(k) # negative sign
        # (-k0 / 180. * np.pi) # negative sign

        # TODO: WHEN USER POINT OUT THE INIT POINT, MAY BE IT DOES NOT ACCURATE AND TAKE A FEW INITIAL PIXELS FOR THE \
        #  ALGORITHM TO TRACE THE RIGHT PATH
        threshold = 2. / 180 * np.pi   # threshold is 3 degree
        print(f'k = {k}')
        print(math.fabs(np.arctan(k) - (-k0 / 180. * np.pi)) * 180 / np.pi)
        # TODO: FOR FIRST FEW INITIAL PIXEL, NO NEED CONSTRAIN
        # May be we should change the init_w, init_h when the
        if math.fabs(curr_w - init_w) < 20:
            return True
        if math.fabs(np.arctan(k) - (-k0 / 180. * np.pi)) < threshold:
            return True
        return False


def choose_interest_point_by_slope_v4(init_h, init_w, curr_h, curr_w, init_set, type=0, k0=0.):
    """
    THIS FUNCTION CREATED TO WORK WITH DIRECTION CONSTRAIN V3
    Choose the interest point base on the slopes constrain
    :param init_h:
    :param init_w:
    :param curr_h:
    :param curr_w:
    :param init_set:
    :param k0:
    :return:
    """
    # Special case: Handle the special cases, may be we don't care too much about them
    # TODO: Adjust here, need to fix like this in the original version
    # TODO: These 3 slope need to be consideration, may be we can feed the direction into the array

    watch_list_slopes = []
    k0 = -k0 / 180. * np.pi
    for i in range(3):
        slope = (curr_h + D[type][i][0] - init_h) / math.fabs(curr_w + D[type][i][1] - init_w) if (curr_w + D[type][i][
            1] - init_w) != 0 else math.inf
        print(f'k0 = {k0}')
        print(f'Slope - k0 = {abs(slope - np.tan(k0))}')
        watch_list_slopes.append(abs(slope - np.tan(k0)))
    min_index = watch_list_slopes.index(min(watch_list_slopes))
    init_set.append((curr_h + D[type][min_index][0], curr_w + D[type][min_index][1]))
    return init_set


# TODO: Modified here, for checking
def check_valid_v4(point_index, image_arr, height_thresh):
    # return 0 <= point_index[0] < image_arr.shape[0] and 0 <= point_index[1] < image_arr.shape[1]
    return height_thresh <= point_index[0] < image_arr.shape[0] and 0 <= point_index[1] < image_arr.shape[1]


def line_tracing_v4(init_point, end_point, grads, type=0, k0=0.):
    init_set = [init_point]
    init_h, init_w = init_point
    end_h, end_w = end_point
    result_set = []
    # Give the stop condition here
    while init_set:
        current_point = init_set.pop()
        # print(current_point)
        # Check reached image boundary here, change check valid also
        if check_valid_v4(current_point, grads[0], height_thresh=end_h):
            result_set.append(current_point)
            curr_h, curr_w = current_point
            watch_list_grads = [grads[0][curr_h, curr_w], grads[1][curr_h, curr_w], grads[2][curr_h, curr_w]]
            min_index = watch_list_grads.index(min(watch_list_grads))
            # TODO: Modified for testing, change to not using constrain
            if direction_constrain_v4(init_h=init_h, init_w=init_w, curr_h=curr_h + D[type][min_index][0],
                                      curr_w=curr_w + D[type][min_index][1], type=type, k0=k0):
                print("Choose by direction")
                init_set.append((curr_h + D[type][min_index][0], curr_w + D[type][min_index][1]))
            else:
                print("Choose by slope")
                # TODO: Here we need to take into account, if the point reached at the end of the line, we must change
                #  the k0 of the slope so that it could follow the "right direction" I think this is not good may be we
                #  should stop the tracing at the end of the line, use approximate to fill the rest, see the line spread
                #  out in which direction
                if math.fabs(init_h - end_h) > math.fabs(init_w - end_w) and math.fabs(curr_h - init_h) / math.fabs(end_h - init_h) > 0.9:
                    print(f'GO TO HERE !!!!')
                    # init_set = choose_interest_point_by_slope_v3(init_h=end_h, init_w=end_w, curr_h=curr_h,
                    #                                          curr_w=curr_w
                    #                                          , init_set=init_set, type=type, k0=60)
                    break
                elif math.fabs(init_h - end_h) <= math.fabs(init_w - end_w) and math.fabs(curr_w - init_w) / math.fabs(end_w - init_w) > 0.9:
                    break
                else:
                    init_set = choose_interest_point_by_slope_v4(init_h=init_h, init_w=init_w, curr_h=curr_h,
                                                             curr_w=curr_w
                                                             , init_set=init_set, type=type, k0=k0)
    return result_set


def generate_mask_im(source_im, result_set):
    """
    Given image and result set, reconstruct the mask image
    :param source_im:
    :param result_set:
    :return: mask image
    """
    # print('=============================s')
    result_images = np.zeros_like(source_im)
    for item in result_set:
        result_images[item[0], item[1]] = 1
    return result_images


# TODO: Tool to create ADJUSTED IMAGE
def objective(w, a, b, c):
    return a * w + b * w ** 2 + c


def use_curve_fitting(result_set, type=0):
    """
    Use built-in function of scipy for apply curve fitting step
    :param result_set:
    :return:
    """
    w = np.array([i[1] for i in result_set])
    h = np.array([i[0] for i in result_set])
    if type == 1:
        popt, _ = curve_fit(objective, h, w)
        a, b, c = popt
        h_line = np.arange(min(h), max(h), 1)
        w_line = objective(h_line, a, b, c)
        w_line = np.around(w_line).astype(int)
        result = [(h_line[i], w_line[i]) for i in range(len(h_line))]
    else:
        popt, _ = curve_fit(objective, w, h)
        a, b, c = popt
        w_line = np.arange(min(w), max(w), 1)
        h_line = objective(w_line, a, b, c)
        h_line = np.around(h_line).astype(int)
        result = [(h_line[i], w_line[i]) for i in range(len(w_line))]
    print("===================")
    print(result)
    return result


def create_image_with_mask(image, result_set, color='red'):
    """
    Plot the detected line on the original image, default color is red
    :param image:
    :param result_set: contains x, y coordinate of
    :return: image with detected line
    """
    image_ = np.copy(image)
    for item in result_set:
        if color == 'red':
            try:
                image_[item[0], item[1]] = np.array([255, 0, 0])
            except IndexError:
                pass
        else:
            try:
                image_[item[0], item[1]] = np.array([0, 0, 255])
            except IndexError:
                pass
    return image_



