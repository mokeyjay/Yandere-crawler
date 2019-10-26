#!/usr/bin/env python3

import urllib.request
import urllib.parse
import json
import time
import datetime
import random
import Yandere
import Function
import Http
import Log

tag_on = input('搜索tags？(y/n)')
if tag_on != 'n':
    print('请自行寻找有效tag，如:landscape\n多tag用法示范:landscape banishment')
    tags = input('输入tags，多个tag以空格分隔：')
    discard_tags = input('要排除的tags，多个tag以空格分隔,不排除则按回车跳过：')
    print('警告：改变tags后，爬取至上次停止图片时停止功能可能失效\n本次爬取图片标签：' + tags + '\n本次排除标签：' + discard_tags)
    # 将排除tags转换为列表
    discard_tags = discard_tags.strip(' ').split(' ')
    # 将易读的空格分隔转换为加号分隔，urllib无法处理空格，会报错
    tags = tags.replace(' ', '+')

settings = Function.read_settings(Function.get('config.json'))
# 开始页码，结束页码，图片比例，图片类型，图片尺寸{最小/最大像素：宽、高、宽高比，上次终止图片ID，保存路径，体积限制、下载延迟、安全模式、争议过滤开/关}
# 当前未进行图片类型筛选

if input('使用默认设置/上次设置吗？若第一次使用则为默认设置，否则为上次设置：(y/n)') == 'n':
    settings = Function.get_settings(settings)
    # 写入设置
    Function.write('config.json', json.dumps(settings), True)

page = settings['start_page']
max_page = settings['stop_page']
pic_type = settings['pic_type']
pic_size = settings['pic_size']

# 创建目录存放今天爬下来的图
Function.create_folder()

start_time = str(int(time.time()))
if tag_on != 'n':
    last_start_id = settings['last_stop_id']  # 上次开始爬取时第一张图片ID。爬到此ID则终止此次爬取
else:
    last_start_id = settings['tagSearch_last_start_id']
Log.add('目标图片ID'+str(last_start_id))
i = 0  # 当前第几张
end = False  # 爬取是否已结束

while True:

    # 终止页码为0 或 未到达终止页码时 才进行爬取
    if max_page == 0 or page <= max_page:
        # 获取页面内容
        Log.add('\n正在读取第'+str(page)+'页……')
        json_data = Yandere.get_json(page, tag_on, tags)
        # 获取每个li的内容
        for li in Yandere.get_li(json_data):
            if li == '':
                print('此页无内容')
                break
            i += 1
            info = Yandere.get_info(li) # (id, tags, size, ext, img_url, rating, status, width, height, score, jpeg_file_size, jpeg_url, jpeg_width, jpeg_height)
            width = info[7]
            height = info[8]

            # 存储last_start_id
            if i == 1:
                if len(info) == 14:
                    if tag_on != 'n':
                        settings['tagSearch_last_stop_id'] = int(info[0])
                    else:
                        settings['last_stop_id'] = int(info[0])
                    Function.write('config.json', json.dumps(settings), True)
                else:
                    # 第一张个li就出现了问题，这就无法存储last_start_id了
                    exit()

            # 数据结构是否错误？
            if len(info) != 14:
                Log.add(str(i) + ' 错误，跳过')
                continue

            # 已经爬到上次开始爬的地方了 且 终止页码为0 本次爬取结束
            if int(info[0]) <= last_start_id and max_page == 0:
                end = True
                break

            download = False  # 是否下载此图？
            
            # 丢弃包含排除tags的post
            # 获取discard_tags与info[1]的差集，以列表形式输出
            if list(set(discard_tags).intersection(set(info[1].strip(' ').split(' ')))):
                Log.add(info[0] + ' 包含应排除tag(s)，跳过')
                continue
            else:
                download = True

            # 限制下载文件体积
            if settings['file_size_limit']:
                if info[10] > settings['file_size']:
                    Log.add(info[0] + ' 体积超限，跳过')
                    continue
                else:
                    if info[2] > settings['file_size']:
                        Log.add(info[0] + '原图尺寸超限，获取最大压缩图片')
                        info[2] = info[10]
                        info[3] = 'jpg'
                        width = info[12]
                        height = info[13]
                        info[4] = info[11]
                    download = True
            else:
                download = True

            # 判断图片比例（不想写一长串……只好如此了）
            if pic_type == 0:
                download = True
            elif pic_type == 1 and width > height:
                download = True
            elif pic_type == 2 and width < height:
                download = True
            elif pic_type == 3 and width == height:
                download = True
            else:
                Log.add(info[0] + ' 比例不符，跳过')
                continue
            # 判断图片尺寸
            if width >= pic_size['min']['width'] and height >= pic_size['min']['height']:
                if pic_size['max']['width'] and width > pic_size['max']['width']:
                    download = False
                if pic_size['max']['height'] and height > pic_size['max']['height']:
                    download = False
            else:
                download = False
            # 判断图片宽高比
            proportion = width / height
            if proportion < pic_size['min']['proportion'] or (pic_size['max']['proportion'] and proportion > pic_size['max']['proportion']):
                download = False
            if not download:
                Log.add(info[0] + ' 尺寸不符，跳过')
                continue

            if info[5] != 'e' or not settings['safe_mode']:
                download = True
            else:
                continue

            # 只下载可见图片
            if info[6] == 'active' and settings['status_active_only']:
                download = True
            else:
                Log.add(info[0] + '审核中，跳过')
                continue

            if download:
                # 获取文件名
                # URL解码
                file_name = urllib.parse.unquote(info[4].split('/')[-1])
                file_name = Function.char_replace(file_name)
                # 文件是否已存在？
                if Function.exists(file_name):
                    Log.add(info[0] + ' 已存在，跳过')
                    continue

                Log.add(str(i) + '. ' + datetime.datetime.now().strftime('%H:%M:%S') + ' 开始下载p' + info[0] + ' 大小' + str("%.2f" %(info[2]/1048576)) + 'M 类型' + info[3])
                ts = time.time()
                img = Http.get(info[4], {'Host': 'files.yande.re', 'Referer': 'https://yande.re/post/show/' + info[0]})
                cost_time = int(time.time() - ts) # 秒级精度可能导致0秒
                if cost_time:
                    aver_speed = info[2]/1024/cost_time
                else:
                    aver_speed = info[2]/1024
                Log.add('下载完毕，耗时' + str(cost_time) + 's, 平均速度' + str("%.2f" %aver_speed) + 'k/s')

                Function.write(file_name, img)
                # 据说站长也很穷，减轻点服务器压力吧
                sleep_time = random.uniform(0.5,10.0)
                Log.add('计划休眠时间' + str("%.2f" %(sleep_time)) + 's')
                Function.add('log_' + start_time + '.txt', Log.get())
                Log.reset()
                time.sleep(sleep_time)
        Function.add('log_' + start_time + '.txt', Log.get())
        Log.reset()

        if end:
            break
    else:
        break

    page += 1

Log.add('爬取结束')
exit(200)