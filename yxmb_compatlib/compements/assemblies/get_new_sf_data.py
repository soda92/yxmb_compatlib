import random
from datetime import datetime
from compements.tool import get_nearest_previous_value


# 函数：根据不同优先级选择数据
def select_data_for_field(field_name, new_sf_date, mz_data, tj_data, mb_data):
    selected_data = None
    from_mz = False  # 标志位，表示数据是否来自门诊
    new_sf_date_dt = datetime.strptime(new_sf_date, '%Y-%m-%d')

    # 1. 优先选择与新建的随访日期一致的门诊数据
    for mz in mz_data:
        if mz.get('随访日期:') == new_sf_date:  # 使用get避免KeyError
            selected_data = mz.get(field_name)  # 使用get避免KeyError
            if (
                selected_data is not None
                and selected_data != ''
                and selected_data != '未查'
            ):
                from_mz = True  # 数据来自门诊
                break

    # 2. 如果没有，选择同月的体检数据
    if not from_mz and (
        selected_data is None or selected_data == '' or selected_data == '未查'
    ):
        tj_date = tj_data.get('体检日期')  # 使用get避免KeyError
        if tj_date:
            tj_date_dt = datetime.strptime(tj_date, '%Y-%m-%d')
            if (
                tj_date_dt.year == new_sf_date_dt.year
                and tj_date_dt.month == new_sf_date_dt.month
            ):
                selected_data = tj_data.get(field_name)  # 使用get避免KeyError

    # 3. 如果没有符合条件的门诊数据和体检数据，选择档案数据
    if not from_mz and (
        selected_data is None or selected_data == '' or selected_data == '未查'
    ):
        selected_data = mb_data.get(field_name)  # 使用get避免KeyError

    return selected_data, from_mz  # 返回数据和标志位


def get_new_sf_data(mb_data, mz_data, tj_data, n_sf_time, sf_data, sfzh):
    # 定义各字段的合理范围
    RANGES = {
        '身高': (90, 300),  # 单位：cm
        '体重': (30, 200),  # 单位：kg
        '收缩压': (70, 220),  # 单位：mmHg
        '舒张压': (40, 140),  # 单位：mmHg
        '心率': (45, 120),  # 单位：次/分钟
        '腰围': (50, 150),  # 单位：cm
    }

    # 记录超出范围的异常
    def check_range(field, value, source):
        """检查值是否在合理范围内，不在则记录异常并修正"""
        if value is None or value == '未查':
            return value

        min_val, max_val = RANGES[field]

        # 转换值为浮点数或整数
        try:
            num_val = float(value) if field in ['身高', '体重'] else int(float(value))
        except ValueError:
            return value

        # 检查范围
        if num_val < min_val or num_val > max_val:
            # 记录异常
            with open('./执行结果/字段值超出范围.txt', 'a+', encoding='utf-8') as f:
                f.write(
                    f'{sfzh} {field}异常: 值({num_val})超出合理范围[{min_val}-{max_val}]，数据来源: {source}\n'
                )
                f.write(f'  随访日期: {n_sf_time}\n\n')

            # 修正为边界值
            return max(min_val, min(num_val, max_val))
        return num_val

    current_year = n_sf_time[:4]

    # 根据规则为每个字段选择数据
    selected_data = {'随访日期': n_sf_time}

    # 业务： 随访的身高体重从档案里调数据 别从门诊记录里
    # 身高
    height, from_mz = mb_data.get('身高'), False
    existing_height_values = [
        (date, float(v['身高']))
        for date, v in sf_data.items()
        if v['身高'] is not None and v['身高'] != '未查'
    ]
    existing_height_values.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))

    # 检查身高差距 - 只有在有历史数据时才比较
    if height is not None and existing_height_values:
        last_height = existing_height_values[-1][1]
        height_diff = abs(float(height) - last_height)
        if height_diff > 0:  # 差距大于10cm
            # 记录异常情况
            with open('./执行结果/身高体重异常记录.txt', 'a+', encoding='utf-8') as f:
                f.write(
                    f'{sfzh}身高异常: 本次身高({height}cm)与最近一次身高({last_height}cm)差距大于0cm (差距: {height_diff:.1f}cm)\n'
                )
                f.write(f'  最近一次随访时间: {existing_height_values[-1][0]}\n')
                f.write(
                    f'  历史身高数据: {[(d, f"{v}cm") for d, v in existing_height_values]}\n'
                )
                f.write(f'  数据来源: {"门诊" if from_mz else "档案/体检"}\n\n')
    source = '门诊' if from_mz else '档案/体检'
    check_range('身高', height, source)
    selected_data['身高'] = height

    # 业务：随访的身高体重从档案里调数据 别从门诊记录里
    # 体重
    weight, from_mz = mb_data.get('体重'), False
    existing_weight_values = [
        (date, float(v['体重']))
        for date, v in sf_data.items()
        if v['体重'] is not None and v['体重'] != '未查'
    ]
    existing_weight_values.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))

    # 提取今年已有的体重值（不包含本次随访）
    current_year_weights = {
        float(v['体重'])
        for date, v in sf_data.items()
        if date.startswith(current_year) and v['体重'] not in [None, '未查']
    }

    print('根据档案、门诊、体检选出的体重:', weight)
    print('以往随访的体重:', existing_weight_values)

    # 检查体重差距 - 只有在有历史数据时才比较
    if weight is not None and existing_weight_values:
        last_weight = existing_weight_values[-1][1]
        weight_diff = abs(float(weight) - last_weight)
        if weight_diff > 10:  # 差距大于10kg
            # 记录异常情况
            with open('./执行结果/身高体重异常记录.txt', 'a+', encoding='utf-8') as f:
                f.write(
                    f'{sfzh}体重异常: 本次体重({weight}kg)与最近一次体重({last_weight}kg)差距大于10kg (差距: {weight_diff:.1f}kg)\n'
                )
                f.write(f'  最近一次随访时间: {existing_weight_values[-1][0]}\n')
                f.write(
                    f'  历史体重数据: {[(d, f"{v}kg") for d, v in existing_weight_values]}\n'
                )
                f.write(f'  数据来源: {"门诊" if from_mz else "档案/体检"}\n\n')

    # 新体重生成逻辑（增加季节因素）
    if existing_weight_values:
        last_weight = existing_weight_values[-1][1]
        last_date = existing_weight_values[-1][0]

        # 获取上次随访和当前随访的季节
        last_month = datetime.strptime(last_date, '%Y-%m-%d').month
        current_month = datetime.strptime(selected_data['随访日期'], '%Y-%m-%d').month

        # 季节判断函数
        def get_season(month):
            if month in [12, 1, 2]:
                return 'winter'
            if month in [6, 7, 8]:
                return 'summer'
            return None

        last_season = get_season(last_month)
        current_season = get_season(current_month)

        # 如果选中的体重不在今年记录中，直接使用
        if weight is not None and float(weight) not in current_year_weights:
            selected_data['体重'] = float(weight)
        else:
            # 生成与今年所有记录不同的体重
            attempts = 0
            while attempts < 20:  # 防止无限循环
                # 根据季节调整变化方向
                if last_season == 'winter' and current_season == 'summer':
                    # 冬季转夏季：体重应减少
                    change = -random.choice(
                        [0.5, 1.0, 1.5, 2.0, 2.5]
                    )  # 增加0.5~3kg  # 减少0.5~3kg
                elif last_season == 'summer' and current_season == 'winter':
                    # 夏季转冬季：体重应增加
                    change = random.choice([0.5, 1.0, 1.5, 2.0, 2.5])  # 增加0.5~3kg
                else:
                    # 其他季节：保持原有随机变化
                    change = random.choice([-2.5, -2.0, -1.5, -1.0, 1.0, 1.5, 2.0, 2.5])

                new_weight = round(last_weight + change, 1)

                # 确保新体重不在今年已有记录中
                if new_weight not in current_year_weights:
                    selected_data['体重'] = new_weight
                    break

                attempts += 1
            else:
                # 如果多次尝试仍冲突，使用选中值或最近值
                selected_data['体重'] = (
                    float(weight) if weight is not None else last_weight
                )
    else:
        # 第一次随访
        selected_data['体重'] = float(weight) if weight is not None else None

    source = '门诊' if from_mz else '档案/体检'
    check_range('体重', weight, source)

    # 收缩压
    sbp, from_mz = select_data_for_field('收缩压', n_sf_time, mz_data, tj_data, mb_data)
    sbp = int(float(sbp))
    existing_systolic_values = {
        int(v['收缩压'])
        for date_str, v in sf_data.items()
        if date_str.startswith(current_year)  # 添加年份过滤条件
        and v['收缩压'] is not None
        and v['收缩压'] != '未查'
    }

    print('根据档案、门诊、体检选出的收缩压:', sbp)
    print('以往随访的收缩压:', existing_systolic_values)

    # if not from_mz:  # 如果数据不是来自门诊，才进行后续的判断和随机生成
    if sbp in existing_systolic_values:
        sbp = random.randint(115, 138)
        while sbp in existing_systolic_values:
            sbp = random.randint(115, 138)
    # else:
    #     sbp = sbp  # 数据来自门诊，直接使用
    selected_data['收缩压'] = sbp
    source = '门诊' if from_mz else '档案/体检'
    check_range('收缩压', sbp, source)

    # 舒张压
    dbp, from_mz = select_data_for_field('舒张压', n_sf_time, mz_data, tj_data, mb_data)
    dbp = int(float(dbp))
    # existing_diastolic_values = {int(v['舒张压']) for v in sf_data.values() if
    #                              v['舒张压'] is not None and v['舒张压'] != "未查"}

    existing_diastolic_values = {
        int(v['舒张压'])
        for date_str, v in sf_data.items()
        if date_str.startswith(current_year)  # 添加年份过滤条件
        and v['舒张压'] is not None
        and v['舒张压'] != '未查'
    }

    print('根据档案、门诊、体检选出的舒张压:', dbp)
    print('以往随访的舒张压:', existing_diastolic_values)

    # if not from_mz:  # 如果数据不是来自门诊，才进行后续的判断和随机生成
    if dbp in existing_diastolic_values:
        try:
            min_diastolic = max(65, int(float(sbp)) - 60)
            max_diastolic = min(85, int(float(sbp)))
            dbp = random.randint(min_diastolic, max_diastolic)
        except:
            min_diastolic = 65
            max_diastolic = 85
        while dbp in existing_diastolic_values:
            dbp = random.randint(min_diastolic, max_diastolic)
    # else:
    #     dbp = dbp  # 数据来自门诊，直接使用
    selected_data['舒张压'] = dbp
    source = '门诊' if from_mz else '档案/体检'
    check_range('舒张压', dbp, source)

    # 心率
    heart_rate, from_mz = select_data_for_field(
        '心率', n_sf_time, mz_data, tj_data, mb_data
    )
    # existing_heart_rate_values = {int(v['心率']) for v in sf_data.values() if v['心率'] != "未查"}

    existing_heart_rate_values = {
        int(v['心率'])
        for date_str, v in sf_data.items()
        if date_str.startswith(current_year)  # 添加年份过滤条件
        and v['心率'] is not None
        and v['心率'] != '未查'
    }

    print('根据档案、门诊、体检选出的心率:', heart_rate)
    print('以往随访的心率:', existing_heart_rate_values)

    # if not from_mz:  # 如果数据不是来自门诊，才进行后续的判断和随机生成
    if heart_rate is None or heart_rate in existing_heart_rate_values:
        heart_rate = random.randint(60, 100)
        while heart_rate in existing_systolic_values:
            heart_rate = random.randint(60, 100)
    # else:
    #     heart_rate = heart_rate  # 数据来自门诊，直接使用
    selected_data['心率'] = heart_rate
    source = '门诊' if from_mz else '档案/体检'
    check_range('心率', heart_rate, source)

    # 腰围
    waistline, from_mz = select_data_for_field(
        '腰围', n_sf_time, mz_data, tj_data, mb_data
    )
    change = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
    if isinstance(waistline, str):
        waistline = int(float(waistline))
    new_waistline = waistline + change
    selected_data['腰围'] = new_waistline
    source = '门诊' if from_mz else '档案/体检'
    check_range('腰围', waistline, source)

    # 日吸烟量
    existing_smoke_values = [
        (date, float(v['日吸烟量']))
        for date, v in sf_data.items()
        if v['日吸烟量'] is not None and v['日吸烟量'] != '未查'
    ]
    smoke_amount = get_nearest_previous_value(existing_smoke_values, n_sf_time)

    if smoke_amount is None:
        smoke_amount, from_mz = select_data_for_field(
            '日吸烟量', n_sf_time, mz_data, tj_data, mb_data
        )
    selected_data['日吸烟量'] = int(float(smoke_amount))

    # 日饮酒量
    existing_drink_values = [
        (date, float(v['日饮酒量']))
        for date, v in sf_data.items()
        if v['日饮酒量'] is not None and v['日饮酒量'] != '未查'
    ]
    drink_amount = get_nearest_previous_value(existing_drink_values, n_sf_time)
    if drink_amount is None:
        drink_amount, from_mz = select_data_for_field(
            '日饮酒量', n_sf_time, mz_data, tj_data, mb_data
        )

    selected_data['日饮酒量'] = int(float(drink_amount))

    # 运动次数
    existing_sport_values = [
        (date, float(v['运动次数']))
        for date, v in sf_data.items()
        if v['运动次数'] is not None and v['运动次数'] != '未查'
    ]
    sport_times = get_nearest_previous_value(existing_sport_values, n_sf_time)
    if sport_times is None:
        sport_times, from_mz = select_data_for_field(
            '运动次数', n_sf_time, mz_data, tj_data, mb_data
        )
    selected_data['运动次数'] = int(float(sport_times))

    # 运动时间
    existing_sport_values = [
        (date, float(v['运动时间']))
        for date, v in sf_data.items()
        if v['运动时间'] is not None and v['运动时间'] != '未查'
    ]
    sport_time = get_nearest_previous_value(existing_sport_values, n_sf_time)
    if sport_time is None:
        sport_time, from_mz = select_data_for_field(
            '运动时间', n_sf_time, mz_data, tj_data, mb_data
        )
    selected_data['运动时间'] = int(float(sport_time))

    # 主食量
    food_amount, from_mz = select_data_for_field(
        '主食量', n_sf_time, mz_data, tj_data, mb_data
    )
    try:
        selected_data['主食量'] = int(float(food_amount)) * 3
    except:
        selected_data['主食量'] = 300

    # 摄盐情况
    salt, from_mz = select_data_for_field(
        '摄盐情况', n_sf_time, mz_data, tj_data, mb_data
    )
    selected_data['摄盐情况'] = salt

    # 空腹血糖
    has_diabetes = '糖尿病' in mb_data.get('疾病史', '')
    glucose_range = (5.9, 6.9) if has_diabetes else (5.2, 6.1)
    glucose, from_mz = select_data_for_field(
        '空腹血糖', n_sf_time, mz_data, tj_data, mb_data
    )
    # existing_glucose_values = {float(v['空腹血糖']) for v in sf_data.values() if v['空腹血糖'] != "未查"}

    existing_glucose_values = {
        int(float(v['空腹血糖']))
        for date_str, v in sf_data.items()
        if date_str.startswith(current_year)  # 添加年份过滤条件
        and v['空腹血糖'] is not None
        and v['空腹血糖'] != '未查'
    }

    # if not from_mz:
    # 先将 glucose 转换为浮点数（如果不是 None）
    if glucose is not None:
        try:
            glucose = float(glucose)
        except (ValueError, TypeError):
            glucose = None

    # 检查 glucose 是否为 None 或已经存在于 existing_glucose_values 中
    if (
        glucose is None
        or glucose in existing_glucose_values
        or not (glucose_range[0] <= glucose <= glucose_range[1])
    ):
        # 如果不在范围内或重复，重新生成一个不重复且在范围内的值
        glucose = round(random.uniform(*glucose_range), 1)
        while glucose in existing_glucose_values or not (
            glucose_range[0] <= glucose <= glucose_range[1]
        ):
            glucose = round(random.uniform(*glucose_range), 1)
    else:
        glucose = glucose
    # else:
    #     mz_glucose = float(glucose)
    #     print(f"来源于门诊的空腹血糖:{mz_glucose}")
    #     if mz_glucose >= 7.0:
    #         print("门诊空腹血糖大于7.0，重新生成")
    #         glucose = round(random.uniform(*glucose_range), 1)
    #         while glucose in existing_glucose_values or not (glucose_range[0] <= glucose <= glucose_range[1]):
    #             glucose = round(random.uniform(*glucose_range), 1)
    #         with open("执行结果/门诊空腹血糖大于7.0，重新生成名单.txt", "a+", encoding="utf-8") as f:
    #             f.write(f"{sfzh}---门诊空腹血糖{mz_glucose}大于7.0---重新选择为{glucose}\n")
    #     else:
    #         glucose = mz_glucose
    #     glucose = glucose
    selected_data['空腹血糖'] = glucose

    return selected_data
