import datetime
import logging
import time
from selenium.webdriver.remote.webdriver import WebDriver
from ..pages.login_page import LoginPage
from ..config.merge_config import load_config

def is_software_expired(config: dict):
    """检查软件是否过期。"""
    # 从配置中获取过期日期，如果未设置则使用一个默认的未来日期
    expiration_date_str = config.get('settings', {}).get('expiration_date', '2099-02-22')
    try:
        expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"警告: 配置中的 'expiration_date' ({expiration_date_str}) 格式无效。请使用 'YYYY-MM-DD' 格式。")
        # 使用一个安全的默认值
        expiration_date = datetime.date(2099, 12, 31)
        
    return datetime.date.today() >= expiration_date

def login(driver: WebDriver):
    """
    执行登录流程。
    现在所有配置（包括凭据）都由 load_config() 统一处理。
    包含登录重试逻辑。
    """
    # 1. 加载所有合并后的配置
    config = load_config()

    # 检查软件是否过期
    if is_software_expired(config):
        raise Exception("软件已过期，请联系管理员。")

    # 2. 从配置中获取凭据和设置
    credentials = config.get('credentials', {})
    settings = config.get('settings', {})
    
    url = credentials.get('url')
    account = credentials.get('username')
    password = credentials.get('password')
    department_name = credentials.get('department_name')
    login_retries = settings.get('login_retries', 4)

    if not all([url, account, password]):
        raise ValueError("配置错误: 未能从 admin.txt 或其他配置源成功加载 url, username, 和 password。")

    # 3. 执行登录，包含重试逻辑
    for attempt in range(login_retries + 1):
        try:
            driver.get(url)
            driver.maximize_window()

            login_page = LoginPage(driver, config)
            login_page.execute_login(account, password, department_name)
            login_page.navigate_after_login()
            
            logging.info("登录成功。")
            return  # 登录成功，退出函数

        except Exception as e:
            logging.warning(f"登录尝试 {attempt + 1}/{login_retries + 1} 失败: {e}")
            if attempt < login_retries:
                time.sleep(2)  # 在重试前稍作等待
            else:
                logging.error("所有登录尝试均失败。")
                raise  # 抛出最后一次的异常