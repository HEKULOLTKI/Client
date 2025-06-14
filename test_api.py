#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API连接测试脚本
用于测试与多智能体协作运维系统API的连接和认证
"""

import requests
import api_config

def test_api_connection():
    """测试API连接"""
    print("开始测试API连接...")
    print(f"API基础URL: {api_config.API_BASE_URL}")
    
    try:
        # 测试基本连接
        response = requests.get(f"{api_config.API_BASE_URL}/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            print("✓ API服务器连接正常")
        else:
            print("✗ API服务器连接异常")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 无法连接到API服务器: {e}")
        return False
    
    return True

def test_authentication_with_type(login_type):
    """测试指定类型的用户认证"""
    print(f"\n尝试登录类型: {login_type}")
    print(f"用户名: {api_config.DEFAULT_USERNAME}")
    
    try:
        auth_data = {
            "login_type": login_type,
            "username": api_config.DEFAULT_USERNAME,
            "password": api_config.DEFAULT_PASSWORD,
            "grant_type": "password"
        }
        
        response = requests.post(
            f"{api_config.API_BASE_URL}{api_config.API_ENDPOINTS['login']}",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=api_config.REQUEST_TIMEOUT
        )
        
        print(f"认证状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✓ 登录类型 '{login_type}' 认证成功")
            print(f"访问令牌: {token_data.get('access_token', '未获取到')[:20]}...")
            return token_data.get('access_token')
        else:
            print(f"✗ 登录类型 '{login_type}' 认证失败")
            return None
    except requests.exceptions.RequestException as e:
        print(f"✗ 认证请求异常: {e}")
        return None

def test_authentication():
    """测试用户认证 - 尝试不同的登录类型"""
    print("\n开始测试用户认证...")
    
    # 尝试不同的登录类型
    login_types = ["operator", "admin", "user", "password", "操作员", "管理员"]
    
    for login_type in login_types:
        access_token = test_authentication_with_type(login_type)
        if access_token:
            return access_token
    
    print("✗ 所有登录类型都认证失败")
    return None

def test_get_tasks(access_token):
    """测试获取任务列表"""
    if not access_token:
        print("跳过任务获取测试（无访问令牌）")
        return
        
    print("\n开始测试获取任务列表...")
    
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{api_config.API_BASE_URL}{api_config.API_ENDPOINTS['my_tasks']}",
            headers=headers,
            timeout=api_config.REQUEST_TIMEOUT
        )
        
        print(f"获取任务状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"✓ 成功获取到 {len(tasks)} 个任务")
            for i, task in enumerate(tasks[:3]):  # 只显示前3个任务
                print(f"  任务{i+1}: {task.get('task_name', '未命名')} - {task.get('status', '未知状态')}")
        else:
            print("✗ 获取任务失败")
    except requests.exceptions.RequestException as e:
        print(f"✗ 获取任务请求异常: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("多智能体协作运维系统 API 测试")
    print("=" * 50)
    
    # 测试连接
    if not test_api_connection():
        print("\n测试终止：无法连接到API服务器")
        return
    
    # 测试认证
    access_token = test_authentication()
    
    # 测试获取任务
    test_get_tasks(access_token)
    
    print("\n" + "=" * 50)
    print("API测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main() 