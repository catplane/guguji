from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from config import config_dict
import logging
from logging.handlers import RotatingFileHandler


db = SQLAlchemy()
redis_store = None  # type:StrictRedis


def write_log(config_class):
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



def create_app(config_name):
    app = Flask(__name__)
    config_class = config_dict[config_name]
    app.config.from_object(config_class)
    write_log(config_class)
    db.init_app(app)
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)
    CSRFProtect(app)
    Session(app)
    from info.modules.index import index_bp
    app.register_blueprint(index_bp)
    return app