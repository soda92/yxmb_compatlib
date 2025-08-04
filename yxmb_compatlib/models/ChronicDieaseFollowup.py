from pydantic import BaseModel


class ChronicDiseaseFollowupData(BaseModel):
    ehrId: str
    flwId: str
    id: int
    districtCode: str
    flwOrgCode: str
    flwOrgName: str
    flwDoctorName: str
    chronicType: int
    useOld: int
    serviceName: int
    followWay: int # 随访方式
    isGj: int # 是否国家标准
    compliance: int # 服药依从性
    untowardEffect: int # 不良反应
    untowardEffectDes: str # 不良反应描述
    flwSortBp: int # 随访分类-血压
    flwSortBg: int # 随访分类-血糖
    hypoglycemia: int # 低血糖
    symptom: int # 症状
    otherSymptom_text: str # 其他症状描述
    sbp: int # 收缩压
    dbp: int # 舒张压
    height: int # 身高

    weightCur: int # 当前体重
    weightTar: int # 目标体重
    heartRateCur: int # 当前心率
    heartRateTar: int # 目标心率
    otherSign: str # 其他体征
    dorsalisPedis: int # 足背动脉搏动
    dorsalisPedisWeaken: int # 足背动脉搏动减弱
    dorsisPedisDisappear: int # 足背动脉搏动消失
    smAmountCur: int # 当前日吸烟量
    smAmountTar: int # 目标日吸烟量
    dkAmountCur: int # 当前日饮酒量
    dkAmountTar: int # 目标日饮酒量
    exCycleCur: int # 当前运动周期
    exCycleTar: int # 目标运动周期
    exTimeCur: int # 当前运动时间
    exTimeTar: int # 目标运动时间
    stAmountCurTypeCur: int # 当前吸烟类型
    stAmountCurTypeTar: int # 目标吸烟类型
    fhAmountCur: int # 当前家庭成员吸烟量
    fhAmountTar: int # 目标家庭成员吸烟量
    psychological: int # 心理状态
    followBehavior: int # 遵医行为
    fbg: int # 空腹血糖
    pbg: float # 餐后血糖
    hba1c: float # 糖化血红蛋白
    hba1cDate: str # 糖化血红蛋白日期
    tc: int # 总胆固醇
    tg: int # 甘油三酯
    ldlC: int # 低密度脂蛋白胆固醇
    hdlC: int # 高密度脂蛋白胆固醇
    bun: int # 尿素氮
    cr: int # 肌酐
    ccr: int # 肌酐清除率
    malb: int # 尿微量白蛋白
    uran: str # 尿常规
    ecg: str # 心电图
    fundusOculi: str # 眼底检查
    otherTest: str # 其他检查
    nextFlwDate: str # 下次随访日期
    TUBERCULOSIS: dict = {}  # 结核病相关数据，默认为空字典
    referralReason: str = ""  # 转诊原因，默认为空字符串
    referralOrgDept: str = ""  # 转诊机构科室，默认为空字符串