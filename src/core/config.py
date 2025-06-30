# OpenAI API配置
OPENAI_API_KEY = "ragflow-E4Y2NiYjE0M2EyYTExZjA4MzM1ZTY5ZG"
CHAT_ID = "2fe60da83a2b11f0a458e69def3db951"

import os
import sys

def get_base_dir():
    """获取基础目录，兼容打包和开发环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 环境
            return sys._MEIPASS
        else:
            # 其他打包工具
            return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取项目根目录作为基础路径
BASE_DIR = get_base_dir()

# 资源路径配置
ASSETS_PATH = os.path.join(BASE_DIR, "resources", "assets")
IMAGES_PATH = os.path.join(ASSETS_PATH, "images")
ICONS_PATH = os.path.join(IMAGES_PATH, "icons")
PETS_PATH = os.path.join(IMAGES_PATH, "pets")

# 宠物图片资源
PET_IDLE = os.path.join(PETS_PATH, "pet_idle.gif")
PET_WAVE = os.path.join(PETS_PATH, "pet_wave.gif")
PET_HAPPY = os.path.join(PETS_PATH, "pet_happy.gif")
PET_AVATAR = os.path.join(PETS_PATH, "pet_head.png")

# 用户界面图标
USER_AVATAR = os.path.join(ICONS_PATH, "user.png")
CLOSE_ICON = os.path.join(ICONS_PATH, "close.png")
APP_ICON = os.path.join(ICONS_PATH, "icon.png")

# 宠物配置
PET_SIZE = (120, 120)
PET_ANIMATION_DURATION = 2000

# 聊天窗口配置
CHAT_WINDOW_SIZE = (400, 600)
CHAT_BUBBLE_MAX_WIDTH = 300