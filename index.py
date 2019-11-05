#!/usr/bin/env python3

import time
import random
import threading
import Http
import Yandere
import Function


def switch_convert(status):
    # 将选项转换为1/0以便判断，倒不是我忘了用bool……
    # 非大小写'y'输入均被判断为否定，包括回车
    if status == 'y' or status == 'Y':
        return 1
    else:
        return 0

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

    if switch_convert(input('选择是否重设图片尺寸限制条件。若重设，输入为0则不限制下载尺寸；若不重设，将从配置文件读取上次条件 (y/n)')):
        settings['pic_size']['min']['width'] = int(input('最小宽度：'))
        settings['pic_size']['min']['height'] = int(input('最小高度：'))
        settings['pic_size']['min']['proportion'] = int(input('最小宽高比：'))
        settings['pic_size']['max']['width'] = int(input('最大宽度：'))
        settings['pic_size']['max']['height'] = int(input('最大高度：'))
        settings['pic_size']['max']['proportion'] = int(input('最大宽高比：'))

    settings['file_size_limit'] = switch_convert(input('限制图片体积？(y/n)'))
    if settings['file_size_limit']:
        settings['file_size'] = int(input('最大文件体积，单位兆字节(MB)：')) * 1048576

    settings['folder_path'] = input('保存路径：')
    settings['tag_search'] = switch_convert(input('启用tag搜索? (y/n)'))
    settings['random_delay'] = switch_convert(input('是否启用下载延迟？(y/n)'))
    settings['safe_mode'] = switch_convert(input('是否过滤NSFW内容? (y/n)'))
    settings['status_check'] = switch_convert(input('不下载待审核图片？(y/n) ※ "待审核"状态多由低质量触发'))

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
    
    # 所有条件满足
    return True

def download(post):
    global folder_path
    # 获取文件名并解码
    # 没错我就是嵌套狂魔
    file_name = Function.rename(Http.decode(post['file_url']))
    # 文件是否已存在？
    # 提醒：存在已知问题
    # 如果网站上post的tags被修改，那么两次爬取的文件名是不同的，exist方法将返回假。这样会造成相同文件重复写入。只有“爬取至上次终止位置”不会出现此问题。
    # ——又不是不能用.jpg
    if Function.exists(folder_path, file_name):
        add_log(post['id'] + ' 已存在，跳过')
        return True

    add_log('{} 开始下载p{} 大小{}M 类型{}'.format(time.strftime('%H:%M:%S'), post['id'], "%.2f" %(post['file_size'] / 1048576), post['file_ext']))
    ts = time.time()
    img = Http.get(post['file_url'], {'Host': 'files.yande.re', 'Referer': 'https://yande.re/post/show/' + post['id']})
    cost_time = time.time() - ts
    add_log('{}下载完毕，耗时{}s，平均速度{}k/s'.format(post['id'], "%.2f" %cost_time, "%.2f" %(post['file_size'] / 1024 / cost_time)))

    Function.write(folder_path, file_name, img)

def add_log(content):
    global mode
    global container
    global log_file_name
    global folder_path
    # 因为没有错误处理所以要将日志立刻写入文件防止丢失
    if mode:
        # 日志输出判断，终端或UI
        print(content)
    else:
        container.insert('end', content + '\n')
        container.see('end')
    Function.add(folder_path, log_file_name, content + '\n')

def main(settings: dict, tags: str, discard_tags: str, output_container, output_mode: str):
    global end
    global data
    global mode
    global container
    global log_file_name
    global folder_path
    global lock
    end = False
    data = []
    mode = output_mode
    container = output_container
    log_file_name = 'log_{}.txt'.format(time.strftime('%H-%M-%S'))
    folder_path = settings['folder_path'] + '/' + time.strftime('%Y%m%d')
    lock = threading.Condition()
    Function.create_folder(folder_path)

    # 建立线程
    # 只启用了单线程
    get_data(settings, tags)
    parallel_task(settings, discard_tags).join()

# 也可以不用进程锁
# 生产者线程：抓取页面，将post元素补充入data队列
class get_data(threading.Thread):
    def __init__(self, settings, tags):
        threading.Thread.__init__(self)
        self.daemon = True
        self.settings = settings
        self.tags = tags
        self.start()
    def run(self):
        global end
        global lock
        global data
        settings = self.settings
        tag_on = settings['tag_search']
        page = settings['start_page']
        stop_page = settings['stop_page']
        if tag_on:
            last_stop_id = settings['tagSearch_last_stop_id']
        else:
            last_stop_id = settings['last_stop_id']
        tags = self.tags
        while True:
            if lock.acquire():
                if end:
                    lock.release()
                    break
                if len(data) < 10:
                    if page <= stop_page or not stop_page:
                        add_log('正在读取第{}页……'.format(str(page)))
                        origin = Yandere.get_li(Yandere.get_json(page, tag_on, tags))
                        if len(origin):
                            data.extend(origin)
                        else:
                            end = True
                            add_log('所有页面读取完毕')
                            lock.release()
                            break
                        if page == settings['start_page']:
                            post = data[0]
                            if post['id'] > last_stop_id:# 考虑开始页不是第一页的情况
                                if tag_on:
                                    settings['tagSearch_last_stop_id'] = post['id']
                                else:
                                    settings['last_stop_id'] = post['id']
                            Function.write(settings['folder_path'], 'config.json', Yandere.return_json(settings), True)
                            if tag_on:
                                settings['tagSearch_last_stop_id'] = last_stop_id
                            else:
                                settings['last_stop_id'] = last_stop_id
                        page += 1
                        lock.notify(1)
                    else:
                        end = True
                        lock.release()
                        break
                else:
                    lock.wait()
                lock.release()

# 消费者线程：从data队列获取post并根据条件筛选，满足条件执行下载
class parallel_task(threading.Thread):
    def __init__(self, settings, discard_tags):
        threading.Thread.__init__(self)
        self.daemon = True
        self.settings = settings
        self.discard_tags = discard_tags
        self.start()
    def run(self):
        global end
        global lock
        global data
        settings = self.settings
        stop_page = settings['stop_page']
        delay_on = settings['random_delay']
        if settings['tag_search']:
            last_stop_id = settings['tagSearch_last_stop_id']
        else:
            last_stop_id = settings['last_stop_id']
        while True:
            if lock.acquire():
                if len(data):
                    post = data.pop(0)
                    time.sleep(0.002)
                    lock.notify(1)
                    if post['id'] <= last_stop_id and not stop_page:
                        # 达到上次爬取位置，跳出循环
                        add_log('达到上次爬取终止位置')
                        end = True
                        lock.release()
                        break
                    else:
                        lock.release()
                    post['id'] = str(post['id'])
                    if judge(post, settings, self.discard_tags):
                        download(post)
                        if delay_on:
                            # 两次下载间随机间隔，虽然不觉得有啥用
                            time.sleep(random.uniform(0.5, 10.0))
                    continue
                else:
                    if end:
                        lock.release()
                        break
                    else:
                        lock.wait()
                lock.release()


if __name__ == "__main__":
    # 获取设置
    settings = Yandere.get_li(Function.read('config.json'))
    if not switch_convert(input('使用上次设置? (y/n)')):
        input_settings(settings)
    if settings['tag_search']:
        tags = input('tag搜索已启用，请输入要搜索的tags，多个tag以空格分隔：')
        discard_tags = input('要排除的tags，多个tag以空格分隔, 不排除则按回车跳过：')
        print('警告：改变tags后，爬取至上次停止图片时停止功能可能失效\n本次爬取图片标签：' + tags + '\n本次排除标签：' + discard_tags)
        # 将排除tags转换为列表
        discard_tags = discard_tags.strip(' ').split(' ')
        # 将易读的空格分隔转换为加号分隔，urllib无法处理空格，会报错
        tags = tags.replace(' ', '+')
    else:
        tags = ''
        discard_tags = ''
    
    # 开始运行
    main(settings, tags, discard_tags, '', True)
    