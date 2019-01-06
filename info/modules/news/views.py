from flask import render_template, current_app, abort, g, jsonify, request

from info import constants, db
from info.models import News, Comment, CommentLike
from info.response_code import RET
from info.utitils.common import get_user_data
from . import news_bp

@news_bp.route('/<int:news_id>')
@get_user_data
def news_detail(news_id):
    user = g.user
    user_dict = user.to_dict() if user else None
    news_obj = None
    if news_id:
        try:
            news_obj = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            abort(404)
            return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    # 新闻对象转字典
    news_dict = news_obj.to_dict() if news_obj else None
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())
    is_collected = False
    if user:
        if news_obj in user.collection_news:
            is_collected = True
    comment_list = []
    try:
        comment_list = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
    commentlike_id_list = []
    if user:
        comment_id_list = [comment.id for comment in comment_list]
        try:
            commentlike_obj_list = CommentLike.query.filter(CommentLike.comment_id.in_(comment_id_list),
                                                             CommentLike.user_id == user.id).all()
        except Exception as e:
            current_app.logger.error(e)
        commentlike_id_list = [commentlike.comment_id for commentlike in commentlike_obj_list]
    comment_dict_list = []
    for comment in comment_list if comment_list else []:
        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        if comment.id in commentlike_id_list:
            comment_dict["is_like"] = True
        comment_dict_list.append(comment_dict)

    data = {
        "user_info": user_dict,
        "click_news_list": news_list,
        "news": news_dict,
        "is_collected": is_collected,
        "comments": comment_dict_list,
    }
    return render_template('news/detail.html', data=data)



@news_bp.route("/news_collect", methods=['POST'])
@get_user_data
def news_collect():
    user = g.user
    json_data = request.json
    news_id = json_data.get("news_id")
    action = json_data.get("action")
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    if not news_id:
        return jsonify(errno=RET.PARAMERR, errmsg="news参数错误")
    if action not in ("collect", "cancel_collect"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        news_obj = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")
    if not news_obj:
        return jsonify(errno=RET.NODATA, errmsg="新闻数据不存在")

    if action == "collect":
        user.collection_news.append(news_obj)
    else:
        user.collection_news.remove(news_obj)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_bp.route('/news_comment', methods=["POST"])
@get_user_data
def news_comment():
    # 1.1 news_id: 新闻id，user:当前登录的用户对象，comment:新闻评论的内容，parent_id:区分主评论，子评论参数
    params_dict = request.json
    news_id = params_dict.get("news_id")
    content = params_dict.get("comment")
    parent_id = params_dict.get("parent_id")
    user = g.user

    # 2.1 非空判断
    if not all([news_id, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3.1 根据news_id查询当前新闻对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询新闻对象异常")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻对象不存在")

    # 3.2 创建评论对象，并给各个属性赋值，保存回数据库
    comment_obj = Comment()
    comment_obj.user_id = user.id
    comment_obj.news_id = news.id
    comment_obj.content = content
    # 区分主评论和子评论
    if parent_id:
        # 代表是一条子评论
        comment_obj.parent_id = parent_id

    # 保存回数据库
    try:
        db.session.add(comment_obj)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    # 4.返回评论对象的字典数据
    return jsonify(errno=RET.OK, errmsg="发布评论成功", data=comment_obj.to_dict())


@news_bp.route('/comment_like', methods=["POST"])
@get_user_data
def set_comment_like():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    if action not in ("add", "remove"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")
    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")
    if action == "add":
        try:
            comment_like_obj = CommentLike.query.filter_by(comment_id=comment_id, user_id=user.id).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询评论点赞对象异常")
        if not comment_like_obj:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = user.id
            db.session.add(comment_like)
            comment.like_count += 1

    else:
        comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=user.id).first()
        try:
            comment_like_obj = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                        CommentLike.user_id == user.id
                                                        ).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询评论点赞对象异常")
        if comment_like_obj:
            db.session.delete(comment_like_obj)
            comment.like_count -= 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存评论对象异常")

    return jsonify(errno=RET.OK, errmsg="操作成功")