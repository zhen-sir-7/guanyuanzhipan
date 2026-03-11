from flask import Flask, request, send_from_directory, session
import os
import config
from app.api import bp as api_bp
from app.api.auth_api import bp as auth_bp
from flask_cors import CORS
from app.models.db_models import db, User  # 移除 HsCode
from app.utils.logger import setup_logger, log_request
from datetime import timedelta
from app.constants import SESSION_LIFETIME
from flask import redirect

# 创建Flask应用
app = Flask(__name__,
            template_folder="frontend",
            static_folder="frontend/static")

# 配置应用
app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # 生产环境需改为True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=SESSION_LIFETIME)

# 跨域配置
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# 初始化数据库
db.init_app(app)

# 注册接口蓝图
CORS(api_bp, supports_credentials=True, origins=["*"])
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)

# 配置日志
setup_logger(app)
app.after_request(log_request)

# 首页路由
@app.route('/')
def index():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/index.html')
def index_html():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json(silent=True)
    if data:
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember', False)
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', 'false') == 'true'

    if not username or not password:
        return {"code": 400, "msg": "用户名或密码不能为空"}, 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return {"code": 401, "msg": "用户名不存在"}, 401
    if not user.check_password(password):
        return {"code": 401, "msg": "密码错误"}, 401

    session.permanent = remember
    session['user_id'] = user.id

    return {
        "code": 200,
        "msg": "登录成功",
        "data": {"id": user.id, "username": user.username, "user_type": user.user_type}
    }, 200

@app.route('/user/<page>')
def user_page(page):
    user_page_path = os.path.join(app.template_folder, 'user', page)
    if not os.path.exists(user_page_path):
        return {"code": 404, "msg": "用户页面不存在"}, 404
    return send_from_directory(os.path.join(app.template_folder, 'user'), page)

@app.route('/admin/<page>')
def admin_page(page):
    admin_page_path = os.path.join(app.template_folder, 'admin', page)
    if not os.path.exists(admin_page_path):
        return {"code": 404, "msg": "管理员页面不存在"}, 404
    return send_from_directory(os.path.join(app.template_folder, 'admin'), page)

@app.route('/<page>.html')
def serve_root_html(page):
    file_path = os.path.join(app.template_folder, page + '.html')
    if not os.path.exists(file_path):
        return {"code": 404, "msg": "页面不存在"}, 404
    return send_from_directory(app.template_folder, page + '.html')

def init_db():
    with app.app_context():
        try:
            db.create_all()

            if not User.query.filter_by(username="admin").first():
                admin = User(user_type="admin", username="admin")
                admin.set_password("admin123")
                db.session.add(admin)

            if not User.query.filter_by(username="user").first():
                user = User(user_type="user", username="user")
                user.set_password("user123")
                db.session.add(user)

            # 移除 HsCode 的初始化代码
            db.session.commit()
            print("数据库初始化完成！")
        except Exception as e:
            db.session.rollback()
            print(f"数据库初始化失败：{str(e)}")
            raise

@app.route('/admin/rule_maintain.html')
def redirect_old_rule_maintain():
    return redirect('/admin/rule_manage.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)