import re
import time
from datetime import datetime

import dask.dataframe as dd
from yxmb_compatlib.mylib.main import CustomBrowser
import pandas as pd
from selenium.common import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from yxmb_compatlib.comment.envWrite import env_write
from yxmb_compatlib.comment.excle_create import check_and_create_excel
from yxmb_compatlib.comment.write_excle import excel_append
from yxmb_compatlib.comment.登录头 import login
from phis_logging import setup_logging

setup_logging()

folder_path = '执行结果/异常名单.xlsx'
check_and_create_excel(folder_path)
# 检查文件是否包含表头
try:
    existing_data = pd.read_excel(folder_path)
    required_columns = {'身份证号', '异常原因'}
    if not required_columns.issubset(existing_data.columns):
        # 文件没有表头，需要添加表头
        header_df = pd.DataFrame(columns=['身份证号', '异常原因'])
        header_df.to_excel(folder_path, index=False, header=True)
        print("文件没有表头,已添加表头")
except pd.errors.EmptyDataError:
    # 文件为空，需要添加表头
    header_df = pd.DataFrame(columns=['身份证号', '异常原因'])
    header_df.to_excel(folder_path, index=False, header=True)
    print("文件为空,已添加表头")

# 读取已查询数量
try:
    with open('执行结果/env.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        fourth_line = lines[2].strip().split(":")
        # 提取查询数量并去除空白字符
        number = int(fourth_line[-1].strip())
        print('已完成数量:', number)
except FileNotFoundError:
    print("文件不存在，请检查env文件路径是否正确。")
except Exception as e:
    print(f"读取env文件时发生错误：{e}")

# 读取文档/宇信更新数据.xlsx文件，并将其内容保存到df1变量中
df1 = pd.read_excel('文档/宇信更新数据.xlsx', engine='openpyxl')

# 获取表头
headers = df1.columns.tolist()
print("表头:", headers)

data1 = df1.to_dict('records')
max_number = len(data1)
print("总操作数:", max_number)
env_write('执行结果/env.txt', 1, f"总操作数:{max_number}")

# Step 1: 读取 Excel 文件
excel_file = '文档/宇信更新数据.xlsx'
df = pd.read_excel(excel_file, engine='openpyxl', skiprows=range(1, number + 1))

# 将所有列转换为字符串格式
df = df.applymap(str)

# 将所有的NaN替换为空字符串
df.fillna("", inplace=True)

# Step 2: 保存为 CSV 文件，避免科学计数法
csv_file = '文档/宇信更新数据.csv'
df.to_csv(csv_file, index=False)

# Step 3: 使用 dask 读取和处理 CSV 文件
dtypes = {col: 'object' for col in df.columns}
dask_df = dd.read_csv(csv_file, dtype=dtypes)
dask_df = dask_df.fillna("")
data = dask_df.compute().to_dict('records')
sy_number = len(data)
print("剩余操作数:", sy_number)

from pathlib import Path
Path(csv_file).unlink(missing_ok=True)  # 删除临时 CSV 文件

driver = CustomBrowser()

login(driver)
script = """
var element = document.evaluate('//*[@id="navLi_10103"]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
element.click();
"""
driver.execute_script(script)

# 进入iframe
iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, '/phis/app/ehr')]")
driver.switch_to.frame(iframe)

# 包含子机构
WebDriverWait(driver, 10).until(
    ec.visibility_of_element_located(
        (By.XPATH, '/html/body/div[1]/div/div/div/table/tbody/tr[2]/td/table/tbody/tr/td[4]/label/input'))).click()

for index, record in enumerate(data):
    # 记录开始时间
    start_time = time.time()

    sfzh = str(record['身份证号']).strip()
    print('当前处理身份证号:', sfzh)

    env_write('执行结果/env.txt', 2, f'当前处理身份证号:{sfzh}')

    # 切换回主内容
    driver.switch_to.default_content()
    # 进入iframe
    iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, '/phis/app/ehr')]")
    driver.switch_to.frame(iframe)

    card_input = WebDriverWait(driver, 10).until(ec.presence_of_element_located(
        (By.XPATH, '//*[@id="idNumber"]')))
    card_input.clear()
    card_input.send_keys(sfzh)
    time.sleep(.8)
    driver.execute_script("document.getElementById('{}').click();".format('chaxun'))
    time.sleep(1.2)

    try:
        # 等待元素可见并获取该元素
        tsd = WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located((By.XPATH, f'//div[contains(text(), "{sfzh}")]')))
    except:
        number = number + 1
        env_write('执行结果/env.txt', 3, f'已完成数量:{number}')
        print(f'无档案')
        excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + '\t', "异常原因", f"无档案")

        continue

    element = WebDriverWait(driver, 10).until(ec.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/div/div[1]/div[2]/div/div/table/tbody/tr/td[8]/div')))

    disease = element.text
    print('慢病类型:', disease)

    element_xpath = f'//div[contains(text(), "{sfzh}")]'
    script = f"""
                var element = document.evaluate('{element_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (element) {{
                    var event = new MouseEvent('dblclick', {{
                        'view': window,
                        'bubbles': true,
                        'cancelable': true
                    }});
                    element.dispatchEvent(event);
                }}
                """
    driver.execute_script(script)  # 双击进入
    time.sleep(1.5)

    # 切换窗口句柄
    all_handler = driver.window_handles
    new_window = [handler for handler in all_handler if handler != driver.window_handles][-1]
    driver.switch_to.window(new_window)
    driver.maximize_window()

    # 点击左上角小箭头
    WebDriverWait(driver, 10).until(
        ec.visibility_of_element_located((By.XPATH, '//*[@id="ext-gen23"]'))).click()

    # 点击随访服务
    WebDriverWait(driver, 10).until(ec.visibility_of_element_located(
        (By.XPATH, "//dt[text()='随访服务']"))).click()
    try:
        # 点击慢病随访
        WebDriverWait(driver, 10).until(ec.visibility_of_element_located(
            (By.XPATH, "//li[contains(text(), '慢病随访')]"))).click()
    except:
        print('无慢病随访按钮')
        excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + '\t', "异常原因", f"无慢病随访按钮")
        # 获取所有窗口的句柄
        window_handles = driver.window_handles

        # 根据窗口数量关闭多余的窗口
        if len(window_handles) == 3:
            # 关闭后面的两个窗口
            for i in range(1, 3):
                driver.switch_to.window(window_handles[i])
                driver.close()
                print(f"第{i}个窗口已关闭")
        elif len(window_handles) == 2:
            # 关闭后面的一个窗口
            driver.switch_to.window(window_handles[1])
            driver.close()
            print(f"窗口已关闭")

        # 切换回第一个窗口
        driver.switch_to.window(window_handles[0])
        print("已切换为初始窗口")
        number = number + 1
        env_write('执行结果/env.txt', 3, f'已完成数量:{number}')
        print(f"执行数量已由{number - 1}更新为{number}")
        # 记录结束时间
        end_time = time.time()
        # 计算并输出执行时间
        execution_time = end_time - start_time
        print(f"程序执行时间: {execution_time:.2f} 秒")
        continue
    # 切换回主内容
    driver.switch_to.default_content()
    # 切换到第一个 iframe
    first_iframe = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen21"]/iframe')))
    driver.switch_to.frame(first_iframe)

    """
    寻找符合的随访日期
    """
    need_data = record["随访日期"].replace(" 00:00:00", "")
    print("需要更新的随访日期:", need_data)
    need_year = datetime.strptime(need_data, "%Y-%m-%d").year  # 提取年份

    date_list = []
    try:
        # 动态查找包含 need_year 的所有年份元素
        year_cells = WebDriverWait(driver, 5).until(ec.presence_of_all_elements_located(
            (By.XPATH, f'//td/div[text()="{need_year}"]')))  # 使用 f-string 动态插入年份
    except TimeoutException:
        print(f"未找到包含 '{need_year}' 的年份元素")
        excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + '\t', "异常原因", f"未找到{need_year}年随访记录")
        number = number + 1
        env_write('执行结果/env.txt', 3, f'已完成数量:{number}')
        continue

    year_element = WebDriverWait(driver, 5).until(ec.presence_of_element_located(
        (By.XPATH, f'//*[@id="ext-gen14-gp-year-{need_year}"]')))
    year_class = year_element.get_attribute('class')
    if year_class == 'x-grid-group':
        print("年份已展开")
    else:
        print("年份未展开，正在展开...")
        year_element.click()
        time.sleep(1)

    for year_cell in year_cells:
        # 获取年份元素的父级 <tr>，然后在该行内找到日期列
        row = year_cell.find_element(By.XPATH, './ancestor::tr')
        date_cell = row.find_element(By.XPATH, './td[2]/div')  # 找到第二个 <td> 中的日期元素
        date = f"{need_year}-{date_cell.text}"  # 动态拼接日期
        print("已有的随访日期:", date)
        date_list.append(date)

    print(f"{need_year}年所有的随访日期:", date_list)
    for date in date_list:
        print("正在处理日期:", date)

        pattern = r"\d{4}-\d{2}-\d{2}"
        match = re.search(pattern, date)
        date_up = match.group(0)  # 提取匹配的日期

        if date_up == need_data:
            disease = []
            # 检查随访类型
            if "高" in date:
                disease.append("高血压")
            if "糖" in date:
                disease.append("糖尿病")
            print("随访类型:", disease)

            date_up = date_up.replace(f"{need_year}-", "")
            try:
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, f'//div[contains(text(), "{date_up}")]'))
                )
                element.click()
            except StaleElementReferenceException:
                print(f"元素 {date_up} 失效，重新查找")
                element = WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, f'//div[contains(text(), "{date_up}")]'))
                )
                element.click()

            # 切换到第二个 iframe
            first_iframe = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen32"]/iframe')))
            driver.switch_to.frame(first_iframe)

            """
            更新随访里的东西
            """
            from followup_update import followup_update

            arg = ""
            if "高血压" in disease and "糖尿病" not in disease:
                arg = "高血压"
            elif "糖尿病" in disease and "高血压" not in disease:
                arg = "糖尿病"
            elif "高血压" in disease and "糖尿病" in disease:
                arg = "高血压糖尿病"
            if arg != "":
                followup_update(driver, sfzh, record, headers, disease, need_data, arg)
            else:
                print("无慢病")
                excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + '\t', "异常原因", f"无慢病")

            # 切换回主内容
            driver.switch_to.default_content()
            # 切换到第一个 iframe
            first_iframe = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.XPATH, '//*[@id="ext-gen21"]/iframe')))
            driver.switch_to.frame(first_iframe)

    # 获取所有窗口的句柄
    window_handles = driver.window_handles

    # 根据窗口数量关闭多余的窗口
    if len(window_handles) == 3:
        # 关闭后面的两个窗口
        for i in range(1, 3):
            driver.switch_to.window(window_handles[i])
            driver.close()
            print(f"第{i}个窗口已关闭")
    elif len(window_handles) == 2:
        # 关闭后面的一个窗口
        driver.switch_to.window(window_handles[1])
        driver.close()
        print(f"窗口已关闭")

    # 切换回第一个窗口
    driver.switch_to.window(window_handles[0])
    print("已切换为初始窗口")
    number = number + 1
    env_write('执行结果/env.txt', 3, f'已完成数量:{number}')
    print(f"执行数量已由{number-1}更新为{number}")
    # 记录结束时间
    end_time = time.time()
    # 计算并输出执行时间
    execution_time = end_time - start_time
    print(f"程序执行时间: {execution_time:.2f} 秒")

print("程序已执行完成")
env_write("执行结果/env.txt", 6, f'执行完成:1')


