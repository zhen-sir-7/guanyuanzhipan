def judge_dm(product, materials, step_content=None, exceptions=None):
    """
    直接材料规则示例：检查特定加工工序。
    若需例外，可解析 exceptions 进行排除（本例未实现）。
    """
    # 假设 step_content 为要求的工序名称
    if step_content and product.specific_process:
        if step_content.lower() in product.specific_process.lower():
            return True, f"满足特定加工工序要求：{step_content}"
        else:
            return False, f"未包含要求的特定加工工序：{step_content}"
    return True, "无直接材料判定要求或已满足"