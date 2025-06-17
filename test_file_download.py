#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在线聊天文件下载功能测试程序
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt

# 添加当前目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from online_chat_widget import FileChatBubble, OnlineChatWidget

class FileDownloadTestWindow(QMainWindow):
    """文件下载功能测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("文件下载功能测试")
        self.setGeometry(100, 100, 600, 500)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title = QLabel("文件下载功能测试")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 测试不同类型的文件消息
        test_files = [
            {
                'file_name': 'test_image.jpg',
                'file_url': '/uploads/chat/test_image.jpg',
                'file_size': 2048576,  # 2MB
                'content': '📎 test_image.jpg'
            },
            {
                'file_name': 'document.pdf',
                'file_url': '/uploads/chat/document.pdf',
                'file_size': 1024000,  # 1MB
                'content': '📎 document.pdf'
            },
            {
                'file_name': 'code.py',
                'file_url': '/uploads/chat/code.py',
                'file_size': 15360,  # 15KB
                'content': '📎 code.py'
            },
            {
                'file_name': 'archive.zip',
                'file_url': '/uploads/chat/archive.zip',
                'file_size': 5242880,  # 5MB
                'content': '📎 archive.zip'
            }
        ]
        
        # 创建文件消息气泡
        for i, file_info in enumerate(test_files):
            bubble = FileChatBubble(
                file_info=file_info,
                is_user=(i % 2 == 0),  # 交替显示用户和其他人的消息
                sender_name="测试用户" if i % 2 == 0 else "其他用户",
                timestamp="12:34"
            )
            layout.addWidget(bubble)
        
        # 添加测试按钮
        test_button = QPushButton("启动完整聊天界面测试")
        test_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        test_button.clicked.connect(self.launch_chat_widget)
        layout.addWidget(test_button)
        
        # 添加使用说明
        instructions = QLabel("""
使用说明：
1. 点击任意文件消息气泡可以下载文件
2. 不同文件类型显示不同的图标
3. 鼠标悬停时气泡颜色会改变
4. 点击下方按钮可以启动完整的聊天界面
        """)
        instructions.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                color: #495057;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(instructions)
        
        layout.addStretch()
        
    def launch_chat_widget(self):
        """启动完整的聊天界面"""
        try:
            self.chat_widget = OnlineChatWidget()
            self.chat_widget.show()
            print("✅ 聊天界面已启动")
        except Exception as e:
            print(f"❌ 启动聊天界面失败: {str(e)}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("文件下载功能测试")
    app.setApplicationVersion("1.0")
    
    # 创建测试窗口
    window = FileDownloadTestWindow()
    window.show()
    
    print("🚀 文件下载功能测试程序已启动")
    print("📱 请在测试窗口中点击文件消息进行下载测试")
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 