from selenium.webdriver.common.by import By

class Locator:
    """一个简单的类，用于封装Selenium定位符。"""
    def __init__(self, by: str, value: str):
        # 将字符串形式的 'id', 'css_selector' 等转换为 By.ID, By.CSS_SELECTOR
        self.by = getattr(By, by.upper(), None) if by else None
        self.value = value

    def to_tuple(self):
        """返回可用于Selenium查找的元组 (By, value)。"""
        if not self.by:
            raise ValueError("Locator type 'by' is not set or invalid.")
        return (self.by, self.value)

    def format(self, *args, **kwargs):
        """允许格式化定位符的值，例如用于动态XPath。"""
        return Locator(self.by, self.value.format(*args, **kwargs))