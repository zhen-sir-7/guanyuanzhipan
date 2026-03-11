from app.utils.exceptions_utils import parse_exceptions, is_hs_code_excluded
from app.constants import CTC_LEVELS

def judge_ctc_rcep(product, materials, step_content, exceptions):
    """
    CTC规则：检查非原产材料是否发生规定的HS编码改变，并处理例外排除。
    step_content: 改变类型（CC, CTH, CTSH）
    exceptions: 例外字符串（如 "851712-851718,851720"）
    返回 (是否通过, 建议)
    """
    # 获取产品的HS编码（6位）
    product_hs = product.hs_code

    level = CTC_LEVELS.get(step_content)
    if not level:
        return False, f"不支持的CTC步骤内容：{step_content}"

    # 解析例外
    exception_ranges = parse_exceptions(exceptions)

    # 筛选非原产材料（原产国不是产品原产国）
    non_orig_materials = [m for m in materials if m.origin_country != product.origin_country]

    if not non_orig_materials:
        return True, "无非原产材料，自动满足CTC规则"

    for m in non_orig_materials:
        material_hs = m.hs_code

        # 检查是否被排除
        if is_hs_code_excluded(material_hs, exception_ranges):
            return False, f"原料 {m.material_name} 的HS编码 {material_hs} 属于例外范围，不被认可"

        # 检查改变是否发生
        if material_hs[:level] == product_hs[:level]:
            return False, f"原料 {m.material_name} 的HS编码 {material_hs} 与产品编码 {product_hs} 在{level}位上相同，未发生{step_content}改变"

    return True, f"所有非原产材料均满足{step_content}改变要求"