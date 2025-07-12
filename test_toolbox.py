#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具箱测试脚本
用于测试Windows工具箱是否能正常工作
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from src.desktop.toolbox_manager import WindowsToolboxDialog

def test_toolbox():
    """测试工具箱"""
    try:
        print("🚀 正在启动工具箱测试...")
        
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 创建工具箱对话框
        print("📦 正在创建工具箱对话框...")
        toolbox = WindowsToolboxDialog(None)
        
        # 显示工具箱
        print("🖥️ 正在显示工具箱...")
        toolbox.show()
        
        print("✅ 工具箱测试启动成功！")
        print("💡 请尝试点击工具箱中的工具按钮，特别是'命令提示符'按钮")
        print("🔧 如果工具箱正常显示且点击工具按钮后能正常启动程序，说明修复成功")
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 工具箱测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_toolbox() 