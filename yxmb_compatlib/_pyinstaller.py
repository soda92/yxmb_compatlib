import os

def get_hook_dirs():
    """返回包含 PyInstaller hook 的目录列表。"""
    return [os.path.join(os.path.dirname(__file__), "hooks")]