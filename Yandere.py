import re
import Http
import Log


def get_html(page=1):
    """
    获取列表页的html源码
    :param page: 页码
    :type page: int
    :return: str
    """
    url = 'https://yande.re/post.xml?page='+str(page)
    html = Http.get(url)
    if not html:
        Log.add('抓取 ' + url + ' 失败')
        exit()

    try:
        html = html.decode('utf-8')
    except:
        Log.add(url + ' 解码失败')
        exit(500)
    return html


def get_li(html: str):
    """
    获取li源码列表
    :param html: html源码
    :type html: str
    :return: list
    """
    return re.compile(r'<post id="\d{6}.+?"/>').findall(html)


def get_info(li):
    """
    获取详情。即id,largeimgurl,width,height
    :param li: li的源码
    :type li: str
    :return: list (id, largeimg_url, width, height)
    """
    return re.compile('post id="(\d+)" tags=".+?file_url="(.+?)".+?is_pending="\w+?" width="(\d+)" height="(\d+)".+?/>').findall(li)
