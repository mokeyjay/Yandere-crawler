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
    url = 'https://yande.re/post?page='+str(page)
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
    return re.compile('<li style="width: 160px;" id="p.+?</li>').findall(html)


def get_info(li):
    """
    获取详情。即id,largeimgurl,width,height
    :param li: li的源码
    :type li: str
    :return: list (id, largeimg_url, width, height)
    """
    return re.compile('id="p(\d+)" class=".+?img" href="(.+?)">.+?directlink-res">(\d+) x (\d+)</span>').findall(li)
