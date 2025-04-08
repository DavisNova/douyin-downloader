import os
import yaml
import subprocess
import threading
import time
import queue
from queue import Empty
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'douyin-downloader-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 获取配置文件的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.yml")

# 全局进程变量
download_process = None
stop_event = threading.Event()
output_queue = queue.Queue()

def load_config():
    """从配置文件加载配置"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件时出错: {str(e)}")
        return {}

def save_config(config):
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"保存配置文件时出错: {str(e)}")
        return False

def read_process_output(process, queue, stop_event):
    """读取进程输出并放入队列"""
    try:
        # 确保使用UTF-8编码来读取输出
        for line in iter(process.stdout.readline, ''):
            if stop_event.is_set():
                break
            if line:
                # 确保所有输出都是utf-8编码
                if isinstance(line, bytes):
                    line = line.decode('utf-8', errors='ignore')
                queue.put(line.strip())
    except UnicodeDecodeError as e:
        print(f"读取进程输出时出现编码错误: {str(e)}")
        # 发送编码错误信息到前端
        queue.put(f"[ERROR] 读取输出时出现编码错误，可能包含不支持的字符: {str(e)}")
    except Exception as e:
        print(f"读取进程输出时出错: {str(e)}")
    finally:
        process.stdout.close()

def process_queue_output(queue, stop_event):
    """处理队列中的输出并通过WebSocket发送"""
    while not stop_event.is_set():
        try:
            # 使用非阻塞方式获取输出
            line = queue.get(block=True, timeout=0.1)
            
            # 确保line是字符串
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')
                
            # 处理进度条信息
            if "%" in line:
                # 尝试提取进度信息
                progress_match = re.search(r'(\d+)%', line)
                if progress_match:
                    progress = int(progress_match.group(1))
                    socketio.emit('progress_update', {'progress': progress, 'text': line})
                else:
                    socketio.emit('output', {'text': line})
            else:
                # 检查是否是下载完成的消息
                if "下载完成" in line or "[下载完成]" in line:
                    socketio.emit('download_complete', {'text': line})
                socketio.emit('output', {'text': line})
        except Empty:
            pass
        except Exception as e:
            print(f"处理输出时出错: {str(e)}")
            socketio.emit('error', {'text': str(e)})

def run_command():
    """运行抖音下载命令"""
    global download_process, stop_event, output_queue
    
    try:
        # 重置停止事件
        stop_event = threading.Event()
        
        # 使用绝对路径
        script_path = os.path.join(BASE_DIR, "DouYinCommand.py")
        
        # 设置环境变量，确保使用UTF-8编码
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        # 启动下载进程，捕获标准输出和错误
        download_process = subprocess.Popen(
            ["python", "-u", script_path], 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False,  # 不使用universal_newlines，我们手动处理编码
            cwd=BASE_DIR,  # 设置工作目录
            bufsize=1,  # 行缓冲
            env=env,    # 使用自定义环境变量
            text=False  # 不使用文本模式，返回原始字节
        )
        
        # 启动读取输出的线程
        output_thread = threading.Thread(
            target=read_process_output, 
            args=(download_process, output_queue, stop_event)
        )
        output_thread.daemon = True
        output_thread.start()
        
        # 启动处理输出的线程
        process_thread = threading.Thread(
            target=process_queue_output,
            args=(output_queue, stop_event)
        )
        process_thread.daemon = True
        process_thread.start()
        
        return {"status": "success", "message": "下载任务已启动"}
    except Exception as e:
        return {"status": "error", "message": f"启动下载任务时出错: {str(e)}"}

@app.route('/')
def index():
    """主页"""
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/save', methods=['POST'])
def save():
    """保存配置"""
    try:
        data = request.form
        
        # 加载当前配置
        config = load_config()
        
        # 更新链接
        if "links" in data and data["links"]:
            config["link"] = [link.strip() for link in data["links"].split('\n') if link.strip()]
        
        # 更新下载路径
        if "path" in data:
            config["path"] = data["path"]
        
        # 更新布尔值选项
        boolean_fields = ["music", "cover", "avatar", "json", "folderstyle", "database"]
        for field in boolean_fields:
            config[field] = field in data  # 如果字段存在于表单数据中，设为True，否则为False
        
        # 更新模式
        if "modes" in data:
            modes = request.form.getlist("modes")
            config["mode"] = modes if modes else ["post"]
        
        # 更新时间范围
        if "start_time" in data:
            config["start_time"] = data["start_time"]
        if "end_time" in data:
            config["end_time"] = data["end_time"]
        
        # 更新线程数
        if "thread" in data and data["thread"].isdigit():
            config["thread"] = int(data["thread"])
        
        # 更新数量限制
        number_fields = ["post", "like", "allmix", "mix", "music"]
        if "number" not in config:
            config["number"] = {}
        for field in number_fields:
            key = f"number_{field}"
            if key in data and data[key].isdigit():
                config["number"][field] = int(data[key])
        
        # 更新增量下载选项
        increase_fields = ["post", "like", "allmix", "mix", "music"]
        if "increase" not in config:
            config["increase"] = {}
        for field in increase_fields:
            key = f"increase_{field}"
            config["increase"][field] = key in data
        
        # 保存配置
        success = save_config(config)
        if success:
            return jsonify({"status": "success", "message": "配置已保存"})
        else:
            return jsonify({"status": "error", "message": "保存配置失败"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"保存配置时出错: {str(e)}"})

@app.route('/run', methods=['POST'])
def run():
    """运行下载任务"""
    result = run_command()
    return jsonify(result)

@app.route('/stop', methods=['POST'])
def stop():
    """停止下载任务"""
    global download_process, stop_event
    
    try:
        if download_process and download_process.poll() is None:
            stop_event.set()
            download_process.terminate()
            return jsonify({"status": "success", "message": "下载任务已停止"})
        else:
            return jsonify({"status": "warning", "message": "没有正在运行的下载任务"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"停止下载任务时出错: {str(e)}"})

@socketio.on('connect')
def handle_connect():
    print('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 