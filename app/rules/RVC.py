import config
from app.utils.exceptions_utils import parse_exceptions, is_hs_code_excluded
from app.constants import DEFAULT_RVC_THRESHOLD

def calculate_rvc(product, materials, rule_name, threshold=None, exceptions=None):
    """
    计算RVC值，支持例外排除（将例外原料视为原产）。
    返回 (rvc值, 是否通过, 建议)
    """
    fob = product.fob_price
    if fob == 0:
        return 0, False, "FOB价格为0，无法计算RVC"

    # 解析例外
    exception_ranges = parse_exceptions(exceptions) if exceptions else []

    # 计算非原产材料价值（排除例外原料）
    non_orig_value = 0.0
    for m in materials:
        if m.origin_country != product.origin_country:
            # 如果HS编码在例外范围内，视为原产
            if is_hs_code_excluded(m.hs_code, exception_ranges):
                continue
            non_orig_value += m.fob_value

    rvc = (fob - non_orig_value) / fob * 100

    # 确定阈值
    if threshold is None:
        rule_cfg = config.RVC_THRESHOLD.get(rule_name, {})
        methods = rule_cfg.get('methods', [])
        if methods:
            threshold = methods[0].get('threshold', DEFAULT_RVC_THRESHOLD)
        else:
            threshold = DEFAULT_RVC_THRESHOLD

    is_pass = rvc >= threshold
    suggestion = f"RVC计算值为{rvc:.2f}%，阈值{threshold}%，" + ("通过" if is_pass else "不通过")
    return rvc, is_pass, suggestion