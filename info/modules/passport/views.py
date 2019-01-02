from flask import current_app, jsonify
from flask import make_response
from flask import request
from info import constants
from info import redis_store
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_bp


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


