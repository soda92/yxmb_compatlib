import logging
from kapybara.shortcuts import WebDriverWait, EC as EC, By
import time
import ddddocr

def yes_verify_code(driver, account, password):
    """
    查询文档中是否有验证码.txt 有的话，就跳过验证码 没有就不跳
    """
    try:
        with open('./文档/验证码.txt', 'r', encoding='utf-8') as file:
            _content = file.readlines()
        logging.info('验证码跳过')

        """
        过验证码版本
        """
        while True:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="phisname"]'))
            ).clear()
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="phisname"]'))
            ).send_keys(account)
            time.sleep(1)
            try:
                driver.switch_to.alert.accept()
            except:
                logging.info('没有弹窗')
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="password"]'))
            ).clear()
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="password"]'))
            ).send_keys(password)
            time.sleep(1)

            captcha_element = driver.find_element('id', 'img')
            captcha_element.screenshot('captcha.png')

            ocr = ddddocr.DdddOcr()
            with open('captcha.png', 'rb') as f:
                img_bytes = f.read()
            res = ocr.classification(img_bytes)
            logging.info('识别出的验证码为：' + res)
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="verifyCode"]'))
            ).clear()
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="verifyCode"]'))
            ).send_keys(res)
            time.sleep(1)
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="submitBtn"]'))
            ).click()

            try:
                WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//span[text()="健康档案"]')
                    )
                )
                break
            except:
                pass

    except:
        """
        不过验证码版本
        """

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="phisname"]'))
        ).send_keys(account)
        time.sleep(1)
        try:
            driver.switch_to.alert.accept()
        except:
            logging.info('没有弹窗')
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="password"]'))
        ).send_keys(password)
        time.sleep(1)
        # driver.maximize_window()
        while True:
            try:
                WebDriverWait(driver, 3).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//span[text()="健康档案"]')
                    )
                )
                break
            except:
                pass

    """
    二者共用部分
    """
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//span[text()="健康档案"]'))
    ).click()
    try:
        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="button-1005-btnIconEl"]')
            )
        ).click()
    except Exception as e:
        logging.info('没有弹窗 %s', e)
