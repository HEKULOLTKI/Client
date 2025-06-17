#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import threading
import time
import json
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QThread
from PyQt5.QtGui import QColor, QPainter, QPen, QFont
from transition_screen import TransitionScreen
from desktop_icon_manager import DesktopIconManager

def cleanup_json_files():
    """清理JSON文件"""
    try:
        json_files = [
            'received_data.json',
            'received_tasks.json'
        ]
        
        deleted_files = []
        for file_path in json_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    print(f"✅ 已删除JSON文件: {file_path}")
                except Exception as e:
                    print(f"❌ 删除文件 {file_path} 失败: {str(e)}")
        
        # 清理备份文件（.notified_* 结尾的文件）
        current_dir = os.getcwd()
        for filename in os.listdir(current_dir):
            if filename.startswith('received_tasks.json.notified_'):
                try:
                    backup_path = os.path.join(current_dir, filename)
                    os.remove(backup_path)
                    deleted_files.append(filename)
                    print(f"✅ 已删除备份文件: {filename}")
                except Exception as e:
                    print(f"❌ 删除备份文件 {filename} 失败: {str(e)}")
        
        if deleted_files:
            print(f"🧹 JSON文件清理完成，共删除 {len(deleted_files)} 个文件")
        else:
            print("🧹 没有找到需要清理的JSON文件")
            
    except Exception as e:
        print(f"❌ 清理JSON文件时出错: {str(e)}")

def monitor_process_and_cleanup(process):
    """监控进程并在结束时清理JSON文件"""
    try:
        print(f"🔍 开始监控desktop_manager进程 (PID: {process.pid})...")
        
        # 等待进程结束
        return_code = process.wait()
        print(f"🔔 检测到desktop_manager进程已结束，返回代码: {return_code}")
        
        # 清理JSON文件
        cleanup_json_files()
        
    except Exception as e:
        print(f"❌ 监控进程时出错: {str(e)}")

def start_cleanup_monitor(process):
    """启动独立线程来监控进程并清理文件"""
    try:
        monitor_thread = threading.Thread(
            target=monitor_process_and_cleanup, 
            args=(process,), 
            daemon=True
        )
        monitor_thread.start()
        print("🔍 已启动独立线程监控desktop_manager进程")
    except Exception as e:
        print(f"❌ 启动进程监控线程失败: {str(e)}")

class DesktopIconWorker(QThread):
    """桌面图标操作工作线程"""
    progress_updated = pyqtSignal(str, int)  # 消息，进度百分比
    operation_completed = pyqtSignal(bool)  # 操作完成，成功状态
    
    def __init__(self, operation_type, parent=None):
        super().__init__(parent)
        self.operation_type = operation_type  # 'backup' 或 'restore'
        self.icon_manager = DesktopIconManager()
        
    def run(self):
        """执行桌面图标操作"""
        try:
            success = False
            
            if self.operation_type == 'backup':
                print("开始备份桌面图标...")
                success = self.icon_manager.backup_desktop_icons(self.progress_callback)
            elif self.operation_type == 'restore':
                print("开始还原桌面图标...")
                success = self.icon_manager.restore_desktop_icons(self.progress_callback)
            
            # 确保进度达到100%
            self.progress_updated.emit("操作完成", 100)
            
            # 发送完成信号
            self.operation_completed.emit(success)
            
        except Exception as e:
            print(f"桌面图标操作失败: {str(e)}")
            self.progress_updated.emit(f"操作失败: {str(e)}", 100)
            self.operation_completed.emit(False)
    
    def progress_callback(self, message, progress):
        """进度回调函数"""
        self.progress_updated.emit(message, progress)


class EnhancedTransitionScreen(TransitionScreen):
    """增强的过渡界面 - 支持桌面图标操作"""
    
    # 定义额外的信号
    icon_operation_completed = pyqtSignal(bool)  # 图标操作完成信号
    
    def __init__(self, message="正在处理，请稍候...", duration=3000, icon_operation=None):
        """
        创建增强的过渡界面
        
        参数:
            message: 显示的消息文本
            duration: 自动关闭的时间（毫秒）
            icon_operation: 图标操作类型 ('backup', 'restore', None)
        """
        super().__init__(message, duration)
        self.icon_operation = icon_operation
        self.icon_worker = None
        self.icon_operation_completed_flag = False
        
        # 如果需要执行图标操作，修改进度文本
        if self.icon_operation == 'backup':
            self.progress_texts = [
                "正在初始化云桌面环境...",
                "正在优化桌面布局...",
                "正在启动云桌面服务...",
                "云桌面启动完成..."
            ]
        elif self.icon_operation == 'restore':
            self.progress_texts = [
                "正在保存云桌面状态...",
                "正在恢复本地桌面...",
                "正在清理云桌面资源...",
                "云桌面关闭完成..."
            ]
    
    def show_transition_with_icon_operation(self, custom_message=None, custom_duration=None, loading_style=None):
        """显示过渡界面并执行图标操作"""
        
        # 启动图标操作工作线程
        if self.icon_operation:
            self.start_icon_operation()
        
        # 显示过渡界面
        self.show_transition(custom_message, custom_duration, loading_style)
    
    def start_icon_operation(self):
        """启动图标操作工作线程"""
        if not self.icon_operation:
            return
        
        print(f"启动图标操作: {self.icon_operation}")
        
        # 创建工作线程
        self.icon_worker = DesktopIconWorker(self.icon_operation)
        
        # 连接信号
        self.icon_worker.progress_updated.connect(self.on_icon_progress_updated)
        self.icon_worker.operation_completed.connect(self.on_icon_operation_completed)
        
        # 启动线程
        self.icon_worker.start()
    
    def on_icon_progress_updated(self, message, progress):
        """图标操作进度更新"""
        print(f"图标操作进度: {progress}% - {message}")
        
        # 更新界面显示
        if hasattr(self, 'info_label'):
            self.info_label.setText(message)
        
        # 更新进度条（如果使用进度条样式）
        if hasattr(self, 'circular_widget') and self.circular_widget.isVisible():
            self.circular_widget.set_progress(progress)
        
        if hasattr(self, 'glowing_bar') and self.glowing_bar.isVisible():
            self.glowing_bar.set_progress(progress)
    
    def on_icon_operation_completed(self, success):
        """图标操作完成"""
        self.icon_operation_completed_flag = True
        
        if success:
            print(f"桌面文件操作完成: {self.icon_operation}")
            if hasattr(self, 'info_label'):
                if self.icon_operation == 'backup':
                    self.info_label.setText("云桌面启动成功，正在进入...")
                elif self.icon_operation == 'restore':
                    self.info_label.setText("云桌面已关闭，正在返回...")
        else:
            print(f"桌面文件操作失败: {self.icon_operation}")
            if hasattr(self, 'info_label'):
                self.info_label.setText("操作遇到问题，但将继续...")
        
        # 发送完成信号
        self.icon_operation_completed.emit(success)
    
    def _on_close_timeout(self):
        """重写关闭超时方法，确保图标操作完成后再关闭"""
        print("过渡页面计时器超时...")
        
        # 检查图标操作是否完成
        if self.icon_operation and not self.icon_operation_completed_flag:
            print("等待图标操作完成...")
            # 延长等待时间
            self.close_timer.start(1000)  # 再等1秒
            return
        
        print("准备关闭过渡页面...")
        self.finished.emit()  # 发出完成信号
        self.close()  # 关闭对话框
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止图标操作线程
        if self.icon_worker and self.icon_worker.isRunning():
            print("正在停止图标操作线程...")
            self.icon_worker.terminate()
            self.icon_worker.wait(3000)  # 等待最多3秒
        
        # 调用父类关闭事件
        super().closeEvent(event)


def create_backup_transition(message="正在打开云桌面...", duration=5000):
    """创建打开云桌面的过渡界面"""
    return EnhancedTransitionScreen(message, duration, 'backup')


def create_restore_transition(message="正在关闭云桌面...", duration=5000):
    """创建关闭云桌面的过渡界面"""
    return EnhancedTransitionScreen(message, duration, 'restore')


def start_desktop_manager():
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
            return False
        
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
                
                process = subprocess.Popen([
                    python_executable, desktop_manager_path
                ], creationflags=creationflags)
            else:
                # 非Windows平台
                process = subprocess.Popen([
                    sys.executable, desktop_manager_path
                ])
        else:
            # 可执行文件，直接运行，不显示终端窗口
            if sys.platform == "win32":
                # Windows平台隐藏窗口
                process = subprocess.Popen([
                    desktop_manager_path
                ], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                process = subprocess.Popen([
                    desktop_manager_path
                ])
        
        print(f"desktop_manager 已启动，进程ID: {process.pid}")
        
        # 启动独立的进程监控来清理JSON文件
        start_cleanup_monitor(process)
        
        return True
        
    except FileNotFoundError:
        print("错误：找不到 desktop_manager 程序或Python解释器")
        return False
    except Exception as e:
        print(f"启动 desktop_manager 时出错: {str(e)}")
        return False


def start_fullscreen_browser():
    """启动全屏浏览器程序"""
    try:
        print("正在启动 fullscreen_browser...")
        
        # 查找fullscreen_browser程序
        browser_paths = [
            "fullscreen_browser.py",
            "fullscreen_browser.exe", 
            "./fullscreen_browser.py",
            "./fullscreen_browser.exe",
            os.path.join(os.path.dirname(__file__), "fullscreen_browser.py"),
            os.path.join(os.path.dirname(__file__), "fullscreen_browser.exe"),
            os.path.join(os.getcwd(), "fullscreen_browser.py"),
            os.path.join(os.getcwd(), "fullscreen_browser.exe")
        ]
        
        browser_path = None
        for path in browser_paths:
            if os.path.exists(path):
                browser_path = path
                break
        
        if not browser_path:
            print("错误：找不到 fullscreen_browser 程序文件")
            return False
        
        # 根据文件类型选择启动方式
        if browser_path.endswith('.py'):
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
                
                process = subprocess.Popen([
                    python_executable, browser_path
                ], creationflags=creationflags)
            else:
                # 非Windows平台
                process = subprocess.Popen([
                    sys.executable, browser_path
                ])
        else:
            # 可执行文件，直接运行，不显示终端窗口
            if sys.platform == "win32":
                # Windows平台隐藏窗口
                process = subprocess.Popen([
                    browser_path
                ], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                process = subprocess.Popen([
                    browser_path
                ])
        
        print(f"fullscreen_browser 已启动，进程ID: {process.pid}")
        return True
        
    except FileNotFoundError:
        print("错误：找不到 fullscreen_browser 程序或Python解释器")
        return False
    except Exception as e:
        print(f"启动 fullscreen_browser 时出错: {str(e)}")
        return False


def main():
    """独立过渡页面的主函数"""
    # 创建独立的应用程序实例
    app = QApplication(sys.argv)
    
    # 获取命令行参数
    message = "正在处理，请稍候..."
    duration = 5000
    operation_type = None
    launch_program = None
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        message = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            pass
    if len(sys.argv) > 3:
        if sys.argv[3] == "--backup":
            operation_type = "backup"
            launch_program = "desktop_manager"
        elif sys.argv[3] == "--restore":
            operation_type = "restore"
            launch_program = "fullscreen_browser"
        elif sys.argv[3] == "--exit-mode":
            # 退出模式，不执行任何操作
            pass
    
    print(f"增强过渡页面启动: {message}")
    print(f"持续时间: {duration}ms")
    print(f"图标操作: {operation_type}")
    print(f"启动程序: {launch_program}")
    
    # 创建过渡页面
    transition_screen = EnhancedTransitionScreen(message, duration, operation_type)
    
    def on_transition_finished():
        """过渡页面完成后的回调"""
        print("过渡页面完成")
        
        # 根据参数启动相应程序
        if launch_program == "desktop_manager":
            print("正在启动desktop_manager...")
            success = start_desktop_manager()
            if success:
                print("desktop_manager启动成功")
            else:
                print("desktop_manager启动失败")
        elif launch_program == "fullscreen_browser":
            print("正在启动fullscreen_browser...")
            success = start_fullscreen_browser()
            if success:
                print("fullscreen_browser启动成功")
            else:
                print("fullscreen_browser启动失败")
        
        # 延迟一点后关闭过渡页面和应用程序
        QTimer.singleShot(500, app.quit)
    
    def on_icon_operation_completed(success):
        """图标操作完成回调"""
        if success:
            print(f"图标操作成功: {operation_type}")
        else:
            print(f"图标操作失败: {operation_type}")
    
    # 连接信号
    transition_screen.finished.connect(on_transition_finished)
    transition_screen.icon_operation_completed.connect(on_icon_operation_completed)
    
    # 显示过渡页面
    transition_screen.show_transition_with_icon_operation()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 