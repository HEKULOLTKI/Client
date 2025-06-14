# OpenAI API配置
OPENAI_API_KEY = "ragflow-E4Y2NiYjE0M2EyYTExZjA4MzM1ZTY5ZG"
CHAT_ID = "2fe60da83a2b11f0a458e69def3db951"

import os

# 获取脚本所在目录作为基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 资源路径配置
ASSETS_PATH = os.path.join(BASE_DIR, "assets")
PET_IDLE = os.path.join(ASSETS_PATH, "pet_idle.gif")
PET_WAVE = os.path.join(ASSETS_PATH, "pet_wave.gif")
PET_HAPPY = os.path.join(ASSETS_PATH, "pet_happy.gif")
PET_AVATAR = os.path.join(ASSETS_PATH, "pet_head.png")
USER_AVATAR = os.path.join(ASSETS_PATH, "user.png")
CLOSE_ICON = os.path.join(ASSETS_PATH, "close.png")

# 宠物配置
PET_SIZE = (120, 120)
PET_ANIMATION_DURATION = 2000

# 聊天窗口配置
CHAT_WINDOW_SIZE = (400, 600)
CHAT_BUBBLE_MAX_WIDTH = 300