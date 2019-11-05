import os.path

def create_folder(folder_path):
    # 创建目录存放今天爬下来的图
    """
    :param folder_path: 文件夹路径
    :return:
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def read(file_name: str):
    """
    获取文件内容
    :param file_name: 文件名
    :return: str
    """
    file = open(file_name)
    data = file.read()
    file.close()
    return data

def write(folder_path: str, file_name: str, data, root: bool = False):
    """
    写出文件
    :param folder_path: 文件夹路径
    :param file_name: 文件名
    :param data: 文件数据
    :param root: 是否写到程序根目录
    :return:
    """
    file_name = file_name if root else folder_path + '/' + file_name  # 类似三元运算符
    file = open(file_name, 'wb')
    if isinstance(data, int) or isinstance(data, str):
        data = str(data).encode()
    file.write(data)
    file.close()

def add(folder_path: str, file_name: str, data, root: bool = False):
    """
    追加文件，用于即时写入日志
    :param folder_path: 文件夹路径
    :param file_name:文件名
    :param data: 待写入数据
    :param root:是否写到程序根目录
    :return:
    """
    # 每检查一个post就至少会打开一次日志文件，也许应该先写入缓冲区，等到退出时一并写入
    file_name = file_name if root else folder_path + '/' + file_name
    file = open(file_name, 'ab')
    if isinstance(data, int) or isinstance(data, str):
        data = str(data).encode()
    file.write(data)
    file.close()

def exists(folder_path: str, file_name: str):
    """
    文件是否存在
    :param folder_path: 文件夹路径
    :param file_name: 文件名
    :return: bool
    """
    return os.path.exists(folder_path + '/' + file_name)

def rename(file_name):
    """
    去除特殊字符
    :type file_name: str
    :return: str
    """
    chr_list = ('?', '\\', r'/', '*', ':', '<', '>', '|', '"')
    for chr in chr_list:
        file_name = file_name.replace(chr, '')
    return file_name