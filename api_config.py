# API 配置文件
# 多智能体协作运维系统 API 配置

import json
import os

# API 基础URL
API_BASE_URL = "http://172.18.122.8:8000"

def get_current_username():
    """从received_data.json文件中获取当前登录用户的用户名（优先users数组）"""
    try:
        # 检查received_data.json文件是否存在
        if os.path.exists('received_data.json'):
            with open('received_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 优先从users数组第一个元素获取
                if 'users' in data and isinstance(data['users'], list) and len(data['users']) > 0:
                    user = data['users'][0]
                    if 'username' in user:
                        return user['username']
                # 兼容旧格式
                if 'user' in data and 'username' in data['user']:
                    return data['user']['username']
        # 如果无法获取，返回默认值
        return "admin"
    except Exception as e:
        print(f"获取当前用户名时出错: {e}")
        return "admin"

def get_current_password():
    """从received_data.json文件中获取当前登录用户的密码"""
    try:
        # 检查received_data.json文件是否存在
        if os.path.exists('received_data.json'):
            with open('received_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 获取密码
                if 'user' in data and 'password' in data['user']:
                    return data['user']['password']
        # 如果无法获取，返回默认值
        return "123456"
    except Exception as e:
        print(f"获取当前用户密码时出错: {e}")
        return "123456"

def get_current_login_type():
    """从received_data.json文件中获取当前登录用户的类型"""
    try:
        # 检查received_data.json文件是否存在
        if os.path.exists('received_data.json'):
            with open('received_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 获取用户类型
                if 'user' in data and 'type' in data['user']:
                    return data['user']['type']
        # 如果无法获取，返回默认值
        return "操作员"
    except Exception as e:
        print(f"获取当前用户类型时出错: {e}")
        return "操作员"

def refresh_username():
    """刷新用户名配置，用于在JSON文件更新后重新获取用户名"""
    global DEFAULT_USERNAME
    DEFAULT_USERNAME = get_current_username()
    print(f"用户名已更新为: {DEFAULT_USERNAME}")
    return DEFAULT_USERNAME

def refresh_password():
    """刷新密码配置，用于在JSON文件更新后重新获取密码"""
    global DEFAULT_PASSWORD
    DEFAULT_PASSWORD = get_current_password()
    print(f"密码已更新")
    return DEFAULT_PASSWORD

def refresh_login_type():
    """刷新登录类型配置，用于在JSON文件更新后重新获取登录类型"""
    global DEFAULT_LOGIN_TYPE
    DEFAULT_LOGIN_TYPE = get_current_login_type()
    print(f"登录类型已更新为: {DEFAULT_LOGIN_TYPE}")
    return DEFAULT_LOGIN_TYPE

def refresh_all_config():
    """刷新所有配置，用于在JSON文件更新后重新获取所有配置"""
    refresh_username()
    refresh_password()
    refresh_login_type()
    print("所有配置已刷新")

# 默认认证信息（从JSON文件动态获取）
DEFAULT_USERNAME = get_current_username()
DEFAULT_PASSWORD = get_current_password()
DEFAULT_LOGIN_TYPE = get_current_login_type()

# API 端点
API_ENDPOINTS = {
    "login": "/api/auth/login",
    "my_tasks": "/api/my-tasks",
    "my_task_stats": "/api/my-task-stats",
    "refresh_token": "/api/auth/refresh",
    "devices": "/api/devices",
    "create_device": "/api/devices"
}

# 任务状态映射
TASK_STATUS = {
    "PENDING": "进行中",
    "COMPLETED": "已完成",
    "CANCELLED": "已取消"
}

# HTTP 请求超时设置（秒）
REQUEST_TIMEOUT = 30 