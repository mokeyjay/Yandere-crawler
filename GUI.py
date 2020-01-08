#!/usr/bin/env python3

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as scrolledtext
import threading
import sys
import Yandere
import Function
import index


class window:
    def __init__(self, container):
        self.container = container
        self.childFrame()
    def childFrame(self):
        left_descrb = ('开始页码', '结束页码', '终止ID', '最大文件体积', 'tag搜索终止ID')
        middle_descrb = ('最小宽度', '最小高度', '最小宽高比', '最大宽度', '最大高度', '最大宽高比')
        switch_descrb = ('下载体积限制', 'tag搜索', '跳过pending', 'NSFW过滤', '新建文件夹', '读取配置文件')
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
            # 锁定开始按钮
            start_button.config(state = 'disabled')
            #start_button.destroy()

            # 获取输入
            for i in range(6):
                if i < 3:
                    text_input[i] = text_options[i].get()
                if i < 5:
                    left_var[i] = left_options[i].get()
                middle_var[i] = middle_options[i].get()
                switch_var[i] = switch_options[i].get()
            
            # 获取设置
            settings = Yandere.get_li(Function.read('config.json'))
            if not switch_var[5]:
                # 选择不从文件读取设置
                settings['start_page'] = left_var[0]
                settings['stop_page'] = left_var[1]
                settings['file_size'] = left_var[3] * 1048576

                settings['pic_size']['min']['width'] = middle_var[0]
                settings['pic_size']['min']['height'] = middle_var[1]
                settings['pic_size']['min']['proportion'] = middle_var[2]
                settings['pic_size']['max']['width'] = middle_var[3]
                settings['pic_size']['max']['height'] = middle_var[4]
                settings['pic_size']['max']['proportion'] = middle_var[5]

                # 若终止id输入项非空，则以输入id覆盖终止id
                if left_var[2]:
                    settings['last_stop_id'] = left_var[2]
                if left_var[4]:
                    settings['tagSearch_last_stop_id'] = left_var[4]
                # 获取下载图片方向
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
                settings['status_check'] = switch_var[2]
                settings['safe_mode'] = switch_var[3]
                settings['date_separate'] = switch_var[4]

                settings['folder_path'] = text_input[0]
            tags = text_input[1]
            discard_tags = text_input[2]

            # 使用子线程解决线程锁死导致的窗口无响应
            thread(settings, tags, discard_tags, output, start_button)

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
        start_button = tk.Button(desc, text = '开始', width = 8, height = 1, command = start)
        start_button.grid(row = 0, column = 0)
        tk.Button(desc, text = '退出', width = 8, height = 1, command = self.container.quit).grid(row = 0, column = 1)

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
            switch_options.append(tk.BooleanVar())
            tk.Checkbutton(right, text=switch_descrb[i], variable=switch_options[i], onvalue=True, offvalue=False).grid(row=i, column=1, sticky='w')
        
        # 下部
        bottom = tk.LabelFrame(self.container, text = '')
        bottom.grid(row = 2, column = 0, columnspan = 3)
        for i in range(3):
            text_options.append(tk.StringVar())
            tk.Label(bottom, text = text_descrb[i]).grid(row = i, column = 0, sticky = 'e')
            tk.Entry(bottom, width = 38, textvariable = text_options[i]).grid(row = i, column = 1)
            #另一种获取输入的方法
            #text_options[i] = tk.Entry(bottom, width = 50)
            #text_options[i].grid(row = i, column = 1)
            #text_options[i].bind('<return>')

        # 输出区
        output = scrolledtext.ScrolledText(self.container, width = 48, height = 12)
        output.grid(row = 3, columnspan = 3)
        output.insert('end', '请以空格分隔要搜索的tags与要排除的tags关键词\n停止页码为0时爬至上次终止图片，非0时爬完此页停止\n若与上次搜索关键词不同建议将tag搜索终止ID设为1\n图片尺寸限制条件为0时则不限制\n文件体积限制单位MB\n"pending"多由低质量触发，建议开启过滤\n"新建文件夹"选项将以当前日期为名建立子文件夹\n不建议在看到"爬取结束"前退出程序\n')
        output.see('end')
        output.update()

# 子线程
class thread(threading.Thread):
    def __init__(self, settings, tags, discard_tags, frame, start_button):
        threading.Thread.__init__(self)
        self.daemon = True
        self.settings = settings
        self.tags = tags
        self.discard_tags = discard_tags
        self.frame = frame
        self.reset_button = start_button
        self.start()
    def run(self):
        self.frame.insert('end', '\n开始爬取\n')
        sys.stdout = redirect(self.frame)
        index.main(self.settings, self.tags, self.discard_tags)
        self.frame.insert('end', '\n爬取结束\n')
        self.frame.see('end')
        sys.stdout = sys.__stdout__
        self.reset_button.config(state = 'normal')
        
# 截获输出
class redirect:
    def __init__(self, frame):
        self.frame = frame
    def write(self, out):
        self.frame.insert('end', out)
        self.frame.see('end')
    def flush(self):
        pass


root = tk.Tk()
root.title('Yande.re爬虫')
root.geometry('360x420+%d+%d' %((root.winfo_screenwidth()-440)/2, (root.winfo_screenheight() - 420)/4))
root.resizable(width=False, height=False)
window(root)
root.mainloop()
