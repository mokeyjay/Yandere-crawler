

_log_msg = ''


def add(msg: str):
    global _log_msg
    _log_msg += msg + '\r'
    print(msg)


def get():
    global _log_msg
    return _log_msg
