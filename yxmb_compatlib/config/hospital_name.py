import sys
from .path import get_config_dir
import logging
from pathlib import Path
import tomllib

# 假设 check_name 函数已在别处定义，或者我们可以像这样简单定义它：
def check_name(name: str, text: str) -> bool:
    """检查一个名称是否存在于文本中。"""
    return name in text


def get_hospital_name() -> str:
    """
    获取医院名称，按以下顺序检测：
    1. 命令行参数
    2. 打包后的可执行文件名
    3. 可执行文件所在的文件夹名称
    4. 当前工作目录路径
    检测时会同时匹配医院中文名及其 pinyin。
    """
    config_dir_path = Path(get_config_dir())
    config_files = config_dir_path.glob("*.toml")
    
    # 加载所有医院配置，获取名称和pinyin
    # 格式: [{'name': '广宁', 'pinyin': 'guangning'}]
    hospital_configs = []
    for f in config_files:
        if f.is_file() and f.stem != 'default':
            try:
                with open(f, 'rb') as config_file:
                    data = tomllib.load(config_file)
                    hospital_configs.append({
                        'name': f.stem,
                        'pinyin': data.get('pinyin', '').lower() # 获取pinyin，转为小写
                    })
            except Exception as e:
                logging.warning(f"无法加载或解析配置文件 {f.name}: {e}")

    # 定义检测源和对应的日志消息模板
    # 格式: (要检查的字符串, 日志消息)
    detection_sources = []

    # 1. 从命令行参数检测 (最高优先级)
    if len(sys.argv) > 1:
        cli_args = " ".join(sys.argv[1:]).lower() # 转为小写以匹配pinyin
        detection_sources.append(
            (cli_args, "从命令行参数检测到医院: {}")
        )

    # 2. 从可执行文件名检测 (仅在打包模式下)
    if getattr(sys, "frozen", False):
        executable_name = Path(sys.executable).stem.lower() # 转为小写
        detection_sources.append(
            (executable_name, "从打包可执行文件检测到医院: {}")
        )

    # 3. 从父文件夹名称检测
    parent_dir_name = Path(sys.executable).parent.name.lower() # 转为小写
    detection_sources.append(
        (parent_dir_name, "从文件夹名称检测到医院: {}")
    )

    # 4. 从当前工作目录检测
    cwd_path = str(Path.cwd()).lower() # 转为小写
    detection_sources.append(
        (cwd_path, "从当前工作目录检测到医院: {}")
    )

    # 遍历所有检测源
    for source_text, log_message in detection_sources:
        for hospital in hospital_configs:
            hospital_name = hospital['name']
            pinyin = hospital['pinyin']
            
            # 检查中文名或pinyin是否存在于源文本中
            # 确保pinyin不为空
            if check_name(hospital_name, source_text) or (pinyin and check_name(pinyin, source_text)):
                logging.info(log_message.format(hospital_name))
                return hospital_name

    # 如果所有方法都失败了
    raise ValueError(
        "无法从可执行文件、路径或命令行参数中检测到医院名称。请确保配置文件存在且命名正确。"
    )
