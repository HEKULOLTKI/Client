#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的智能桌面助手应用程序
整合了全屏浏览器、桌面管理器、AI聊天、桌面宠物等所有功能
"""

import sys
import os
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSystemTrayIcon, 
                             QMenu, QAction, QMessageBox, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QIcon, QFont

# 导入所有模块
from src.browser.fullscreen_browser import FullscreenBrowser, APIServer
from src.desktop.desktop_manager import DesktopManager
from src.ui.widgets.pet_widget import PetWidget
from src.ui.widgets.chat_widget import ChatWidget
from src.ui.widgets.online_chat_widget import OnlineChatWidget
from src.api.openai_api import OpenAIChat
from src.core import config
from src.ui.screens.transition_screen import TransitionScreen


class IntegratedApplication(QMainWindow):
    """统一的应用程序主窗口"""
    
    # 定义信号
    data_received = pyqtSignal(dict)  # 数据接收信号
    module_switch = pyqtSignal(str)   # 模块切换信号
    
    def __init__(self):
        super().__init__()
        self.current_module = None
        self.modules = {}
        self.api_server = None
        self.tray_icon = None
        
        # 初始化共享数据
        self.shared_data = {
            'user_info': {},
            'tasks': [],
            'role': None,
            'session': {}
        }
        
        # 初始化UI
        self.init_ui()
        
        # 初始化模块
        self.init_modules()
        
        # 设置系统托盘
        self.setup_system_tray()
        
        # 启动API服务器
        self.start_api_server()
        
        # 默认启动全屏浏览器模块
        self.switch_module('browser')
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("智能桌面助手")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建堆叠部件来管理不同模块
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # 隐藏主窗口（应用程序主要通过模块窗口和系统托盘运行）
        self.hide()
    
    def init_modules(self):
        """初始化所有模块"""
        print("🚀 正在初始化所有模块...")
        
        # 初始化OpenAI聊天
        self.openai_chat = OpenAIChat()
        
        # 创建占位部件（用于堆叠部件）
        placeholder = QLabel("智能桌面助手")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setFont(QFont("Microsoft YaHei", 24))
        self.stacked_widget.addWidget(placeholder)
        
        # 初始化各个模块（作为独立窗口）
        self.modules['browser'] = None  # 全屏浏览器将在需要时创建
        self.modules['desktop'] = None  # 桌面管理器将在需要时创建
        self.modules['pet'] = None      # 宠物将在需要时创建
        self.modules['chat'] = None     # 聊天将在需要时创建
        self.modules['online_chat'] = None  # 在线聊天将在需要时创建
        
        print("✅ 模块初始化完成")
    
    def start_api_server(self):
        """启动API服务器"""
        try:
            self.api_server = APIServer(self)
            self.api_server.close_fullscreen_signal.connect(self.on_fullscreen_close_requested)
            self.api_server.open_digital_twin_signal.connect(self.on_digital_twin_requested)
            
            # 在新线程中运行服务器
            import threading
            self.server_thread = threading.Thread(target=self.api_server.run, daemon=True)
            self.server_thread.start()
            
            print("✅ API服务器已启动")
        except Exception as e:
            print(f"❌ API服务器启动失败: {e}")
    
    def setup_system_tray(self):
        """设置系统托盘图标"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠️ 系统托盘不可用")
            return
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(config.APP_ICON))
        self.tray_icon.setToolTip("智能桌面助手")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 添加模块切换菜单
        browser_action = QAction("全屏浏览器", self)
        browser_action.triggered.connect(lambda: self.switch_module('browser'))
        tray_menu.addAction(browser_action)
        
        desktop_action = QAction("桌面管理器", self)
        desktop_action.triggered.connect(lambda: self.switch_module('desktop'))
        tray_menu.addAction(desktop_action)
        
        pet_action = QAction("桌面宠物", self)
        pet_action.triggered.connect(lambda: self.switch_module('pet'))
        tray_menu.addAction(pet_action)
        
        chat_action = QAction("AI聊天", self)
        chat_action.triggered.connect(lambda: self.switch_module('chat'))
        tray_menu.addAction(chat_action)
        
        tray_menu.addSeparator()
        
        # 添加显示/隐藏主窗口
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.toggle_main_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # 添加退出选项
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 双击托盘图标显示主窗口
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 显示欢迎通知
        self.tray_icon.showMessage(
            "智能桌面助手",
            "应用程序已启动，可以通过系统托盘访问所有功能",
            QSystemTrayIcon.Information,
            3000
        )
    
    def on_tray_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_main_window()
    
    def toggle_main_window(self):
        """切换主窗口显示/隐藏"""
        if self.isHidden():
            self.show()
            self.raise_()
            self.activateWindow()
        else:
            self.hide()
    
    def switch_module(self, module_name):
        """切换到指定模块"""
        print(f"🔄 切换到模块: {module_name}")
        
        # 关闭当前模块的独立窗口
        if self.current_module and self.current_module != module_name:
            self.close_current_module()
        
        # 启动新模块
        if module_name == 'browser':
            self.start_browser()
        elif module_name == 'desktop':
            self.start_desktop_manager()
        elif module_name == 'pet':
            self.start_pet()
        elif module_name == 'chat':
            self.start_chat()
        elif module_name == 'online_chat':
            self.start_online_chat()
        
        self.current_module = module_name
        self.module_switch.emit(module_name)
    
    def close_current_module(self):
        """关闭当前模块"""
        if self.current_module and self.current_module in self.modules:
            module = self.modules[self.current_module]
            if module and hasattr(module, 'close'):
                module.close()
    
    def start_browser(self):
        """启动全屏浏览器"""
        if not self.modules['browser']:
            # 创建浏览器实例但不启动其内部的API服务器
            self.modules['browser'] = FullscreenBrowser(start_api=False)
            
            # 连接信号
            if self.api_server:
                try:
                    self.api_server.close_fullscreen_signal.disconnect()
                except:
                    pass
                self.api_server.close_fullscreen_signal.connect(self.modules['browser'].close_fullscreen)
                
                try:
                    self.api_server.open_digital_twin_signal.disconnect()
                except:
                    pass
                self.api_server.open_digital_twin_signal.connect(self.modules['browser'].open_digital_twin_platform)
        
        self.modules['browser'].show()
        self.modules['browser'].raise_()
        self.modules['browser'].activateWindow()
    
    def start_desktop_manager(self):
        """启动桌面管理器"""
        if not self.modules['desktop']:
            self.modules['desktop'] = DesktopManager()
            # 传递共享数据
            if self.shared_data['tasks']:
                self.modules['desktop'].received_tasks = self.shared_data['tasks']
                self.modules['desktop'].user_session_info = self.shared_data['user_info']
                self.modules['desktop'].update_role_display()
                self.modules['desktop'].update_task_display()
        
        self.modules['desktop'].show()
        self.modules['desktop'].raise_()
    
    def start_pet(self):
        """启动桌面宠物"""
        if not self.modules['pet']:
            self.modules['pet'] = PetWidget()
            self.modules['pet'].doubleClicked.connect(lambda: self.switch_module('chat'))
        
        self.modules['pet'].show()
        self.modules['pet'].raise_()
    
    def start_chat(self):
        """启动AI聊天"""
        if not self.modules['chat']:
            self.modules['chat'] = ChatWidget(self.openai_chat)
        
        self.modules['chat'].show()
        self.modules['chat'].raise_()
        self.modules['chat'].activateWindow()
    
    def start_online_chat(self):
        """启动在线聊天"""
        if not self.modules['online_chat']:
            try:
                self.modules['online_chat'] = OnlineChatWidget()
            except Exception as e:
                print(f"❌ 无法启动在线聊天: {e}")
                QMessageBox.warning(self, "错误", f"无法启动在线聊天: {str(e)}")
                return
        
        self.modules['online_chat'].show()
        self.modules['online_chat'].raise_()
        self.modules['online_chat'].activateWindow()
    
    @pyqtSlot()
    def on_fullscreen_close_requested(self):
        """处理全屏关闭请求"""
        print("📱 收到全屏关闭请求")
        
        # 提取并保存数据
        if self.api_server:
            self.shared_data['tasks'] = self.api_server.received_tasks
            self.shared_data['user_info'] = self.api_server.user_session_info
        
        # 显示过渡动画
        transition = TransitionScreen("正在加载桌面管理器...", 2000)
        transition.show()
        
        # 延迟切换到桌面管理器
        QTimer.singleShot(500, lambda: self.switch_module('desktop'))
    
    @pyqtSlot(str)
    def on_digital_twin_requested(self, url):
        """处理数字孪生平台请求"""
        print(f"🌐 收到数字孪生平台请求: {url}")
        
        # 如果浏览器模块存在，让它打开URL
        if self.modules['browser']:
            self.modules['browser'].open_digital_twin_platform(url)
    
    def update_shared_data(self, data):
        """更新共享数据"""
        if 'tasks' in data:
            self.shared_data['tasks'] = data['tasks']
        if 'user_info' in data:
            self.shared_data['user_info'] = data['user_info']
        if 'role' in data:
            self.shared_data['role'] = data['role']
        
        # 通知数据接收
        self.data_received.emit(data)
        
        # 更新各模块的数据
        if self.modules['desktop']:
            self.modules['desktop'].received_tasks = self.shared_data['tasks']
            self.modules['desktop'].user_session_info = self.shared_data['user_info']
            self.modules['desktop'].update_role_display()
            self.modules['desktop'].update_task_display()
    
    def quit_application(self):
        """退出应用程序"""
        reply = QMessageBox.question(
            self, 
            '确认退出', 
            '确定要退出智能桌面助手吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print("👋 正在退出应用程序...")
            
            # 关闭所有模块
            for module_name, module in self.modules.items():
                if module and hasattr(module, 'close'):
                    try:
                        module.close()
                        print(f"✅ 已关闭模块: {module_name}")
                    except Exception as e:
                        print(f"❌ 关闭模块 {module_name} 时出错: {e}")
            
            # 停止API服务器
            if self.api_server and hasattr(self.api_server, 'stop'):
                try:
                    self.api_server.stop()
                    print("✅ API服务器已停止")
                except Exception as e:
                    print(f"❌ 停止API服务器时出错: {e}")
            
            # 隐藏托盘图标
            if self.tray_icon:
                self.tray_icon.hide()
            
            # 退出应用
            QApplication.quit()
    
    def closeEvent(self, event):
        """主窗口关闭事件"""
        # 不直接退出，而是隐藏到系统托盘
        event.ignore()
        self.hide()
        
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "智能桌面助手",
                "应用程序已最小化到系统托盘",
                QSystemTrayIcon.Information,
                2000
            )


def main():
    """主函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("智能桌面助手")
    app.setOrganizationName("YourCompany")
    
    # 设置应用程序图标
    if hasattr(config, 'APP_ICON') and os.path.exists(config.APP_ICON):
        app.setWindowIcon(QIcon(config.APP_ICON))
    
    # 设置全局字体
    font = QFont("Microsoft YaHei UI", 9)
    app.setFont(font)
    
    # 创建并显示主应用程序
    main_app = IntegratedApplication()
    
    # 处理命令行参数（如果需要直接启动某个模块）
    if len(sys.argv) > 1:
        module = sys.argv[1].lower()
        if module in ['browser', 'desktop', 'pet', 'chat', 'online_chat']:
            main_app.switch_module(module)
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 