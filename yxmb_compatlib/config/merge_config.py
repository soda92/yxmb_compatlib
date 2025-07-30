import tomllib
import os
from collections.abc import Mapping
from pathlib import Path

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

def _load_and_merge_credentials(config: dict, config_dir: str):
    """
    查找并加载 admin.txt 中的凭据，然后合并到配置中。
    它会在配置目录的父目录（应用根目录）中寻找 admin.txt。
    """
    # config_dir 是 '.../hospital_config'，其父目录是应用根目录
    admin_txt_path = Path(config_dir).parent / 'admin.txt'

    if not admin_txt_path.exists():
        print("警告: 在应用根目录下未找到 'admin.txt'。将跳过凭据加载。")
        return config

    try:
        with open(admin_txt_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
            if len(lines) >= 4:
                # 确保 credentials 表存在
                config.setdefault('credentials', {})
                
                # 将凭据合并到配置中
                config['credentials']['url'] = lines[0]
                config['credentials']['username'] = lines[1]
                config['credentials']['password'] = lines[2]
                config['credentials']['department_name'] = lines[3]
                print(f"成功从 '{admin_txt_path}' 加载凭据。")
            else:
                print(f"警告: '{admin_txt_path}' 文件格式不正确，应至少包含4行。")
    except Exception as e:
        print(f"错误: 读取 '{admin_txt_path}' 时发生错误: {e}")

    return config

def load_config():
    """
    加载并合并配置。
    1. 加载 default.toml。
    2. 加载特定医院的 toml 文件并覆盖默认值。
    3. 加载 admin.txt 中的凭据并合并。
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

    # 4. 加载并合并 admin.txt 中的凭据
    config = _load_and_merge_credentials(config, config_dir)

    return config
