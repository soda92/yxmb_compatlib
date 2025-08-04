import difflib
import random
import time
from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd
from pandas import Timestamp
from selenium.common import StaleElementReferenceException


def get_drink_amount(drink_type, drink_number):
    if drink_type == '啤酒（酒精含量15-40）':
        if (
            drink_number
            == '少量（啤酒<250-500ml/次，色酒100-150ml/次，白酒<25-50ml/次）'
        ):
            return random.randint(5, 10)  # 250-500ml
        elif (
            drink_number
            == '中量（啤酒<500-2500ml/次，色酒100-150ml/次，白酒50-250ml/次）'
        ):
            return random.randint(10, 50)  # 500-2500ml
        elif drink_number == '大量（啤酒>2500ml/次，其它酒>250ml/次）':
            return random.randint(50, 100)  # >2500ml
    elif drink_type == '色酒（酒精含量<15）':
        if (
            drink_number
            == '少量（啤酒<250-500ml/次，色酒100-150ml/次，白酒<25-50ml/次）'
        ):
            return random.randint(2, 3)  # 100-150ml
        elif (
            drink_number
            == '中量（啤酒<500-2500ml/次，色酒100-150ml/次，白酒50-250ml/次）'
        ):
            return random.randint(2, 3)  # 100-150ml
        elif drink_number == '大量（啤酒>2500ml/次，其它酒>250ml/次）':
            return random.randint(5, 10)  # >250ml
    elif drink_type == '白酒（酒精含量≥45）':
        if (
            drink_number
            == '少量（啤酒<250-500ml/次，色酒100-150ml/次，白酒<25-50ml/次）'
        ):
            return random.randint(1, 2)  # 25-50ml
        elif (
            drink_number
            == '中量（啤酒<500-2500ml/次，色酒100-150ml/次，白酒50-250ml/次）'
        ):
            return random.randint(3, 5)  # 50-250ml
        elif drink_number == '大量（啤酒>2500ml/次，其它酒>250ml/次）':
            return random.randint(6, 10)  # >250ml


def is_similar(drug_name, drug_names_set, threshold=0.8):
    """
    判断一个药物名称是否与集合中的任何药物名称相似。

    :param drug_name: 当前待检查的药物名称
    :param drug_names_set: 已知药物名称的集合
    :param threshold: 相似度阈值，默认0.8
    :return: 如果相似的药物存在，则返回True，否则返回False
    """
    for name in drug_names_set:
        # 计算相似度
        similarity = difflib.SequenceMatcher(None, drug_name, name).ratio()

        # 如果相似度达到阈值，返回True
        if similarity >= threshold:
            return True

    # 如果没有找到相似药物，返回False
    return False


def update_exercise_time(sfzh, sport_time, bmi):
    sport_time = int(float(sport_time))
    bmi = float(bmi)
    # 提取出生日期（yyyyMMdd）
    birth_date_str = sfzh[6:14]
    birth_date = datetime.strptime(birth_date_str, '%Y%m%d')
    # 获取当前日期
    today = datetime.today()
    # 计算年龄
    age = today.year - birth_date.year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1  # 还没有过生日，减去一岁
    if bmi >= 24.0:
        is_obese = True
    else:
        is_obese = False

    if age <= 70:
        # if sport_time < 60 and not is_obese:
        #     return sport_time + 20
        # elif sport_time < 50 and is_obese:
        #     return sport_time + 30
        # else:
        #     return sport_time
        if is_obese or sport_time == 0:
            return sport_time + 30
        else:
            return sport_time
    else:
        # if sport_time < 30 and not is_obese:
        #     return sport_time + 20
        # elif sport_time < 20 and is_obese:
        #     return sport_time + 30
        # else:
        #     return sport_time
        if is_obese or sport_time == 0:
            return sport_time + 20
        else:
            return sport_time


def update_staple_food(bmi, staple_food):
    staple_food = int(staple_food)
    bmi = float(bmi)

    if bmi < 18.5:
        if staple_food > 200:
            staple_food = max(staple_food - 50, 200)
        else:
            staple_food = 200
    elif 18.5 <= bmi < 24.0:
        if staple_food > 200:
            staple_food = max(staple_food - 50, 200)
        else:
            staple_food = 200
    elif 24.0 <= bmi < 28.0:
        if staple_food > 200:
            staple_food = max(staple_food - 50, 200)
        else:
            staple_food = staple_food
    else:
        if staple_food > 200:
            staple_food = max(staple_food - 50, 200)
        else:
            staple_food = staple_food

    return staple_food


def safe_find_element(driver, by, value, retries=3):
    for attempt in range(retries):
        try:
            return driver.find_element(by, value)
        except StaleElementReferenceException:
            if attempt < retries - 1:
                time.sleep(1)  # 等待一会再重试
            else:
                raise


# 定义一个处理不同类型的安全比较函数
def safe_key(value):
    # 将所有值转换为字符串进行比较
    # 如果是 Timestamp 类型，先转换为字符串
    if isinstance(value, pd.Timestamp):
        return str(value)  # 你可以根据需要调整格式
    return str(value)  # 将其他类型转换为字符串


def process_date(new_sf_time):
    # 判断 new_sf_time 是否为 datetime 对象
    if isinstance(new_sf_time, datetime):
        # 如果是 datetime 对象，直接进行格式化
        return new_sf_time.strftime('%Y-%m-%d')

    # 如果是字符串，检查是否符合日期格式
    elif isinstance(new_sf_time, str):
        try:
            # 尝试解析不同的日期格式
            # 假设日期格式有几种常见的格式，可以根据需求调整
            if (
                len(new_sf_time) == 10
                and new_sf_time[4] == '-'
                and new_sf_time[7] == '-'
            ):
                # 格式为 'YYYY-MM-DD'
                new_sf_time = datetime.strptime(new_sf_time, '%Y-%m-%d')
                return new_sf_time.strftime('%Y-%m-%d')
            elif (
                len(new_sf_time) == 19
                and new_sf_time[4] == '-'
                and new_sf_time[7] == '-'
                and new_sf_time[10] == ' '
            ):
                # 格式为 'YYYY-MM-DD HH:MM:SS'
                new_sf_time = datetime.strptime(new_sf_time, '%Y-%m-%d %H:%M:%S')
                return new_sf_time.strftime('%Y-%m-%d')
            else:
                raise ValueError('不支持的日期格式')
        except ValueError as e:
            return str(e)

    # 如果既不是字符串也不是 datetime 对象，返回错误信息
    return '输入无效'


def calculate_age(birthdate):
    """根据出生日期计算精确年龄（年、月、日）"""
    today = datetime.today()
    age = today.year - birthdate.year

    # 如果今年生日还没过，年龄减1
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


def hypertension_assessment(dbp, sbp, sfzh, sf_time, people_name, doctor_name):
    # 从身份证中提取出生日期
    birthdate_str = sfzh[6:14]  # 提取年月日部分，例如：19901012
    birthdate = datetime.strptime(birthdate_str, '%Y%m%d')  # 转换为日期对象

    dbp = int(dbp)
    sbp = int(sbp)

    # 计算精确年龄
    age = calculate_age(birthdate)

    # 根据年龄设定血压阈值
    if age >= 65:
        sbp_threshold = 150  # 65岁以上收缩压阈值
        dbp_threshold = 90  # 65岁以上舒张压阈值
    else:
        sbp_threshold = 140  # 65岁以下收缩压阈值
        dbp_threshold = 90  # 65岁以下舒张压阈值

    # 评估血压
    if sbp <= sbp_threshold and dbp <= dbp_threshold:
        return '高血压（血压控制达标）'
    else:
        with open('执行结果/需要追访名单.txt', 'a+', encoding='utf-8') as f:
            f.write(
                f'身份证号-{sfzh}; 舒张压-{dbp}; 收缩压-{sbp}; 随访日期-{sf_time}; 患者姓名-{people_name}; 随访人-{doctor_name}; 血压控制不达标需要追访\n'
            )
        return '高血压（血压控制不达标）'


def diabetes_assessment(blood_glucose, sfzh, sf_time, people_name, doctor_name):
    blood_glucose = float(blood_glucose)
    # 评估血压
    if blood_glucose < 7:
        return '糖尿病（血糖控制达标）'
    else:
        with open('执行结果/需要追访名单.txt', 'a+', encoding='utf-8') as f:
            f.write(
                f'身份证号-{sfzh}; 空腹血糖-{blood_glucose}; 随访日期-{sf_time}; 患者姓名-{people_name}; 随访人-{doctor_name}; 血糖控制不达标需要追访\n'
            )
        return '糖尿病（血糖控制不达标）'


def parse_date(date_value):
    """
    通用日期解析函数（支持12种日期格式）
    支持类型：
    - Pandas Timestamp
    - Python datetime/date
    - numpy.datetime64
    - 字符串（多种格式）
    - Excel序列日期数字
    - Unix时间戳
    """
    # 处理空值
    if pd.isnull(date_value):
        raise ValueError('输入日期值为空')

    # 类型1：Pandas Timestamp
    if isinstance(date_value, Timestamp):
        return date_value.to_pydatetime().replace(tzinfo=None)

    # 类型2：Python datetime对象
    if isinstance(date_value, datetime):
        return date_value

    # 类型3：Python date对象
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time())

    # 类型4：numpy.datetime64
    if isinstance(date_value, np.datetime64):
        return date_value.astype('datetime64[ns]').to_pydatetime()

    # 类型5：字符串日期
    if isinstance(date_value, str):
        # 去除前后空格和特殊字符
        clean_str = date_value.strip().replace('/', '-').replace('\\', '-')

        # 尝试常见日期格式
        formats = [
            '%Y-%m-%d',  # 2023-08-15
            '%Y%m%d',  # 20230815
            '%d-%m-%Y',  # 15-08-2023
            '%m-%d-%Y',  # 08-15-2023
            '%Y-%m-%d %H:%M',  # 2023-08-15 14:30
            '%Y/%m/%d',  # 2023/08/15
            '%d.%m.%Y',  # 15.08.2023
            '%Y年%m月%d日',  # 2023年08月15日
        ]

        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                continue

    # 类型6：Excel序列日期（整数/浮点数）
    try:
        if 0 < float(date_value) < 100000:
            # Excel日期从1900-01-01开始（Windows版本）
            return datetime(1899, 12, 30) + timedelta(days=float(date_value))
    except (ValueError, TypeError):
        pass

    # 类型7：Unix时间戳（秒/毫秒）
    try:
        ts = float(date_value)
        if 1e9 < ts < 2e12:  # 范围：2001-2033年
            return datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
    except (ValueError, TypeError):
        pass

    # 类型8：日期时间字符串（带时区）
    if isinstance(date_value, str) and 'T' in date_value:
        try:
            return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except ValueError:
            pass

    # 最终尝试：dateutil解析（需要安装python-dateutil）
    try:
        from dateutil.parser import parse

        return parse(date_value)
    except ImportError:
        pass
    except (ValueError, OverflowError):
        pass

    raise ValueError(f'无法解析的日期格式：{type(date_value)} - {date_value}')


# 辅助函数：从历史数据中获取最近的有效值
def get_nearest_previous_value(data_list, target_date):
    # 过滤有效数据：日期不超过目标日期且值有效
    valid_data = [
        (date, value)
        for date, value in data_list
        if date <= target_date and value is not None
    ]

    if not valid_data:
        return None

    # 按日期降序排序（最近的日期在前）
    valid_data.sort(key=lambda x: x[0], reverse=True)

    # 返回最近日期的值
    return valid_data[0][1]


# 重构建议池：每条建议都标记适用的疾病类型
advice_pool = [
    # 核心监测建议（根据疾病类型自动选择）
    {'condition': ('高血压', '糖尿病'), 'advice': '定期监测血压、血糖、足背动脉;'},
    {'condition': ('高血压',), 'advice': '定期监测血压、足背动脉;'},
    {'condition': ('糖尿病',), 'advice': '定期监测血糖、足背动脉;'},
    # 核心通用建议（所有患者都适用）
    {
        'condition': ('通用',),
        'advice': '严格遵医嘱用药，注意药物剂量、用法、时间，勿自行更改或停药;',
    },
    {'condition': ('通用',), 'advice': '低盐低脂饮食，每日食盐摄入量不超过5克;'},
    {'condition': ('通用',), 'advice': '避免被动吸烟;'},
    {'condition': ('通用',), 'advice': '保证7-8小时优质睡眠，避免熬夜;'},
    # 糖尿病专用建议
    {'condition': ('糖尿病',), 'advice': '每日监测晨起空腹血糖;'},
    {'condition': ('糖尿病',), 'advice': '学习低血糖识别与处理，随身携带糖果;'},
    {'condition': ('糖尿病',), 'advice': '每年至少1次眼底检查、肾功能检查;'},
    {'condition': ('糖尿病',), 'advice': '足部每日检查，预防糖尿病足;'},
    {'condition': ('糖尿病',), 'advice': '限制精制碳水摄入，增加全谷物比例;'},
    {'condition': ('糖尿病',), 'advice': '学习食物升糖指数(GI)概念;'},
    {'condition': ('糖尿病',), 'advice': '控制餐后2小时血糖在10mmol/L以下;'},
    {'condition': ('糖尿病',), 'advice': '记录血糖监测日记;'},
    # 高血压专用建议
    {'condition': ('高血压',), 'advice': '每日监测晨起空腹血压;'},
    {'condition': ('高血压',), 'advice': '保持情绪稳定，避免情绪剧烈波动;'},
    {'condition': ('高血压',), 'advice': '冬季注意保暖，避免寒冷刺激;'},
    {'condition': ('高血压',), 'advice': '收缩压控制在130mmHg以下;'},
    {'condition': ('高血压',), 'advice': '记录血压监测日记;'},
    # 通用扩展建议
    {'condition': ('通用',), 'advice': '烹饪使用植物油，避免动物油脂;'},
    {'condition': ('通用',), 'advice': '外出携带疾病卡片和应急药物;'},
    {'condition': ('通用',), 'advice': '避免长时间静坐，每小时活动5分钟;'},
    {'condition': ('通用',), 'advice': '出现头晕、心悸、视物模糊立即就医;'},
    {'condition': ('通用',), 'advice': '定期进行心血管风险评估;'},
    {'condition': ('通用',), 'advice': '流感季节前接种疫苗;'},
    # 结尾建议（所有患者都适用）
    {'condition': ('通用',), 'advice': '预防并发症，如有不适立即就医，定期复诊;'},
    {'condition': ('通用',), 'advice': '若控制不佳或出现异常，建议上级医院就诊'},
]


def generate_doctor_advice(mb_type):
    """根据疾病类型生成针对性的医生建议组合"""
    advice_list = []

    # 1. 添加监测建议（根据疾病类型）
    for item in advice_pool:
        if isinstance(item, dict) and all(
            disease in mb_type for disease in item['condition']
        ):
            advice_list.append(item['advice'])
            break

    # 2. 添加核心通用建议（必选）
    core_advices = [
        item['advice']
        for item in advice_pool
        if isinstance(item, dict)
        and '通用' in item['condition']
        and '建议' not in item['advice']
    ]
    # 确保核心建议按顺序添加
    core_advices = core_advices[:4]  # 取前4条核心通用建议
    advice_list.extend(core_advices)

    # 3. 根据疾病类型筛选相关建议
    disease_specific = []
    general_advices = []

    for item in advice_pool:
        if not isinstance(item, dict):
            continue

        # 跳过已经添加的核心建议
        if item['advice'] in advice_list:
            continue

        # 收集特定疾病建议
        if '通用' not in item['condition']:
            if all(disease in mb_type for disease in item['condition']):
                disease_specific.append(item['advice'])

        # 收集通用建议
        elif '通用' in item['condition']:
            general_advices.append(item['advice'])

    # 4. 添加疾病特定建议（优先）
    # 根据疾病数量决定添加数量：单病种2-4条，双病种4-6条
    num_disease = len(mb_type)
    num_to_add = random.randint(2, 4) if num_disease == 1 else random.randint(4, 6)

    if len(disease_specific) > num_to_add:
        advice_list.extend(random.sample(disease_specific, num_to_add))
    else:
        advice_list.extend(disease_specific)

    # 5. 添加通用建议（补充）
    remaining = 15 - len(advice_list)  # 目标总建议数约15条
    if remaining > 0 and general_advices:
        num_general = min(remaining, random.randint(3, 5), len(general_advices))
        advice_list.extend(random.sample(general_advices, num_general))

    # 6. 添加结尾建议
    ending_advices = [
        item['advice']
        for item in advice_pool
        if isinstance(item, dict) and '建议' in item['advice']
    ]
    advice_list.extend(ending_advices)

    # 7. 重新编号并组合
    renumbered_advice = ''
    for i, advice in enumerate(advice_list, 1):
        renumbered_advice += f'{i}.{advice}\n'

    return renumbered_advice
