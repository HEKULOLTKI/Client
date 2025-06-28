#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目主启动文件
支持启动不同的模块：
- 全屏浏览器
- 桌面管理器
- 各种测试模块
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """主函数 - 根据命令行参数启动不同模块"""
    # 如果没有参数，默认启动全屏浏览器
    if len(sys.argv) < 2:
        module = 'browser'
        print("🚀 正在启动全屏浏览器...")
        print("💡 提示：您也可以使用以下命令启动其他模块：")
        print("  python main.py browser     # 启动全屏浏览器")
        print("  python main.py desktop     # 启动桌面管理器")
        print("  python main.py pet         # 启动桌面宠物")
        print("  python main.py chat        # 启动聊天窗口")
        print("-" * 50)
    else:
        module = sys.argv[1].lower()
    
    try:
        if module == 'browser':
            from src.browser.fullscreen_browser import main as browser_main
            browser_main()
        elif module == 'desktop':
            from src.desktop.desktop_manager import main as desktop_main
            # 将剩余的参数传递给desktop_manager
            original_argv = sys.argv
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # 保留脚本名和额外参数
            desktop_main()
            sys.argv = original_argv  # 恢复原始参数
        elif module == 'pet':
            # 启动独立的宠物应用
            from PyQt5.QtWidgets import QApplication
            from src.ui.widgets.pet_widget import PetWidget
            
            app = QApplication(sys.argv)
            pet = PetWidget()
            pet.show()
            sys.exit(app.exec_())
        elif module == 'chat':
            # 启动独立的聊天应用
            from PyQt5.QtWidgets import QApplication
            from src.ui.widgets.chat_widget import ChatWidget
            from src.api.openai_api import OpenAIChat
            
            app = QApplication(sys.argv)
            openai_chat = OpenAIChat()
            chat = ChatWidget(openai_chat)
            chat.show()
            sys.exit(app.exec_())
        else:
            print(f"未知的模块: {module}")
            sys.exit(1)
            
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保所有依赖都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 