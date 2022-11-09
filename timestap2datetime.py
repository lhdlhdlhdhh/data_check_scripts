import os
import time

import pandas as pd


def find_check_csvs(src_dir):
    check_csv_paths = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.csv'):
                check_csv_paths.append(os.path.join(root, file))
    return check_csv_paths


def time2date(src_dir, out_dir):
    check_csv_paths = find_check_csvs(src_dir)
    print(check_csv_paths)
    for path in check_csv_paths:
        csv_name = os.path.basename(path)
        if csv_name.endswith('.csv'):
            s_time = time.time()
            print(f'time2date file:{path} start:{time.time()}')
            timeheader = 'Time (GPS ns)' if csv_name.endswith('gnss.csv') else 'timestamp'
            df = pd.read_csv(path)
            date_df = pd.to_datetime(df[timeheader].values, utc=True, unit="ns").tz_convert(
                'Asia/Shanghai').strftime("%Y-%m-%d %H:%M:%S.%f")
            df['datetime'] = date_df
            df.to_csv(os.path.join(out_dir, f'{csv_name}.datetime.csv'))
            print(f"time2date file:{src_dir} spent:{time.time() - s_time}")


if __name__ == '__main__':
    time2date('/home/lhd/coding/data_check_scripts/converter_data/20220803165046', '/home/lhd/coding/data_check_scripts/output_data/ori_csv_time2date')
