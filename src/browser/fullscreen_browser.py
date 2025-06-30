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
import logging
# 解决模块导入问题
import sys
import os

# 获取项目根目录并添加到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.ui.screens.transition_screen import TransitionScreen
    print("✅ 成功导入transition_screen模块")
except ImportError:
    try:
        # 尝试相对导入
        from ui.screens.transition_screen import TransitionScreen
        print("✅ 成功使用相对路径导入transition_screen模块")
    except ImportError:
        # 如果都失败，创建一个简单的占位类
        print("⚠️ 导入transition_screen失败，使用占位类")
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
                "origins": "*",  # 允许来自任何来源
                "methods": ["POST"],
                "allow_headers": ["Content-Type"]
            },
            r"/status": {
                "origins": "*",  # 允许来自任何来源
                "methods": ["GET"]
            },
            r"/get-tasks": {
                "origins": "*",  # 允许来自任何来源
                "methods": ["GET"]
            },
            r"/pdf-preview": {
                "origins": "*",  # 允许来自任何来源
                "methods": ["POST"],
                "allow_headers": ["Content-Type"]
            }
        })
        
        # 存储接收到的任务数据
        self.received_tasks = []
        self.user_session_info = {}
        
        # PDF下载统计
        self.download_stats = {
            "total_requests": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "network_errors": 0,
            "file_errors": 0,
            "access_denied": 0,
            "unexpected_auth_errors": 0
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
    
    def update_download_stats(self, result_type: str):
        """更新下载统计"""
        self.download_stats["total_requests"] += 1
        if result_type in self.download_stats:
            self.download_stats[result_type] += 1
        
        # 定期输出统计信息
        if self.download_stats["total_requests"] % 5 == 0:
            print(f"📊 下载统计: {self.download_stats}")
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
                
                # 这里可以处理接收到的JSON数据
                print(f"接收到JSON数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
                
                # 检查是否是数字孪生平台数据
                digital_twin_url = self.extract_digital_twin_url(json_data)
                if digital_twin_url:
                    print(f"检测到数字孪生平台数据，准备打开孪生平台网页: {digital_twin_url}")
                    
                    # 发射信号通知主线程打开孪生平台
                    self.open_digital_twin_signal.emit(digital_twin_url)
                    
                # 检查是否是特定的用户角色选择数据
                elif self.is_role_selection_data(json_data):
                    print("检测到角色选择数据，准备关闭全屏网页...")
                    
                    # 提取并存储任务数据和用户信息
                    self.extract_and_store_data(json_data)
                    
                    # 发射信号通知主线程关闭全屏
                    self.close_fullscreen_signal.emit()
                
                # 保存JSON文件到本地（可选）
                with open('received_data.json', 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
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
    
    def extract_digital_twin_url(self, data):
        """检测并提取数字孪生平台的访问地址"""
        try:
            # 递归搜索JSON数据中的数字孪生平台信息
            def search_digital_twin(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        # 检查是否包含数字孪生平台的描述
                        if key == "description" and isinstance(value, str):
                            if "数字孪生平台系统访问地址" in value:
                                print(f"✅ 找到数字孪生平台描述: {value}")
                                # 在同一级别或附近寻找URL
                                parent_obj = obj
                                return self.find_url_in_object(parent_obj, current_path)
                        
                        # 递归搜索子对象
                        result = search_digital_twin(value, current_path)
                        if result:
                            return result
                            
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        result = search_digital_twin(item, current_path)
                        if result:
                            return result
                
                return None
            
            url = search_digital_twin(data)
            if url:
                print(f"🔗 提取到数字孪生平台URL: {url}")
                return url
            else:
                print("❌ 未找到数字孪生平台的访问地址")
                return None
                
        except Exception as e:
            print(f"❌ 提取数字孪生平台URL时出错: {str(e)}")
            return None
    
    def find_url_in_object(self, obj, description_path):
        """在对象中查找URL字段"""
        if not isinstance(obj, dict):
            return None
        
        # 常见的URL字段名
        url_fields = ['url', 'link', 'address', 'href', 'endpoint', 'access_url', 'web_url', 'system_url']
        
        # 优先在同一个对象中查找URL
        for field in url_fields:
            if field in obj and isinstance(obj[field], str):
                url = obj[field].strip()
                if self.is_valid_url(url):
                    print(f"🔗 在字段 '{field}' 中找到URL: {url}")
                    return url
        
        # 如果没找到，尝试查找value字段或其他可能包含URL的字段
        for key, value in obj.items():
            if isinstance(value, str) and self.is_valid_url(value.strip()):
                print(f"🔗 在字段 '{key}' 中找到URL: {value.strip()}")
                return value.strip()
        
        return None
    
    def is_valid_url(self, url_string):
        """检查字符串是否是有效的URL"""
        if not url_string:
            return False
        
        # 基本的URL格式检查
        url_string = url_string.strip()
        
        # 检查是否以http或https开头
        if url_string.startswith(('http://', 'https://')):
            # 简单检查是否包含域名或IP地址
            if '.' in url_string or 'localhost' in url_string or '127.0.0.1' in url_string:
                return True
        
        # 检查是否是IP地址开头的URL（可能没有协议前缀）
        if url_string.startswith(('192.168.', '10.', '172.', '127.0.0.1', 'localhost')):
            return True
        
        return False

    def extract_and_store_data(self, data):
        """提取并存储任务数据和用户信息"""
        try:
            # 存储任务数据
            tasks = data.get('tasks', [])
            self.received_tasks = tasks
            print(f"存储了 {len(tasks)} 个任务")
            
            # 存储用户会话信息
            self.user_session_info = {
                'user': data.get('user', {}),
                'selectedRole': data.get('selectedRole', {}),
                'session': data.get('session', {}),
                'timestamp': data.get('timestamp', '')
            }
            
            # 将任务数据也保存到单独的文件
            with open('received_tasks.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'tasks': self.received_tasks,
                    'user_info': self.user_session_info,
                    'updated_at': data.get('timestamp', '')
                }, f, ensure_ascii=False, indent=2)
            
            print(f"任务数据已保存到 received_tasks.json")
            print(f"用户: {self.user_session_info.get('user', {}).get('username', 'Unknown')}")
            print(f"角色: {self.user_session_info.get('selectedRole', {}).get('label', 'Unknown')}")
            
        except Exception as e:
            print(f"提取存储数据时出错: {str(e)}")
    
    def is_role_selection_data(self, data):
        """检查是否是有效的数据格式（支持新格式和旧格式）"""
        
        # 检查新格式：任务分配版本
        if data.get('action') == 'task_deployment':
            print(f"🆕 检测到新格式数据（任务分配版本）")
            
            # 检查新格式的必需字段
            required_fields = ['action', 'deployment_info', 'assigned_tasks', 'deployment_summary']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ 新格式缺少必需字段: {missing_fields}")
                return False
            
            # 验证deployment_info结构
            deployment_info = data.get('deployment_info', {})
            required_deployment_fields = ['target_role', 'deployment_time', 'operator']
            missing_deployment_fields = [field for field in required_deployment_fields if field not in deployment_info]
            
            if missing_deployment_fields:
                print(f"❌ deployment_info缺少字段: {missing_deployment_fields}")
                return False
            
            # 验证operator结构
            operator = deployment_info.get('operator', {})
            required_operator_fields = ['user_id', 'username', 'operator_role']
            missing_operator_fields = [field for field in required_operator_fields if field not in operator]
            
            if missing_operator_fields:
                print(f"❌ operator缺少字段: {missing_operator_fields}")
                return False
            
            # 验证任务数组
            assigned_tasks = data.get('assigned_tasks', [])
            if not assigned_tasks:
                print(f"❌ assigned_tasks不能为空")
                return False
            
            # 验证每个任务的基本字段
            for i, task in enumerate(assigned_tasks):
                required_task_fields = ['assignment_id', 'assignment_status', 'task_id', 'task_name', 'task_type']
                missing_task_fields = [field for field in required_task_fields if field not in task]
                if missing_task_fields:
                    print(f"❌ 任务{i}缺少字段: {missing_task_fields}")
                    return False
            
            print(f"✅ 新格式数据验证通过:")
            print(f"   🎯 目标角色: {deployment_info.get('target_role')}")
            print(f"   👤 操作员: {operator.get('username')} (ID: {operator.get('user_id')})")
            print(f"   📋 任务数量: {len(assigned_tasks)}")
            print(f"   🆔 部署ID: {data.get('deployment_summary', {}).get('deployment_id')}")
            return True
        
        # 检查旧格式：传统任务版本
        elif 'tasks' in data and data['tasks']:
            print(f"📜 检测到旧格式数据（传统任务版本）")
            
            # 检查旧格式的基本字段
            tasks = data.get('tasks', [])
            if not isinstance(tasks, list) or not tasks:
                print(f"❌ tasks字段格式不正确或为空")
                return False
            
            # 验证任务格式
            for i, task in enumerate(tasks):
                if not isinstance(task, dict):
                    print(f"❌ 任务{i}格式不正确，应为字典类型")
                    return False
                
                # 检查任务的基本字段
                required_task_fields = ['id', 'name']
                missing_fields = [field for field in required_task_fields if field not in task]
                if missing_fields:
                    print(f"❌ 任务{i}缺少字段: {missing_fields}")
                    return False
            
            print(f"✅ 旧格式数据验证通过:")
            print(f"   📋 任务数量: {len(tasks)}")
            if 'user' in data:
                print(f"   👤 用户: {data['user'].get('username', '未知')}")
            if 'selectedRole' in data:
                print(f"   🎯 角色: {data['selectedRole'].get('label', '未知')}")
            return True
        
        # 检查用户数据同步格式
        elif data.get('action') == 'user_data_sync':
            print(f"🔄 检测到用户数据同步格式")
            
            # 检查用户数据同步的必需字段
            required_fields = ['action', 'sync_info', 'users', 'sync_summary']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ 用户数据同步缺少必需字段: {missing_fields}")
                return False
            
            # 验证sync_info结构
            sync_info = data.get('sync_info', {})
            required_sync_fields = ['sync_type', 'sync_time', 'operator']
            missing_sync_fields = [field for field in required_sync_fields if field not in sync_info]
            
            if missing_sync_fields:
                print(f"❌ sync_info缺少字段: {missing_sync_fields}")
                return False
            
            # 验证operator结构
            operator = sync_info.get('operator', {})
            required_operator_fields = ['user_id', 'username', 'operator_role']
            missing_operator_fields = [field for field in required_operator_fields if field not in operator]
            
            if missing_operator_fields:
                print(f"❌ operator缺少字段: {missing_operator_fields}")
                return False
            
            # 验证用户数组
            users = data.get('users', [])
            if not users:
                print(f"❌ users不能为空")
                return False
            
            # 验证每个用户的基本字段
            for i, user in enumerate(users):
                required_user_fields = ['id', 'username', 'role', 'type', 'status']
                missing_user_fields = [field for field in required_user_fields if field not in user]
                if missing_user_fields:
                    print(f"❌ 用户{i}缺少字段: {missing_user_fields}")
                    return False
            
            print(f"✅ 用户数据同步验证通过:")
            print(f"   🔄 同步类型: {sync_info.get('sync_type')}")
            print(f"   👤 操作员: {operator.get('username')} (ID: {operator.get('user_id')})")
            print(f"   👥 用户数量: {len(users)}")
            print(f"   🆔 同步ID: {data.get('sync_summary', {}).get('sync_id')}")
            return True
        
        # 检查是否是角色选择数据（特殊格式）
        elif data.get('action') == 'role_selection':
            print(f"🎭 检测到角色选择数据")
            
            required_fields = ['user', 'selectedRole', 'timestamp', 'action']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ 角色选择数据缺少必需字段: {missing_fields}")
                return False
            
            # 检查user字段
            user_data = data.get('user', {})
            user_required_fields = ['id', 'username', 'role']
            missing_user_fields = [field for field in user_required_fields if field not in user_data]
            if missing_user_fields:
                print(f"❌ user字段缺少必需子字段: {missing_user_fields}")
                return False
            
            # 检查selectedRole字段
            role_data = data.get('selectedRole', {})
            role_required_fields = ['value', 'label']
            missing_role_fields = [field for field in role_required_fields if field not in role_data]
            if missing_role_fields:
                print(f"❌ selectedRole字段缺少必需子字段: {missing_role_fields}")
                return False
            
            print(f"✅ 角色选择数据验证通过:")
            print(f"   👤 用户: {user_data.get('username')}")
            print(f"   🎯 角色: {role_data.get('label')}")
            return True
        
        # 无法识别的格式
        else:
            print(f"❌ 无法识别的数据格式:")
            print(f"   📋 数据字段: {list(data.keys())}")
            print(f"   🔍 action字段: {data.get('action', '未设置')}")
            print(f"   📝 支持的格式:")
            print(f"      - 任务分配: action='task_deployment' + deployment_info + assigned_tasks")
            print(f"      - 用户同步: action='user_data_sync' + sync_info + users")
            print(f"      - 旧格式: tasks数组 + 可选的user/selectedRole")
            print(f"      - 角色选择: action='role_selection' + user + selectedRole")
            return False
    
    def validate_download_request(self, pdf_data):
        """验证下载请求的基本信息"""
        try:
            data = pdf_data.get('data', {})
            filename = data.get('filename')
            download_url = data.get('download_url')
            
            if not filename:
                print("❌ 缺少文件名信息")
                self.logger.error("缺少文件名信息")
                return False
            
            if not download_url:
                print("❌ 缺少下载URL信息")
                self.logger.error("缺少下载URL信息")
                return False
            
            print(f"✅ 下载请求验证通过")
            print(f"   📋 文件名: {filename}")
            print(f"   🔗 下载URL: {download_url}")
            self.logger.info(f"下载请求验证通过: {filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ 下载请求验证时出错: {str(e)}")
            self.logger.error(f"下载请求验证出错: {str(e)}")
            return False
    
    def handle_download_error(self, error, pdf_data):
        """处理下载错误"""
        error_str = str(error)
        error_type = type(error).__name__
        
        self.logger.error(f"下载错误 ({error_type}): {error_str}")
        
        if 'timeout' in error_str.lower():
            print("⏱️ 下载超时 - 网络连接可能较慢")
            print("💡 建议: 检查网络连接或稍后重试")
            self.update_download_stats("network_errors")
            return "timeout"
        
        elif 'connection' in error_str.lower():
            print("🌐 网络连接问题 - 无法连接到服务器")
            print("💡 建议: 检查后端服务器是否正常运行")
            self.update_download_stats("network_errors")
            return "connection_error"
        
        elif '404' in error_str:
            print("📁 文件不存在 - 请检查文件路径")
            self.update_download_stats("file_errors")
            return "file_not_found"
        
        elif '403' in error_str:
            print("🚫 访问被拒绝 - 文件权限问题")
            print("💡 建议: 检查文件是否存在于允许的目录中")
            self.update_download_stats("file_errors")
            return "access_denied"
        
        elif '401' in error_str or 'Unauthorized' in error_str:
            print("🔐 认证错误 - 但PDF下载应该无需认证")
            print("💡 建议: 检查后端是否已正确移除认证要求")
            self.update_download_stats("failed_downloads")
            return "unexpected_auth_error"
        
        else:
            print(f"❌ 未知错误: {error_str}")
            self.update_download_stats("failed_downloads")
            return "unknown_error"
    
    def download_with_retry(self, download_url, local_path, file_size, max_retries=3):
        """带重试机制的下载函数"""
        from urllib.parse import urlparse
        parsed_url = urlparse(download_url)
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 下载尝试 {attempt + 1}/{max_retries}")
                self.logger.info(f"下载尝试 {attempt + 1}/{max_retries}: {download_url}")
                
                if parsed_url.scheme == 'file':
                    # 本地文件协议，直接复制文件
                    source_path = parsed_url.path
                    print(f"📁 本地文件复制: {source_path} -> {local_path}")
                    
                    shutil.copy2(source_path, local_path)
                    downloaded_size = os.path.getsize(local_path)
                    
                else:
                    # HTTP/HTTPS协议，下载文件
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
                            print(f"📋 服务器文件名: {server_filename}")
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
                self.logger.info(f"下载成功: {local_path}, 大小: {downloaded_size} bytes")
                return True
                
            except requests.exceptions.RequestException as e:
                error_type = self.handle_download_error(e, None)
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒、6秒
                    print(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 所有下载尝试均失败")
                    self.logger.error(f"所有下载尝试均失败: {str(e)}")
                    raise e
            except Exception as e:
                print(f"❌ 下载过程中出现意外错误: {str(e)}")
                self.logger.error(f"下载意外错误: {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)
        
        return False
    
    def download_and_open_pdf(self, pdf_data):
        """下载并打开PDF文件 - 增强版本，支持token验证和重试机制"""
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
            print(f"   📋 文件名: {filename}")
            print(f"   🔗 下载URL: {download_url}")
            print(f"   📏 文件大小: {file_size} bytes")
            
            self.logger.info(f"收到PDF预览请求: {filename}")
            
            # 验证下载请求
            if not self.validate_download_request(pdf_data):
                print("❌ 下载请求验证失败，跳过下载")
                self.update_download_stats("failed_downloads")
                return
            
            # 验证下载URL
            if not self.validate_download_url(download_url):
                print(f"❌ 无效的下载URL: {download_url}")
                self.update_download_stats("failed_downloads")
                return
            
            # 验证文件类型
            if not self.validate_file_type(filename):
                print(f"❌ 不支持的文件类型: {filename}")
                self.update_download_stats("failed_downloads")
                return
            
            # 创建临时目录
            temp_dir = os.path.join(tempfile.gettempdir(), 'ACO_PDF_Preview')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 构建本地文件路径
            local_path = os.path.join(temp_dir, filename)
            
            print(f"\n📥 开始下载PDF文件...")
            print(f"   💾 保存路径: {local_path}")
            
            # 使用带重试机制的下载
            if self.download_with_retry(download_url, local_path, file_size):
                # 验证下载的文件
                actual_size = os.path.getsize(local_path)
                if file_size > 0 and actual_size != file_size:
                    print(f"⚠️ 警告: 文件大小不匹配 (期望: {file_size}, 实际: {actual_size})")
                    self.logger.warning(f"文件大小不匹配: 期望 {file_size}, 实际 {actual_size}")
                
                print(f"✅ PDF文件处理完成!")
                print(f"   📁 本地路径: {local_path}")
                print(f"   📏 实际大小: {actual_size} bytes")
                
                # 打开PDF文件
                self.open_pdf_file(local_path)
                
                # 更新成功统计
                self.update_download_stats("successful_downloads")
                self.logger.info(f"PDF文件成功处理: {filename}")
                
            else:
                print("❌ PDF文件下载失败")
                self.update_download_stats("failed_downloads")
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"🔐 下载失败: 意外的认证错误")
                print(f"💡 建议: 检查后端是否已正确移除认证要求")
                self.update_download_stats("unexpected_auth_errors")
            elif e.response.status_code == 403:
                print(f"🚫 下载失败: 访问被拒绝")
                print(f"💡 建议: 检查文件权限和目录限制")
                self.update_download_stats("access_denied")
            elif e.response.status_code == 404:
                print(f"📁 下载失败: 文件不存在")
                self.update_download_stats("file_errors")
            else:
                print(f"❌ 下载失败: HTTP {e.response.status_code}")
                self.update_download_stats("failed_downloads")
            self.logger.error(f"HTTP错误: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            error_type = self.handle_download_error(e, pdf_data)
            print(f"❌ 下载PDF文件时网络错误: {str(e)}")
            
        except Exception as e:
            print(f"❌ 处理PDF文件时出错: {str(e)}")
            self.logger.error(f"处理PDF文件出错: {str(e)}")
            self.update_download_stats("failed_downloads")
            import traceback
            traceback.print_exc()
    
    def validate_download_url(self, url):
        """验证下载URL的安全性"""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            
            # 允许HTTP/HTTPS协议和本地文件协议（用于测试）
            if parsed.scheme not in ['http', 'https', 'file']:
                print(f"❌ 不支持的协议: {parsed.scheme}")
                return False
            
            # 对于file协议，直接返回True（本地文件测试）
            if parsed.scheme == 'file':
                print(f"🔍 检测到本地文件协议，允许访问: {url}")
                return True
            
            # 验证主机名（可选，可以根据需要配置允许的主机）
            allowed_hosts = ['localhost', '127.0.0.1', '172.18.122.8']  # 添加项目相关的主机
            if parsed.hostname and parsed.hostname not in allowed_hosts:
                # 允许私网地址
                if not (parsed.hostname.startswith(('192.168.', '10.', '172.')) or 
                       'localhost' in parsed.hostname):
                    print(f"⚠️ 主机名未在允许列表中: {parsed.hostname}")
                    # 暂时允许，但记录警告
            
            return True
            
        except Exception as e:
            print(f"❌ 验证URL时出错: {str(e)}")
            return False
    
    def decode_filename(self, filename):
        """安全解码文件名，处理中文字符"""
        try:
            print(f"🔤 开始解码文件名: {repr(filename)} (类型: {type(filename)})")
            
            # 如果文件名已经是Unicode字符串，直接返回
            if isinstance(filename, str):
                # 尝试URL解码（如果是URL编码的）
                try:
                    decoded = unquote(filename, encoding='utf-8')
                    if decoded != filename:
                        print(f"✅ URL解码成功: {filename} -> {decoded}")
                        if hasattr(self, 'logger'):
                            self.logger.info(f"URL解码文件名: {filename} -> {decoded}")
                        return decoded
                    else:
                        # 如果URL解码没有变化，说明不是URL编码，直接返回
                        print(f"✅ 文件名已是UTF-8格式: {filename}")
                        return filename
                except Exception as e:
                    print(f"⚠️ URL解码失败，使用原始文件名: {str(e)}")
                    return filename
            
            # 如果是字节串，尝试解码
            if isinstance(filename, bytes):
                print(f"🔄 字节串解码: {repr(filename)}")
                decoded = filename.decode('utf-8', errors='replace')
                print(f"✅ 字节串解码成功: {decoded}")
                return decoded
            
            # 其他类型转为字符串
            str_filename = str(filename)
            print(f"✅ 转换为字符串: {str_filename}")
            return str_filename
            
        except Exception as e:
            print(f"❌ 文件名解码失败: {str(e)}")
            if hasattr(self, 'logger'):
                self.logger.error(f"文件名解码失败: {str(e)}")
            # 返回安全的默认文件名
            return "document.pdf"
    
    def sanitize_filename(self, filename):
        """清理文件名，确保在文件系统中安全"""
        try:
            print(f"🔧 开始清理文件名: {repr(filename)}")
            
            # 解码文件名
            decoded_filename = self.decode_filename(filename)
            print(f"🔤 解码后文件名: {decoded_filename}")
            
            # 移除或替换不安全的字符
            # Windows文件名不能包含: < > : " | ? * \ /
            # 同时处理其他可能有问题的字符
            unsafe_chars = r'[<>:"|?*\\\/\x00-\x1f\x7f]'
            safe_filename = re.sub(unsafe_chars, '_', decoded_filename)
            
            # 移除前后空格和点（Windows不允许文件名以点结尾）
            safe_filename = safe_filename.strip(' .')
            
            # 移除连续的下划线（美化）
            safe_filename = re.sub(r'_{2,}', '_', safe_filename)
            
            # 确保文件名不为空
            if not safe_filename or safe_filename == '.pdf' or safe_filename == '_':
                safe_filename = "document.pdf"
                print(f"⚠️ 文件名为空或无效，使用默认名称: {safe_filename}")
            
            # 确保有.pdf扩展名
            if not safe_filename.lower().endswith('.pdf'):
                # 如果原文件名没有扩展名，添加.pdf
                if '.' not in safe_filename:
                    safe_filename += '.pdf'
                    print(f"📎 添加PDF扩展名: {safe_filename}")
                else:
                    # 如果有其他扩展名，替换为.pdf
                    name_part = os.path.splitext(safe_filename)[0]
                    safe_filename = name_part + '.pdf'
                    print(f"📎 替换为PDF扩展名: {safe_filename}")
            
            # 限制文件名长度（Windows路径限制）
            # 考虑中文字符可能占用更多字节
            max_length = 180  # 减少最大长度，为中文字符预留空间
            if len(safe_filename) > max_length:
                name_part = safe_filename[:-4]  # 移除.pdf
                safe_filename = name_part[:max_length-4] + '.pdf'  # 保留.pdf
                print(f"✂️ 截断长文件名: {safe_filename}")
            
            # 验证最终文件名
            if not safe_filename or safe_filename == '.pdf':
                safe_filename = "document.pdf"
                print(f"⚠️ 最终验证失败，使用默认名称: {safe_filename}")
            
            print(f"✅ 文件名清理完成: {filename} -> {safe_filename}")
            if hasattr(self, 'logger'):
                self.logger.info(f"文件名清理: {filename} -> {safe_filename}")
            
            return safe_filename
            
        except Exception as e:
            print(f"❌ 文件名清理失败: {str(e)}")
            if hasattr(self, 'logger'):
                self.logger.error(f"文件名清理失败: {str(e)}")
            import traceback
            traceback.print_exc()
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
                self.logger.info(f"从URL提取文件名: {url} -> {filename}")
                return filename
            
            return None
            
        except Exception as e:
            self.logger.error(f"从URL提取文件名失败: {str(e)}")
            return None
    
    def validate_file_type(self, filename):
        """验证文件类型"""
        try:
            # 清理并解码文件名
            clean_filename = self.sanitize_filename(filename)
            allowed_extensions = ['.pdf']
            file_ext = os.path.splitext(clean_filename)[1].lower()
            
            is_valid = file_ext in allowed_extensions
            if not is_valid:
                self.logger.warning(f"无效的文件类型: {file_ext}, 文件名: {clean_filename}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"文件类型验证失败: {str(e)}")
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
                
                from src.ui.widgets.pdf_viewer_widget import PDFPreviewDialog
                print("✅ 成功导入PDF查看器组件")
                
                # 使用QTimer确保在主线程中打开PDF查看器
                def show_pdf_in_main_thread():
                    try:
                        # 获取当前活动的QApplication实例
                        app = QApplication.instance()
                        if not app:
                            print("❌ 没有找到QApplication实例")
                            self._fallback_open_pdf(file_path)
                            return
                        
                        # 创建并显示PDF查看器对话框
                        viewer = PDFPreviewDialog(file_path, "PDF预览", None)
                        viewer.show()
                        print(f"✅ PDF弹窗查看器已显示: {file_path}")
                        
                    except Exception as e:
                        print(f"❌ 显示PDF查看器失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        # 如果弹窗失败，尝试使用系统默认程序
                        self._fallback_open_pdf(file_path)
                
                # 使用QTimer.singleShot在主线程中执行
                QTimer.singleShot(0, show_pdf_in_main_thread)
                
                print(f"✅ PDF查看器已安排在主线程中打开")
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
            print("API服务器启动中，监听8800端口...")
            print("CORS已启用，允许来自任何地址的跨域请求")
            from werkzeug.serving import make_server
            self.server = make_server('0.0.0.0', 8800, self.app, threaded=True)
            print(f"✅ API服务器已在端口 8800 启动")
            self.server.serve_forever()
        except Exception as e:
            print(f"API服务器启动失败: {str(e)}")
    
    def stop(self):
        """停止API服务器"""
        if hasattr(self, 'server'):
            print("🛑 正在停止API服务器...")
            self.server.shutdown()
            print("✅ API服务器已停止")

    def extract_filename_from_content_disposition(self, content_disposition):
        """从Content-Disposition头中提取文件名"""
        try:
            import re
            from urllib.parse import unquote
            
            # 尝试匹配 filename*=UTF-8''encoded_filename (RFC 5987)
            rfc5987_match = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition)
            if rfc5987_match:
                encoded_filename = rfc5987_match.group(1)
                decoded_filename = unquote(encoded_filename, encoding='utf-8')
                self.logger.info(f"从Content-Disposition提取文件名(RFC5987): {decoded_filename}")
                return decoded_filename
            
            # 尝试匹配 filename="filename" 或 filename=filename
            filename_match = re.search(r'filename="?([^";]+)"?', content_disposition)
            if filename_match:
                filename = filename_match.group(1)
                # 尝试解码（可能是URL编码或其他编码）
                try:
                    decoded_filename = unquote(filename, encoding='utf-8')
                    self.logger.info(f"从Content-Disposition提取文件名(标准): {decoded_filename}")
                    return decoded_filename
                except:
                    self.logger.info(f"从Content-Disposition提取文件名(原始): {filename}")
                    return filename
            
            self.logger.warning(f"无法从Content-Disposition提取文件名: {content_disposition}")
            return None
            
        except Exception as e:
            self.logger.error(f"解析Content-Disposition失败: {str(e)}")
            return None


class FullscreenBrowser(QMainWindow):
    def __init__(self, start_api=True):
        super().__init__()
        self.api_server = None
        self.api_thread = None
        self.desktop_manager_process = None
        self.process_monitor = None
        self.transition_screen = None
        # 默认情况下允许关闭desktop_manager
        self.should_close_desktop_manager = True
        self.init_ui()
        # 只有在独立运行时才启动API服务器
        if start_api:
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
            # 连接关闭全屏信号
            self.api_server.close_fullscreen_signal.connect(self.close_fullscreen)
            # 连接打开数字孪生平台信号
            self.api_server.open_digital_twin_signal.connect(self.open_digital_twin_platform)
            
            self.api_thread = threading.Thread(target=self.api_server.run, daemon=True)
            self.api_thread.start()
            print("API服务器线程已启动")
        except Exception as e:
            print(f"启动API服务器时出错: {str(e)}")
    
    def cleanup_json_files(self):
        """清理JSON文件"""
        try:
            print("🧹 开始清理JSON文件...")
            print(f"   当前工作目录: {os.getcwd()}")
            
            json_files = [
                'received_data.json',
                'received_tasks.json'
            ]
            
            deleted_files = []
            
            # 检查并删除主要JSON文件
            for file_path in json_files:
                full_path = os.path.abspath(file_path)
                print(f"🔍 检查文件: {full_path}")
                
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                        print(f"✅ 已删除JSON文件: {file_path}")
                    except Exception as e:
                        print(f"❌ 删除文件 {file_path} 失败: {str(e)}")
                else:
                    print(f"⚪ 文件不存在: {file_path}")
            
            # 清理备份文件（.notified_* 结尾的文件）
            current_dir = os.getcwd()
            print(f"🔍 扫描备份文件目录: {current_dir}")
            
            backup_files = []
            try:
                for filename in os.listdir(current_dir):
                    if filename.startswith('received_tasks.json.notified_'):
                        backup_files.append(filename)
                
                print(f"🔍 找到 {len(backup_files)} 个备份文件")
                
                for filename in backup_files:
                    try:
                        backup_path = os.path.join(current_dir, filename)
                        os.remove(backup_path)
                        deleted_files.append(filename)
                        print(f"✅ 已删除备份文件: {filename}")
                    except Exception as e:
                        print(f"❌ 删除备份文件 {filename} 失败: {str(e)}")
                        
            except Exception as e:
                print(f"❌ 扫描备份文件时出错: {str(e)}")
            
            if deleted_files:
                print(f"🧹 JSON文件清理完成，共删除 {len(deleted_files)} 个文件:")
                for file in deleted_files:
                    print(f"   - {file}")
            else:
                print("🧹 没有找到需要清理的JSON文件")
                
        except Exception as e:
            print(f"❌ 清理JSON文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_desktop_manager_ended(self):
        """当desktop_manager进程结束时的处理"""
        print("🔔 检测到desktop_manager进程已结束，开始清理JSON文件...")
        self.cleanup_json_files()
        
        # 停止进程监控
        if self.process_monitor:
            self.process_monitor.stop()
            self.process_monitor = None
    
    def open_digital_twin_platform(self, url):
        """打开数字孪生平台（线程安全）"""
        print(f"🚀 准备打开数字孪生平台: {url}")
        # 使用QTimer.singleShot确保在主线程中执行UI操作
        QTimer.singleShot(0, lambda: self._open_digital_twin_platform_impl(url))
    
    def _open_digital_twin_platform_impl(self, url):
        """实际执行打开数字孪生平台的操作"""
        try:
            print(f"🌐 正在加载数字孪生平台网页: {url}")
            
            # 确保URL有协议前缀
            if not url.startswith(('http://', 'https://')):
                if url.startswith(('192.168.', '10.', '172.', '127.0.0.1', 'localhost')):
                    url = f"http://{url}"
                else:
                    url = f"https://{url}"
            
            # 加载数字孪生平台网页
            self.browser.load(QUrl(url))
            
            # 确保窗口处于全屏状态
            if not self.isFullScreen():
                self.showFullScreen()
            
            # 更新窗口标题
            self.setWindowTitle(f"数字孪生平台 - {url} | API: 8800端口")
            
            print(f"✅ 数字孪生平台已加载: {url}")
            print("🔄 当前网页已切换到数字孪生平台")
            
        except Exception as e:
            print(f"❌ 打开数字孪生平台时出错: {str(e)}")



    def close_fullscreen(self):
        """关闭全屏模式（线程安全）"""
        # 使用QTimer.singleShot确保在主线程中执行UI操作
        QTimer.singleShot(0, self._show_transition_screen)
    
    def _show_transition_screen(self):
        """显示过渡页面"""
        # 先隐藏当前全屏浏览器窗口
        self.hide()
        
        # 创建新的过渡页面实例（不再使用，改为独立过渡）
        # self.transition_screen = TransitionScreen("正在关闭网页，准备启动桌面管理器...", 3000)
        
        # 使用QTimer异步显示过渡页面，避免阻塞
        QTimer.singleShot(0, self._show_transition_screen_async)
        
    def _show_transition_screen_async(self):
        """异步显示过渡页面"""
        print("🚀 正在启动独立过渡页面进程...")
        
        # 启动独立的过渡页面进程
        success = self._start_independent_transition()
        
        if success:
            print("✅ 独立过渡页面进程启动成功，等待过渡页面完全显示...")
            # 增加等待时间，确保过渡页面完全启动并显示
            # 增加到2500ms，给过渡页面足够的启动和显示时间
            QTimer.singleShot(2500, self._close_after_transition_started)
        else:
            print("❌ 过渡页面启动失败，直接启动桌面管理器...")
            # 如果过渡页面启动失败，直接启动桌面管理器
            self.start_desktop_manager()
            QTimer.singleShot(100, self.close)
    
    def _close_after_transition_started(self):
        """在过渡页面启动后关闭浏览器"""
        print("🔄 过渡页面已完全启动，正在关闭浏览器应用...")
        self.should_close_desktop_manager = False  # 不关闭desktop_manager，因为还没启动
        self.close()
    
    def _start_independent_transition(self):
        """启动独立的过渡页面进程（包含桌面图标备份）"""
        try:
            # 准备启动增强过渡页面的参数
            message = "正在打开云桌面..."
            duration = "5000"  # 增加持续时间，因为需要执行图标备份
            
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 查找增强过渡页面脚本（新的路径结构）
            script_paths = [
                os.path.join(current_dir, "src", "ui", "screens", "enhanced_transition_screen.py"),
                os.path.join(current_dir, "src", "ui", "screens", "independent_transition.py"),
                # 兼容旧路径
                os.path.join(os.path.dirname(__file__), "enhanced_transition_screen.py"),
                "enhanced_transition_screen.py",
                os.path.join(os.path.dirname(__file__), "independent_transition.py"),
                "independent_transition.py"
            ]
            
            script_path = None
            script_type = "enhanced"  # enhanced 或 basic
            
            print("🔍 正在查找过渡页面脚本...")
            for path in script_paths:
                print(f"  检查路径: {path}")
                if os.path.exists(path):
                    script_path = path
                    if "independent_transition" in path:
                        script_type = "basic"
                    print(f"  ✅ 找到文件!")
                    break
                else:
                    print(f"  ❌ 文件不存在")
            
            if not script_path:
                print("❌ 错误：找不到任何过渡页面文件，将直接启动桌面管理器")
                # 如果找不到过渡页面文件，直接启动桌面管理器作为最后的备用方案
                self.start_desktop_manager()
                return False
            
            print(f"📁 使用过渡页面脚本: {script_path} (类型: {script_type})")
            
            # 启动过渡页面进程
            process = None
            cmd_args = []
            
            if sys.platform == "win32":
                # Windows平台使用pythonw运行，不显示终端窗口
                python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                if not os.path.exists(python_executable):
                    python_executable = sys.executable
                    creationflags = subprocess.CREATE_NO_WINDOW
                else:
                    creationflags = 0
                
                # 根据脚本类型使用不同的参数
                if script_type == "enhanced":
                    cmd_args = [python_executable, script_path, message, duration, "--backup"]
                else:
                    cmd_args = [python_executable, script_path, message, duration]
                
                print(f"📝 启动命令: {' '.join(cmd_args)}")
                
                process = subprocess.Popen(cmd_args, creationflags=creationflags)
                
                if script_type == "enhanced":
                    print("🚀 增强过渡页面进程已启动，将执行桌面文件备份并启动桌面管理器")
                else:
                    print("🚀 基础过渡页面进程已启动，将启动桌面管理器")
            else:
                # 非Windows平台
                if script_type == "enhanced":
                    cmd_args = [sys.executable, script_path, message, duration, "--backup"]
                else:
                    cmd_args = [sys.executable, script_path, message, duration]
                
                print(f"📝 启动命令: {' '.join(cmd_args)}")
                
                process = subprocess.Popen(cmd_args)
                
                if script_type == "enhanced":
                    print("🚀 增强过渡页面进程已启动，将执行桌面文件备份并启动桌面管理器")
                else:
                    print("🚀 基础过渡页面进程已启动，将启动桌面管理器")
            
            # 验证进程是否成功启动
            if process:
                # 等待一小段时间，检查进程是否立即崩溃
                import time
                time.sleep(0.5)  # 增加等待时间到500ms
                
                if process.poll() is None:
                    print(f"✅ 过渡页面进程启动成功 (PID: {process.pid})，过渡页面将负责启动桌面管理器")
                    # 再等待一点，确保过渡页面窗口已经显示
                    time.sleep(0.5)
                    return True
                else:
                    print(f"❌ 过渡页面进程启动失败，进程立即退出 (返回码: {process.poll()})")
                    # 进程启动失败，作为备用方案直接启动桌面管理器
                    print("⚠️ 使用备用方案：直接启动桌面管理器")
                    self.start_desktop_manager()
                    return False
            else:
                print("❌ 无法创建过渡页面进程")
                # 无法创建进程，作为备用方案直接启动桌面管理器
                print("⚠️ 使用备用方案：直接启动桌面管理器")
                self.start_desktop_manager()
                return False
            
        except Exception as e:
            print(f"❌ 启动增强过渡页面时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 如果启动失败，作为备用方案直接启动desktop_manager
            print("⚠️ 使用备用方案：直接启动桌面管理器")
            self.start_desktop_manager()
            return False
    
    def _on_transition_finished(self):
        """过渡页面完成后的回调（现在不再使用）"""
        # 这个方法现在不再使用，因为过渡页面是独立运行的
        pass
    
    def _close_fullscreen_impl(self):
        """实际执行关闭全屏的操作 - 改为直接关闭程序"""
        print("正在关闭网页程序...")
        # 直接关闭程序而不是窗口化
        self._close_application()
            
    def _force_close_impl(self):
        """强制关闭实现"""
        print("强制关闭网页...")
        self._close_application()
        
    def _close_application(self):
        """关闭应用程序"""
        print("正在关闭应用程序...")
        
        # desktop_manager已经在过渡页面前启动，这里不需要再启动
        # 只需要标记desktop_manager不应该被关闭
        self.should_close_desktop_manager = False
        
        # 关闭当前应用程序
        self.close()
    
    def _exit_application(self):
        """退出应用程序"""
        print("正在退出应用程序...")
        # 退出时不启动desktop_manager，并且允许关闭已有的desktop_manager
        self.should_close_desktop_manager = True
        self.close()
    
    def on_load_finished(self, success):
        """页面加载完成后的回调"""
        if success:
            print("网页加载成功！")
            print("API服务器地址: http://localhost:8800")
            print("上传JSON数据: POST http://localhost:8800/upload")
            print("检查API状态: GET http://localhost:8800/status")
            print("功能提示：")
            print("  📋 当接收到包含用户角色选择的JSON数据时，将自动退出全屏模式并启动desktop_manager")
            print("  🌐 当接收到包含'数字孪生平台系统访问地址'的JSON数据时，将自动切换到孪生平台网页")
            print("CORS支持已启用，任何地址的前端都可以发送跨域请求")
            print("键盘快捷键：")
            print("  ESC - 退出程序")
            print("  F11 - 切换全屏状态")
            print("  F5  - 刷新页面")
            print("  Ctrl+Q - 退出全屏并启动desktop_manager")
        else:
            print("网页加载失败，请检查localhost:3000是否可访问")
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # 按ESC键显示退出过渡页面
        if event.key() == Qt.Key_Escape:
            self._show_exit_transition()
        # 按F11切换全屏状态
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        # 按F5刷新页面
        elif event.key() == Qt.Key_F5:
            self.browser.reload()
        # 按Ctrl+Q退出全屏并启动desktop_manager
        elif event.key() == Qt.Key_Q and (event.modifiers() & Qt.ControlModifier):
            if self.isFullScreen():
                self.close_fullscreen()
            else:
                self.start_desktop_manager()
        else:
            super().keyPressEvent(event)
            
    def _show_exit_transition(self):
        """显示退出过渡页面"""
        # 先隐藏当前全屏浏览器窗口
        self.hide()
        
        # 创建新的过渡页面实例
        self.transition_screen = TransitionScreen("正在退出程序...", 2000)
        
        # 使用QTimer异步显示过渡页面，避免阻塞
        QTimer.singleShot(0, self._show_exit_transition_async)
        
    def _show_exit_transition_async(self):
        """异步显示退出过渡页面"""
        # 启动独立的退出过渡页面进程
        self._start_independent_exit_transition()
        
        # 立即关闭当前浏览器应用
        print("独立退出过渡页面已启动，正在关闭浏览器应用...")
        self.should_close_desktop_manager = True  # 退出时允许关闭已有的desktop_manager
        QTimer.singleShot(100, self.close)  # 延迟100ms关闭浏览器应用
        
    def _start_independent_exit_transition(self):
        """启动独立的退出过渡页面进程"""
        try:
            # 准备启动独立过渡页面的参数
            message = "正在退出程序..."
            duration = "2000"
            
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 查找独立过渡页面脚本（新的路径结构）
            script_paths = [
                os.path.join(current_dir, "src", "ui", "screens", "independent_transition.py"),
                os.path.join(current_dir, "src", "ui", "screens", "enhanced_transition_screen.py"),
                # 兼容旧路径
                os.path.join(os.path.dirname(__file__), "independent_transition.py"),
                "independent_transition.py",
                os.path.join(os.path.dirname(__file__), "enhanced_transition_screen.py"),
                "enhanced_transition_screen.py"
            ]
            
            script_path = None
            for path in script_paths:
                if os.path.exists(path):
                    script_path = path
                    break
            
            if not script_path:
                print("错误：找不到过渡页面文件")
                return
            
            # 启动独立过渡页面进程（退出模式不启动desktop_manager）
            if sys.platform == "win32":
                # Windows平台使用pythonw运行，不显示终端窗口
                python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                if not os.path.exists(python_executable):
                    python_executable = sys.executable
                    creationflags = subprocess.CREATE_NO_WINDOW
                else:
                    creationflags = 0
                
                subprocess.Popen([
                    python_executable, script_path, message, duration, "--exit-mode"
                ], creationflags=creationflags)
            else:
                # 非Windows平台
                subprocess.Popen([
                    sys.executable, script_path, message, duration, "--exit-mode"
                ])
            
            print("独立退出过渡页面进程已启动")
            
        except Exception as e:
            print(f"启动独立退出过渡页面时出错: {str(e)}")
    
    def _on_exit_transition_finished(self):
        """退出过渡页面完成后的回调（现在不再使用）"""
        # 这个方法现在不再使用，因为过渡页面是独立运行的
        pass
        
    def start_desktop_manager(self):
        """启动desktop_manager程序"""
        try:
            print("正在启动 desktop_manager...")
            
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            main_py_path = os.path.join(current_dir, "main.py")
            
            # 优先使用新的 main.py 启动方式
            if os.path.exists(main_py_path):
                print("🚀 使用新的main.py启动desktop_manager...")
                
                if sys.platform == "win32":
                    # Windows平台使用pythonw运行，不显示终端窗口
                    python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                    if not os.path.exists(python_executable):
                        python_executable = sys.executable
                        creationflags = subprocess.CREATE_NO_WINDOW
                    else:
                        creationflags = 0
                    
                    # 通过main.py启动desktop_manager，传递auto-open-tasks参数
                    self.desktop_manager_process = subprocess.Popen([
                        python_executable, main_py_path, "desktop", "--auto-open-tasks"
                    ], creationflags=creationflags)
                else:
                    # 非Windows平台
                    self.desktop_manager_process = subprocess.Popen([
                        sys.executable, main_py_path, "desktop", "--auto-open-tasks"
                    ])
                
                print(f"desktop_manager 已启动，进程ID: {self.desktop_manager_process.pid}")
                print("✅ 通过main.py启动desktop_manager成功")
                
                # 启动进程监控
                self.start_process_monitor()
                return
            
            # 备用方案：查找旧的desktop_manager程序路径
            desktop_manager_paths = [
                # 新的路径结构
                os.path.join(current_dir, "src", "desktop", "desktop_manager.py"),
                # 旧的路径结构（兼容性）
                "desktop_manager.py",
                "desktop_manager.exe", 
                "./desktop_manager.py",
                "./desktop_manager.exe",
                os.path.join(os.path.dirname(__file__), "desktop_manager.py"),
                os.path.join(os.path.dirname(__file__), "desktop_manager.exe"),
                os.path.join(os.getcwd(), "desktop_manager.py"),
                os.path.join(os.getcwd(), "desktop_manager.exe")
            ]
            
            desktop_manager_path = None
            for path in desktop_manager_paths:
                if os.path.exists(path):
                    desktop_manager_path = path
                    break
            
            if not desktop_manager_path:
                print("错误：找不到 desktop_manager 程序文件")
                print("提示：请确保main.py存在或desktop_manager.py在正确位置")
                return
            
            # 根据文件类型选择启动方式
            if desktop_manager_path.endswith('.py'):
                # Python文件，使用python运行，不显示终端窗口
                if sys.platform == "win32":
                    # Windows平台使用pythonw运行，不显示终端窗口
                    python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                    if not os.path.exists(python_executable):
                        # 如果找不到pythonw，则使用python但隐藏窗口
                        python_executable = sys.executable
                        creationflags = subprocess.CREATE_NO_WINDOW
                    else:
                        creationflags = 0
                    
                    # 启动desktop_manager并传递自动打开任务对话框的参数
                    self.desktop_manager_process = subprocess.Popen([
                        python_executable, desktop_manager_path, "--auto-open-tasks"
                    ], creationflags=creationflags)
                else:
                    # 非Windows平台
                    self.desktop_manager_process = subprocess.Popen([
                        sys.executable, desktop_manager_path, "--auto-open-tasks"
                    ])
            else:
                # 可执行文件，直接运行，不显示终端窗口
                if sys.platform == "win32":
                    # Windows平台隐藏窗口，传递自动打开任务对话框的参数
                    self.desktop_manager_process = subprocess.Popen([
                        desktop_manager_path, "--auto-open-tasks"
                    ], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.desktop_manager_process = subprocess.Popen([
                        desktop_manager_path, "--auto-open-tasks"
                    ])
            
            print(f"desktop_manager 已启动，进程ID: {self.desktop_manager_process.pid}")
            print("✅ 已传递 --auto-open-tasks 参数，desktop_manager 将自动打开任务提交对话框")
            
            # 启动进程监控
            self.start_process_monitor()
            
        except FileNotFoundError:
            print("错误：找不到 desktop_manager 程序或Python解释器")
        except Exception as e:
            print(f"启动 desktop_manager 时出错: {str(e)}")
    
    def start_process_monitor(self):
        """启动进程监控"""
        if self.desktop_manager_process and self.desktop_manager_process.poll() is None:
            # 进程仍在运行，启动监控
            self.process_monitor = ProcessMonitor(self.desktop_manager_process)
            self.process_monitor.process_ended.connect(self.on_desktop_manager_ended)
            self.process_monitor.start()
            print("🔍 已启动desktop_manager进程监控，将在进程结束时自动清理JSON文件")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        print("正在关闭应用程序...")
        
        # 停止进程监控
        if self.process_monitor:
            print("正在停止进程监控...")
            self.process_monitor.stop()
            self.process_monitor.quit()
            self.process_monitor.wait(3000)  # 等待最多3秒
            self.process_monitor = None
        
        # 只有在明确需要关闭desktop_manager时才关闭它
        if hasattr(self, 'should_close_desktop_manager') and self.should_close_desktop_manager:
            if self.desktop_manager_process and self.desktop_manager_process.poll() is None:
                try:
                    print("正在关闭 desktop_manager 进程...")
                    self.desktop_manager_process.terminate()
                    # 等待进程结束，最多等待3秒
                    try:
                        self.desktop_manager_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        # 如果进程没有正常结束，强制杀死
                        self.desktop_manager_process.kill()
                    print("desktop_manager 进程已关闭")
                    
                    # 如果手动关闭了desktop_manager，也清理JSON文件
                    self.cleanup_json_files()
                    
                except Exception as e:
                    print(f"关闭 desktop_manager 进程时出错: {str(e)}")
        else:
            print("desktop_manager 进程将继续运行...")
        
        event.accept()

def main():
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序名称
    app.setApplicationName("全屏浏览器")
    
    # 创建并显示主窗口
    window = FullscreenBrowser()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
