from flask import Blueprint

# 1.创建蓝图对象
index_bp = Blueprint("index", __name__)

# 3.让包知道views文件中的视图函数
from info.modules.index.views import *

