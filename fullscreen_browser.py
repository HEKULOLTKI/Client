import sys
import json
import threading
import subprocess
import os
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QKeySequence
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from transition_screen import TransitionScreen

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
            }
        })
        
        # 存储接收到的任务数据
        self.received_tasks = []
        self.user_session_info = {}
        
        self.setup_routes()
        
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
    
    def run(self):
        """运行API服务器"""
        try:
            print("API服务器启动中，监听8800端口...")
            print("CORS已启用，允许来自任何地址的跨域请求")
            self.app.run(host='0.0.0.0', port=8800, debug=False, threaded=True)
        except Exception as e:
            print(f"API服务器启动失败: {str(e)}")


class FullscreenBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_server = None
        self.api_thread = None
        self.desktop_manager_process = None
        self.process_monitor = None
        self.transition_screen = None
        # 默认情况下允许关闭desktop_manager
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
        # 启动独立的过渡页面进程
        self._start_independent_transition()
        
        # 立即关闭当前浏览器应用
        print("独立过渡页面已启动，正在关闭浏览器应用...")
        self.should_close_desktop_manager = False  # 不关闭desktop_manager，因为还没启动
        QTimer.singleShot(100, self.close)  # 延迟100ms关闭浏览器应用
        
    def _start_independent_transition(self):
        """启动独立的过渡页面进程（包含桌面图标备份）"""
        try:
            # 准备启动增强过渡页面的参数
            message = "正在打开云桌面..."
            duration = "5000"  # 增加持续时间，因为需要执行图标备份
            
            # 查找增强过渡页面脚本
            script_path = os.path.join(os.path.dirname(__file__), "enhanced_transition_screen.py")
            if not os.path.exists(script_path):
                script_path = "enhanced_transition_screen.py"
            
            if not os.path.exists(script_path):
                print("错误：找不到 enhanced_transition_screen.py 文件，使用备用方案")
                # 使用原始过渡页面作为备用
                script_path = os.path.join(os.path.dirname(__file__), "independent_transition.py")
                if not os.path.exists(script_path):
                    script_path = "independent_transition.py"
                
                if not os.path.exists(script_path):
                    print("错误：找不到任何过渡页面文件")
                    self.start_desktop_manager()
                    return
                
                # 使用原始过渡页面
                if sys.platform == "win32":
                    python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                    if not os.path.exists(python_executable):
                        python_executable = sys.executable
                        creationflags = subprocess.CREATE_NO_WINDOW
                    else:
                        creationflags = 0
                    
                    subprocess.Popen([
                        python_executable, script_path, message, duration
                    ], creationflags=creationflags)
                else:
                    subprocess.Popen([
                        sys.executable, script_path, message, duration
                    ])
                
                print("启动了备用过渡页面进程")
                return
            
            # 启动增强过渡页面进程（包含桌面图标备份）
            if sys.platform == "win32":
                # Windows平台使用pythonw运行，不显示终端窗口
                python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                if not os.path.exists(python_executable):
                    python_executable = sys.executable
                    creationflags = subprocess.CREATE_NO_WINDOW
                else:
                    creationflags = 0
                
                subprocess.Popen([
                    python_executable, script_path, message, duration, "--backup"
                ], creationflags=creationflags)
            else:
                # 非Windows平台
                subprocess.Popen([
                    sys.executable, script_path, message, duration, "--backup"
                ])
            
            print("增强过渡页面进程已启动，将执行桌面文件备份")
            
        except Exception as e:
            print(f"启动增强过渡页面时出错: {str(e)}")
            # 如果启动失败，直接启动desktop_manager
            self.start_desktop_manager()
    
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
            
            # 查找独立过渡页面脚本
            script_path = os.path.join(os.path.dirname(__file__), "independent_transition.py")
            if not os.path.exists(script_path):
                script_path = "independent_transition.py"
            
            if not os.path.exists(script_path):
                print("错误：找不到 independent_transition.py 文件")
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
            
            # 查找desktop_manager程序
            desktop_manager_paths = [
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
