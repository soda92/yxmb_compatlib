import ddddocr
import logging
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .locator import Locator

class LoginPage:
    """封装登录页面的所有操作和元素，包括重试逻辑。"""

    def __init__(self, driver: WebDriver, config: dict):
        self.driver = driver
        self.config = config
        self.timeout = config.get('settings', {}).get('default_timeout', 10)
        self.login_timeout = config.get('settings', {}).get('login_timeout', 30)
        self.wait = WebDriverWait(self.driver, self.timeout)

        # 从配置中加载定位符
        login_cfg = self.config['login']
        self.locators = {
            'username': Locator(*login_cfg['username']),
            'password': Locator(*login_cfg['password']),
            'login_button': Locator(*login_cfg['login_button']),
            'captcha_image': Locator(*login_cfg.get('captcha_image', [None, None])),
            'captcha_input': Locator(*login_cfg.get('captcha_input', [None, None])),
            'department_button': Locator(*login_cfg.get('department_button', [None, None]))
        }

        # 从 settings 中加载配置
        settings_cfg = self.config.get('settings', {})
        self.login_retries = settings_cfg.get('login_retries', 4)
        self.ignore_department_selection = settings_cfg.get('ignore_department', False)

    def _sanitize_url(self, url: str) -> str:
        """移除URL中的jsessionid等部分，以便进行可靠的比较。"""
        return url.split(';')[0]

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
            pass  # 没有弹窗，正常继续

    def _check_login_success(self, initial_url: str) -> bool:
        """检查是否已经登录成功，通过URL变化判断。"""
        current_url = self._sanitize_url(self.driver.current_url)
        if current_url != initial_url:
            logging.info(f"检测到URL已改变: {initial_url} -> {current_url}")
            return True
        return False

    def has_captcha(self) -> bool:
        """检查登录页面是否有验证码。"""
        # 使用配置中的布尔值作为主要判断依据
        captcha_enabled = self.config.get('login', {}).get('captcha_enabled', True)
        if not captcha_enabled:
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

    def _check_captcha_error(self) -> bool:
        """检查是否存在验证码错误信息。"""
        try:
            # 使用一个很短的超时来快速检查元素是否存在
            WebDriverWait(self.driver, 1).until(
                EC.visibility_of_element_located(("xpath", "//font[contains(text(), '验证码错误')]"))
            )
            logging.warning("检测到验证码错误，将立即重试。")
            return True
        except TimeoutException:
            return False

    def login(self, url: str, username: str, password: str, department_name: str = None):
        """
        执行完整的登录流程，包含重试、验证码错误处理和成功验证。
        """
        initial_url = ""
        for attempt in range(self.login_retries + 1):
            try:
                logging.info(f"开始第 {attempt + 1}/{self.login_retries + 1} 次登录尝试...")
                if attempt == 0:
                    self.driver.maximize_window()
                
                self.driver.get(url)
                
                initial_url = self._sanitize_url(self.driver.current_url)
                logging.info(f"初始URL: {initial_url}")

                # 填写表单
                self._send_keys(self.locators['username'], username)
                self._send_keys(self.locators['password'], password)

                if self.has_captcha():
                    self.solve_captcha()

                self._click_element(self.locators['login_button'])

                # 检查验证码错误，如果发现，立即进入下一次循环
                if self._check_captcha_error():
                    time.sleep(1) # 短暂等待后重试
                    continue

                # 验证登录是否成功（通过URL是否改变）
                extended_timeout = self.login_timeout + (attempt * 5)
                logging.info(f"等待页面跳转，超时时间: {extended_timeout}秒")
                
                WebDriverWait(self.driver, extended_timeout).until(
                    lambda driver: self._sanitize_url(driver.current_url) != initial_url
                )
                
                final_url = self._sanitize_url(self.driver.current_url)
                logging.info(f"URL已改变，登录验证成功: {initial_url} -> {final_url}")

                # 登录后选择科室（如果需要）
                if department_name and self.locators['department_button'].by and not self.ignore_department_selection:
                    try:
                        dep_locator = self.locators['department_button'].format(name=department_name)
                        self._click_element(dep_locator)
                    except TimeoutException:
                        logging.warning(f"未找到科室按钮: {department_name}")
                
                self._handle_alert()

                # 执行登录后的导航操作
                self.navigate_after_login()

                logging.info("登录流程完全成功。")
                return

            except TimeoutException:
                current_url = self._sanitize_url(self.driver.current_url)
                logging.warning(f"登录尝试 {attempt + 1} 超时。当前URL: {current_url}")
                
                if self._check_login_success(initial_url):
                    logging.info("虽然超时，但检测到登录实际上已成功。")
                    self.navigate_after_login()
                    return
                
                if attempt < self.login_retries:
                    time.sleep(2 + attempt)
                else:
                    logging.error("所有登录尝试均因超时失败。")
                    raise Exception("登录失败：页面在多次尝试后仍未跳转。")
                    
            except Exception as e:
                logging.error(f"登录尝试 {attempt + 1} 失败，发生错误: {e}", exc_info=True)
                
                if self._check_login_success(initial_url):
                    logging.info("虽然出现异常，但检测到登录实际上已成功。")
                    self.navigate_after_login()
                    return
                
                if attempt < self.login_retries:
                    time.sleep(2 + attempt)
                else:
                    logging.error("所有登录尝试均因发生未知错误而失败。")
                    raise

    def navigate_after_login(self):
        """登录成功后，根据配置执行一系列操作。"""
        post_login_actions = self.config.get('login', {}).get('post_login_actions', [])

        for action in post_login_actions:
            action_type = action.get('type')
            description = action.get('description', '未知操作')
            is_optional = action.get('optional', False)
            
            print(f"执行操作: {description} (类型: {action_type})")

            try:
                if action_type == 'switch_window':
                    if len(self.driver.window_handles) > 1:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                elif action_type == 'maximize_window':
                    self.driver.maximize_window()
                elif action_type == 'handle_alert':
                    self._handle_alert()
                elif action_type == 'click':
                    locator_data = action.get('locator')
                    if locator_data:
                        locator = Locator(*locator_data)
                        self._click_element(locator)
                else:
                    print(f"警告: 未知的操作类型 '{action_type}'")

            except TimeoutException as e:
                if is_optional:
                    print(f"警告: 可选操作 '{description}' 失败，元素未找到。继续执行...")
                else:
                    print(f"错误: 执行操作 '{description}' 失败。")
                    raise e
            except Exception as e:
                print(f"错误: 执行操作 '{description}' 时发生意外错误: {e}")
                raise e