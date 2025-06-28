#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON数据触发过渡页面和desktop启动
"""

import requests
import json
import time
import sys

def test_task_deployment_format():
    """测试新格式：任务分配版本"""
    print("\n🧪 测试1: 任务分配格式 (action='task_deployment')")
    
    data = {
        "action": "task_deployment",
        "deployment_info": {
            "target_role": "系统架构设计师",
            "deployment_time": "2024-01-15 14:30:00",
            "operator": {
                "user_id": "admin001",
                "username": "管理员",
                "operator_role": "项目经理"
            }
        },
        "assigned_tasks": [
            {
                "assignment_id": "ASSIGN001",
                "assignment_status": "pending",
                "task_id": "TASK001",
                "task_name": "系统架构设计",
                "task_type": "design"
            }
        ],
        "deployment_summary": {
            "deployment_id": "DEPLOY001",
            "total_tasks": 1
        }
    }
    
    return send_json_data(data)

def test_traditional_format():
    """测试旧格式：传统任务版本"""
    print("\n🧪 测试2: 传统任务格式 (包含tasks数组)")
    
    data = {
        "tasks": [
            {
                "id": "TASK001",
                "name": "系统架构设计",
                "description": "设计系统整体架构"
            }
        ],
        "user": {
            "id": "user001",
            "username": "张三",
            "role": "engineer"
        },
        "selectedRole": {
            "value": "architect",
            "label": "系统架构设计师"
        },
        "timestamp": "2024-01-15 14:30:00"
    }
    
    return send_json_data(data)

def test_role_selection_format():
    """测试角色选择格式"""
    print("\n🧪 测试3: 角色选择格式 (action='role_selection')")
    
    data = {
        "action": "role_selection",
        "user": {
            "id": "user001",
            "username": "张三",
            "role": "engineer"
        },
        "selectedRole": {
            "value": "architect",
            "label": "系统架构设计师"
        },
        "timestamp": "2024-01-15 14:30:00"
    }
    
    return send_json_data(data)

def test_user_sync_format():
    """测试用户数据同步格式"""
    print("\n🧪 测试4: 用户数据同步格式 (action='user_data_sync')")
    
    data = {
        "action": "user_data_sync",
        "sync_info": {
            "sync_type": "full",
            "sync_time": "2024-01-15 14:30:00",
            "operator": {
                "user_id": "admin001",
                "username": "管理员",
                "operator_role": "系统管理员"
            }
        },
        "users": [
            {
                "id": "user001",
                "username": "张三",
                "role": "engineer",
                "type": "internal",
                "status": "active"
            }
        ],
        "sync_summary": {
            "sync_id": "SYNC001",
            "total_users": 1
        }
    }
    
    return send_json_data(data)

def test_digital_twin_format():
    """测试数字孪生平台格式"""
    print("\n🧪 测试5: 数字孪生平台格式")
    
    data = {
        "platform_info": {
            "description": "数字孪生平台系统访问地址",
            "url": "http://192.168.1.100:8080/digital-twin"
        }
    }
    
    return send_json_data(data)

def send_json_data(data):
    """发送JSON数据到API服务器"""
    url = "http://localhost:8800/upload"
    
    try:
        print(f"📤 发送数据到: {url}")
        print(f"📋 数据内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ 请求成功: {response.json()}")
            return True
        else:
            print(f"❌ 请求失败: 状态码 {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：无法连接到API服务器")
        print("   请确保fullscreen_browser已启动并正在监听8800端口")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 发送请求时出错: {str(e)}")
        return False

def check_api_status():
    """检查API服务器状态"""
    url = "http://localhost:8800/status"
    
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✅ API服务器运行正常: {response.json()}")
            return True
        else:
            print(f"❌ API服务器响应异常")
            return False
    except:
        print("❌ 无法连接到API服务器")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("JSON数据触发测试工具")
    print("=" * 60)
    
    # 首先检查API服务器状态
    print("\n🔍 检查API服务器状态...")
    if not check_api_status():
        print("\n⚠️  请先启动fullscreen_browser:")
        print("   python main.py browser")
        sys.exit(1)
    
    print("\n请选择要测试的JSON格式：")
    print("1. 任务分配格式 (新格式)")
    print("2. 传统任务格式 (旧格式)")
    print("3. 角色选择格式")
    print("4. 用户数据同步格式")
    print("5. 数字孪生平台格式")
    print("6. 测试所有格式")
    print("0. 退出")
    
    while True:
        choice = input("\n请输入选项 (0-6): ").strip()
        
        if choice == "0":
            print("退出测试")
            break
        elif choice == "1":
            if test_task_deployment_format():
                print("\n💡 如果过渡页面和desktop启动了，说明新格式触发成功！")
        elif choice == "2":
            if test_traditional_format():
                print("\n💡 如果过渡页面和desktop启动了，说明旧格式触发成功！")
        elif choice == "3":
            if test_role_selection_format():
                print("\n💡 如果过渡页面和desktop启动了，说明角色选择格式触发成功！")
        elif choice == "4":
            if test_user_sync_format():
                print("\n💡 如果过渡页面和desktop启动了，说明用户同步格式触发成功！")
        elif choice == "5":
            if test_digital_twin_format():
                print("\n💡 如果浏览器切换到了数字孪生平台，说明格式触发成功！")
        elif choice == "6":
            print("\n🧪 测试所有格式...")
            
            # 测试会触发desktop的格式
            formats = [
                ("任务分配", test_task_deployment_format),
                ("传统任务", test_traditional_format),
                ("角色选择", test_role_selection_format),
                ("用户同步", test_user_sync_format)
            ]
            
            for name, test_func in formats:
                if test_func():
                    print(f"\n⏰ 等待5秒观察效果...")
                    time.sleep(5)
                    
                    response = input(f"\n{name}格式是否成功触发了过渡页面和desktop? (y/n): ").strip().lower()
                    if response == 'y':
                        print(f"✅ {name}格式触发成功！")
                        print("\n💡 您可以使用这种格式的JSON数据")
                        return
                    else:
                        print(f"❌ {name}格式未触发")
            
            # 最后测试数字孪生平台格式
            test_digital_twin_format()
            
        else:
            print("无效的选项，请重新输入")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main() 