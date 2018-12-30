from info.modules.index import index_bp
from flask import current_app
from info import redis_store


# 2.使用蓝图对象装饰视图函数
@index_bp.route('/')
def index():
    # 使用日志
    current_app.logger.debug("debug日志信息")
    # 设置redis键值对数据
    redis_store.set("name", "laowang")
    return "index"

