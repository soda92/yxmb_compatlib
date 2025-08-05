import tomllib
import os
import sys
import shutil
from collections.abc import Mapping
from pathlib import Path
from functools import lru_cache # 1. 导入 lru_cache


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


def _load_and_merge_envtxt_and_admintxt_to_config(config: dict, config_dir: str):
    """
    查找并加载 admin.txt 中的凭据，然后合并到配置中。
    它会在当前工作目录的 '文档' 子目录中寻找 admin.txt。
    """
    from phis_config import ProgramConfigV2
    url = ProgramConfigV2.get_url()
    username = ProgramConfigV2.get_username()
    password = ProgramConfigV2.get_password()
    department_name = ProgramConfigV2.get_department_name()

    # 确保 credentials 表存在
    config.setdefault("credentials", {})

    config["credentials"]["url"] = url
    config["credentials"]["username"] = username
    config["credentials"]["password"] = password
    config["credentials"]["department_name"] = department_name

    config.setdefault('new_follow_up', {})
    config['new_follow_up']['use_clinic_record_other_than_contracted_doctor'] = ProgramConfigV2.use_other_doctor_records()

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


@lru_cache(maxsize=None) # 2. 添加装饰器
def load_config():
    """
    加载并合并配置。
    此函数的结果会被缓存，在程序单次运行中只执行一次。
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
    config = _load_and_merge_envtxt_and_admintxt_to_config(config, config_dir)

    return config
