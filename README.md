# 抖音下载器 (DouYin Downloader)

一个功能强大的抖音内容批量下载工具，支持视频、图集、音乐等多种内容的无水印下载，并提供命令行和Web界面两种使用方式。

## ✨ 主要特性

- **多种内容类型支持**
  - 视频和图集作品批量下载（无水印）
  - 主页发布/喜欢作品批量获取
  - 合集作品批量下载
  - 音乐作品批量下载
  - 直播信息获取

- **强大的批量处理能力**
  - 多线程并发下载提高效率
  - 支持多链接批量处理
  - 断点续传功能
  - 自动跳过已下载内容

- **灵活的配置选项**
  - 支持命令行参数和YAML配置文件
  - 自定义下载路径、线程数等
  - 可选择性下载音乐、封面、头像等附加内容
  - 支持时间范围筛选

- **增量更新和数据持久化**
  - 支持增量更新模式避免重复下载
  - SQLite数据库持久化存储下载记录
  - 支持用户收藏功能

- **用户友好的界面**
  - 命令行彩色输出提升使用体验
  - Web图形界面方便操作
  - 详细的下载进度和统计信息
  - 实时日志反馈

## 🚀 快速开始

### 安装

1. 克隆仓库或下载源代码:
```bash
git clone https://github.com/yourusername/douyin-downloader.git
cd douyin-downloader
```

2. 安装所需依赖:
```bash
pip install -r requirements.txt
```

3. 准备配置文件:
```bash
cp config.example.yml config.yml
```

### 使用方法

#### 方式一：Web界面（推荐）

1. 启动Web服务:
```bash
python web_ui.py
```

2. 在浏览器中访问 `http://localhost:5000` 使用Web界面进行下载

3. Web界面功能:
   - 输入抖音链接（支持多行批量输入）
   - 设置下载选项和过滤条件
   - 实时查看下载进度和日志
   - 管理用户收藏列表

#### 方式二：命令行方式

使用配置文件:
```bash
python DouYinCommand.py
```

使用命令行参数:
```bash
python DouYinCommand.py -C True -l "抖音分享链接" -p "下载路径"
```

## 🔍 项目架构

### 目录结构

```
douyin-downloader/
├── apiproxy/               # API代理模块
│   ├── common/             # 通用工具
│   └── douyin/             # 抖音API相关
│       ├── database.py     # 数据库操作
│       ├── douyin.py       # 抖音核心API
│       ├── download.py     # 下载功能实现
│       ├── result.py       # 结果格式化
│       └── urls.py         # API URL集合
├── web/                    # Web界面模块
│   ├── app.py              # Flask应用
│   ├── static/             # 静态资源
│   └── templates/          # HTML模板
├── utils/                  # 通用工具模块
│   └── logger.py           # 日志管理
├── logs/                   # 日志目录
├── downloaded/             # 默认下载目录
├── DouYinCommand.py        # 命令行入口
├── web_ui.py               # Web界面入口
├── config.yml              # 配置文件
├── test_download.py        # 测试脚本
└── requirements.txt        # 依赖列表
```

### 核心模块

1. **抖音API模块 (apiproxy/douyin/)**
   - `douyin.py`: 实现抖音API请求、数据解析和处理
   - `database.py`: 管理SQLite数据库，存储下载记录和用户收藏
   - `download.py`: 实现内容下载、多线程控制和进度显示
   - `result.py`: 负责API结果格式化和转换
   - `urls.py`: 管理所有API端点URL

2. **命令行应用 (DouYinCommand.py)**
   - 解析命令行参数和配置文件
   - 处理不同类型的下载请求（视频、图集、合集等）
   - 多链接批量处理
   - 错误捕获和恢复机制

3. **Web界面 (web/)**
   - Flask应用提供Web服务
   - Socket.IO实时通信更新下载状态
   - 响应式UI设计，支持移动端
   - 用户收藏管理功能

## 💡 实现细节

### 1. 链接解析与内容提取

- 支持多种抖音链接格式（分享链接、主页链接、直链等）
- 通过正则表达式提取关键标识（sec_uid, aweme_id等）
- 使用抖音非官方API获取无水印内容
- 自动处理重定向链接和短链接

### 2. 下载核心功能

- 多线程下载加速处理
- 断点续传支持大文件下载
- 文件命名规范化，避免非法字符
- 自动创建分类目录
- 自动处理Unicode和特殊字符

### 3. 数据持久化

- SQLite数据库存储下载历史
- 表结构设计:
  - `t_user_post`: 用户发布作品记录
  - `t_user_like`: 用户喜欢作品记录
  - `t_mix`: 合集作品记录
  - `t_music`: 音乐作品记录
  - `t_user_collection`: 用户收藏记录（保存自定义命名的用户链接）

### 4. 增量更新机制

- 通过数据库记录判断内容是否已下载
- 支持按时间范围过滤，避免重复下载
- 可配置增量更新策略
- 识别置顶作品，避免因置顶内容导致的更新中断

### 5. 时间筛选功能

- 支持精确日期范围筛选，使用YYYY-MM-DD格式（如"2025-03-19"）
- 支持使用"now"关键字表示当前时间（自动转换为执行时的日期）
- 在获取列表时预先过滤，提高下载效率
- 自动显示每个作品的发布时间，并跳过范围外的作品
- 时间筛选示例:
  ```yaml
  # 只下载2025年1月到3月的内容
  start_time: "2025-01-01"
  end_time: "2025-03-31"
  
  # 下载最近一周内发布的内容
  start_time: "2025-03-14"
  end_time: "now"
  ```

### 6. Web界面特性

- Bootstrap响应式设计
- 异步AJAX请求保持界面流畅
- Socket.IO实时推送下载进度和日志
- 用户收藏功能方便管理常用链接
- 下载任务可随时中断和恢复

### 7. 用户收藏功能

用户收藏功能允许保存和管理常用的抖音用户主页链接，使用方法如下：

1. **添加用户到收藏**：
   - 点击下载链接输入框旁边的"用户收藏"按钮
   - 在弹出的模态框中，输入用户主页链接（格式如 `https://www.douyin.com/user/MS4wLjABXXXX`）
   - 输入自定义名称（可选，不填则使用默认名称）
   - 点击"添加用户"按钮保存

2. **使用收藏的用户链接**：
   - 点击"用户收藏"按钮查看已保存的用户列表
   - 在列表中找到需要的用户，点击"选择"按钮
   - 用户链接会自动填充到下载输入框中
   - 无需再手动复制粘贴链接

3. **管理收藏列表**：
   - 可以删除不再需要的用户记录
   - 可以通过"刷新"按钮更新用户列表
   - 所有收藏信息保存在数据库中，重启程序后仍然可用

## 📋 支持的链接类型

- 作品分享链接: `https://v.douyin.com/xxx/`
- 个人主页: `https://www.douyin.com/user/xxx`
- 单个视频: `https://www.douyin.com/video/xxx`
- 图集: `https://www.douyin.com/note/xxx`
- 合集: `https://www.douyin.com/collection/xxx`
- 音乐原声: `https://www.douyin.com/music/xxx`
- 直播: `https://live.douyin.com/xxx`

## 🛠️ 高级用法

### 配置文件参数

配置文件(`config.yml`)支持以下主要参数:

```yaml
# 下载链接，支持多个链接
link:
  - "https://v.douyin.com/xxxxx/"
  - "https://v.douyin.com/yyyyy/"

# 下载保存路径，默认当前目录
path: "./downloaded"

# 下载选项
music: true      # 是否下载音乐
cover: true      # 是否下载封面
avatar: true     # 是否下载头像
json: true       # 是否保存JSON数据
folderstyle: true  # 是否使用文件夹风格保存

# 下载模式设置
mode: 
  - "post"      # post:发布作品 like:点赞作品 mix:合集作品

# 下载数量设置（0表示全部下载）
number:
  post: 0       # 发布作品下载数量
  like: 0       # 点赞作品下载数量
  allmix: 0     # 所有合集下载数量
  mix: 0        # 单个合集下载数量
  music: 0      # 音乐下载数量

# 其他设置
thread: 5       # 下载线程数
database: true  # 是否使用数据库

# 增量更新配置
increase:
  post: false   # 是否增量下载主页作品
  like: false   # 是否增量下载喜欢作品

# 时间范围过滤（可选）
start_time: "2023-01-01"  # 开始时间，格式：YYYY-MM-DD
end_time: "now"           # 结束时间，使用"now"表示当前时间

# Cookie设置（从浏览器获取）
cookies:
  msToken: "xxxxxx"
  ttwid: "xxxxxx"
  odin_tt: "xxxxxx"
```

### 命令行参数

```
基础参数:
  -C, --cmd            使用命令行模式
  -l, --link           下载链接
  -p, --path           保存路径
  -t, --thread         线程数（默认5）

下载选项:
  -m, --music          下载音乐（默认True）
  -c, --cover          下载封面（默认True）
  -a, --avatar         下载头像（默认True）
  -j, --json           保存JSON数据（默认True）
  -fs, --folderstyle   文件夹保存风格（默认True）

模式选择:
  -M, --mode           下载模式(post/like/mix)

增量更新:
  --postincrease       主页作品增量下载
  --likeincrease       喜欢作品增量下载
  
时间范围:
  --start_time         开始时间 (YYYY-MM-DD)
  --end_time           结束时间 (YYYY-MM-DD)
```

## 📝 注意事项

1. **使用须知**
   - 本工具仅供学习交流使用，请勿用于非法用途
   - 下载内容受抖音API限制，可能随时变化
   - 建议适当控制请求频率，避免IP被限制

2. **常见问题解决**
   - **'DataBase' object has no attribute 'insert_user_post' 错误**：
     这可能是由于模块导入冲突导致的，修改apiproxy目录下的代码，使用`import ... as ...`方式明确命名导入的模块。
   
   - **下载失败或无法获取内容**：
     检查配置文件中的Cookie信息是否有效，通常需要从浏览器开发者工具中获取最新的Cookie。
   
   - **时间筛选无效**：
     确保日期格式正确（YYYY-MM-DD），并检查是否存在时区差异。作品时间是按照服务器返回的创建时间进行判断的。
   
   - **内存占用过高**：
     下载大量内容时，建议限制下载数量或减少线程数。如果仍有问题，可以拆分为多次下载。
   
   - **Socket.IO连接问题**：
     Web界面使用Socket.IO进行实时通信，如果遇到连接问题，可能是网络或防火墙限制，尝试使用命令行方式运行。

3. **环境要求**
   - Python 3.7+
   - 请确保安装所有requirements.txt中的依赖
   - Web界面需要浏览器支持
   - 增量更新功能需要启用数据库支持

## 🤝 贡献指南

欢迎通过以下方式贡献:

1. 提交Bug报告和功能请求
2. 提交Pull Request改进代码
3. 完善文档和使用示例

## 📜 许可证

本项目采用 [MIT](LICENSE) 许可证。

## 🙏 致谢

- 感谢所有开源社区的贡献者
- 特别感谢[Rich](https://github.com/Textualize/rich)提供优秀的终端美化支持
- 感谢[Flask](https://flask.palletsprojects.com/)和[Bootstrap](https://getbootstrap.com/)提供Web开发框架

---

**免责声明**: 本工具仅供学习交流使用，使用者需遵守相关法律法规，尊重内容创作者的权益。

## 📊 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=jiji262/douyin-downloader&type=Date)](https://star-history.com/#jiji262/douyin-downloader&Date)

# License

[MIT](https://opensource.org/licenses/MIT) 

