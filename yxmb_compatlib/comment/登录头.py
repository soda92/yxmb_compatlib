import datetime
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
    """
    # 1. 加载所有合并后的配置（包括 .toml 和 admin.txt）
    config = load_config()

    # 检查软件是否过期
    if is_software_expired(config):
        raise Exception("软件已过期，请联系管理员。")

    # 2. 从配置中获取凭据
    credentials = config.get('credentials', {})
    url = credentials.get('url')
    account = credentials.get('username')
    password = credentials.get('password')
    department_name = credentials.get('department_name')

    if not all([url, account, password]):
        raise ValueError("配置错误: 未能从 admin.txt 或其他配置源成功加载 url, username, 和 password。")

    # 3. 执行登录
    driver.get(url)
    driver.maximize_window()

    login_page = LoginPage(driver, config)
    login_page.execute_login(account, password, department_name)

    # 4. 登录成功后的通用操作
    login_page.navigate_after_login()