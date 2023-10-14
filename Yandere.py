import json
import Http

# 基本上是json操作


def get_json(page: int, tag_on, tags: str):
    """
    获取列表页的json数据
    :param page: 页码
    :type page: int
    :param tag_on: tag搜索开关
    :type tags: str
    :return: str
    """
    if tag_on:
        url = 'https://yande.re/post.json?tags={}&page={}'.format(tags, str(page))
    else:
        url = 'https://yande.re/post.json?page=' + str(page)  # JSON API
    json_data = Http.get(url)
    if not json_data:
        print('请求 ' + url + ' 失败')
        exit()

    try:
        json_data = json_data.decode('utf-8')
    except:
        print(url + ' 解码失败')
        exit(500)
    return json_data


def get_li(json_data: str):
    """
    获取li数据列表
    :param json: json_data数组
    :type json_data: str
    :return: list
    """
    return json.loads(json_data)


def return_json(settings: dict):
    """
    :param settings: 配置项，缩进宽度4
    :type settings: dict
    :return: json
    """
    return json.dumps(settings, indent=4)
