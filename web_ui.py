#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
抖音下载器 Web 配置界面启动脚本
"""

import os
import sys

# 确保工作目录正确
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# 添加当前目录到Python路径
sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    print("正在启动抖音下载器配置界面...")
    print("服务启动后，请访问 http://localhost:5000 来使用抖音下载器")
    
    try:
        from web.app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"错误: 未安装所需依赖，请运行 'pip install flask pyyaml': {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1) 