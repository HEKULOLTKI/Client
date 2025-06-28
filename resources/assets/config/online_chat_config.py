import os

# 获取脚本所在目录作为基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 服务器配置
CHAT_API_BASE_URL = "http://172.18.122.8:8000"  # 聊天API服务器地址
CHAT_API_TIMEOUT = 10  # API请求超时时间（秒）

# 心跳配置
HEARTBEAT_INTERVAL = 30000  # 心跳间隔（毫秒）
RECONNECT_INTERVAL = 5000   # 重连间隔（毫秒）
AUTO_REFRESH_INTERVAL = 1000  # 自动刷新间隔（毫秒） - 3秒刷新一次，减少频繁刷新

# 文件上传配置
UPLOAD_MAX_SIZE = 50 * 1024 * 1024  # 最大文件大小 50MB
UPLOAD_ALLOWED_EXTENSIONS = [
    # 图片文件
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg',
    # 文档文件
    '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # 代码文件
    '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
    # 压缩文件
    '.zip', '.rar', '.7z', '.tar', '.gz',
    # 音频视频
    '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv'
]
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 分块上传大小 1MB

# 头像配置 - 使用工程师头像
ENGINEER_AVATARS_PATH = os.path.join(BASE_DIR, "..", "images", "roles", "engineer")
# 网络规划设计师对应 network_engineer
NETWORK_PLANNING_DESIGNER_AVATAR = os.path.join(ENGINEER_AVATARS_PATH, "network_engineer.jpg")
# 系统规划与管理师对应 network_planning (原Network_Planning_and_Management_Engineer)
NETWORK_PLANNING_AVATAR = os.path.join(ENGINEER_AVATARS_PATH, "Network_Planning_and_Management_Engineer.jpg")
# 系统架构师对应 system_architect
SYSTEM_ARCHITECT_AVATAR = os.path.join(ENGINEER_AVATARS_PATH, "system_architect.jpg")
# 系统分析师对应 systems_analyst
SYSTEMS_ANALYST_AVATAR = os.path.join(ENGINEER_AVATARS_PATH, "Systems_Analyst.png")

# 默认头像配置
DEFAULT_USER_AVATAR = SYSTEM_ARCHITECT_AVATAR
DEFAULT_ONLINE_USER_AVATAR = NETWORK_PLANNING_DESIGNER_AVATAR
DEFAULT_SYSTEM_AVATAR = NETWORK_PLANNING_AVATAR

# 备用头像路径（如果工程师头像不存在）
ASSETS_PATH = os.path.join(BASE_DIR, "assets")
FALLBACK_USER_AVATAR = os.path.join(ASSETS_PATH, "user.png")
FALLBACK_ONLINE_USER_AVATAR = os.path.join(ASSETS_PATH, "pet_head.png")

# 聊天窗口配置
CHAT_WINDOW_SIZE = (800, 700)
CHAT_BUBBLE_MAX_WIDTH = 450
CHAT_AVATAR_SIZE = (40, 40)
USER_LIST_AVATAR_SIZE = (30, 30)

# 消息配置
MAX_MESSAGE_LENGTH = 2000  # 最大消息长度
MESSAGE_HISTORY_LIMIT = 100  # 历史消息加载限制
AUTO_SCROLL_DELAY = 100  # 自动滚动延迟（毫秒）

# 界面配置
CHAT_ROOM_ID = "global"  # 默认聊天室ID
WINDOW_OPACITY = 0.95  # 窗口透明度
WINDOW_SHADOW_BLUR = 10  # 窗口阴影模糊半径

# 颜色主题
COLORS = {
    'primary': '#2ecc71',       # 主色调
    'primary_hover': '#27ae60',  # 主色调悬停
    'primary_pressed': '#229954', # 主色调按下
    'secondary': '#f8f9fa',     # 次要色
    'background': '#ffffff',    # 背景色
    'text_primary': '#1C1C1C',  # 主要文字色
    'text_secondary': '#666666', # 次要文字色
    'text_muted': '#999999',    # 静音文字色
    'border': '#E8E8E8',       # 边框色
    'success': '#2ecc71',      # 成功色
    'warning': '#f39c12',      # 警告色
    'error': '#e74c3c',        # 错误色
    'online': '#2ecc71',       # 在线状态色
    'offline': '#e74c3c',      # 离线状态色
}

# 字体配置
FONTS = {
    'default': 'Microsoft YaHei UI',
    'title': {'family': 'Microsoft YaHei UI', 'size': 12, 'weight': 'bold'},
    'message': {'family': 'Microsoft YaHei UI', 'size': 10, 'weight': 'normal'},
    'timestamp': {'family': 'Microsoft YaHei UI', 'size': 8, 'weight': 'normal'},
    'username': {'family': 'Microsoft YaHei UI', 'size': 9, 'weight': 'bold'},
    'status': {'family': 'Microsoft YaHei UI', 'size': 9, 'weight': 'normal'},
}

# 动画配置
ANIMATIONS = {
    'message_appear_duration': 300,  # 消息出现动画时长
    'loading_duration': 1000,       # 加载动画时长
    'hover_duration': 200,          # 悬停动画时长
}

# 调试配置
DEBUG_MODE = False  # 调试模式开关
LOG_LEVEL = 'INFO'  # 日志级别
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'online_chat.log')  # 日志文件路径

# 缓存配置
CACHE_DIR = os.path.join(BASE_DIR, 'cache', 'online_chat')
AVATAR_CACHE_SIZE = 100  # 头像缓存数量
MESSAGE_CACHE_SIZE = 1000  # 消息缓存数量

# 创建必要的目录
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def get_avatar_path(avatar_type='user'):
    """
    获取头像路径
    avatar_type: 'user', 'online_user', 'system', 'network_engineer', 'network_planning', 'system_architect', 'systems_analyst'
    """
    avatar_map = {
        'user': DEFAULT_USER_AVATAR,
        'online_user': DEFAULT_ONLINE_USER_AVATAR, 
        'system': DEFAULT_SYSTEM_AVATAR,
        # 按职业类型分配头像
        'network_engineer': NETWORK_PLANNING_DESIGNER_AVATAR,     # 网络规划设计师
        'network_planning': NETWORK_PLANNING_AVATAR,             # 系统规划与管理师
        'system_architect': SYSTEM_ARCHITECT_AVATAR,             # 系统架构师
        'systems_analyst': SYSTEMS_ANALYST_AVATAR                # 系统分析师
    }
    
    avatar_path = avatar_map.get(avatar_type, DEFAULT_USER_AVATAR)
    
    # 检查文件是否存在，如果不存在使用备用头像
    if not os.path.exists(avatar_path):
        fallback_map = {
            'user': FALLBACK_USER_AVATAR,
            'online_user': FALLBACK_ONLINE_USER_AVATAR,
            'system': FALLBACK_ONLINE_USER_AVATAR,
            'network_engineer': FALLBACK_ONLINE_USER_AVATAR,
            'network_planning': FALLBACK_ONLINE_USER_AVATAR,
            'system_architect': FALLBACK_USER_AVATAR,
            'systems_analyst': FALLBACK_USER_AVATAR
        }
        return fallback_map.get(avatar_type, FALLBACK_USER_AVATAR)
    
    return avatar_path

def get_avatar_by_profession(profession_name):
    """
    根据职业名称获取对应的头像路径
    profession_name: 职业名称
    """
    profession_avatar_map = {
        # 中文职业名称映射
        '网络规划设计师': 'network_engineer',
        '网络规划管理师': 'network_engineer',
        '系统规划与管理师': 'network_planning', 
        '系统架构设计师': 'system_architect',
        '系统分析师': 'systems_analyst',
        # 英文职业代码映射
        'network_engineer': 'network_engineer',
        'network_planning': 'network_planning',
        'system_architect': 'system_architect',
        'systems_analyst': 'systems_analyst',
        # 兼容性别名
        '网络工程师': 'network_engineer',
        '规划管理师': 'network_planning',
        '架构师': 'system_architect',
        '分析师': 'systems_analyst'
    }
    
    avatar_type = profession_avatar_map.get(profession_name, 'online_user')
    return get_avatar_path(avatar_type)

def is_file_allowed(filename):
    """检查文件是否允许上传"""
    if not filename:
        return False
    
    # 获取文件扩展名
    _, ext = os.path.splitext(filename.lower())
    return ext in UPLOAD_ALLOWED_EXTENSIONS

def format_file_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def get_file_type_icon(filename):
    """根据文件扩展名获取图标emoji"""
    if not filename:
        return "📄"
    
    _, ext = os.path.splitext(filename.lower())
    
    icon_map = {
        # 图片
        '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️', 
        '.webp': '🖼️', '.bmp': '🖼️', '.svg': '🖼️',
        
        # 文档
        '.pdf': '📄', '.txt': '📝', '.doc': '📄', '.docx': '📄',
        '.xls': '📊', '.xlsx': '📊', '.ppt': '📊', '.pptx': '📊',
        
        # 代码
        '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
        '.json': '📋', '.xml': '📋', '.yaml': '📋', '.yml': '📋',
        
        # 压缩
        '.zip': '🗜️', '.rar': '🗜️', '.7z': '🗜️', '.tar': '🗜️', '.gz': '🗜️',
        
        # 媒体
        '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬', 
        '.mov': '🎬', '.mkv': '🎬'
    }
    
    return icon_map.get(ext, '📄') 