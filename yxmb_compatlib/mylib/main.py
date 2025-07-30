import configparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

class CustomBrowser(webdriver.Chrome):
    def __init__(self, disable_image=False):
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read('配置文件/config.ini', encoding='utf-8')

        # 获取配置文件的内容
        google = config.get('config', 'Google')
        browser_drivers = config.get('config', 'Browser_drivers')

        if google == 'BIN':
            if browser_drivers == 'no':
                driver_path = r"BIN\109.0.5414.172\chromedriver.exe"
                browser_path = r'BIN\thorium.exe'
                service = Service(driver_path)
                options = webdriver.ChromeOptions()
                options.binary_location = browser_path
                options.add_argument('-ignore-certificate-errors')
                options.add_argument('-ignore-ssl-errors')
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option('excludeSwitches', ['enable-automation'])

                # # 中文语言
                # options.add_argument("--lang=zh-CN")
                # # 用户目录
                # from pathlib import Path
                # temp_user_data_dir = Path("chrome_data")
                # temp_user_data_dir.mkdir(exist_ok=True)
                # options.add_argument(f"user-data-dir={temp_user_data_dir}")

                if disable_image:
                    options.add_argument("--blink-settings=imagesEnabled=false")
                    # TODO KEY 冲突
                    # prefs = {"profile.managed_default_content_settings.images": 2}
                    # options.add_experimental_option("prefs", prefs)

                # 方法一：禁用密码保存提示（推荐）
                # 这会禁止浏览器弹出“保存密码”的提示
                options.add_experimental_option("prefs", {
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False
                })

                # 调用父类（webdriver.Chrome）的构造器
                super().__init__(service=service, options=options)
                self.set_page_load_timeout(600)  # 页面加载超时
                self.implicitly_wait(10)  # 元素未找到时的等待时间
        elif google == 'google':
            if browser_drivers == 'no':
                super().__init__()
                self.set_page_load_timeout(600)
                self.implicitly_wait(10)
            elif browser_drivers == 'yes':
                driver_path = "chromedriver.exe"
                service = Service(driver_path)
                options = webdriver.ChromeOptions()
                options.add_argument('-ignore-certificate-errors')
                options.add_argument('-ignore-ssl-errors')
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                if disable_image:
                    options.add_argument("--blink-settings=imagesEnabled=false")
                    prefs = {"profile.managed_default_content_settings.images": 2}
                    options.add_experimental_option("prefs", prefs)

                super().__init__(service=service, options=options)
                self.set_page_load_timeout(600)
                self.implicitly_wait(10)
        elif google == 'hh':  # 火狐浏览器
            if browser_drivers == 'yes':
                geckodriver_path = "geckodriver.exe"
                service = Service(geckodriver_path)
                options = webdriver.FirefoxOptions()
                options.add_argument('-ignore-certificate-errors')
                options.add_argument('-ignore-ssl-errors')
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.set_preference("dom.webdriver.enabled", False)
                options.set_preference('useAutomationExtension', False)
                options.add_argument("--disable-infobars")
                options.add_argument('disable-infobars')
                options.set_preference("dom.webdriver.enabled", False)
                options.set_preference("marionette.enabled", False)


                super().__init__(service=service, options=options)
                self.set_page_load_timeout(600)
                self.implicitly_wait(10)

        # from kapybara.shared_data import shared_data
        # shared_data.driver = self

    def stop(self):
        self.quit()