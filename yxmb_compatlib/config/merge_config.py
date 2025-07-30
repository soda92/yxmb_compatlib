import tomllib
import os
from collections.abc import Mapping

def deep_merge(source, destination):
    """
    递归地将 source 字典合并到 destination 字典中。
    """
    for key, value in source.items():
        if isinstance(value, Mapping) and key in destination and isinstance(destination[key], Mapping):
            destination[key] = deep_merge(value, destination[key])
        else:
            destination[key] = value
    return destination

def load_config():
    """
    加载并合并配置。

    首先加载 default.toml，然后加载指定医院的 toml 文件并覆盖默认值。
    """
    # 1. 加载默认配置
    from ..config.path import get_config_dir
    config_dir = get_config_dir()
    from ..config.hospital_name import get_hospital_name
    hospital_name = get_hospital_name()
    default_config_path = os.path.join(config_dir, 'default.toml')
    try:
        with open(default_config_path, 'r', encoding='utf-8') as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        raise Exception("默认配置文件 'default.toml' 未找到！")

    # 2. 如果存在，加载并合并特定医院的配置
    hospital_config_path = os.path.join(config_dir, f'{hospital_name}.toml')
    if os.path.exists(hospital_config_path):
        with open(hospital_config_path, 'r', encoding='utf-8') as f:
            hospital_config = tomllib.load(f)
            # 3. 深度合并配置
            config = deep_merge(hospital_config, config)

    return config
