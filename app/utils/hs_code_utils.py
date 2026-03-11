def standardize_hs_code(hs_code):
    """
    将输入的HS编码标准化为纯数字，长度4-10位。
    去除所有非数字字符，如果结果长度小于4位或大于10位，视为错误。
    """
    if not hs_code:
        raise ValueError("HS编码不能为空")
    clean = ''.join(filter(str.isdigit, str(hs_code)))
    if len(clean) < 4 or len(clean) > 10:
        raise ValueError(f"HS编码长度必须为4-10位数字，当前为{len(clean)}位")
    return clean