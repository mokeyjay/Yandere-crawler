import time
import random
import Http
import Yandere
import Function
import Log

def switch_convert(status):
    if status == 'y':
        return 1
    else:
        return 0

def compare(width, height):
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

    print('输入图片尺寸限制条件，为0则不限制：')
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
    settings['status_active_only'] = switch_convert(input('不下载待审核图片？(y/n) ※ "待审核"状态多由低质量触发'))

    return settings

def judge(post, settings, discard_tags):
    #pending判断
    if settings['status_active_only']:
        if post['status'] != 'active':
            Log.add(post['id'] + ' is pending，跳过')
            return False
    #分级判断
    if settings['safe_mode']:
        if post['rating'] == 'e':
            return False
    #排除tag判断
    if settings['tag_search']:
        if list(set(discard_tags).intersection(set(post['tags'].strip(' ').split(' ')))):
            Log.add(post['id'] + ' 包含待排除tags，跳过')
            return False
    #文件体积判断
    if settings['file_size_limit']:
        if post['file_size'] > settings['file_size']:
            Log.add(post['id'] + ' 超过体积限制，跳过')
            return False
    #图片比例判断
    #由于预览图经过压缩，因此判断预览图尺寸会比原图多出一点冗余
    if settings['pic_type']:
        if not (settings['pic_type'] == compare(post['preview_width'], post['preview_height'])):
            Log.add(post['id'] + ' 比例不符，跳过')
            return False
    #图片宽高比判断
    proportion = post['preview_width'] / post['preview_height']
    pic_size = settings['pic_size']
    if proportion < pic_size['min']['proportion'] or (pic_size['max']['proportion'] and proportion > pic_size['max']['proportion']):
        Log.add(post['id'] + ' 宽高比不符，跳过')
    #图片尺寸判断
    width = post['width']
    height = post['height']
    if width < pic_size['min']['width'] or height < pic_size['min']['height']:
        Log.add(post['id'] + ' 小于最小尺寸要求，跳过')
        return False
    else:
        if (pic_size['max']['width'] and width > pic_size['max']['width']) or (pic_size['max']['height'] and height > pic_size['max']['height']):
            Log.add(post['id'] + ' 大于最大尺寸限制，跳过')
            return False
    
    #所有条件满足
    return True

def download(post, folder_path):
    # 获取文件名
    # URL解码
    file_name = Http.decode(post['file_url'])
    file_name = Function.rename(file_name)
    # 文件是否已存在？
    if Function.exists(folder_path, file_name):
        Log.add(post['id'] + ' 已存在，跳过')
        return True

    Log.add(time.strftime('%H:%M:%S') + ' 开始下载p' + post['id'] + ' 大小' + str("%.2f" %(post['file_size'] / 1048576)) + 'M 类型' + post['file_ext'])
    ts = time.time()
    img = Http.get(post['file_url'], {'Host': 'files.yande.re', 'Referer': 'https://yande.re/post/show/' + post['id']})
    cost_time = time.time() - ts
    Log.add('下载完毕，耗时' + str("%.2f" %cost_time) + 's, 平均速度' + str("%.2f" %(post['file_size'] / 1024 / cost_time)) + 'k/s')

    Function.write(folder_path, file_name, img)

def write_log(folder_path, start_time):
    Function.add(folder_path, 'log_' + start_time + '.txt', Log.get())
    Log.reset()


if __name__ == "__main__":
    #获取设置
    settings = Yandere.get_li(Function.read('config.json'))
    if not switch_convert(input('使用上次设置? (y/n)')):
        input_settings(settings)
        
    page = settings['start_page']
    stop_page = settings['stop_page']
    last_stop_id = settings['last_stop_id']
    tag_on = settings['tag_search']
    folder_path = settings['folder_path'] + '/' + time.strftime('%Y%m%d')
    delay_on = settings['random_delay']
    start_time = time.strftime('%H-%M-%S')

    if tag_on:
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
    
    Function.create_folder(folder_path)
    i = 1
    end = False

    while True:
        if page <= stop_page or not stop_page:
            Log.add('正在读取第' + str(page) + '页……')
            data = Yandere.get_json(page, tag_on, tags)
            for post in Yandere.get_li(data):
                if i == 1:
                    settings['last_stop_id'] = post['id']
                    Function.write(settings['folder_path'], 'config.json', Yandere.return_json(settings), True)
                if post['id'] <= last_stop_id and not stop_page:
                    end = True
                    break
                post['id'] = str(post['id'])
                if judge(post, settings, discard_tags):
                    download(post, folder_path)
                    if delay_on:
                        time.sleep(random.uniform(0.5, 10.0))
                Log.output()
                write_log(folder_path, start_time)
                i += 1
            if end:
                break
            page += 1
        else:
            break