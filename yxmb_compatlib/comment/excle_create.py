import os
import pandas as pd
import logging


def check_and_create_excel(file_path):
    try:
        if not os.path.exists(file_path):
            # Create an empty DataFrame
            df = pd.DataFrame()
            # Save the DataFrame to an Excel file
            df.to_excel(file_path, index=False)
            logging.info(f"文件 '{file_path}' 不存在，已创建新Excel文件。")
        else:
            logging.info(f"文件 '{file_path}' 已存在。")
    except Exception as e:
        logging.info(f'处理文件时出现异常: {str(e)}')
