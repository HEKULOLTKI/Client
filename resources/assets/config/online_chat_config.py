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
ICONS_PATH = os.path.join(BASE_DIR, "..", "images", "icons")
FALLBACK_USER_AVATAR = os.path.join(ICONS_PATH, "user.png")
FALLBACK_ONLINE_USER_AVATAR = os.path.join(ICONS_PATH, "user.png")

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
DEBUG_MODE = True  # 调试模式开关（临时开启用于测试）
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
        # 中文职业名称映射（完整名称）
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
        
        # 简化名称和常用别名
        '网络工程师': 'network_engineer',
        '网络设计师': 'network_engineer',
        '网络管理师': 'network_engineer',
        '规划设计师': 'network_engineer',
        '规划管理师': 'network_planning',
        '系统管理师': 'network_planning',
        '架构师': 'system_architect',
        '系统架构师': 'system_architect',
        '架构设计师': 'system_architect',
        '分析师': 'systems_analyst',
        '系统分析员': 'systems_analyst',
        
        # 角色代码（可能从后端传来）
        'Network_Planning_and_Management_Engineer': 'network_planning',
        'Systems_Analyst': 'systems_analyst',
        'network_planning_engineer': 'network_planning',
        'system_analysis': 'systems_analyst',
        
        # 其他可能的变体
        '网络': 'network_engineer',
        '规划': 'network_planning',
        '架构': 'system_architect',
        '分析': 'systems_analyst'
    }
    
    avatar_type = profession_avatar_map.get(profession_name, 'online_user')
    return get_avatar_path(avatar_type)

def create_rounded_avatar(avatar_path, size=40):
    """
    创建完美圆形头像
    avatar_path: 头像文件路径
    size: 头像大小（像素）
    返回: QPixmap对象
    """
    from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath, QPen
    from PyQt5.QtCore import Qt
    
    # 加载原始图片
    original_pixmap = QPixmap(avatar_path)
    
    # 如果图片加载失败，创建默认头像
    if original_pixmap.isNull():
        print(f"⚠️ 头像加载失败: {avatar_path}")
        # 创建默认头像
        return create_default_avatar(size)
    
    # 创建目标Pixmap，确保透明背景
    result_pixmap = QPixmap(size, size)
    result_pixmap.fill(Qt.transparent)
    
    # 创建画师
    painter = QPainter(result_pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    
    # 创建圆形裁剪路径
    path = QPainterPath()
    path.addEllipse(0.0, 0.0, float(size), float(size))
    painter.setClipPath(path)
    
    # 计算图片缩放和定位
    # 保持纵横比的同时填充整个圆形区域
    image_size = original_pixmap.size()
    scale_factor = max(size / image_size.width(), size / image_size.height())
    
    scaled_width = int(image_size.width() * scale_factor)
    scaled_height = int(image_size.height() * scale_factor)
    
    # 居中定位
    x_offset = (size - scaled_width) // 2
    y_offset = (size - scaled_height) // 2
    
    # 缩放并绘制图片
    scaled_pixmap = original_pixmap.scaled(
        scaled_width, scaled_height, 
        Qt.KeepAspectRatio, 
        Qt.SmoothTransformation
    )
    
    painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
    
    # 绘制圆形边框（可选）
    painter.setClipping(False)
    painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(0, 0, size-1, size-1)
    
    painter.end()
    
    print(f"✅ 圆形头像处理完成: {avatar_path} -> {size}x{size}")
    return result_pixmap

def create_default_avatar(size=40):
    """
    创建默认头像（简单的用户图标）
    size: 头像大小
    返回: QPixmap对象
    """
    from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
    from PyQt5.QtCore import Qt
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制背景圆
    painter.setBrush(QColor(100, 149, 237))  # 蓝色背景
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    
    # 绘制用户图标
    painter.setPen(QColor(255, 255, 255))
    painter.setBrush(QColor(255, 255, 255))
    
    # 头部 (圆形)
    head_size = size // 4
    head_x = (size - head_size) // 2
    head_y = size // 4
    painter.drawEllipse(head_x, head_y, head_size, head_size)
    
    # 身体 (椭圆)
    body_width = int(size * 0.6)
    body_height = int(size * 0.4)
    body_x = (size - body_width) // 2
    body_y = int(size * 0.5)
    painter.drawEllipse(body_x, body_y, body_width, body_height)
    
    painter.end()
    
    print(f"🔄 创建默认头像，大小: {size}x{size}")
    return pixmap

def create_user_profession_mapping():
    """
    创建用户职业映射配置
    """
    # 预定义的用户职业映射
    predefined_mapping = {
        # 测试用户
        'user1': '系统架构设计师',
        'user2': '网络规划设计师', 
        'user3': '系统规划与管理师',
        'user4': '系统分析师',
        
        # 管理员用户
        'admin': '系统架构设计师',
        'administrator': '系统架构设计师',
        'root': '系统架构设计师',
        
        # 访客用户
        'guest': '网络规划设计师',
        'visitor': '网络规划设计师',
        
        # 角色关键词映射
        'architect': '系统架构设计师',
        'network': '网络规划设计师',
        'manager': '系统规划与管理师',
        'analyst': '系统分析师'
    }
    
    return predefined_mapping

def get_profession_by_priority(username):
    """
    根据优先级获取用户职业
    1. 预定义映射
    2. 用户名关键词推断
    3. 哈希分配
    """
    # 1. 预定义映射
    predefined_mapping = create_user_profession_mapping()
    if username in predefined_mapping:
        return predefined_mapping[username]
    
    # 2. 关键词推断
    username_lower = username.lower()
    if any(keyword in username_lower for keyword in ['admin', 'architect', '架构', 'arch']):
        return '系统架构设计师'
    elif any(keyword in username_lower for keyword in ['network', '网络', 'net']):
        return '网络规划设计师'
    elif any(keyword in username_lower for keyword in ['manager', '管理', 'mgr', 'planning']):
        return '系统规划与管理师'
    elif any(keyword in username_lower for keyword in ['analyst', '分析', 'analysis']):
        return '系统分析师'
    
    # 3. 哈希分配（确保同一用户总是得到相同职业）
    default_professions = ['系统架构设计师', '网络规划设计师', '系统规划与管理师', '系统分析师']
    user_hash = hash(username) % len(default_professions)
    return default_professions[user_hash]

def debug_avatar_config():
    """
    调试头像配置，检查所有头像文件是否存在
    """
    print("🔍 调试头像配置状态：")
    print(f"📁 工程师头像目录: {ENGINEER_AVATARS_PATH}")
    print(f"📁 图标目录: {ICONS_PATH}")
    
    avatar_files = {
        '网络规划设计师': NETWORK_PLANNING_DESIGNER_AVATAR,
        '系统规划与管理师': NETWORK_PLANNING_AVATAR,
        '系统架构师': SYSTEM_ARCHITECT_AVATAR,
        '系统分析师': SYSTEMS_ANALYST_AVATAR,
        '备用用户头像': FALLBACK_USER_AVATAR,
        '备用在线用户头像': FALLBACK_ONLINE_USER_AVATAR
    }
    
    for name, path in avatar_files.items():
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {path}")
    
    print(f"🎯 默认用户头像: {DEFAULT_USER_AVATAR}")
    print(f"🎯 默认在线用户头像: {DEFAULT_ONLINE_USER_AVATAR}")
    print(f"🎯 默认系统头像: {DEFAULT_SYSTEM_AVATAR}")
    
    print("📝 支持的职业映射:")
    for profession in ['网络规划设计师', '系统架构设计师', '系统分析师', '系统规划与管理师']:
        avatar_type = get_avatar_by_profession(profession)
        print(f"   {profession} -> {avatar_type}")
    
    print("👥 用户职业映射测试:")
    test_users = ['user1', 'user2', 'user3', 'user4', 'admin', 'guest', 'architect', 'network']
    for user in test_users:
        profession = get_profession_by_priority(user)
        avatar_path = get_avatar_by_profession(profession)
        print(f"   {user} -> {profession} -> {avatar_path}")
    
    print("🎯 用户身份识别系统就绪")

# 自动执行调试（仅在开发模式下）
if DEBUG_MODE:
    debug_avatar_config()

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