import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import tkinter.scrolledtext as scrolledtext

class window:

    def __init__(self, container):
        self.container = container
        self.childFrame()
    def childFrame(self):
        left_descrb = ('开始页码', '结束页码', '终止ID', '下载体积限制', 'tag搜索终止ID')
        middle_descrb = ('最小宽度', '最小高度', '最小宽高比', '最大宽度', '最大高度', '最大宽高比')
        switch_descrb = ('下载体积限制', 'tag搜索', '下载延迟', '跳过pending', '安全模式', '从文件读取配置')
        text_descrb = ('下载路径', '要搜索的tags', '要排除的tags')
        left_var = ('start_page', 'stop_page', 'last_stop_id', 'file_size', 'tagSearch_last_stop_id')
        switch_var = ('file_size_limit', 'tag_on', 'random_delay', 'status_active_only', 'safe_mode', 'fuzzy_judgment')
        left_options = [] # len = 5
        middle_options = [] # len = 6
        switch_options = [] # len = 6
        text_options = [] # len = 3

        def start():
            output.insert('end', left_options[0].get())

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
        pic_type_ui = ttk.Combobox(middle, values = ('全部', '横图', '竖图', '方形'), textvariable = middle_options, width = 4)
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
        output.insert('end', 'tag搜索终止ID仅当tag搜索选项启用时生效\n')
        output.see('end')
        output.update()

        
        # def get_content():


root = tk.Tk()
root.title('Yande.re爬虫')
root.geometry('600x600')
window(root)
root.mainloop()