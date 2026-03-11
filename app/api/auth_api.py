from functools import wraps
from flask import request, jsonify, g, session, Blueprint
from app.models.db_models import db, User
from app.utils.error_handler import handle_api_error
import re

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_password(password):
    """密码至少8位，包含大小写字母和数字"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含至少一个大写字母"
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含至少一个小写字母"
    if not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"
    return True, ""

# 普通登录校验装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = None
        if 'user_id' in session:
            user_id = session['user_id']
        else:
            user_id = request.headers.get('X-User-ID')

        if not user_id:
            return jsonify({"code": 401, "msg": "请先登录", "data": None})

        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在或登录已过期", "data": None})

        g.user = user
        return f(*args, **kwargs)
    return decorated_function

# 管理员权限校验装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = None
        if 'user_id' in session:
            user_id = session['user_id']
        else:
            user_id = request.headers.get('X-User-ID')

        if not user_id:
            return jsonify({"code": 401, "msg": "请先登录", "data": None})

        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 401, "msg": "用户不存在或登录已过期", "data": None})

        if user.user_type != 'admin':
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None})

        g.user = user
        return f(*args, **kwargs)
    return decorated_function

# 注册接口
@bp.route('/register', methods=['POST'])
@handle_api_error
def register():
    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空"}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名和密码不能为空"}), 400

    # 密码强度校验
    valid, msg = validate_password(password)
    if not valid:
        return jsonify({"code": 400, "msg": msg}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"code": 400, "msg": "用户名已存在"}), 400

    new_user = User(username=username, user_type='user')
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        "code": 200,
        "msg": "注册成功",
        "data": {"user_id": new_user.id, "username": new_user.username}
    })