from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, comment="账号编号")
    user_type = db.Column(db.String(20), nullable=False, comment="账号类型（user/admin）")
    username = db.Column(db.String(50), unique=True, nullable=False, comment="账户号")
    password_hash = db.Column(db.String(200), nullable=False, comment="加密密码")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True, comment="产品编号")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, comment="账号编号", index=True)
    product_name = db.Column(db.String(100), nullable=False, comment="产品名称")
    hs_code = db.Column(db.String(10), nullable=False, comment="HS编码（4-10位）")
    origin_country = db.Column(db.String(50), nullable=False, comment="原产国")
    fob_price = db.Column(db.Float, nullable=False, comment="FOB价格")
    direct_labor_cost = db.Column(db.Float, nullable=True, comment="直接人工成本")
    direct_operating_cost = db.Column(db.Float, nullable=True, comment="直接经营成本")
    profit = db.Column(db.Float, nullable=True, comment="利润")
    other_cost = db.Column(db.Float, nullable=True, comment="其他成本")
    specific_process = db.Column(db.String(200), nullable=True, comment="特定加工过程")
    materials = db.relationship("Material", backref="product", lazy=True, cascade="all, delete-orphan")
    active_ingredient_total_weight = db.Column(db.Float, nullable=True, comment="活性成分总重量（单位与FOB一致）")
    active_ingredient_origin_weight = db.Column(db.Float, nullable=True, comment="原产活性成分重量")

class Material(db.Model):
    __tablename__ = "material"
    id = db.Column(db.Integer, primary_key=True, comment="原料编号")
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False, comment="产品编号", index=True)
    material_name = db.Column(db.String(100), nullable=False, comment="原料名称")
    hs_code = db.Column(db.String(10), nullable=False, comment="HS编码（4-10位）")
    fob_value = db.Column(db.Float, nullable=False, comment="FOB价值")
    origin_country = db.Column(db.String(50), nullable=False, comment="原产国")


class Rule(db.Model):
    __tablename__ = "rule"
    id = db.Column(db.Integer, primary_key=True, comment="规则步骤编号")
    hs_code = db.Column(db.String(10), nullable=False, comment="HS编码（4-10位）", index=True)
    product_description = db.Column(db.String(200), nullable=True, comment="产品描述")
    rule_name = db.Column(db.String(50), nullable=False, comment="适用规则（如RCEP）", index=True)
    step_order = db.Column(db.Integer, nullable=False, comment="步骤顺序")
    step_type = db.Column(db.String(20), nullable=False, comment="步骤类型（CTC/RVC/WO/DM）")
    step_content = db.Column(db.String(500), nullable=True, comment="步骤内容（如CTH/CC）")
    threshold_value = db.Column(db.Float, nullable=True, comment="阈值（如RVC所需百分比）")
    exceptions = db.Column(db.Text, nullable=True, comment="例外条例（支持单个/范围/逗号分隔）")

    __table_args__ = (
        db.UniqueConstraint('hs_code', 'rule_name', 'step_order', name='uq_rule_hs_name_order'),
    )


class JudgeResult(db.Model):
    __tablename__ = "judge_result"
    id = db.Column(db.Integer, primary_key=True, comment="判定编号")
    judge_time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment="判定时间", index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False, comment="产品编号", index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, comment="账号编号", index=True)
    judge_result = db.Column(db.String(20), nullable=False, comment="判定结果（通过/不通过）")
    rule_name = db.Column(db.String(50), nullable=False, comment="使用的贸易规则")