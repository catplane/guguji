from info.modules.index import index_bp
from flask import current_app, render_template
from info import redis_store


@index_bp.route('/')
def index():
    # 返回渲染模板文件
    print(current_app.url_map)
    return render_template("news/index.html")


@index_bp.route('/favicon.ico')
def get_favicon():
    return current_app.send_static_file("news/favicon.ico")
