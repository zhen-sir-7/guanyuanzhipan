def judge_active_50(product):
    total = product.active_ingredient_total_weight
    origin = product.active_ingredient_origin_weight

    # 检查数据有效性
    if total is None or origin is None:
        return False, "产品缺少活性成分重量信息，无法判定"

    if total <= 0:
        return False, "活性成分总重量必须大于0"

    if origin < 0 or origin > total:
        return False, f"原产活性成分重量({origin})超出有效范围(0~{total})"

    ratio = (origin / total) * 100
    if ratio >= 50:
        return True, f"原产活性成分占比 {ratio:.2f}%，满足≥50%要求"
    else:
        return False, f"原产活性成分占比 {ratio:.2f}%，不满足≥50%要求"