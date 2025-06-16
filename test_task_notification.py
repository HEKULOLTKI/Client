#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务通知功能修改效果
本脚本用于测试修改后的任务通知弹窗获取任务的方式是否与提交任务保持一致。
"""

import json
import os
from datetime import datetime

def create_test_task_data():
    """创建测试用的任务数据"""
    test_tasks = [
        {
            "id": 1,
            "assignment_id": 1,
            "name": "测试任务1",
            "task_name": "测试任务1",
            "description": "这是一个测试任务",
            "type": "开发",
            "task_type": "开发",
            "status": "待分配",
            "assignment_status": "待分配",
            "progress": 0,
            "priority": "high",
            "assigned_at": datetime.now().isoformat(),
            "estimated_duration": "2小时"
        },
        {
            "id": 2,
            "assignment_id": 2,
            "name": "测试任务2",
            "task_name": "测试任务2",
            "description": "这是另一个测试任务",
            "type": "测试",
            "task_type": "测试",
            "status": "进行中",
            "assignment_status": "进行中",
            "progress": 50,
            "priority": "normal",
            "assigned_at": datetime.now().isoformat(),
            "estimated_duration": "1小时"
        },
        {
            "id": 3,
            "assignment_id": 3,
            "name": "测试任务3",
            "task_name": "测试任务3",
            "description": "已完成的任务",
            "type": "部署",
            "task_type": "部署",
            "status": "已完成",
            "assignment_status": "已完成",
            "progress": 100,
            "priority": "low",
            "assigned_at": datetime.now().isoformat(),
            "estimated_duration": "0.5小时"
        }
    ]
    
    return test_tasks

def create_test_received_tasks():
    """创建测试用的received_tasks.json文件"""
    tasks = create_test_task_data()
    
    task_data = {
        "tasks": tasks,
        "user_info": {
            "user": {
                "id": 23,
                "username": "user1",
                "type": "操作员"
            },
            "selectedRole": {
                "label": "开发工程师",
                "value": "developer"
            }
        },
        "data_source": "test_data",
        "original_format": "test",
        "validation_passed": True,
        "fetch_time": datetime.now().isoformat()
    }
    
    # 保存到文件
    with open('received_tasks.json', 'w', encoding='utf-8') as f:
        json.dump(task_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 已创建测试任务数据文件: received_tasks.json")
    print(f"📋 包含 {len(tasks)} 个任务:")
    
    for i, task in enumerate(tasks, 1):
        status = task.get('status', '未知')
        name = task.get('name', '未命名')
        task_type = task.get('type', '未知类型')
        priority = task.get('priority', 'normal')
        print(f"   {i}. {name} - 状态: {status} | 类型: {task_type} | 优先级: {priority}")
    
    return task_data

def create_test_user_sync_data():
    """创建测试用的用户数据同步格式文件"""
    user_sync_data = {
        "sync_info": {
            "sync_id": "test_sync_001",
            "sync_time": datetime.now().isoformat(),
            "operator": {
                "operator_id": "op001",
                "operator_type": "前端操作员"
            }
        },
        "deployment_info": {
            "deployment_id": "deploy_001",
            "environment": "测试环境"
        },
        "user_data": {
            "id": 23,
            "username": "user1",
            "password": "test123",
            "type": "操作员",
            "status": "active"
        },
        "sync_summary": {
            "selected_role": {
                "label": "开发工程师",
                "value": "developer"
            }
        }
    }
    
    # 保存到文件
    with open('received_data.json', 'w', encoding='utf-8') as f:
        json.dump(user_sync_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 已创建用户数据同步文件: received_data.json")
    print(f"👤 用户信息: {user_sync_data['user_data']['username']} (ID: {user_sync_data['user_data']['id']})")
    print(f"🎯 角色: {user_sync_data['sync_summary']['selected_role']['label']}")

def main():
    """主测试函数"""
    print("🧪 开始创建测试数据...")
    print("=" * 50)
    
    # 创建测试任务数据
    print("1. 创建测试任务数据...")
    create_test_received_tasks()
    
    print("\n" + "=" * 50)
    
    # 创建用户同步数据（可选）
    print("2. 创建用户数据同步文件...")
    create_test_user_sync_data()
    
    print("\n" + "=" * 50)
    print("🎉 测试数据创建完成！")
    print("\n📝 测试说明:")
    print("   - received_tasks.json: 包含3个测试任务（2个待处理，1个已完成）")
    print("   - received_data.json: 用户数据同步格式文件")
    print("\n🚀 现在可以启动 desktop_manager.py 来测试任务通知功能")
    print("   修改后的任务通知弹窗将使用与提交任务相同的获取方式")
    print("\n✅ 预期结果:")
    print("   - 启动时会弹出任务通知，显示2个待处理任务")
    print("   - 任务获取方式与提交任务保持一致")
    print("   - 如果没有received_tasks.json，会通过API获取任务")

if __name__ == "__main__":
    main() 