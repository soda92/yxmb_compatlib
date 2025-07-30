import sys
from pathlib import Path


def get_config_dir() -> str:
    """
    获取配置文件所在目录的路径
    兼容打包
    """
    if getattr(sys, "frozen", False):
        # 如果是打包的应用, 根据MEIPASS获取配置目录
        return Path(sys._MEIPASS).joinpath("hospital_config").as_posix()
    else:
        # 如果是开发环境，使用当前脚本所在目录的上一级目录
        return Path(__file__).resolve().parent.parent.joinpath("hospital_config").as_posix()
