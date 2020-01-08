import urllib.request


def get(url: str, header: list = {}):
    """
    HTTP GET获取
    :param url: URL地址
    :param header: HTTP头
    :return: row
    """
    header['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    header['Accept-Language'] = 'zh-CN,zh;q=0.8,en;q=0.6'
    header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3790.0 Safari/537.36'
    req = urllib.request.urlopen(urllib.request.Request(url, headers=header))
    try:
        return req.read()
    except:
        retry_count = 4
        while retry_count:
            req = urllib.request.urlopen(urllib.request.Request(url, headers=header))
            try:
                return req.read()
            except:
                retry_count -= 1
                print('从{}下载文件时发生异常，重试下载，剩余尝试次数{}次'.format(url, retry_count))
                continue


def decode(url: str):
    """
    解码文件名
    :param url: 从网址中截取的文件名
    :return: str
    """
    return urllib.parse.unquote(url.split('/')[-1])
