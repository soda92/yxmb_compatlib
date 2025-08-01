from PyInstaller.utils.hooks import collect_data_files
import os
import yxmb_compatlib

# 找到 yxmb_compatlib 库的安装位置
module_path = os.path.dirname(yxmb_compatlib.__file__)
# 指定要包含的 config 目录的路径
config_source_path = os.path.join(module_path, 'hospital_config')

# 收集 config 目录下的所有文件
# collect_data_files 会自动保持相对于模块的目录结构
datas = collect_data_files('yxmb_compatlib')

# 或者，如果您只想包含特定的 hospital_config 目录，可以使用：
# datas = [(config_source_path + '/*', 'yxmb_compatlib/hospital_config')]