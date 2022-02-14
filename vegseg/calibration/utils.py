#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 14 15:01:01 2022

@author: Nacriema

Refs:

"""
import simplejson
from matplotlib import pyplot as plt
from PIL import Image, ImageDraw
import numpy as np
from math import sqrt
from numpy.linalg import inv, norm

# Function in HC coordinate
def point_to_hc_coord(point):
    return np.array([point[0], point[1], 1.0])


def point_hc_to_point(hc_point):
    point = hc_point / hc_point[-1]
    return point[0], point[1]


def hc_line_from_2_point(hc_point_0, hc_point_1):
    return np.cross(hc_point_0, hc_point_1)


def hc_point_from_2_line(hc_line_0, hc_line_1):
    point = np.cross(hc_line_0, hc_line_1)
    point = point / point[-1]
    return point


# TODO: Must rename this function later, this return the line passing through a point and // to the another line
def hc_line_from_line_and_point(hc_line, hc_point):
    hc_line_ = np.array([hc_line[0], hc_line[1], 0])
    hc_point = hc_point / hc_point[-1]
    hc_line_rs = np.array([hc_line[0], hc_line[1], -np.dot(hc_line_, hc_point)])


# TODO: Make another function find the line when given a point passing through and perpendicular to the another line
def hc_point_from_line_and_point_2(hc_line, hc_point):
    hc_line_ = np.array([-hc_line[1], hc_line[0], 0])
    hc_point = hc_point / hc_point[-1]
    hc_line_rs = np.array([-hc_line[1], hc_line[0], -np.dot(hc_line_, hc_point)])
    return hc_line_rs


def get_intercept_point(hc_line, width, height, type=0):
    """Compute intercept point of hc line with the x and y boundary of image"""
    top = hc_point_from_2_line(hc_line, np.array([0, 1, 0]))  # y = 0
    bot = hc_point_from_2_line(hc_line, np.array([0, 1, -height]))  # y = height
    left = hc_point_from_2_line(hc_line, np.array([1, 0, 0]))  # x = 0
    right = hc_point_from_2_line(hc_line, np.array([1, 0, -width]))  # x = width
    return top, bot, left, right


def euclide_len_by_two_point(pointA, pointB):
    return sqrt((pointA[0] - pointB[0]) ** 2 + (pointA[1] - pointB[1]) ** 2)


# TODO: Heron's formula to calculate area of triangle
def triangle_area_heron(pointA, pointB, pointC):
    AB = euclide_len_by_two_point(pointA, pointB)
    BC = euclide_len_by_two_point(pointB, pointC)
    AC = euclide_len_by_two_point(pointA, pointC)
    S = (AB + BC + AC) / 2.0
    return sqrt(S * (S - AB) * (S - BC) * (S - AC))


def intersection_of_two_3d_line(point_C, point_D, e, f):
    """
    :param point_C:
    :param point_D:
    :param e: direction vector of point C
    :param f: direction vector of point D
    :return:
    """
    # See this link: https://math.stackexchange.com/questions/270767/find-intersection-of-two-3d-lines
    point_C = np.array(list(point_C))
    point_D = np.array(list(point_D))
    g = point_D - point_C
    f_cross_g = np.cross(f, g)
    f_cross_e = np.cross(f, e)
    check_same_direction = np.dot(f_cross_g, f_cross_e)
    if check_same_direction > 0:
        point_intersect = point_C + norm(f_cross_g) / norm(f_cross_e) * e
    else:
        point_intersect = point_C - norm(f_cross_g) / norm(f_cross_e) * e
    return point_intersect