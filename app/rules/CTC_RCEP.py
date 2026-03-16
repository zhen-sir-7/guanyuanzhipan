from app.utils.exceptions_utils import parse_exceptions, is_hs_code_excluded
from app.constants import CTC_LEVELS


# 获取RCEP成员国列表（示例，实际应从数据库或配置文件读取）
def get_member_countries():
    # 此处仅为示例，请根据实际情况替换
    return ['中国', '日本', '韩国', '澳大利亚', '新西兰', '越南', '泰国', '马来西亚', '新加坡', '印度尼西亚', '菲律宾',
            '文莱', '老挝', '柬埔寨', '缅甸']


def judge_ctc_rcep(product, materials, step_content, exceptions, use_accumulation=True):

    product_hs = product.hs_code
    product_origin = product.origin_country

    level = CTC_LEVELS.get(step_content)
    if not level:
        return False, f"不支持的CTC步骤内容：{step_content}"

    # 解析例外范围
    exception_ranges = parse_exceptions(exceptions)

    # 获取协定成员国列表（如果启用累积）
    member_countries = get_member_countries() if use_accumulation else []

    # 筛选非原产材料：原产国既不是产品原产国，也不属于成员国
    non_orig_materials = []
    accumulated_materials = []  # 记录因累积而视为原产的材料
    for m in materials:
        if m.origin_country == product_origin:
            continue  # 原产材料
        if use_accumulation and m.origin_country in member_countries:
            accumulated_materials.append(m)  # 因累积规则视为原产
            continue
        non_orig_materials.append(m)

    # 如果没有非原产材料，直接通过
    if not non_orig_materials:
        msg = "无非原产材料，自动满足CTC规则"
        if accumulated_materials:
            msg += f"（{len(accumulated_materials)}种原料因累积规则被视为原产）"
        return True, msg

    # 检查每个非原产材料
    for m in non_orig_materials:
        material_hs = m.hs_code
        material_name = m.material_name

        # 检查是否被例外排除
        if is_hs_code_excluded(material_hs, exception_ranges):
            return False, f"原料 {material_name} 的HS编码 {material_hs} 属于例外范围，不被认可"

        # 检查HS编码是否发生所需改变
        if material_hs[:level] == product_hs[:level]:
            return False, f"原料 {material_name} 的HS编码 {material_hs} 与产品编码 {product_hs} 在{level}位上相同，未发生{step_content}改变"

    # 所有非原产材料均满足
    msg = f"所有非原产材料均满足{step_content}改变要求"
    if accumulated_materials:
        msg += f"（{len(accumulated_materials)}种原料因累积规则被视为原产）"
    return True, msg