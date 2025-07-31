import datetime
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from ..pages.login_page import LoginPage
from ..config import load_config
import time  # noqa: F401
import os

from .envWrite import env_write

# 检查是否需要重置已完成数量
if os.getenv("reset_finished_count") == "1":
    env_write('执行结果/env.txt', 3, f'已完成数量:0')

def is_software_expired(config: dict = None):
    """检查软件是否过期。"""
    if config is None:
        config = load_config()
    # 从配置中获取过期日期，如果未设置则使用一个默认的未来日期
    expiration_date_str = config.get("settings", {}).get(
        "expiration_date", "2099-02-22"
    )
    try:
        expiration_date = datetime.datetime.strptime(
            expiration_date_str, "%Y-%m-%d"
        ).date()
    except ValueError:
        print(
            f"警告: 配置中的 'expiration_date' ({expiration_date_str}) 格式无效。请使用 'YYYY-MM-DD' 格式。"
        )
        # 使用一个安全的默认值
        expiration_date = datetime.date(2099, 12, 31)

    return datetime.date.today() >= expiration_date


def login(driver: WebDriver):
    """
    执行登录流程。
    所有配置和重试逻辑都由LoginPage处理。
    """
    # 1. 加载所有合并后的配置
    config = load_config()

    # 检查软件是否过期
    if is_software_expired(config):
        raise Exception("软件已过期，请联系管理员。")

    # 2. 从配置中获取凭据
    credentials = config.get("credentials", {})
    url = credentials.get("url")
    account = credentials.get("username")
    password = credentials.get("password")
    department_name = credentials.get("department_name")

    if not all([url, account, password]):
        raise ValueError(
            "配置错误: 未能从 admin.txt 或其他配置源成功加载 url, username, 和 password。"
        )

    # 3. 实例化LoginPage并执行带重试的登录
    try:
        login_page = LoginPage(driver, config)
        login_page.login_with_retries(url, account, password, department_name)
    except Exception as e:
        logging.error(f"登录流程最终失败: {e}")
        # 可以在这里决定是否关闭浏览器或执行其他清理操作
        driver.quit()
        raise
