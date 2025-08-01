import sys
from pathlib import Path


def get_config_dir() -> str:
    """
    获取配置文件所在目录的路径
    兼容打包: hook-yxmb_compatlib.py 中的 collect_data_files 会自动处理
    """
    # 使用当前脚本所在目录的上一级目录
    return Path(__file__).resolve().parent.parent.joinpath("hospital_config").as_posix()
