from flask import Blueprint, request
from flask import current_app as app
from utils.constant import *
from utils.signal import clipboard_update_signal
import traceback
from schema import Schema

clipboard = Blueprint('clipboard', __name__, url_prefix='/clipboard')


@clipboard.route('/get_agent')
def get_agent():
    try:
        register_server = app.extensions['register_server']
        if register_server:
            return {"data": register_server.get_client_list(), "code": SUCCESS_CODE, "msg": ""}
    except:
        print(traceback.format_exc())
        return {"code": FAIL_CODE, "msg": "不是服务器"}

@clipboard.route('/update_clipboard', methods=['POST'])
def update_clipboard():
    input = request.get_json()
    clipboard_update_signal.send(text=input['text'], file_list=input['file_list'])
    return input