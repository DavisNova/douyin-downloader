#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import List, Optional
from pathlib import Path
# import asyncio  # 暂时注释掉
# import aiohttp  # 暂时注释掉
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from apiproxy.douyin import douyin_headers
from apiproxy.common import utils

logger = logging.getLogger("douyin_downloader")
console = Console()

class Download(object):
    def __init__(self, thread=5, music=True, cover=True, avatar=True, resjson=True, folderstyle=True):
        self.thread = thread
        self.music = music
        self.cover = cover
        self.avatar = avatar
        self.resjson = resjson
        self.folderstyle = folderstyle
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            transient=True  # 添加这个参数，进度条完成后自动消失
        )
        self.retry_times = 3
        self.chunk_size = 8192
        self.timeout = 30

    def _download_media(self, url: str, path: Path, desc: str) -> bool:
        """通用下载方法，处理所有类型的媒体下载"""
        try:
            # 规范化路径，确保路径有效
            path = Path(str(path).rstrip())
            
            # 确保父目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if path.exists():
                self.console.print(f"[cyan]⏭️  跳过已存在: {desc}[/]")
                return True
                
            # 使用新的断点续传下载方法替换原有的下载逻辑
            return self.download_with_resume(url, path, desc)
        except OSError as e:
            # 处理路径相关错误
            logger.error(f"文件路径错误: {path}, 错误: {str(e)}")
            
            # 尝试使用替代路径
            try:
                alt_path = path.parent / f"media_{int(time.time())}{path.suffix}"
                logger.info(f"尝试使用替代路径: {alt_path}")
                return self.download_with_resume(url, alt_path, desc)
            except Exception as e2:
                logger.error(f"使用替代路径仍然失败: {str(e2)}")
                return False
        except Exception as e:
            logger.error(f"下载媒体失败: {str(e)}")
            return False

    def _download_media_files(self, aweme: dict, path: Path, name: str, desc: str) -> None:
        """下载所有媒体文件"""
        try:
            # 确保路径是有效的
            path = Path(str(path).rstrip())
            
            # 确保目录存在
            path.mkdir(parents=True, exist_ok=True)
            
            # 视频或图集下载
            if aweme["awemeType"] == 0:  # 视频
                video_path = path / f"{name}_video.mp4"
                if url := aweme.get("video", {}).get("play_addr", {}).get("url_list", [None])[0]:
                    if not self._download_media(url, video_path, f"{desc}视频"):
                        raise Exception("视频下载失败")
                    
            elif aweme["awemeType"] == 1:  # 图集
                for i, image in enumerate(aweme.get("images", [])):
                    if url := image.get("url_list", [None])[0]:
                        image_path = path / f"{name}_image_{i+1}.jpg"
                        if not self._download_media(url, image_path, f"{desc}图片{i+1}"):
                            # 继续下载其他图片，但记录失败
                            self.console.print(f"[yellow]⚠️  图片{i+1}下载失败[/]")

            # 下载音乐（非关键，失败不影响整体流程）
            if self.music and (url := aweme.get("music", {}).get("play_url", {}).get("url_list", [None])[0]):
                music_path = path / f"{name}_music.mp3"
                if not self._download_media(url, music_path, f"{desc}音乐"):
                    self.console.print(f"[yellow]⚠️  音乐下载失败[/]")

            # 下载封面（非关键，失败不影响整体流程）
            if self.cover and aweme["awemeType"] == 0:
                if url := aweme.get("video", {}).get("cover", {}).get("url_list", [None])[0]:
                    cover_path = path / f"{name}_cover.jpg"
                    if not self._download_media(url, cover_path, f"{desc}封面"):
                        self.console.print(f"[yellow]⚠️  封面下载失败[/]")

            # 下载头像（非关键，失败不影响整体流程）
            if self.avatar:
                if url := aweme.get("author", {}).get("avatar", {}).get("url_list", [None])[0]:
                    avatar_path = path / f"{name}_avatar.jpg"
                    if not self._download_media(url, avatar_path, f"{desc}头像"):
                        self.console.print(f"[yellow]⚠️  头像下载失败[/]")
                    
        except Exception as e:
            logger.error(f"下载媒体文件时出错: {str(e)}")
            raise Exception(f"下载失败: {str(e)}")

    def awemeDownload(self, awemeDict: dict, savePath: Path) -> None:
        """下载单个作品的所有内容"""
        if not awemeDict:
            logger.warning("无效的作品数据")
            return
            
        try:
            # 创建保存目录
            save_path = Path(savePath)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 获取用户信息和时间信息
            author_name = utils.replaceStr(awemeDict.get('author', {}).get('nickname', 'unknown'))
            create_time = awemeDict.get('create_time', time.strftime("%Y-%m-%d_%H.%M.%S"))
            
            # 构建文件名 - 使用用户名+时间命名，不再使用视频描述
            file_name = f"{author_name}_{create_time}"
            
            # 创建作品目录
            if self.folderstyle:
                # 处理目录名以避免路径问题
                aweme_path = save_path / file_name
                # 强制处理目录名，确保规范
                aweme_path = Path(str(aweme_path).rstrip())
                try:
                    aweme_path.mkdir(exist_ok=True)
                except Exception as e:
                    # 如果创建目录失败，使用简化的目录名
                    logger.warning(f"创建目录失败: {str(e)}, 尝试使用简化名称")
                    simple_name = f"User_{create_time}"
                    aweme_path = save_path / simple_name
                    aweme_path.mkdir(exist_ok=True)
                    # 更新文件名以匹配目录名
                    file_name = simple_name
            else:
                aweme_path = save_path
                
            # 保存原始描述到JSON数据的额外字段，方便以后查询
            if self.resjson:
                # 添加原始描述到JSON数据
                if 'desc' in awemeDict:
                    awemeDict['original_desc'] = awemeDict['desc']
                # 添加用于显示的文件名信息
                awemeDict['file_name'] = file_name
                
                json_path = aweme_path / f"{file_name}_result.json"
                self._save_json(json_path, awemeDict)
            
            # 下载媒体文件
            self._download_media_files(awemeDict, aweme_path, file_name, f"[{author_name}]")
                
        except Exception as e:
            logger.error(f"处理作品时出错: {str(e)}")
            # 重新抛出异常，以便上层函数可以感知到错误
            raise

    def _save_json(self, path: Path, data: dict) -> None:
        """保存JSON数据，确保使用UTF-8编码"""
        try:
            # 确保路径存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用UTF-8编码保存JSON文件
            with open(path, "w", encoding='utf-8', errors='ignore') as f:
                json.dump(data, ensure_ascii=False, indent=2, fp=f)
        except UnicodeEncodeError as e:
            logger.error(f"保存JSON时遇到编码错误: {path}, 错误: {str(e)}")
            # 尝试使用不同的方法保存
            try:
                # 移除可能导致问题的字符
                import re
                text = json.dumps(data, ensure_ascii=False, indent=2)
                # 移除不可打印字符
                text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
                with open(path, "w", encoding='utf-8', errors='ignore') as f:
                    f.write(text)
                logger.info(f"已清理特殊字符后保存JSON: {path}")
            except Exception as e2:
                logger.error(f"二次尝试保存JSON失败: {path}, 错误: {str(e2)}")
        except Exception as e:
            logger.error(f"保存JSON失败: {path}, 错误: {str(e)}")

    def userDownload(self, awemeList: List[dict], savePath: Path):
        if not awemeList:
            self.console.print("[yellow]⚠️  没有找到可下载的内容[/]")
            return

        save_path = Path(savePath)
        save_path.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        total_count = len(awemeList)
        success_count = 0
        failed_count = 0
        
        # 显示下载信息面板
        self.console.print(Panel(
            Text.assemble(
                ("下载配置\n", "bold cyan"),
                (f"总数: {total_count} 个作品\n", "cyan"),
                (f"线程: {self.thread}\n", "cyan"),
                (f"保存路径: {save_path}\n", "cyan"),
            ),
            title="抖音下载器",
            border_style="cyan"
        ))

        with self.progress:
            download_task = self.progress.add_task(
                "[cyan]📥 批量下载进度", 
                total=total_count
            )
            
            for i, aweme in enumerate(awemeList):
                try:
                    # 显示当前正在下载的作品信息
                    desc = aweme.get('desc', '未知')[:30]
                    create_time = aweme.get('create_time', '')
                    self.console.print(f"[cyan]⬇️ 下载[{i+1}/{total_count}]: {create_time} - {desc}[/]")
                    
                    self.awemeDownload(awemeDict=aweme, savePath=save_path)
                    success_count += 1
                    self.progress.update(download_task, advance=1)
                except Exception as e:
                    # 详细记录失败原因
                    failed_count += 1
                    self.console.print(f"[red]❌ 下载失败[{i+1}/{total_count}]: {str(e)}[/]")
                    # 尝试获取更多错误信息
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
                    self.progress.update(download_task, advance=1)

        # 显示下载完成统计
        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.console.print(Panel(
            Text.assemble(
                ("下载完成\n", "bold green"),
                (f"成功: {success_count}/{total_count}\n", "green"),
                (f"失败: {failed_count}/{total_count}\n", "red" if failed_count > 0 else "green"),
                (f"用时: {minutes}分{seconds}秒\n", "green"),
                (f"保存位置: {save_path}\n", "green"),
            ),
            title="下载统计",
            border_style="green"
        ))

    def download_with_resume(self, url: str, filepath: Path, desc: str) -> bool:
        """支持断点续传的下载方法"""
        file_size = filepath.stat().st_size if filepath.exists() else 0
        headers = {'Range': f'bytes={file_size}-'} if file_size > 0 else {}
        
        for attempt in range(self.retry_times):
            try:
                response = requests.get(url, headers={**douyin_headers, **headers}, 
                                     stream=True, timeout=self.timeout)
                
                if response.status_code not in (200, 206):
                    raise Exception(f"HTTP {response.status_code}")
                    
                total_size = int(response.headers.get('content-length', 0)) + file_size
                mode = 'ab' if file_size > 0 else 'wb'
                
                with self.progress:
                    task = self.progress.add_task(f"[cyan]⬇️  {desc}", total=total_size)
                    self.progress.update(task, completed=file_size)  # 更新断点续传的进度
                    
                    with open(filepath, mode) as f:
                        for chunk in response.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                size = f.write(chunk)
                                self.progress.update(task, advance=size)
                                
                return True
                
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.retry_times}): {str(e)}")
                if attempt == self.retry_times - 1:
                    self.console.print(f"[red]❌ 下载失败: {desc}\n   {str(e)}[/]")
                    return False
                time.sleep(1)  # 重试前等待


class DownloadManager:
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def download_with_resume(self, url, filepath, callback=None):
        # 检查是否存在部分下载的文件
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        headers = {'Range': f'bytes={file_size}-'}
        
        response = requests.get(url, headers=headers, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        mode = 'ab' if file_size > 0 else 'wb'
        
        with open(filepath, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    if callback:
                        callback(len(chunk))


if __name__ == "__main__":
    pass
