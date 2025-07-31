import random
import time

from kapybara import FormElement
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from yxmb_compatlib.comment.write_excle import excel_append
from phis_introducing_med.introducing_medication import introducing_medication
from yxmb_compatlib.compements.tool import (
    update_exercise_time,
    update_staple_food,
    hypertension_assessment,
    diabetes_assessment
)


def new_follow_up(driver, new_sf_data, sfzh, record, headers):
    if '随访方式' in headers:
        sf_method = record['随访方式']
    else:
        sf_method = '门诊'

    driver.switch_to.default_content()

    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, "//li[contains(text(),'慢病随访')]"))
    ).click()
    time.sleep(1)

    # 切换到第一个 iframe
    first_iframe = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen21"]/iframe'))
    )
    driver.switch_to.frame(first_iframe)

    # 切换到第二个 iframe
    second_iframe = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen32"]/iframe'))
    )
    driver.switch_to.frame(second_iframe)

    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located(
            (By.XPATH, '//*[@id="document_title"]/tbody/tr/td[3]/img')
        )
    )
    element.click()

    # 获取慢病类型
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located(
            (By.XPATH, '//*[@id="divOne_1"]/tbody/tr[2]/td/input[1]')
        )
    )
    mb_type = element.get_attribute('value')

    # 获取人群分类
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located(
            (By.XPATH, '//*[@id="divOne_1"]/tbody/tr[1]/td/input[4]')
        )
    )
    mb_group = element.get_attribute('value')

    # 随访日期
    follow_date = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="dateCreated"]'))
    )
    driver.execute_script(
        "document.getElementById('dateCreated').removeAttribute('readonly');"
    )
    follow_date.clear()
    follow_date.send_keys(new_sf_data['随访日期'])

    # 是否加入国家标准版
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located(
            (
                By.XPATH,
                "//td[contains(text(),'是否加入国家标准版')]//input[@name='isGj' and @value='1']",
            )
        )
    ).click()
    time.sleep(0.5)

    # 随访方式
    wait = WebDriverWait(driver, 10)  # 等待最多10秒
    select_element = wait.until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="followWay"]'))
    )
    select = Select(select_element)
    select.select_by_visible_text(sf_method)

    wait = WebDriverWait(driver, 10)
    checkbox = wait.until(
        ec.element_to_be_clickable(
            (By.XPATH, "//label[contains(text(), '无症状')]/preceding-sibling::input")
        )
    )
    if not checkbox.is_selected():
        checkbox.click()

        try:
            element = WebDriverWait(driver, 3).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//span[contains(text(), "是否确认清除其他症状")]')
                )
            )
            print('是否确认清除其他症状')
            time.sleep(0.5)
            yes_element = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//button[contains(text(), "是")]')
                )
            )
            driver.execute_script('arguments[0].click();', yes_element)
        except TimeoutException:
            pass


    # 收缩压sbp
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="sbp"]'))
    )
    element.clear()
    sbp = str(int(float(new_sf_data['收缩压'])))
    element.send_keys(sbp)

    # 舒张压dbp
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="dbp"]'))
    )
    element.clear()
    dbp = str(int(float(new_sf_data['舒张压'])))
    element.send_keys(dbp)

    # 身高
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="height"]'))
    )
    element.clear()
    element.send_keys(new_sf_data['身高'])

    # 体重
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="weightCur"]'))
    )
    element.clear()
    element.send_keys(new_sf_data['体重'])

    # 目标体重
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="bmiCur"]'))
    )
    bmi = element.get_attribute('value')
    bmi = float(bmi)

    target_weight = new_sf_data['体重']
    if bmi >= 24:
        target_weight = new_sf_data['体重'] - random.randint(1, 2)
    elif bmi < 18.5:
        target_weight = new_sf_data['体重'] + random.randint(1, 2)
    elif bmi >= 28:
        target_weight = new_sf_data['体重'] - random.randint(2, 3)
    target_weight = str(round(float(target_weight), 1))
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="weightTar"]'))
    )
    element.clear()
    element.send_keys(target_weight)

    # 心率
    try:
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="heartRateCur"]'))
        )
        element.clear()
        element.send_keys(new_sf_data['心率'])

        # 目标心率
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="heartRateTar"]'))
        )
        element.clear()
        element.send_keys(new_sf_data['心率'])
    except:
        pass

    # 其他体征
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="otherSign"]'))
    )
    element.clear()
    waist = new_sf_data['腰围']
    # 业务：腹型肥胖
    # 在评估里显示腹型肥胖，在生活方式指导里选择减腹围
    gender = FormElement('性别', '//*[@id="divOne_1"]/tbody/tr[1]/td/input[2]').value
    idf = False
    if gender == '女':
        if waist >= 85:
            idf = True
    elif gender == '男':
        if waist >= 90:
            idf = True

    # 日吸烟量
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="smAmountCur"]'))
    )
    element.clear()
    element.send_keys(new_sf_data['日吸烟量'])

    target_smoke_amount = 0
    # 目标日吸烟量
    if int(new_sf_data['日吸烟量']) >= 1:
        target_smoke_amount = int(new_sf_data['日吸烟量']) - 1
    target_smoke_amount = str(target_smoke_amount)

    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="smAmountTar"]'))
    )
    element.clear()
    element.send_keys(target_smoke_amount)

    # 日饮酒量
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="dkAmountCur"]'))
    )
    element.clear()
    element.send_keys(new_sf_data['日饮酒量'])

    # 目标日饮酒量
    target_drink_amount = 0
    if int(new_sf_data['日饮酒量']) >= 5:
        target_drink_amount = int(new_sf_data['日饮酒量']) - random.randint(2, 3)
    target_drink_amount = str(target_drink_amount)
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="dkAmountTar"]'))
    )
    element.clear()
    element.send_keys(target_drink_amount)

    # 运动次数
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="exCycleCur"]'))
    )
    element.clear()
    element.send_keys(new_sf_data['运动次数'])

    # 目标运动次数
    target_sport_times = 7
    if int(new_sf_data['运动次数']) < 7:
        target_sport_times = int(new_sf_data['运动次数']) + 1
    target_sport_times = str(target_sport_times)

    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="exCycleTar"]'))
    )
    element.clear()
    element.send_keys(target_sport_times)

    # 运动时间
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="exTimeCur"]'))
    )
    element.clear()
    element.send_keys(new_sf_data['运动时间'])

    # 目标运动时间
    target_sport_time = update_exercise_time(sfzh, new_sf_data['运动时间'], bmi)

    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="exTimeTar"]'))
    )
    element.clear()
    element.send_keys(target_sport_time)

    # 摄盐情况
    try:
        salt = new_sf_data['摄盐情况']
        if salt == '重':
            element = WebDriverWait(driver, 3).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//*[@id="stAmountCurTypeCur3"]')
                )
            )
            element.click()
        else:
            element = WebDriverWait(driver, 3).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//*[@id="stAmountCurTypeCur1"]')
                )
            )
            element.click()
    except:
        pass

    # 建议摄盐情况
    try:
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located(
                (By.XPATH, '//*[@id="stAmountCurTypeTar1"]')
            )
        )
        element.click()
    except:
        pass

    # 主食量
    try:
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="fhAmountCur"]'))
        )
        element.clear()
        element.send_keys(new_sf_data['主食量'])

        # 目标主食量
        target_fh_amount = update_staple_food(bmi, new_sf_data['主食量'])
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="fhAmountTar"]'))
        )
        element.clear()
        element.send_keys(target_fh_amount)
    except:
        pass

    # 空腹血糖
    element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="fbg"]'))
    )

    with open('./执行结果/env.txt', 'r', encoding='utf-8') as file:
        content = file.readlines()
    # 使用 split() 方法分割字符串
    place = content[6].replace('：', ':').split(':')[1]
    place = place.strip()
    print('无糖尿病是否录入空腹血糖:', place)
    if place == '否':
        element.clear()
        # 方法1：直接执行JS清空并触发事件（推荐）
        js_script = """
            var input = document.getElementById('fbg');
            input.value = '';
            // 创建并触发keyup事件
            var event = new Event('keyup');
            input.dispatchEvent(event);
        """
        driver.execute_script(js_script)
        # 执行JS清空隐藏输入框的值
        driver.execute_script("document.getElementById('fbg_hidden').value = '';")
    if place == '是':
        element.clear()
        element.send_keys(new_sf_data['空腹血糖'])
    if '糖尿病' in mb_type:
        element.clear()
        element.send_keys(new_sf_data['空腹血糖'])

    # 餐后血糖
    try:
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="pbg"]'))
        )
        element.clear()
        element.send_keys('未查')
    except:
        pass

    # 糖化血红蛋白
    try:
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="hba1c"]'))
        )
        element.clear()
        element.send_keys('未查')

        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="hba1cDate"]'))
        )
        element.clear()
    except:
        pass

    # TC
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="tc"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="tc"]'))
    ).send_keys('未查')

    # TG
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="tg"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="tg"]'))
    ).send_keys('未查')

    # HDL-C
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="hdlC"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="hdlC"]'))
    ).send_keys('未查')

    # LDL-C
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ldlC"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ldlC"]'))
    ).send_keys('未查')

    # BUN
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="bun"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="bun"]'))
    ).send_keys('未查')

    # Cr
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="cr"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="cr"]'))
    ).send_keys('未查')

    # 肌酐清除率
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ccr"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ccr"]'))
    ).send_keys('未查')

    # 尿检
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="uran"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="uran"]'))
    ).send_keys('未查')

    # 尿微量白蛋白
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="malb"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="malb"]'))
    ).send_keys('未查')

    # 心电图
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ecg"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ecg"]'))
    ).send_keys('未查')

    # 眼底
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="fundusOculi"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="fundusOculi"]'))
    ).send_keys('未查')

    # 其他辅助检查
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="otherTest"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="otherTest"]'))
    ).send_keys('未查')

    # 是否咳嗽、咳痰≥2周
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="isCough2"]'))
    ).click()
    time.sleep(0.5)

    # 是否痰中带血或咯血
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="isHemoptysis2"]'))
    ).click()
    time.sleep(0.5)

    # 患者姓名
    people_element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located(
            (By.XPATH, '//*[@id="divOne_1"]/tbody/tr[1]/td/input[1]')
        )
    )
    people_name = people_element.get_attribute('value')
    print('患者姓名：', people_name)

    # 随访人
    doctor_element = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="followPerson"]'))
    )
    doctor_name = doctor_element.get_attribute('value')
    print('随访人：', doctor_name)
    # 评估
    pg = ''
    if '高血压' in mb_type:
        # 判断血压是否控制满意
        hypertension_result = hypertension_assessment(
            dbp, sbp, sfzh, new_sf_data['随访日期'], people_name, doctor_name
        )
        pg = pg + hypertension_result + ','
        if hypertension_result == '高血压（血压控制不达标）':
            print('高血压（血压控制不达标）')
            if '高血压' in mb_type and '糖尿病' not in mb_type:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located(
                        (By.XPATH, '//*[@id="divOne_1"]/tbody/tr[4]/td/label[2]')
                    )
                )
                driver.execute_script('arguments[0].scrollIntoView();', element)
                # element.click()
                driver.execute_script('arguments[0].click();', element)
            elif '高血压' in mb_type and '糖尿病' in mb_type:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located(
                        (By.XPATH, '//*[@id="divOne_1"]/tbody/tr[4]/td/label[2]')
                    )
                )
                driver.execute_script('arguments[0].scrollIntoView();', element)
                # element.click()
                driver.execute_script('arguments[0].click();', element)

    if '糖尿病' in mb_type:
        diabetes_result = diabetes_assessment(
            new_sf_data['空腹血糖'],
            sfzh,
            new_sf_data['随访日期'],
            people_name,
            doctor_name,
        )
        pg = pg + diabetes_result + ','
        if diabetes_result == '糖尿病（血糖控制不达标）':
            print('糖尿病（血糖控制不达标）')
            if '高血压' not in mb_type and '糖尿病' in mb_type:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located(
                        (By.XPATH, '//*[@id="divOne_1"]/tbody/tr[4]/td/label[2]')
                    )
                )
                driver.execute_script('arguments[0].scrollIntoView();', element)
                # element.click()
                driver.execute_script('arguments[0].click();', element)
            elif '高血压' in mb_type and '糖尿病' in mb_type:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located(
                        (By.XPATH, '//*[@id="divOne_1"]/tbody/tr[5]/td/label[2]')
                    )
                )
                driver.execute_script('arguments[0].scrollIntoView();', element)
                # element.click()
                driver.execute_script('arguments[0].click();', element)

    if '冠心病' in mb_type:
        pg = pg + '冠心病（控制平稳）' + ','
    if '脑卒中' in mb_type:
        pg = pg + '脑卒中（控制平稳）' + ','

    if new_sf_data['日吸烟量'] != 0:
        pg = pg + '吸烟' + ','
    if new_sf_data['日饮酒量'] != 0:
        pg = pg + '饮酒' + ','
    if 24 <= bmi < 28:
        pg = pg + '超重' + ','
    if bmi >= 28:
        pg = pg + '肥胖' + ','
    if new_sf_data['运动次数'] == 0 or new_sf_data['运动时间'] == 0:
        pg = pg + '运动未达标' + ','

    # 业务：腹型肥胖
    if idf:
        pg = pg + '腹型肥胖'

    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="assess"]'))
    ).clear()
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="assess"]'))
    ).send_keys(pg)

    # 生活指导建议项
    from phis_lifestyle_advice import generate_lifestyle_advice
    life_suggestions = generate_lifestyle_advice(
        new_sf_data=new_sf_data,
        mb_group=mb_group,
        bmi=bmi,
        xb=gender)

    FormElement('生活指导建议', 'lifestyle').set_value(life_suggestions)

    # 医生建议
    from phis_doctor_advice import generate_doctor_advice
    advice = generate_doctor_advice(mb_type)
    FormElement('医生建议', 'suggest').set_value(advice)

    # 点击用药情况
    try:
        medication_element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located(
                (By.XPATH, '//font[contains(text(), "用  药  情  况")]')
            )
        )
    except TimeoutException:
        medication_element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located(
                (By.XPATH, '//font[contains(text(), "用药情况")]')
            )
        )
    driver.execute_script('arguments[0].click();', medication_element)
    time.sleep(1.5)

    try:
        element = WebDriverWait(driver, 5).until(
            ec.presence_of_element_located(
                (By.XPATH, '//span[contains(text(), "需要先")]')
            )
        )
        print('需要先保存随访，才能引入用药')
        FormElement('是', '//button[contains(text(), "是")]').click()

        try:
            # 获取本季度已做过慢病随访，是否继续保存
            with open('./执行结果/env.txt', 'r', encoding='utf-8') as file:
                content = file.readlines()
            # 使用 split() 方法分割字符串
            yes = content[5].replace('：', ':').split(':')[1].strip()

            element = WebDriverWait(driver, 3).until(
                ec.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(),'本季度已做过慢病随访')]")
                )
            )
            print('获取本季度已做过慢病随访，是否继续保存:', yes)
            FormElement('是否保存', f"//button[text()='{yes}']").click()
            with open(
                './执行结果/本季度已做过慢病随访.txt', 'a+', encoding='utf-8'
            ) as a:
                a.write(f'{new_sf_data}-本季度已做过慢病随访，是否继续保存:{yes}\n')

            if yes == '否':
                return False

        except TimeoutException:
            pass

        WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.XPATH, "//button[text()='确定']"))
        ).click()
        try:
            element = WebDriverWait(driver, 5).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//span[contains(text(), "是否加入到个人服务计划中")]')
                )
            )
            WebDriverWait(driver, 5).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//button[contains(text(), "否")]')
                )
            ).click()
        except:
            pass
        # 点击用药情况
        FormElement('用药情况', 'yongyao').click()
    except:
        pass

    # 开始引入用药
    result = introducing_medication(driver, mb_type, new_sf_data)
    if result is False or result == set():
        print(f'{sfzh}---没有引入任何药品')
        with open('./执行结果/没有引入任何药品.txt', 'a+', encoding='utf-8') as file:
            file.write(f'{sfzh}---没有引入任何药品\n')
    time.sleep(1.5)

    # 点击保存
    save_button = WebDriverWait(driver, 30).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="saveAction"]'))
    )
    driver.execute_script('arguments[0].click();', save_button)

    try:
        # 获取本季度已做过慢病随访，是否继续保存
        with open('./执行结果/env.txt', 'r', encoding='utf-8') as file:
            content = file.readlines()
        # 使用 split() 方法分割字符串
        yes = content[5].replace('：', ':').split(':')[1].strip()

        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located(
                (By.XPATH, "//span[contains(text(),'本季度已做过慢病随访')]")
            )
        )
        print('获取本季度已做过慢病随访，是否继续保存:', yes)

        element_yes = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, f"//button[text()='{yes}']"))
        )
        driver.execute_script('arguments[0].click();', element_yes)

        with open('./执行结果/本季度已做过慢病随访.txt', 'a+', encoding='utf-8') as a:
            a.write(f'{new_sf_data}-本季度已做过慢病随访，是否继续保存:{yes}\n')

        if yes == '否':
            return False

    except TimeoutException:
        pass

    try:
        element = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located(
                (By.XPATH, "//span[contains(text(),'药品名称不能为空或无')]")
            )
        )
        WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.XPATH, "//button[text()='确定']"))
        ).click()
        excel_append(
            '执行结果/异常名单.xlsx',
            '身份证号',
            sfzh + '\t',
            '异常原因',
            '药品名称不能为空或无无法保存',
        )
        return False
    except TimeoutException:
        pass

    try:
        element = WebDriverWait(driver, 120).until(
            ec.presence_of_element_located(
                (By.XPATH, "//span[contains(text(),'保存成功')]")
            )
        )
        WebDriverWait(driver, 120).until(
            ec.presence_of_element_located((By.XPATH, "//button[text()='确定']"))
        ).click()
        print(f'{new_sf_data}-随访保存成功')
        excel_append(
            '执行结果/成功名单.xlsx',
            '身份证号',
            sfzh,
            '成功',
            f'慢病随访新建成功-{new_sf_data}, 引入用药-{result}',
        )
    except TimeoutException:
        print(f'{new_sf_data}-随访保存超时')
        excel_append(
            '执行结果/异常名单.xlsx',
            '身份证号',
            sfzh + '\t',
            '异常原因',
            '保存超时-需验证重跑',
        )
