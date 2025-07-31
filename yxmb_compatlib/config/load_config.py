import tomllib
import os
import sys
import shutil
from collections.abc import Mapping
from pathlib import Path


def deep_merge(source, destination):
    """
    递归地将 source 字典合并到 destination 字典中。
    """
    for key, value in source.items():
        if (
            isinstance(value, Mapping)
            and key in destination
            and isinstance(destination[key], Mapping)
        ):
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
    admin_txt_path = Path.cwd() / "文档" / "admin.txt"

    if not admin_txt_path.exists():
        print("警告: 在应用根目录下未找到 'admin.txt'。将跳过凭据加载。")
        return config

    try:
        with open(admin_txt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
            if len(lines) >= 4:
                # 确保 credentials 表存在
                config.setdefault("credentials", {})

                # 将凭据合并到配置中
                config["credentials"]["url"] = lines[0]
                config["credentials"]["username"] = lines[1]
                config["credentials"]["password"] = lines[2]
                config["credentials"]["department_name"] = lines[3]
                print(f"成功从 '{admin_txt_path}' 加载凭据。")
            else:
                print(f"警告: '{admin_txt_path}' 文件格式不正确，应至少包含4行。")
    except Exception as e:
        print(f"错误: 读取 '{admin_txt_path}' 时发生错误: {e}")

    return config


def _handle_external_config(hospital_name: str, config_dir: str):
    """
    在打包模式下，处理外部配置文件。
    1. 如果外部配置文件不存在，则从包内复制一份。
    2. 返回外部配置文件的路径（如果存在）。
    """
    if not getattr(sys, "frozen", False):
        # 仅在打包模式下运行
        return None

    if os.getenv("YXMB_SUPPRESS_CONFIG_COPY"):
        print("检测到 YXMB_SUPPRESS_CONFIG_COPY 环境变量，跳过外部配置处理。")
        return None

    try:
        # 源路径是包内的 hospital_config 目录
        source_path = Path(config_dir) / f"{hospital_name}.toml"
        # 目标路径是可执行文件所在的目录
        executable_dir = Path(sys.executable).parent
        destination_path = executable_dir / f"{hospital_name}.toml"

        # 如果目标文件不存在，且源文件存在，则复制
        if not destination_path.exists() and source_path.exists():
            print(
                f"未找到外部配置文件，正在从包内复制 '{source_path.name}' 到 '{executable_dir}'"
            )
            shutil.copy(source_path, destination_path)

        return destination_path if destination_path.exists() else None
    except Exception as e:
        print(f"处理外部配置文件时出错: {e}")
        return None


def load_config():
    """
    加载并合并配置。
    1. 加载 default.toml。
    2. 加载特定医院的 toml 文件并覆盖默认值。
    3. (打包模式下) 处理并加载外部的医院 toml 文件。
    4. 加载 admin.txt 中的凭据并合并。
    """
    # 1. 加载默认配置
    from ..config.path import get_config_dir

    config_dir = get_config_dir()
    from ..config.hospital_name import get_hospital_name

    hospital_name = get_hospital_name()
    default_config_path = os.path.join(config_dir, "default.toml")
    try:
        # 使用 'rb' 模式以符合 tomllib 的要求
        with open(default_config_path, "rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        raise Exception("默认配置文件 'default.toml' 未找到！")

    # 2. 如果存在，加载并合并特定医院的配置（从包内）
    hospital_config_path = os.path.join(config_dir, f"{hospital_name}.toml")
    if os.path.exists(hospital_config_path):
        with open(hospital_config_path, "rb") as f:
            hospital_config = tomllib.load(f)
            config = deep_merge(hospital_config, config)

    # 3. (打包模式下) 处理并加载外部的医院配置文件
    external_config_path = _handle_external_config(hospital_name, config_dir)
    if external_config_path and external_config_path.exists():
        print(f"正在从外部文件加载配置: {external_config_path}")
        with open(external_config_path, "rb") as f:
            external_config = tomllib.load(f)
            # 深度合并，外部配置覆盖内部配置
            config = deep_merge(external_config, config)

    # 4. 加载并合并 admin.txt 中的凭据
    config = _load_and_merge_credentials(config, config_dir)

    return config
