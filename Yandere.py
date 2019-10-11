import json
import Http
import Log


def get_json(page, tag_on, tags):
    """
    获取列表页的json数据
    :param page: 页码
    :type page: int
    :return: str
    """
    if tag_on == 'n':
        url = 'https://yande.re/post.json?page=' + str(page) #JSON API
    else:
        url = 'https://yande.re/post.json?tags=' + str(tags) + '&page=' + str(page)
    json_data = Http.get(url)
    if not json_data:
        Log.add('请求 ' + url + ' 失败')
        exit()

    try:
        json_data = json_data.decode('utf-8')
    except:
        Log.add(url + ' 解码失败')
        exit(500)
    return json_data


def get_li(json_data: str):
    """
    获取li数据列表
    :param json: json数组
    :type json: str
    :return: list
    """
    return json.loads(json_data)


def get_info(dic):
    """
    获取详情。即id,largeimgurl,width,height
    :param dic: json中单个post的数据
    :type dic: dictionary
    :return: list (id, size, ext, largeimg_url, width, height)
    """
    plist = []
    jlist = ['id', 'file_size', 'file_ext', 'file_url', 'rating', 'status', 'width', 'height', 'score', 'jpeg_file_size', 'jpeg_url', 'jpeg_width', 'jpeg_height']
    # id file_size width height score jpeg_file_size jpeg_width jpeg_height为 int : 0,1,6,7,8,9,11,12
    # file_ext file_url rating status jpeg_url为 str : 2,3,4,5,10
    # score项目未使用
    # score的forum说明：“受欢迎程度”
    for ele in jlist:
        plist.append(dic[ele])
    plist[0] = str(plist[0])
    return plist
