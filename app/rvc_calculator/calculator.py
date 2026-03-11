from app.rules.RVC import calculate_rvc

def rvc_calculator_main(product_id, user_id, rule_name, db):
    from app.models.db_models import Product, Material

    product = Product.query.filter_by(id=product_id, user_id=user_id).first()
    if not product:
        return {"code": 400, "msg": "产品不存在或无权限", "data": None}

    materials = Material.query.filter_by(product_id=product_id).all()

    rvc_value, is_pass, suggestion = calculate_rvc(product, materials, rule_name)
    return {
        "code": 200,
        "msg": "计算成功",
        "data": {
            "rvc_value": rvc_value,
            "is_pass": is_pass,
            "suggestion": suggestion,
            "product_name": product.product_name,
            "rule_name": rule_name
        }
    }