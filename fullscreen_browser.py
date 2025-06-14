import sys
import json
import threading
import subprocess
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from transition_screen import TransitionScreen

# 禁用Flask的默认日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class APIServer(QObject):
    # 定义信号用于跨线程通信
    close_fullscreen_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = Flask(__name__)
        
        # 配置CORS，允许从localhost:3000访问
        CORS(self.app, resources={
            r"/upload": {
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["POST"],
                "allow_headers": ["Content-Type"]
            },
            r"/status": {
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["GET"]
            }
        })
        
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
                
                # 检查是否是特定的用户角色选择数据
                if self.is_role_selection_data(json_data):
                    print("检测到角色选择数据，准备关闭全屏网页...")
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
    
    def is_role_selection_data(self, data):
        """检查是否是角色选择数据"""
        required_fields = ['user', 'selectedRole', 'timestamp', 'action']
        
        # 检查所有必需字段是否存在
        if not all(field in data for field in required_fields):
            return False
        
        # 检查action字段是否为role_selection
        if data.get('action') != 'role_selection':
            return False
        
        # 检查user字段是否包含必要的子字段
        user_data = data.get('user', {})
        user_required_fields = ['id', 'username', 'role', 'type', 'status']
        if not all(field in user_data for field in user_required_fields):
            return False
        
        # 检查selectedRole字段是否包含必要的子字段
        role_data = data.get('selectedRole', {})
        role_required_fields = ['value', 'label', 'description']
        if not all(field in role_data for field in role_required_fields):
            return False
        
        print(f"角色选择数据验证通过: 用户={user_data.get('username')}, 角色={role_data.get('label')}")
        return True
    
    def run(self):
        """运行API服务器"""
        try:
            print("API服务器启动中，监听8800端口...")
            print("CORS已启用，允许来自localhost:3000的跨域请求")
            self.app.run(host='0.0.0.0', port=8800, debug=False, threaded=True)
        except Exception as e:
            print(f"API服务器启动失败: {str(e)}")


class FullscreenBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_server = None
        self.api_thread = None
        self.desktop_manager_process = None
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
        self.browser.load(QUrl("http://localhost:3000"))
        
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
            
            self.api_thread = threading.Thread(target=self.api_server.run, daemon=True)
            self.api_thread.start()
            print("API服务器线程已启动")
        except Exception as e:
            print(f"启动API服务器时出错: {str(e)}")
    
    def close_fullscreen(self):
        """关闭全屏模式（线程安全）"""
        # 使用QTimer.singleShot确保在主线程中执行UI操作
        QTimer.singleShot(0, self._show_transition_screen)
    
    def _show_transition_screen(self):
        """显示过渡页面"""
        # 先隐藏当前全屏浏览器窗口
        self.hide()
        
        # 创建新的过渡页面实例
        self.transition_screen = TransitionScreen("正在关闭网页...", 3000)
        
        # 使用QTimer异步显示过渡页面，避免阻塞
        QTimer.singleShot(0, self._show_transition_screen_async)
        
    def _show_transition_screen_async(self):
        """异步显示过渡页面"""
        # 显示过渡页面并开始动画
        self.transition_screen.show_transition()
        # 过渡完成后关闭程序
        QTimer.singleShot(100, self._close_application)
        
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
        
        # 启动desktop_manager
        self.start_desktop_manager()
        
        # 标记desktop_manager不应该被关闭
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
            print("提示：当接收到包含用户角色选择的JSON数据时，将自动退出全屏模式并启动desktop_manager")
            print("CORS支持已启用，前端可以正常发送跨域请求")
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
        # 显示过渡页面并开始动画
        self.transition_screen.show_transition()
        # 过渡完成后退出程序
        QTimer.singleShot(100, self._exit_application)
        
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
                    
                    self.desktop_manager_process = subprocess.Popen([
                        python_executable, desktop_manager_path
                    ], creationflags=creationflags)
                else:
                    # 非Windows平台
                    self.desktop_manager_process = subprocess.Popen([
                        sys.executable, desktop_manager_path
                    ])
            else:
                # 可执行文件，直接运行，不显示终端窗口
                if sys.platform == "win32":
                    # Windows平台隐藏窗口
                    self.desktop_manager_process = subprocess.Popen([
                        desktop_manager_path
                    ], creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.desktop_manager_process = subprocess.Popen([
                        desktop_manager_path
                    ])
            
            print(f"desktop_manager 已启动，进程ID: {self.desktop_manager_process.pid}")
            
        except FileNotFoundError:
            print("错误：找不到 desktop_manager 程序或Python解释器")
        except Exception as e:
            print(f"启动 desktop_manager 时出错: {str(e)}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        print("正在关闭应用程序...")
        
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
