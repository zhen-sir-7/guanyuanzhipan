import pandas as pd
from app.utils.hs_code_utils import standardize_hs_code

def validate_rule_excel(file_path):
    """
    校验规则Excel文件（新Rule表）
    期望列：hs_code, product_description, rule_name, step_order, step_type,
            step_content, threshold_value, exceptions
    返回 (是否通过, 错误信息列表, 有效数据列表)
    """
    errors = []
    valid_data = []
    required_columns = ['hs_code', 'rule_name', 'step_order', 'step_type']

    try:
        df = pd.read_excel(file_path)
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"缺少必要列：{col}")
                return False, errors, valid_data

        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel行号（从2开始）
            hs_code = str(row.get('hs_code', '')).strip()
            product_desc = row.get('product_description')
            rule_name = str(row.get('rule_name', '')).strip()
            step_order = row.get('step_order')
            step_type = str(row.get('step_type', '')).strip()
            step_content = row.get('step_content')
            threshold = row.get('threshold_value')
            exceptions = row.get('exceptions')

            # 标准化HS编码
            try:
                std_hs = standardize_hs_code(hs_code)
            except ValueError as e:
                errors.append(f"第{row_num}行：{str(e)}")
                continue

            # step_order 必须为整数
            try:
                step_order = int(step_order)
            except:
                errors.append(f"第{row_num}行：step_order必须为整数")
                continue

            # 阈值必须为数字（如果提供）
            if threshold is not None and pd.notna(threshold):
                try:
                    threshold = float(threshold)
                except:
                    errors.append(f"第{row_num}行：threshold_value必须为数字")
                    continue

            # 收集有效数据
            valid_data.append({
                'hs_code': std_hs,
                'product_description': product_desc if pd.notna(product_desc) else None,
                'rule_name': rule_name,
                'step_order': step_order,
                'step_type': step_type,
                'step_content': step_content if pd.notna(step_content) else None,
                'threshold_value': threshold if threshold is not None else None,
                'exceptions': exceptions if pd.notna(exceptions) else None
            })

        return len(errors) == 0, errors, valid_data

    except Exception as e:
        errors.append(f"文件读取失败：{str(e)}")
        return False, errors, valid_data