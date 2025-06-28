#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Manager启动脚本（带JSON文件清理监控）
确保当desktop_manager关闭时自动清理JSON文件
"""

import os
import sys
import subprocess
import threading
import time
import json

def cleanup_json_files():
    """清理JSON文件"""
    try:
        print("🧹 执行JSON文件清理...")
        
        json_files = [
            'received_data.json',
            'received_tasks.json'
        ]
        
        deleted_files = []
        
        # 清理主要JSON文件
        for file_path in json_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    print(f"✅ 已删除JSON文件: {file_path}")
                except Exception as e:
                    print(f"❌ 删除文件 {file_path} 失败: {str(e)}")
        
        # 清理备份文件
        current_dir = os.getcwd()
        for filename in os.listdir(current_dir):
            if filename.startswith('received_tasks.json.notified_'):
                try:
                    os.remove(filename)
                    deleted_files.append(filename)
                    print(f"✅ 已删除备份文件: {filename}")
                except Exception as e:
                    print(f"❌ 删除备份文件 {filename} 失败: {str(e)}")
        
        if deleted_files:
            print(f"🧹 JSON文件清理完成，共删除 {len(deleted_files)} 个文件")
        else:
            print("🧹 没有找到需要清理的JSON文件")
            
        return len(deleted_files)
        
    except Exception as e:
        print(f"❌ 清理JSON文件时出错: {str(e)}")
        return 0

def monitor_desktop_manager(process):
    """监控desktop_manager进程"""
    try:
        print(f"🔍 开始监控desktop_manager进程 (PID: {process.pid})...")
        
        # 等待进程结束
        return_code = process.wait()
        print(f"🔔 检测到desktop_manager进程已结束，返回代码: {return_code}")
        
        # 执行清理
        cleanup_json_files()
        
    except Exception as e:
        print(f"❌ 监控进程时出错: {str(e)}")

def find_desktop_manager():
    """查找desktop_manager程序"""
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
    
    for path in desktop_manager_paths:
        if os.path.exists(path):
            return path
    
    return None

def start_desktop_manager_with_monitor():
    """启动desktop_manager并设置监控"""
    try:
        print("🚀 正在启动带监控的Desktop Manager...")
        
        # 查找desktop_manager程序
        desktop_manager_path = find_desktop_manager()
        if not desktop_manager_path:
            print("❌ 找不到desktop_manager程序文件")
            return False
        
        print(f"📍 找到程序文件: {desktop_manager_path}")
        
        # 根据文件类型选择启动方式
        if desktop_manager_path.endswith('.py'):
            # Python文件
            if sys.platform == "win32":
                # Windows平台使用pythonw运行，不显示终端窗口
                python_executable = sys.executable.replace('python.exe', 'pythonw.exe')
                if not os.path.exists(python_executable):
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
            # 可执行文件
            if sys.platform == "win32":
                process = subprocess.Popen([
                    desktop_manager_path
                ], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                process = subprocess.Popen([desktop_manager_path])
        
        print(f"✅ Desktop Manager已启动，PID: {process.pid}")
        
        # 启动监控线程
        monitor_thread = threading.Thread(
            target=monitor_desktop_manager, 
            args=(process,), 
            daemon=True
        )
        monitor_thread.start()
        print("🔍 进程监控已启动")
        
        # 等待用户输入或进程结束
        print("\n" + "=" * 60)
        print("✅ Desktop Manager运行中...")
        print("💡 提示：")
        print("   - Desktop Manager窗口中按ESC或点击退出按钮正常关闭")
        print("   - 或者在此窗口按Ctrl+C强制结束")
        print("   - 程序关闭时将自动清理JSON文件")
        print("=" * 60)
        
        try:
            # 等待进程结束或用户中断
            while process.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⚠️  收到中断信号，正在关闭desktop_manager...")
            try:
                process.terminate()
                process.wait(timeout=5)
                print("✅ Desktop Manager已关闭")
                
                # 手动执行清理
                cleanup_json_files()
                
            except subprocess.TimeoutExpired:
                print("⚠️  强制结束进程...")
                process.kill()
                cleanup_json_files()
        
        # 等待监控线程完成
        monitor_thread.join(timeout=2)
        
        print("🎉 程序结束")
        return True
        
    except Exception as e:
        print(f"❌ 启动desktop_manager时出错: {str(e)}")
        return False

def check_existing_files():
    """检查现有的JSON文件"""
    json_files = ['received_data.json', 'received_tasks.json']
    backup_files = []
    
    # 检查主要文件
    existing_main = []
    for file_path in json_files:
        if os.path.exists(file_path):
            existing_main.append(file_path)
    
    # 检查备份文件
    current_dir = os.getcwd()
    for filename in os.listdir(current_dir):
        if filename.startswith('received_tasks.json.notified_'):
            backup_files.append(filename)
    
    total_files = len(existing_main) + len(backup_files)
    
    if total_files > 0:
        print(f"⚠️  发现 {total_files} 个现有JSON文件:")
        for f in existing_main:
            print(f"   📄 {f}")
        for f in backup_files:
            print(f"   📦 {f}")
        
        choice = input("\n是否在启动前清理这些文件? (y/n): ").strip().lower()
        if choice in ['y', 'yes', '是', '1']:
            cleaned = cleanup_json_files()
            print(f"✅ 预清理完成，删除了 {cleaned} 个文件")
    else:
        print("✅ 当前目录没有JSON文件")

def main():
    """主函数"""
    print("🚀 Desktop Manager启动器（带JSON清理监控）")
    print("=" * 60)
    print(f"📍 工作目录: {os.getcwd()}")
    
    # 检查现有文件
    check_existing_files()
    
    print("\n🔧 准备启动Desktop Manager...")
    
    # 启动desktop_manager并设置监控
    success = start_desktop_manager_with_monitor()
    
    if not success:
        print("\n❌ 启动失败")
        input("按Enter键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main() 