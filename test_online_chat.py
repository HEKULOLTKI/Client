#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
在线聊天功能测试
测试完善后的在线聊天组件，包括工程师头像、文件上传等功能
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 添加当前目录到模块搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from online_chat_widget import OnlineChatWidget
from file_upload_widget import FileUploadWidget
import online_chat_config as config

class OnlineChatTestWindow(QMainWindow):
    """在线聊天测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.chat_widget = None
        self.upload_widget = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置测试界面"""
        self.setWindowTitle("在线聊天功能测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("在线聊天功能测试")
        title.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2ecc71; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # 配置信息显示
        info_text = f"""
配置信息:
• 服务器地址: {config.CHAT_API_BASE_URL}
• 聊天室: {config.CHAT_ROOM_ID}
• 窗口大小: {config.CHAT_WINDOW_SIZE[0]}x{config.CHAT_WINDOW_SIZE[1]}
• 最大文件大小: {config.format_file_size(config.UPLOAD_MAX_SIZE)}
• 头像路径: image/engineer/
"""
        
        info_label = QLabel(info_text)
        info_label.setFont(QFont("Microsoft YaHei UI", 9))
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                color: #495057;
            }
        """)
        layout.addWidget(info_label)
        
        # 测试按钮
        self.create_test_buttons(layout)
        
    def create_test_buttons(self, layout):
        """创建测试按钮"""
        # 打开聊天窗口
        chat_btn = QPushButton("打开在线聊天窗口")
        chat_btn.setFixedHeight(50)
        chat_btn.setFont(QFont("Microsoft YaHei UI", 12))
        chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        chat_btn.clicked.connect(self.open_chat_window)
        layout.addWidget(chat_btn)
        
        # 测试文件上传组件
        upload_btn = QPushButton("测试文件上传组件")
        upload_btn.setFixedHeight(50)
        upload_btn.setFont(QFont("Microsoft YaHei UI", 12))
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        upload_btn.clicked.connect(self.test_file_upload)
        layout.addWidget(upload_btn)
        
        # 测试头像加载
        avatar_btn = QPushButton("测试工程师头像加载")
        avatar_btn.setFixedHeight(50)
        avatar_btn.setFont(QFont("Microsoft YaHei UI", 12))
        avatar_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #0f6674;
            }
        """)
        avatar_btn.clicked.connect(self.test_avatar_loading)
        layout.addWidget(avatar_btn)
        
        # 退出按钮
        exit_btn = QPushButton("退出测试")
        exit_btn.setFixedHeight(40)
        exit_btn.setFont(QFont("Microsoft YaHei UI", 10))
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        
    def open_chat_window(self):
        """打开聊天窗口"""
        try:
            if self.chat_widget is None:
                self.chat_widget = OnlineChatWidget()
                
            # 设置测试用户信息
            self.chat_widget.set_user_info("测试用户")
            
            # 显示聊天窗口
            self.chat_widget.show()
            
            # 居中显示
            screen = QApplication.desktop().availableGeometry()
            size = self.chat_widget.geometry()
            x = (screen.width() - size.width()) // 2
            y = (screen.height() - size.height()) // 2
            self.chat_widget.move(x, y)
            
            print("✅ 在线聊天窗口已打开")
            
        except Exception as e:
            print(f"❌ 打开聊天窗口失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def test_file_upload(self):
        """测试文件上传组件"""
        try:
            if self.upload_widget is None:
                self.upload_widget = FileUploadWidget()
                self.upload_widget.setWindowTitle("文件上传测试")
                self.upload_widget.resize(600, 500)
                
            self.upload_widget.show()
            
            # 居中显示
            screen = QApplication.desktop().availableGeometry()
            size = self.upload_widget.geometry()
            x = (screen.width() - size.width()) // 2
            y = (screen.height() - size.height()) // 2
            self.upload_widget.move(x, y)
            
            print("✅ 文件上传组件已打开")
            
        except Exception as e:
            print(f"❌ 打开文件上传组件失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def test_avatar_loading(self):
        """测试工程师头像加载"""
        try:
            print("🧪 测试工程师头像加载...")
            
            # 测试各种头像类型
            avatar_types = ['user', 'online_user', 'system']
            for avatar_type in avatar_types:
                avatar_path = config.get_avatar_path(avatar_type)
                exists = os.path.exists(avatar_path)
                status = "✅ 存在" if exists else "❌ 不存在"
                print(f"  {avatar_type}: {avatar_path} - {status}")
            
            # 测试文件大小和格式支持
            print("\n📁 支持的文件格式:")
            extensions = config.UPLOAD_ALLOWED_EXTENSIONS
            for i, ext in enumerate(extensions):
                if i % 8 == 0:
                    print()
                print(f"{ext:>6}", end=" ")
            print(f"\n\n📊 最大文件大小: {config.format_file_size(config.UPLOAD_MAX_SIZE)}")
            
            # 测试文件类型图标
            print("\n🎨 文件类型图标测试:")
            test_files = [
                "test.py", "image.jpg", "document.pdf", "archive.zip", 
                "music.mp3", "video.mp4", "data.json", "unknown.xyz"
            ]
            for filename in test_files:
                icon = config.get_file_type_icon(filename)
                print(f"  {filename:>15} -> {icon}")
            
            print("\n✅ 头像和配置测试完成")
            
        except Exception as e:
            print(f"❌ 头像测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 关闭所有测试窗口
        if self.chat_widget:
            self.chat_widget.close()
        if self.upload_widget:
            self.upload_widget.close()
        event.accept()

def main():
    """主函数"""
    print("=== 在线聊天功能测试启动 ===")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {current_dir}")
    print(f"配置文件: online_chat_config.py")
    print("=" * 50)
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("在线聊天功能测试")
    app.setApplicationVersion("1.0")
    
    # 设置应用程序样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ffffff;
        }
        QWidget {
            font-family: "Microsoft YaHei UI", "Arial", sans-serif;
        }
    """)
    
    try:
        # 创建并显示测试窗口
        test_window = OnlineChatTestWindow()
        test_window.show()
        
        # 居中显示
        screen = app.desktop().availableGeometry()
        size = test_window.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        test_window.move(x, y)
        
        print("✅ 测试窗口已启动")
        print("💡 提示: 可以测试聊天窗口、文件上传和头像加载功能")
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 应用程序启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 