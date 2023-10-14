import os
import re


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


def existing(folder_path: str):
    """
    检索指定文件夹下所有文件，用于判断是否已存在相同内容但名称不同的图片
    :param folder_path: 文件夹路径
    :return: dict
    """
    # 遍历指定目录下所有文件，将生成器转换为字典便于检索
    # for root, dirs, files in os.walk(folder_path, topdown = False):
    #    gen_list = files
    gen_list = os.listdir(folder_path)
    gen_dict = {}
    for elem in gen_list:
        key = re.match('yande.re (\d+).+?', elem)
        if key:
            gen_dict[key.group(1)] = [elem, os.path.getsize(folder_path + os.sep + elem)]
    return gen_dict


def rename_file(folder_path: str, origin_file_name: str, new_file_name: str):
    try:
        os.rename(folder_path + os.sep + origin_file_name, folder_path + os.sep + new_file_name)
    except FileNotFoundError:
        print('发生异常：系统找不到{}'.format(origin_file_name))
    except FileExistsError:
        print('发生异常：更新文件名{}已存在'.format(new_file_name))


def rename(file_name):
    """
    去除特殊字符
    :type file_name: str
    :return: str
    """
    chr_list = r'[\\/:*?"<>|]'
    for char in chr_list:
        file_name = file_name.replace(char, '')
    return file_name
