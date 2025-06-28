#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字孪生平台功能测试脚本
发送包含"数字孪生平台系统访问地址"的JSON数据来测试功能
"""

import requests
import json
import time

# API端点
API_URL = "http://localhost:8800/upload"

# 测试数据 - 包含数字孪生平台访问地址
test_data = {
    "action": "system_access",
    "timestamp": "2024-01-01T12:00:00Z",
    "user": {
        "id": "test_user_001",
        "username": "测试用户",
        "role": "operator"
    },
    "system_info": {
        "system_id": "digital_twin_platform_001",
        "system_name": "数字孪生平台",
        "description": "数字孪生平台系统访问地址",
        "url": "http://localhost:3001",  # 测试用的孪生平台地址
        "status": "active",
        "access_level": "full"
    },
    "request_info": {
        "request_type": "platform_access",
        "requested_by": "test_user_001",
        "reason": "测试数字孪生平台功能"
    }
}

# 备用测试数据 - 不同的数据结构
alternative_test_data = {
    "type": "platform_request",
    "platforms": [
        {
            "id": "platform_001", 
            "name": "监控平台",
            "description": "系统监控平台",
            "access_url": "http://localhost:3002"
        },
        {
            "id": "platform_002",
            "name": "数字孪生系统",
            "description": "数字孪生平台系统访问地址",
            "web_url": "http://172.18.122.8:3001"  # 使用实际可能的地址
        }
    ],
    "user_context": {
        "user_id": "test_002",
        "session_id": "session_12345"
    }
}

def test_digital_twin_platform():
    """测试数字孪生平台功能"""
    print("🧪 开始测试数字孪生平台功能...")
    
    try:
        # 检查API服务器状态
        print("🔍 检查API服务器状态...")
        status_response = requests.get("http://localhost:8800/status", timeout=5)
        if status_response.status_code == 200:
            print("✅ API服务器运行正常")
            print(f"   响应: {status_response.json()}")
        else:
            print(f"❌ API服务器状态异常: {status_response.status_code}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到API服务器: {str(e)}")
        print("请确保全屏浏览器程序正在运行")
        return
    
    # 测试第一种数据格式
    print("\n📤 发送测试数据 1 (system_info格式)...")
    try:
        response = requests.post(
            API_URL,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 测试数据 1 发送成功!")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 测试数据 1 发送失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 发送测试数据 1 时出错: {str(e)}")
    
    print("\n⏰ 等待3秒后发送第二组测试数据...")
    time.sleep(3)
    
    # 测试第二种数据格式
    print("\n📤 发送测试数据 2 (platforms数组格式)...")
    try:
        response = requests.post(
            API_URL,
            json=alternative_test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 测试数据 2 发送成功!")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 测试数据 2 发送失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 发送测试数据 2 时出错: {str(e)}")
    
    print("\n🎯 测试完成!")
    print("请观察全屏浏览器窗口是否自动切换到数字孪生平台网页")

def print_test_data():
    """打印测试数据供参考"""
    print("📋 测试数据 1 (JSON格式):")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    print("\n📋 测试数据 2 (JSON格式):")
    print(json.dumps(alternative_test_data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 数字孪生平台功能测试脚本")
    print("=" * 60)
    
    choice = input("\n请选择操作:\n1. 运行测试\n2. 查看测试数据\n请输入选择 (1/2): ").strip()
    
    if choice == "1":
        test_digital_twin_platform()
    elif choice == "2":
        print_test_data()
    else:
        print("❌ 无效选择，退出程序") 