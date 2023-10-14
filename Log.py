
# 其实这个文件并没有被调用
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
    """
    在终端输出日志
    """
    print(_log_msg)


def g_output(container):
    """
    在GUI的滚动文本框输出日志
    :param container: 要插入文本信息的组件名称
    """
    container.insert('end', _log_msg)
    container.see('end')


def reset():
    """
    清除临时日志内容
    """
    global _log_msg
    _log_msg = ''
