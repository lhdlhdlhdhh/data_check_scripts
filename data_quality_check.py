#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2022-8-13

@author: lihaodong
"""
import json
import os
import sys
import argparse
import time
from json import JSONDecodeError

import numpy as np
import pandas as pd

from plotting_on_maps import draw_html

time_coefficient = 1e9  # ns -> s coefficient
RTK_TIMESTAMP = "Time (GPS ns)"
CAN_TIMESTAMP = "timestamp"
ERROR_TYPE_VALUE = '值异常'
ERROR_TYPE_CHANGE = '变化率异常'
ERROR_TYPE_LOSS_FRAME = '帧异常'
STEP1_VALUE_COLUMNS = ['error_type', 'child_error_type', 'columns', 'timestamp', 'loss_frame', 'value_max']
STEP2_VALUE_COLUMNS = ['error_type', 'child_error_type', 'columns', 'start_timestamp', 'end_timestamp', 'loss_frame', 'value_max']


def arg_parser():
    parser = argparse.ArgumentParser(prog='data_quality_check',
                                     description='check preprocessed data',
                                     usage='''\n    %(prog)s <options>\n
Examples:\n\n    %(prog)s <option> <path> ...\n
Available Options:\n    
                  -i \t\t The input directory
                  -o \t\t output directory
                  ''')
    parser.add_argument('-i', '--input_dir', required=True, type=str, help='The input preprocessed directory')
    parser.add_argument('-o', '--output', required=True, type=str, help='The output directory')
    parser.add_argument('-c', '--config_path', required=False, default='./config.json', type=str, help='The config_path')
    parser.add_argument('-m', '--model', required=False, type=str, help='RTK/CAN csv suffix name')
    parser.add_argument('-t', '--time_continuity_gap', required=False, type=float, default=1,
                        help='time_continuity_gap(s)')
    parser.add_argument('-f', '--frame_frequency', required=False, type=int, default=100, help='frame_frequency')
    parser.add_argument('-s', '--map_satellite', required=False, type=str, default='google', help='g:google.2:gaode')
    return parser.parse_args()


def verify_path(src_dir, out_dir):
    """
    verify_path src_dir,out_dir
    :param src_dir, out_dir
    :return: csv_df, out_dir
    """
    if not os.path.isfile(src_dir) or not src_dir.endswith('.csv'):
        print('please input exists csv file.')
        sys.exit(-1)
    if out_dir.endswith('/'):
        out_dir = out_dir[:-1]
        if not os.path.isdir(out_dir):
            print('please check out_dir is exists.')
            sys.exit(-1)
    csv_df = pd.read_csv(src_dir)
    return csv_df, out_dir


def load_config(config_path):
    if not os.path.isfile(config_path):
        print('please make sure exists config.json file.')
        sys.exit(-1)
    with open(config_path, 'r') as f:
        conf_str = f.read()
    try:
        conf = json.loads(conf_str)
    except JSONDecodeError:
        print('please make sure config.json file.')
        sys.exit(-1)
    return conf


def check_frame(csv_df, time_header, topic_np, frame_frequency, topic, _max, _min, error_type, save_accuracy):
    if len(topic_np) == 0:
        raise Exception('No data!!!please make sure csv file is right.')
        # sys.exit(-1)
        # print('No data!!!please make sure csv file is right.')
        # sys.exit(-1)
    step1_value = []
    max_index_err = np.where((topic_np > _max))[0]
    min_index_err = np.where((topic_np < _min))[0]
    nan_index_err = np.where(np.isnan(topic_np))[0]
    for ind in max_index_err:
        if ind == 0:
            continue
        value_max = int(round(topic_np[ind] * save_accuracy, 0))
        loss_frame = 1
        if not np.isnan(csv_df.loc[ind][time_header]):
            timestamp = int(round(csv_df.loc[ind][time_header], 0))
        else:
            timestamp = 0
        child_error_type = '大于最大值'
        if topic in (RTK_TIMESTAMP, CAN_TIMESTAMP):
            loss_frame = int(round(value_max / time_coefficient / save_accuracy * frame_frequency, 0))
            if loss_frame > 1:
                loss_frame -= 1
            loss_frame = max(loss_frame, 1)
            child_error_type = f'丢帧:{child_error_type}'
        step1_value.append([error_type, child_error_type, topic, timestamp, loss_frame, value_max])
    for ind in min_index_err:
        if ind == 0:
            continue
        value_max = int(round(topic_np[ind] * save_accuracy, 0))
        loss_frame = 1
        if not np.isnan(csv_df.loc[ind][time_header]):
            timestamp = int(round(csv_df.loc[ind][time_header], 0))
        else:
            timestamp = 0
        child_error_type = '小于最小值'
        if topic in (RTK_TIMESTAMP, CAN_TIMESTAMP):
            loss_frame = int(round(value_max / time_coefficient / save_accuracy * frame_frequency, 0))
            if loss_frame > 1:
                loss_frame -= 1
            loss_frame = max(loss_frame, 1)
            child_error_type = f'多帧:{child_error_type}'
        step1_value.append([error_type, child_error_type, topic, timestamp, loss_frame, value_max])
    for ind in nan_index_err:
        if ind == 0:
            continue
        loss_frame = 1
        child_error_type = '空值'
        if topic in (RTK_TIMESTAMP, CAN_TIMESTAMP):
            timestamp = 0
        else:
            timestamp = int(round(csv_df.loc[ind][time_header], 0))
        step1_value.append([error_type, child_error_type, topic, timestamp, loss_frame, -1])
    step1_df = pd.DataFrame(step1_value, columns=STEP1_VALUE_COLUMNS)
    return step1_df


def check_duration(step1_df, topic, _max, _min, time_continuity_gap, error_type):
    step2_value = []
    if len(step1_df):
        timestamp = step1_df['timestamp'].to_numpy()
        start_timestamp = 0
        end_timestamp = 0
        value_max = None
        loss_frame = 0
        child_error_type = ''

        if error_type == ERROR_TYPE_LOSS_FRAME:  # 丢帧
            for ind in range(len(timestamp)):
                if child_error_type != step1_df.loc[ind]['child_error_type']:
                    start_timestamp = 0
                    end_timestamp = 0
                    loss_frame = 0
                if start_timestamp == 0:
                    start_timestamp = step1_df.loc[ind]['timestamp']
                if end_timestamp == 0:
                    end_timestamp = step1_df.loc[ind]['timestamp']
                child_error_type = step1_df.loc[ind]['child_error_type']
                if int(step1_df.loc[ind]['timestamp'] - end_timestamp) < (time_continuity_gap * time_coefficient):
                    loss_frame += step1_df.loc[ind]['loss_frame']
                    end_timestamp = step1_df.loc[ind]['timestamp']
                else:
                    if child_error_type == '多帧:小于最小值':
                        error_type = ERROR_TYPE_CHANGE
                    step2_value.append([error_type, child_error_type, topic, start_timestamp, end_timestamp, loss_frame, 0])
                    loss_frame = step1_df.loc[ind]['loss_frame']
                    end_timestamp = step1_df.loc[ind]['timestamp']
                    start_timestamp = step1_df.loc[ind]['timestamp']
            step2_value.append([error_type, child_error_type, topic, start_timestamp, end_timestamp, loss_frame, 0])
        else:
            for ind in range(len(timestamp)):
                if child_error_type != step1_df.loc[ind]['child_error_type']:
                    start_timestamp = 0
                    end_timestamp = 0
                    loss_frame = 0
                    value_max = 0
                if start_timestamp == 0:
                    start_timestamp = step1_df.loc[ind]['timestamp']
                if end_timestamp == 0:
                    end_timestamp = step1_df.loc[ind]['timestamp']
                child_error_type = step1_df.loc[ind]['child_error_type']
                if int((step1_df.loc[ind]['timestamp'] - end_timestamp) / time_coefficient) < time_continuity_gap:
                    if step1_df.loc[ind]['value_max'] > _max:
                        now_diff = step1_df.loc[ind]['value_max'] - _max
                    else:
                        now_diff = abs(_min - step1_df.loc[ind]['value_max'])
                    if value_max is not None:
                        if value_max > _max:
                            max_diff = value_max - _max
                        else:
                            max_diff = abs(_min - value_max)
                        if now_diff > max_diff:
                            value_max = step1_df.loc[ind]['value_max']
                    else:
                        value_max = step1_df.loc[ind]['value_max']
                    end_timestamp = step1_df.loc[ind]['timestamp']
                    loss_frame += step1_df.loc[ind]['loss_frame']
                else:
                    step2_value.append([error_type, child_error_type, topic, start_timestamp, end_timestamp, loss_frame, value_max])
                    end_timestamp = step1_df.loc[ind]['timestamp']
                    value_max = step1_df.loc[ind]['value_max']
                    start_timestamp = step1_df.loc[ind]['timestamp']
                    loss_frame = 1
            step2_value.append([error_type, child_error_type, topic, start_timestamp, end_timestamp, loss_frame, value_max])
    step2_df = pd.DataFrame(step2_value, columns=STEP2_VALUE_COLUMNS)
    return step2_df


def check_topic(csv_df, time_header, time_continuity_gap, frame_frequency, topic, topic_value):
    # step1 value
    topic_np = csv_df[topic].to_numpy()
    max_value = topic_value['max_value']
    min_value = topic_value['min_value']
    max_change = topic_value['max_change']
    min_change = topic_value['min_change']
    save_accuracy = topic_value['save_accuracy']
    error_type_value = ERROR_TYPE_VALUE
    error_type_change = ERROR_TYPE_CHANGE
    if topic in (RTK_TIMESTAMP, CAN_TIMESTAMP):
        error_type_change = ERROR_TYPE_LOSS_FRAME
    # if topic == RTK_TIMESTAMP:  # CAN_TIMESTAMP is not ns need open
        max_value *= time_coefficient
        min_value *= time_coefficient
        max_change *= time_coefficient
        min_change *= time_coefficient
    step1_value_df = check_frame(csv_df, time_header, topic_np, frame_frequency, topic, max_value, min_value, error_type_value, save_accuracy)
    # step1 change
    change_diff_np = csv_df[topic].diff().to_numpy()
    step1_change_df = check_frame(csv_df, time_header, change_diff_np, frame_frequency, topic, max_change, min_change, error_type_change, save_accuracy)

    # step2 value
    step2_value_df = check_duration(step1_value_df, topic, max_value, min_value, time_continuity_gap, error_type_value)
    step2_change_df = check_duration(step1_change_df, topic, max_change, min_change, time_continuity_gap, error_type_change)
    s1_df = pd.concat([step1_value_df, step1_change_df])
    if len(step2_value_df) == 0 and len(step2_change_df) == 0:
        step2_change_df.loc[1] = ['正常', 'not found error', topic, 0, 0, 0, 0]
    s2_df = pd.concat([step2_value_df, step2_change_df])
    return s1_df, s2_df


def single_check(src_dir, out_dir, conf, model, time_continuity_gap, frame_frequency, map_satellite):
    s_time = time.time()
    print(f'check file:{src_dir} start:{s_time}')
    csv_df, out_dir = verify_path(src_dir, out_dir)
    csv_name = os.path.basename(src_dir)
    if model is None:
        model = src_dir.split('_', -1)[-1].split('.')[0]
    if model == 'gnss':
        time_header = RTK_TIMESTAMP
    else:
        time_header = CAN_TIMESTAMP
        # global time_coefficient  # CAN_TIMESTAMP is not ns need open
        # time_coefficient = 1  # CAN_TIMESTAMP is not ns need open
    topics = conf.get(model, {})
    # print(topics)
    step1 = pd.DataFrame([], columns=STEP1_VALUE_COLUMNS)
    step2 = pd.DataFrame([], columns=STEP2_VALUE_COLUMNS)
    # print(f'csv_df.columns{csv_df.columns}')
    for k, v in topics.items():
        if v.get('is_check') and k in csv_df.columns:
            frame_frequency = v.get('frame_frequency', frame_frequency)
            # print(f'{csv_name} {time_header} {frame_frequency}')
            s1_df, s2_df = check_topic(csv_df, time_header, time_continuity_gap, frame_frequency, k, v)
            step1 = pd.concat([step1, s1_df])
            step2 = pd.concat([step2, s2_df])
    step1_date = pd.to_datetime(step1["timestamp"].values, utc=True, unit="ns").tz_convert('Asia/Shanghai').strftime("%Y-%m-%d %H:%M:%S.%f")
    step1['datetime'] = step1_date
    step2_start_date = pd.to_datetime(step2["start_timestamp"].values, utc=True, unit="ns").tz_convert('Asia/Shanghai').strftime("%Y-%m-%d %H:%M:%S.%f")
    step2_end_date = pd.to_datetime(step2["end_timestamp"].values, utc=True, unit="ns").tz_convert('Asia/Shanghai').strftime("%Y-%m-%d %H:%M:%S.%f")
    step2['start_datetime'] = step2_start_date
    step2['end_datetime'] = step2_end_date
    step1.to_csv(os.path.join(out_dir, f'{csv_name}.frame.csv'))
    step2.to_csv(os.path.join(out_dir, f'{csv_name}.duration.csv'))
    if model == 'gnss':
        draw_html(src_dir, out_dir, map_satellite, plot_conf=conf)
    print(f"check file:{src_dir} spent:{time.time() - s_time}")


# bulk dir
def verify_bulk_path(src_dir, out_dir):
    """
    verify_path src_dir,out_dir
    :return: csv_df, out_dir
    """
    if src_dir.endswith('/'):
        src_dir = src_dir[:-1]
        if not os.path.isdir(src_dir):
            print('please input exists src_dir.')
            sys.exit(-1)
    if out_dir.endswith('/'):
        out_dir = out_dir[:-1]
        if not os.path.isdir(out_dir):
            print('please check out_dir is exists.')
            sys.exit(-1)
    return src_dir, out_dir


def find_check_csvs(src_dir, conf):
    check_csv_paths = []
    csv_suffix_list = conf.keys()
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            for csv_suffix in csv_suffix_list:
                if file.endswith(f'{csv_suffix}.csv'):
                    check_csv_paths.append((os.path.join(root, file), csv_suffix))
    return check_csv_paths


def bulk_check_dir(src_dir, out_dir, conf, time_continuity_gap, frame_frequency, map_satellite):
    s_time = time.time()
    print(f'bulk_check_dir dir:{src_dir} start:{s_time}')
    src_dir, out_dir = verify_bulk_path(src_dir, out_dir)
    check_csv_paths = find_check_csvs(src_dir, conf)
    gnss_csv_list = []
    for check_csv_path in check_csv_paths:
        single_check(check_csv_path[0], out_dir, conf, check_csv_path[1], time_continuity_gap, frame_frequency, map_satellite)
        if check_csv_path[1] == 'gnss':
            gnss_csv_list.append(check_csv_path[0])
    if gnss_csv_list:
        gnss_df_list = [pd.read_csv(gnss_csv) for gnss_csv in gnss_csv_list]
        draw_df = pd.concat(gnss_df_list)
        draw_df.sort_values(by='Time (GPS ns)')
        draw_df = draw_df.reset_index()
        # draw_html(src_dir, out_dir, "google", draw_df, plot_conf=conf)
        # draw_html(src_dir, out_dir, "gaode", draw_df, plot_conf=conf)
        draw_html(src_dir, out_dir, map_satellite, draw_df, plot_conf=conf)
    print(f"bulk_check_dir dir:{src_dir} spent:{time.time() - s_time}")


def check_data(src_dir, out_dir, config_path='./config.json', model=None, time_continuity_gap=1, frame_frequency=100, map_satellite="gaode"):
    conf = load_config(config_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if src_dir.endswith('.csv'):
        single_check(src_dir, out_dir, conf, model, time_continuity_gap, frame_frequency, map_satellite)
    else:
        bulk_check_dir(src_dir, out_dir, conf, time_continuity_gap, frame_frequency, map_satellite)


if __name__ == '__main__':
    # 得到参数
    args = arg_parser()
    print(args)
    src_dir = args.input_dir
    out_dir = args.output
    config_path = args.config_path
    model = args.model
    time_continuity_gap = args.time_continuity_gap
    frame_frequency = args.frame_frequency
    map_satellite = args.map_satellite
    check_data(src_dir, out_dir, config_path, model, time_continuity_gap, frame_frequency, map_satellite)
    # cmd:python data_quality_check.py -i /home/lhd/coding/data_check_scripts/can_bag_20220808132117_000_gnss.csv -o ./output -c ./config.json
    # cmd:python data_quality_check.py -i /home/lhd/coding/data_check_scripts/20220803165046_data/canbus/can_bag_20220803125217_000_gaspedel.csv -o ./output -c ./config.json -m gaspedel
