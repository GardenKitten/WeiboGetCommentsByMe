import requests
import re
import yaml
from datetime import datetime
import os
import tkinter as tk
from tkinter import messagebox

def process_string(input_string):
    # 删除所有带有class="icon-link"的<img>标签
    input_string = re.sub(r'<img\s+class="icon-link"\s+[^>]*>', '', input_string)

    # 将没有class="icon-link"的<img>标签转换格式
    input_string = re.sub(r'<img\s.*?src="(.*?)".*?/>', r'<img src=\1 height=16>', input_string)

    # 对包含用户名的<a>标签进行替换
    input_string = re.sub(r'回复<a href=/n/([^"]+)"?\susercard="name=@([^"]+)">@([^<]+)</a>:', '', input_string)
    input_string = re.sub(r'回复 <a href=/n/([^"]+)"?\susercard="name=@([^"]+)">@([^<]+)</a>:', '', input_string)

    # 删除所有的<a>标签
    input_string = re.sub(r'<a\s.*?</a>', '', input_string)

    return input_string


try:
    # 读取配置文件
    with open('config.yaml', 'r', encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)

    headers = config['headers']
    cookies = config['cookies']
    path = config['path']

    messagebox.showinfo("Success", "读取配置文件成功！")
except FileNotFoundError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "Configuration file 'config.yaml' not found.")
    exit(1)
except yaml.YAMLError as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", f"Error reading configuration file: {e}")
    exit(1)

# 如果路径不存在，则创建目录
os.makedirs(os.path.dirname(path), exist_ok=True)

try:
    # 发送请求并遍历订单页
    page = 0  # 起始页
    while True:
        url = f'https://www.weibo.com/ajax/message/myCmt?page={page}'
        response = requests.get(url, headers=headers, cookies=cookies)
        response.encoding = 'utf-8'
        parsed_data = response.json()

        cmts = parsed_data["data"]["comments"]

        # 如果没有订单数据，则跳出循环
        if not cmts:
            break

        num = 0

        for cmt in cmts:

            # 原微博
            original_user = cmt["page_info"]["content1"]
            original_post = cmt["page_info"]["content2"]
            original_post = process_string(original_post)
            userID = cmt["page_info"]["uidPageInfo"]

            # 回复时间
            created_time = cmt["created_at"]
            # 将字符串解析为datetime对象
            date_object = datetime.strptime(created_time, '%a %b %d %H:%M:%S %z %Y')
            # 将datetime对象转换为所需格式的字符串，包含星期几
            formatted_date = date_object.strftime('%Y-%m-%d %H:%M:%S %a')

            # 你的评论
            text = cmt["text"]
            text = process_string(text)

            # 对方的评论（如果存在）
            reply_comment = cmt.get("reply_comment")

            # 如果是楼中楼
            if reply_comment is not None:
                reply_userID = reply_comment["user"]["id"]
                reply_userName = reply_comment["user"]["name"]
                reply_text = reply_comment["text"]
                reply_text = process_string(reply_text)

                # 写入Markdown文件
                with open(path, 'a', encoding='utf-8') as md_file:
                    md_file.write(f"**原微博：** \n\n")
                    md_file.write(f"[{original_user}](https://www.weibo.com/u/{userID})：\n{original_post}\n\n")
                    md_file.write(f"> **被回复的评论：** \n> \n")
                    md_file.write(f"> [@{reply_userName}](https://www.weibo.com/u/{reply_userID}):\n{reply_text}\n\n")
                    md_file.write(f"> **你的评论：** {text}\n> \n")
                    md_file.write(f"> **评论时间：** {formatted_date}\n\n")
                    md_file.write("\n---\n\n")  # 添加分隔线

            # 如果不是楼中楼
            else:
                # 写入Markdown文件
                with open(path, 'a', encoding='utf-8') as md_file:
                    md_file.write(f"**原微博：** \n\n")
                    md_file.write(f"[{original_user}](https://www.weibo.com/u/{userID})：\n{original_post}\n\n")
                    md_file.write(f"> **评论：** {text}\n> \n")
                    md_file.write(f"> **评论时间：** {formatted_date}\n\n")
                    md_file.write("\n---\n\n")  # 添加分隔线

        # 前进到下一页
        page += 1
        print(f"page:{page}")

    print("写入完成")
    messagebox.showinfo("Success", "md 文件生成成功！")

except requests.RequestException as e:
    root = tk.Tk()
    root.withdraw()
    print("Error", f"Error making HTTP request: {e}")
    messagebox.showerror("Error", f"Error making HTTP request: {e}")

