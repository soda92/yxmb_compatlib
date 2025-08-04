import time
import numpy as np
import re
from selenium.webdriver.remote.webdriver import WebDriver


def get_value_by_aliases(record, headers, canonical_name, aliases_map):
    """
    根据标准名在别名映射中查找所有可能的列名，并从记录中获取值。
    :param record: 当前行的数据字典。
    :param headers: Excel文件的实际列标题列表。
    :param canonical_name: 程序内部使用的标准字段名 (e.g., 'sbp')。
    :param aliases_map: 从TOML加载的列别名配置。
    :return: (value, found_header) or (None, None)
    """
    possible_names = aliases_map.get(canonical_name, [canonical_name])
    for name in possible_names:
        if name in headers:
            return record.get(name), name
    return None, None


def followup_update(driver: WebDriver, sfzh, record, headers, disease, need_data, diease_type):
    """
    使用JavaScript直接发送XHR请求来更新随访数据，以提高速度和稳定性。
    """
    from yxmb_compatlib.config import load_config
    from yxmb_compatlib.comment.write_excle import excel_append, excel_append2
    import json
    from pydantic import ValidationError
    from .models.ChronicDieaseFollowup import ChronicDiseaseFollowupData

    from pathlib import Path
    Path("main.html").write_text(encoding='utf8', data=driver.page_source)

    config = load_config()
    aliases = config.get("column_aliases", {})

    # --- 内部辅助函数 ---
    def get_val(canonical_name, default_val=None):
        """从记录中获取值，如果不存在则返回默认值."""
        val, _ = get_value_by_aliases(record, headers, canonical_name, aliases)
        # 处理空值、NaN等情况
        if val is None or (isinstance(val, str) and val.strip().lower() in ["", "nan"]):
            return default_val
        if isinstance(val, float) and np.isnan(val):
            return default_val
        return val

    def map_value(value, mapping, default_if_unmapped=None):
        """将文本值映射到代码."""
        if value is None:
            return default_if_unmapped
        for key, code in mapping.items():
            if key in str(value):
                return code
        return default_if_unmapped

    # --- 1. 从页面提取动态ID和基本信息 ---
    try:
        print("正在从页面提取动态ID...")
        ehr_id = driver.execute_script("return document.getElementById('ehrId').value;")
        flw_id = driver.execute_script("return document.getElementById('flwId').value;")
        district_code, flw_org_code = re.findall("orgCode *: *'(.*)'", driver.page_source)
        flw_org_name = driver.execute_script("return document.getElementsByName('flwOrgName')[0].value;")
        flw_doctor_name = driver.execute_script("return document.getElementsByName('flwDoctorName')[0].value;")
        print(f"ehrId: {ehr_id}, flwId: {flw_id}")
    except Exception as e:
        print(f"错误：无法从页面提取关键ID: {e}")
        excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + "\t", "异常原因", "无法从页面提取关键ID")
        return

    # --- 2. 构建请求体 (Payload) ---
    print("正在构建请求数据...")

    # 定义值到代码的映射
    follow_way_map = {"门诊": "1", "家庭": "2", "电话": "3"}
    compliance_map = {"规律": "1", "间断": "2", "不服药": "3"}
    untoward_effect_map = {"无": "1", "有": "2"}
    category_map = {"控制满意": "1", "控制不满意": "2", "不良反应": "3", "并发症": "4"}
    hypoglycemia_map = {"无": "1", "偶尔": "2", "频繁": "3"}
    st_amount_map = {"轻": "1", "中": "2", "重": "3"}
    psychological_map = {"良好": "1", "一般": "2", "差": "3"}
    
    # 症状映射 (注意：这是一个多选，但请求体中只有一个symptom字段，通常是取第一个非“无”的值)
    # 简化处理：如果Excel中包含多个，我们按顺序查找并映射第一个找到的。
    # 实际的网页JS可能会将多个值组合，但根据示例，它只发送一个数字。
    symptom_map = {
        "无症状": "1", "头痛头晕": "2", "恶心呕吐": "3", "眼花耳鸣": "4", "呼吸困难": "5",
        "心悸胸闷": "6", "鼻衄出血不止": "7", "四肢发麻": "8", "下肢水肿": "9", "其他": "10"
        # ... 可根据需要添加更多糖尿病症状
    }

    payload = {
        "ehrId": ehr_id,
        "flwId": flw_id,
        "id": flw_id, # 通常id和flwId相同
        "districtCode": district_code,
        "flwOrgCode": flw_org_code,
        "flwOrgName": flw_org_name,
        "flwDoctorName": flw_doctor_name,
        "chronicType": "3" if diease_type == "高糖" else ("1" if diease_type == "高血压" else "2"),
        "useOld": "0",
        "serviceName": "1",

        # --- 从Excel映射的字段 ---
        "followWay": map_value(get_val("follow_way"), follow_way_map, "1"),
        "isGj": "1" if "是" in str(get_val("is_national_standard", "否")) else "0",
        "compliance": map_value(get_val("compliance"), compliance_map, "1"),
        "untowardEffect": map_value(get_val("untoward_effect"), untoward_effect_map, "1"),
        "untowardEffectDes": get_val("untoward_effect_desc", ""),
        
        "flwSortBp": map_value(get_val("followup_category_bp"), category_map, "1"),
        "flwSortBg": map_value(get_val("followup_category_bg"), category_map, "1"),
        "hypoglycemia": map_value(get_val("hypoglycemia"), hypoglycemia_map, "1"),
        
        "symptom": map_value(get_val("symptom"), symptom_map, "1"),
        "otherSymptom_text": get_val("symptom_desc", ""),

        # 体征 (使用-1作为默认空值)
        "sbp": get_val("sbp", -1),
        "dbp": get_val("dbp", -1),
        "height": get_val("height", -1),
        "weightCur": get_val("weight_cur", -1),
        "weightTar": get_val("weight_tar", -1),
        "heartRateCur": get_val("heart_rate_cur", -1),
        "heartRateTar": get_val("heart_rate_tar", -1),
        "otherSign": get_val("other_sign", ""),

        # 生活方式
        "smAmountCur": get_val("sm_amount_cur", -1),
        "smAmountTar": get_val("sm_amount_tar", -1),
        "dkAmountCur": get_val("dk_amount_cur", -1),
        "dkAmountTar": get_val("dk_amount_tar", -1),
        "exCycleCur": get_val("ex_cycle_cur", -1),
        "exCycleTar": get_val("ex_cycle_tar", -1),
        "exTimeCur": get_val("ex_time_cur", -1),
        "exTimeTar": get_val("ex_time_tar", -1),
        "stAmountCurTypeCur": map_value(get_val("st_amount_cur"), st_amount_map, "1"),
        "stAmountCurTypeTar": map_value(get_val("st_amount_tar"), st_amount_map, "1"),
        "fhAmountCur": get_val("fh_amount_cur", -1),
        "fhAmountTar": get_val("fh_amount_tar", -1),
        "psychological": map_value(get_val("psychological"), psychological_map, "1"),
        "followBehavior": map_value(get_val("follow_behavior"), psychological_map, "1"), # 遵医行为和心理调整用同一个映射

        # 辅助检查
        "fbg": get_val("fbg", -1),
        "pbg": get_val("pbg", -1),
        "hba1c": get_val("hba1c", -1),
        "tc": get_val("tc", -1),
        "tg": get_val("tg", -1),
        "ldlC": get_val("ldl_c", -1),
        "hdlC": get_val("hdl_c", -1),
        "bun": get_val("bun", -1),
        "cr": get_val("cr", -1),
        "ccr": get_val("ccr", -1),
        "malb": get_val("malb", -1),
        "uran": get_val("uran", ""),
        "ecg": get_val("ecg", ""),
        "fundusOculi": get_val("fundus_oculi", ""),
        "otherTest": get_val("other_test", ""),

        # 转诊
        "referralReason": get_val("referral_reason", ""),
        "referralOrgDept": get_val("referral_org_dept", ""),
        
        # 其他
        "nextFlwDate": get_val("next_flw_date", ""), # 确保Excel中有下次随访日期列
    }

    # --- 2.5 使用Pydantic模型验证数据 ---
    try:
        print("正在使用Pydantic模型验证数据...")
        validated_data = ChronicDiseaseFollowupData(**payload)
        # 将验证和转换后的数据转回字典以用于JS
        payload_to_send = validated_data.model_dump()
        print("数据验证通过。")
    except ValidationError as e:
        print(f"数据验证失败: {e}")
        # 将详细的验证错误写入日志
        error_details = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + "\t", "异常原因", f"数据验证失败: {error_details}")
        return


    # --- 3. 定义并执行JavaScript Fetch请求 ---
    # URLSearchParams会自动处理值的URL编码
    js_script = f"""
    const payload = {json.dumps(payload_to_send)};
    const formData = new URLSearchParams();
    for (const key in payload) {{
        formData.append(key, payload[key]);
    }}

    const url = '/phis/app/svc/flw/chronic/update';
    const callback = arguments[arguments.length - 1];

    fetch(url, {{
        method: 'POST',
        headers: {{
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }},
        body: formData
    }})
    .then(response => response.json())
    .then(data => callback({{success: true, data: data}}))
    .catch(error => callback({{success: false, error: error.toString()}}));
    """

    print("正在发送更新请求...")
    try:
        # 使用异步脚本执行，等待fetch完成
        result = driver.execute_async_script(js_script)

        # --- 4. 处理返回结果 ---
        if result and result.get('success'):
            response_data = result.get('data', {})
            if response_data.get('code') == 200:
                print(f"更新成功: {response_data.get('body', '无详细信息')}")
                excel_append2("执行结果/更新结果.xlsx", ["身份证号", "随访日期"], [sfzh, need_data])
            else:
                error_msg = response_data.get('body') or f"服务器返回代码 {response_data.get('code')}"
                print(f"更新失败: {error_msg}")
                excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + "\t", "异常原因", f"保存失败: {error_msg}")
        else:
            error_info = result.get('error', '未知JavaScript错误')
            print(f"请求执行失败: {error_info}")
            excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + "\t", "异常原因", f"请求执行失败: {error_info}")

    except Exception as e:
        print(f"执行JavaScript或处理结果时发生严重错误: {e}")
        excel_append("执行结果/异常名单.xlsx", "身份证号", sfzh + "\t", "异常原因", f"脚本执行错误: {e}")

    time.sleep(1) # 短暂等待，以防操作过快
