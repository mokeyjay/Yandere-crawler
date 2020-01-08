#!/usr/bin/env python3

import time
import random
import threading
import queue
import Http
import Yandere
import Function


def switch_convert(status):
    # 非大小写'y'输入均被判断为否定，包括回车
    if status == 'y' or status == 'Y':
        return True
    else:
        return False


def compare(width, height):
    # 懒得写一串选项判断
    if width > height:
        return 1
    elif width < height:
        return 2
    else:
        return 3


def input_settings(settings: dict):
    settings['start_page'] = int(input('开始页码：'))
    settings['stop_page'] = int(input('停止页码，为0时爬取至上次终止图片，非0时爬完此页即停止：'))
    settings['pic_type'] = int(input('图片比例，0=全部 1=横图 2=竖图 3=正方形：'))
    settings['folder_path'] = input('保存路径：')
    settings['tag_search'] = switch_convert(input('启用tag搜索? (y/n)'))
    return settings


def judge(post, settings, discard_tags):
    # pending判断
    # 发现其他状态类型，将判断条件从“仅active”改为“排除pending”
    if settings['status_check']:
        if post['status'] == 'pending':
            add_log('{} is {}，跳过。原因：{}'.format(post['id'], post['status'], post['flag_detail']['reason']))
            return False
    # 分级判断
    if settings['safe_mode']:
        if post['rating'] == 'e':
            return False
    # 排除tag判断
    if settings['tag_search']:
        if list(set(discard_tags).intersection(set(post['tags'].strip(' ').split(' ')))):
            add_log(post['id'] + ' 包含待排除tags，跳过')
            return False
    # 文件体积判断
    if settings['file_size_limit']:
        if post['file_size'] > settings['file_size']:
            add_log(post['id'] + ' 超过体积限制，跳过')
            return False
    # 图片比例判断
    # 由于预览图经过压缩，因此判断预览图尺寸会比原图多出一点冗余
    if settings['pic_type']:
        if not (settings['pic_type'] == compare(post['preview_width'], post['preview_height'])):
            add_log(post['id'] + ' 比例不符，跳过')
            return False
    # 图片宽高比判断
    proportion = post['preview_width'] / post['preview_height']
    pic_size = settings['pic_size']
    if proportion < pic_size['min']['proportion'] or (pic_size['max']['proportion'] and proportion > pic_size['max']['proportion']):
        add_log(post['id'] + ' 宽高比不符，跳过')
    # 图片尺寸判断
    width = post['width']
    height = post['height']
    if width < pic_size['min']['width'] or height < pic_size['min']['height']:
        add_log(post['id'] + ' 小于最小尺寸要求，跳过')
        return False
    else:
        if (pic_size['max']['width'] and width > pic_size['max']['width']) or (pic_size['max']['height'] and height > pic_size['max']['height']):
            add_log(post['id'] + ' 大于最大尺寸限制，跳过')
            return False
    #下载判断
    # 获取文件名并解码
    file_name = Function.rename(Http.decode(post['file_url']))
    # 文件是否已存在？
    # 尝试读取以id:[文件名,大小]为键值对的存放保存目录下所有符合指定命名规则的图片的字典
    # 基于以下前提：Y站不会修改文件命名规则；已张贴的post其二进制文件不会被修改(二进制文件内容，大小、扩展名)，只有tags被修改。大小检查用于修正因意外导致的下载错误。
    if post['id'] in exist_files_dict:
        if exist_files_dict[post['id']][1] == post['file_size']:
            if exist_files_dict[post['id']][0] == file_name:
                add_log(post['id'] + ' 已存在，跳过')
            else:
                Function.rename_file(folder_path, exist_files_dict[post['id']][0], file_name)
                add_log(post['id'] + ' tags变化，重命名原始文件')
            return False
        else:
            print('发现文件更新：{}'.format(post['id']))


    # 所有条件满足
    return True


def download(post):
    file_name = Function.rename(Http.decode(post['file_url']))
    add_log('{} 开始下载p{} 大小{}M 类型{}'.format(time.strftime('%H:%M:%S'), post['id'], "%.2f" % (post['file_size'] / 1048576), post['file_ext']))
    ts = time.time()
    img = Http.get(post['file_url'], {'Host': 'files.yande.re', 'Referer': 'https://yande.re/post/show/' + post['id']})
    cost_time = time.time() - ts
    add_log('{}下载完毕，耗时{}s，平均速度{}k/s'.format(post['id'], "%.2f" %cost_time, "%.2f" % (post['file_size'] / 1024 / cost_time)))
    Function.write(folder_path, file_name, img)


def add_log(content):
    # 给输出加锁。避免文件写入冲突与UI输出异常。
    log_lock.acquire()
    print(content)
    # 因为没有错误处理所以要将日志立刻写入文件防止丢失
    Function.add(folder_path, log_file_name, content + '\n')
    log_lock.release()


def main(settings: dict, tags: str, discard_tags: str):
    global log_file_name
    global folder_path
    global log_lock
    global exist_files_dict
    end = threading.Event()
    data = queue.Queue(80)
    log_lock = threading.Lock()
    lock = threading.Condition()
    log_file_name = 'log_{}.txt'.format(time.strftime('%Y%m%d-%H%M%S'))
    if settings['tag_search']:
        folder_path = settings['folder_path'] + '/' + tags
    elif settings['date_separate']:
        folder_path = settings['folder_path'] + '/' + time.strftime('%Y%m%d')
        log_file_name = 'log_{}.txt'.format(time.strftime('%H%M%S'))
    else:
        folder_path = settings['folder_path']
    Function.create_folder(folder_path)
    # 遍历文件存放目录，获取所有已有文件名。不检索子目录。
    exist_files_dict = Function.existing(folder_path)
    # 将排除tags转换为列表
    discard_tags = discard_tags.strip(' ').split(' ')
    # 将易读的空格分隔转换为加号分隔，urllib无法处理空格，会报错
    tags = tags.replace(' ', '+')

    # 建立线程
    # 只启用了单线程，低内存设备不建议启用多线程
    get_data(lock, data, end, settings, tags, discard_tags)
    parallel_task(lock, data, end, settings).join()


# 子线程共用类
class task_thread(threading.Thread):
    def __init__(self, lock, queue, event, settings):
        threading.Thread.__init__(self)
        self.daemon = True
        self.lock = lock
        self.queue = queue
        self.event = event
        self.settings = settings
        self.start()


# 生产者线程：抓取页面，将post元素补充入data队列
class get_data(task_thread):
    def __init__(self, lock, queue, event, settings, tags, discard_tags):
        task_thread.__init__(self, lock, queue, event, settings)
        self.tags = tags
        self.discard_tags = discard_tags
    def run(self):
        lock = self.lock
        data = self.queue
        end = self.event
        settings = self.settings
        tag_on = settings['tag_search']
        page = settings['start_page']
        stop_page = settings['stop_page']
        if tag_on:
            last_stop_id = settings['tagSearch_last_stop_id']
        else:
            last_stop_id = settings['last_stop_id']
        while not end.is_set():
            with lock:
                if data.qsize() < 20:
                    if page <= stop_page or not stop_page:
                        add_log('正在读取第{}页……'.format(str(page)))
                        origin = Yandere.get_li(Yandere.get_json(page, tag_on, self.tags))
                        if len(origin):
                            if page == settings['start_page']:
                                post = origin[0]
                                if post['id'] > last_stop_id:  # 考虑开始页不是第一页的情况
                                    if tag_on:
                                        settings['tagSearch_last_stop_id'] = post['id']
                                    else:
                                        settings['last_stop_id'] = post['id']
                                Function.write(settings['folder_path'], 'config.json', Yandere.return_json(settings), True)  # 我超尖欸
                                if tag_on:
                                    settings['tagSearch_last_stop_id'] = last_stop_id
                                else:
                                    settings['last_stop_id'] = last_stop_id
                            for post in origin:
                                if post['id'] <= last_stop_id:
                                    add_log('达到上次爬取终止位置')
                                    end.set()
                                    break
                                post['id'] = str(post['id'])
                                if judge(post, settings, self.discard_tags):
                                    data.put(post)
                            page += 1
                            lock.notify(1)
                        else:
                            end.set()
                            lock.notify_all()
                            add_log('页面为空\n所有页面读取完毕')
                    else:
                        end.set()
                else:
                    lock.wait()


# 消费者线程：从data队列获取post并根据条件筛选，满足条件执行下载
class parallel_task(task_thread):
    def run(self):
        lock = self.lock
        data = self.queue
        end = self.event
        settings = self.settings
        stop_page = settings['stop_page']
        if settings['tag_search']:
            last_stop_id = settings['tagSearch_last_stop_id']
        else:
            last_stop_id = settings['last_stop_id']
        while True:
            if lock.acquire():
                if data.qsize():
                    post = data.get(0)
                    data.task_done()
                    lock.notify(1)
                    if int(post['id']) <= last_stop_id and not stop_page:
                        # 达到上次爬取位置，跳出循环
                        add_log('达到上次爬取终止位置')
                        end.set()
                        lock.notify_all()
                        lock.release()
                        break
                    else:
                        lock.release()
                    download(post)
                    # 两次下载间随机间隔，虽然不觉得有啥用
                    time.sleep(random.uniform(0.5, 10.0))
                    continue
                else:
                    if end.is_set():
                        lock.notify_all()
                        lock.release()
                        break
                    else:
                        lock.wait()
                lock.release()


if __name__ == "__main__":
    # 获取设置
    settings = Yandere.get_li(Function.read('config.json'))
    # 为定时任务做出修改，条件为真时跳过输入设置直接开始下载
    if settings['task_mode']:
        tags = settings['tags']
        discard_tags = settings['discard_tags']
    else:
        if not switch_convert(input('使用上次设置? (y/n)')):
            input_settings(settings)
        if settings['tag_search']:
            tags = input('tag搜索已启用，请输入要搜索的tags，多个tag以空格分隔：')
            discard_tags = input('要排除的tags，多个tag以空格分隔, 不排除则按回车跳过：')
            print('警告：改变tags后，爬取至上次停止图片时停止功能可能失效\n本次爬取图片标签：' + tags + '\n本次排除标签：' + discard_tags)
        else:
            tags = ''
            discard_tags = ''

    # 开始运行
    main(settings, tags, discard_tags)
