#!/usr/bin/env python3

import logging
import asyncio
import argparse
from time import time, strftime
from json import loads, dumps
from os import makedirs, listdir, rename
from os.path import exists, join, splitext
from aiofiles import open as aopen
from aiohttp import ClientSession
from Http import decode
from Function import rename as frename
from Http import asyncget, headers


class shared_signals:
    def __init__(self, thread_count: int = 2) -> None:
        self.event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.thread_count: int = thread_count
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=80)  # 下载任务队列
        self.qsize_low: asyncio.Event = asyncio.Event()  # 下载队列任务量不足的信号
        self.task_clear: asyncio.Event = asyncio.Event()  # 抓取任务结束的信号，但下载任务可能仍在进行
        self.write_queue: asyncio.Queue = asyncio.Queue(maxsize=2*self.thread_count)  # 文件写入队列


# 异步文件写入函数，将output_folder从下载线程剥离
async def write_worker(output_folder: str, signals: shared_signals) -> None:
    loop, write_queue, task_clear = asyncio.get_event_loop(), signals.write_queue, signals.task_clear
    while True:
        try:
            filename, content = await asyncio.wait_for(write_queue.get(), timeout=1)
            write_queue.task_done()
            if filename is None:
                write_queue.task_done()
                break
            async with aopen(join(output_folder, filename), 'wb') as f:
                await f.write(content)
        except asyncio.TimeoutError:
            if task_clear.is_set() and len(asyncio.all_tasks(loop)) <= 2:  # 主线程+自身，避免过早退出
                break
    logging.debug("写入线程退出")


def format_size(size: int) -> str:
    if size >= 1048576:
        return f"{size/1048576:>5.2f}M" if size < 1073741824 else f"{size/1073741824:>5.2f}G"
    return f"{size/1024:>5.2f}K" if size >= 1024 else f"{size:>5}B"


class api_crawler:
    def __init__(self, settings: dict) -> None:
        self._filter: dict = settings["filter"]
        self.local_fdict: dict[int, str] = {}
        self.output_folder: str = None
        self.session: ClientSession = None
        self.payload: list[dict] = []

    def _init_local_flist(self) -> None:
        if self.output_folder is None:
            return
        # 生成输出文件夹下所有符合指定命名规则的文件列表，以id-文件名为键值对的字典形式存储
        # 基于以下前提：Y站不会修改文件命名规则；已张贴的post其二进制文件不会被修改(二进制文件内容，大小、扩展名)，只有tags被修改。
        # 若文件命名规则发生变化，则此函数需要更新
        for file in listdir(self.output_folder):
            # if key := match(r"yande.re (\d+).+?", file): # 正则
            #     self.__fdict[key[1]] = file
            if file[:9] == "yande.re ":  # 字符串分割
                # 如果不需要随tags变化更新文件名，可以考虑使用集合计算
                self.local_fdict[int(file[9:9+file[9:].find(' ')])] = file  # 第二个空格前为id

    def _post_normalize(self, post: dict) -> tuple[bool, dict]:
        fname = post.get("file_name")
        if fname is None:
            post["file_name"] = fname = frename(decode(post['file_url']))
        fext = post.get("file_ext", splitext(fname)[1][1:])
        normalized_post = {"id": post["id"], "url": post["file_url"], "size": post["file_size"], "fname": fname, "fext": fext}
        if self._filter["file_type"] == "origin":
            return True, normalized_post
        elif self._filter["file_type"] == "forcepng":
            if fext != "png":
                logging.info(f"{post['id']} 的原图格式非png，跳过")
            return (False, {}) if fext != "png" else (True, normalized_post)
        elif self._filter["file_type"] == "jpeg":
            url, size, fname = post["jpeg_url"], post["jpeg_file_size"], frename(decode(post['jpeg_url']))
        elif self._filter["file_type"] == "sample":
            url, size, fname = post["sample_url"], post["sample_file_size"], frename(decode(post['sample_url']))
        elif self._filter["file_type"] == "preview":
            url, size, fname = post["preview_url"], 0, frename(decode(post['preview_url']))
        return True, {"id": post["id"], "url": url, "size": size, "fname": fname, "fext": "jpg"}
        # return True, {"id": post["id"], "url": post["file_url"], "size": post["file_size"], "fname": fname, "fext": post.get("file_ext", fname.rsplit('.', 1)[1])}

    # 空功能，在post_crawler中有具体功能，在pool_crawler中为无条件通过
    def _post_filter(self, post: dict) -> bool:
        return True

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

    async def next_page(self) -> bool:
        return False

    async def get_data(self, url: str) -> list | dict | None:
        # 从json接口获取posts并序列化，若未出错则返回posts列表，否则返回None对象。错误处理在主函数中进行
        if self.session is None:
            self.session = ClientSession(headers=headers)
        response, _ = await asyncget(self.session, url)
        if response is None:
            logging.error(f'请求失败: {url}')
            return None
        try:
            json_data = response.decode('utf-8')
            return loads(json_data)
        except UnicodeDecodeError:
            logging.error(f'解码失败: {url}')
            return None

    async def _get_post_without_filter(self) -> dict | None:
        if not self.payload and not await self.next_page():
            return None
        return self.payload.pop(0)

    async def get_post(self) -> dict | None:
        if not self.payload:
            return None
        while post := await self._get_post_without_filter():
            post_id = post["id"]
            exist_file_name, file_name = self.local_fdict.get(post_id), frename(decode(post['file_url']))  # 删除非法字符
            if exist_file_name is None:
                post["file_name"] = file_name
                if self._post_filter(post):
                    match_format_filter, post = self._post_normalize(post)
                    return post if match_format_filter else None
            elif exist_file_name == file_name:
                logging.info(f"{post_id} 已存在，跳过")
            else:
                logging.info(f"{post_id} 已存在但tags有变化。重命名原文件，跳过下载")
                rename(join(self.output_folder, exist_file_name), join(self.output_folder, file_name))
        return None


class pool_crawler(api_crawler):
    def __init__(self, settings: dict, pool_id: int) -> None:
        super().__init__(settings)
        self.pool_id: int = pool_id
        self.flag_not_end: bool = True
        self._init_settings(settings)
        self._init_local_flist()

    def _init_settings(self, settings: dict) -> None:
        # 实例化此对象即意味着运行在pool下载模式下，除输出文件夹以外的设置项都将被忽略
        self.output_folder = join(settings["folder_path"], str(self.pool_id))
        if not exists(self.output_folder):
            makedirs(self.output_folder)

    async def get_page(self) -> dict | None:
        logging.warning(f"正在读取pool: {self.pool_id}")
        return await self.get_data(f"https://yande.re/pool/show.json?id={self.pool_id}")

    async def next_page(self) -> bool:
        if self.flag_not_end:
            posts = await self.get_page()
            if posts:
                self.payload.extend(posts["posts"])
                self.flag_not_end = False
        return self.flag_not_end


# 封装请求posts的功能，使按页抓取和按pool抓取的对外行为一致，简化主线程逻辑
# 初始化logger句柄的功能也在这里，避免处理输出文件夹的问题
class post_crawler(api_crawler):
    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self.page: int = 1
        self.start_page: int = 1
        self.stop_page: int = -1
        self.flag_tag_search: bool = False
        self.tags: set[str] = {}
        self.discard_tags: set[str] = {}
        self.tags_str: str = ''
        self.flag_not_end: bool = True
        self._init_settings(settings)
        self._init_local_flist()

    def _init_settings(self, settings: dict) -> None:
        # 实例化此对象即意味着并非运行在pool下载模式下
        if settings["tag_search"]:
            tags = settings["tags"]
            if not tags:
                return None
            self.tags = set(tags.split(' '))
            self.tags_str = tags.replace(' ', '+')
            self.discard_tags = set() if settings["discard_tags"] else set(settings["discard_tags"].split(' '))
            self.output_folder = join(settings["folder_path"], tags.replace(':', ''))
            self.flag_tag_search = True
        elif settings["date_separate"]:
            self.output_folder = join(settings["folder_path"], strftime('%Y%m%d'))
        else:
            self.output_folder = settings["folder_path"]
        if not exists(self.output_folder):
            makedirs(self.output_folder)
        self.start_page = settings["start_page"]
        self.stop_page = settings["stop_page"]
        self.page = self.start_page

    def _post_filter(self, post: dict) -> bool:  # TODO: 分析各条件使用频率，重排序
        # pending判断
        # 发现其他状态类型，将判断条件从“仅active”改为“排除pending”
        if self._filter["status_check"] and post["status"] == 'pending':
            logging.info(f"{post['id']} is {post['status']}，跳过。原因：{post['flag_detail']['reason']}")
            return False
        # 分级判断, safe, questionable, explicit
        if self._filter["safe_mode"] and post["rating"] == 'e':
            return False
        # 排除tag判断
        if self.flag_tag_search and self.discard_tags & set(post["tags"]):
            logging.info(f"{post['id']} 包含待排除tags，跳过")
            return False
        # 文件体积判断
        if 0 < self._filter["file_limit"] < post["file_size"]:
            logging.info(f"{post['id']} 超过体积限制，跳过")
            return False
        # 图片比例判断(粗略)
        # 由于预览图经过压缩，因此判断预览图尺寸会比原图多出一点冗余
        if self._filter["ratio"] == "all":
            matched = False
        elif self._filter["ratio"] == "horizontal":
            if post["preview_width"] > post["preview_height"]:
                matched = True
        elif self._filter["ratio"] == "vertical":
            if post["preview_width"] < post["preview_height"]:
                matched = True
        elif self._filter["ratio"] == "square":
            if post["preview_width"] != post["preview_height"]:
                matched = True
        if matched:
            logging.info(f"{post['id']} 比例不符，跳过")
            return False
        # 图片宽高比判断(精确)
        proportion = post["preview_width"] / post["preview_height"]
        pixel_limit = self._filter["pixel_limit"]
        if 0 < pixel_limit["max_proportion"] < proportion or proportion < pixel_limit["min_proportion"]:
            logging.info(f"{post['id']} 宽高比不符，跳过")
            return False
        # 图片尺寸判断，只判断原图(或大图)尺寸
        if pixel_limit["min_width"] > post["width"]:
            logging.info(f"{post['id']}宽度小于下限，跳过")
            return False
        if 0 < pixel_limit["max_width"] < post["width"]:
            logging.info(f"{post['id']}宽度大于上限，跳过")
            return False
        if pixel_limit["min_height"] > post["height"]:
            logging.info(f"{post['id']}高度小于下限，跳过")
            return False
        if 0 < pixel_limit["max_height"] < post["height"]:
            logging.info(f"{post['id']}高度大于上限，跳过")
            return False
        # 所有条件满足
        return True

    async def get_page(self) -> list | None:
        logging.warning(f"正在读取第{self.page}页……")
        url = f"https://yande.re/post.json?tags={self.tags_str}&page={self.page}" if self.flag_tag_search else f"https://yande.re/post.json?page={self.page}"
        return await self.get_data(url)

    async def next_page(self) -> bool:
        if self.stop_page > -1 and self.page > self.stop_page:
            self.flag_not_end = False
            return False
        posts = await self.get_page()
        if posts:
            self.payload.extend(posts)
            self.page += 1
        else:
            self.flag_not_end = False
        return self.flag_not_end


def init_logger(log_level: str="info", log_file: str=None) -> None:
    logger = logging.getLogger()
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(message)s", "%H:%M:%S")
    # StreamHandler输出到屏幕
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if log_file:
        # FileHandler输出到文件
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', type=int, default=-1, help='开始页码')
    parser.add_argument('-e', '--end', type=int, default=-1, help='结束页码')
    parser.add_argument('-o', '--output_folder', type=str, default='', help='保存路径')
    parser.add_argument('-t', '--threads', type=int, default=-1, help='并行下载线程数，不是分段并行下载')
    parser.add_argument('-l', '--log', type=str, default='info', help='日志等级')
    # parser.add_argument('-d', '--debug', action='store_true', help='调试模式')
    # parser.add_argument('-r', '--retry', type=int, default=10, help='http请求失败时的重试次数，达到重试次数上限后不再创建新任务')
    parser.add_argument('--pool_id', type=int, default=0, help='按pool下载post，如果指定pool id，则忽略除输出文件夹和下载线程数外的其他参数')
    parser.add_argument('--ratio', type=str, default="null", help='图片比例，all=全部, horizontal=横图, vertical=竖图, square=方形')
    # parser.add_argument('--tags', type=str, default='', help='按tags搜索，设置此参数时将自动运行在tags搜索模式')
    # parser.add_argument('--discard_tags', type=str, default='', help='要排除的tags，仅在tags搜索模式下生效')
    return parser.parse_args()


def main() -> None:
    # 创建协程任务池
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # 读取命令行参数
    args = parse_args()
    # 读取配置文件
    with open('config.json', 'r', encoding='utf-8') as f:
        settings = loads(f.read())
    # 创建队列及信号量
    if args.threads > 0:
        settings["thread_count"] = args.threads
    signals = shared_signals(settings["thread_count"])
    # 创建主线程
    crawler_thread = get_data(settings, signals, args)
    if crawler_thread.can_run():
        for task in [parallel_task(signals) for _ in range(crawler_thread.settings["thread_count"])]:
            loop.create_task(task.run())
        loop.create_task(write_worker(crawler_thread.crawler.output_folder, signals))
        loop.run_until_complete(crawler_thread.run())


# 生产者线程：抓取页面，将post元素补充入data队列
class get_data:
    def __init__(self, settings: dict, signals: shared_signals, args: argparse.Namespace = None) -> None:
        self.settings: dict = settings
        self.queue: asyncio.Queue = signals.queue
        self.qsize_low: asyncio.Event = signals.qsize_low
        self.task_clear: asyncio.Event = signals.task_clear
        self.crawler: post_crawler | pool_crawler = None
        self.mode: str = "pages"  # pages, tags, pool
        self.last_stop_id: int = 0
        self.latest_post_id: int = 0
        self._init(settings, args)

    def _init(self, settings: dict, args: argparse.Namespace = None) -> None:
        if args.start > -1:
            settings["start_page"] = args.start
        if args.end > -1:
            settings["stop_page"] = args.end
        if args.output_folder:
            settings["folder_path"] = args.output_folder
        # settings["thread_count"] = args.threads
        if args.ratio != "null":
            settings["filter"]["ratio"] = args.ratio
        if args.pool_id > 0:
            self.mode = "pool"
            self.crawler = pool_crawler(settings, args.pool_id)
        else:
            self.crawler = post_crawler(settings)
        if not self.crawler.output_folder:
            return
        init_logger(args.log.upper(), join(self.crawler.output_folder, f"log_{strftime('%Y-%m-%d %H-%M-%S')}.txt"))
        if self.mode == "pages":
            self.last_stop_id = settings["last_stop_id"]
        elif self.mode == "tags":
            self.last_stop_id = settings["tagSearch_last_stop_id"]

    def can_run(self) -> bool:
        return bool(self.crawler.output_folder)

    async def _main_loop(self) -> None:
        queue_put_count = 0
        await self.crawler.next_page()
        while post := await self.crawler.get_post():
            post_id = post["id"]
            logging.info(f"{post_id} 符合下载条件")
            if self.latest_post_id == 0:
                self.latest_post_id = post_id
                if self.mode == "pages":
                    self.settings["last_stop_id"] = (post_id if self.crawler.start_page > 1 else max(self.settings["last_stop_id"], post_id))
                elif self.mode == "tags":
                    self.settings["tagSearch_last_stop_id"] = post_id
            if self.mode != "pool" and post_id <= self.last_stop_id:
                logging.warning("达到上次爬取终止位置")
                break
            # post过滤器，按条件判断是否应该下载
            # await self.queue.put({"id": post_id, "url": post["file_url"], "size": post["file_size"], "fname": post["file_name"], "fext": post.get("file_ext", splitext(post["file_name"])[1][1:])})
            await self.queue.put(post)
            queue_put_count += 1
            logging.debug(f"{post_id} 已添加到队列")
            if queue_put_count > 30 or len(self.crawler.payload) < 10:
                await self.qsize_low.wait()  # 等待下载线程通知队列中任务量不足
                self.qsize_low.clear()
                flag_not_end = await self.crawler.next_page()
                if not flag_not_end and not self.task_clear.is_set():
                    self.task_clear.set()  # 通知下载线程无可用任务
                    logging.debug("已请求完所有post的信息")
                queue_put_count = 0

    async def run(self) -> None:
        await self._main_loop()
        logging.info("已处理所有post信息" + "，等待下载线程" if self.queue.qsize() else "")
        if not self.task_clear.is_set():
            self.task_clear.set()  # 写入终止标志
        await self.crawler.close()
        loop = asyncio.get_event_loop()
        while (atask_count := len(asyncio.all_tasks(loop))) and atask_count > 1:
            logging.info(f"{atask_count}个线程仍在运行")
            qsize = self.queue.qsize()
            await asyncio.sleep(max(1, min(10, 2*qsize)))  # 根据队列中任务量决定等待时间，不考虑复杂情况
        if self.mode != "pool":
            async with aopen('config.json', 'w', encoding='utf-8') as f:
                await f.write(dumps(self.settings, indent=4, ensure_ascii=False))
        logging.debug("抓取线程退出")


# 消费者线程：从data队列获取post并执行下载
class parallel_task:
    def __init__(self, signals: shared_signals) -> None:
        self.queue: asyncio.Queue = signals.queue
        self.qsize_low: asyncio.Event = signals.qsize_low
        self.task_clear: asyncio.Event = signals.task_clear
        self.file_write_queue: asyncio.Queue = signals.write_queue
        self.session: ClientSession = None
        self.total_file_size = 0

    async def _download(self, post: dict) -> None:
        if self.session is None:
            self.session = ClientSession(headers=headers)
        logging.info(f"{post['id']} 下载开始，大小：{format_size(post['size'])}，类型：{post['fext']}，开始于{strftime('%H:%M:%S')}")
        ts = time()
        img, size = await asyncget(self.session, post['url'], special_headers={'Host': 'files.yande.re', 'Referer': f"https://yande.re/post/show/{post['id']}"})
        if img is None:
            logging.error(f"{post['id']} 下载失败")
            return
        cost_time = time() - ts
        self.total_file_size += size
        logging.info(f"{post['id']} 下载完毕，耗时{cost_time:>5.2f}s，平均速度{format_size(post['size']/cost_time)}/s")
        self.total_file_size += post['size']
        await self.file_write_queue.put((post['fname'], img))

    async def _main_loop(self) -> None:
        while True:
            try:
                post = await asyncio.wait_for(self.queue.get(), timeout=1)
                self.queue.task_done()
            except asyncio.TimeoutError:
                logging.debug("下载线程正在等待")
                if self.task_clear.is_set():
                    logging.debug("无可用下载任务，下载线程准备退出")
                    if self.session is not None:
                        await self.session.close()
                    return
                continue
            if self.total_file_size > 1073741824:  # 每下载1G刷新session
                await self.session.close()
                self.session = ClientSession(headers=headers)
            if self.queue.qsize() < 10 and not self.qsize_low.is_set():
                self.qsize_low.set()  # 通知生产者线程队列中任务不足
            await self._download(post)
            # 两次下载间随机间隔，高频访问会被暂时阻止连接
            # 生产者线程更新数据库时建议启用
            # await asyncio.sleep(uniform(0.5, 10.0))

    async def run(self) -> None:
        await self._main_loop()
        logging.debug("下载线程退出")


if __name__ == "__main__":
    main()
