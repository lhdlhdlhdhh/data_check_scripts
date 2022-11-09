#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 13 15:26:42 2021

@author: jiaqi
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time

import gps_converter
from plotting_every_30s.modify_yaw_angle import modify_yaw_angle_from_ISO_8855

topics = [
    {'topic_name': 'East velocity (m/s)', 'yticks_min': -55, 'yticks_max': 55, 'ylim_min': -60, 'ylim_max': 60},
    {'topic_name': 'North velocity (m/s)', 'yticks_min': -55, 'yticks_max': 55, 'ylim_min': -60, 'ylim_max': 60},
    {'topic_name': 'Vertical velocity (m/s)', 'yticks_min': -55, 'yticks_max': 55, 'ylim_min': -60, 'ylim_max': 60},
    {'topic_name': 'Heading (deg)', 'yticks_min': -720, 'yticks_max': 720, 'ylim_min': -730, 'ylim_max': 730},
    {'topic_name': 'yaw velocity(deg/s)', 'yticks_min': -0.03, 'yticks_max': 0.03, 'ylim_min': -0.03, 'ylim_max': 0.03},
    {'topic_name': 'position type', 'yticks_min': 0, 'yticks_max': 50, 'ylim_min': 0, 'ylim_max': 55},
]
can_topics = [
    {'topic_name': 'brakeStatus_out', 'yticks_min': 0, 'yticks_max': 1, 'ylim_min': -1, 'ylim_max': 2},
    {'topic_name': 'gas_pedal', 'yticks_min': 0, 'yticks_max': 90, 'ylim_min': -10, 'ylim_max': 100},
    {'topic_name': 'steering_angle', 'yticks_min': -700, 'yticks_max': 700, 'ylim_min': -750, 'ylim_max': 750},
]


def return_local_time(unix_time):
    return time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(unix_time))


def plot_30s(df_oxts, output_path, topic_name, topic_range, can_df=None):
    df_oxts = df_oxts.dropna(subset=['Latitude (deg)'])
    df_oxts = df_oxts.dropna(subset=['Longitude (deg)'])
    df_oxts = df_oxts.dropna(subset=['East velocity (m/s)'])
    df_oxts = df_oxts.dropna(subset=['North velocity (m/s)'])

    timestamp_oxts = np.array(df_oxts['Time (GPS ns)']) / 1e9
    # timestamp_oxts = np.array(df_oxts['Time (GPS ns)']) / 1e9  + 315964800 - 18
    f = int(len(timestamp_oxts) / (timestamp_oxts[-1] - timestamp_oxts[0]))

    lat = np.array(df_oxts['Latitude (deg)'])
    long = np.array(df_oxts['Longitude (deg)'])
    h = np.array(df_oxts['Altitude (m)'])

    # %%
    seg_speed_value = None
    if can_df is None:
        seg_value = np.array(df_oxts[topic_name])
        if topic_name == 'Heading (deg)':
            seg_value = (seg_value * 180 / np.pi)
            seg_value = modify_yaw_angle_from_ISO_8855(seg_value)
            # topic_range['yticks_min'], topic_range['yticks_max']
    else:
        df_oxts['Time (GPS ns)'] = df_oxts['Time (GPS ns)'].astype('int64')
        can_df = pd.merge_asof(df_oxts, can_df, left_on='Time (GPS ns)', right_on='timestamp', direction='forward')
        seg_value = np.array(can_df[topic_name])
        if topic_name in ['brakeStatus_out', 'gas_pedal']:
            speed_df = df_oxts['East velocity (m/s)'] ** 2 + df_oxts['North velocity (m/s)'] ** 2
            seg_speed_value = np.sqrt(np.array(speed_df))
    plot_name2 = topic_name  # name for the second plot

    # %% gps convert
    x, y, z = gps_converter.gps2ecef(lat, long, h)
    x_ref, y_ref, z_ref = x[0], y[0], z[0]
    lat0, long0 = lat[0], long[0]
    xEast, yNorth, zUp = gps_converter.ecef2enu(x, y, z, x_ref, y_ref, z_ref, lat0, long0)
    trajectory = np.stack([xEast, yNorth, lat, long])
    # trajectory = np.stack([xEast, yNorth, lat, long])

    # %% slice the road for every 30 seconds
    times = timestamp_oxts - timestamp_oxts[0]
    times_trans = timestamp_oxts - timestamp_oxts[0]
    interval = 30  # every 30 seconds
    index = np.searchsorted(times, np.arange(0, int(times[-1]), interval), side='left', sorter=None)

    seg_value_slice = []
    trajectory_whole = []
    max_yaw = 0
    for i in range(len(index) - 1):
        if index[i + 1] - index[i]:
            current_trajectory = trajectory[:, index[i]:index[i + 1]]
            trajectory_whole.append(current_trajectory)
            seg_value_slice_data = [times_trans[index[i]:index[i + 1]],
                                    seg_value[index[i]:index[i + 1]],
                                    timestamp_oxts[index[i]:index[i + 1]]]
            if seg_speed_value is not None:
                seg_value_slice_data.append(seg_speed_value[index[i]:index[i + 1]])
            seg_value_slice.append(seg_value_slice_data)
            # max_yaw = max(max_yaw, max(seg_value_slice[-1][1])-min(seg_value_slice[-1][1]))

    print('max_yaw: ', max_yaw)

    color = ['green', 'pink', 'orange', 'blue', 'yellow', 'red']
    # range_axs2 = [np.floor(min(seg_value)), np.ceil(max(seg_value))]

    for i, route in enumerate(trajectory_whole):
        title = "trajectory : {}".format(i)
        points = np.arange(6)
        interval = route.shape[1] // len(points) * points

        fig, axs = plt.subplots(2, 1, figsize=[8.89, 17.78])
        plt.rcParams['axes.facecolor'] = '#222222'

        # subplot 1
        # axs[0].plot(route[0,:], route[1,:], linewidth=4, label = 'Trajectory')
        axs[0].plot(route[0, :], route[1, :], '.', markersize=3, label='Trajectory')

        for ind in range(len(points)):
            axs[0].plot(route[0, interval[ind]], route[1, interval[ind]], 'o', color=color[ind], markersize=12)

        axs[0].set_ylabel('North (meter)')
        axs[0].set_xlabel('East (meter)')
        axs[0].axis('equal')
        axs[0].title.set_text(title)

        # subplot 2
        x_slice = seg_value_slice[i][0]
        y_slice = seg_value_slice[i][1]  # - min(seg_value_slice[i][1])topic
        # axs[1].plot(x_slice, y_slice, linewidth=4, color='red', alpha=0.6, label='yaw angle')
        axs[1].plot(x_slice, y_slice, linewidth=3, color='red', alpha=0.6, label=topic_name)
        # print('~~~~', topic_name)
        for ind in range(len(points)):
            axs[1].plot(x_slice[interval[ind]], y_slice[interval[ind]], 'o', color=color[ind], markersize=12)

        if topic_name == 'Heading (deg)':
            topic_range['yticks_min'] = (
                        (y_slice[interval[0:len(points)]].max() + y_slice[interval[0:len(points)]].min()) / 2 - 180)
            topic_range['yticks_max'] = (
                        (y_slice[interval[0:len(points)]].max() + y_slice[interval[0:len(points)]].min()) / 2 + 180)
            # print('yticks_min, yticks_max', topic_range['yticks_min'], topic_range['yticks_max'])
            topic_range['ylim_min'] = topic_range['yticks_min'] - 10
            topic_range['ylim_max'] = topic_range['yticks_max'] + 10
        axs[1].set_yticks(np.arange(topic_range['yticks_min'], topic_range['yticks_max'], 45), minor=False)
        axs[1].set_ylim([topic_range['ylim_min'], topic_range['ylim_max']])

        axs[1].yaxis.grid(True, which='major')
        axs[1].xaxis.grid(True)

        axs[1].set_xlabel('Time (s)')
        axs[1].set_ylabel(plot_name2)
        axs[1].title.set_text("{} : {}".format(plot_name2, i))
        axs[1].legend(loc='upper left', facecolor='white')
        if seg_speed_value is not None:
            t2 = axs[1].twinx()
            y2_slice = seg_value_slice[i][3]
            t2.plot(x_slice, y2_slice, linewidth=3, color='yellow', alpha=0.6, label='speed(m/s)')
            t2.set_ylabel('speed', fontsize=9)
            t2.set_ylim([0, y2_slice.max() + 1])
            t2.legend(loc='upper right', facecolor='white')
        start_time = return_local_time(seg_value_slice[i][2][0])
        filename = "{}_{}_{}.png".format(os.path.basename(output_path), i, start_time)
        fig.savefig(os.path.join(output_path, filename))
        print(i)


def plotting_all(input_path, output_path, can_paths=[]):
    # %%
    df_oxts = pd.read_csv(input_path)
    basename = os.path.basename(input_path)
    dir_name = os.path.splitext(basename)[0]
    dir_name_output_path = os.path.join(output_path, dir_name)
    os.makedirs(dir_name_output_path, exist_ok=True)
    topics.extend(can_topics)
    for topic in topics:
        topic_name = topic['topic_name']
        topic_output_path = os.path.join(dir_name_output_path, topic_name)
        # topic_output_path = re.sub(r"\(.*?\)|\{.*?\}|\[.*?\]", "", topic_output_path)
        if '(' in topic_output_path and topic_output_path.index('(') > -1:
            topic_output_path = topic_output_path[:topic_output_path.index('(')]
        topic_output_path = topic_output_path.replace(' ', '_')
        os.makedirs(topic_output_path, exist_ok=True)
        can_df = None
        if topic in can_topics:
            can_df = pd.read_csv(can_paths[can_topics.index(topic)])
        plot_30s(df_oxts, topic_output_path, topic_name, topic_range=topic, can_df=can_df)


if __name__ == '__main__':
    input_path = '/home/lhd/coding/data_check_scripts/converter_data/20220803165046/gnss/can_bag_20220803165046_001_gnss.csv'
    output_path = '../output_data/'
    can_path_list = [
        '/home/lhd/coding/data_check_scripts/converter_data/20220803165046/canbus/can_bag_20220803165047_001_brakeStatus.csv',
        '/home/lhd/coding/data_check_scripts/converter_data/20220803165046/canbus/can_bag_20220803165047_001_gaspedel.csv',
        '/home/lhd/coding/data_check_scripts/converter_data/20220803165046/canbus/can_bag_20220803165047_001_steering.csv'
    ]
    plotting_all(input_path, output_path, can_path_list)
