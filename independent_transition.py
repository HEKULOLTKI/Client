#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import json
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from transition_screen import TransitionScreen

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
        print("正在启动全屏浏览器...")
        
        # 查找全屏浏览器程序
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
        
        print(f"全屏浏览器已启动，进程ID: {process.pid}")
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
    message = "正在打开云桌面..."
    duration = 3000
    exit_mode = False
    launch_browser = False  # 新增：是否启动浏览器
    
    if len(sys.argv) > 1:
        message = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            pass
    if len(sys.argv) > 3:
        if sys.argv[3] == "--exit-mode":
            exit_mode = True
        elif sys.argv[3] == "--launch-browser":
            launch_browser = True
    if len(sys.argv) > 4 and sys.argv[4] == "--launch-browser":
        launch_browser = True
    
    print(f"独立过渡页面启动: {message}, 持续时间: {duration}ms, 退出模式: {exit_mode}, 启动浏览器: {launch_browser}")
    
    # 创建过渡页面
    transition_screen = TransitionScreen(message, duration)
    
    def on_transition_finished():
        """过渡页面完成后的回调"""
        if exit_mode:
            print("退出模式：过渡页面完成，直接关闭")
        elif launch_browser:
            print("过渡页面完成，正在启动全屏浏览器...")
            
            # 启动全屏浏览器
            success = start_fullscreen_browser()
            
            if success:
                print("全屏浏览器启动成功，过渡页面即将关闭")
            else:
                print("全屏浏览器启动失败，但过渡页面仍将关闭")
        else:
            print("过渡页面完成，正在启动desktop_manager...")
            
            # 启动desktop_manager
            success = start_desktop_manager()
            
            if success:
                print("desktop_manager启动成功，过渡页面即将关闭")
            else:
                print("desktop_manager启动失败，但过渡页面仍将关闭")
        
        # 延迟一点后关闭过渡页面和应用程序
        QTimer.singleShot(500, app.quit)
    
    # 连接完成信号
    transition_screen.finished.connect(on_transition_finished)
    
    # 显示过渡页面
    transition_screen.show_transition()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 