from flask import Flask, request, send_from_directory, session, request_started
import os
import config
from app.api import bp as api_bp
from app.api.auth_api import bp as auth_bp
from flask_cors import CORS
from app.models.db_models import db, User
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
CORS(app, supports_credentials=True)

# 初始化数据库
db.init_app(app)

# 注册接口蓝图
CORS(api_bp, supports_credentials=True, origins=["*"])
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)

# 配置日志
setup_logger(app)
app.after_request(log_request)

# ==================== 静态页面路由（使用绝对路径）====================
# 首页
@app.route('/')
def index():
    # 使用绝对路径指向 frontend/index.html
    template_dir = os.path.join(app.root_path, app.template_folder)
    return send_from_directory(template_dir, 'index.html')

@app.route('/index.html')
def index_html():
    template_dir = os.path.join(app.root_path, app.template_folder)
    return send_from_directory(template_dir, 'index.html')

# 用户页面
@app.route('/user/<page>.html')
def user_page(page):
    filename = page + '.html'
    user_dir = os.path.join(app.root_path, app.template_folder, 'user')
    user_page_path = os.path.join(user_dir, filename)
    if not os.path.exists(user_page_path):
        return {"code": 404, "msg": "用户页面不存在"}, 404
    return send_from_directory(user_dir, filename)

# 管理员页面
@app.route('/admin/<page>.html')
def admin_page(page):
    filename = page + '.html'
    admin_dir = os.path.join(app.root_path, app.template_folder, 'admin')
    admin_page_path = os.path.join(admin_dir, filename)
    if not os.path.exists(admin_page_path):
        return {"code": 404, "msg": "管理员页面不存在"}, 404
    return send_from_directory(admin_dir, filename)

# 根目录下的普通页面（如 /about.html）
@app.route('/<page>.html')
def serve_root_html(page):
    filename = page + '.html'
    root_dir = os.path.join(app.root_path, app.template_folder)
    file_path = os.path.join(root_dir, filename)
    if not os.path.exists(file_path):
        return {"code": 404, "msg": "页面不存在"}, 404
    return send_from_directory(root_dir, filename)

# ==================== API 路由 ====================
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

# 重定向旧规则维护页面
@app.route('/admin/rule_maintain.html')
def redirect_old_rule_maintain():
    return redirect('/admin/rule_manage.html')

# ==================== 数据库初始化函数 ====================
def init_db():
    """手动初始化数据库（可在bash中调用）"""
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
            db.session.commit()
            print("数据库初始化完成！")
        except Exception as e:
            db.session.rollback()
            print(f"数据库初始化失败：{str(e)}")
            raise

# ==================== 信号初始化（自动执行一次）====================
def initialize_database(*args, **kwargs):
    if not hasattr(app, 'initialized'):
        with app.app_context():
            print("开始初始化数据库...")
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
                db.session.commit()
                print("数据库初始化完成！")
                app.initialized = True
            except Exception as e:
                print(f"数据库初始化失败：{e}")
                db.session.rollback()

# 连接信号：在第一个请求开始前执行
request_started.connect(initialize_database, app)

# ==================== 本地开发启动 ====================
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)