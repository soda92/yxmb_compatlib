import configparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from typing import Optional, Union
from pathlib import Path
import logging


# --- 辅助函数 ---

import logging


def disable_login_bg(driver, urls:list[str]):
    # 启用网络拦截
    driver.execute_cdp_cmd('Network.enable', {})

    # 定义要阻止的图片URL模式
    # 示例：阻止来自 example.com 域名下的所有图片
    # 或者阻止包含特定关键词的图片
    block_patterns = urls
    # "*.example.com/*.png",  # 阻止example.com下所有png图片
    # "*.othersite.com/ads/*.jpg", # 阻止othersite.com下ads目录的jpg图片
    # "data:image/*" # 阻止base64编码的图片 (data URI)

    # 添加请求拦截规则
    # resourceType: 'Image' 确保我们只拦截图片请求
    # urlFilter: 使用通配符匹配URL
    # behavior: 'block' 阻止请求
    driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': block_patterns})

    logging.info('已设置图片拦截规则。')



def _find_bin_version() -> str:
    """在 BIN 目录中查找浏览器版本。"""
    # ... (代码从旧类中移到这里)
    entries = Path('BIN').iterdir()
    versions = [
        entry.name for entry in entries if entry.is_dir() and entry.name.startswith('1')
    ]
    if not versions:
        logging.critical('无法在BIN目录中找到浏览器.')
        exit(-1)

    versions.sort(reverse=True)
    logging.info(f'找到的浏览器版本: {versions}')
    return versions[0]


# --- 工厂函数 ---


def create_browser(disable_image=False) -> Union[webdriver.Chrome, webdriver.Firefox]:
    """
    一个工厂函数，用于根据配置文件创建和配置一个 WebDriver 实例。
    """
    config_path = Path('配置文件/config.ini')
    use_existing_browser = False
    if not config_path.exists(): # 没有配置文件
        if not Path('BIN').exists():
            # 没有配置文件和浏览器时，使用默认浏览器
            use_existing_browser = True
        else:
            # 有浏览器自动创建配置文件
            config_path.parent.mkdir(exist_ok=True, parents=True)
            config_path.write_text(
                encoding='utf8',
                data="""[config]
Google=BIN
Browser_drivers=no
# 上面这个no是代表不使用驱动
""",
            )
    else: # 有配置文件
        if not Path('BIN').exists():
            # 有配置文件，但是没有浏览器
            logging.critical(f'浏览器不存在，请复制一个浏览器。')
            exit(-1)

    google = "google"
    browser_drivers = "no"

    if not use_existing_browser:
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')

        google = config.get('config', 'Google')
        if google.lower() in ["google", "hh"]:
            google = google.lower()
        browser_drivers = config.get('config', 'Browser_drivers').lower()

    driver = None
    options = None
    service = None

    # 根据配置设置选项
    if google == 'BIN':
        version = _find_bin_version()
        driver_path = f'BIN/{version}/chromedriver.exe'
        browser_path = r'BIN/thorium.exe'
        service = Service(driver_path)
        options = webdriver.ChromeOptions()
        options.binary_location = browser_path
        prefs = {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
        }
        if disable_image:
            options.add_argument('--blink-settings=imagesEnabled=false')
            prefs['profile.managed_default_content_settings.images'] = 2
        options.add_experimental_option('prefs', prefs)

    elif google == 'google' and browser_drivers == 'yes':
        driver_path = 'chromedriver.exe'
        service = Service(driver_path)
        options = webdriver.ChromeOptions()
        prefs = {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
        }
        if disable_image:
            options.add_argument('--blink-settings=imagesEnabled=false')
            prefs['profile.managed_default_content_settings.images'] = 2
        if prefs:
            options.add_experimental_option('prefs', prefs)

    elif google == 'google' and browser_drivers == 'no':
        options = webdriver.ChromeOptions()
        prefs = {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
        }
        if disable_image:
            options.add_argument('--blink-settings=imagesEnabled=false')
            prefs['profile.managed_default_content_settings.images'] = 2
        if prefs:
            options.add_experimental_option('prefs', prefs)

    elif google == 'hh' and browser_drivers == 'yes':
        geckodriver_path = 'geckodriver.exe'
        service = Service(geckodriver_path)
        options = webdriver.FirefoxOptions()
        # ... (此处可以添加所有 Firefox 的特定选项)

    # 通用设置
    if options and isinstance(options, webdriver.ChromeOptions):
        options.add_argument('-ignore-certificate-errors')
        options.add_argument('-ignore-ssl-errors')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

    # --- 实例化 Driver ---
    if google == 'BIN':
        driver = webdriver.Chrome(service=service, options=options)
    elif google == 'google' and browser_drivers == 'yes':
        driver = webdriver.Chrome(service=service, options=options)
    elif google == 'google' and browser_drivers == 'no':
        driver = webdriver.Chrome(options=options)
    elif google == 'hh' and browser_drivers == 'yes':
        driver = webdriver.Firefox(service=service, options=options)
    else:
        # 默认或不支持的情况
        logging.info('使用默认的 Selenium WebDriver 初始化。')
        driver = webdriver.Chrome()

    driver.set_page_load_timeout(600)
    driver.implicitly_wait(10)

    from yxmb_compatlib.config import load_config
    config = load_config()
    urls = config.get('login_bg', {}).get('bg_urls', [])
    disable_login_bg(driver, urls)
    return driver


# --- 向后兼容的类 ---


class CustomBrowser:
    """
    一个包装类，用于向后兼容。
    它在内部使用 create_browser 工厂，并将所有方法调用委托给真实的 driver 实例。
    """

    def __init__(self, disable_image=False):
        # 使用工厂创建并持有 driver 实例
        self._driver = create_browser(disable_image=disable_image)

    def find_element_cross_iframe(
        self, by: By, value: str, depth: int = 0, max_depth: int = 5
    ) -> Optional[WebElement]:
        """
        在主文档和所有 iframe 中递归查找元素。
        """
        try:
            return self._driver.find_element(by, value)
        except NoSuchElementException:
            pass

        if depth >= max_depth:
            return None

        iframes = self._driver.find_elements(By.TAG_NAME, 'iframe')
        for iframe in iframes:
            self._driver.switch_to.frame(iframe)
            element = self.find_element_cross_iframe(by, value, depth + 1, max_depth)
            if element:
                # 找到元素后，保持在当前 iframe 上下文中并返回
                return element
            # 如果未找到，切回父级 frame 继续搜索下一个 iframe
            self._driver.switch_to.parent_frame()

        # 如果在所有 iframe 中都未找到，返回 None
        return None

    def stop(self):
        """停止并关闭浏览器。"""
        return self._driver.quit()

    def __getattr__(self, name):
        """
        将所有其他属性和方法的调用委托给内部的 driver 实例，
        以确保 CustomBrowser 的行为与标准 WebDriver 完全相同。
        """
        return getattr(self._driver, name)
