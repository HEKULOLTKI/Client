#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF预览客户端 - 修复版本
修复了模块导入问题和中文文件名编码处理
"""

import sys
import json
import threading
import subprocess
import os
import time
import tempfile
import platform
import shutil
import requests
import logging
from urllib.parse import unquote, quote
import re
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QKeySequence
from flask import Flask, request, jsonify
from flask_cors import CORS

# 解决模块导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 简化的过渡屏幕类（避免导入问题）
class TransitionScreen:
    def __init__(self, message, duration):
        print(f"过渡屏幕: {message} (持续 {duration}ms)")
    def show(self):
        pass

# 禁用Flask的默认日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class ProcessMonitor(QThread):
    """进程监控线程 - 监控desktop_manager进程状态"""
    process_ended = pyqtSignal()
    
    def __init__(self, process):
        super().__init__()
        self.process = process
        self.running = True
        
    def run(self):
        """监控进程状态"""
        print(f"🔍 开始监控desktop_manager进程 (PID: {self.process.pid})...")
        
        while self.running and self.process:
            try:
                # 检查进程是否仍在运行
                return_code = self.process.poll()
                if return_code is not None:
                    # 进程已结束
                    print(f"🔔 检测到desktop_manager进程已结束，返回代码: {return_code}")
                    self.process_ended.emit()
                    break
                    
                # 每500毫秒检查一次，提高响应速度
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ 监控进程时出错: {str(e)}")
                # 即使出错也尝试清理
                self.process_ended.emit()
                break
                
    def stop(self):
        """停止监控"""
        self.running = False


class APIServer(QObject):
    # 定义信号用于跨线程通信
    close_fullscreen_signal = pyqtSignal()
    open_digital_twin_signal = pyqtSignal(str)  # 新增信号，传递孪生平台URL
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = Flask(__name__)
        
        # 配置CORS，允许来自任何地址的访问
        CORS(self.app, resources={
            r"/upload": {
                "origins": "*",
                "methods": ["POST"],
                "allow_headers": ["Content-Type"]
            },
            r"/status": {
                "origins": "*",
                "methods": ["GET"]
            },
            r"/get-tasks": {
                "origins": "*",
                "methods": ["GET"]
            },
            r"/pdf-preview": {
                "origins": "*",
                "methods": ["POST"],
                "allow_headers": ["Content-Type"]
            }
        })
        
        # 存储接收到的任务数据
        self.received_tasks = []
        self.user_session_info = {}
        
        # PDF下载统计（简化版本）
        self.download_stats = {
            "total_requests": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "network_errors": 0,
            "file_errors": 0
        }
        
        # 配置日志
        self.setup_logging()
        
        self.setup_routes()
    
    def setup_logging(self):
        """配置详细日志"""
        # 创建logger
        self.logger = logging.getLogger('PDFClient')
        self.logger.setLevel(logging.INFO)
        
        # 避免重复配置
        if not self.logger.handlers:
            try:
                # 创建文件处理器
                file_handler = logging.FileHandler('pdf_client.log', encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                
                # 创建控制台处理器
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                
                # 创建格式器
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)
                
                # 添加处理器到logger
                self.logger.addHandler(file_handler)
                self.logger.addHandler(console_handler)
            except Exception as e:
                print(f"⚠️ 日志配置失败: {str(e)}")
    
    def update_download_stats(self, result_type: str):
        """更新下载统计"""
        if "total_requests" not in self.download_stats:
            self.download_stats["total_requests"] = 0
        
        self.download_stats["total_requests"] += 1
        if result_type in self.download_stats:
            self.download_stats[result_type] += 1
        
        # 定期输出统计信息
        if self.download_stats["total_requests"] % 5 == 0:
            print(f"📊 下载统计: {self.download_stats}")
            if hasattr(self, 'logger'):
                self.logger.info(f"下载统计: {self.download_stats}")
        
    def setup_routes(self):
        """设置API路由"""
        @self.app.route('/upload', methods=['POST', 'OPTIONS'])
        def upload_json():
            # 处理OPTIONS预检请求
            if request.method == 'OPTIONS':
                return '', 200
                
            try:
                # 检查是否是JSON数据
                if not request.is_json:
                    return jsonify({'error': '请求必须是JSON格式'}), 400
                
                # 获取JSON数据
                json_data = request.get_json()
                
                print(f"接收到JSON数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
                
                # 保存JSON文件到本地（可选）
                try:
                    with open('received_data.json', 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"⚠️ 保存JSON文件失败: {str(e)}")
                
                return jsonify({'message': 'JSON文件接收成功', 'status': 'success'})
                
            except Exception as e:
                print(f"处理JSON数据时出错: {str(e)}")
                return jsonify({'error': f'处理数据时出错: {str(e)}'}), 500
        
        @self.app.route('/pdf-preview', methods=['POST', 'OPTIONS'])
        def pdf_preview():
            """处理PDF预览请求"""
            # 处理OPTIONS预检请求
            if request.method == 'OPTIONS':
                return '', 200
                
            try:
                # 检查是否是JSON数据
                if not request.is_json:
                    return jsonify({'error': '请求必须是JSON格式'}), 400
                
                # 获取JSON数据
                pdf_data = request.get_json()
                
                print(f"📄 接收到PDF预览请求: {json.dumps(pdf_data, ensure_ascii=False, indent=2)}")
                
                # 验证数据格式
                if pdf_data.get('action') != 'pdf_download_and_preview':
                    return jsonify({'error': '无效的操作类型'}), 400
                
                # 提取必要信息
                if 'data' not in pdf_data:
                    return jsonify({'error': '缺少data字段'}), 400
                
                data = pdf_data['data']
                filename = data.get('filename')
                download_url = data.get('download_url')
                file_size = data.get('file_size', 0)
                
                if not filename or not download_url:
                    return jsonify({'error': '缺少必要的文件信息'}), 400
                
                print(f"📋 文件名: {filename}")
                print(f"🔗 下载URL: {download_url}")
                print(f"📏 文件大小: {file_size} bytes")
                
                # 发送成功响应
                response = {
                    "status": "success",
                    "message": "PDF预览请求已接收",
                    "timestamp": time.time(),
                    "received_data": {
                        "filename": filename,
                        "file_size": file_size
                    }
                }
                
                # 在新线程中处理PDF下载和打开
                threading.Thread(
                    target=self.download_and_open_pdf,
                    args=(pdf_data,),
                    daemon=True
                ).start()
                
                return jsonify(response)
                
            except Exception as e:
                print(f"❌ 处理PDF预览请求时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'处理PDF预览请求时出错: {str(e)}'}), 500
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """API状态检查"""
            return jsonify({'message': 'API服务器运行正常', 'port': 8800})
        
        @self.app.route('/get-tasks', methods=['GET'])
        def get_stored_tasks():
            """获取存储的任务数据"""
            return jsonify({
                'tasks': self.received_tasks,
                'user_info': self.user_session_info,
                'status': 'success'
            })
    
    def decode_filename(self, filename):
        """安全解码文件名，处理中文字符"""
        try:
            # 如果文件名已经是Unicode字符串，直接返回
            if isinstance(filename, str):
                # 尝试URL解码（如果是URL编码的）
                try:
                    decoded = unquote(filename, encoding='utf-8')
                    if hasattr(self, 'logger'):
                        self.logger.info(f"URL解码文件名: {filename} -> {decoded}")
                    return decoded
                except Exception:
                    return filename
            
            # 如果是字节串，尝试解码
            if isinstance(filename, bytes):
                return filename.decode('utf-8', errors='replace')
            
            return str(filename)
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"文件名解码失败: {str(e)}")
            print(f"❌ 文件名解码失败: {str(e)}")
            # 返回安全的默认文件名
            return "document.pdf"
    
    def sanitize_filename(self, filename):
        """清理文件名，确保在文件系统中安全"""
        try:
            # 解码文件名
            decoded_filename = self.decode_filename(filename)
            
            # 移除或替换不安全的字符
            # Windows文件名不能包含: < > : " | ? * \ /
            unsafe_chars = r'[<>:"|?*\\\/]'
            safe_filename = re.sub(unsafe_chars, '_', decoded_filename)
            
            # 移除前后空格和点
            safe_filename = safe_filename.strip(' .')
            
            # 确保文件名不为空
            if not safe_filename or safe_filename == '.pdf':
                safe_filename = "document.pdf"
            
            # 确保有.pdf扩展名
            if not safe_filename.lower().endswith('.pdf'):
                # 如果原文件名没有扩展名，添加.pdf
                if '.' not in safe_filename:
                    safe_filename += '.pdf'
                else:
                    # 如果有其他扩展名，替换为.pdf
                    safe_filename = os.path.splitext(safe_filename)[0] + '.pdf'
            
            # 限制文件名长度（Windows路径限制）
            if len(safe_filename) > 200:
                name_part = safe_filename[:-4]  # 移除.pdf
                safe_filename = name_part[:196] + '.pdf'  # 保留.pdf
            
            if hasattr(self, 'logger'):
                self.logger.info(f"文件名清理: {filename} -> {safe_filename}")
            print(f"🔧 文件名清理: {filename} -> {safe_filename}")
            return safe_filename
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"文件名清理失败: {str(e)}")
            print(f"❌ 文件名清理失败: {str(e)}")
            return "document.pdf"
    
    def extract_filename_from_url(self, url):
        """从URL中提取文件名"""
        try:
            from urllib.parse import urlparse, unquote
            
            parsed = urlparse(url)
            path = parsed.path
            
            # 从路径中提取文件名
            if '/' in path:
                filename = path.split('/')[-1]
            else:
                filename = path
            
            # URL解码文件名
            if filename:
                filename = unquote(filename, encoding='utf-8')
                if hasattr(self, 'logger'):
                    self.logger.info(f"从URL提取文件名: {url} -> {filename}")
                print(f"🔗 从URL提取文件名: {url} -> {filename}")
                return filename
            
            return None
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"从URL提取文件名失败: {str(e)}")
            print(f"❌ 从URL提取文件名失败: {str(e)}")
            return None
    
    def extract_filename_from_content_disposition(self, content_disposition):
        """从Content-Disposition头中提取文件名"""
        try:
            # 尝试匹配 filename*=UTF-8''encoded_filename (RFC 5987)
            rfc5987_match = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition)
            if rfc5987_match:
                encoded_filename = rfc5987_match.group(1)
                decoded_filename = unquote(encoded_filename, encoding='utf-8')
                if hasattr(self, 'logger'):
                    self.logger.info(f"从Content-Disposition提取文件名(RFC5987): {decoded_filename}")
                print(f"📋 从Content-Disposition提取文件名(RFC5987): {decoded_filename}")
                return decoded_filename
            
            # 尝试匹配 filename="filename" 或 filename=filename
            filename_match = re.search(r'filename="?([^";]+)"?', content_disposition)
            if filename_match:
                filename = filename_match.group(1)
                # 尝试解码（可能是URL编码或其他编码）
                try:
                    decoded_filename = unquote(filename, encoding='utf-8')
                    if hasattr(self, 'logger'):
                        self.logger.info(f"从Content-Disposition提取文件名(标准): {decoded_filename}")
                    print(f"📋 从Content-Disposition提取文件名(标准): {decoded_filename}")
                    return decoded_filename
                except:
                    if hasattr(self, 'logger'):
                        self.logger.info(f"从Content-Disposition提取文件名(原始): {filename}")
                    print(f"📋 从Content-Disposition提取文件名(原始): {filename}")
                    return filename
            
            if hasattr(self, 'logger'):
                self.logger.warning(f"无法从Content-Disposition提取文件名: {content_disposition}")
            print(f"⚠️ 无法从Content-Disposition提取文件名: {content_disposition}")
            return None
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"解析Content-Disposition失败: {str(e)}")
            print(f"❌ 解析Content-Disposition失败: {str(e)}")
            return None
    
    def download_and_open_pdf(self, pdf_data):
        """下载并打开PDF文件 - 支持中文文件名处理"""
        try:
            # 更新统计
            self.update_download_stats("total_requests")
            
            # 提取基本信息
            data = pdf_data['data']
            original_filename = data['filename']
            download_url = data['download_url']
            file_size = data.get('file_size', 0)
            
            # 优化文件名处理
            filename = self.sanitize_filename(original_filename)
            
            # 尝试从URL中提取更准确的文件名
            url_filename = self.extract_filename_from_url(download_url)
            if url_filename:
                url_filename = self.sanitize_filename(url_filename)
                if url_filename != "document.pdf":  # 如果从URL提取的文件名有效
                    filename = url_filename
            
            print(f"\n📄 收到PDF预览请求:")
            print(f"   📋 原始文件名: {original_filename}")
            print(f"   🔧 清理后文件名: {filename}")
            print(f"   🔗 下载URL: {download_url}")
            print(f"   📏 文件大小: {file_size} bytes")
            
            if hasattr(self, 'logger'):
                self.logger.info(f"收到PDF预览请求: {filename}")
            
            # 验证文件类型
            if not filename.lower().endswith('.pdf'):
                print(f"❌ 不支持的文件类型: {filename}")
                self.update_download_stats("failed_downloads")
                return
            
            # 验证下载URL
            if not download_url.startswith(('http://', 'https://', 'file://')):
                print(f"❌ 无效的下载URL协议: {download_url}")
                self.update_download_stats("failed_downloads")
                return
            
            # 创建临时目录
            temp_dir = os.path.join(tempfile.gettempdir(), 'ACO_PDF_Preview')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 构建本地文件路径
            local_path = os.path.join(temp_dir, filename)
            
            print(f"\n📥 开始下载PDF文件...")
            print(f"   💾 保存路径: {local_path}")
            
            # 下载文件
            if self.download_file(download_url, local_path, file_size):
                # 验证下载的文件
                actual_size = os.path.getsize(local_path)
                if file_size > 0 and actual_size != file_size:
                    print(f"⚠️ 警告: 文件大小不匹配 (期望: {file_size}, 实际: {actual_size})")
                    if hasattr(self, 'logger'):
                        self.logger.warning(f"文件大小不匹配: 期望 {file_size}, 实际 {actual_size}")
                
                print(f"✅ PDF文件处理完成!")
                print(f"   📁 本地路径: {local_path}")
                print(f"   📏 实际大小: {actual_size} bytes")
                
                # 打开PDF文件
                self.open_pdf_file(local_path)
                
                # 更新成功统计
                self.update_download_stats("successful_downloads")
                if hasattr(self, 'logger'):
                    self.logger.info(f"PDF文件成功处理: {filename}")
                
            else:
                print("❌ PDF文件下载失败")
                self.update_download_stats("failed_downloads")
                
        except Exception as e:
            print(f"❌ 处理PDF文件时出错: {str(e)}")
            if hasattr(self, 'logger'):
                self.logger.error(f"处理PDF文件出错: {str(e)}")
            self.update_download_stats("failed_downloads")
            import traceback
            traceback.print_exc()
    
    def download_file(self, download_url, local_path, file_size):
        """下载文件"""
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(download_url)
            
            if parsed_url.scheme == 'file':
                # 本地文件协议，直接复制文件
                source_path = parsed_url.path
                print(f"📁 本地文件复制: {source_path} -> {local_path}")
                
                shutil.copy2(source_path, local_path)
                return True
                
            else:
                # HTTP/HTTPS协议，下载文件
                print(f"🌐 开始网络下载...")
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()
                
                # 尝试从Content-Disposition头中获取文件名
                content_disposition = response.headers.get('content-disposition', '')
                if content_disposition:
                    server_filename = self.extract_filename_from_content_disposition(content_disposition)
                    if server_filename:
                        # 使用服务器提供的文件名更新本地路径
                        server_filename = self.sanitize_filename(server_filename)
                        local_dir = os.path.dirname(local_path)
                        local_path = os.path.join(local_dir, server_filename)
                        print(f"📋 使用服务器文件名: {server_filename}")
                        if hasattr(self, 'logger'):
                            self.logger.info(f"使用服务器文件名: {server_filename}")
                
                # 检查文件大小
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) != file_size:
                    print(f"⚠️ 文件大小不匹配: 预期 {file_size}, 实际 {content_length}")
                
                # 保存到本地
                downloaded_size = 0
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if file_size > 0:
                            progress = (downloaded_size / file_size) * 100
                            print(f"📊 下载进度: {progress:.1f}%", end='\r')
                
                print(f"\n✅ 下载成功！文件大小: {downloaded_size} bytes")
                if hasattr(self, 'logger'):
                    self.logger.info(f"下载成功: {local_path}, 大小: {downloaded_size} bytes")
                return True
                
        except Exception as e:
            print(f"❌ 下载文件失败: {str(e)}")
            if hasattr(self, 'logger'):
                self.logger.error(f"下载文件失败: {str(e)}")
            self.update_download_stats("network_errors")
            return False
    
    def open_pdf_file(self, file_path):
        """使用PyMuPDF弹窗查看器打开PDF文件"""
        try:
            print(f"🔍 使用PDF弹窗查看器打开文件: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False
            
            # 导入PDF查看器组件
            try:
                # 添加项目根目录到路径
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(current_dir))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                
                from src.ui.widgets.pdf_viewer_widget import show_pdf_viewer
                print("✅ 成功导入PDF查看器组件")
                
                # 在新线程中显示PDF查看器（避免阻塞主线程）
                def show_viewer():
                    try:
                        show_pdf_viewer(file_path, None)
                        print(f"✅ PDF弹窗查看器已显示: {file_path}")
                    except Exception as e:
                        print(f"❌ 显示PDF查看器失败: {str(e)}")
                        # 如果弹窗失败，尝试使用系统默认程序
                        self._fallback_open_pdf(file_path)
                
                # 在新线程中启动查看器
                viewer_thread = threading.Thread(target=show_viewer, daemon=True)
                viewer_thread.start()
                
                print(f"✅ PDF查看器线程已启动")
                return True
                
            except ImportError as e:
                print(f"⚠️ 无法导入PDF查看器组件: {str(e)}")
                print("🔄 回退到系统默认程序打开PDF")
                return self._fallback_open_pdf(file_path)
            
        except Exception as e:
            print(f"❌ 打开PDF文件失败: {str(e)}")
            # 如果出错，尝试使用系统默认程序
            return self._fallback_open_pdf(file_path)
    
    def _fallback_open_pdf(self, file_path):
        """回退方法：使用系统默认程序打开PDF"""
        try:
            print(f"🔄 使用系统默认程序打开PDF: {file_path}")
            
            system = platform.system()
            
            print(f"🖥️ 检测到操作系统: {system}")
            print(f"📄 准备打开PDF文件: {file_path}")
            
            if system == 'Windows':
                os.startfile(file_path)
                print("✅ 已使用Windows默认程序打开PDF")
            elif system == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
                print("✅ 已使用macOS默认程序打开PDF")
            elif system == 'Linux':
                subprocess.call(['xdg-open', file_path])
                print("✅ 已使用Linux默认程序打开PDF")
            else:
                print(f"❌ 不支持的操作系统: {system}")
                print(f"📁 请手动打开文件: {file_path}")
                return False
            
            print("🎉 PDF文件已成功打开")
            return True
            
        except Exception as e:
            print(f"❌ 使用系统默认程序打开PDF失败: {str(e)}")
            print(f"📁 请手动打开文件: {file_path}")
            return False

    def run(self):
        """运行API服务器"""
        try:
            print("🚀 API服务器启动中，监听8800端口...")
            print("🌐 CORS已启用，允许来自任何地址的跨域请求")
            print("📄 PDF预览功能已启用，支持中文文件名")
            self.app.run(host='0.0.0.0', port=8800, debug=False, threaded=True)
        except Exception as e:
            print(f"❌ API服务器启动失败: {str(e)}")


class FullscreenBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_server = None
        self.api_thread = None
        self.desktop_manager_process = None
        self.process_monitor = None
        self.transition_screen = None
        self.should_close_desktop_manager = True
        self.init_ui()
        self.start_api_server()
    
    def init_ui(self):
        # 创建QWebEngineView
        self.browser = QWebEngineView()
        
        # 设置为中央组件
        self.setCentralWidget(self.browser)
        
        # 加载网页
        self.browser.load(QUrl("http://172.18.122.8:3000"))
        
        # 设置窗口标题
        self.setWindowTitle("全屏浏览器 - localhost:3000 | API: 8800端口")
        
        # 全屏显示
        self.showFullScreen()
        
        # 连接页面加载完成信号
        self.browser.loadFinished.connect(self.on_load_finished)
    
    def start_api_server(self):
        """在单独的线程中启动API服务器"""
        try:
            self.api_server = APIServer()
            
            self.api_thread = threading.Thread(target=self.api_server.run, daemon=True)
            self.api_thread.start()
            print("✅ API服务器线程已启动")
        except Exception as e:
            print(f"❌ 启动API服务器时出错: {str(e)}")
    
    def on_load_finished(self, success):
        """页面加载完成后的回调"""
        if success:
            print("🌐 网页加载成功！")
            print("📡 API服务器地址: http://localhost:8800")
            print("📤 上传JSON数据: POST http://localhost:8800/upload")
            print("📄 PDF预览: POST http://localhost:8800/pdf-preview")
            print("📊 检查API状态: GET http://localhost:8800/status")
            print("\n🔧 功能提示：")
            print("  📋 支持接收任务数据和PDF预览请求")
            print("  🌐 支持中文文件名的PDF下载和预览")
            print("  🔒 已启用CORS，支持跨域请求")
            print("\n⌨️ 键盘快捷键：")
            print("  ESC - 退出程序")
            print("  F11 - 切换全屏状态")
            print("  F5  - 刷新页面")
        else:
            print("❌ 网页加载失败，请检查网络连接")
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # 按ESC键退出程序
        if event.key() == Qt.Key_Escape:
            self.close()
        # 按F11切换全屏状态
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        # 按F5刷新页面
        elif event.key() == Qt.Key_F5:
            self.browser.reload()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        print("🔄 正在关闭应用程序...")
        event.accept()


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序名称
    app.setApplicationName("PDF预览客户端")
    
    # 创建并显示主窗口
    window = FullscreenBrowser()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 