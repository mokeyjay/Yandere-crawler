import os.path
import datetime

# 图片存储位置
_folder_name = 'E:/Yandere/'


def create_folder():
    global _folder_name
    # 创建目录存放今天爬下来的图
    _folder_name += datetime.datetime.now().strftime('%Y%m%d')
    if not os.path.exists(_folder_name):
        os.makedirs(_folder_name)


def write(file_name: str, data, root: bool = False):
    """
    写出文件
    :param file_name: 文件名
    :param data: 文件数据
    :param root: 是否写到根目录
    :return:
    """
    global _folder_name
    file_name = file_name if root else _folder_name + '/' + file_name  # 类似三元运算符
    file = open(file_name, 'wb')
    if isinstance(data, int) or isinstance(data, str):
        data = str(data).encode()
    file.write(data)
    file.close()


def get(file_name: str):
    """
    获取文件内容
    :param file_name: 文件名
    :return: str
    """
    file = open(file_name)
    data = file.readline()
    file.close()
    return data


def exists(file_name: str):
    """
    文件是否存在
    :param file_name: 文件名
    :return: bool
    """
    global _folder_name
    return os.path.exists(_folder_name + '/' + file_name)
