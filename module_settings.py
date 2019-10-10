import json

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
    return settings

def edit_settings(settings: dict, item, value: int):
    settings[item] = value
    return settings