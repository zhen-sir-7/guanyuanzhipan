def judge_wo(product, materials, step_content=None, exceptions=None):
    """
    完全获得规则：所有原料必须原产。
    step_content 和 exceptions 在此处未使用，但保留参数以保持接口一致。
    """
    for m in materials:
        if m.origin_country != product.origin_country:
            return False, f"原料 {m.material_name} 的原产国 {m.origin_country} 与产品原产国 {product.origin_country} 不一致"
    return True, "所有原料均为原产，满足完全获得"