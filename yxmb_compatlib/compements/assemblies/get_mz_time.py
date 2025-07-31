import re
import time

from selenium.webdriver import ActionChains

from kapybara.shortcuts import By, ec, WebDriverWait, StaleElementReferenceException

from comment.check_element import check_element
from comment.excle_write import excel_append2
from kapybara.form_element import FormElement


def get_mz_time(driver, record, headers):
    # 获取机构名称
    with open('./执行结果/env.txt', 'r', encoding='utf-8') as file:
        content = file.readlines()
    # 使用 split() 方法分割字符串
    place = content[4].replace('：', ':').split(':')[1].strip()
    print('需要判断的机构名称:', place)

    # 获取新建时间范围
    with open('./文档/admin.txt', 'r', encoding='utf-8') as file:
        content = file.readlines()
    # 使用 split() 方法分割字符串
    start_date = content[4].replace('：', ':').split(':')[1].strip()
    end_date = content[5].replace('：', ':').split(':')[1].strip()
    print('随访新建起始时间:', start_date)
    print('随访新建结束时间:', end_date)

    require = False
    doctor = ''
    # 判断是否需要根据签约医生来获取门诊日期
    if '签约医生' in headers:
        doctor = record['签约医生'].strip()
        print(f'需要根据签约医生{doctor}来获取门诊日期')
        require = True

    driver.switch_to.default_content()

    time.sleep(1)
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, "//dt[contains(text(),'门诊服务')]"))
    ).click()
    time.sleep(1)

    # 切换到第一个 iframe
    first_iframe = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen21"]/iframe'))
    )
    driver.switch_to.frame(first_iframe)

    # 使用一个无限循环，直到找不到元素
    while True:
        try:
            # 如果找不到元素，break跳出循环
            if not check_element(driver):
                break
        except:
            break
    time.sleep(1.5)
    # 获取页脚值
    page_number = (
        WebDriverWait(driver, 20)
        .until(ec.presence_of_element_located((By.XPATH, '//*[@id="ext-comp-1006"]')))
        .text
    )

    # 获取总页数
    count_number = re.findall(r'\d+', page_number)
    print('门诊总页数:', count_number)

    data_list = []
    needData = ''

    for i in range(0, int(count_number[0])):
        try:
            # 获取div下子div的数量
            WebDriverWait(driver, 20).until(
                ec.presence_of_element_located(
                    (
                        By.XPATH,
                        '/html/body/div[1]/div/div[1]/div/div[1]/div[2]/div/child::div',
                    )
                )
            )
            div_elements = driver.find_elements(
                By.XPATH,
                '/html/body/div[1]/div/div[1]/div/div[1]/div[2]/div/child::div',
            )
        except Exception as e:
            print(e)
            print(f'没有门诊记录')
            return data_list
        for j in range(1, len(div_elements) + 1):
            # 获取门诊机构名称
            name = FormElement(
                '门诊机构名称',
                f'//*[@id="ext-gen22"]/div[{j}]/table/tbody/tr[1]/td[3]/div',
            ).text
            doctor_name = FormElement(
                '门诊医生', f'//*[@id="ext-gen22"]/div[{j}]/table/tbody/tr[1]/td[4]/div'
            ).text

            if place in name:
                # print(f"当前选中的机构名称: {name}")
                # 获取门诊日期
                try:
                    element = WebDriverWait(driver, 10).until(
                        ec.presence_of_element_located(
                            (
                                By.XPATH,
                                f'//*[@id="ext-gen22"]/div[{j}]/table/tbody/tr[1]/td[2]/div',
                            )
                        )
                    )
                    date = element.text
                except StaleElementReferenceException:
                    # 如果元素过时，重新定位
                    element = WebDriverWait(driver, 10).until(
                        ec.presence_of_element_located(
                            (
                                By.XPATH,
                                f'//*[@id="ext-gen22"]/div[{j}]/table/tbody/tr[1]/td[2]/div',
                            )
                        )
                    )
                    date = element.text

                if str(start_date) <= str(date) <= str(end_date):
                    element = WebDriverWait(driver, 10).until(
                        ec.presence_of_element_located(
                            (
                                By.XPATH,
                                f'//*[@id="ext-gen22"]/div[{j}]/table/tbody/tr[1]/td[2]/div',
                            )
                        )
                    )
                    ActionChains(driver).double_click(element).perform()
                    time.sleep(1)

                    try:
                        element = WebDriverWait(driver, 10).until(
                            ec.presence_of_element_located(
                                (
                                    By.XPATH,
                                    f'/html/body/div[1]/div/div[1]/div/div[1]/div[2]/div/div[{j}]/table/tbody/tr[2]/td/div/div[1]',
                                )
                            )
                        )
                        needData = element.text
                    except StaleElementReferenceException:
                        # 如果元素过时，重新定位
                        element = WebDriverWait(driver, 10).until(
                            ec.presence_of_element_located(
                                (
                                    By.XPATH,
                                    f'/html/body/div[1]/div/div[1]/div/div[1]/div[2]/div/div[{j}]/table/tbody/tr[2]/td/div/div[1]',
                                )
                            )
                        )
                        needData = element.text
                    ActionChains(driver).double_click(element).perform()
                    time.sleep(1)

                    if '代' in needData:
                        sfzh = str(record['身份证号']) + '\t'
                        # 转换评估结果为 Excel 中的表头和内容格式
                        column_headers = [
                            '身份证号',
                            '代开药门诊日期',
                            '代开药门诊机构名称',
                            '代开药门诊医生',
                            '代开药门诊数据',
                        ]

                        # 将数据填充到内容列表中
                        contents = [sfzh + '\t', date, name, doctor_name, needData]

                        # 使用示例
                        file_path = '执行结果/代开药门诊数据.csv'
                        excel_append2(file_path, column_headers, contents)

                # print(f"门诊数据: {needData}")

                # print(f"门诊日期: {date}")
                if require:
                    if doctor == doctor_name:
                        if (
                            str(start_date) <= str(date) <= str(end_date)
                            and '代' not in needData
                        ):
                            # print(f"{date}在{start_date}-{end_date}时间范围内")
                            data_list.append(date)
                else:
                    if (
                        str(start_date) <= str(date) <= str(end_date)
                        and '代' not in needData
                    ):
                        # print(f"{date}在{start_date}-{end_date}时间范围内")
                        data_list.append(date)

        # 点击下一页按钮
        if i < int(count_number[0]) - 1:  # 如果不是最后一页，则继续翻页
            element = WebDriverWait(driver, 5).until(
                ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen43"]'))
            )
            driver.execute_script('arguments[0].click();', element)

            # 使用一个无限循环，直到找不到元素
            while True:
                try:
                    # 如果找不到元素，break跳出循环
                    if not check_element(driver):
                        break
                except:
                    break
            time.sleep(1.5)

    return data_list
