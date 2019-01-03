from info.models import User
from info.modules.index import index_bp
from flask import current_app, render_template, session
from info import redis_store


@index_bp.route('/')
def index():
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.erro(e)

    return render_template("news/index.html", data={"user_info": user.to_dict() if user else None})


@index_bp.route('/favicon.ico')
def get_favicon():
    return current_app.send_static_file("news/favicon.ico")
