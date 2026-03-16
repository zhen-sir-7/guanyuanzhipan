from flask import request, jsonify, g
from app.api import bp
from app.models.db_models import Product, Material, Rule, JudgeResult, db
from app.utils.policy_spider import crawl_policy
from app.rvc_calculator.calculator import rvc_calculator_main
from app.rules.WO import judge_wo
from app.rules.CTC_RCEP import judge_ctc_rcep
from app.rules.RVC import calculate_rvc
from app.rules.DM import judge_dm
from app.utils.hs_code_utils import standardize_hs_code
from datetime import datetime
from app.api.auth_api import login_required
from app.utils.error_handler import handle_api_error
from sqlalchemy.orm import joinedload
from app.constants import DEFAULT_PAGE, DEFAULT_PER_PAGE
from app.rules.active_50 import judge_active_50

@bp.route('/user/policy_query', methods=['POST'])
@login_required
@handle_api_error
def policy_query():
    if request.is_json:
        keyword = request.json.get('keyword', '').strip()
    else:
        keyword = request.form.get('keyword', '').strip()

    if not keyword:
        return jsonify({"code": 400, "msg": "关键词不能为空", "data": None})

    policies = crawl_policy(keyword)
    return jsonify({"code": 200, "msg": "查询成功", "data": policies})


@bp.route('/user/product_add', methods=['POST'])
@login_required
@handle_api_error
def product_add():
    data = request.json
    user_id = g.user.id
    product_name = data.get('product_name')
    hs_code = data.get('hs_code')
    origin_country = data.get('origin_country')
    fob_price = data.get('fob_price')

    if not all([user_id, product_name, hs_code, origin_country, fob_price]):
        return jsonify({"code": 400, "msg": "必填项不能为空", "data": None})

    try:
        std_hs = standardize_hs_code(hs_code)
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None})

    if std_hs[:4] == "3808":
        active_total = data.get('active_ingredient_total_weight')
        active_origin = data.get('active_ingredient_origin_weight')
        if active_total is None or active_origin is None:
            return jsonify({"code": 400, "msg": "HS3808产品必须填写活性成分重量信息", "data": None})


    product = Product(
        user_id=user_id,
        product_name=product_name,
        hs_code=std_hs,
        origin_country=origin_country,
        fob_price=float(fob_price),
        direct_labor_cost=data.get('direct_labor_cost'),
        direct_operating_cost=data.get('direct_operating_cost'),
        profit=data.get('profit'),
        other_cost=data.get('other_cost'),
        specific_process=data.get('specific_process'),
        active_ingredient_total_weight = data.get('active_ingredient_total_weight'),
        active_ingredient_origin_weight = data.get('active_ingredient_origin_weight')
        )
    db.session.add(product)
    db.session.commit()

    materials = data.get('materials', [])
    for m in materials:
        try:
            mat_hs = standardize_hs_code(m.get('hs_code'))
        except ValueError as e:
            db.session.rollback()
            return jsonify({"code": 400, "msg": f"原料HS编码错误：{str(e)}", "data": None})
        material = Material(
            product_id=product.id,
            material_name=m.get('material_name'),
            hs_code=mat_hs,
            fob_value=float(m.get('fob_value')),
            origin_country=m.get('origin_country')
        )
        db.session.add(material)
    db.session.commit()

    return jsonify({"code": 200, "msg": "产品添加成功", "data": {"product_id": product.id}})


@bp.route('/user/product_list', methods=['POST'])
@login_required
@handle_api_error
def product_list():
    data = request.json or {}
    page = data.get('page', DEFAULT_PAGE)
    per_page = data.get('per_page', DEFAULT_PER_PAGE)

    user_id = g.user.id
    pagination = Product.query.options(joinedload(Product.materials))\
        .filter_by(user_id=user_id)\
        .paginate(page=page, per_page=per_page, error_out=False)

    products = pagination.items
    product_list = []
    for p in products:
        material_list = [{
            "id": m.id,
            "material_name": m.material_name,
            "hs_code": m.hs_code,
            "fob_value": m.fob_value,
            "origin_country": m.origin_country
        } for m in p.materials]
        product_list.append({
            "id": p.id,
            "product_name": p.product_name,
            "hs_code": p.hs_code,
            "origin_country": p.origin_country,
            "fob_price": p.fob_price,
            "materials": material_list
        })

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "items": product_list,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages
        }
    })


@bp.route('/user/calculate_rvc', methods=['POST'])
@login_required
@handle_api_error
def calculate_rvc_api():
    product_id = request.json.get('product_id')
    user_id = g.user.id
    rule_name = request.json.get('rule_name')

    if not all([product_id, rule_name]):
        return jsonify({"code": 400, "msg": "参数不能为空", "data": None})

    result = rvc_calculator_main(product_id, user_id, rule_name, db)
    return jsonify(result)


@bp.route('/user/origin_judge', methods=['POST'])
@login_required
@handle_api_error
def origin_judge():
    data = request.json
    product_id = data.get('product_id')
    user_id = g.user.id
    rule_name = data.get('rule_name')

    if not all([product_id, rule_name]):
        return jsonify({"code": 400, "msg": "参数不能为空", "data": None})

    # 查询产品
    product = Product.query.filter_by(id=product_id, user_id=user_id).first()
    if not product:
        return jsonify({"code": 400, "msg": "产品不存在或无权限", "data": None})
    materials = Material.query.filter_by(product_id=product_id).all()

    # 获取产品HS编码（已标准化）
    product_hs = product.hs_code

    # 查询所有规则（按规则名称筛选）
    all_rules = Rule.query.filter_by(rule_name=rule_name).all()
    if not all_rules:
        return jsonify({"code": 400, "msg": "该规则名称下无任何规则", "data": None})

    # 筛选出匹配的规则（产品HS编码以规则HS编码开头）
    matched_rules = [r for r in all_rules if product_hs.startswith(r.hs_code)]
    if not matched_rules:
        return jsonify({"code": 400, "msg": "该产品无对应判定规则", "data": None})

    # 按规则HS编码长度降序排序，取最长前缀的规则组
    matched_rules.sort(key=lambda r: len(r.hs_code), reverse=True)
    longest_prefix = matched_rules[0].hs_code
    # 提取该前缀的所有步骤
    steps = [r for r in matched_rules if r.hs_code == longest_prefix]
    steps.sort(key=lambda r: r.step_order)

    judge_results = []
    final_pass = True
    suggestions = []

    for step in steps:
        step_type = step.step_type
        step_content = step.step_content
        threshold = step.threshold_value
        exceptions = step.exceptions

        if step_type == "WO":
            is_pass, suggestion = judge_wo(product, materials, step_content, exceptions)
        elif step_type == "CTC_RCEP":
            is_pass, suggestion = judge_ctc_rcep(product, materials, step_content, exceptions)
        elif step_type == "RVC":
            rvc_value, is_pass, suggestion = calculate_rvc(product, materials, rule_name, threshold, exceptions)
            judge_results.append({
                "step": f"{step_type} ({step_content})" if step_content else step_type,
                "is_pass": is_pass,
                "suggestion": suggestion,
                "rvc_value": rvc_value
            })
            if not is_pass:
                final_pass = False
                suggestions.append(suggestion)
            continue
        elif step_type == "CR":
            is_pass = True
            suggestion = f"化学反应规则自动满足（{step_content or '无具体要求'}）"
        elif step_type == "ACTIVE_50":
            is_pass, suggestion = judge_active_50(product)
        else:
            is_pass = False
            suggestion = f"不支持的步骤类型：{step_type}"

        judge_results.append({
            "step": f"{step_type} ({step_content})" if step_content else step_type,
            "is_pass": is_pass,
            "suggestion": suggestion
        })

        if not is_pass:
            final_pass = False
            suggestions.append(suggestion)

    # 保存判定结果
    judge_result = JudgeResult(
        product_id=product_id,
        user_id=user_id,
        judge_result="通过" if final_pass else "不通过",
        rule_name=rule_name
    )
    db.session.add(judge_result)
    db.session.commit()

    certificate_template = ""
    if final_pass:
        certificate_template = f"""
        原产地证明申请模板
        产品名称：{product.product_name}
        HS编码：{product.hs_code}
        原产国：{product.origin_country}
        FOB价格：{product.fob_price}
        贸易规则：{rule_name}
        判定结果：通过
        申请日期：{datetime.now().strftime('%Y-%m-%d')}
        """

    return jsonify({
        "code": 200,
        "msg": "判定完成",
        "data": {
            "final_pass": final_pass,
            "step_results": judge_results,
            "total_suggestion": "；".join(suggestions) if suggestions else "无",
            "certificate_template": certificate_template
        }
    })


@bp.route('/user/judge_result_list', methods=['POST'])
@login_required
@handle_api_error
def judge_result_list():
    user_id = g.user.id
    data = request.json or {}
    product_id = data.get('product_id')
    page = data.get('page', DEFAULT_PAGE)
    per_page = data.get('per_page', DEFAULT_PER_PAGE)

    query = JudgeResult.query.filter_by(user_id=user_id)
    if product_id:
        query = query.filter_by(product_id=product_id)

    pagination = query.order_by(JudgeResult.judge_time.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    result_list = [{
        "id": r.id,
        "product_id": r.product_id,
        "rule_name": r.rule_name,
        "result": r.judge_result,
        "judge_time": r.judge_time.strftime("%Y-%m-%d %H:%M:%S")
    } for r in pagination.items]

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "items": result_list,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages
        }
    })


@bp.route('/user/product_delete', methods=['POST'])
@login_required
@handle_api_error
def product_delete():
    product_id = request.json.get('product_id')
    user_id = g.user.id

    if not product_id:
        return jsonify({"code": 400, "msg": "产品ID不能为空", "data": None})

    product = Product.query.filter_by(id=product_id, user_id=user_id).first()
    if not product:
        return jsonify({"code": 400, "msg": "产品不存在或无权限", "data": None})

    Material.query.filter_by(product_id=product_id).delete()
    JudgeResult.query.filter_by(product_id=product_id).delete()
    db.session.delete(product)
    db.session.commit()
    return jsonify({"code": 200, "msg": "产品删除成功", "data": None})


@bp.route('/user/product_detail/<int:product_id>', methods=['GET'])
@login_required
@handle_api_error
def product_detail(product_id):
    user_id = g.user.id
    product = Product.query.options(joinedload(Product.materials)).filter_by(id=product_id, user_id=user_id).first()
    if not product:
        return jsonify({"code": 400, "msg": "产品不存在或无权限", "data": None})

    material_list = [{
        "id": m.id,
        "material_name": m.material_name,
        "hs_code": m.hs_code,
        "fob_value": m.fob_value,
        "origin_country": m.origin_country
    } for m in product.materials]

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "id": product.id,
            "product_name": product.product_name,
            "hs_code": product.hs_code,
            "origin_country": product.origin_country,
            "fob_price": product.fob_price,
            "direct_labor_cost": product.direct_labor_cost,
            "direct_operating_cost": product.direct_operating_cost,
            "profit": product.profit,
            "other_cost": product.other_cost,
            "specific_process": product.specific_process,
            "materials": material_list
        }
    })