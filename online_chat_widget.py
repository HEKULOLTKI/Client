from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, 
                           QLabel, QHBoxLayout, QScrollArea, QFrame, 
                           QToolButton, QSizePolicy, QProgressBar, QLayout,
                           QTextEdit, QFileDialog, QApplication, QMessageBox)
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal
from PyQt5.QtGui import (QFont, QIcon, QPixmap, QPainter, QColor, QPainterPath, 
                        QPen, QFontMetrics)
import requests
import time
import json
from datetime import datetime
import config

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
            avatar_pixmap = QPixmap("assets/user.png")
        else:
            avatar_pixmap = QPixmap("assets/online_user.png")
            # 如果没有在线用户头像，使用默认头像
            if avatar_pixmap.isNull():
                avatar_pixmap = QPixmap("assets/pet_head.png")
        
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
        max_width = 450  # 最大宽度
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

class OnlineChatAPI(QThread):
    """在线聊天API处理线程"""
    message_received = pyqtSignal(dict)
    messages_loaded = pyqtSignal(list)
    online_users_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_url = "http://localhost:8000"  # 根据API文档的默认地址
        self.token = None  # 需要JWT Token
        self.room_id = "global"  # 默认聊天室
        
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
    
    def send_message(self, content, message_type="text", reply_to=None):
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
                
            response = requests.post(url, json=data, headers=self.get_headers(), 
                                   params=params, timeout=10)
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
                                  params=params, timeout=10)
            response.raise_for_status()
            
            messages = response.json()
            self.messages_loaded.emit(messages)
            
        except Exception as e:
            self.error_occurred.emit(f"加载消息失败: {str(e)}")
    
    def load_online_users(self):
        """加载在线用户列表"""
        try:
            url = f"{self.base_url}/api/chat/online-users"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            
            users = response.json()
            self.online_users_loaded.emit(users)
            
        except Exception as e:
            self.error_occurred.emit(f"加载在线用户失败: {str(e)}")
    
    def send_heartbeat(self):
        """发送心跳保持在线状态"""
        try:
            url = f"{self.base_url}/api/chat/heartbeat"
            response = requests.post(url, headers=self.get_headers(), timeout=5)
            response.raise_for_status()
            
        except Exception as e:
            print(f"心跳发送失败: {str(e)}")

class OnlineChatWidget(QWidget):
    """在线聊天窗口组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = "当前用户"  # 默认用户名，可以通过方法设置
        self.api = OnlineChatAPI()
        self.heartbeat_timer = QTimer()
        self.offline_mode = False  # 离线模式标志
        
        # 设置窗口属性
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        
        # 初始化拖动变量
        self._is_drag = False
        self._drag_pos = None
        
        # 检查服务器连接，如果失败则进入离线模式
        self.check_server_connection()
        
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
        self.setFixedSize(800, 700)
        
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
        
        toolbar_layout.addWidget(self.file_btn)
        toolbar_layout.addWidget(self.refresh_btn)
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
        self.api.message_received.connect(self.on_message_sent)
        self.api.messages_loaded.connect(self.on_messages_loaded)
        self.api.online_users_loaded.connect(self.on_online_users_loaded)
        self.api.error_occurred.connect(self.on_error_occurred)
        
    def setup_heartbeat(self):
        """设置心跳定时器"""
        if not self.offline_mode:
            self.heartbeat_timer.timeout.connect(self.send_heartbeat)
            self.heartbeat_timer.start(30000)
    
    def check_server_connection(self):
        """检查服务器连接"""
        try:
            # 尝试简单的连接测试
            response = requests.get(f"{self.api.base_url}/api/status", timeout=3)
            if response.status_code == 200:
                self.offline_mode = False
                self.status_label.setText("正在连接...")
                self.setup_heartbeat()
                self.load_initial_data()
            else:
                self.enter_offline_mode()
        except Exception as e:
            print(f"服务器连接失败: {str(e)}")
            self.enter_offline_mode()
    
    def enter_offline_mode(self):
        """进入离线模式"""
        self.offline_mode = True
        self.status_label.setText("离线模式")
        self.online_count_label.setText("离线: 0")
        self.online_count_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                background-color: #fdeaea;
                padding: 5px 10px;
                border-radius: 15px;
            }
        """)
        
        # 添加离线模式说明
        self.add_message(
            "当前处于离线模式，无法连接到聊天服务器。\n您可以在此测试界面功能，但无法发送真实消息。", 
            is_user=False, 
            sender_name="系统", 
            timestamp="--:--"
        )
        
        # 添加一些示例用户和消息
        self.load_offline_demo_data()
    
    def load_offline_demo_data(self):
        """加载离线演示数据"""
        # 添加示例消息
        demo_messages = [
            {"content": "欢迎使用在线聊天室！", "sender": "系统", "time": "09:00"},
            {"content": "大家好！", "sender": "张三", "time": "09:15"},
            {"content": "有人在吗？", "sender": "李四", "time": "09:30"},
        ]
        
        for msg in demo_messages:
            self.add_message(
                msg["content"],
                is_user=False,
                sender_name=msg["sender"],
                timestamp=msg["time"]
            )
        
        # 添加示例在线用户
        demo_users = [
            {"username": "张三", "user_id": 1},
            {"username": "李四", "user_id": 2},
            {"username": "王五", "user_id": 3},
            {"username": self.current_user, "user_id": 4}
        ]
        
        for user in demo_users:
            self.add_online_user(user)
        
        self.online_count_label.setText(f"演示: {len(demo_users)}")
    
    def load_initial_data(self):
        """加载初始数据"""
        if self.offline_mode:
            self.load_offline_demo_data()
            return
            
        self.loading_indicator.show()
        self.status_label.setText("正在加载...")
        
        # 加载消息历史
        self.api.load_messages()
        
        # 加载在线用户
        self.api.load_online_users()  # 每30秒发送一次心跳
        
    def set_user_info(self, username, token=None):
        """设置用户信息"""
        self.current_user = username
        if token:
            self.api.set_token(token)
            
    def set_room_id(self, room_id):
        """设置聊天室ID"""
        self.api.set_room_id(room_id)
        
    def load_initial_data(self):
        """加载初始数据"""
        self.loading_indicator.show()
        self.status_label.setText("正在加载...")
        
        # 加载消息历史
        self.api.load_messages()
        
        # 加载在线用户
        self.api.load_online_users()
        
    def add_message(self, content, is_user=False, sender_name="", timestamp=""):
        """添加消息到聊天区域"""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")
            
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
        
        if self.offline_mode:
            # 离线模式下模拟发送
            timestamp = datetime.now().strftime("%H:%M")
            self.add_message(text, is_user=True, sender_name=self.current_user, timestamp=timestamp)
            
            # 模拟系统回复
            QTimer.singleShot(1000, lambda: self.add_message(
                "这是离线模式的模拟回复。实际聊天需要连接到服务器。",
                is_user=False,
                sender_name="系统",
                timestamp=datetime.now().strftime("%H:%M")
            ))
            return
            
        # 在线模式
        # 显示发送状态
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.loading_indicator.show()
        
        # 发送消息
        self.api.send_message(text)
        
    def upload_file(self):
        """上传文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", 
            "图片文件 (*.png *.jpg *.jpeg *.gif *.webp);;文档文件 (*.pdf *.txt *.doc *.docx *.xls *.xlsx);;所有文件 (*.*)"
        )
        
        if file_path:
            # 这里应该实现文件上传逻辑
            # 目前只显示提示
            QMessageBox.information(self, "文件上传", f"文件上传功能开发中\n选择的文件: {file_path}")
            
    def refresh_chat(self):
        """刷新聊天"""
        self.loading_indicator.show()
        self.status_label.setText("正在刷新...")
        
        # 清空当前消息
        self.clear_messages()
        
        # 重新加载数据
        self.load_initial_data()
        
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
        avatar_pixmap = QPixmap("assets/online_user.png")
        if avatar_pixmap.isNull():
            avatar_pixmap = QPixmap("assets/user.png")
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
        
        # 添加消息到界面
        content = message_data.get('content', '')
        sender_name = message_data.get('sender_name', self.current_user)
        timestamp = message_data.get('timestamp', '')
        
        # 格式化时间戳
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%H:%M")
            except:
                formatted_time = datetime.now().strftime("%H:%M")
        else:
            formatted_time = datetime.now().strftime("%H:%M")
            
        self.add_message(content, is_user=True, sender_name=sender_name, timestamp=formatted_time)
        
    def on_messages_loaded(self, messages):
        """消息加载完成处理"""
        self.loading_indicator.hide()
        self.status_label.setText("已连接")
        
        # 添加消息到界面
        for message in reversed(messages):  # 倒序显示，最新的在下面
            content = message.get('content', '')
            sender_name = message.get('sender_name', '未知用户')
            timestamp = message.get('timestamp', '')
            sender_id = message.get('sender_id', 0)
            
            # 判断是否是当前用户发送的消息
            is_user = sender_name == self.current_user
            
            # 格式化时间戳
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%H:%M")
                except:
                    formatted_time = ""
            else:
                formatted_time = ""
                
            self.add_message(content, is_user, sender_name, formatted_time)
            
    def on_online_users_loaded(self, users):
        """在线用户加载完成处理"""
        # 清空当前用户列表
        self.clear_online_users()
        
        # 更新在线用户数量
        user_count = len(users)
        self.online_count_label.setText(f"在线: {user_count}")
        
        # 添加用户到列表
        for user in users:
            self.add_online_user(user)
            
    def on_error_occurred(self, error_message):
        """错误处理"""
        self.loading_indicator.hide()
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_label.setText("连接错误")
        
        # 显示错误消息
        QMessageBox.warning(self, "错误", error_message)
        
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
        # 停止心跳定时器
        if self.heartbeat_timer.isActive():
            self.heartbeat_timer.stop()
        event.accept() 