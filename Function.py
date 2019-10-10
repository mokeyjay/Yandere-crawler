import os.path
import datetime
import json

# 图片存储位置
_folder_name = 'K:/Yandere/'


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


def add(file_name: str, data, root: bool = False):
    """
    追加文件，用于即时写入日志
    :return:
    """
    global _folder_name
    file_name = file_name if root else _folder_name + '/' + file_name  # 类似三元运算符
    file = open(file_name, 'ab')
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
    data = file.read()
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


def char_replace(file_name):
    """
    去除特殊字符
    """
    chr_list = ('?', '\\', r'/', '*', ':', '<', '>', '|', '"')
    for chr in chr_list:
        file_name = file_name.replace(chr, '')
    return file_name


def read_settings(json_file):
    return json.loads(json_file)


def get_settings(settings: dict):
    settings['start_page'] = int(input('开始页码：'))
    settings['stop_page'] = int(input('停止页码，为0时爬取至上次终止图片，非0时爬完此页即停止：'))
    settings['pic_type'] = int(input('图片比例，0=全部 1=横图 2=竖图 3=正方形：'))
    settings['pic_ext'] = input('图片类型，png/jpg：')

    print('输入图片尺寸限制条件，为0则不限制：')
    settings['pic_size']['min']['width'] = int(input('最小宽度：'))
    settings['pic_size']['min']['height'] = int(input('最小高度：'))
    settings['pic_size']['min']['proportion'] = int(input('最小宽高比：'))
    settings['pic_size']['max']['width'] = int(input('最大宽度：'))
    settings['pic_size']['max']['height'] = int(input('最大高度：'))
    settings['pic_size']['max']['proportion'] = int(input('最大宽高比：'))

    # settings['folder_path'] = input('保存路径：')
    # 很遗憾该选项无效，手动改路径吧
    delay_on = input('是否启用下载延迟？(y/n)')
    if delay_on == 'n':
        settings['random_delay'] = 0
    else:
        settings['random_delay'] = 1

    settings['safe_mode'] = 1 # 强制安全浏览，不服打我呀

    status = input('只下载无争议图片？(y/n)')
    if status == 'n':
        settings['status_active_only'] = 0
    else:
        settings['status_active_only'] = 1

    return settings


def edit_settings(settings: dict, item, value: int):
    settings[item] = value
    return settings