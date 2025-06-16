#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试认证和任务获取功能
分析认证失败和任务获取失败的原因
"""

import json
import os
import requests
import api_config
from datetime import datetime

def create_test_json_with_user2():
    """创建包含user2账号的测试JSON文件"""
    test_data = {
        "user": {
            "id": 24,
            "username": "user2",
            "password": "123456",
            "type": "操作员"
        },
        "selectedRole": {
            "label": "系统架构师",
            "value": "system_architect"
        }
    }
    
    with open('received_data.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 测试JSON文件已创建（user2账号）")
    return test_data

def test_api_connection():
    """测试API服务器连接"""
    print("🌐 测试API服务器连接...")
    try:
        response = requests.get(f"{api_config.API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API服务器连接正常")
            return True
        else:
            print(f"⚠️ API服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请检查服务器是否启动")
        return False
    except Exception as e:
        print(f"❌ 连接测试异常: {str(e)}")
        return False

def test_authentication(username, password, login_type):
    """测试认证功能"""
    print(f"\n🔐 测试认证: {username} / {password} / {login_type}")
    
    try:
        # 准备认证数据
        auth_data = {
            'login_type': login_type,
            'username': username,
            'password': password,
            'grant_type': 'password'
        }
        
        print(f"📤 发送认证请求: {auth_data}")
        
        # 发送认证请求
        response = requests.post(
            f"{api_config.API_BASE_URL}/api/auth/login",
            data=auth_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            print(f"✅ 认证成功，获得token: {access_token[:20]}...")
            return access_token
        else:
            print(f"❌ 认证失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 认证异常: {str(e)}")
        return None

def test_get_tasks(access_token):
    """测试获取任务功能"""
    print(f"\n📋 测试获取任务...")
    
    if not access_token:
        print("❌ 没有有效的访问令牌，无法获取任务")
        return []
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"📤 发送任务获取请求...")
        
        response = requests.get(
            f"{api_config.API_BASE_URL}/api/my-tasks",
            headers=headers,
            timeout=10
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容: {response.text}")
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ 成功获取 {len(tasks)} 个任务")
            return tasks
        else:
            print(f"❌ 获取任务失败: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 获取任务异常: {str(e)}")
        return []

def test_different_accounts():
    """测试不同的账号"""
    print("\n🧪 测试不同账号的认证...")
    
    # 测试账号列表
    test_accounts = [
        {"username": "user2", "password": "123456", "login_type": "操作员"},
        {"username": "admin", "password": "123456", "login_type": "管理员"},
        {"username": "admin", "password": "123456", "login_type": "操作员"},
        {"username": "user2", "password": "123456", "login_type": "管理员"},
    ]
    
    for account in test_accounts:
        print(f"\n{'='*50}")
        access_token = test_authentication(
            account["username"], 
            account["password"], 
            account["login_type"]
        )
        
        if access_token:
            tasks = test_get_tasks(access_token)
            print(f"📊 任务数量: {len(tasks)}")
        else:
            print("❌ 认证失败，跳过任务获取")

def analyze_config():
    """分析当前配置"""
    print("\n🔍 分析当前配置...")
    
    # 刷新配置
    api_config.refresh_all_config()
    
    print(f"API基础URL: {api_config.API_BASE_URL}")
    print(f"默认用户名: {api_config.DEFAULT_USERNAME}")
    print(f"默认密码: {api_config.DEFAULT_PASSWORD}")
    print(f"默认登录类型: {api_config.DEFAULT_LOGIN_TYPE}")
    print(f"请求超时: {api_config.REQUEST_TIMEOUT}秒")

def main():
    """主测试函数"""
    print("🚀 开始认证和任务获取测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 创建测试数据
    test_data = create_test_json_with_user2()
    
    # 2. 分析配置
    analyze_config()
    
    # 3. 测试API连接
    if not test_api_connection():
        print("❌ API服务器连接失败，终止测试")
        return
    
    # 4. 测试不同账号
    test_different_accounts()
    
    # 5. 使用配置文件中的账号测试
    print(f"\n{'='*50}")
    print("🔧 使用配置文件中的账号测试...")
    access_token = test_authentication(
        api_config.DEFAULT_USERNAME,
        api_config.DEFAULT_PASSWORD,
        api_config.DEFAULT_LOGIN_TYPE
    )
    
    if access_token:
        tasks = test_get_tasks(access_token)
        print(f"📊 配置账号任务数量: {len(tasks)}")
    
    print("\n🏁 测试完成")

def cleanup():
    """清理测试文件"""
    if os.path.exists('received_data.json'):
        os.remove('received_data.json')
        print("🧹 测试文件已清理")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup() 