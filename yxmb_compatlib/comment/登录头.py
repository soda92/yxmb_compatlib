import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from ..pages.login_page import LoginPage
from ..config.merge_config import load_config

def is_software_expired():
    """检查软件是否过期。"""
    # 建议将过期日期也放入配置中
    expiration_date = datetime.date(2099, 2, 22)
    return datetime.date.today() >= expiration_date

def login(driver: WebDriver):
    """
    执行登录流程。

    1. 从文件中读取凭据。
    2. 加载默认和特定医院的配置。
    3. 使用配置和凭据初始化 LoginPage。
    4. 执行登录。
    """
    # 建议将凭据文件的路径也放入配置中
    with open("./文档/admin.txt", 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file.readlines()]
        url, account, password, name = lines[0], lines[1], lines[2], lines[3]

    driver.get(url)
    driver.maximize_window()

    # 加载合并后的配置
    config = load_config()

    # 使用配置执行登录
    login_page = LoginPage(driver, config)
    login_page.execute_login(account, password, name)

    # 登录成功后的通用操作
    login_page.navigate_after_login()