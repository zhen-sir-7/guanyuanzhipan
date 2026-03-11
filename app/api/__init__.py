from flask import Blueprint

# 创建蓝图
bp = Blueprint('api', __name__, url_prefix='/api')

# 导入子模块
from app.api import user_api
from app.api import admin_api
from app.api import auth_api

# 解决循环导入问题
import app.models.db_models as models
db = models.db