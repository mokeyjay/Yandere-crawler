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

settings = Function.read_settings(Function.get('config.json'))
# 开始页码，结束页码，图片比例，图片类型，图片尺寸{最小/最大像素：宽、高、宽高比，上次终止图片ID}
# 当前未进行图片类型筛选

if input('使用默认设置/上次设置吗？若第一次使用则为默认设置，否则为上次设置：(y/n)') == 'n':
    settings = Function.get_settings(settings)

page = settings['start_page']
max_page = settings['stop_page']
pic_type = settings['pic_type']
pic_size = settings['pic_size']

# 创建目录存放今天爬下来的图
Function.create_folder()

start_time = str(int(time.time()))
last_start_id = settings['last_stop_id']  # 上次开始爬取时第一张图片ID。爬到此ID则终止此次爬取
Log.add('目标图片ID'+str(last_start_id))
i = 0  # 当前第几张
end = False  # 爬取是否已结束

while True:

    # 终止页码为0 或 未到达终止页码时 才进行爬取
    if max_page == 0 or page <= max_page:
        # 获取页面内容
        Log.add('\n正在读取第'+str(page)+'页……')
        json_data = Yandere.get_json(page)
        # 获取每个li的内容
        for li in Yandere.get_li(json_data):
            i += 1
            info = Yandere.get_info(li) # (id, size, ext, img_url, width, height)
            width = info[4]
            height = info[5]

            # 存储last_start_id
            if i == 1:
                if len(info) == 6:
                    settings['last_stop_id'] = int(info[0])
                    Function.write('config.json', json.dumps(settings), True)
                else:
                    # 第一张个li就出现了问题，这就无法存储last_start_id了
                    exit()

            # 数据结构是否错误？
            if len(info) != 6:
                Log.add(str(i) + ' 错误，跳过')
                continue

            # 已经爬到上次开始爬的地方了 且 终止页码为0 本次爬取结束
            if int(info[0]) == last_start_id and max_page == 0:
                end = True
                break

            download = False  # 是否下载此图？
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
                Log.add('图片比例不符，跳过')
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
                Log.add('图片尺寸不符，跳过')
                continue

            if download:
                # 获取文件名
                # URL解码
                file_name = urllib.parse.unquote(info[3].split('/')[-1])
                file_name = Function.char_replace(file_name)
                # 文件是否已存在？
                if Function.exists(file_name):
                    Log.add(info[0] + ' 已存在，跳过')
                    continue

                Log.add(str(i) + '. ' + datetime.datetime.now().strftime('%H:%M:%S') + ' 开始下载p' + info[0] + ' 大小' + str("%.2f" %(info[1]/1048576)) + 'M 类型' + info[2])
                ts = time.time()
                img = Http.get(info[3], {'Host': 'files.yande.re', 'Referer': 'https://yande.re/post/show/'+info[0]})
                cost_time = int(time.time() - ts) # 秒级精度可能导致0秒
                if cost_time:
                    aver_speed = info[1]/1024/cost_time
                else:
                    aver_speed = info[1]/1024
                Log.add('下载完毕，耗时' + str(cost_time) + 's, 平均速度' + str("%.2f" %aver_speed) + 'k/s')

                Function.write(file_name, img)
                # 据说站长也很穷，减轻点服务器压力吧
                sleep_time = random.uniform(0.5,10.0)
                Log.add('计划休眠时间' + str("%.2f" %(sleep_time)) + 's')
                Function.add('log_' + start_time + '.txt', Log.get())
                Log.reset()
                time.sleep(sleep_time)

        if end:
            break
    else:
        break

    page += 1

Log.add('爬取结束')
exit(200)