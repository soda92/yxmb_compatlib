import sys
from .path import get_config_dir
import logging


def get_hospital_name() -> str:
    """
    获取医院名称。
    1.从可执行名称中获取（打包）
    2.如果文件名称中没有，从文件夹名称获取
    3.检测命令行参数
    """
    name_to_detect = ""
    from pathlib import Path

    executable = Path(sys.executable)
    config_dir_files = Path(get_config_dir()).glob("*.toml")
    config_names = [f.stem for f in config_dir_files if f.is_file()]

    if getattr(sys, "frozen", False):
        # 如果是打包的应用
        name_to_detect += Path(sys.executable).stem
        for name in config_names:
            if name in name_to_detect:
                logging.info(f"从打包可执行文件检测到医院名称: {name}")
                return name

    name_to_detect += executable.parent.name
    for name in config_names:
        if name in name_to_detect:
            logging.info(f"从文件夹名称检测到医院名称: {name}")
            return name

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            for name in config_names:
                if name in arg:
                    logging.info(f"从命令行参数检测到医院名称: {name}")
                    return name

    raise ValueError(
        "无法从可执行文件或配置文件中检测到医院名称，请检查配置文件或命令行参数。"
    )
