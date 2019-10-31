import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import tkinter.scrolledtext as scrolledtext
import time
import random
import Http
import Yandere
import Function
import Log
import index

class window:

    def __init__(self, container):
        self.container = container
        self.childFrame()
    def childFrame(self):
        left_descrb = ('开始页码', '结束页码', '终止ID', '最大文件体积', 'tag搜索终止ID')
        middle_descrb = ('最小宽度', '最小高度', '最小宽高比', '最大宽度', '最大高度', '最大宽高比')
        switch_descrb = ('下载体积限制', 'tag搜索', '下载延迟', '跳过pending', '安全模式', '从文件读取配置')
        text_descrb = ('下载路径', '要搜索的tags', '要排除的tags')
        left_options = [] # len = 5
        middle_options = [] # len = 6
        switch_options = [] # len = 6
        text_options = [] # len = 3
        left_var = [0] * 5
        middle_var = [0] * 6
        switch_var = [1] * 6
        text_input = [''] * 3

        def start():
            for i in range(6):
                if i < 3:
                    text_input[i] = text_options[i].get()
                if i < 5:
                    left_var[i] = left_options[i].get()
                middle_var[i] = middle_options[i].get()
                switch_var[i] = switch_options[i].get()
            if not switch_var[5]:
                settings['start_page'] = left_var[0]
                settings['stop_page'] = left_var[1]
                settings['file_size'] = left_var[3] * 1048576

                settings['pic_size']['min']['width'] = middle_var[0]
                settings['pic_size']['min']['height'] = middle_var[1]
                settings['pic_size']['min']['proportion'] = middle_var[2]
                settings['pic_size']['max']['width'] = middle_var[3]
                settings['pic_size']['max']['height'] = middle_var[4]
                settings['pic_size']['max']['proportion'] = middle_var[5]

                if not left_var[2]:
                    settings['last_stop_id'] = left_var[2]
                if not left_var[4]:
                    settings['tagSearch_last_stop_id'] = left_var[4]
                pic_type= middle_option.get()
                if pic_type == '全部':
                    settings['pic_type'] = 0
                elif pic_type == '横图':
                    settings['pic_type'] = 1
                elif pic_type == '竖图':
                    settings['pic_type'] = 2
                elif pic_type == '方形':
                    settings['pic_type'] = 3
                

                settings['file_size_limit'] = switch_var[0]
                settings['tag_search'] = switch_var[1]
                settings['random_delay'] = switch_var[2]
                settings['status_active_only'] = switch_var[3]
                settings['safe_mode'] = switch_var[4]

                settings['folder_path'] = text_input[0]
            tags = text_input[1].replace(' ', '+')
            discard_tags = text_input[2].strip(' ').split(' ')
            page = settings['start_page']
            stop_page = settings['stop_page']
            last_stop_id = settings['last_stop_id']
            tag_on = settings['tag_search']
            folder_path = settings['folder_path'] + '/' + time.strftime('%Y%m%d')
            delay_on = settings['random_delay']
            start_time = time.strftime('%H-%M-%S')
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
                        if index.judge(post, settings, discard_tags):
                            index.download(post, folder_path)
                            if delay_on:
                                time.sleep(random.uniform(0.5, 10.0))
                        Log.g_output(output)
                        index.write_log(folder_path, start_time)
                        i += 1
                    if end:
                        break
                    page += 1
                else:
                    break

        # 选项区
        # 左上
        left = tk.LabelFrame(self.container, text = '基本设置')
        left.grid(row = 0, column = 0)
        for i in range(5):
            left_options.append(tk.IntVar())
            tk.Label(left, text = left_descrb[i]).grid(row = i, column = 0, sticky = 'e')
            tk.Entry(left,width = 6, textvariable = left_options[i]).grid(row = i, column = 1)
        
        # 左下
        desc = tk.LabelFrame(self.container, text = '运行')
        desc.grid(row = 1, column = 0)
        tk.Button(desc, text = '开始！', width = 10, height = 1, command = start).grid(row = 0, column = 0)
        # tk.Button(desc, text = '退出', width = 10, height = 1, command = self.container.quit()).grid(row = 0, column = 1)

        # 中间
        middle = tk.LabelFrame(self.container, text = '尺寸设置')
        middle.grid(row = 0, column = 1, rowspan = 2)
        for i in range(6):
            middle_options.append(tk.IntVar())
            tk.Label(middle, text = middle_descrb[i]).grid(row = i, column = 0, sticky = 'e')
            tk.Entry(middle, width = 6, textvariable = middle_options[i]).grid(row = i, column = 1)
        tk.Label(middle, text = '图片方向').grid(row = 6, column = 0, sticky = 'e')
        middle_option = tk.StringVar()
        pic_type_ui = ttk.Combobox(middle, values = ('全部', '横图', '竖图', '方形'), textvariable = middle_option, width = 4)
        pic_type_ui.grid(row = 6, column = 1)
        
        # 右侧
        right = tk.LabelFrame(self.container, text = '开关项')
        right.grid(row = 0, column = 2, rowspan = 2)
        for i in range(6):
            tk.Label(right, text = switch_descrb[i]).grid(row =i, column = 0, sticky = 'e')
            switch_options.append(tk.IntVar())
            tk.Radiobutton(right, text = '开', variable = switch_options[i], value = 1).grid(row = i, column = 1)
            tk.Radiobutton(right, text = '关', variable = switch_options[i], value = 0).grid(row = i, column = 2)
        
        # 下部
        bottom = tk.LabelFrame(self.container, text = '')
        bottom.grid(row = 2, column = 0, columnspan = 3)
        for i in range(3):
            text_options.append(tk.StringVar())
            tk.Label(bottom, text = text_descrb[i]).grid(row = i, column = 0, sticky = 'e')
            tk.Entry(bottom, width = 50, textvariable = text_options[i]).grid(row = i, column = 1,)
            #text_options[i] = tk.Entry(bottom, width = 50)
            #text_options[i].grid(row = i, column = 1)
            #text_options[i].bind('<return>')

        # 输出区
        output = scrolledtext.ScrolledText(self.container, width = 60, height = 12)
        output.grid(row = 3, columnspan = 3)
        output.insert('end', 'tag搜索终止ID仅当tag搜索选项启用时生效\n部分功能暂缺，可能会有错误\n点\"开始\"后窗口会无响应但是爬取功能确实在运行，后续考虑解决')
        output.see('end')
        output.update()

        
        # def get_content():


root = tk.Tk()
root.title('Yande.re爬虫')
root.geometry('440x425')
window(root)
settings = Yandere.get_li(Function.read('config.json'))
root.mainloop()