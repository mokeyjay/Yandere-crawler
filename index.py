#!/usr/bin/env python3

import Yandere
import urllib.request
import urllib.parse
import time
import Log
import Function
import Http

# 页码
page = 2
# 终止页码。为0时根据last_start_id来判断是否停止爬取；非0时爬完此页即停止
# 此参数必须 >= page
max_page = 2
# 要下载的图片类型。0=全部 1=横图 2=竖图 3=正方形
pic_type = 1
# 图片尺寸限制。0为不限制
pic_size = {
    'min': {'width': 0, 'height': 0},
    'max': {'width': 0, 'height': 0},
}

# 创建目录存放今天爬下来的图
Function.create_folder()

last_start_id = int(Function.get('last_start_id.data'))  # 上次开始爬取时第一张图片ID。爬到此ID则终止此次爬取
i = 0  # 当前第几张
end = False  # 爬取是否已结束

while True:

    # 终止页码为0 或 未到达终止页码时 才进行爬取
    if max_page == 0 or page <= max_page:
        # 获取页面内容
        Log.add('正在读取第'+str(page)+'页……')
        html = Yandere.get_html(page)
        # 获取每个li的内容
        for li in Yandere.get_li(html):
            i += 1
            info = Yandere.get_info(li)[0]  # (id, img_url, width, height)

            # 存储last_start_id
            if i == 1:
                if len(info) == 4:
                    Function.write('last_start_id.data', info[0], True)
                else:
                    # 第一张个li就出现了问题，这就无法存储last_start_id了
                    exit()

            # 数据结构是否错误？
            if len(info) != 4:
                Log.add(str(i) + ' 错误，跳过')
                continue

            # 已经爬到上次开始爬的地方了 且 终止页码为0 本次爬取结束
            if int(info[0]) == last_start_id and max_page == 0:
                end = True
                break

            download = False  # 是否下载此图？
            # 不想写一长串……只好如此了
            if pic_type == 0:
                download = True
            elif pic_type == 1 and info[2] > info[3]:
                download = True
            elif pic_type == 2 and info[2] < info[3]:
                download = True
            elif pic_type == 3 and info[2] == info[3]:
                download = True
            else:
                Log.add('图片类型不符，跳过')
                continue

            # todo 判断尺寸限制……

            if download:
                # 获取文件名，并进行url解码
                file_name = info[1].split('/')[-1]
                file_name = urllib.parse.unquote(file_name)
                # 文件是否已存在？
                if Function.exists(file_name):
                    Log.add(info[0] + ' 已存在，跳过')
                    continue

                Log.add(str(i)+' - ' + info[0] + ' 开始下载……')
                ts = time.time()
                img = Http.get(info[1], {'Host': 'files.yande.re', 'Referer': 'https://yande.re/post/show/'+info[0]})
                Log.add('下载完毕。耗时：'+str(int(time.time() - ts))+'s')

                Function.write(file_name, img)

        if end:
            break
    else:
        break

    page += 1

Log.add('爬取结束')
Function.write('log_' + str(int(time.time())) + '.txt', Log.get())
exit(200)