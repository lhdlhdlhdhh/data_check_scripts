from builtins import ValueError
import os, shutil, re, sys, subprocess, logging

from datetime import datetime
from functools import wraps


def create_new_dir(abs_path, dir_name):
    dir_path = os.path.join(abs_path, dir_name)
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    return dir_path


datetime_format = '%Y_%m_%d_%H_%M_%S'
log_dir = create_new_dir("./", "log")
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(log_dir, f'{datetime.now():{datetime_format}}_logging.log')),
                        logging.StreamHandler()])


class Hint:
    datetime_format = '%Y-%m-%d %H:%M:%S'
    INFO = f"[\033[92mInfo\033[0m]\t"
    WARNING = f"[\033[93mWarn\033[0m]\t"
    FAIL = f"[\033[91mError\033[0m]\t"
    DONE = f"[\033[92mDone\033[0m]\t"
    TASK = f"[\033[92mTask\033[0m]\t"

    @property
    def info(self):
        return f"[\033[92mInfo\033[0m]\t"

    @property
    def warning(self):
        return f"[\033[93mWarn\033[0m]\t"

    @property
    def fail(self):
        return f"[\033[91mError\033[0m]\t"

    @property
    def done(self):
        return f"[\033[92mDone\033[0m]\t"

    @property
    def task(self):
        return f"[\033[92mTask\033[0m]\t"


hint = Hint()


def mylog(text, pos):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            t1 = datetime.now()
            logging.info(f"{hint.task} {text} {args[pos]}")
            try:
                retval = func(*args, **kw)
                logging.info(f"{hint.done} {text} {args[pos]}")
                logging.info(f"cost time: {datetime.now() - t1}")
                return retval
            except subprocess.CalledProcessError as exc:
                logging.error(f"{hint.fail} {text} {args[pos]}")
                logging.exception(exc)
                raise exc
            except Exception as exc:
                logging.error(f"{hint.fail} {text} {args[pos]}")
                logging.exception(exc)
                raise exc
        return wrapper
    return decorator


def find_files(dir_path, recursive=False, suffix=".bag", prefix=''):
    all_files = []
    if recursive:
        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.startswith(prefix) and f.endswith(suffix):
                    all_files.append(os.path.join(root, f))
    else:
        for f in os.listdir(dir_path):
            if f.startswith(prefix) and f.endswith(suffix):
                all_files.append(os.path.join(dir_path, f))
    if len(all_files) == 0:
        raise ValueError(f"There is no file with suffix:{suffix} and prefix:{prefix} in {dir_path}")
    all_files.sort()
    return all_files
