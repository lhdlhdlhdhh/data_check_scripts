"""
check src_dir nums,types,names
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd


def get_readable_time(unix_timestamp):
    hour_min_sec = datetime.fromtimestamp(unix_timestamp).strftime("%Y%m%d_%H%M%S.%f")
    return hour_min_sec


def check_loss_frame(csv_file, time_gap, time_continuity_gap, frame_frequency=None):
    csv_name_file = os.path.basename(csv_file).split('.')[0]
    if csv_file.endswith('.csv'):
        time_header = 'Time (GPS ns)'
        time_coeff = 1e9
    else:
        time_header = 'timestamp'
        time_coeff = 1
    time_gap *= time_coeff
    time_continuity_gap *= time_coeff

    csv_df = pd.read_csv(csv_file)
    print(f'begin to anaysis {os.path.split(csv_file)[-1]}')

    timestamp = csv_df[time_header].to_numpy()
    time_diff = np.round(timestamp[1:] - timestamp[:-1], 5)
    time_diff_sort = np.argsort(time_diff)

    if frame_frequency is None:
        frame_frequency = int(len(timestamp) / ((timestamp[-1] - timestamp[0])/1e9))

    index_with_gap = np.where(time_diff > time_gap)[0]

    loss_frame_step1 = []
    for ind in index_with_gap:
        loss_frame_step1.append(['丢帧', time_header, int(timestamp[ind]), int(time_diff[ind] / time_coeff * frame_frequency)])
    loss_frame_df = pd.DataFrame(loss_frame_step1, columns=['error_type', 'columns', 'timestamp', 'error_value'])
    loss_frame_df.to_csv(f'../output/{csv_name_file}_check_step1_res.csv')

    # step2
    loss_frame_step_2 = []
    if loss_frame_step1:
        loss_timestamp = loss_frame_df['timestamp'].to_numpy()
        loss_time_diff = np.round(loss_timestamp[1:] - loss_timestamp[:-1], 5)
        index_with_con_gap = np.where(loss_time_diff < time_continuity_gap)[0]

        start_timestamp = 0
        for ind in range(len(loss_time_diff)):
            if start_timestamp == 0:
                start_timestamp = loss_frame_df.loc[ind]['timestamp']
            if ind not in index_with_con_gap:
                end_timestamp = loss_frame_df.loc[ind]['timestamp'] + int(loss_frame_df.loc[ind]['error_value']/frame_frequency*time_coeff)
                loss_frame_step_2.append(['丢帧', time_header, start_timestamp, end_timestamp, (end_timestamp-start_timestamp)/time_coeff*frame_frequency])
                start_timestamp = 0
        # print(loss_frame_step_2)
    step2_df = pd.DataFrame(loss_frame_step_2, columns=['error_type', 'columns', 'start_timestamp', 'end_timestamp', 'error_value'])
    step2_df.to_csv(f'../output/{csv_name_file}_check_step2_res.csv')
    return loss_frame_step1, loss_frame_step_2


if __name__ == '__main__':
    # check_loss_frame('../220318_145840.csv', 0.3, 1, 60)
    # 1331647171421000000
    check_loss_frame('../can_bag_20220808132117_000_gnss.csv', 0.015, 1, 100)

    # for file in os.listdir(' ')
