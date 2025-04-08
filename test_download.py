#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
from apiproxy.douyin.douyin import Douyin
from apiproxy.douyin.download import Download
from apiproxy.douyin import douyin_headers

# 设置参数
config = {
    "path": os.path.join(os.getcwd(), "downloaded"),
    "music": True,
    "cover": True,
    "avatar": True,
    "json": True,
    "start_time": "2025-03-19",
    "end_time": "2025-03-21",
    "folderstyle": True,
    "mode": ["post"],
    "database": True,
    "thread": 5
}

# 确保目录存在
os.makedirs(config["path"], exist_ok=True)

# 用户 sec_uid 
test_user = "MS4wLjABAAAA7-_U51NU20l-szhmcWPYHRGXbu8HGP4hz5ohlmV-UgtzT9QqfXEVTIjFESBARYG-"

# 初始化下载器
dy = Douyin(database=config["database"])
dl = Download(
    thread=config["thread"],
    music=config["music"],
    cover=config["cover"],
    avatar=config["avatar"],
    resjson=config["json"],
    folderstyle=config["folderstyle"]
)

# 下载测试
print("开始测试下载功能")
start_time = time.time()

try:
    # 获取用户信息
    print("正在获取用户信息...")
    data = dy.getUserDetailInfo(sec_uid=test_user)
    nickname = "未知用户"
    if data and data.get('user'):
        nickname = data['user']['nickname']
    print(f"用户名: {nickname}")
    
    # 创建保存目录
    user_path = os.path.join(config["path"], f"test_user_{nickname}_{test_user}")
    os.makedirs(user_path, exist_ok=True)
    
    # 获取用户作品
    print("正在获取用户作品...")
    datalist = dy.getUserInfo(
        test_user, 
        "post", 
        35, 
        0, 
        False,
        start_time=config.get("start_time", ""),
        end_time=config.get("end_time", "")
    )
    
    if datalist:
        print(f"获取到 {len(datalist)} 个作品")
        # 下载作品
        mode_path = os.path.join(user_path, "post")
        os.makedirs(mode_path, exist_ok=True)
        dl.userDownload(awemeList=datalist, savePath=mode_path)
        print("下载完成")
    else:
        print("未获取到作品或时间范围内没有作品")
    
except Exception as e:
    print(f"发生错误: {str(e)}")

end_time = time.time()
print(f"测试完成，耗时: {int(end_time - start_time)}秒") 