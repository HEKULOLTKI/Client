# API 配置文件
# 多智能体协作运维系统 API 配置

import json
import os

# API 基础URL
API_BASE_URL = "http://localhost:8000"

def get_current_username():
    """从received_data.json文件中获取当前登录用户的用户名"""
    try:
        # 检查received_data.json文件是否存在
        if os.path.exists('received_data.json'):
            with open('received_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 获取用户名
                if 'user' in data and 'username' in data['user']:
                    return data['user']['username']
        # 如果无法获取，返回默认值
        return "admin"
    except Exception as e:
        print(f"获取当前用户名时出错: {e}")
        return "admin"

def refresh_username():
    """刷新用户名配置，用于在JSON文件更新后重新获取用户名"""
    global DEFAULT_USERNAME
    DEFAULT_USERNAME = get_current_username()
    print(f"用户名已更新为: {DEFAULT_USERNAME}")
    return DEFAULT_USERNAME

# 默认认证信息（从JSON文件动态获取用户名）
DEFAULT_USERNAME = get_current_username()
DEFAULT_PASSWORD = "123456"
DEFAULT_LOGIN_TYPE = "操作员"  # 根据用户类型选择：操作员、管理员等

# API 端点
API_ENDPOINTS = {
    "login": "/api/auth/login",
    "my_tasks": "/api/my-tasks",
    "my_task_stats": "/api/my-task-stats",
    "refresh_token": "/api/auth/refresh"
}

# 任务状态映射
TASK_STATUS = {
    "PENDING": "进行中",
    "COMPLETED": "已完成",
    "CANCELLED": "已取消"
}

# HTTP 请求超时设置（秒）
REQUEST_TIMEOUT = 30 