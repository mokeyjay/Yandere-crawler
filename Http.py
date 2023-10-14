import logging
from urllib.parse import unquote
from asyncio import sleep
from random import uniform
from aiohttp import ClientSession


headers: dict = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


# 指数退避，但需要给出上次等待时间
async def sleep_backoff(sleep_time: int) -> int:
    sleep_time = min(60, 2*sleep_time)
    await sleep(sleep_time + uniform(-0.5, 0.5))
    return sleep_time


async def asyncget(session: ClientSession, url: str, special_headers: dict = None, retry_count: int = 10, retry_delay: int = 1) -> tuple[bytes | None, int]:
    """
    HTTP GET获取
    :param session: aiohttp.ClientSession, 复用连接
    :param url: URL地址
    :param special_headers: 附加HTTP头
    :param retry_count: 最大重试次数
    :param retry_delay: 初始重试等待时间
    :return: row
    """
    while retry_count:
        try:
            response = await session.get(url) if special_headers is None else await session.get(url, headers=special_headers.update(headers))
            try:
                return await response.read(), response.content_length
            # 捕获任何错误
            except Exception as e:
                logging.warning(f"读取数据时发生异常: {url} {e}，剩余重试次数{retry_count}次")
        except Exception as e:
            logging.warning(f"建立连接时发生异常: {url} {e}，剩余重试次数{retry_count}次")
        retry_count -= 1
        retry_delay = await sleep_backoff(retry_delay)
    logging.error('无法解析地址')
    return None, 0


def decode(url: str):
    """
    解码文件名
    :param url: 从网址中截取的文件名
    :return: str
    """
    return unquote(url.split('/')[-1])