from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, 
                           QLabel, QHBoxLayout, QScrollArea, QFrame, 
                           QToolButton, QSizePolicy, QProgressBar, QLayout,
                           QTextEdit, QFileDialog, QApplication, QMessageBox,
                           QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QUrl, QMimeData
from PyQt5.QtGui import (QFont, QIcon, QPixmap, QPainter, QColor, QPainterPath, 
                        QPen, QFontMetrics, QDesktopServices, QCursor, QBrush, QClipboard)
from PyQt5.QtSvg import QSvgWidget
import requests
import time
import json
import os
import subprocess
import webbrowser
import platform
import mimetypes
import tempfile
import uuid
from datetime import datetime
from resources.assets.config import online_chat_config as config
from src.api.token_manager import TokenManager
from src.ui.widgets.file_upload_widget import FileUploadWidget
from resources.assets.images.file_icons import get_file_icon_path

class OnlineLoadingIndicator(QProgressBar):
    """在线聊天加载指示器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        self.setTextVisible(False)
        self.setRange(0, 0)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #F0F2F5;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
            }
        """)
        self.hide()

class OnlineChatBubble(QFrame):
    """在线聊天气泡组件"""
    def __init__(self, text, is_user=True, sender_name="", timestamp="", profession="", message_type="text", parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text = text
        self.sender_name = sender_name
        self.timestamp = timestamp
        self.profession = profession
        self.message_type = message_type
        
        # 判断是否为系统消息
        self.is_system_message = (message_type == "system" or sender_name == "系统")
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.setStyleSheet("""
            OnlineChatBubble {
                background-color: transparent;
                border: none;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 消息信息栏（发送者和时间）- 系统消息不显示发送者信息
        if not is_user and not self.is_system_message:
            info_layout = QHBoxLayout()
            info_layout.setContentsMargins(50, 0, 0, 0)
            
            sender_label = QLabel(sender_name)
            sender_label.setFont(QFont("Microsoft YaHei UI", 8))
            sender_label.setStyleSheet("color: #666666;")
            
            time_label = QLabel(timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #999999;")
            
            info_layout.addWidget(sender_label)
            info_layout.addStretch()
            info_layout.addWidget(time_label)
            
            layout.addLayout(info_layout)
        
        # 消息主体布局
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(10)
        
        # 创建消息容器
        msg_container = QFrame()
        msg_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # 系统消息使用特殊样式
        if self.is_system_message:
            msg_container.setStyleSheet("""
                QFrame {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                }
            """)
        else:
            msg_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {'#2ecc71' if is_user else 'white'};
                    border-radius: 18px;
                }}
            """)
        
        container_layout = QHBoxLayout(msg_container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(0)
        
        # 创建头像 - 系统消息不显示头像
        avatar = None
        if not self.is_system_message:
            avatar = QLabel()
            avatar.setFixedSize(40, 40)
            
            # 获取头像路径
            if is_user:
                # 当前用户头像：优先根据职业选择，默认使用系统架构师
                if self.profession:
                    avatar_path = config.get_avatar_by_profession(self.profession)
                    print(f"👤 用户头像: 职业={self.profession}, 路径={avatar_path}")
                else:
                    avatar_path = config.get_avatar_path('user')
                    print(f"👤 用户头像: 默认路径={avatar_path}")
            else:
                # 其他用户头像：优先根据职业选择，默认使用网络规划设计师
                if self.profession:
                    avatar_path = config.get_avatar_by_profession(self.profession)
                    print(f"👥 其他用户头像: 职业={self.profession}, 路径={avatar_path}")
                else:
                    avatar_path = config.get_avatar_path('online_user')
                    print(f"👥 其他用户头像: 默认路径={avatar_path}")
            
            # 使用统一的头像处理函数
            avatar_pixmap = config.create_rounded_avatar(avatar_path, 40)
            avatar.setPixmap(avatar_pixmap)
            avatar.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                    margin: 0px;
                }
            """)
        
        # 创建文本容器
        text_container = QFrame()
        text_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # 创建文本标签
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setFont(QFont("Microsoft YaHei UI", 10))
        
        # 计算文本宽度
        font_metrics = QFontMetrics(text_label.font())
        max_width = config.CHAT_BUBBLE_MAX_WIDTH  # 最大宽度
        padding = 40    # 内边距总和
        
        # 计算实际文本宽度
        text_width = 0
        max_line_width = 0
        for line in text.split('\n'):
            line_width = font_metrics.horizontalAdvance(line)
            text_width += line_width
            max_line_width = max(max_line_width, line_width)
        
        # 设置文本标签的宽度
        min_width = min(max_line_width + padding, max_width)
        text_label.setMinimumWidth(min_width)
        
        # 如果文本宽度超过最大宽度，启用自动换行
        if max_line_width > max_width:
            text_label.setMaximumWidth(max_width)
        else:
            text_label.setMaximumWidth(min_width)
        
        text_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        
        # 设置文本样式和对齐方式
        if self.is_system_message:
            # 系统消息使用特殊样式
            text_label.setStyleSheet("""
                QLabel {
                    color: #856404;
                    background: transparent;
                    padding: 5px;
                    qproperty-alignment: AlignCenter;
                }
            """)
        else:
            text_label.setStyleSheet(f"""
                QLabel {{
                    color: {'white' if is_user else '#1C1C1C'};
                    background: transparent;
                    padding: 5px;
                    qproperty-alignment: AlignLeft;
                }}
            """)
        
        # 文本容器布局
        text_layout = QHBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        
        if self.is_system_message:
            # 系统消息居中显示
            text_layout.addStretch(1)
            text_layout.addWidget(text_label)
            text_layout.addStretch(1)
        elif is_user:
            # 用户消息：文本左对齐，整体靠右
            text_layout.addWidget(text_label)
        else:
            # 其他用户消息：文本左对齐，整体靠左
            text_layout.addWidget(text_label)
            text_layout.addStretch(1)
        
        # 添加文本容器到消息容器
        container_layout.addWidget(text_container)
        
        # 设置最终布局
        if self.is_system_message:
            # 系统消息居中显示，不显示头像
            msg_layout.addStretch(1)
            msg_layout.addWidget(msg_container)
            msg_layout.addStretch(1)
        elif is_user:
            msg_layout.addStretch(1)  # 左侧弹性空间
            msg_layout.addWidget(msg_container)  # 消息气泡
            if avatar:
                msg_layout.addWidget(avatar)  # 头像靠右
        else:
            if avatar:
                msg_layout.addWidget(avatar)  # 头像靠左
            msg_layout.addWidget(msg_container)  # 消息气泡
            msg_layout.addStretch(1)  # 右侧弹性空间
        
        # 用户消息显示时间在右侧，系统消息显示时间居中
        if is_user and timestamp and not self.is_system_message:
            time_layout = QHBoxLayout()
            time_layout.setContentsMargins(0, 0, 50, 0)
            time_layout.addStretch()
            
            time_label = QLabel(timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #999999;")
            time_layout.addWidget(time_label)
            
            layout.addLayout(msg_layout)
            layout.addLayout(time_layout)
        elif self.is_system_message and timestamp:
            # 系统消息时间居中显示
            time_layout = QHBoxLayout()
            time_layout.setContentsMargins(0, 5, 0, 0)
            time_layout.addStretch()
            
            time_label = QLabel(timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #856404;")
            time_layout.addWidget(time_label)
            time_layout.addStretch()
            
            layout.addLayout(msg_layout)
            layout.addLayout(time_layout)
        else:
            layout.addLayout(msg_layout)

class ImageChatBubble(QFrame):
    """图片消息气泡组件 - 直接显示图片"""
    def __init__(self, file_info, is_user=True, sender_name="", timestamp="", profession="", parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.file_info = file_info
        self.sender_name = sender_name
        self.timestamp = timestamp
        self.profession = profession
        
        # 从文件信息中提取数据
        self.file_name = file_info.get('file_name', '未知图片')
        self.file_url = file_info.get('file_url', '')
        self.file_size = file_info.get('file_size', 0)
        self.content = file_info.get('content', f"🖼️ {self.file_name}")
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.setStyleSheet("""
            ImageChatBubble {
                background-color: transparent;
                border: none;
            }
        """)
        
        # 图片相关属性
        self.image_label = None
        self.loading_label = None
        self.max_image_width = 300
        self.max_image_height = 200
        
        self.setup_ui()
        self.load_image()
        
    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 消息信息栏（发送者和时间）
        if not self.is_user:
            info_layout = QHBoxLayout()
            info_layout.setContentsMargins(50, 0, 0, 0)
            
            sender_label = QLabel(self.sender_name)
            sender_label.setFont(QFont("Microsoft YaHei UI", 8))
            sender_label.setStyleSheet("color: #666666;")
            
            time_label = QLabel(self.timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #999999;")
            
            info_layout.addWidget(sender_label)
            info_layout.addStretch()
            info_layout.addWidget(time_label)
            
            layout.addLayout(info_layout)
        
        # 消息主体布局
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(10)
        
        # 创建图片消息容器
        image_container = QFrame()
        image_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        image_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
                # 图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }
        """)
        self.image_label.setMinimumSize(150, 100)
        self.image_label.setMaximumSize(self.max_image_width, self.max_image_height)
        self.image_label.setScaledContents(False)

        # 加载提示
        self.loading_label = QLabel("🔄 正在加载图片...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.loading_label.setStyleSheet("color: #6c757d;")

        container_layout.addWidget(self.loading_label)
        container_layout.addWidget(self.image_label)
        
        # 设置图片点击事件
        self.image_label.mousePressEvent = self.on_image_clicked
        self.image_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.image_label.setToolTip("点击查看大图")
        
        # 添加操作按钮（浮动在图片上方）
        self.setup_image_controls()
        
        # 创建头像
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        
        # 获取头像路径
        if self.is_user:
            # 当前用户头像：优先根据职业选择，默认使用系统架构师
            if self.profession:
                avatar_path = config.get_avatar_by_profession(self.profession)
                print(f"🖼️ 用户图片头像: 职业={self.profession}, 路径={avatar_path}")
            else:
                avatar_path = config.get_avatar_path('user')
                print(f"🖼️ 用户图片头像: 默认路径={avatar_path}")
        else:
            # 其他用户头像：优先根据职业选择，默认使用网络规划设计师
            if self.profession:
                avatar_path = config.get_avatar_by_profession(self.profession)
                print(f"🖼️ 其他用户图片头像: 职业={self.profession}, 路径={avatar_path}")
            else:
                avatar_path = config.get_avatar_path('online_user')
                print(f"🖼️ 其他用户图片头像: 默认路径={avatar_path}")
        
        # 使用统一的头像处理函数
        avatar_pixmap = config.create_rounded_avatar(avatar_path, 40)
        avatar.setPixmap(avatar_pixmap)
        avatar.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        # 设置最终布局
        if self.is_user:
            msg_layout.addStretch(1)  # 左侧弹性空间
            msg_layout.addWidget(image_container)  # 图片消息气泡
            msg_layout.addWidget(avatar)  # 头像靠右
        else:
            msg_layout.addWidget(avatar)  # 头像靠左
            msg_layout.addWidget(image_container)  # 图片消息气泡
            msg_layout.addStretch(1)  # 右侧弹性空间
        
        # 用户消息显示时间在右侧
        if self.is_user and self.timestamp:
            time_layout = QHBoxLayout()
            time_layout.setContentsMargins(0, 0, 50, 0)
            time_layout.addStretch()
            
            time_label = QLabel(self.timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #999999;")
            time_layout.addWidget(time_label)
            
            layout.addLayout(msg_layout)
            layout.addLayout(time_layout)
        else:
            layout.addLayout(msg_layout)
    
    def load_image(self):
        """加载并显示图片"""
        if not self.file_url:
            self.loading_label.setText("❌ 图片链接无效")
            self.image_label.hide()
            return
        
        # 在新线程中下载图片
        self.download_thread = ImageDownloadThread(self.file_url, self.get_api_headers())
        self.download_thread.image_loaded.connect(self.on_image_loaded)
        self.download_thread.load_failed.connect(self.on_image_load_failed)
        self.download_thread.start()
    
    def get_api_headers(self):
        """获取API请求头"""
        # 查找父窗口中的OnlineChatWidget来获取API headers
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, 'api') and parent_widget.api:
                return parent_widget.api.get_headers()
            parent_widget = parent_widget.parent()
        return {}
    
    def on_image_loaded(self, pixmap):
        """图片加载成功"""
        self.loading_label.hide()
        
        # 计算合适的显示尺寸
        original_size = pixmap.size()
        scaled_size = self.calculate_display_size(original_size)
        
        # 缩放图片
        scaled_pixmap = pixmap.scaled(
            scaled_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # 设置图片
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setFixedSize(scaled_size)
        self.image_label.show()
        
        # 添加点击事件查看大图
        self.image_label.mousePressEvent = lambda event: self.show_full_image(pixmap)
        self.image_label.setCursor(QCursor(Qt.PointingHandCursor))
        
        print(f"✅ 图片加载成功: {self.file_name}")
    
    def on_image_load_failed(self, error_msg):
        """图片加载失败"""
        self.loading_label.setText(f"❌ 图片加载失败: {error_msg}")
        self.image_label.hide()
        print(f"❌ 图片加载失败: {self.file_name} - {error_msg}")
    
    def calculate_display_size(self, original_size):
        """计算适合显示的图片尺寸"""
        width = original_size.width()
        height = original_size.height()
        
        # 如果图片小于最大尺寸，保持原尺寸
        if width <= self.max_image_width and height <= self.max_image_height:
            return original_size
        
        # 按比例缩放
        width_ratio = self.max_image_width / width
        height_ratio = self.max_image_height / height
        scale_ratio = min(width_ratio, height_ratio)
        
        new_width = int(width * scale_ratio)
        new_height = int(height * scale_ratio)
        
        return QSize(new_width, new_height)
    
    def setup_image_controls(self):
        """设置图片操作控件"""
        # 创建按钮容器
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(8, 5, 8, 5)
        controls_layout.setSpacing(8)
        
        # 查看大图按钮
        view_btn = QPushButton("🔍")
        view_btn.setFixedSize(30, 30)
        view_btn.setFont(QFont("Microsoft YaHei UI", 12))
        view_btn.setCursor(QCursor(Qt.PointingHandCursor))
        view_btn.setToolTip("查看大图")
        view_btn.clicked.connect(self.view_full_image)
        
        # 下载按钮 - 使用SVG图标
        download_btn = QPushButton()
        download_btn.setFixedSize(30, 30)
        download_btn.setCursor(QCursor(Qt.PointingHandCursor))
        download_btn.setToolTip("下载图片")
        download_btn.clicked.connect(self.download_image)
        
        # 设置SVG图标
        download_icon_path = os.path.join(os.path.dirname(get_file_icon_path('download')), '下载.svg')
        if os.path.exists(download_icon_path):
            download_btn.setIcon(QIcon(download_icon_path))
            download_btn.setIconSize(QSize(18, 18))
        else:
            # 如果SVG文件不存在，回退到emoji
            download_btn.setText("📥")
            download_btn.setFont(QFont("Microsoft YaHei UI", 12))
        
        # 按钮样式
        button_style = f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #dee2e6;
                border-radius: 15px;
                color: #495057;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: white;
                border-color: #adb5bd;
                transform: scale(1.1);
            }}
            QPushButton:pressed {{
                background-color: #f8f9fa;
                transform: scale(0.95);
            }}
        """
        
        view_btn.setStyleSheet(button_style)
        download_btn.setStyleSheet(button_style)
        
        controls_layout.addStretch()
        controls_layout.addWidget(view_btn)
        controls_layout.addWidget(download_btn)
        
        # 添加到容器的底部
        container_layout = self.image_label.parent().layout()
        container_layout.addLayout(controls_layout)
    
    def view_full_image(self):
        """查看大图"""
        if hasattr(self.image_label, 'pixmap') and self.image_label.pixmap() and not self.image_label.pixmap().isNull():
            self.show_full_image(self.image_label.pixmap())
    
    def on_image_clicked(self, event):
        """图片点击事件"""
        if event.button() == Qt.LeftButton:
            self.view_full_image()
    
    def show_full_image(self, pixmap):
        """显示大图"""
        dialog = ImageViewDialog(pixmap, self.file_name, self)
        dialog.exec_()
    
    def download_image(self):
        """下载图片到本地"""
        if not self.file_url:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "下载失败", "图片链接不存在")
            return
        
        try:
            print(f"📥 准备下载图片: {self.file_name}")
            
            # 查找父窗口中的OnlineChatWidget
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, 'download_file_from_chat'):
                    # 找到了OnlineChatWidget，调用其下载方法
                    parent_widget.download_file_from_chat(self.file_url, self.file_name)
                    return
                parent_widget = parent_widget.parent()
            
            # 如果找不到父窗口的下载方法，则回退到浏览器下载
            print("⚠️ 未找到父窗口下载方法，回退到浏览器下载")
            
            # 构建完整的文件URL
            from resources.assets.config.online_chat_config import CHAT_API_BASE_URL
            if self.file_url.startswith('http'):
                full_url = self.file_url
            else:
                full_url = f"{CHAT_API_BASE_URL}{self.file_url}"
            
            # 使用浏览器打开
            from PyQt5.QtCore import QUrl
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(full_url))
            
        except Exception as e:
            print(f"❌ 图片下载失败: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "下载失败", f"图片下载失败：{str(e)}")
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

class ImageDownloadThread(QThread):
    """图片下载线程"""
    image_loaded = pyqtSignal(QPixmap)
    load_failed = pyqtSignal(str)
    
    def __init__(self, image_url, headers=None):
        super().__init__()
        self.image_url = image_url
        self.headers = headers or {}
    
    def run(self):
        """下载图片"""
        try:
            # 构建完整的图片URL
            from resources.assets.config.online_chat_config import CHAT_API_BASE_URL
            if self.image_url.startswith('http'):
                full_url = self.image_url
            else:
                full_url = f"{CHAT_API_BASE_URL}{self.image_url}"
            
            print(f"🖼️ 开始下载图片: {full_url}")
            
            # 下载图片数据
            response = requests.get(full_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # 创建QPixmap
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                self.image_loaded.emit(pixmap)
            else:
                self.load_failed.emit("图片格式不支持")
                
        except requests.exceptions.Timeout:
            self.load_failed.emit("下载超时")
        except requests.exceptions.ConnectionError:
            self.load_failed.emit("网络连接失败")
        except requests.exceptions.HTTPError as e:
            self.load_failed.emit(f"HTTP错误: {e.response.status_code}")
        except Exception as e:
            self.load_failed.emit(str(e))

class ImageViewDialog(QDialog):
    """增强版图片查看对话框 - 支持缩放、拖拽和全屏"""
    def __init__(self, pixmap, filename, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"图片查看器 - {filename}")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        self.setModal(True)
        
        # 图片相关属性
        self.original_pixmap = pixmap
        self.filename = filename
        self.scale_factor = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.last_mouse_pos = QPoint()
        self.drag_sensitivity = 1.0  # 拖动灵敏度
        
        # 计算初始窗口大小
        screen = QApplication.primaryScreen().geometry()
        initial_width = min(pixmap.width() + 100, int(screen.width() * 0.9))
        initial_height = min(pixmap.height() + 150, int(screen.height() * 0.9))
        self.resize(initial_width, initial_height)
        
        # 居中显示
        self.move(
            (screen.width() - initial_width) // 2,
            (screen.height() - initial_height) // 2
        )
        
        self.setup_ui()
        self.update_image()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)
        
        # 图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: none;
            }
        """)
        self.image_label.setMinimumSize(200, 200)
        
        # 设置拖拽
        self.image_label.setMouseTracking(True)
        self.image_label.setCursor(QCursor(Qt.OpenHandCursor))  # 显示可拖拽光标
        self.image_label.mousePressEvent = self.mouse_press_event
        self.image_label.mouseMoveEvent = self.mouse_move_event
        self.image_label.mouseReleaseEvent = self.mouse_release_event
        self.image_label.mouseDoubleClickEvent = self.mouse_double_click_event
        
        # 启用图片标签的拖拽功能
        self.image_label.setAcceptDrops(False)  # 不接受外部拖放
        self.scroll_area.setMouseTracking(True)  # 滚动区域也启用鼠标跟踪
        
        self.scroll_area.setWidget(self.image_label)
        
        # 信息栏
        info_layout = QHBoxLayout()
        self.info_label = QLabel()
        self.update_info_label()
        self.info_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                padding: 5px;
            }
        """)
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(info_layout)
        
    def update_image(self):
        """更新图片显示"""
        if self.original_pixmap.isNull():
            return
            
        # 计算缩放后的尺寸
        scaled_size = self.original_pixmap.size() * self.scale_factor
        
        # 缩放图片
        scaled_pixmap = self.original_pixmap.scaled(
            scaled_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())
        
        # 更新信息
        self.update_info_label()
        
    def update_info_label(self):
        """更新信息标签"""
        original_size = self.original_pixmap.size()
        current_size = self.original_pixmap.size() * self.scale_factor
        
        info_text = (f"📁 {self.filename} | "
                    f"📐 原始: {original_size.width()}×{original_size.height()} | "
                    f"📏 当前: {int(current_size.width())}×{int(current_size.height())} | "
                    f"🔍 {int(self.scale_factor * 100)}% | "
                    f"💡 双击重置位置，Ctrl+滚轮缩放，方向键移动")
        
        self.info_label.setText(info_text)
        
    def zoom_in(self):
        """放大"""
        new_scale = min(self.scale_factor * 1.25, self.max_scale)
        if new_scale != self.scale_factor:
            self.scale_factor = new_scale
            self.update_image()
            
    def zoom_out(self):
        """缩小"""
        new_scale = max(self.scale_factor / 1.25, self.min_scale)
        if new_scale != self.scale_factor:
            self.scale_factor = new_scale
            self.update_image()
            
    def reset_zoom(self):
        """重置缩放"""
        self.scale_factor = 1.0
        self.update_image()
        
    def fit_to_window(self):
        """适应窗口大小"""
        if self.original_pixmap.isNull():
            return
            
        # 获取可用空间
        available_size = self.scroll_area.size() - QSize(20, 20)  # 留出边距
        
        # 计算适合的缩放比例
        scale_w = available_size.width() / self.original_pixmap.width()
        scale_h = available_size.height() / self.original_pixmap.height()
        
        self.scale_factor = min(scale_w, scale_h, 1.0)  # 不超过原始大小
        self.scale_factor = max(self.scale_factor, self.min_scale)
        
        self.update_image()
        
    def save_image(self):
        """保存图片到本地"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import os
            
            # 获取文件扩展名
            _, ext = os.path.splitext(self.filename)
            if not ext:
                ext = '.png'
                
            # 构建文件过滤器
            filter_text = f"图片文件 (*{ext});;PNG文件 (*.png);;JPEG文件 (*.jpg);;所有文件 (*.*)"
            
            # 弹出保存对话框
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "保存图片", 
                self.filename,
                filter_text
            )
            
            if save_path:
                # 保存原始图片
                if self.original_pixmap.save(save_path):
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(self, "保存成功", f"图片已保存到:\n{save_path}")
                else:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "保存失败", "无法保存图片")
                    
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "保存失败", f"保存图片时发生错误:\n{str(e)}")
            
    def mouse_press_event(self, event):
        """鼠标按下事件 - 增强版拖动"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPos()  # 使用全局坐标
            self.last_mouse_pos = event.globalPos()
            self.image_label.setCursor(QCursor(Qt.ClosedHandCursor))
            
            # 记录当前滚动条位置
            self.initial_h_scroll = self.scroll_area.horizontalScrollBar().value()
            self.initial_v_scroll = self.scroll_area.verticalScrollBar().value()
            
            event.accept()  # 接受事件
            
    def mouse_move_event(self, event):
        """鼠标移动事件 - 增强版拖动"""
        if self.is_dragging and event.buttons() == Qt.LeftButton:
            # 计算总的移动距离（从开始拖动的位置）
            current_pos = event.globalPos()
            total_delta = current_pos - self.drag_start_pos
            
            # 应用拖动灵敏度
            delta_x = int(total_delta.x() * self.drag_sensitivity)
            delta_y = int(total_delta.y() * self.drag_sensitivity)
            
            # 获取滚动条
            h_scroll = self.scroll_area.horizontalScrollBar()
            v_scroll = self.scroll_area.verticalScrollBar()
            
            # 计算新的滚动位置（基于初始位置）
            new_h_value = self.initial_h_scroll - delta_x
            new_v_value = self.initial_v_scroll - delta_y
            
            # 确保在有效范围内
            new_h_value = max(h_scroll.minimum(), min(h_scroll.maximum(), new_h_value))
            new_v_value = max(v_scroll.minimum(), min(v_scroll.maximum(), new_v_value))
            
            # 设置滚动条位置
            h_scroll.setValue(new_h_value)
            v_scroll.setValue(new_v_value)
            
            event.accept()  # 接受事件
        elif not self.is_dragging:
            # 如果没有拖动，显示正常光标
            self.image_label.setCursor(QCursor(Qt.OpenHandCursor))
            
    def mouse_release_event(self, event):
        """鼠标释放事件 - 增强版拖动"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.image_label.setCursor(QCursor(Qt.OpenHandCursor))
            
            # 清理拖动状态
            self.drag_start_pos = QPoint()
            self.last_mouse_pos = QPoint()
            
            event.accept()  # 接受事件
            
    def mouse_double_click_event(self, event):
        """鼠标双击事件 - 重置图片位置到中心"""
        if event.button() == Qt.LeftButton:
            # 重置滚动条到中心位置
            h_scroll = self.scroll_area.horizontalScrollBar()
            v_scroll = self.scroll_area.verticalScrollBar()
            
            # 计算中心位置
            h_center = (h_scroll.maximum() + h_scroll.minimum()) // 2
            v_center = (v_scroll.maximum() + v_scroll.minimum()) // 2
            
            h_scroll.setValue(h_center)
            v_scroll.setValue(v_center)
            
            # 提供视觉反馈
            self.status_feedback("图片已重置到中心位置")
            
            event.accept()
            
    def status_feedback(self, message):
        """显示状态反馈信息"""
        try:
            # 临时显示状态信息
            original_text = self.info_label.text()
            self.info_label.setText(f"✓ {message}")
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    font-size: 12px;
                    padding: 5px;
                    font-weight: bold;
                }
            """)
            
            # 2秒后恢复原始信息
            QTimer.singleShot(2000, lambda: [
                self.info_label.setText(original_text),
                self.info_label.setStyleSheet("""
                    QLabel {
                        color: #6c757d;
                        font-size: 12px;
                        padding: 5px;
                    }
                """)
            ])
        except:
            pass  # 忽略错误，避免影响主要功能
            
    def wheelEvent(self, event):
        """鼠标滚轮事件"""
        if event.modifiers() == Qt.ControlModifier:
            # Ctrl + 滚轮进行缩放
            angle_delta = event.angleDelta().y()
            if angle_delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # 普通滚动
            super().wheelEvent(event)
            
    def keyPressEvent(self, event):
        """键盘事件 - 支持方向键拖动"""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.zoom_in()
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
            elif event.key() == Qt.Key_0:
                self.reset_zoom()
            elif event.key() == Qt.Key_F:
                self.fit_to_window()
        elif event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() in [Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]:
            # 方向键移动图片
            self.move_image_with_keys(event.key())
        else:
            super().keyPressEvent(event)
            
    def move_image_with_keys(self, key):
        """使用方向键移动图片"""
        h_scroll = self.scroll_area.horizontalScrollBar()
        v_scroll = self.scroll_area.verticalScrollBar()
        
        step = 50  # 移动步长
        
        if key == Qt.Key_Left:
            h_scroll.setValue(h_scroll.value() - step)
        elif key == Qt.Key_Right:
            h_scroll.setValue(h_scroll.value() + step)
        elif key == Qt.Key_Up:
            v_scroll.setValue(v_scroll.value() - step)
        elif key == Qt.Key_Down:
            v_scroll.setValue(v_scroll.value() + step)
        else:
            super().keyPressEvent(event)
            
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 可以在这里添加自动适应窗口的逻辑

class FileChatBubble(QFrame):
    """文件消息气泡组件 - 支持点击下载"""
    def __init__(self, file_info, is_user=True, sender_name="", timestamp="", profession="", parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.file_info = file_info
        self.sender_name = sender_name
        self.timestamp = timestamp
        self.profession = profession
        
        # 从文件信息中提取数据
        self.file_name = file_info.get('file_name', '未知文件')
        self.file_url = file_info.get('file_url', '')
        self.file_size = file_info.get('file_size', 0)
        self.content = file_info.get('content', f"📎 {self.file_name}")
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.setStyleSheet("""
            FileChatBubble {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.setup_ui()
        
    def get_file_type_style(self):
        """根据文件类型获取专门的样式配置"""
        if not self.file_name:
            return self.get_default_style()
        
        file_ext = os.path.splitext(self.file_name.lower())[1]
        
        # 获取对应的 SVG 图标路径
        icon_path = get_file_icon_path(self.file_name)
        
        # PDF文件 - 白色主题（统一样式）
        if file_ext in ['.pdf']:
            return {
                'icon_path': icon_path,
                'name': 'PDF文档',
                'bg_color': 'white',
                'icon_bg': '#c0392b' if self.is_user else '#bd2130',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#c0392b'
            }
        # Word文档 - 白色主题（统一样式）
        elif file_ext in ['.doc', '.docx']:
            return {
                'icon_path': icon_path,
                'name': 'Word文档',
                'bg_color': 'white',
                'icon_bg': '#2980b9' if self.is_user else '#0056b3',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#2980b9'
            }
        # Excel表格 - 白色主题（统一样式）
        elif file_ext in ['.xls', '.xlsx']:
            return {
                'icon_path': icon_path,
                'name': 'Excel表格',
                'bg_color': 'white',
                'icon_bg': '#229954' if self.is_user else '#1e7e34',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#229954'
            }
        # PowerPoint演示 - 白色主题（统一样式）
        elif file_ext in ['.ppt', '.pptx']:
            return {
                'icon_path': icon_path,
                'name': 'PPT演示',
                'bg_color': 'white',
                'icon_bg': '#e67e22' if self.is_user else '#e8590c',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#e67e22'
            }
        # 文本文件 - 白色主题（统一样式）
        elif file_ext in ['.txt', '.md', '.rtf']:
            return {
                'icon_path': icon_path,
                'name': '文本文档',
                'bg_color': 'white',
                'icon_bg': '#6c757d' if self.is_user else '#5a6268',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#6c757d'
            }
        # 代码文件 - 白色主题（统一样式）
        elif file_ext in ['.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml', '.java', '.cpp', '.c']:
            return {
                'icon_path': icon_path,
                'name': '代码文件',
                'bg_color': 'white',
                'icon_bg': '#8e44ad' if self.is_user else '#59359a',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#8e44ad'
            }
        # 压缩文件 - 白色主题（统一样式）
        elif file_ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return {
                'icon_path': icon_path,
                'name': '压缩文件',
                'bg_color': 'white',
                'icon_bg': '#d4af37' if self.is_user else '#e0a800',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#d4af37'
            }
        # 音频文件 - 白色主题（统一样式）
        elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']:
            return {
                'icon_path': icon_path,
                'name': '音频文件',
                'bg_color': 'white',
                'icon_bg': '#c2185b' if self.is_user else '#b02a5b',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#c2185b'
            }
        # 视频文件 - 白色主题（统一样式）
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']:
            return {
                'icon_path': icon_path,
                'name': '视频文件',
                'bg_color': 'white',
                'icon_bg': '#34495e' if self.is_user else '#495057',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#34495e'
            }
        # 图片文件 - 白色主题（统一样式）
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']:
            return {
                'icon_path': icon_path,
                'name': '图片文件',
                'bg_color': 'white',
                'icon_bg': '#16a085' if self.is_user else '#1ba085',
                'text_color': '#1C1C1C',  # 改为深色文字
                'border_color': '#16a085'
            }
        else:
            return self.get_default_style()
    
    def get_default_style(self):
        """默认文件样式（统一样式）"""
        # 获取默认的未知文件图标
        icon_path = get_file_icon_path('unknown')
        
        return {
            'icon_path': icon_path,
            'name': '文件',
            'bg_color': 'white',
            'icon_bg': '#7f8c8d' if self.is_user else '#5a6268',
            'text_color': '#1C1C1C',  # 改为深色文字
            'border_color': '#7f8c8d'
        }
    
    def setup_ui(self):
        """设置UI界面"""
        # 获取文件类型样式
        file_style = self.get_file_type_style()
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 消息信息栏（发送者和时间）
        if not self.is_user:
            info_layout = QHBoxLayout()
            info_layout.setContentsMargins(50, 0, 0, 0)
            
            sender_label = QLabel(self.sender_name)
            sender_label.setFont(QFont("Microsoft YaHei UI", 8))
            sender_label.setStyleSheet("color: #666666;")
            
            time_label = QLabel(self.timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #999999;")
            
            info_layout.addWidget(sender_label)
            info_layout.addStretch()
            info_layout.addWidget(time_label)
            
            layout.addLayout(info_layout)
        
        # 消息主体布局
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(10)
        
        # 创建文件消息容器 - 使用统一样式（无边框）
        file_container = QFrame()
        file_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        file_container.setStyleSheet(f"""
            QFrame {{
                background-color: {file_style['bg_color']};
                border: none;
                border-radius: 18px;
            }}
        """)
        
        container_layout = QVBoxLayout(file_container)
        container_layout.setContentsMargins(15, 12, 15, 12)
        container_layout.setSpacing(8)
        
        # 文件显示布局
        file_layout = QHBoxLayout()
        file_layout.setSpacing(12)
        
        # 文件图标容器
        icon_container = QLabel()
        icon_container.setFixedSize(80, 80)
        icon_container.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border-radius: 40px;
                border: none;
            }
        """)
        
        # 创建一个内部容器来显示 SVG 图标
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(15, 15, 15, 15)
        icon_inner_layout.setAlignment(Qt.AlignCenter)
        
        # 加载并显示 SVG 图标
        svg_icon = QSvgWidget(file_style['icon_path'])
        svg_icon.setFixedSize(50, 50)  # SVG 图标大小
        
        # 设置 SVG 样式，确保背景透明
        svg_icon.setStyleSheet("""
            QSvgWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        icon_inner_layout.addWidget(svg_icon)
        
        # 文件信息布局
        file_info_layout = QVBoxLayout()
        file_info_layout.setSpacing(4)
        
        # 文件类型标签
        file_type_label = QLabel(file_style['name'])
        file_type_label.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
        file_type_label.setStyleSheet(f"""
            QLabel {{
                color: {file_style['text_color']};
                background: transparent;
            }}
        """)
        
        # 文件名标签（截断显示）
        file_name_display = self.file_name
        if len(file_name_display) > 20:
            file_name_display = file_name_display[:17] + "..."
        
        file_name_label = QLabel(file_name_display)
        file_name_label.setFont(QFont("Microsoft YaHei UI", 10))
        file_name_label.setStyleSheet(f"""
            QLabel {{
                color: {file_style['text_color']};
                background: transparent;
                opacity: 0.8;
            }}
        """)
        
        # 文件大小标签
        size_text = self.format_file_size(self.file_size)
        file_size_label = QLabel(size_text)
        file_size_label.setFont(QFont("Microsoft YaHei UI", 9))
        file_size_label.setStyleSheet(f"""
            QLabel {{
                color: {file_style['text_color']};
                background: transparent;
                opacity: 0.7;
            }}
        """)
        
        file_info_layout.addWidget(file_type_label)
        file_info_layout.addWidget(file_name_label)
        file_info_layout.addWidget(file_size_label)
        file_info_layout.addStretch()
        
        file_layout.addWidget(icon_container)
        file_layout.addLayout(file_info_layout)
        
        # 下载按钮 - 使用SVG图标
        download_btn = QPushButton()
        download_btn.setFixedSize(40, 40)
        download_btn.setCursor(QCursor(Qt.PointingHandCursor))
        download_btn.setToolTip("下载文件")
        
        # 设置SVG图标
        download_icon_path = os.path.join(os.path.dirname(get_file_icon_path('download')), '下载.svg')
        if os.path.exists(download_icon_path):
            download_btn.setIcon(QIcon(download_icon_path))
            download_btn.setIconSize(QSize(20, 20))
        else:
            # 如果SVG文件不存在，回退到emoji
            download_btn.setText("📥")
            download_btn.setFont(QFont("Microsoft YaHei UI", 14))
        
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                color: #333333;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.2);
                transform: scale(0.95);
            }
        """)
        download_btn.clicked.connect(self.download_file)
        
        file_layout.addWidget(download_btn)
        
        container_layout.addLayout(file_layout)
        
        # 创建头像
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        
        # 获取头像路径
        if self.is_user:
            # 当前用户头像：优先根据职业选择，默认使用系统架构师
            if self.profession:
                avatar_path = config.get_avatar_by_profession(self.profession)
                print(f"📎 用户文件头像: 职业={self.profession}, 路径={avatar_path}")
            else:
                avatar_path = config.get_avatar_path('user')
                print(f"📎 用户文件头像: 默认路径={avatar_path}")
        else:
            # 其他用户头像：优先根据职业选择，默认使用网络规划设计师
            if self.profession:
                avatar_path = config.get_avatar_by_profession(self.profession)
                print(f"📎 其他用户文件头像: 职业={self.profession}, 路径={avatar_path}")
            else:
                avatar_path = config.get_avatar_path('online_user')
                print(f"📎 其他用户文件头像: 默认路径={avatar_path}")
        
        # 使用统一的头像处理函数
        avatar_pixmap = config.create_rounded_avatar(avatar_path, 40)
        avatar.setPixmap(avatar_pixmap)
        avatar.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        # 设置最终布局
        if self.is_user:
            msg_layout.addStretch(1)  # 左侧弹性空间
            msg_layout.addWidget(file_container)  # 文件消息气泡
            msg_layout.addWidget(avatar)  # 头像靠右
        else:
            msg_layout.addWidget(avatar)  # 头像靠左
            msg_layout.addWidget(file_container)  # 文件消息气泡
            msg_layout.addStretch(1)  # 右侧弹性空间
        
        # 用户消息显示时间在右侧
        if self.is_user and self.timestamp:
            time_layout = QHBoxLayout()
            time_layout.setContentsMargins(0, 0, 50, 0)
            time_layout.addStretch()
            
            time_label = QLabel(self.timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #999999;")
            time_layout.addWidget(time_label)
            
            layout.addLayout(msg_layout)
            layout.addLayout(time_layout)
        else:
            layout.addLayout(msg_layout)
    
    def get_file_icon(self):
        """根据文件类型返回对应的图标路径 - 使用新的 SVG 图标系统"""
        return self.get_file_type_style()['icon_path']
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def download_file(self):
        """下载文件 - 直接下载到本地"""
        if not self.file_url:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "下载失败", "文件URL不存在")
            return
        
        try:
            print(f"📥 准备下载文件: {self.file_name}")
            print(f"🔗 文件URL: {self.file_url}")
            
            # 查找父窗口中的OnlineChatWidget
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, 'download_file_from_chat'):
                    # 找到了OnlineChatWidget，调用其下载方法
                    parent_widget.download_file_from_chat(self.file_url, self.file_name)
                    return
                parent_widget = parent_widget.parent()
            
            # 如果找不到父窗口的下载方法，则回退到浏览器下载
            print("⚠️ 未找到父窗口下载方法，回退到浏览器下载")
            
            # 构建完整的文件URL
            from resources.assets.config.online_chat_config import CHAT_API_BASE_URL
            if self.file_url.startswith('http'):
                full_url = self.file_url
            else:
                full_url = f"{CHAT_API_BASE_URL}{self.file_url}"
            
            # 使用浏览器打开
            from PyQt5.QtCore import QUrl
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(full_url))
            
            # 显示提示
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "文件已打开", 
                                  f"文件 {self.file_name} 已在浏览器中打开\n"
                                  f"如果是图片或PDF，将在浏览器中预览\n"
                                  f"其他文件类型将自动下载")
            
        except Exception as e:
            print(f"❌ 文件下载失败: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "下载失败", f"文件下载失败：{str(e)}")
    
    def mousePressEvent(self, event):
        """鼠标点击事件 - 已禁用下载功能"""
        # 不再处理下载，只调用父类方法
        super().mousePressEvent(event)

class PasteEnabledLineEdit(QLineEdit):
    """支持粘贴文件的输入框"""
    file_pasted = pyqtSignal(list)  # 发送粘贴的文件路径列表
    image_pasted = pyqtSignal(QPixmap)  # 发送粘贴的图片
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # 启用拖拽
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用自定义右键菜单
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def keyPressEvent(self, event):
        """处理按键事件，特别是粘贴操作"""
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            # Ctrl+V 粘贴
            try:
                self.handle_paste()
                return
            except Exception as e:
                print(f"❌ 自定义粘贴处理失败: {e}")
                # 如果自定义粘贴失败，回退到默认粘贴
                print("🔄 回退到默认粘贴方法")
                super().keyPressEvent(event)
                return
        
        # 其他按键事件正常处理
        super().keyPressEvent(event)
    
    def handle_paste(self):
        """处理粘贴操作"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        print(f"📋 剪贴板内容检测: hasUrls={mime_data.hasUrls()}, hasImage={mime_data.hasImage()}, hasText={mime_data.hasText()}")
        
        # 优先检查是否有文件路径
        if mime_data.hasUrls():
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                print(f"📋 粘贴文件: {file_paths}")
                self.file_pasted.emit(file_paths)
                return
        
        # 检查是否有图片数据
        if mime_data.hasImage():
            print("📋 检测到剪贴板中有图片数据")
            
            # 尝试多种方式获取图片
            pixmap = None
            
            # 方法1：直接从剪贴板获取QPixmap
            try:
                pixmap = clipboard.pixmap()
                if not pixmap.isNull():
                    print("📋 成功通过pixmap()获取图片")
                else:
                    print("📋 pixmap()返回空图片，尝试其他方法")
                    pixmap = None
            except Exception as e:
                print(f"📋 pixmap()方法失败: {e}")
            
            # 方法2：从QImage转换
            if pixmap is None or pixmap.isNull():
                try:
                    image = clipboard.image()
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        if not pixmap.isNull():
                            print("📋 成功通过QImage转换获取图片")
                        else:
                            print("📋 QImage转换为QPixmap失败")
                            pixmap = None
                    else:
                        print("📋 clipboard.image()返回空图片")
                except Exception as e:
                    print(f"📋 QImage转换方法失败: {e}")
            
            # 如果成功获取图片，发送信号
            if pixmap and not pixmap.isNull():
                print(f"📋 图片尺寸: {pixmap.width()}x{pixmap.height()}")
                self.image_pasted.emit(pixmap)
                return
            else:
                print("⚠️ 所有图片获取方法都失败了")
        
        # 检查是否有文本（可能是文件路径）
        if mime_data.hasText():
            text = mime_data.text().strip()
            print(f"📋 检测到文本内容: {text[:100]}...")  # 只显示前100个字符
            
            # 检查是否是文件路径
            if os.path.exists(text) and os.path.isfile(text):
                print(f"📋 识别为文件路径: {text}")
                self.file_pasted.emit([text])
                return
            else:
                print("📋 文本不是有效文件路径，执行普通文本粘贴")
        
        # 如果都不是，执行正常的文本粘贴
        print("📋 执行默认文本粘贴")
        try:
            self.paste()  # 使用Qt的粘贴方法
        except Exception as e:
            print(f"❌ 默认粘贴也失败了: {e}")
            # 最后的备用方案
            try:
                clipboard = QApplication.clipboard()
                if clipboard.mimeData().hasText():
                    text = clipboard.text()
                    self.insert(text)
                    print("✅ 使用insert方法成功粘贴文本")
            except Exception as e2:
                print(f"❌ 所有粘贴方法都失败了: {e2}")
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        from PyQt5.QtWidgets import QMenu, QAction
        
        menu = QMenu(self)
        
        # 添加标准菜单项
        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.handle_paste)
        menu.addAction(paste_action)
        
        paste_text_action = QAction("粘贴文本", self)
        paste_text_action.triggered.connect(self.paste_text_only)
        menu.addAction(paste_text_action)
        
        # 检查剪贴板内容
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            paste_image_action = QAction("粘贴图片", self)
            paste_image_action.triggered.connect(self.paste_image_only)
            menu.addAction(paste_image_action)
        
        if mime_data.hasUrls():
            paste_file_action = QAction("粘贴文件", self)
            paste_file_action.triggered.connect(self.paste_files_only)
            menu.addAction(paste_file_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    def paste_text_only(self):
        """只粘贴文本内容"""
        clipboard = QApplication.clipboard()
        if clipboard.mimeData().hasText():
            try:
                self.paste()
                print("✅ 强制文本粘贴成功")
            except Exception as e:
                print(f"❌ 强制文本粘贴失败: {e}")
    
    def paste_image_only(self):
        """只粘贴图片内容"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            print("📋 强制图片粘贴")
            
            # 尝试获取图片
            pixmap = None
            try:
                pixmap = clipboard.pixmap()
                if pixmap.isNull():
                    image = clipboard.image()
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
            except Exception as e:
                print(f"❌ 强制图片粘贴失败: {e}")
                return
            
            if pixmap and not pixmap.isNull():
                self.image_pasted.emit(pixmap)
                print("✅ 强制图片粘贴成功")
            else:
                print("❌ 无法获取图片数据")
    
    def paste_files_only(self):
        """只粘贴文件内容"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasUrls():
            file_paths = []
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                self.file_pasted.emit(file_paths)
                print(f"✅ 强制文件粘贴成功: {file_paths}")
            else:
                print("❌ 没有有效的文件路径")
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖拽放下事件"""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                print(f"🎯 拖拽文件: {file_paths}")
                self.file_pasted.emit(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

class OnlineModernButton(QPushButton):
    """现代风格按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(45)
        self.setFont(QFont("Microsoft YaHei UI", 10))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 22px;
                padding: 5px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #a9dfbf;
            }
        """)

class FileUploadDialog(QDialog):
    """文件上传对话框"""
    file_uploaded = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件上传")
        self.setFixedSize(600, 500)
        # 修改窗口标志，防止影响父窗口
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        # 设置为模态对话框，但不阻塞其他应用程序
        self.setModal(True)
        # 防止关闭事件传播
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 文件上传组件
        self.upload_widget = FileUploadWidget()
        self.upload_widget.file_uploaded.connect(self.on_file_uploaded)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        
        layout.addWidget(self.upload_widget)
        layout.addWidget(button_box)
        
    def on_file_uploaded(self, file_info):
        """文件上传完成"""
        self.file_uploaded.emit(file_info)
        
    def set_auth_headers(self, headers):
        """设置认证头"""
        if hasattr(self, 'upload_widget'):
            self.upload_widget.set_headers(headers)
        
    def closeEvent(self, event):
        """重写关闭事件，防止事件传播"""
        print("🔒 FileUploadDialog 正在关闭，阻止事件传播")
        # 停止事件传播到父窗口
        event.accept()
        # 隐藏而不是销毁窗口
        self.hide()
        # 不调用父类的closeEvent，防止事件传播
        # super().closeEvent(event)  # 注释掉这行

class OnlineChatAPI(QThread):
    """在线聊天API处理线程"""
    message_received = pyqtSignal(dict)
    messages_loaded = pyqtSignal(list)
    online_users_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_url = config.CHAT_API_BASE_URL  # 使用配置文件中的服务器地址
        self.token = None  # 需要JWT Token
        self.room_id = config.CHAT_ROOM_ID  # 默认聊天室
        self.token_manager = TokenManager()  # 添加Token管理器
        self.auto_load_token()  # 自动加载token
        
    def auto_load_token(self):
        """自动从JSON文件加载token"""
        try:
            token = self.token_manager.get_token()
            if token:
                self.token = token
                user_info = self.token_manager.get_user_info()
                print(f"自动加载token成功，用户: {user_info.get('username', 'Unknown')}")
                return True
            else:
                print("未能从配置文件中获取token")
                return False
        except Exception as e:
            print(f"自动加载token失败: {str(e)}")
            return False
    
    def refresh_token(self):
        """刷新token"""
        return self.auto_load_token()
    
    def set_token(self, token):
        """设置JWT Token"""
        self.token = token
        
    def set_room_id(self, room_id):
        """设置聊天室ID"""
        self.room_id = room_id
        
    def get_headers(self):
        """获取请求头"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def send_message(self, content, message_type="text", reply_to=None, file_info=None):
        """发送消息 - 根据分析报告优化"""
        try:
            url = f"{self.base_url}/api/chat/send"
            params = {"room_id": self.room_id}
            
            # 根据分析报告构建完整的消息数据结构
            data = {
                "message_type": message_type,
                "content": content
            }
            
            # 添加回复消息ID（如果存在）
            if reply_to:
                data["reply_to"] = reply_to
            
            # 文件信息处理（用于文件消息）
            if file_info:
                # 文件信息应该通过上传接口处理，这里只传递文件相关的内容
                if message_type in ["file", "image"]:
                    data["content"] = f"发送了文件: {file_info.get('file_name', '未知文件')}"
                
            print(f"发送消息请求: URL={url}, 参数={params}, 数据={data}")
                
            response = requests.post(url, json=data, headers=self.get_headers(), 
                                   params=params, timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
            message_data = response.json()
            
            # 验证响应数据结构（根据分析报告的ChatMessage模型）
            required_fields = ['id', 'sender_id', 'sender_name', 'content', 'timestamp']
            for field in required_fields:
                if field not in message_data:
                    print(f"警告: 响应缺少必需字段 '{field}'")
            
            print(f"消息发送成功: ID={message_data.get('id', 'N/A')}")
            self.message_received.emit(message_data)
            
        except requests.exceptions.Timeout:
            self.error_occurred.emit("发送消息超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("无法连接到服务器，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.error_occurred.emit("认证失败，请重新登录")
            elif e.response.status_code == 403:
                self.error_occurred.emit("权限不足，无法发送消息")
            elif e.response.status_code == 413:
                self.error_occurred.emit("消息内容过大，请减少内容长度")
            else:
                self.error_occurred.emit(f"发送消息失败: HTTP {e.response.status_code}")
        except Exception as e:
            self.error_occurred.emit(f"发送消息失败: {str(e)}")
    
    def load_messages(self, limit=50, before=None):
        """加载消息历史 - 根据分析报告优化"""
        try:
            url = f"{self.base_url}/api/chat/messages"
            
            # 根据分析报告优化参数构建
            params = {
                "room_id": self.room_id,
                "limit": min(limit, 100)  # 限制单次加载量，避免过载
            }
            
            # 分页支持（基于消息ID）
            if before:
                params["before"] = before
                
            print(f"加载消息请求: URL={url}, 参数={params}")
                
            response = requests.get(url, headers=self.get_headers(), 
                                  params=params, timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
            messages = response.json()
            
            # 验证消息数据结构
            if not isinstance(messages, list):
                print("警告: 服务器返回的不是消息列表格式")
                messages = []
            
            # 验证每条消息的数据完整性
            valid_messages = []
            for msg in messages:
                if self._validate_message_structure(msg):
                    valid_messages.append(msg)
                else:
                    print(f"跳过无效消息: {msg}")
            
            print(f"成功加载 {len(valid_messages)} 条消息")
            self.messages_loaded.emit(valid_messages)
            
        except requests.exceptions.Timeout:
            self.error_occurred.emit("加载消息超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("无法连接到服务器，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.error_occurred.emit("认证失败，请重新登录")
            elif e.response.status_code == 403:
                self.error_occurred.emit("权限不足，无法获取消息")
            else:
                self.error_occurred.emit(f"加载消息失败: HTTP {e.response.status_code}")
        except Exception as e:
            self.error_occurred.emit(f"加载消息失败: {str(e)}")
    
    def _validate_message_structure(self, message):
        """验证消息数据结构完整性 - 根据分析报告的ChatMessage模型"""
        if not isinstance(message, dict):
            return False
        
        # 根据分析报告的必需字段
        required_fields = ['id', 'sender_id', 'sender_name', 'content', 'timestamp']
        for field in required_fields:
            if field not in message:
                print(f"消息缺少必需字段: {field}")
                return False
        
        # 验证消息类型
        message_type = message.get('message_type', 'text')
        valid_types = ['text', 'file', 'image', 'system']
        if message_type not in valid_types:
            print(f"无效的消息类型: {message_type}")
            return False
        
        # 验证时间戳格式
        timestamp = message.get('timestamp')
        if timestamp:
            try:
                from datetime import datetime
                # 尝试解析ISO格式时间戳
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except Exception:
                print(f"无效的时间戳格式: {timestamp}")
                return False
        
        return True
    
    def load_online_users(self):
        """加载在线用户列表"""
        try:
            url = f"{self.base_url}/api/chat/online-users"
            response = requests.get(url, headers=self.get_headers(), timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
            users = response.json()
            self.online_users_loaded.emit(users)
            
        except Exception as e:
            self.error_occurred.emit(f"加载在线用户失败: {str(e)}")
    
    def is_image_file(self, filename):
        """判断文件是否为图片"""
        if not filename:
            return False
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        ext = os.path.splitext(filename.lower())[1]
        return ext in image_extensions
    
    def upload_file_and_send(self, file_path, room_id="global"):
        """上传文件并发送消息 - 根据分析报告实现"""
        try:
            url = f"{self.base_url}/api/chat/upload"
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.error_occurred.emit("文件不存在")
                return
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            max_size = 10 * 1024 * 1024  # 10MB 限制（按照分析报告）
            if file_size > max_size:
                self.error_occurred.emit(f"文件大小超过限制({max_size // (1024*1024)}MB)")
                return
            
            # 获取文件信息
            filename = os.path.basename(file_path)
            
            # 检查文件类型
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',  # 图片
                'application/pdf', 'text/plain',  # 文档
                'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # Word
                'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # Excel
            ]
            
            # 根据文件扩展名判断MIME类型
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type not in allowed_types:
                # 特殊处理一些常见类型
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    content_type = 'image/jpeg'
                elif ext == '.png':
                    content_type = 'image/png'
                elif ext == '.gif':
                    content_type = 'image/gif'
                elif ext == '.webp':
                    content_type = 'image/webp'
                elif ext == '.pdf':
                    content_type = 'application/pdf'
                elif ext == '.txt':
                    content_type = 'text/plain'
                elif ext in ['.doc', '.docx']:
                    content_type = 'application/msword'
                elif ext in ['.xls', '.xlsx']:
                    content_type = 'application/vnd.ms-excel'
                else:
                    self.error_occurred.emit(f"不支持的文件类型: {ext}")
                    return
            
            print(f"📤 开始上传文件: {filename}, 大小: {file_size}, 类型: {content_type}")
            
            # 准备multipart/form-data请求
            headers = self.get_headers()
            # 移除Content-Type，让requests自动设置multipart边界
            if 'Content-Type' in headers:
                del headers['Content-Type']
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, content_type)
                }
                data = {
                    'room_id': room_id
                }
                
                response = requests.post(url, files=files, data=data, headers=headers, 
                                       timeout=config.CHAT_API_TIMEOUT * 2)  # 文件上传需要更长时间
            
            response.raise_for_status()
            
            # 解析响应 - 应该返回ChatMessage格式
            message_data = response.json()
            
            # 自动设置消息类型：如果是图片文件，设置为image类型
            if self.is_image_file(message_data.get('file_name', filename)):
                message_data['message_type'] = 'image'
                print(f"🖼️ 检测到图片文件，设置消息类型为: image")
            elif 'message_type' not in message_data:
                message_data['message_type'] = 'file'
                print(f"📄 设置消息类型为: file")
            
            # 验证响应数据结构
            if not self._validate_message_structure(message_data):
                print("警告: 文件上传响应数据结构不完整")
            
            print(f"✅ 文件上传成功: {message_data.get('file_name', filename)}")
            print(f"   文件URL: {message_data.get('file_url', 'N/A')}")
            print(f"   消息ID: {message_data.get('id', 'N/A')}")
            print(f"   消息类型: {message_data.get('message_type', 'N/A')}")
            
            # 发出消息接收信号
            self.message_received.emit(message_data)
            
        except requests.exceptions.Timeout:
            self.error_occurred.emit("文件上传超时，请检查网络连接或文件大小")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("无法连接到服务器，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 413:
                self.error_occurred.emit("文件大小超过服务器限制(10MB)")
            elif e.response.status_code == 415:
                self.error_occurred.emit("不支持的文件类型")
            elif e.response.status_code == 401:
                self.error_occurred.emit("认证失败，请重新登录")
            elif e.response.status_code == 403:
                self.error_occurred.emit("权限不足，无法上传文件")
            else:
                self.error_occurred.emit(f"文件上传失败: HTTP {e.response.status_code}")
        except Exception as e:
            self.error_occurred.emit(f"文件上传失败: {str(e)}")
    
    def send_heartbeat(self):
        """发送心跳保持在线状态"""
        try:
            url = f"{self.base_url}/api/chat/heartbeat"
            response = requests.post(url, headers=self.get_headers(), timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
        except Exception as e:
            print(f"心跳发送失败: {str(e)}")
    
    def delete_message(self, message_id, room_id="global"):
        """删除消息 - 根据分析报告实现软删除"""
        try:
            url = f"{self.base_url}/api/chat/messages/{message_id}"
            params = {"room_id": room_id}
            
            print(f"🗑️ 删除消息请求: ID={message_id}, 房间={room_id}")
            
            response = requests.delete(url, headers=self.get_headers(), 
                                     params=params, timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 消息删除成功: {result}")
            return True
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("❌ 消息删除失败: 只能删除自己的消息")
                self.error_occurred.emit("只能删除自己的消息")
            elif e.response.status_code == 404:
                print("❌ 消息删除失败: 消息不存在")
                self.error_occurred.emit("消息不存在或已被删除")
            elif e.response.status_code == 401:
                print("❌ 消息删除失败: 认证失败")
                self.error_occurred.emit("认证失败，请重新登录")
            else:
                print(f"❌ 消息删除失败: HTTP {e.response.status_code}")
                self.error_occurred.emit(f"删除消息失败: HTTP {e.response.status_code}")
        except Exception as e:
            print(f"❌ 消息删除失败: {str(e)}")
            self.error_occurred.emit(f"删除消息失败: {str(e)}")
        
        return False
    
    def get_chat_stats(self):
        """获取聊天统计信息 - 根据分析报告实现"""
        try:
            url = f"{self.base_url}/api/chat/stats"
            
            response = requests.get(url, headers=self.get_headers(), 
                                  timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
            stats = response.json()
            print(f"📊 聊天统计: {stats}")
            return stats
            
        except Exception as e:
            print(f"获取聊天统计失败: {str(e)}")
            return None
    
    def download_file_direct(self, file_url, file_name, save_path=None):
        """直接下载文件到本地"""
        try:
            # 构建完整的文件URL
            if file_url.startswith('http'):
                full_url = file_url
            else:
                full_url = f"{self.base_url}{file_url}"
            
            print(f"📥 开始下载文件: {file_name}")
            print(f"🔗 文件URL: {full_url}")
            
            # 如果没有指定保存路径，使用默认下载目录
            if not save_path:
                # 获取用户的下载目录
                downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                if not os.path.exists(downloads_dir):
                    downloads_dir = os.path.expanduser("~")  # 如果下载目录不存在，使用用户主目录
                save_path = os.path.join(downloads_dir, file_name)
            
            # 如果文件已存在，添加数字后缀
            base_path = save_path
            counter = 1
            while os.path.exists(save_path):
                name, ext = os.path.splitext(base_path)
                save_path = f"{name}({counter}){ext}"
                counter += 1
            
            # 下载文件
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            response = requests.get(full_url, headers=headers, 
                                  timeout=config.CHAT_API_TIMEOUT * 3,  # 下载需要更长时间
                                  stream=True)  # 流式下载，支持大文件
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 写入文件
            with open(save_path, 'wb') as f:
                downloaded_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 打印下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"📥 下载进度: {progress:.1f}% ({downloaded_size}/{total_size} 字节)")
            
            print(f"✅ 文件下载成功: {save_path}")
            return save_path
            
        except requests.exceptions.Timeout:
            print(f"❌ 文件下载超时: {file_name}")
            raise Exception("下载超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            print(f"❌ 网络连接错误: {file_name}")
            raise Exception("网络连接失败，请检查网络设置")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"❌ 文件不存在: {file_name}")
                raise Exception("文件不存在或已被删除")
            elif e.response.status_code == 403:
                print(f"❌ 无权限访问文件: {file_name}")
                raise Exception("无权限访问此文件")
            else:
                print(f"❌ HTTP错误 {e.response.status_code}: {file_name}")
                raise Exception(f"下载失败: HTTP {e.response.status_code}")
        except OSError as e:
            print(f"❌ 文件写入错误: {str(e)}")
            raise Exception(f"文件保存失败: {str(e)}")
        except Exception as e:
            print(f"❌ 文件下载失败: {str(e)}")
            raise Exception(f"下载失败: {str(e)}")

class OnlineChatWidget(QWidget):
    """在线聊天窗口组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connection_error = False
        self.current_user = ""
        self._is_drag = False
        self._drag_pos = QPoint()
        
        # 初始化API
        self.api = OnlineChatAPI()
        
        # 初始化Token管理器
        self.token_manager = TokenManager()
        
        # 初始化用户身份缓存系统
        self.user_profession_cache = {}  # 用户名 -> 职业映射
        self.user_avatar_cache = {}      # 用户名 -> 头像路径映射
        
        # 初始化心跳定时器
        self.heartbeat_timer = QTimer()
        
        # 初始化自动刷新定时器
        self.auto_refresh_timer = QTimer()
        
        # 初始化窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(*config.CHAT_WINDOW_SIZE)
        
        # 创建UI
        self.setup_ui()
        
        # 设置连接
        self.setup_connections()
        
        # 初始化界面状态
        self.status_label.setText("正在连接...")
        self.online_count_label.setText("等待连接")
        
        # 自动加载用户token
        self.load_user_from_token()
        
        # 初始化用户身份映射
        self.initialize_user_identity_mapping()
    
    def initialize_user_identity_mapping(self):
        """初始化用户身份映射"""
        try:
            # 从token管理器获取当前用户职业信息
            user_info = self.token_manager.get_user_info()
            if user_info and user_info.get('username') and user_info.get('role'):
                username = user_info.get('username')
                profession = user_info.get('role')
                self.update_user_profession_cache(username, profession)
                print(f"🎯 从token初始化用户身份: {username} -> {profession}")
            
            # 从桌面管理器获取角色数据（如果可用）
            self.load_user_profession_from_desktop_manager()
            
            print(f"✅ 用户身份映射初始化完成，缓存用户数: {len(self.user_profession_cache)}")
        except Exception as e:
            print(f"❌ 用户身份映射初始化失败: {str(e)}")
    
    def load_user_profession_from_desktop_manager(self):
        """从桌面管理器加载用户职业信息"""
        try:
            # 尝试从received_tasks.json文件读取用户角色信息
            import json
            if os.path.exists('received_tasks.json'):
                with open('received_tasks.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_info = data.get('user_info', {})
                    user_data = user_info.get('user', {})
                    if user_data.get('username') and user_data.get('role'):
                        username = user_data.get('username')
                        profession = user_data.get('role')
                        self.update_user_profession_cache(username, profession)
                        print(f"🎯 从桌面管理器加载用户身份: {username} -> {profession}")
        except Exception as e:
            print(f"⚠️ 从桌面管理器加载用户身份失败: {str(e)}")
    
    def update_user_profession_cache(self, username, profession):
        """更新用户职业缓存"""
        if username and profession:
            self.user_profession_cache[username] = profession
            # 同时缓存头像路径
            avatar_path = config.get_avatar_by_profession(profession)
            self.user_avatar_cache[username] = avatar_path
            print(f"📝 用户职业缓存更新: {username} -> {profession} -> {avatar_path}")
    
    def get_user_profession(self, username):
        """获取用户职业信息"""
        if not username:
            return None
            
        # 1. 从缓存中查找
        if username in self.user_profession_cache:
            profession = self.user_profession_cache[username]
            print(f"🎯 从缓存获取用户职业: {username} -> {profession}")
            return profession
        
        # 2. 如果是当前用户，从token获取
        if username == self.current_user:
            try:
                user_info = self.token_manager.get_user_info()
                if user_info and user_info.get('role'):
                    profession = user_info.get('role')
                    self.update_user_profession_cache(username, profession)
                    print(f"🎯 从token获取当前用户职业: {username} -> {profession}")
                    return profession
            except Exception as e:
                print(f"⚠️ 从token获取用户职业失败: {e}")
        
        # 3. 使用配置文件中的智能职业识别系统
        profession = config.get_profession_by_priority(username)
        if profession:
            self.update_user_profession_cache(username, profession)
            print(f"🎯 智能识别用户职业: {username} -> {profession}")
            return profession
        
        # 4. 兜底：返回默认网络规划设计师
        profession = '网络规划设计师'
        self.update_user_profession_cache(username, profession)
        print(f"🎯 使用兜底职业: {username} -> {profession}")
        return profession
    
    
    def get_user_avatar_path(self, username, profession=None):
        """获取用户头像路径"""
        # 1. 从缓存中查找
        if username in self.user_avatar_cache:
            return self.user_avatar_cache[username]
        
        # 2. 根据职业获取头像
        if not profession:
            profession = self.get_user_profession(username)
        
        if profession:
            avatar_path = config.get_avatar_by_profession(profession)
            self.user_avatar_cache[username] = avatar_path
            return avatar_path
        
        # 3. 返回默认头像
        return config.get_avatar_path('online_user')

    def load_user_from_token(self):
        """从token加载用户信息"""
        try:
            user_info = self.token_manager.get_user_info()
            if user_info:
                self.current_user = user_info.get('username', '当前用户')
                print(f"从token加载用户信息成功: {self.current_user}")
                # 连接服务器
                self.check_server_connection()
                return True
            else:
                print("无法从token获取用户信息，使用默认用户名")
                self.current_user = "当前用户"  # 设置默认用户名
                # 连接服务器
                self.check_server_connection()
                return False
        except Exception as e:
            print(f"加载用户信息失败: {str(e)}")
            self.current_user = "当前用户"  # 设置默认用户名
            # 连接服务器
            self.check_server_connection()
            return False
    
    def refresh_user_token(self):
        """刷新用户token和信息"""
        if self.api.refresh_token():
            self.load_user_from_token()
            return True
        return False
        
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 主容器
        main_container = QFrame(self)
        main_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E8E8E8;
            }
        """)
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 标题栏
        self.create_title_bar(container_layout)
        
        # 加载指示器
        self.loading_indicator = OnlineLoadingIndicator()
        container_layout.addWidget(self.loading_indicator)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 聊天区域
        self.create_chat_area(content_layout)
        
        # 在线用户列表
        self.create_online_users_area(content_layout)
        
        container_layout.addLayout(content_layout)
        
        # 输入区域
        self.create_input_area(container_layout)
        
        # 添加主容器到主布局
        main_layout.addWidget(main_container)
        
        # 设置窗口大小
        self.setFixedSize(*config.CHAT_WINDOW_SIZE)
        
    def create_title_bar(self, layout):
        """创建标题栏"""
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid #E8E8E8;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(25, 15, 25, 15)
        
        # 标题和状态
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        title_label = QLabel("在线聊天室")
        title_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #1C1C1C;")
        
        self.status_label = QLabel("正在连接...")
        self.status_label.setFont(QFont("Microsoft YaHei UI", 9))
        self.status_label.setStyleSheet("color: #666666;")
        
        title_container.addWidget(title_label)
        title_container.addWidget(self.status_label)
        
        # 在线用户数显示
        self.online_count_label = QLabel("在线: 0")
        self.online_count_label.setFont(QFont("Microsoft YaHei UI", 10))
        self.online_count_label.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                background-color: #e8f5e8;
                padding: 5px 10px;
                border-radius: 15px;
            }
        """)
        
        # 关闭按钮
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFont(QFont("Arial", 16, QFont.Bold))
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                color: #666666;
                border-radius: 15px;
            }
            QToolButton:hover {
                background-color: #FFE1E1;
                color: #ff0000;
            }
        """)
        close_btn.clicked.connect(self.hide)
        
        title_layout.addLayout(title_container)
        title_layout.addStretch()
        title_layout.addWidget(self.online_count_label)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
    def create_chat_area(self, layout):
        """创建聊天区域"""
        chat_container = QFrame()
        chat_container.setStyleSheet("QFrame { background-color: white; border: none; }")
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # 聊天滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #D0D0D0;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #B0B0B0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        self.chat_area = QWidget()
        self.chat_area.setStyleSheet("background-color: #F0F2F5;")
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_layout.setContentsMargins(10, 15, 10, 15)
        
        self.scroll.setWidget(self.chat_area)
        chat_layout.addWidget(self.scroll)
        
        layout.addWidget(chat_container, 3)  # 占据3/4的宽度
        
    def create_online_users_area(self, layout):
        """创建在线用户区域"""
        users_container = QFrame()
        users_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-left: 1px solid #E8E8E8;
            }
        """)
        users_layout = QVBoxLayout(users_container)
        users_layout.setContentsMargins(15, 10, 15, 10)
        users_layout.setSpacing(10)
        
        # 在线用户标题
        users_title = QLabel("在线用户")
        users_title.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        users_title.setStyleSheet("color: #1C1C1C; padding: 5px 0;")
        users_layout.addWidget(users_title)
        
        # 用户列表滚动区域
        self.users_scroll = QScrollArea()
        self.users_scroll.setWidgetResizable(True)
        self.users_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.users_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.users_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #E8E8E8;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #C0C0C0;
                min-height: 20px;
                border-radius: 3px;
            }
        """)
        
        self.users_area = QWidget()
        self.users_area.setStyleSheet("background-color: transparent;")
        self.users_layout = QVBoxLayout(self.users_area)
        self.users_layout.setAlignment(Qt.AlignTop)
        self.users_layout.setSpacing(5)
        self.users_layout.setContentsMargins(0, 0, 0, 0)
        
        self.users_scroll.setWidget(self.users_area)
        users_layout.addWidget(self.users_scroll)
        
        layout.addWidget(users_container, 1)  # 占据1/4的宽度
        
    def create_input_area(self, layout):
        """创建输入区域"""
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid #E8E8E8;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(30, 15, 30, 20)
        input_layout.setSpacing(10)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)
        
        # 文件上传按钮
        self.file_btn = QPushButton("📎 文件")
        self.file_btn.setFixedHeight(35)
        self.file_btn.setFont(QFont("Microsoft YaHei UI", 9))
        self.file_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #666666;
                border: 1px solid #E8E8E8;
                border-radius: 17px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.file_btn.clicked.connect(self.upload_file)
        
        # 电话按钮
        self.call_btn = QPushButton("电话")
        self.call_btn.setFixedHeight(35)
        self.call_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), '../../../resources/assets/images/file_icons/电话.svg')))
        self.call_btn.setIconSize(QSize(16, 16))
        self.call_btn.setFont(QFont("Microsoft YaHei UI", 9))
        self.call_btn.setToolTip("语音通话")
        self.call_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #666666;
                border: 1px solid #E8E8E8;
                border-radius: 17px;
                padding: 5px 15px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.call_btn.clicked.connect(self.start_voice_call)
        
        # 视频电话按钮
        self.video_call_btn = QPushButton("视频")
        self.video_call_btn.setFixedHeight(35)
        self.video_call_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), '../../../resources/assets/images/file_icons/视频电话.svg')))
        self.video_call_btn.setIconSize(QSize(16, 16))
        self.video_call_btn.setFont(QFont("Microsoft YaHei UI", 9))
        self.video_call_btn.setToolTip("视频通话")
        self.video_call_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #666666;
                border: 1px solid #E8E8E8;
                border-radius: 17px;
                padding: 5px 15px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.video_call_btn.clicked.connect(self.start_video_call)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setFixedHeight(35)
        self.refresh_btn.setFont(QFont("Microsoft YaHei UI", 9))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #666666;
                border: 1px solid #E8E8E8;
                border-radius: 17px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_chat)
        
        # 重连按钮
        self.reconnect_btn = QPushButton("🔌 重连")
        self.reconnect_btn.setFixedHeight(35)
        self.reconnect_btn.setFont(QFont("Microsoft YaHei UI", 9))
        self.reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #666666;
                border: 1px solid #E8E8E8;
                border-radius: 17px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.reconnect_btn.clicked.connect(self.reset_connection)
        
        toolbar_layout.addWidget(self.file_btn)
        toolbar_layout.addWidget(self.call_btn)
        toolbar_layout.addWidget(self.video_call_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addWidget(self.reconnect_btn)
        toolbar_layout.addStretch()
        
        input_layout.addLayout(toolbar_layout)
        
        # 输入行
        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(15)
        
        self.input = PasteEnabledLineEdit()
        self.input.setFixedHeight(45)
        self.input.setFont(QFont("Microsoft YaHei UI", 10))
        self.input.setPlaceholderText("输入消息或粘贴文件(Ctrl+V)...")
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #F0F2F5;
                border: 2px solid #F0F2F5;
                border-radius: 22px;
                padding: 0 20px;
                color: #1C1C1C;
            }
            QLineEdit:focus {
                border: 2px solid #2ecc71;
                background-color: white;
            }
        """)
        self.input.returnPressed.connect(self.send_message)
        
        # 连接粘贴信号
        self.input.file_pasted.connect(self.handle_pasted_files)
        self.input.image_pasted.connect(self.handle_pasted_image)
        
        self.send_btn = OnlineModernButton("发送")
        self.send_btn.setFixedWidth(120)
        self.send_btn.clicked.connect(self.send_message)
        
        input_row_layout.addWidget(self.input)
        input_row_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(input_row_layout)
        
        layout.addWidget(input_frame)
        
    def setup_connections(self):
        """设置信号连接"""
        # API信号连接
        self.api.message_received.connect(self.on_message_sent)
        self.api.messages_loaded.connect(self.on_messages_loaded)
        self.api.online_users_loaded.connect(self.on_online_users_loaded)
        self.api.error_occurred.connect(self.on_error_occurred)
        
        # 自动刷新定时器连接
        self.auto_refresh_timer.timeout.connect(self.auto_refresh_messages)
    
    def setup_heartbeat(self):
        """设置心跳定时器"""
        if not self.connection_error:
            self.heartbeat_timer.timeout.connect(self.send_heartbeat)
            self.heartbeat_timer.start(config.HEARTBEAT_INTERVAL)
            
            # 启动自动刷新定时器
            self.auto_refresh_timer.start(config.AUTO_REFRESH_INTERVAL)
    
    def check_server_connection(self):
        """检查服务器连接"""
        try:
            # 通过健康检查端点测试服务器连接
            response = requests.get(f"{self.api.base_url}/health", timeout=3)
            if response.status_code == 200:
                self.connection_error = False
                self.status_label.setText("正在连接...")
                self.setup_heartbeat()
                self.load_initial_data()
            else:
                self.handle_connection_error("服务器健康检查失败")
        except Exception as e:
            print(f"服务器连接失败: {str(e)}")
            self.handle_connection_error(f"服务器连接失败: {str(e)}")
    
    def handle_connection_error(self, error_message):
        """处理连接错误"""
        self.connection_error = True
        self.status_label.setText("连接失败")
        self.online_count_label.setText("无连接")
        self.online_count_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                background-color: #fdeaea;
                padding: 5px 10px;
                border-radius: 15px;
            }
        """)
        
        # 显示错误信息
        self.add_message(
            f"连接服务器失败: {error_message}", 
            is_user=False, 
            sender_name="系统", 
            timestamp="--:--"
        )
        # 确保错误消息也滚动到底部
        self.force_scroll_to_bottom(force_always=True)
    
    def load_initial_data(self):
        """加载初始数据"""
        self.loading_indicator.show()
        self.status_label.setText("正在加载...")
        
        # 加载消息历史
        self.api.load_messages()
        
        # 加载在线用户
        self.api.load_online_users()
        
    def set_user_info(self, username, token=None):
        """设置用户信息"""
        self.current_user = username
        if token:
            self.api.set_token(token)
            
    def set_room_id(self, room_id):
        """设置聊天室ID"""
        self.api.set_room_id(room_id)
        
    def add_message(self, content, is_user=False, sender_name="", timestamp="", message_type="text", file_info=None, profession=""):
        """添加消息到聊天区域"""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
        
        # 根据消息类型和文件信息选择合适的气泡
        if message_type == "image" and file_info:
            # 图片消息使用ImageChatBubble
            bubble = ImageChatBubble(file_info, is_user, sender_name, timestamp, profession)
        elif message_type == "file" and file_info:
            # 文件消息使用FileChatBubble
            bubble = FileChatBubble(file_info, is_user, sender_name, timestamp, profession)
        else:
            # 普通文本消息使用OnlineChatBubble
            bubble = OnlineChatBubble(content, is_user, sender_name, timestamp, profession, message_type)
            
        self.chat_layout.addWidget(bubble)
        
        # 智能滚动到底部（只有用户在底部时才滚动）
        self.force_scroll_to_bottom()
        
    def is_user_at_bottom(self):
        """检测用户是否在聊天底部附近"""
        try:
            scroll_bar = self.scroll.verticalScrollBar()
            # 如果用户距离底部不超过100像素，认为用户在底部
            threshold = 100
            current_pos = scroll_bar.value()
            max_pos = scroll_bar.maximum()
            return (max_pos - current_pos) <= threshold
        except:
            return True  # 异常情况下默认认为在底部
    
    def force_scroll_to_bottom(self, force_send=False, force_receive=False, force_always=False):
        """智能滚动到聊天最底部 - 只有在用户在底部时才滚动"""
        try:
            # 检查用户是否在底部附近
            user_at_bottom = self.is_user_at_bottom()
            
            # 只有在以下情况才滚动：
            # 1. 用户在底部附近
            # 2. 强制滚动（force_always=True）
            # 3. 用户发送消息（force_send=True）
            should_scroll = user_at_bottom or force_always or force_send
            
            if not should_scroll:
                if force_receive:
                    print("📥 用户正在查看历史消息，跳过自动滚动")
                return
            
            scroll_bar = self.scroll.verticalScrollBar()
            
            # 立即滚动到底部
            scroll_bar.setValue(scroll_bar.maximum())
            
            # 多次尝试确保滚动成功
            def delayed_scroll_1():
                scroll_bar.setValue(scroll_bar.maximum())
                self.scroll.ensureVisible(0, scroll_bar.maximum(), 0, 0)
                
            def delayed_scroll_2():
                scroll_bar.setValue(scroll_bar.maximum())
                self.scroll.verticalScrollBar().setSliderPosition(scroll_bar.maximum())
                
            def delayed_scroll_3():
                # 最终确保滚动
                scroll_bar.setValue(scroll_bar.maximum())
                if force_send:
                    print("📤 强制滚动到底部: 发送消息")
                elif force_receive:
                    print("📥 智能滚动到底部: 接收消息")
                elif force_always:
                    print("📜 强制滚动到底部: 系统消息")
                else:
                    print("📜 智能滚动到底部: 添加消息")
            
            # 分层延迟滚动，确保可靠性
            QTimer.singleShot(50, delayed_scroll_1)   # 50ms后第一次尝试
            QTimer.singleShot(100, delayed_scroll_2)  # 100ms后第二次尝试
            QTimer.singleShot(200, delayed_scroll_3)  # 200ms后最终确认
            
            # 对于发送消息，额外增加强制滚动
            if force_send or force_always:
                def final_force_scroll():
                    scroll_bar.setValue(scroll_bar.maximum())
                    # 强制刷新滚动区域
                    self.scroll.update()
                    self.chat_area.update()
                    
                QTimer.singleShot(300, final_force_scroll)  # 300ms后最终强制滚动
                
        except Exception as e:
            print(f"⚠️ 滚动到底部失败: {e}")
            # 备用滚动方法
            try:
                QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
                    self.scroll.verticalScrollBar().maximum()
                ))
            except:
                pass
        
    def send_message(self):
        """发送消息"""
        text = self.input.text().strip()
        if not text:
            return
        
        # 清空输入框
        self.input.clear()
        
        # 检查服务器连接状态
        if self.connection_error:
            self.add_message(
                "无法发送消息：服务器连接已断开，请点击重连", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保连接错误消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
            return
            
        # 在线模式
        # 显示发送状态
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.loading_indicator.show()
        
        # 发送消息
        self.api.send_message(text)
        
    def check_connection_before_send(self):
        """发送消息前检查连接状态"""
        print(f"发送消息前检查连接状态: connection_error={self.connection_error}")
        print(f"API base_url: {self.api.base_url}")
        
        try:
            # 通过健康检查端点快速测试连接
            response = requests.get(f"{self.api.base_url}/health", timeout=2)
            print(f"健康检查响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                self.connection_error = False
                print("健康检查成功，允许发送消息")
                return True
            else:
                self.connection_error = True
                print(f"健康检查失败，状态码: {response.status_code}")
                self.add_message(
                    f"无法发送消息：服务器健康检查异常 (状态码: {response.status_code})", 
                    is_user=False, 
                    sender_name="系统", 
                    timestamp=datetime.now().strftime("%H:%M")
                )
                return False
        except Exception as e:
            self.connection_error = True
            print(f"健康检查异常: {str(e)}")
            self.add_message(
                f"无法发送消息：连接失败 ({str(e)})", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            return False
        
    def upload_file(self):
        """打开文件上传对话框"""
        print("🔍 准备打开文件上传对话框...")
        
        # 创建对话框时指定父窗口
        dialog = FileUploadDialog(self)
        dialog.file_uploaded.connect(self.on_file_uploaded)
        
        # 设置认证头
        if hasattr(self, 'api') and self.api:
            headers = self.api.get_headers()
            dialog.set_auth_headers(headers)
        
        # 使用异常处理包装对话框显示
        try:
            print("📂 显示文件上传对话框...")
            result = dialog.exec_()
            print(f"📂 文件上传对话框结果: {result}")
        except Exception as e:
            print(f"❌ 文件上传对话框出错: {str(e)}")
        finally:
            # 确保对话框被正确清理
            try:
                dialog.hide()
                dialog.deleteLater()
                print("🔒 文件上传对话框已安全关闭")
            except Exception as e:
                print(f"❌ 清理文件上传对话框时出错: {str(e)}")
    
    def on_file_uploaded(self, file_info):
        """处理文件上传完成 - 根据分析报告优化"""
        # 获取文件路径
        file_path = file_info.get('file_path', '')
        filename = file_info.get('filename', '未知文件')
        file_size = file_info.get('file_size', 0)
        
        if not file_path or not os.path.exists(file_path):
            self.add_message(
                "文件路径无效，上传失败", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保错误消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
            return
        
        # 显示上传状态
        self.add_message(
            f"正在上传文件: {filename} ({config.format_file_size(file_size)})", 
            is_user=False, 
            sender_name="系统", 
            timestamp=datetime.now().strftime("%H:%M")
        )
        # 确保上传状态消息也滚动到底部
        self.force_scroll_to_bottom(force_always=True)
        
        if self.connection_error:
            # 连接断开时提示错误
            self.add_message(
                "无法上传文件：服务器连接已断开", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保连接错误消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
        else:
            # 在线模式通过API上传文件
            print(f"📤 通过API上传文件: {file_path}")
            self.api.upload_file_and_send(file_path, self.api.room_id)
    
    def refresh_chat(self):
        """刷新聊天"""
        self.loading_indicator.show()
        self.status_label.setText("正在刷新...")
        
        # 清空当前消息
        self.clear_messages()
        
        # 重新加载数据
        self.load_initial_data()
        
    def auto_refresh_messages(self):
        """自动刷新消息（只加载新消息，不清空现有消息）"""
        if not self.connection_error:
            # 静默加载最新消息，避免频繁的UI更新
            self.api.load_messages(limit=20)  # 加载最新的20条消息进行比较
        
    def reset_connection(self):
        """重置连接状态并重新连接"""
        print(f"重置连接前状态: connection_error={self.connection_error}")
        
        # 停止心跳和自动刷新定时器
        if self.heartbeat_timer.isActive():
            self.heartbeat_timer.stop()
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
        
        # 重置连接状态
        self.connection_error = False
        
        # 显示重连中状态
        self.status_label.setText("正在重连...")
        self.online_count_label.setText("重连中...")
        self.online_count_label.setStyleSheet("""
            QLabel {
                color: #f39c12;
                background-color: #fef9e7;
                padding: 5px 10px;
                border-radius: 15px;
            }
        """)
        
        # 添加重连提示
        self.add_message(
            "正在尝试重新连接服务器...", 
            is_user=False, 
            sender_name="系统", 
            timestamp=datetime.now().strftime("%H:%M")
        )
        # 确保重连消息也滚动到底部
        self.force_scroll_to_bottom(force_always=True)
        
        # 延迟500ms后开始重连
        QTimer.singleShot(500, self.check_server_connection)
        
        print(f"重置连接后状态: connection_error={self.connection_error}")
        
    def clear_messages(self):
        """清空消息"""
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def clear_online_users(self):
        """清空在线用户列表"""
        while self.users_layout.count():
            child = self.users_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def add_online_user(self, user_info):
        """添加在线用户到列表"""
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 8px 12px;
                margin: 2px;
            }
            QFrame:hover {
                background-color: #f0f0f0;
            }
        """)
        
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(8, 8, 8, 8)
        user_layout.setSpacing(10)
        
        # 创建用户头像
        avatar = QLabel()
        avatar.setFixedSize(30, 30)  # 在线用户列表中使用较小的头像
        
        # 获取用户信息
        username = user_info.get('username', '未知用户')
        
        # 🎯 使用智能用户身份识别系统
        # 1. 获取用户职业信息
        profession = self.get_user_profession(username)
        
        # 2. 获取对应的头像路径
        avatar_path = self.get_user_avatar_path(username, profession)
        
        print(f"👥 在线用户头像映射: {username} -> {profession} -> {avatar_path}")
        
        # 使用统一的头像处理函数
        avatar_pixmap = config.create_rounded_avatar(avatar_path, 30)
        avatar.setPixmap(avatar_pixmap)
        avatar.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        # 创建用户信息布局（头像+用户名+职业标识）
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)
        
        # 用户名标签
        user_label = QLabel(username)
        user_label.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        user_label.setStyleSheet("color: #1C1C1C;")
        
        # 职业标识标签（可选显示）
        if profession and profession != '未知角色':
            # 简化职业显示
            profession_display = profession.replace('设计师', '').replace('师', '').replace('系统', '')
            if len(profession_display) > 4:
                profession_display = profession_display[:4] + '...'
            
            profession_label = QLabel(profession_display)
            profession_label.setFont(QFont("Microsoft YaHei UI", 8))
            profession_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    background-color: #f0f2f5;
                    padding: 2px 6px;
                    border-radius: 8px;
                    font-size: 8px;
                }
            """)
            profession_label.setAlignment(Qt.AlignCenter)
            
            user_info_layout.addWidget(user_label)
            user_info_layout.addWidget(profession_label)
        else:
            user_info_layout.addWidget(user_label)
            user_info_layout.addStretch()
        
        # 主布局：头像 + 用户信息
        user_layout.addWidget(avatar)
        user_layout.addLayout(user_info_layout)
        user_layout.addStretch()
        
        # 为用户框添加工具提示
        tooltip_text = f"用户: {username}"
        if profession and profession != '未知角色':
            tooltip_text += f"\n职业: {profession}"
        user_frame.setToolTip(tooltip_text)
        
        self.users_layout.addWidget(user_frame)
        
    def send_heartbeat(self):
        """发送心跳"""
        self.api.send_heartbeat()
        
    # 信号处理方法
    def on_message_sent(self, message_data):
        """消息发送成功处理 - 根据分析报告优化"""
        self.loading_indicator.hide()
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        # 消息发送成功说明连接正常
        self.connection_error = False
        
        # 验证消息数据结构
        if not self.api._validate_message_structure(message_data):
            print("警告: 发送的消息数据结构不完整")
            return
        
        # 提取消息信息（按照分析报告的ChatMessage模型）
        content = message_data.get('content', '')
        sender_name = message_data.get('sender_name', self.current_user)
        sender_role = message_data.get('sender_role', '')  # 添加角色信息
        timestamp = message_data.get('timestamp', '')
        message_type = message_data.get('message_type', 'text')
        message_id = message_data.get('id', '')
        
        # 格式化时间戳（ISO格式）
        formatted_time = self._format_timestamp(timestamp)
        
        # 构建文件信息（如果是文件消息）
        file_info = None
        if message_type in ["file", "image"]:
            file_info = {
                'file_name': message_data.get('file_name', '未知文件'),
                'file_url': message_data.get('file_url', ''),
                'file_size': message_data.get('file_size', 0),
                'content': content
            }
            
        # 获取当前用户职业信息
        current_user_profession = self._get_user_profession(sender_role)
        
        # 创建消息气泡并设置message_id
        if message_type == "image" and file_info:
            bubble = ImageChatBubble(file_info, True, sender_name, formatted_time, current_user_profession)
        elif message_type == "file" and file_info:
            bubble = FileChatBubble(file_info, True, sender_name, formatted_time, current_user_profession)
        else:
            bubble = OnlineChatBubble(content, True, sender_name, formatted_time, current_user_profession, message_type)
        
        # 设置消息ID和其他属性用于去重和管理
        if message_id:
            bubble.message_id = message_id
        bubble.text = content
        bubble.timestamp = formatted_time
        bubble.sender_name = sender_name
        bubble.message_type = message_type
            
        self.chat_layout.addWidget(bubble)
        
        # 强制滚动到底部（发送消息）
        self.force_scroll_to_bottom(force_send=True)
        
        print(f"✅ 消息发送成功: '{content[:30]}...' | 类型: '{message_type}' | 发送者: '{sender_name}' | 角色: '{sender_role}' | ID: '{message_id}'")
        
    def on_messages_loaded(self, messages):
        """消息加载完成处理 - 根据分析报告优化"""
        self.loading_indicator.hide()
        self.connection_error = False  # 成功加载说明连接正常
        self.status_label.setText("已连接")
        
        # 获取已存在的消息ID，避免重复添加
        existing_messages = set()
        existing_message_signatures = set()  # 基于内容和时间戳的签名
        
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            widget = item.widget() if item else None
            if widget:
                # 基于ID去重
                if hasattr(widget, 'message_id') and widget.message_id:
                    existing_messages.add(widget.message_id)
                
                # 基于内容和时间戳去重（作为备用机制）
                if hasattr(widget, 'text') and hasattr(widget, 'timestamp'):
                    signature = f"{widget.text}_{widget.timestamp}_{getattr(widget, 'sender_name', '')}"
                    existing_message_signatures.add(signature)
        
        # 获取当前用户的所有可能标识
        possible_user_names = self._get_possible_user_names()
        
        print(f"📋 开始加载 {len(messages)} 条消息，当前用户标识: {possible_user_names}")
        
        # 添加消息到界面
        for message in reversed(messages):  # 倒序显示，最新的在下面
            message_id = message.get('id', '')
            content = message.get('content', '')
            sender_name = message.get('sender_name', '未知用户')
            sender_role = message.get('sender_role', '')  # 添加角色信息支持
            timestamp = message.get('timestamp', '')
            sender_id = message.get('sender_id', 0)
            message_type = message.get('message_type', 'text')
            
            # 格式化时间戳
            formatted_time = self._format_timestamp(timestamp)
            
            # 自动识别图片类型：如果服务器没有正确设置消息类型，客户端自动识别
            if message_type == 'file' and message.get('file_name'):
                # 检查文件名是否为图片
                if self._is_image_file(message.get('file_name')):
                    message_type = 'image'
                    print(f"🖼️ 自动识别图片文件: {message.get('file_name')}")
            
            # 创建消息签名用于去重
            message_signature = f"{content}_{formatted_time}_{sender_name}"
            
            # 多重去重检查
            should_skip = False
            
            # 1. 基于消息ID去重
            if message_id and message_id in existing_messages:
                print(f"跳过重复消息 (ID): {message_id}")
                should_skip = True
            
            # 2. 基于消息签名去重（备用机制）
            elif message_signature in existing_message_signatures:
                print(f"跳过重复消息 (签名): {message_signature[:50]}...")
                should_skip = True
            
            if should_skip:
                continue
                
            # 增强的用户身份判断逻辑
            is_user = sender_name in possible_user_names
            
            # 构建文件信息（如果是文件消息）
            file_info = None
            if message_type in ["file", "image"]:
                file_info = {
                    'file_name': message.get('file_name', '未知文件'),
                    'file_url': message.get('file_url', ''),
                    'file_size': message.get('file_size', 0),
                    'content': content
                }
                
            # 获取发送者职业信息
            sender_profession = self._get_user_profession(sender_role)
            
            # 创建消息气泡并添加消息ID
            if message_type == "image" and file_info:
                bubble = ImageChatBubble(file_info, is_user, sender_name, formatted_time, sender_profession)
            elif message_type == "file" and file_info:
                bubble = FileChatBubble(file_info, is_user, sender_name, formatted_time, sender_profession)
            else:
                bubble = OnlineChatBubble(content, is_user, sender_name, formatted_time, sender_profession, message_type)
                
            # 设置消息ID和其他属性用于去重和管理
            if message_id:
                bubble.message_id = message_id
            bubble.text = content
            bubble.timestamp = formatted_time
            bubble.sender_name = sender_name
            bubble.message_type = message_type
            
            self.chat_layout.addWidget(bubble)
            
            # 调试输出
            print(f"📝 添加消息: '{content[:20]}...' | 类型: '{message_type}' | 发送者: '{sender_name}' | 角色: '{sender_role}' | ID: '{message_id}' | 是当前用户: {is_user}")
        
        # 强制滚动到底部（接收消息）
        self.force_scroll_to_bottom(force_receive=True)
        
        print(f"✅ 消息加载完成，共显示 {self.chat_layout.count()} 条消息")
    
    def _format_timestamp(self, timestamp):
        """格式化时间戳 - 支持ISO格式"""
        if not timestamp:
            return datetime.now().strftime("%H:%M")
            
        try:
            # 尝试解析ISO格式时间戳（按照分析报告的格式）
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M")
        except Exception as e:
            print(f"时间戳解析失败: {timestamp}, 错误: {e}")
            return datetime.now().strftime("%H:%M")
    
    def _get_user_profession(self, sender_role=None):
        """获取用户职业信息"""
        # 优先使用传入的角色信息
        if sender_role:
            return sender_role
            
        # 从token获取当前用户职业信息
        try:
            user_info = self.token_manager.get_user_info()
            if user_info:
                return user_info.get('profession', '')
        except Exception as e:
            print(f"获取用户职业信息失败: {e}")
        
        return ""
    
    def _get_possible_user_names(self):
        """获取当前用户的所有可能标识"""
        possible_user_names = set()
        
        # 添加当前用户名
        if self.current_user:
            possible_user_names.add(self.current_user)
        
        # 从token管理器获取用户信息
        try:
            user_info = self.token_manager.get_user_info()
            if user_info and user_info.get('username'):
                possible_user_names.add(user_info.get('username'))
        except Exception as e:
            print(f"获取token用户信息失败: {e}")
        
        return possible_user_names
    
    def _is_image_file(self, filename):
        """判断文件是否为图片"""
        if not filename:
            return False
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        ext = os.path.splitext(filename.lower())[1]
        return ext in image_extensions
    
    def on_online_users_loaded(self, users):
        """在线用户加载完成处理"""
        # 清空当前用户列表
        self.clear_online_users()
        
        # 成功加载用户列表说明连接正常
        self.connection_error = False
        
        # 更新在线用户数量
        user_count = len(users)
        self.online_count_label.setText(f"在线: {user_count}")
        self.online_count_label.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                background-color: #e8f5e8;
                padding: 5px 10px;
                border-radius: 15px;
            }
        """)
        
        # 添加用户到列表
        for user in users:
            self.add_online_user(user)
            
    def on_error_occurred(self, error_message):
        """错误处理"""
        self.loading_indicator.hide()
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        # 设置连接错误状态
        self.connection_error = True
        self.status_label.setText("连接错误")
        self.online_count_label.setText("连接异常")
        self.online_count_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                background-color: #fdeaea;
                padding: 5px 10px;
                border-radius: 15px;
            }
        """)
        
        # 显示错误消息
        self.add_message(
            f"API调用失败: {error_message}", 
            is_user=False, 
            sender_name="系统", 
            timestamp=datetime.now().strftime("%H:%M")
        )
        # 确保错误消息也滚动到底部
        self.force_scroll_to_bottom(force_always=True)
        
    # 窗口事件处理
    def paintEvent(self, event):
        """绘制窗口阴影"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制窗口阴影
        for i in range(10):
            opacity = 10 - i
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, opacity))
            painter.drawRoundedRect(self.rect().adjusted(i, i, -i, -i), 20, 20)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._is_drag = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self._is_drag and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self._is_drag = False
        
    def closeEvent(self, event):
        """关闭事件"""
        # 停止心跳和自动刷新定时器
        if self.heartbeat_timer.isActive():
            self.heartbeat_timer.stop()
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
        event.accept() 

    def handle_pasted_files(self, file_paths):
        """处理粘贴的文件列表"""
        if not file_paths:
            return
        
        print(f"📋 处理粘贴的文件: {file_paths}")
        
        # 检查连接状态
        if self.connection_error:
            self.add_message(
                "无法上传文件：服务器连接已断开，请点击重连", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保错误消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
            return
        
        # 处理每个文件
        for file_path in file_paths:
            if not os.path.exists(file_path):
                self.add_message(
                    f"文件不存在: {file_path}", 
                    is_user=False, 
                    sender_name="系统", 
                    timestamp=datetime.now().strftime("%H:%M")
                )
                # 确保错误消息也滚动到底部
                self.force_scroll_to_bottom(force_always=True)
                continue
                
            if not os.path.isfile(file_path):
                self.add_message(
                    f"不是有效文件: {file_path}", 
                    is_user=False, 
                    sender_name="系统", 
                    timestamp=datetime.now().strftime("%H:%M")
                )
                # 确保错误消息也滚动到底部
                self.force_scroll_to_bottom(force_always=True)
                continue
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB 限制
                self.add_message(
                    f"文件过大(超过10MB): {os.path.basename(file_path)}", 
                    is_user=False, 
                    sender_name="系统", 
                    timestamp=datetime.now().strftime("%H:%M")
                )
                # 确保错误消息也滚动到底部
                self.force_scroll_to_bottom(force_always=True)
                continue
            
            # 直接上传文件，不显示系统提示
            self.api.upload_file_and_send(file_path, self.api.room_id)
    
    def handle_pasted_image(self, pixmap):
        """处理粘贴的图片数据"""
        print("📋 处理粘贴的图片")
        
        # 检查连接状态
        if self.connection_error:
            self.add_message(
                "无法上传图片：服务器连接已断开，请点击重连", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保错误消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
            return
        
        try:
            # 生成临时文件名
            temp_dir = tempfile.gettempdir()
            temp_filename = f"pasted_image_{uuid.uuid4().hex[:8]}.png"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # 保存图片到临时文件
            if pixmap.save(temp_path, "PNG"):
                print(f"📋 图片已保存到临时文件: {temp_path}")
                
                # 直接上传文件，不显示系统提示
                self.api.upload_file_and_send(temp_path, self.api.room_id)
                
                # 设置定时器清理临时文件
                QTimer.singleShot(30000, lambda: self.cleanup_temp_file(temp_path))  # 30秒后清理
                
            else:
                self.add_message(
                    "保存粘贴的图片失败", 
                    is_user=False, 
                    sender_name="系统", 
                    timestamp=datetime.now().strftime("%H:%M")
                )
                # 确保错误消息也滚动到底部
                self.force_scroll_to_bottom(force_always=True)
                
        except Exception as e:
            print(f"❌ 处理粘贴图片失败: {str(e)}")
            self.add_message(
                f"处理粘贴图片失败: {str(e)}", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保错误消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
    
    def cleanup_temp_file(self, file_path):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ 临时文件已清理: {file_path}")
        except Exception as e:
            print(f"⚠️ 清理临时文件失败: {str(e)}")

    def download_file_from_chat(self, file_url, file_name):
        """从聊天框下载文件 - 直接下载到本地"""
        try:
            # 显示下载开始提示
            self.add_message(
                f"开始下载文件: {file_name}...", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保下载开始消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
            
            # 让用户选择保存位置
            from PyQt5.QtWidgets import QFileDialog
            
            # 获取文件扩展名
            _, ext = os.path.splitext(file_name)
            
            # 构建文件过滤器
            if ext:
                filter_text = f"{ext.upper()[1:]} 文件 (*{ext});;所有文件 (*.*)"
            else:
                filter_text = "所有文件 (*.*)"
            
            # 弹出保存对话框
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "保存文件", 
                file_name,  # 默认文件名
                filter_text
            )
            
            if not save_path:
                # 用户取消了保存
                self.add_message(
                    "文件下载已取消", 
                    is_user=False, 
                    sender_name="系统", 
                    timestamp=datetime.now().strftime("%H:%M")
                )
                # 确保取消消息也滚动到底部
                self.force_scroll_to_bottom(force_always=True)
                return
            
            # 使用API下载文件
            downloaded_path = self.api.download_file_direct(file_url, file_name, save_path)
            
            # 显示下载成功提示
            self.add_message(
                f"文件下载成功: {os.path.basename(downloaded_path)}\n保存位置: {downloaded_path}", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保下载成功消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
            
            # 询问是否打开文件所在文件夹
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 
                "下载完成", 
                f"文件已成功下载到:\n{downloaded_path}\n\n是否打开文件所在文件夹？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 打开文件所在文件夹
                folder_path = os.path.dirname(downloaded_path)
                
                if platform.system() == "Windows":
                    # Windows: 使用explorer打开并选中文件
                    subprocess.run(f'explorer /select,"{downloaded_path}"', shell=True)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", "-R", downloaded_path])
                else:  # Linux
                    subprocess.run(["xdg-open", folder_path])
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 文件下载失败: {error_msg}")
            
            # 显示下载失败提示
            self.add_message(
                f"文件下载失败: {error_msg}", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
            # 确保下载失败消息也滚动到底部
            self.force_scroll_to_bottom(force_always=True)
    
    def start_voice_call(self):
        """启动语音通话"""
        try:
            # 创建语音通话选择对话框
            dialog = CallSelectionDialog(self, call_type="voice")
            dialog.set_online_users(self.online_users)
            
            if dialog.exec_() == QDialog.Accepted:
                selected_user = dialog.get_selected_user()
                if selected_user:
                    self.initiate_call(selected_user, "voice")
        except Exception as e:
            print(f"启动语音通话失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"启动语音通话失败: {str(e)}")
    
    def start_video_call(self):
        """启动视频通话"""
        try:
            # 创建视频通话选择对话框
            dialog = CallSelectionDialog(self, call_type="video")
            dialog.set_online_users(self.online_users)
            
            if dialog.exec_() == QDialog.Accepted:
                selected_user = dialog.get_selected_user()
                if selected_user:
                    self.initiate_call(selected_user, "video")
        except Exception as e:
            print(f"启动视频通话失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"启动视频通话失败: {str(e)}")
    
    def initiate_call(self, target_user, call_type):
        """发起通话"""
        try:
            call_type_name = "语音通话" if call_type == "voice" else "视频通话"
            
            # 在聊天中显示通话消息
            self.add_message(
                f"正在发起与 {target_user} 的{call_type_name}...", 
                True, 
                self.current_user, 
                datetime.now().strftime("%H:%M"),
                "system"
            )
            
            # 这里可以集成实际的通话功能
            # 例如：启动WebRTC、调用第三方通话API等
            
            # 目前显示功能提示
            reply = QMessageBox.question(
                self,
                "通话功能",
                f"即将与 {target_user} 进行{call_type_name}\n\n"
                f"通话功能正在开发中，是否要在浏览器中打开通话链接？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 这里可以打开实际的通话链接
                # 目前打开一个示例链接
                call_url = f"https://meet.jit.si/call-{target_user}-{int(time.time())}"
                webbrowser.open(call_url)
                
                self.add_message(
                    f"已在浏览器中打开{call_type_name}链接", 
                    False, 
                    "系统", 
                    datetime.now().strftime("%H:%M"),
                    "system"
                )
            else:
                self.add_message(
                    f"已取消与 {target_user} 的{call_type_name}", 
                    False, 
                    "系统", 
                    datetime.now().strftime("%H:%M"),
                    "system"
                )
                
        except Exception as e:
            print(f"发起通话失败: {str(e)}")
            self.add_message(
                f"发起通话失败: {str(e)}", 
                False, 
                "系统", 
                datetime.now().strftime("%H:%M"),
                "system"
            )


class CallSelectionDialog(QDialog):
    """通话用户选择对话框"""
    
    def __init__(self, parent=None, call_type="voice"):
        super().__init__(parent)
        self.call_type = call_type
        self.online_users = []
        self.selected_user = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        call_type_name = "语音通话" if self.call_type == "voice" else "视频通话"
        self.setWindowTitle(f"选择{call_type_name}对象")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel(f"选择要进行{call_type_name}的用户")
        title_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 图标
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), 
                                f'../../../resources/assets/images/file_icons/{"电话" if self.call_type == "voice" else "视频电话"}.svg')
        if os.path.exists(icon_path):
            icon_label.setPixmap(QIcon(icon_path).pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # 用户列表
        self.user_list = QWidget()
        self.user_list.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        self.user_layout = QVBoxLayout(self.user_list)
        self.user_layout.setContentsMargins(10, 10, 10, 10)
        self.user_layout.setSpacing(5)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.user_list)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarNever)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        layout.addWidget(scroll_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedHeight(35)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #666;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.call_btn = QPushButton(f"开始{call_type_name}")
        self.call_btn.setFixedHeight(35)
        self.call_btn.setEnabled(False)
        self.call_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.call_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.call_btn)
        
        layout.addLayout(button_layout)
    
    def set_online_users(self, users):
        """设置在线用户列表"""
        self.online_users = users
        self.update_user_list()
    
    def update_user_list(self):
        """更新用户列表显示"""
        # 清空现有用户
        for i in reversed(range(self.user_layout.count())):
            child = self.user_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not self.online_users:
            # 没有在线用户
            no_users_label = QLabel("暂无在线用户")
            no_users_label.setAlignment(Qt.AlignCenter)
            no_users_label.setStyleSheet("color: #999; padding: 20px;")
            self.user_layout.addWidget(no_users_label)
            return
        
        # 添加用户选项
        self.user_buttons = []
        for user in self.online_users:
            user_btn = QPushButton(user)
            user_btn.setCheckable(True)
            user_btn.setFixedHeight(40)
            user_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #333;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 8px 15px;
                    text-align: left;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    border-color: #007bff;
                }
                QPushButton:checked {
                    background-color: #007bff;
                    color: white;
                    border-color: #007bff;
                }
            """)
            user_btn.clicked.connect(lambda checked, username=user: self.select_user(username))
            self.user_layout.addWidget(user_btn)
            self.user_buttons.append(user_btn)
        
        self.user_layout.addStretch()
    
    def select_user(self, username):
        """选择用户"""
        self.selected_user = username
        
        # 取消其他用户的选中状态
        for btn in self.user_buttons:
            if btn.text() != username:
                btn.setChecked(False)
        
        # 启用通话按钮
        self.call_btn.setEnabled(True)
    
    def get_selected_user(self):
        """获取选中的用户"""
        return self.selected_user