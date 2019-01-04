from info.models import User, News, Category
from info.modules.index import index_bp
from flask import current_app, render_template, session, jsonify, request
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


@index_bp.route('/news_list')
def get_news_list():
    args_dict = request.args
    page = args_dict.get("page", "1")
    per_page = args_dict.get("per_page", constants.HOME_PAGE_MAX_NEWS)
    category_id = args_dict.get("cid", "1")
    if not category_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    try:
        page = int(page)
        per_page = int(per_page)
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    filters = []
    if  category_id != 1:
        #SQLALCHEMY对==符号有一个重写__eq__的行为使==符号直接返回字符串,详情请看demo
        filters.append(News.category_id == category_id)
    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
        items = paginate.items
        total_page = paginate.pages
        current_page = paginate.page
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")
    news_li = []
    for news in items:
        news_li.append(news.to_dict())
    data = {
        "news_list": news_li,
        "current_page": current_page,
        "total_page": total_page
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)



@index_bp.route('/favicon.ico')
def get_favicon():
    return current_app.send_static_file("news/favicon.ico")
