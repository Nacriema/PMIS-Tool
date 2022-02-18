#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Feb 14 15:00:43 2022

@author: Nacriema

Refs:

"""
from .utils import *


def process(img_rgb, v1_left, v1_right, v2_left, v2_right, corres_point_left,
            corres_point_right, pylon_left, pylon_right):
    v1_left_0 = tuple(v1_left[:2])
    v1_left_1 = tuple(v1_left[2:])

    v1_right_0 = tuple(v1_right[:2])
    v1_right_1 = tuple(v1_right[2:])

    v2_left_0 = tuple(v2_left[:2])
    v2_left_1 = tuple(v2_left[2:])

    v2_right_0 = tuple(v2_right[:2])
    v2_right_1 = tuple(v2_right[2:])

    img_width, img_height = img_rgb.size
    pp_x = int(img_width / 2.0)
    pp_y = int(img_height / 2.0)

    v1_left_line = hc_line_from_2_point(point_to_hc_coord(v1_left_0), point_to_hc_coord(v1_left_1))
    v1_right_line = hc_line_from_2_point(point_to_hc_coord(v1_right_0), point_to_hc_coord(v1_right_1))

    v2_left_line = hc_line_from_2_point(point_to_hc_coord(v2_left_0), point_to_hc_coord(v2_left_1))
    v2_right_line = hc_line_from_2_point(point_to_hc_coord(v2_right_0), point_to_hc_coord(v2_right_1))

    v1 = hc_point_from_2_line(v1_left_line, v1_right_line)
    v2 = hc_point_from_2_line(v2_left_line, v2_right_line)

    v1_left_top, v1_left_bot, _, _ = get_intercept_point(v1_left_line, img_width, img_height)
    v1_right_top, v1_right_bot, _, _ = get_intercept_point(v1_right_line, img_width, img_height)

    v2_left_top, v2_left_bot, _, _ = get_intercept_point(v2_left_line, img_width, img_height)
    v2_right_top, v2_right_bot, _, _ = get_intercept_point(v2_right_line, img_width, img_height)

    height_line_1 = hc_line_from_2_point(v1, point_to_hc_coord((pp_x, pp_y)))
    perpendicular_height_line_1 = hc_point_from_line_and_point_2(height_line_1, v2)

    height_line_2 = hc_line_from_2_point(v2, point_to_hc_coord((pp_x, pp_y)))
    perpendicular_height_line_2 = hc_point_from_line_and_point_2(height_line_2, v1)

    v3 = hc_point_from_2_line(perpendicular_height_line_1, perpendicular_height_line_2)
    # TODO: Here we have the v1, v2 as well v3 points
    # Compute the scaling factor for each
    lambda_1_square = 1.0 * triangle_area_heron(point_hc_to_point(v3), point_hc_to_point(v2), (pp_x, pp_y)) / \
                      triangle_area_heron(point_hc_to_point(v1), point_hc_to_point(v2), point_hc_to_point(v3))
    lambda_2_square = 1.0 * triangle_area_heron(point_hc_to_point(v1), point_hc_to_point(v3), (pp_x, pp_y)) / \
                      triangle_area_heron(point_hc_to_point(v1), point_hc_to_point(v2), point_hc_to_point(v3))
    lambda_3_square = 1.0 * triangle_area_heron(point_hc_to_point(v1), point_hc_to_point(v2), (pp_x, pp_y)) / \
                      triangle_area_heron(point_hc_to_point(v1), point_hc_to_point(v2), point_hc_to_point(v3))

    # assert lambda_3_square <= lambda_1_square <= lambda_2_square

    # TODO: Nice we have the lambda, Calculate te focal length, in the original paper of Cipolla
    #  (x1 - x0) * (x2 - x0) + alpha**2 = 0
    v1_normal = np.array(list(point_hc_to_point(v1)))
    v2_normal = np.array(list(point_hc_to_point(v2)))
    v3_normal = np.array(list(point_hc_to_point(v3)))
    pp_normal = np.array([pp_x, pp_y])

    # focal_square = - np.dot((v1_normal - pp_normal), (v2_normal - pp_normal))
    focal_square = np.abs(np.dot((v1_normal - pp_normal), (v2_normal - pp_normal)))
    print(f'Focal square = {focal_square}')

    ld_1 = -sqrt(lambda_1_square)
    ld_2 = sqrt(lambda_2_square)
    ld_3 = sqrt(lambda_3_square)

    # TODO: Change here, I think focal is the number < 0
    f = -sqrt(focal_square)
    R_wc = np.array([[ld_1 / f * (v1_normal[0] - pp_normal[0]), ld_2 / f * (v2_normal[0] - pp_normal[0]),
                      ld_3 / f * (v3_normal[0] - pp_normal[0])],
                     [ld_1 / f * (v1_normal[1] - pp_normal[1]), ld_2 / f * (v2_normal[1] - pp_normal[1]),
                      ld_3 / f * (v3_normal[1] - pp_normal[1])],
                     [ld_1, ld_2, ld_3]])
    R_cw = inv(R_wc)
    C_d_left = inv(R_wc) @ np.array([corres_point_left[0] - pp_normal[0], corres_point_left[1] - pp_normal[1], f])
    C_d_right = inv(R_wc) @ np.array([corres_point_right[0] - pp_normal[0], corres_point_right[1] - pp_normal[1], f])
    camera_position = intersection_of_two_3d_line(pylon_left, pylon_right, C_d_left, C_d_right)

    result = {
        "Principal point": [pp_x, pp_y],
        "Vanishing point 1": v1.tolist(),
        "Vanishing point 2": v2.tolist(),
        "Vanishing point 3": v3.tolist(),
        "Lambda 1 square": lambda_1_square,
        "Lambda 2 square": lambda_2_square,
        "Lambda 3 square": lambda_3_square,
        "Focal": sqrt(focal_square),
        "Rotation matrix R_wc": R_wc.tolist(),
        "Rotation matrix R_cw": R_cw.tolist(),
        "C_d_left": C_d_left.tolist(),
        "C_d_right": C_d_right.tolist(),
        "Camera position": camera_position.tolist()
    }
    return result, pp_x, pp_y, v1, v2, v3, v1_left_0, v1_left_bot, v1_right_0, v1_right_bot, v2_left_bot, v2_right_bot


def visualization(img_rgb, pp_x, pp_y, v1, v2, v3, v1_left_0, v1_left_bot, v1_right_0, v1_right_bot, v2_left_bot,
                  v2_right_bot, corres_point_left, corres_point_right):
    img_ = ImageDraw.Draw(img_rgb)
    img_.ellipse((pp_x - 4, pp_y - 4, pp_x + 4, pp_y + 4), fill='blue')

    img_.ellipse((int(v2[0]) - 2, int(v2[1]) - 2, int(v2[0]) + 2, int(v2[1]) + 2), fill='cyan')
    img_.line([v1_left_0, point_hc_to_point(v1_left_bot)], fill='yellow', width=2)
    img_.line([v1_right_0, point_hc_to_point(v1_right_bot)], fill='yellow', width=2)

    img_.line([point_hc_to_point(v2), point_hc_to_point(v2_left_bot)], fill='yellow', width=2)
    img_.line([point_hc_to_point(v2), point_hc_to_point(v2_right_bot)], fill='yellow', width=2)

    img_.line([point_hc_to_point(v1), (pp_x, pp_y)], fill='#e803fc', width=3)
    img_.line([point_hc_to_point(v2), (pp_x, pp_y)], fill='#e803fc', width=3)
    img_.line([point_hc_to_point(v3), (pp_x, pp_y)], fill='#e803fc', width=3)

    img_.line([point_hc_to_point(v3), point_hc_to_point(v1)], fill='cyan', width=3)
    img_.line([point_hc_to_point(v3), point_hc_to_point(v2)], fill='cyan', width=3)
    img_.line([point_hc_to_point(v1), point_hc_to_point(v2)], fill='cyan', width=3)

    img_.ellipse(
        [corres_point_left[0] - 2, corres_point_left[1] - 2, corres_point_left[0] + 2, corres_point_left[1] + 2],
        fill='#0bfc03')
    img_.ellipse(
        [corres_point_right[0] - 2, corres_point_right[1] - 2, corres_point_right[0] + 2, corres_point_right[1] + 2],
        fill='#0bfc03')
    # return img_rgb
