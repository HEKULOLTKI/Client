#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断过渡页面和desktop启动问题
"""

import os
import sys
import json
import subprocess

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    abs_path = os.path.abspath(file_path)
    exists = os.path.exists(file_path)
    print(f"{'✅' if exists else '❌'} {description}: {abs_path}")
    return exists

def check_json_files():
    """检查JSON文件状态"""
    print("\n📄 检查JSON文件:")
    
    # 检查received_tasks.json
    if check_file_exists('received_tasks.json', 'received_tasks.json'):
        try:
            with open('received_tasks.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   📋 文件内容预览:")
                print(f"   - tasks数量: {len(data.get('tasks', []))}")
                print(f"   - user_info: {data.get('user_info', {}).get('user', {}).get('username', '无')}")
                print(f"   - selectedRole: {data.get('user_info', {}).get('selectedRole', {}).get('label', '无')}")
        except Exception as e:
            print(f"   ❌ 读取文件失败: {e}")
    
    # 检查received_data.json
    check_file_exists('received_data.json', 'received_data.json')

def check_python_modules():
    """检查Python模块"""
    print("\n🐍 检查Python环境:")
    print(f"   Python版本: {sys.version}")
    print(f"   Python路径: {sys.executable}")
    
    # 检查PyQt5
    try:
        import PyQt5
        print(f"   ✅ PyQt5已安装")
    except ImportError:
        print(f"   ❌ PyQt5未安装")
    
    # 检查requests
    try:
        import requests
        print(f"   ✅ requests已安装")
    except ImportError:
        print(f"   ❌ requests未安装")

def check_project_structure():
    """检查项目结构"""
    print("\n📁 检查项目结构:")
    
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"   项目根目录: {current_dir}")
    
    # 检查关键文件
    files_to_check = [
        ('main.py', 'main.py'),
        ('src/browser/fullscreen_browser.py', '全屏浏览器'),
        ('src/desktop/desktop_manager.py', '桌面管理器'),
        ('src/ui/screens/transition_screen.py', '基础过渡页面'),
        ('src/ui/screens/independent_transition.py', '独立过渡页面'),
        ('src/ui/screens/enhanced_transition_screen.py', '增强过渡页面')
    ]
    
    all_exist = True
    for file_path, description in files_to_check:
        full_path = os.path.join(current_dir, file_path)
        if not check_file_exists(full_path, description):
            all_exist = False
    
    return all_exist

def test_transition_page():
    """测试过渡页面是否能正常启动"""
    print("\n🧪 测试过渡页面:")
    
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 查找过渡页面脚本
    script_paths = [
        os.path.join(current_dir, "src", "ui", "screens", "independent_transition.py"),
        os.path.join(current_dir, "src", "ui", "screens", "enhanced_transition_screen.py")
    ]
    
    script_path = None
    for path in script_paths:
        if os.path.exists(path):
            script_path = path
            break
    
    if not script_path:
        print("   ❌ 找不到过渡页面脚本")
        return False
    
    print(f"   📄 使用脚本: {script_path}")
    
    # 尝试启动过渡页面（测试模式，2秒后自动关闭）
    try:
        print("   🚀 尝试启动过渡页面（测试模式，2秒后自动关闭）...")
        
        cmd = [sys.executable, script_path, "测试过渡页面", "2000", "--exit-mode"]
        
        if sys.platform == "win32":
            # Windows下使用CREATE_NEW_CONSOLE，这样能看到输出
            process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            process = subprocess.Popen(cmd)
        
        # 等待进程结束
        return_code = process.wait(timeout=5)
        
        if return_code == 0:
            print("   ✅ 过渡页面测试成功")
            return True
        else:
            print(f"   ❌ 过渡页面返回错误代码: {return_code}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ 过渡页面测试超时")
        process.kill()
        return False
    except Exception as e:
        print(f"   ❌ 启动过渡页面失败: {e}")
        return False

def test_desktop_manager():
    """测试desktop_manager是否能正常启动"""
    print("\n🧪 测试desktop_manager:")
    
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_py_path = os.path.join(current_dir, "main.py")
    
    if not os.path.exists(main_py_path):
        print("   ❌ 找不到main.py")
        return False
    
    try:
        print("   🚀 尝试启动desktop_manager（将在3秒后终止）...")
        
        cmd = [sys.executable, main_py_path, "desktop"]
        
        if sys.platform == "win32":
            # Windows下使用CREATE_NEW_CONSOLE
            process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            process = subprocess.Popen(cmd)
        
        # 等待3秒
        import time
        time.sleep(3)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            print("   ✅ desktop_manager启动成功")
            # 终止进程
            process.terminate()
            return True
        else:
            print(f"   ❌ desktop_manager启动后立即退出，返回代码: {process.poll()}")
            return False
            
    except Exception as e:
        print(f"   ❌ 启动desktop_manager失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("=" * 60)
    print("系统诊断工具")
    print("=" * 60)
    
    # 1. 检查项目结构
    structure_ok = check_project_structure()
    
    # 2. 检查Python环境
    check_python_modules()
    
    # 3. 检查JSON文件
    check_json_files()
    
    # 4. 测试过渡页面
    transition_ok = test_transition_page()
    
    # 5. 测试desktop_manager
    desktop_ok = test_desktop_manager()
    
    # 诊断结果
    print("\n" + "=" * 60)
    print("📊 诊断结果:")
    print("=" * 60)
    
    if structure_ok and transition_ok and desktop_ok:
        print("✅ 所有组件都正常！")
        print("\n可能的问题：")
        print("1. JSON数据格式不正确")
        print("2. 网络连接问题")
        print("\n建议：")
        print("1. 运行 test_json_trigger.py 测试不同的JSON格式")
        print("2. 检查控制台输出，查看具体的错误信息")
    else:
        print("❌ 发现以下问题：")
        if not structure_ok:
            print("   - 项目文件结构不完整")
        if not transition_ok:
            print("   - 过渡页面无法正常启动")
        if not desktop_ok:
            print("   - desktop_manager无法正常启动")
        
        print("\n建议：")
        print("1. 确保所有项目文件都存在")
        print("2. 检查Python环境和依赖是否正确安装")
        print("3. 查看具体的错误信息")
    
    print("\n💡 提示：如果fullscreen_browser正在运行，请查看其控制台输出")
    print("   特别注意以下信息：")
    print("   - '检测到xxx格式数据'")
    print("   - '数据验证通过/失败'")
    print("   - '正在启动独立过渡页面进程'")

if __name__ == "__main__":
    main() 