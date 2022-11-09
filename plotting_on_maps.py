#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 28 12:23:15 2022

@author: jiaqi
"""

import folium
from folium.features import DivIcon
import os
import pandas as pd
import numpy as np
import time


def return_local_time(unix_time):
    return time.strftime("%Y%m%d_%H%M%S", time.localtime(unix_time))


def return_data_raw(df_lane, latitude='Latitude (deg)', longitude='Longitude (deg)'):
    df_lane = df_lane.dropna(subset=[latitude])
    df_lane = df_lane.dropna(subset=[longitude])
    #    df_lane = df_lane.dropna(subset=['ISO yaw angle (deg)'])
    # data_raw = np.array([df_lane[latitude], df_lane[longitude]])
    latitude, longitude = df_lane[latitude].to_numpy(), df_lane[longitude].to_numpy()
    data_raw = list(zip(latitude, longitude))

    return data_raw, df_lane


def return_data_raw_diff(df_lane, latitude='Latitude (deg)', longitude='Longitude (deg)', diff_lati = 0.002, diff_longi=0.0046 ):
    df_lane = df_lane.dropna(subset=[latitude])
    df_lane = df_lane.dropna(subset=[longitude])
    #    df_lane = df_lane.dropna(subset=['ISO yaw angle (deg)'])
    # data_raw = np.array([df_lane[latitude], df_lane[longitude]])
    latitude, longitude = df_lane[latitude].to_numpy(), df_lane[longitude].to_numpy()
    latitude -= diff_lati
    longitude += diff_longi
    data_raw = list(zip(latitude, longitude))

    return data_raw, df_lane


def set_initial_map(location_point, zoom_start,  tilechoice='google_satellite'):
    tile_choices = ['google_satellite', 'Gaode_satellite']
    if tilechoice not in tile_choices:
        raise ValueError(f'please choose between {tile_choices}')

    if tilechoice == 'google_satellite':
        m = folium.Map(location=location_point,
                       zoom_start=zoom_start,
                       tiles='https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                       attr='google_map'
                       )
    elif tilechoice == 'Gaode_satellite':
        m = folium.Map(location=location_point,
                       zoom_start=zoom_start,
                       tiles='http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', # 高德
                       attr='高德地图'
                       )
    return m


def plot_points_with_folium(data_raw, m, color, radius=0.6):
    # loc2 = [tuple(x) for x in data_raw.T.tolist()]
    for i, loc in enumerate(data_raw):
        folium.Circle(
            radius=radius,
            location=loc,
            popup="",
            color=color,
            fill=True,
        ).add_to(m)
    return m


def plot_index_points_with_folium(data_raw, m, color, radius=0.6):
    # loc2 = [tuple(x) for x in data_raw.T.tolist()]
    loc2 = data_raw
    for i, loc in enumerate(loc2):
        folium.Circle(
            radius=radius,
            location=loc,
            popup="",
            color=color,
            fill=True,
        ).add_to(m)

        folium.map.Marker(
            loc,
            icon=DivIcon(
                icon_size=(250, 36),
                icon_anchor=(0, 0),
                html='<div style="font-size: 14pt;color: red">{}</div>'.format(i),
            )
        ).add_to(m)
    return m


def plot_line_with_folium(data_raw, m, color, weight=3, opacity=0.8):
    # loc2 = [tuple(x) for x in data_raw.T.tolist()]
    folium.PolyLine(data_raw,
                    color=color,
                    weight=weight,
                    opacity=opacity).add_to(m)
    return m


def plot_every_30_seconds(data_raw, m, timestamp, color="green"):
    # timestamp = np.array(df['timestamp'])

    times = timestamp - timestamp[0]
    interval = 30
    index = np.searchsorted(times, np.arange(0, int(times[-1]), interval), side='left', sorter=None)

    # loc2 = [tuple(x) for x in data_raw.T.tolist()]
    loc2 = data_raw
    for i in range(len(index) - 1):

        if index[i] == index[i + 1]:
            continue

        loc = loc2[index[i]:index[i + 1]]

        folium.Circle(
            radius=1,
            location=loc[0],
            popup="The Waterfront",
            color=color,
            fill=True,
        ).add_to(m)

        folium.map.Marker(
            loc[len(loc) // 3],
            icon=DivIcon(
                icon_size=(250, 36),
                icon_anchor=(0, 0),
                html='<div style="font-size: 14pt;color: red">{}</div>'.format(i),
            )
        ).add_to(m)

    return m


def draw_html(csv_path, output, map_satellite="google", draw_df=None, plot_conf=None):
    if draw_df is None:
        df = pd.read_csv(csv_path)
    else:
        df = draw_df
    data_raw, df_filtered = return_data_raw(df)
    if map_satellite == "google":
        satellite = "google_satellite"
    else:
        satellite = "Gaode_satellite"
    # Gaode_satellite  /  google_satellite
    m = set_initial_map(data_raw[0], zoom_start=14, tilechoice=satellite)
    m = plot_line_with_folium(data_raw, m, 'red', weight=3)
    # timestamp = np.array(df_filtered['Time (GPS ns)']) / 1e9 + 315964782 - 18  # GPS timestamp
    # timestamp = np.array(df_filtered['Time (GPS ns)']) / 1e9  # UNIX timestamp
    # print(f'draw_html:{csv_path} start time: {return_local_time(timestamp[0])}')
    # print(f'draw_html:{csv_path} end time: {return_local_time(timestamp[-1])}')

    # m = plot_every_30_seconds(data_raw, m, timestamp, color='orange',)
    # m = plot_points_with_folium(data_raw[:100],m,'orange')

    diff_lati = 0.002
    diff_longi = 0.0046
    if plot_conf is not None:
        diff_lati = plot_conf.get('plot_map', {}).get('diff_lati', diff_lati)
        diff_longi = plot_conf.get('plot_map', {}).get('diff_longi', diff_longi)
    data_raw, df_filtered = return_data_raw_diff(df, diff_lati=diff_lati, diff_longi=diff_longi)
    m = plot_line_with_folium(data_raw, m, 'orange', weight=3)

    # output_file = f'{return_local_time(timestamp[0])}_{int(timestamp[0])}_{satellite}.html'
    output_file = os.path.join(output, f'{os.path.basename(csv_path)}.{satellite}.html')
    m.save(output_file)


# %%
if __name__ == '__main__':
    path = '/home/lhd/coding/data_check_scripts/test_data/can_bag_20220823092508_20220823092508_000000_gnss.csv'
    output_folder = '/home/lhd/coding/data_check_scripts/test_data'

    draw_html(path, output_folder, "google")
