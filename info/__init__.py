from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_session import Session
from config import config_dict
import logging
from logging.handlers import RotatingFileHandler

# 只是申明了db对象而已，并没有做真实的数据库初始化操作


db = SQLAlchemy()

# 将redis数据库对象申明成全局变量
# # type:StrictRedis 提前申明redis_store数据类型
redis_store = None  # type:StrictRedis


def write_log(config_class):
    """记录日志方法"""

    # 设置日志的记录等级
    logging.basicConfig(level=config_class.LOG_LEVEL)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小:100M、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式 日志等级 输入日志信息的文件名   行数  日志信息
    #                  DEBUG  index.py           100   name
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 将app封装起来，给外界调用提供一个接口方法：create_app

def create_app(config_name):
    """
    将与app相关联的配置封装到`工厂方法`中
    :return: app对象
    """

    # 1.创建app对象
    app = Flask(__name__)
    # 根据development键获取对应的配置类名
    config_class = config_dict[config_name]

    app.config.from_object(config_class)

    # 1.1.记录日志
    write_log(config_class)

    # 2.创建mysql数据库对象
    # 延迟加载，懒加载思想，当app有值的时候才进行真正的初始化操作
    db.init_app(app)

    # 3.创建redis数据库对象(懒加载的思想)
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    """
    redis_store.set("age", 18)  ---->存储到redis ---0号数据库
    session["name"] = "laowang" ---->存储到redis ---1号数据库
    """
    # 4.开启后端的CSRF保护机制
    CSRFProtect(app)

    @app.after_request
    def after_request(response):
        # 调用函数生成 csrf_token
        csrf_token = generate_csrf()
        # 通过 cookie 将值传给前端
        response.set_cookie("csrf_token", csrf_token)
        return response

    # 5.借助Session调整flask.session的存储位置到redis中存储
    Session(app)

    # 6.注册首页蓝图
    # 将蓝图的导入延迟到工厂方法中，真正需要注册蓝图的时候再导入，能够解决循环导入的文件
    from info.modules.index import index_bp
    app.register_blueprint(index_bp)

    from info.modules.passport import passport_bp
    app.register_blueprint(passport_bp)


    return app