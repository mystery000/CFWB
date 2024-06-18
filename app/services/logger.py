import os
import glob
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler

def cleanup_old_logs(log_folder, days_to_keep=30):
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
    log_files = glob.glob(os.path.join(log_folder, 'server_logs.*'))

    for log_file in log_files:
        try:
            file_date_str = log_file.split('.')[-1]
            file_date = datetime.datetime.strptime(file_date_str, '%Y-%m-%d')
            if file_date < cutoff_date:
                os.remove(log_file)
        except Exception as e:
            print(f"Error while deleting log file {log_file}: {e}")

def get_logger(name, log_level=logging.INFO):
    log_folder = 'app/logs'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_file_path = os.path.join(log_folder, 'server_logs')

    cleanup_old_logs(log_folder=log_folder)

    handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=0)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(log_level)

    return logger