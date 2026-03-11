from functools import wraps
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException

def handle_api_error(f):
    """API接口统一异常处理装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPException as e:
            current_app.logger.error(f"HTTP {e.code}: {e.description}")
            return jsonify({"code": e.code, "msg": e.description, "data": None}), e.code
        except Exception as e:
            current_app.logger.exception(f"Unhandled error in {f.__name__}: {str(e)}")
            return jsonify({"code": 500, "msg": "服务器内部错误", "data": None}), 500
    return decorated