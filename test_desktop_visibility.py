#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试桌面管理器窗口可见性的脚本
用于诊断顶部悬浮窗口没有出现的问题
"""

import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from src.desktop.desktop_manager import DesktopManager

def test_desktop_manager_visibility():
    """测试桌面管理器的可见性"""
    print("🔍 开始测试桌面管理器可见性...")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    
    try:
        # 创建桌面管理器
        print("📱 创建DesktopManager实例...")
        desktop_manager = DesktopManager()
        
        # 检查窗口属性
        print("🔧 检查窗口属性...")
        print(f"   窗口大小: {desktop_manager.width()} x {desktop_manager.height()}")
        print(f"   窗口位置: ({desktop_manager.x()}, {desktop_manager.y()})")
        print(f"   窗口可见: {desktop_manager.isVisible()}")
        print(f"   窗口隐藏: {desktop_manager.isHidden()}")
        print(f"   窗口最小化: {desktop_manager.isMinimized()}")
        
        # 检查窗口标志
        flags = desktop_manager.windowFlags()
        print(f"🏳️ 窗口标志:")
        if flags & Qt.FramelessWindowHint:
            print("   ✅ 无边框窗口")
        if flags & Qt.WindowStaysOnTopHint:
            print("   ✅ 置顶窗口")
        if flags & Qt.Tool:
            print("   ✅ 工具窗口")
        
        # 强制显示窗口
        print("👁️ 强制显示窗口...")
        desktop_manager.show()
        desktop_manager.raise_()
        desktop_manager.activateWindow()
        
        # 再次检查可见性
        print("🔍 显示后的状态:")
        print(f"   窗口可见: {desktop_manager.isVisible()}")
        print(f"   窗口位置: ({desktop_manager.x()}, {desktop_manager.y()})")
        
        # 设置一个定时器来显示确认对话框
        def show_confirmation():
            reply = QMessageBox.question(
                None, 
                "窗口可见性确认", 
                "您现在能看到桌面顶部的悬浮窗口吗？\n\n"
                "如果能看到，请点击'Yes'\n"
                "如果看不到，请点击'No'",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                print("✅ 用户确认能看到窗口")
            else:
                print("❌ 用户确认看不到窗口")
                print("🔧 尝试其他显示方法...")
                
                # 尝试不同的显示方法
                desktop_manager.setWindowState(Qt.WindowNoState)
                desktop_manager.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
                desktop_manager.show()
                desktop_manager.move(100, 100)  # 移动到更明显的位置
                
                # 再次询问
                reply2 = QMessageBox.question(
                    None,
                    "第二次确认",
                    "现在能看到窗口了吗？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply2 == QMessageBox.Yes:
                    print("✅ 使用备用方法成功显示窗口")
                else:
                    print("❌ 仍然无法显示窗口，可能存在其他问题")
            
            app.quit()
        
        # 3秒后显示确认对话框
        QTimer.singleShot(3000, show_confirmation)
        
        # 运行应用程序
        return app.exec_()
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_desktop_manager_visibility()) 