import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLabel, QSystemTrayIcon, QMenu, 
                             QDesktopWidget, QToolButton, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient
import config
from pet_widget import PetWidget
from chat_widget import ChatWidget
from transition_page import TransitionPage
from openai_api import OpenAIChat

class DesktopManager(QWidget):
    """桌面管理器 - 在桌面顶部悬浮显示"""
    
    # 定义信号
    launch_browser = pyqtSignal()
    show_settings = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.pet_widget = None
        self.chat_widget = None
        self.transition_page = None
        self.openai_chat = None  # 添加OpenAI聊天实例
        self.is_expanded = False
        self.setup_ui()
        self.setup_timer()
        self.setup_animations()
        self.position_at_top()
        
    def setup_ui(self):
        """设置UI界面"""
        # 设置窗口属性 - 桌面顶部悬浮
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口大小
        self.setFixedHeight(60)
        self.setMinimumWidth(800)
        
        # 创建主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)
        
        # 创建背景框架
        self.background_frame = QFrame()
        self.background_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(45, 52, 54, 220),
                    stop:1 rgba(99, 110, 114, 200));
                border-radius: 25px;
                border: 1px solid rgba(116, 125, 140, 150);
            }
        """)
        
        # 背景框架布局
        frame_layout = QHBoxLayout(self.background_frame)
        frame_layout.setContentsMargins(15, 8, 15, 8)
        frame_layout.setSpacing(10)
        
        # 左侧 - 系统信息区域
        self.create_info_section(frame_layout)
        
        # 中间 - 分隔符
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: rgba(255, 255, 255, 100); }")
        frame_layout.addWidget(separator)
        
        # 右侧 - 功能按钮区域
        self.create_buttons_section(frame_layout)
        
        # 添加背景框架到主布局
        main_layout.addWidget(self.background_frame)
        self.setLayout(main_layout)
        
    def create_info_section(self, layout):
        """创建信息显示区域"""
        info_layout = QHBoxLayout()
        
        # 时间显示
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.time_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                padding: 2px 8px;
            }
        """)
        
        # 日期显示
        self.date_label = QLabel()
        self.date_label.setFont(QFont("Microsoft YaHei", 9))
        self.date_label.setStyleSheet("""
            QLabel {
                color: #dcdde1;
                background: transparent;
                padding: 2px 8px;
            }
        """)
        
        # 系统状态
        self.status_label = QLabel("系统运行正常")
        self.status_label.setFont(QFont("Microsoft YaHei", 9))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00d2d3;
                background: transparent;
                padding: 2px 8px;
            }
        """)
        
        # 添加到布局
        info_layout.addWidget(self.time_label)
        info_layout.addWidget(self.date_label)
        info_layout.addWidget(self.status_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
    def create_buttons_section(self, layout):
        """创建功能按钮区域"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # 按钮配置
        buttons_config = [
            ("🌐", "浏览器", self.launch_browser_action, "#3498db"),
            ("🐱", "宠物", self.show_pet, "#e74c3c"),
            ("💬", "聊天", self.show_chat, "#2ecc71"),
            ("⚙️", "设置", self.show_settings_action, "#f39c12"),
            ("🔄", "刷新", self.refresh_system, "#9b59b6"),
            ("❌", "退出", self.exit_application, "#95a5a6")
        ]
        
        for icon, tooltip, handler, color in buttons_config:
            button = self.create_button(icon, tooltip, handler, color)
            buttons_layout.addWidget(button)
        
        layout.addLayout(buttons_layout)
        
    def create_button(self, text, tooltip, handler, color):
        """创建功能按钮"""
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setFixedSize(40, 40)
        button.setFont(QFont("Segoe UI Emoji", 12))
        button.clicked.connect(handler)
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color},
                    stop:1 {self.darken_color(color, 0.8)});
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.lighten_color(color, 1.2)},
                    stop:1 {color});
                transform: scale(1.05);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.darken_color(color, 0.7)},
                    stop:1 {self.darken_color(color, 0.9)});
            }}
        """)
        
        return button
        
    def darken_color(self, hex_color, factor=0.8):
        """使颜色变暗"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def lighten_color(self, hex_color, factor=1.2):
        """使颜色变亮"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lightened = tuple(min(255, int(c * factor)) for c in rgb)
        return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"
        
    def setup_timer(self):
        """设置定时器"""
        # 时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新
        
        # 初始化时间显示
        self.update_time()
        
    def setup_animations(self):
        """设置动画效果"""
        # 创建动画对象
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def position_at_top(self):
        """将管理器定位到屏幕顶部中央"""
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        
        # 计算位置 - 顶部中央
        x = (screen_rect.width() - self.width()) // 2
        y = 10  # 距离顶部10像素
        
        self.move(x, y)
        
    def update_time(self):
        """更新时间显示"""
        current_time = QTime.currentTime()
        time_text = current_time.toString("hh:mm:ss")
        self.time_label.setText(time_text)
        
        # 更新日期
        from datetime import datetime
        current_date = datetime.now()
        date_text = current_date.strftime("%Y年%m月%d日")
        self.date_label.setText(date_text)
        
    def launch_browser_action(self):
        """启动浏览器"""
        try:
            self.status_label.setText("正在启动浏览器...")
            # 启动全屏浏览器
            subprocess.Popen([sys.executable, "fullscreen_browser.py"])
            self.status_label.setText("浏览器已启动")
        except Exception as e:
            self.status_label.setText(f"启动失败: {str(e)}")
            
    def show_pet(self):
        """显示/隐藏宠物"""
        if not self.pet_widget:
            self.pet_widget = PetWidget()
            self.pet_widget.doubleClicked.connect(self.show_chat)
            
        if self.pet_widget.isVisible():
            self.pet_widget.hide()
            self.status_label.setText("宠物已隐藏")
        else:
            self.pet_widget.show()
            self.status_label.setText("宠物已显示")
            
    def show_chat(self):
        """显示/隐藏聊天窗口"""
        if not self.chat_widget:
            # 创建OpenAI聊天实例（如果还没有的话）
            if not self.openai_chat:
                self.openai_chat = OpenAIChat()
            # 传递openai_chat参数给ChatWidget
            self.chat_widget = ChatWidget(self.openai_chat)
            
        if self.chat_widget.isVisible():
            self.chat_widget.hide()
            self.status_label.setText("聊天窗口已隐藏")
        else:
            self.chat_widget.show()
            self.status_label.setText("聊天窗口已显示")
            
    def show_settings_action(self):
        """显示设置"""
        self.status_label.setText("设置功能开发中...")
        # TODO: 实现设置界面
        
    def refresh_system(self):
        """刷新系统状态"""
        self.status_label.setText("正在刷新...")
        QTimer.singleShot(1000, lambda: self.status_label.setText("系统运行正常"))
        
    def exit_application(self):
        """退出应用程序"""
        if not self.transition_page:
            self.transition_page = TransitionPage()
            self.transition_page.transition_completed.connect(self.close_all_and_exit)
            self.transition_page.force_close.connect(self.close_all_and_exit)
            
        self.transition_page.start_transition(2000, "正在退出桌面管理器...")
        
    def close_all_and_exit(self):
        """关闭所有窗口并退出"""
        # 关闭所有子窗口
        if self.pet_widget:
            self.pet_widget.close()
        if self.chat_widget:
            self.chat_widget.close()
        if self.transition_page:
            self.transition_page.close()
            
        # 退出应用程序
        QApplication.quit()
        
    def mousePressEvent(self, event):
        """鼠标按下事件 - 支持拖拽"""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽移动"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            new_pos = event.globalPos() - self.drag_pos
            # 限制在屏幕顶部区域
            desktop = QDesktopWidget()
            screen_rect = desktop.availableGeometry()
            if new_pos.y() < 0:
                new_pos.setY(0)
            elif new_pos.y() > 100:  # 限制在顶部100像素内
                new_pos.setY(100)
            self.move(new_pos)
            
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape:
            self.exit_application()
        elif event.key() == Qt.Key_F1:
            self.show_pet()
        elif event.key() == Qt.Key_F2:
            self.show_chat()
        elif event.key() == Qt.Key_F3:
            self.launch_browser_action()
        super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """关闭事件"""
        self.close_all_and_exit()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("桌面管理器")
    app.setQuitOnLastWindowClosed(True)
    
    # 创建并显示桌面管理器
    desktop_manager = DesktopManager()
    desktop_manager.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 