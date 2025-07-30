import time
import ddddocr
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .locator import Locator

class LoginPage:
    """封装登录页面的所有操作和元素。"""

    def __init__(self, driver: WebDriver, config: dict):
        self.driver = driver
        self.config = config
        self.timeout = config.get('settings', {}).get('default_timeout', 10)
        self.wait = WebDriverWait(self.driver, self.timeout)

        # 从配置中加载定位符
        login_cfg = self.config['login']
        self.locators = {
            'username': Locator(*login_cfg['username']),
            'password': Locator(*login_cfg['password']),
            'login_button': Locator(*login_cfg['login_button']),
            'captcha_image': Locator(*login_cfg.get('captcha', [None, None])),
            'captcha_input': Locator(*login_cfg.get('captcha_input', [None, None])),
            'department_button': Locator(*login_cfg.get('department_button', [None, None])),
            'health_record_menu': Locator(*self.config.get('home', {}).get('health_record_menu', [None, None]))
        }

    def _find_element(self, locator: Locator):
        """使用WebDriverWait查找元素。"""
        return self.wait.until(EC.visibility_of_element_located(locator.to_tuple()))

    def _click_element(self, locator: Locator):
        """查找并点击元素。"""
        self.wait.until(EC.element_to_be_clickable(locator.to_tuple())).click()

    def _send_keys(self, locator: Locator, text: str):
        """向元素发送文本。"""
        element = self._find_element(locator)
        element.clear()
        element.send_keys(text)

    def _handle_alert(self, timeout=1):
        """处理可能出现的弹窗。"""
        try:
            WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            pass # 没有弹窗，正常继续

    def has_captcha(self) -> bool:
        """检查登录页面是否有验证码。"""
        # 使用配置中的布尔值作为主要判断依据
        if 'captcha' in self.config['login'] and self.config['login']['captcha'] is False:
            return False
        
        # 如果配置为true或未配置，则检查元素是否存在
        try:
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(self.locators['captcha_image'].to_tuple())
            )
            return True
        except TimeoutException:
            return False

    def solve_captcha(self):
        """识别并输入验证码。"""
        captcha_element = self._find_element(self.locators['captcha_image'])
        img_bytes = captcha_element.screenshot_as_png

        ocr = ddddocr.DdddOcr(show_ad=False)
        res = ocr.classification(img_bytes)
        print(f'识别出的验证码为：{res}')

        self._send_keys(self.locators['captcha_input'], res)

    def execute_login(self, username, password, department_name=None):
        """执行完整的登录流程。"""
        self._handle_alert()
        self._send_keys(self.locators['username'], username)
        self._handle_alert() # 输入用户名后可能也有弹窗
        self._send_keys(self.locators['password'], password)

        if self.has_captcha():
            # 如果需要，可以加入更复杂的逻辑，例如多次尝试
            self.solve_captcha()

        self._click_element(self.locators['login_button'])

        # 登录后选择科室（如果需要）
        if department_name and self.locators['department_button'].by:
            try:
                # 更新定位符以包含科室名称
                dep_locator = self.locators['department_button'].format(department_name)
                self._click_element(dep_locator)
            except TimeoutException:
                print(f"未找到科室按钮: {department_name}")

        self._handle_alert()

    def navigate_after_login(self):
        """登录成功后，切换窗口并导航到指定菜单。"""
        # 切换到新窗口
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.maximize_window()

        # 点击菜单项
        if self.locators['health_record_menu'].by:
            try:
                self._click_element(self.locators['health_record_menu'])
            except TimeoutException:
                print("未找到'健康档案'菜单或类似按钮。")
        
        self._handle_alert()