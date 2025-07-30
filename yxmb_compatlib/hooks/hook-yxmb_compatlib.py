from PyInstaller.utils.hooks import collect_data_files
import os
import yxmb_compatlib

# 找到 yxmb_compatlib 库的安装位置
module_path = os.path.dirname(yxmb_compatlib.__file__)
# 指定要包含的 config 目录的路径
config_source_path = os.path.join(module_path, 'hospital_config')

# 收集 config 目录下的所有文件，并将其放入打包后根目录的 'config' 文件夹中
datas = collect_data_files(config_source_path, destdir='hospital_config')