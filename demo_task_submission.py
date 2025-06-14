#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务提交功能演示脚本
演示如何使用桌面管理器的任务提交功能
"""

import sys
import requests
import api_config

def demo_task_submission():
    """演示任务提交功能"""
    print("=" * 60)
    print("桌面管理器任务提交功能演示")
    print("=" * 60)
    
    print("\n📋 功能说明:")
    print("1. 点击桌面管理器上的 📤 任务提交 按钮")
    print("2. 系统会自动获取当前用户的所有任务")
    print("3. 将状态为'进行中'的任务标记为'已完成'")
    print("4. 显示提交结果")
    
    print("\n🔧 当前配置:")
    print(f"API服务器: {api_config.API_BASE_URL}")
    print(f"用户名: {api_config.DEFAULT_USERNAME}")
    print(f"用户类型: {api_config.DEFAULT_LOGIN_TYPE}")
    
    print("\n📊 当前任务状态:")
    
    try:
        # 先进行认证
        auth_data = {
            "login_type": api_config.DEFAULT_LOGIN_TYPE,
            "username": api_config.DEFAULT_USERNAME,
            "password": api_config.DEFAULT_PASSWORD,
            "grant_type": "password"
        }
        
        auth_response = requests.post(
            f"{api_config.API_BASE_URL}{api_config.API_ENDPOINTS['login']}",
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=api_config.REQUEST_TIMEOUT
        )
        
        if auth_response.status_code != 200:
            print("❌ 认证失败，无法获取任务状态")
            return
            
        token_data = auth_response.json()
        access_token = token_data.get('access_token')
        
        # 获取任务列表
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        tasks_response = requests.get(
            f"{api_config.API_BASE_URL}{api_config.API_ENDPOINTS['my_tasks']}",
            headers=headers,
            timeout=api_config.REQUEST_TIMEOUT
        )
        
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            print(f"📝 总任务数: {len(tasks)}")
            
            pending_tasks = [task for task in tasks if task.get('status') == '进行中']
            completed_tasks = [task for task in tasks if task.get('status') == '已完成']
            
            print(f"🔄 进行中任务: {len(pending_tasks)}")
            print(f"✅ 已完成任务: {len(completed_tasks)}")
            
            print("\n📋 任务详情:")
            for i, task in enumerate(tasks, 1):
                status_icon = "🔄" if task.get('status') == '进行中' else "✅" if task.get('status') == '已完成' else "❓"
                print(f"   {i}. {status_icon} {task.get('task_name', '未命名任务')} - {task.get('status', '未知状态')} ({task.get('progress', 0)}%)")
            
            if pending_tasks:
                print(f"\n🎯 点击任务提交按钮将提交 {len(pending_tasks)} 个进行中的任务")
            else:
                print("\n✨ 当前没有待提交的任务")
                
        else:
            print("❌ 获取任务列表失败")
            
    except Exception as e:
        print(f"❌ 连接API失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("使用说明:")
    print("1. 确保 API 服务器在 http://localhost:8000 运行")
    print("2. 运行 python desktop_manager.py 启动桌面管理器")
    print("3. 点击顶部的 📤 任务提交 按钮")
    print("4. 等待任务提交完成")
    print("=" * 60)

if __name__ == "__main__":
    demo_task_submission() 