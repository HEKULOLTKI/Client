# API 配置文件
# 多智能体协作运维系统 API 配置

# API 基础URL
API_BASE_URL = "http://localhost:8000"

# 默认认证信息（实际使用时应该从环境变量或配置文件读取）
DEFAULT_USERNAME = "user1"
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