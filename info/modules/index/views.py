from info.models import User, News, Category
from info.modules.index import index_bp
from flask import current_app, render_template, session, jsonify
from info import redis_store, constants
from info.response_code import RET


@index_bp.route('/')
def index():
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
    news_list = None
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询分类数据异常")
    # 分类对象列表转换成字典列表
    category_dict_list = []
    for category in categories if categories else []:
        category_dict_list.append(category.to_dict())

    data = {
        "user_info":user.to_dict() if user else None,
        "click_news_list": click_news_list,
        "categories": category_dict_list
    }

    return render_template("news/index.html", data=data)


@index_bp.route('/favicon.ico')
def get_favicon():
    return current_app.send_static_file("news/favicon.ico")
