import logging
import re
from logging.handlers import RotatingFileHandler
import os
from flask import request, g

def setup_logger(app):
    """配置应用日志"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'app.log')
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # 添加过滤器脱敏密码
    class SensitiveFilter(logging.Filter):
        def filter(self, record):
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                # 隐藏密码字段（JSON格式或表单格式）
                record.msg = re.sub(r'"password":\s*"[^"]*"', '"password":"***"', record.msg)
                record.msg = re.sub(r'password=[^&]*', 'password=***', record.msg)
            return True

    handler.addFilter(SensitiveFilter())
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

def log_request(response):
    """记录请求日志（可挂载为after_request）"""
    from flask import current_app
    user_id = g.user.id if hasattr(g, 'user') else 'anonymous'
    data = request.get_json(silent=True) or request.form.to_dict()
    if 'password' in data:
        data['password'] = '***'
    current_app.logger.info(f"User:{user_id} {request.method} {request.path} - Data:{data} - Response:{response.status}")
    return response