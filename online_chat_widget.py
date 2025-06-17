from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, 
                           QLabel, QHBoxLayout, QScrollArea, QFrame, 
                           QToolButton, QSizePolicy, QProgressBar, QLayout,
                           QTextEdit, QFileDialog, QApplication, QMessageBox,
                           QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import (QFont, QIcon, QPixmap, QPainter, QColor, QPainterPath, 
                        QPen, QFontMetrics, QDesktopServices, QCursor)
import requests
import time
import json
import os
import subprocess
import webbrowser
from datetime import datetime
import online_chat_config as config
from token_manager import TokenManager
from file_upload_widget import FileUploadWidget

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
    def __init__(self, text, is_user=True, sender_name="", timestamp="", parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text = text
        self.sender_name = sender_name
        self.timestamp = timestamp
        
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
        
        # 消息信息栏（发送者和时间）
        if not is_user:
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
        msg_container.setStyleSheet(f"""
            QFrame {{
                background-color: {'#2ecc71' if is_user else '#F0F2F5'};
                border-radius: 18px;
            }}
        """)
        
        container_layout = QHBoxLayout(msg_container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(0)
        
        # 创建头像
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        if is_user:
            avatar_pixmap = QPixmap(config.get_avatar_path('user'))
        else:
            avatar_pixmap = QPixmap(config.get_avatar_path('online_user'))
        
        avatar.setPixmap(avatar_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar.setStyleSheet("""
            QLabel {
                border-radius: 20px;
                background-color: white;
                padding: 2px;
                border: 2px solid #E8E8E8;
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
        
        if is_user:
            # 用户消息：文本左对齐，整体靠右
            text_layout.addWidget(text_label)
        else:
            # 其他用户消息：文本左对齐，整体靠左
            text_layout.addWidget(text_label)
            text_layout.addStretch(1)
        
        # 添加文本容器到消息容器
        container_layout.addWidget(text_container)
        
        # 设置最终布局
        if is_user:
            msg_layout.addStretch(1)  # 左侧弹性空间
            msg_layout.addWidget(msg_container)  # 消息气泡
            msg_layout.addWidget(avatar)  # 头像靠右
        else:
            msg_layout.addWidget(avatar)  # 头像靠左
            msg_layout.addWidget(msg_container)  # 消息气泡
            msg_layout.addStretch(1)  # 右侧弹性空间
        
        # 用户消息显示时间在右侧
        if is_user and timestamp:
            time_layout = QHBoxLayout()
            time_layout.setContentsMargins(0, 0, 50, 0)
            time_layout.addStretch()
            
            time_label = QLabel(timestamp)
            time_label.setFont(QFont("Microsoft YaHei UI", 8))
            time_label.setStyleSheet("color: #999999;")
            time_layout.addWidget(time_label)
            
            layout.addLayout(msg_layout)
            layout.addLayout(time_layout)
        else:
            layout.addLayout(msg_layout)

class FileChatBubble(QFrame):
    """文件消息气泡组件 - 支持点击下载"""
    def __init__(self, file_info, is_user=True, sender_name="", timestamp="", parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.file_info = file_info
        self.sender_name = sender_name
        self.timestamp = timestamp
        
        # 从文件信息中提取数据
        self.file_name = file_info.get('file_name', '未知文件')
        self.file_url = file_info.get('file_url', '')
        self.file_size = file_info.get('file_size', 0)
        self.content = file_info.get('content', f"📎 {self.file_name}")
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.setStyleSheet("""
            FileChatBubble {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.setup_ui()
        
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
        
        # 创建文件消息容器
        file_container = QFrame()
        file_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        file_container.setStyleSheet(f"""
            QFrame {{
                background-color: {'#27ae60' if self.is_user else '#ecf0f1'};
                border: 2px solid {'#2ecc71' if self.is_user else '#bdc3c7'};
                border-radius: 18px;
                padding: 10px;
            }}
            QFrame:hover {{
                background-color: {'#229954' if self.is_user else '#d5dbdb'};
                border-color: {'#27ae60' if self.is_user else '#95a5a6'};
            }}
        """)
        
        container_layout = QVBoxLayout(file_container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        container_layout.setSpacing(8)
        
        # 文件图标和名称行
        file_header = QHBoxLayout()
        file_header.setSpacing(10)
        
        # 文件图标
        file_icon = QLabel(self.get_file_icon())
        file_icon.setFont(QFont("Microsoft YaHei UI", 20))
        file_icon.setFixedSize(40, 40)
        file_icon.setAlignment(Qt.AlignCenter)
        file_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {'rgba(255,255,255,0.2)' if self.is_user else 'white'};
                border-radius: 20px;
                color: {'white' if self.is_user else '#2c3e50'};
            }}
        """)
        
        # 文件信息
        file_info_layout = QVBoxLayout()
        file_info_layout.setSpacing(2)
        
        # 文件名
        file_name_label = QLabel(self.file_name)
        file_name_label.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        file_name_label.setStyleSheet(f"""
            QLabel {{
                color: {'white' if self.is_user else '#2c3e50'};
                background: transparent;
            }}
        """)
        file_name_label.setWordWrap(True)
        
        # 文件大小
        size_text = self.format_file_size(self.file_size)
        file_size_label = QLabel(size_text)
        file_size_label.setFont(QFont("Microsoft YaHei UI", 8))
        file_size_label.setStyleSheet(f"""
            QLabel {{
                color: {'rgba(255,255,255,0.8)' if self.is_user else '#7f8c8d'};
                background: transparent;
            }}
        """)
        
        file_info_layout.addWidget(file_name_label)
        file_info_layout.addWidget(file_size_label)
        
        file_header.addWidget(file_icon)
        file_header.addLayout(file_info_layout)
        file_header.addStretch()
        
        # 下载按钮
        download_btn = QPushButton("📥 点击下载")
        download_btn.setFont(QFont("Microsoft YaHei UI", 9))
        download_btn.setFixedHeight(30)
        download_btn.setCursor(QCursor(Qt.PointingHandCursor))
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'rgba(255,255,255,0.2)' if self.is_user else '#3498db'};
                color: {'white' if self.is_user else 'white'};
                border: {'1px solid rgba(255,255,255,0.3)' if self.is_user else 'none'};
                border-radius: 15px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {'rgba(255,255,255,0.3)' if self.is_user else '#2980b9'};
            }}
            QPushButton:pressed {{
                background-color: {'rgba(255,255,255,0.1)' if self.is_user else '#21618c'};
            }}
        """)
        download_btn.clicked.connect(self.download_file)
        
        container_layout.addLayout(file_header)
        container_layout.addWidget(download_btn)
        
        # 创建头像
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        if self.is_user:
            avatar_pixmap = QPixmap(config.get_avatar_path('user'))
        else:
            avatar_pixmap = QPixmap(config.get_avatar_path('online_user'))
        
        avatar.setPixmap(avatar_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar.setStyleSheet("""
            QLabel {
                border-radius: 20px;
                background-color: white;
                padding: 2px;
                border: 2px solid #E8E8E8;
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
        """根据文件类型返回对应的图标"""
        if not self.file_name:
            return "📄"
        
        file_ext = os.path.splitext(self.file_name.lower())[1]
        
        # 图片文件
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']:
            return "🖼️"
        # 文档文件
        elif file_ext in ['.pdf']:
            return "📕"
        elif file_ext in ['.doc', '.docx']:
            return "📘"
        elif file_ext in ['.xls', '.xlsx']:
            return "📗"
        elif file_ext in ['.ppt', '.pptx']:
            return "📙"
        elif file_ext in ['.txt']:
            return "📝"
        # 代码文件
        elif file_ext in ['.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml']:
            return "💻"
        # 压缩文件
        elif file_ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return "🗜️"
        # 音频文件
        elif file_ext in ['.mp3', '.wav', '.flac', '.aac']:
            return "🎵"
        # 视频文件
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv']:
            return "🎬"
        else:
            return "📄"
    
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
        """下载文件"""
        if not self.file_url:
            QMessageBox.warning(self, "下载失败", "文件URL不存在")
            return
        
        try:
            # 构建完整的文件URL
            base_url = config.CHAT_API_BASE_URL
            if self.file_url.startswith('http'):
                full_url = self.file_url
            else:
                full_url = f"{base_url}{self.file_url}"
            
            print(f"📥 开始下载文件: {self.file_name}")
            print(f"🔗 文件URL: {full_url}")
            
            # 方式1：使用浏览器下载（推荐，因为可以利用浏览器的下载管理器）
            QDesktopServices.openUrl(QUrl(full_url))
            
            # 显示下载提示
            QMessageBox.information(self, "下载开始", 
                                  f"文件 {self.file_name} 已在浏览器中打开\n"
                                  f"如果是图片或PDF，将在浏览器中预览\n"
                                  f"其他文件类型将自动下载")
            
        except Exception as e:
            print(f"❌ 文件下载失败: {str(e)}")
            QMessageBox.critical(self, "下载失败", f"文件下载失败：{str(e)}")
    
    def mousePressEvent(self, event):
        """鼠标点击事件 - 整个气泡都可以点击下载"""
        if event.button() == Qt.LeftButton:
            self.download_file()
        super().mousePressEvent(event)

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
        """发送消息"""
        try:
            url = f"{self.base_url}/api/chat/send"
            params = {"room_id": self.room_id}
            data = {
                "message_type": message_type,
                "content": content
            }
            if reply_to:
                data["reply_to"] = reply_to
            if file_info:
                data["file_info"] = file_info
                
            response = requests.post(url, json=data, headers=self.get_headers(), 
                                   params=params, timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
            message_data = response.json()
            self.message_received.emit(message_data)
            
        except Exception as e:
            self.error_occurred.emit(f"发送消息失败: {str(e)}")
    
    def load_messages(self, limit=50, before=None):
        """加载消息历史"""
        try:
            url = f"{self.base_url}/api/chat/messages"
            params = {
                "room_id": self.room_id,
                "limit": limit
            }
            if before:
                params["before"] = before
                
            response = requests.get(url, headers=self.get_headers(), 
                                  params=params, timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
            messages = response.json()
            self.messages_loaded.emit(messages)
            
        except Exception as e:
            self.error_occurred.emit(f"加载消息失败: {str(e)}")
    
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
    
    def send_heartbeat(self):
        """发送心跳保持在线状态"""
        try:
            url = f"{self.base_url}/api/chat/heartbeat"
            response = requests.post(url, headers=self.get_headers(), timeout=config.CHAT_API_TIMEOUT)
            response.raise_for_status()
            
        except Exception as e:
            print(f"心跳发送失败: {str(e)}")

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
        self.chat_area.setStyleSheet("background-color: white;")
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
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addWidget(self.reconnect_btn)
        toolbar_layout.addStretch()
        
        input_layout.addLayout(toolbar_layout)
        
        # 输入行
        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(15)
        
        self.input = QLineEdit()
        self.input.setFixedHeight(45)
        self.input.setFont(QFont("Microsoft YaHei UI", 10))
        self.input.setPlaceholderText("输入消息...")
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
        
    def add_message(self, content, is_user=False, sender_name="", timestamp="", message_type="text", file_info=None):
        """添加消息到聊天区域"""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
        
        # 如果是文件消息，使用FileChatBubble
        if message_type == "file" and file_info:
            bubble = FileChatBubble(file_info, is_user, sender_name, timestamp)
        else:
            bubble = OnlineChatBubble(content, is_user, sender_name, timestamp)
            
        self.chat_layout.addWidget(bubble)
        
        # 滚动到底部
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
        
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
        """处理文件上传完成"""
        # 发送文件消息
        filename = file_info.get('filename', '未知文件')
        file_size = file_info.get('file_size', 0)
        file_url = file_info.get('file_url', '')
        
        # 构造文件消息内容
        file_message = f"📎 {filename}\n大小: {config.format_file_size(file_size)}"
        
        if self.connection_error:
            # 连接断开时提示错误
            self.add_message(
                "无法上传文件：服务器连接已断开", 
                is_user=False, 
                sender_name="系统", 
                timestamp=datetime.now().strftime("%H:%M")
            )
        else:
            # 在线模式通过API发送文件消息
            self.api.send_message(file_message, message_type="file", file_info=file_info)
            
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
                padding: 5px;
                margin: 2px;
            }
            QFrame:hover {
                background-color: #f0f0f0;
            }
        """)
        
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(8, 5, 8, 5)
        user_layout.setSpacing(8)
        
        # 用户头像
        avatar = QLabel()
        avatar.setFixedSize(30, 30)
        avatar_pixmap = QPixmap(config.get_avatar_path('online_user'))
        avatar.setPixmap(avatar_pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar.setStyleSheet("""
            QLabel {
                border-radius: 15px;
                background-color: #f8f9fa;
                border: 1px solid #E8E8E8;
            }
        """)
        
        # 用户信息
        user_info_layout = QVBoxLayout()
        user_info_layout.setSpacing(2)
        
        username = user_info.get('username', '未知用户')
        user_label = QLabel(username)
        user_label.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        user_label.setStyleSheet("color: #1C1C1C;")
        
        status_text = "在线"
        status_label = QLabel(status_text)
        status_label.setFont(QFont("Microsoft YaHei UI", 8))
        status_label.setStyleSheet("color: #2ecc71;")
        
        user_info_layout.addWidget(user_label)
        user_info_layout.addWidget(status_label)
        
        user_layout.addWidget(avatar)
        user_layout.addLayout(user_info_layout)
        user_layout.addStretch()
        
        self.users_layout.addWidget(user_frame)
        
    def send_heartbeat(self):
        """发送心跳"""
        self.api.send_heartbeat()
        
    # 信号处理方法
    def on_message_sent(self, message_data):
        """消息发送成功处理"""
        self.loading_indicator.hide()
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        # 消息发送成功说明连接正常
        self.connection_error = False
        
        # 添加消息到界面
        content = message_data.get('content', '')
        sender_name = message_data.get('sender_name', self.current_user)
        timestamp = message_data.get('timestamp', '')
        message_type = message_data.get('message_type', 'text')
        
        # 格式化时间戳
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%H:%M")
            except:
                formatted_time = datetime.now().strftime("%H:%M")
        else:
            formatted_time = datetime.now().strftime("%H:%M")
        
        # 构建文件信息（如果是文件消息）
        file_info = None
        if message_type == "file":
            file_info = {
                'file_name': message_data.get('file_name', '未知文件'),
                'file_url': message_data.get('file_url', ''),
                'file_size': message_data.get('file_size', 0),
                'content': content
            }
            
        # 发送的消息总是当前用户的，强制设置为True
        self.add_message(content, is_user=True, sender_name=sender_name, 
                        timestamp=formatted_time, message_type=message_type, file_info=file_info)
        print(f"发送消息: '{content}' | 类型: '{message_type}' | 发送者: '{sender_name}' | 强制显示在右边")
        
    def on_messages_loaded(self, messages):
        """消息加载完成处理"""
        self.loading_indicator.hide()
        self.connection_error = False  # 成功加载说明连接正常
        self.status_label.setText("已连接")
        
        # 获取已存在的消息ID，避免重复添加
        existing_messages = set()
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and hasattr(item.widget(), 'message_id'):
                existing_messages.add(item.widget().message_id)
        
        # 获取当前用户的所有可能标识
        possible_user_names = set()
        if self.current_user:
            possible_user_names.add(self.current_user)
        
        # 从token管理器获取用户信息
        try:
            user_info = self.token_manager.get_user_info()
            if user_info and user_info.get('username'):
                possible_user_names.add(user_info.get('username'))
        except:
            pass
        
        # 打印调试信息
        print(f"当前用户身份标识: {possible_user_names}")
        
        # 添加消息到界面
        for message in reversed(messages):  # 倒序显示，最新的在下面
            message_id = message.get('id', '')
            if message_id and message_id in existing_messages:
                continue  # 跳过已存在的消息
                
            content = message.get('content', '')
            sender_name = message.get('sender_name', '未知用户')
            timestamp = message.get('timestamp', '')
            sender_id = message.get('sender_id', 0)
            message_type = message.get('message_type', 'text')
            
            # 增强的用户身份判断逻辑
            is_user = sender_name in possible_user_names
            
            # 调试输出
            print(f"消息: '{content[:20]}...' | 类型: '{message_type}' | 发送者: '{sender_name}' | 是当前用户: {is_user}")
            
            # 格式化时间戳
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%H:%M")
                except:
                    formatted_time = ""
            else:
                formatted_time = ""
            
            # 构建文件信息（如果是文件消息）
            file_info = None
            if message_type == "file":
                file_info = {
                    'file_name': message.get('file_name', '未知文件'),
                    'file_url': message.get('file_url', ''),
                    'file_size': message.get('file_size', 0),
                    'content': content
                }
                
            # 创建消息气泡并添加消息ID
            if message_type == "file" and file_info:
                bubble = FileChatBubble(file_info, is_user, sender_name, formatted_time)
            else:
                bubble = OnlineChatBubble(content, is_user, sender_name, formatted_time)
                
            if message_id:
                bubble.message_id = message_id
            self.chat_layout.addWidget(bubble)
            
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