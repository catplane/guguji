
import random
import re
from datetime import datetime

from flask import current_app, jsonify, session
from flask import make_response
from flask import request
from info import constants, db
from info import redis_store
from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utitils.captcha.captcha import captcha
from info.utitils.response_code import RET
from . import passport_bp



@passport_bp.route('/login', methods=["POST"])
def login():
    """
    1. 获取参数和判断是否有值
    2. 从数据库查询出指定的用户
    3. 校验密码
    4. 保存用户登录状态
    5. 返回结果
    :return:
    """
    json_data = request.json
    mobile = json_data.get("mobile")
    password = json_data.get("password")
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据错误")

    if not user:
        return jsonify(errno=RET.USERERR, errmsg="用户不存在")

    if not user.check_passowrd(password):
        return jsonify(errno=RET.PWDERR, errmsg="密码错误")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    user.last_login = datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")


@passport_bp.route("/logout", methods=["POST"])
def logout():
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('mobile', None)
    return jsonify(errno=RET.OK, errmsg="OK")


@passport_bp.route('/image_code')
def get_image_code():
    """
        获取图片验证码
        :return:
        """
    code_id = request.args.get('code_id')
    name, text, image = captcha.generate_captcha()
    try:
        redis_store.setex('ImageCode_' + code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return make_response(jsonify(errno=RET.DATAERR, errmsg='保存图片验证码失败'))

    resp = make_response(image)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp


@passport_bp.route('/sms_code', methods=["POST"])
def send_sms():
    # 1.接收参数并判断是否有值
    param_dict = request.json
    mobile = param_dict.get("mobile")
    image_code = param_dict.get("image_code")
    image_code_id = param_dict.get("image_code_id")
    if not all([mobile, image_code_id, image_code]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")
    if not re.match("^1[3578][0-9]{9}$", mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机号不正确")
    try:
        real_image_code = redis_store.get("ImageCode_%s" % image_code_id)
        if real_image_code:
            redis_store.delete("ImageCode_" + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取图片验证码失败")

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg="验证码已过期")
    if image_code.lower() != real_image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="该手机已被注册")
    result = random.randint(0,999999)
    sms_code = "%06d" %result
    current_app.logger.debug("短信验证码的内容：%s" % sms_code)
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], "1")
    if result != 0:
        return jsonify(errno=RET.THIRDERR, errmsg="发短信失败")
    try:
        redis_store.set("SMS_" + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码失败")

    return jsonify(errno=RET.OK, errmsg="发送成功")


@passport_bp.route('/register', methods=["POST"])
def register():
    """
    1. 获取参数和判断是否有值
    2. 从redis中获取指定手机号对应的短信验证码的
    3. 校验验证码
    4. 初始化 user 模型，并设置数据并添加到数据库
    5. 保存当前用户的状态
    6. 返回注册的结果
    :return:
    """

    # 1. 获取参数和判断是否有值
    json_data = request.json
    mobile = json_data.get("mobile")
    sms_code = json_data.get("sms_code")
    password = json_data.get("password")

    if not all([mobile, sms_code, password]):
        # 参数不全
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 2. 从redis中获取指定手机号对应的短信验证码的
    try:
        real_sms_code = redis_store.get("SMS_" + mobile)
    except Exception as e:
        current_app.logger.error(e)
        # 获取本地验证码失败
        return jsonify(errno=RET.DBERR, errmsg="获取本地验证码失败")

    if not real_sms_code:
        # 短信验证码过期
        return jsonify(errno=RET.NODATA, errmsg="短信验证码过期")

    # 3. 校验验证码
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")
    # 删除短信验证码
    try:
        redis_store.delete("SMS_" + mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 4. 初始化 user 模型，并设置数据并添加到数据库
    user = User()
    user.nick_name = mobile
    user.mobile = mobile
    # 对密码进行处理
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        # 数据保存错误
        return jsonify(errno=RET.DATAERR, errmsg="数据保存错误")
    # 5. 保存用户登录状态
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    # 6. 返回注册结果
    return jsonify(errno=RET.OK, errmsg="OK")
