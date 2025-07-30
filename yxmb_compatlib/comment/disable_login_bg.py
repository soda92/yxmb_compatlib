import logging


def disable_login_bg(driver):
    # 启用网络拦截
    driver.execute_cdp_cmd('Network.enable', {})

    # 定义要阻止的图片URL模式
    # 示例：阻止来自 example.com 域名下的所有图片
    # 或者阻止包含特定关键词的图片
    block_patterns = [
        # "*.example.com/*.png",  # 阻止example.com下所有png图片
        # "*.othersite.com/ads/*.jpg", # 阻止othersite.com下ads目录的jpg图片
        # "data:image/*" # 阻止base64编码的图片 (data URI)
        'http://10.216.11.12:8089/cis/images/img/bg@3x.png',
        'http://10.216.11.12:8089/cis/images/img/bg-login@2x.png',
    ]

    # 添加请求拦截规则
    # resourceType: 'Image' 确保我们只拦截图片请求
    # urlFilter: 使用通配符匹配URL
    # behavior: 'block' 阻止请求
    driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': block_patterns})

    logging.info('已设置图片拦截规则。')
