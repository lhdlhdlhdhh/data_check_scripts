"""
check src_dir nums,types,names
"""

import numpy as np
import pandas as pd


def check_error_speed(csv_file, max_speed, min_speed):
    time_header = 'Time (GPS ns)'
    time_gap = 1
    speed_header = 'ISO i.s. longitudinal velocity (m/s)'
    csv_df = pd.read_csv(csv_file)
    longitudinal_velocity_df = csv_df[speed_header].to_numpy()
    index_with_speed_err = np.where(longitudinal_velocity_df > max_speed)[0]
    f_a = []
    for ind in index_with_speed_err:
        f_l = ['值异常', speed_header, int(csv_df.loc[ind][time_header]), longitudinal_velocity_df[ind]]
        f_a.append(f_l)
    step1_df = pd.DataFrame(f_a, columns=['error_type', 'columns', 'timestamp', 'error_value'])
    step1_df.to_csv('./error2.csv')

    # step2
    timestamp = step1_df['timestamp'].to_numpy()
    time_diff = np.round(timestamp[1:] - timestamp[:-1], 5)
    index_with_gap = np.where(time_diff < time_gap)[0]

    start_timestamp = 0
    abs_max_value = 0
    res = []
    for ind in range(len(time_diff)):
        if start_timestamp == 0:
            start_timestamp = step1_df.loc[ind]['timestamp']
        if ind in index_with_gap:
            abs_max_value = max([abs_max_value, abs(step1_df.loc[ind]['error_value'])])
        else:
            end_timestamp = step1_df.loc[ind]['timestamp']
            abs_max_value = abs(step1_df.loc[ind]['error_value'])
            res.append(['值异常', speed_header, start_timestamp, end_timestamp, abs_max_value])
            start_timestamp = 0
            abs_max_value = 0
    step2_df = pd.DataFrame(res, columns=['error_type', 'columns', 'start_timestamp', 'end_timestamp', 'error_value'])
    step2_df.to_csv('../output/error2.csv')


if __name__ == '__main__':
    check_error_speed('../220318_145840.csv', 50, 0)
