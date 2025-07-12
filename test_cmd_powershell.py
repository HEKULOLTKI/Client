#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMD和PowerShell启动测试脚本
"""

import subprocess
import sys
import os

def test_cmd_direct():
    """直接测试CMD启动"""
    print("🔧 测试直接启动CMD...")
    try:
        # 方法1：直接启动
        process = subprocess.Popen(['cmd.exe'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"✅ CMD启动成功，PID: {process.pid}")
        return True
    except Exception as e:
        print(f"❌ CMD启动失败: {e}")
        return False

def test_powershell_direct():
    """直接测试PowerShell启动"""
    print("⚡ 测试直接启动PowerShell...")
    try:
        # 方法1：直接启动
        process = subprocess.Popen(['powershell.exe'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"✅ PowerShell启动成功，PID: {process.pid}")
        return True
    except Exception as e:
        print(f"❌ PowerShell启动失败: {e}")
        return False

def test_cmd_with_shell():
    """测试带shell参数的CMD启动"""
    print("🔧 测试带shell参数的CMD启动...")
    try:
        process = subprocess.Popen(['cmd.exe'], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"✅ CMD启动成功，PID: {process.pid}")
        return True
    except Exception as e:
        print(f"❌ CMD启动失败: {e}")
        return False

def test_powershell_with_shell():
    """测试带shell参数的PowerShell启动"""
    print("⚡ 测试带shell参数的PowerShell启动...")
    try:
        process = subprocess.Popen(['powershell.exe'], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"✅ PowerShell启动成功，PID: {process.pid}")
        return True
    except Exception as e:
        print(f"❌ PowerShell启动失败: {e}")
        return False

def test_os_system():
    """测试使用os.system启动"""
    print("🔧 测试使用os.system启动CMD...")
    try:
        result = os.system('start cmd.exe')
        print(f"✅ os.system启动CMD成功，返回值: {result}")
        return True
    except Exception as e:
        print(f"❌ os.system启动CMD失败: {e}")
        return False

def test_os_system_powershell():
    """测试使用os.system启动PowerShell"""
    print("⚡ 测试使用os.system启动PowerShell...")
    try:
        result = os.system('start powershell.exe')
        print(f"✅ os.system启动PowerShell成功，返回值: {result}")
        return True
    except Exception as e:
        print(f"❌ os.system启动PowerShell失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试CMD和PowerShell启动...")
    print("=" * 50)
    
    # 测试各种启动方法
    tests = [
        ("CMD直接启动", test_cmd_direct),
        ("PowerShell直接启动", test_powershell_direct),
        ("CMD带shell参数", test_cmd_with_shell),
        ("PowerShell带shell参数", test_powershell_with_shell),
        ("os.system启动CMD", test_os_system),
        ("os.system启动PowerShell", test_os_system_powershell),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 统计成功率
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    print(f"\n📈 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

if __name__ == "__main__":
    main() 