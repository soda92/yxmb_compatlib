import logging
import os


def check_and_create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logging.info(f"文件夹 '{folder_path}' 不存在，已创建成功！")
    else:
        logging.info(f"文件夹 '{folder_path}' 已存在。")
