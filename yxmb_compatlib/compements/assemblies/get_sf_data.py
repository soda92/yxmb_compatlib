import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from compements.tool import parse_date


def get_sf_data(driver):
    # 获取新建时间范围
    with open('./文档/admin.txt', 'r', encoding='utf-8') as file:
        content = file.readlines()
    start_date = content[4].replace('：', ':').split(':')[1].strip()
    end_date = content[5].replace('：', ':').split(':')[1].strip()
    print('随访新建起始时间:', start_date)
    print('随访新建结束时间:', end_date)

    start_date = parse_date(start_date)
    start_year = start_date.year
    print('随访新建起始年份：', start_year)
    end_date = parse_date(end_date)
    end_year = end_date.year
    print('随访新建结束年份：', end_year)

    start_year = start_year - 1  # 考虑可能包含前一年的数据

    sf_data_collection = {}

    for year in range(start_year, end_year + 1):
        driver.switch_to.default_content()
        # 切换到第一个 iframe
        first_iframe = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen21"]/iframe'))
        )
        driver.switch_to.frame(first_iframe)

        try:
            year_element = WebDriverWait(driver, 5).until(
                ec.presence_of_element_located(
                    (By.XPATH, f'//*[@id="ext-gen14-gp-year-{year}"]')
                )
            )
        except:
            print(f'{year}年暂无随访记录')
            continue

        year_class = year_element.get_attribute('class')
        if year_class == 'x-grid-group':
            print(f'{year}年已展开')
        else:
            print(f'{year}年未展开，正在展开...')
            year_element.click()
            time.sleep(1)

        # 获取该年份下的所有随访记录元素
        elements = WebDriverWait(driver, 15).until(
            ec.presence_of_all_elements_located(
                (
                    By.XPATH,
                    f"//div[@id='ext-gen14-gp-year-{year}-bd']//div[@class='x-grid3-cell-inner x-grid3-col-1 x-unselectable']",
                )
            )
        )
        print(f'{year}年共有{len(elements)}条随访记录')

        # 遍历该年份下的每条随访记录
        for index in range(len(elements)):
            # 重新获取当前元素列表（避免StaleElementReferenceException）
            current_elements = WebDriverWait(driver, 15).until(
                ec.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        f"//div[@id='ext-gen14-gp-year-{year}-bd']//div[@class='x-grid3-cell-inner x-grid3-col-1 x-unselectable']",
                    )
                )
            )

            if index >= len(current_elements):
                break

            element = current_elements[index]
            element.click()
            time.sleep(1)  # 等待加载

            # 切换到第二个 iframe (随访详情)
            driver.switch_to.default_content()

            second_iframe = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//*[@id="ext-gen21"]/iframe')
                )
            )
            driver.switch_to.frame(second_iframe)

            second_iframe = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//*[@id="ext-gen32"]/iframe')
                )
            )
            driver.switch_to.frame(second_iframe)

            # 获取随访日期作为主键
            try:
                follow_date_element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="dateCreated"]'))
                )
                follow_date = follow_date_element.get_attribute('value')
                print(f'获取到随访日期: {follow_date}')
            except Exception as e:
                print(f'获取随访日期失败: {str(e)}')
                driver.switch_to.default_content()
                driver.switch_to.frame(first_iframe)
                continue

            # 初始化随访数据字典
            sf_data = {}

            # 收缩压
            try:
                sbp_element = WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="sbp"]'))
                )
                sf_data['收缩压'] = sbp_element.get_attribute('value') or '未查'
            except:
                sf_data['收缩压'] = '未查'

            # 舒张压
            try:
                dbp_element = WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="dbp"]'))
                )
                sf_data['舒张压'] = dbp_element.get_attribute('value') or '未查'
            except:
                sf_data['舒张压'] = '未查'

            # 空腹血糖
            try:
                fbg_element = WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="fbg"]'))
                )
                sf_data['空腹血糖'] = fbg_element.get_attribute('value') or '未查'
            except:
                sf_data['空腹血糖'] = '未查'

            # 心率
            try:
                hr_element = WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located(
                        (By.XPATH, '//*[@id="heartRateCur"]')
                    )
                )
                sf_data['心率'] = hr_element.get_attribute('value') or '未查'
            except:
                sf_data['心率'] = '未查'

            # 餐后血糖
            try:
                pbg_element = WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="pbg"]'))
                )
                sf_data['餐后血糖'] = pbg_element.get_attribute('value') or '未查'
            except:
                sf_data['餐后血糖'] = '未查'

            # 糖化血红蛋白
            try:
                hba1c_element = WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="hba1c"]'))
                )
                sf_data['糖化血红蛋白'] = hba1c_element.get_attribute('value') or '未查'
            except:
                sf_data['糖化血红蛋白'] = '未查'

            # 体重
            try:
                weight_element = WebDriverWait(driver, 5).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="weightCur"]'))
                )
                sf_data['体重'] = weight_element.get_attribute('value') or '未查'
            except:
                sf_data['体重'] = '未查'

            # 当前身高
            try:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="height"]'))
                )
                height = element.get_attribute('value')
                sf_data['身高'] = height
            except:
                sf_data['身高'] = '未查'

            # 日吸烟量
            try:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="smAmountCur"]'))
                )
                smoke_amount = element.get_attribute('value')
                sf_data['日吸烟量'] = smoke_amount
            except:
                sf_data['日吸烟量'] = '未查'

            # 日饮酒量
            try:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="dkAmountCur"]'))
                )
                drink_amount = element.get_attribute('value')
                sf_data['日饮酒量'] = drink_amount
            except:
                sf_data['日饮酒量'] = '未查'

            # 运动次数
            try:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="exCycleCur"]'))
                )
                sport_times = element.get_attribute('value')
                sf_data['运动次数'] = sport_times
            except:
                sf_data['运动次数'] = '未查'

            # 运动时间
            try:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, '//*[@id="exTimeCur"]'))
                )
                sport_time = element.get_attribute('value')
                sf_data['运动时间'] = sport_time
            except:
                sf_data['运动时间'] = '未查'

            # 使用随访日期作为键存储数据
            sf_data_collection[follow_date] = sf_data
            # print(f"已保存随访数据 [{follow_date}]: {sf_data}")

            # 返回上级iframe继续处理下一条
            driver.switch_to.default_content()
            first_iframe = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.XPATH, '//*[@id="ext-gen21"]/iframe')
                )
            )
            driver.switch_to.frame(first_iframe)

    return sf_data_collection
