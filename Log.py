

_log_msg = ''


def add(msg: str):
    """
    添加日志信息
    :param msg:
    :return:
    """
    global _log_msg
    _log_msg += msg + '\n'

def get():
    """
    获取日志内容
    """
    global _log_msg
    return _log_msg

def output():
    print(_log_msg)

def g_output(container):
    container.insert('end', _log_msg)

def reset():
    """
    清除临时日志内容
    """
    global _log_msg
    _log_msg = ''