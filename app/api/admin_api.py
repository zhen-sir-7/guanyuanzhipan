from flask import request, jsonify, g
from app.api import bp
from app.models.db_models import User, Rule, Product, Material, JudgeResult, db
from datetime import datetime
from app.utils.hs_code_utils import standardize_hs_code
from app.api.auth_api import admin_required
from app.utils.error_handler import handle_api_error
from sqlalchemy import func
import os
from app.utils.excel_validator import validate_rule_excel


# ------------------- 规则管理（单表 Rule） -------------------

@bp.route('/admin/rule_add', methods=['POST'])
@admin_required
@handle_api_error
def rule_add():
    """添加单条规则步骤"""
    data = request.json
    hs_code = data.get('hs_code')
    product_description = data.get('product_description')
    rule_name = data.get('rule_name')
    step_order = data.get('step_order')
    step_type = data.get('step_type')
    step_content = data.get('step_content')
    threshold_value = data.get('threshold_value')
    exceptions = data.get('exceptions')

    if not all([hs_code, rule_name, step_order, step_type]):
        return jsonify({"code": 400, "msg": "必填项不能为空", "data": None})

    try:
        std_hs = standardize_hs_code(hs_code)
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None})

    # 检查同一HS编码、规则名称、步骤顺序是否已存在
    existing = Rule.query.filter_by(
        hs_code=std_hs,
        rule_name=rule_name,
        step_order=step_order
    ).first()
    if existing:
        return jsonify({"code": 400, "msg": "该HS编码下已存在相同规则名称和步骤顺序的规则", "data": None})

    rule = Rule(
        hs_code=std_hs,
        product_description=product_description,
        rule_name=rule_name,
        step_order=step_order,
        step_type=step_type,
        step_content=step_content,
        threshold_value=threshold_value,
        exceptions=exceptions
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify({"code": 200, "msg": "规则步骤添加成功", "data": {"rule_id": rule.id}})


@bp.route('/admin/rule_query', methods=['POST'])
@admin_required
@handle_api_error
def rule_query():
    """查询规则步骤，支持按HS编码、规则名称筛选"""
    hs_code = request.json.get('hs_code', '').strip()
    rule_name = request.json.get('rule_name', '').strip()
    rule_id = request.json.get('rule_id')

    query = Rule.query
    if rule_id:
        query = query.filter_by(id=rule_id)
    else:
        if hs_code:
            try:
                std_hs = standardize_hs_code(hs_code)
                query = query.filter_by(hs_code=std_hs)
            except ValueError as e:
                return jsonify({"code": 400, "msg": str(e), "data": None})
        if rule_name:
            query = query.filter_by(rule_name=rule_name)

    rules = query.order_by(Rule.hs_code, Rule.rule_name, Rule.step_order).all()
    rule_list = [{
        "id": r.id,
        "hs_code": r.hs_code,
        "product_description": r.product_description,
        "rule_name": r.rule_name,
        "step_order": r.step_order,
        "step_type": r.step_type,
        "step_content": r.step_content,
        "threshold_value": r.threshold_value,
        "exceptions": r.exceptions
    } for r in rules]
    return jsonify({"code": 200, "msg": "查询成功", "data": rule_list})


@bp.route('/admin/rule_update', methods=['POST'])
@admin_required
@handle_api_error
def rule_update():
    """更新单条规则步骤"""
    rule_id = request.json.get('rule_id')
    data = request.json

    if not rule_id:
        return jsonify({"code": 400, "msg": "规则ID不能为空", "data": None})

    rule = Rule.query.get(rule_id)
    if not rule:
        return jsonify({"code": 400, "msg": "规则不存在", "data": None})

    if 'hs_code' in data:
        try:
            rule.hs_code = standardize_hs_code(data['hs_code'])
        except ValueError as e:
            return jsonify({"code": 400, "msg": str(e), "data": None})
    if 'product_description' in data:
        rule.product_description = data['product_description']
    if 'rule_name' in data:
        rule.rule_name = data['rule_name']
    if 'step_order' in data:
        rule.step_order = data['step_order']
    if 'step_type' in data:
        rule.step_type = data['step_type']
    if 'step_content' in data:
        rule.step_content = data['step_content']
    if 'threshold_value' in data:
        rule.threshold_value = data['threshold_value']
    if 'exceptions' in data:
        rule.exceptions = data['exceptions']

    db.session.commit()
    return jsonify({"code": 200, "msg": "规则更新成功", "data": None})


@bp.route('/admin/rule_delete', methods=['POST'])
@admin_required
@handle_api_error
def rule_delete():
    """删除单条规则步骤"""
    rule_id = request.json.get('rule_id')
    if not rule_id:
        return jsonify({"code": 400, "msg": "规则ID不能为空", "data": None})

    rule = Rule.query.get(rule_id)
    if not rule:
        return jsonify({"code": 400, "msg": "规则不存在", "data": None})

    db.session.delete(rule)
    db.session.commit()
    return jsonify({"code": 200, "msg": "规则删除成功", "data": None})


@bp.route('/admin/rule_import', methods=['POST'])
@admin_required
@handle_api_error
def rule_import():
    """批量导入规则（Excel）"""
    file = request.files.get('file')
    if not file:
        return jsonify({"code": 400, "msg": "请上传文件", "data": None})

    # 保存临时文件
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)

    # 调用校验器
    is_valid, errors, valid_data = validate_rule_excel(temp_path)
    os.remove(temp_path)

    if not is_valid:
        return jsonify({"code": 400, "msg": "文件校验失败", "data": {"errors": errors}})

    # 批量插入
    try:
        for row in valid_data:
            # 检查重复（可选：跳过或覆盖）
            existing = Rule.query.filter_by(
                hs_code=row['hs_code'],
                rule_name=row['rule_name'],
                step_order=row['step_order']
            ).first()
            if existing:
                continue  # 跳过已存在的
            rule = Rule(
                hs_code=row['hs_code'],
                product_description=row['product_description'],
                rule_name=row['rule_name'],
                step_order=row['step_order'],
                step_type=row['step_type'],
                step_content=row['step_content'],
                threshold_value=row['threshold_value'],
                exceptions=row['exceptions']
            )
            db.session.add(rule)
        db.session.commit()
        return jsonify({"code": 200, "msg": f"成功导入 {len(valid_data)} 条规则步骤", "data": None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"导入失败：{str(e)}", "data": None})


# ------------------- 判定结果查看 -------------------

@bp.route('/admin/all_judge_results', methods=['GET'])
@admin_required
@handle_api_error
def all_judge_results():
    """管理员查看所有用户的判定结果"""
    results = JudgeResult.query.options(
        db.joinedload(JudgeResult.user),
        db.joinedload(JudgeResult.product)
    ).order_by(JudgeResult.judge_time.desc()).all()
    result_list = []
    for r in results:
        result_list.append({
            "id": r.id,
            "username": r.user.username if r.user else "未知用户",
            "product_name": r.product.product_name if r.product else "未知产品",
            "rule_name": r.rule_name,
            "result": r.judge_result,
            "judge_time": r.judge_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify({"code": 200, "msg": "查询成功", "data": result_list})


# ------------------- 使用情况可视化数据接口 -------------------

@bp.route('/admin/get_visual_data', methods=['POST'])
@admin_required
@handle_api_error
def get_visual_data():
    total_judge = JudgeResult.query.count()
    pass_count = JudgeResult.query.filter_by(judge_result='通过').count()
    pass_rate = round(pass_count / total_judge * 100, 2) if total_judge > 0 else 0

    # HS编码分布：关联产品表，从Rule表获取产品描述（可选）
    hs_counts = db.session.query(
        Product.hs_code,
        func.count(JudgeResult.id).label('count')
    ).join(JudgeResult, JudgeResult.product_id == Product.id)\
     .group_by(Product.hs_code)\
     .order_by(func.count(JudgeResult.id).desc())\
     .all()

    hs_bubble_data = []
    for hs_code, cnt in hs_counts:
        # 从Rule表获取任意一条规则的产品描述（如果有）
        rule = Rule.query.filter_by(hs_code=hs_code).first()
        hs_name = rule.product_description if rule else f"HS{hs_code}"
        hs_bubble_data.append({
            "hs_code": hs_code,
            "count": cnt,
            "hs_name": hs_name
        })

    return jsonify({
        "code": 200,
        "msg": "获取成功",
        "data": {
            "total_judge": total_judge,
            "pass_rate": pass_rate,
            "hs_bubble_data": hs_bubble_data
        }
    })