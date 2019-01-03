from redis import StrictRedis
import logging


class Config(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql://root:1@127.0.0.1:3306/information22"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    SECRET_KEY = "DSAGFDSHUIHNJKDSALHUFKEDHWNSAFUEKWN78907432"
    SESSION_TYPE = "redis"
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db = 1)
    SESSION_USE_SIGNER = True
    SESSION_PREMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.ERROR


config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}