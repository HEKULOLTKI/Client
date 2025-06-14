from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, 
                           QLabel, QHBoxLayout, QScrollArea, QFrame, 
                           QToolButton, QSizePolicy, QProgressBar, QLayout)
from PyQt5.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import (QFont, QIcon, QPixmap, QPainter, QColor, QPainterPath, 
                        QPen, QFontMetrics)

class LoadingIndicator(QProgressBar):
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
                background-color: #0066FF;
            }
        """)
        self.hide()

class ChatBubble(QFrame):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.text = text
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.setStyleSheet("""
            ChatBubble {
                background-color: transparent;
                border: none;
            }
        """)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 创建消息容器
        msg_container = QFrame()
        msg_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        msg_container.setStyleSheet(f"""
            QFrame {{
                background-color: {'#0066FF' if is_user else '#F0F2F5'};
                border-radius: 18px;
            }}
        """)
        
        msg_layout = QHBoxLayout(msg_container)
        msg_layout.setContentsMargins(15, 10, 15, 10)
        msg_layout.setSpacing(0)
        
        # 创建头像
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        avatar_pixmap = QPixmap(f"assets/{'user' if is_user else 'pet_head'}.png")
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
                qproperty-alignment: AlignLeft;  /* 统一使用左对齐 */
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
            # 宠物消息：文本左对齐，整体靠左
            text_layout.addWidget(text_label)
            text_layout.addStretch(1)
        
        # 添加文本容器到消息容器
        msg_layout.addWidget(text_container)
        
        # 设置最终布局
        if is_user:
            layout.addStretch(1)  # 左侧弹性空间
            layout.addWidget(msg_container)  # 消息气泡
            layout.addWidget(avatar)  # 头像靠右
        else:
            layout.addWidget(avatar)  # 头像靠左
            layout.addWidget(msg_container)  # 消息气泡
            layout.addStretch(1)  # 右侧弹性空间
class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(45)
        self.setFont(QFont("Microsoft YaHei UI", 10))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #0066FF;
                color: white;
                border-radius: 22px;
                padding: 5px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0052CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton:disabled {
                background-color: #CCE0FF;
            }
        """)

class ChatWidget(QWidget):
    def __init__(self, openai_chat, parent=None):
        super().__init__(parent)
        self.openai_chat = openai_chat
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
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
        
        title_label = QLabel("AI Desktop Pet")
        title_label.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #1C1C1C;")
        
        close_btn = QToolButton()
        close_btn.setIcon(QIcon("assets/close.png"))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #FFE1E1;
                border-radius: 15px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        container_layout.addWidget(title_bar)
        
        # 加载指示器
        self.loading_indicator = LoadingIndicator()
        container_layout.addWidget(self.loading_indicator)
        
        # 聊天区域
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
        container_layout.addWidget(self.scroll)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                border-top: 1px solid #E8E8E8;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(30, 20, 30, 20)
        input_layout.setSpacing(15)
        
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
                border: 2px solid #0066FF;
                background-color: white;
            }
        """)
        self.input.returnPressed.connect(self.on_send)
        
        self.send_btn = ModernButton("发送")
        self.send_btn.setFixedWidth(140)
        self.send_btn.clicked.connect(self.on_send)
        
        input_layout.addWidget(self.input)
        input_layout.addWidget(self.send_btn)
        
        container_layout.addWidget(input_frame)
        
        # 添加主容器到主布局
        main_layout.addWidget(main_container)
        
        # 设置窗口大小和初始化拖动变量
        self.setFixedSize(600, 700)
        self._is_drag = False
        self._drag_pos = None
        
        # 连接信号
        self.openai_chat.response_received.connect(self.handle_response)
        self.openai_chat.error_occurred.connect(self.handle_error)
        
        # 初始化等待状态
        self.is_waiting = False
        
        # 添加欢迎消息
        self.add_message("你好！我是你的AI桌面宠物，让我们开始聊天吧！", is_user=False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制窗口阴影
        for i in range(10):
            opacity = 10 - i
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, opacity))
            painter.drawRoundedRect(self.rect().adjusted(i, i, -i, -i), 20, 20)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_drag = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_drag and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_drag = False

    def add_message(self, text, is_user):
        bubble = ChatBubble(text, is_user)
        self.chat_layout.addWidget(bubble)
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def on_send(self):
        if self.is_waiting:
            return
            
        text = self.input.text().strip()
        if text:
            self.add_message(text, is_user=True)
            self.input.clear()
            
            self.loading_indicator.show()
            self.input.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.is_waiting = True
            
            messages = [
                {"role": "system", "content": "你是一个可爱的桌面宠物，请用轻松愉快的语气和用户聊天。"},
                {"role": "user", "content": text}
            ]
            self.openai_chat.chat_async(messages)

    def handle_response(self, response):
        self.loading_indicator.hide()
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.is_waiting = False
        self.add_message(response, is_user=False)

    def handle_error(self, error_message):
        self.loading_indicator.hide()
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.is_waiting = False
        self.add_message(f"抱歉，出现了一个错误：{error_message}", is_user=False)
# 已通过 openai_chat 参数与 OpenAIChat 对接，无需更改