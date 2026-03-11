from app.utils.hs_code_utils import standardize_hs_code

def parse_exceptions(exception_str):
    """
    解析例外条例字符串，返回 (start, end) 元组列表。
    支持格式：
    - 单个编码: "851712"
    - 范围: "851712-851718"
    - 多个: "851712,851718,851720"
    若输入为空或无效，返回空列表。
    """
    if not exception_str or not isinstance(exception_str, str):
        return []
    parts = [p.strip() for p in exception_str.split(',') if p.strip()]
    ranges = []
    for part in parts:
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                start = standardize_hs_code(start.strip())
                end = standardize_hs_code(end.strip())
                if start and end:
                    ranges.append((start, end))
            except:
                continue
        else:
            code = standardize_hs_code(part)
            ranges.append((code, code))
    return ranges

def is_hs_code_excluded(hs_code, exception_ranges):
    """
    判断给定HS编码是否被例外规则排除
    """
    for start, end in exception_ranges:
        if start <= hs_code <= end:
            return True
    return False