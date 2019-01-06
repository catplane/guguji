from flask import session, current_app, jsonify, g

from info.response_code import RET


def do_index_class(index):
    if index == 1:
        return "first"
    elif index == 2:
        return "second"
    elif index == 3:
        return "third"
    else:
        return ""


def get_user_data(view_func):
    import functools
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):

        # 1.实现装饰器业务逻辑
        # ---------------1.用户登录成功，查询用户基本信息展示----------------
        # 1.获取用户的id
        user_id = session.get("user_id")
        # 先声明防止局部变量不能访问
        user = None

        # 延迟导入User解决循环导入问题
        from info.models import User
        if user_id:
            # 2.根据user_id查询当前登录的用户对象
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

        # 将用户对象保存到g对象中
        g.user = user

        # 2.实现被装饰函数原有功能
        return view_func(*args, **kwargs)


    return wrapper