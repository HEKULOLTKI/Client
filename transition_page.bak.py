from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QApplication, QDesktopWidget, QPushButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEasingCurve, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QBrush
import sys
import config

class TransitionPage(QWidget):
    """过渡页面组件"""
    
    # 定义信号
    transition_completed = pyqtSignal()
    force_close = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """设置UI界面"""
        # 设置窗口属性 - 确保真正全屏
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # 移除透明背景属性，改为不透明背景
        # self.setAttribute(Qt.WA_TranslucentBackground)  # 注释掉这行
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # 获取屏幕尺寸并设置全屏
        desktop = QApplication.desktop()
        screen_rect = desktop.screenGeometry()
        self.setGeometry(screen_rect)
        
        # 确保窗口全屏显示
        self.showFullScreen()
        
        # 设置完全不透明的黑色背景
        self.setStyleSheet("""
            QWidget {
                background-color: rgb(0, 0, 0);
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        
        # 创建内容容器
        content_widget = QWidget()
        content_widget.setFixedSize(400, 300)
        content_widget.setStyleSheet("""
            QWidget {
                background-color: rgb(255, 255, 255);
                border-radius: 20px;
                border: 2px solid rgb(100, 149, 237);
            }
        """)
        
        # 内容布局
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        self.title_label = QLabel("正在关闭网页...")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                padding: 10px;
            }
        """)
        
        # 状态标签
        self.status_label = QLabel("请稍候，正在处理中...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Microsoft YaHei", 12))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background: transparent;
                padding: 5px;
            }
        """)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 4px;
            }
        """)
        
        # 按钮容器
        button_container = QHBoxLayout()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedSize(80, 35)
        self.cancel_button.setFont(QFont("Microsoft YaHei", 10))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 17px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        self.cancel_button.clicked.connect(self.cancel_transition)
        
        # 强制关闭按钮
        self.force_close_button = QPushButton("强制关闭")
        self.force_close_button.setFixedSize(80, 35)
        self.force_close_button.setFont(QFont("Microsoft YaHei", 10))
        self.force_close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 17px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.force_close_button.clicked.connect(self.force_close_action)
        
        # 添加按钮到容器
        button_container.addStretch()
        button_container.addWidget(self.cancel_button)
        button_container.addSpacing(10)
        button_container.addWidget(self.force_close_button)
        button_container.addStretch()
        
        # 添加组件到内容布局
        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.status_label)
        content_layout.addWidget(self.progress_bar)
        content_layout.addStretch()
        content_layout.addLayout(button_container)
        
        # 添加内容容器到主布局
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)
        
    def setup_animations(self):
        """设置动画"""
        # 进度动画定时器
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
        # 淡入动画定时器
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self.fade_in_step)
        
        # 完成动画定时器
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.timeout.connect(self.complete_transition)
        
        # 初始化动画变量
        self.current_progress = 0
        self.progress_step = 2
        self.fade_opacity = 0.0
        self.fade_step = 0.05
        
    def start_transition(self, duration=3000, message="正在关闭网页..."):
        """开始过渡动画"""
        # 设置消息
        self.title_label.setText(message)
        self.status_label.setText("请稍候，正在处理中...")
        
        # 重置进度
        self.current_progress = 0
        self.progress_bar.setValue(0)
        
        # 计算进度步长
        self.progress_step = 100 / (duration / 50)  # 每50ms更新一次
        
        # 显示窗口并确保全屏
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        
        # 开始淡入动画
        self.fade_opacity = 0.0
        self.fade_timer.start(20)  # 20ms间隔
        
        # 开始进度动画
        self.progress_timer.start(50)  # 50ms间隔
        
        # 设置完成定时器
        self.completion_timer.start(duration)
        
    def fade_in_step(self):
        """淡入动画步骤"""
        self.fade_opacity += self.fade_step
        if self.fade_opacity >= 1.0:
            self.fade_opacity = 1.0
            self.fade_timer.stop()
        
        # 应用透明度效果
        self.setWindowOpacity(self.fade_opacity)
        
    def update_progress(self):
        """更新进度条"""
        self.current_progress += self.progress_step
        if self.current_progress >= 100:
            self.current_progress = 100
            self.progress_timer.stop()
            
        self.progress_bar.setValue(int(self.current_progress))
        
        # 更新状态文本
        if self.current_progress < 30:
            self.status_label.setText("正在保存数据...")
        elif self.current_progress < 60:
            self.status_label.setText("正在关闭网页...")
        elif self.current_progress < 90:
            self.status_label.setText("正在清理缓存...")
        else:
            self.status_label.setText("即将完成...")
            
    def complete_transition(self):
        """完成过渡"""
        self.progress_timer.stop()
        self.progress_bar.setValue(100)
        self.status_label.setText("处理完成！")
        
        # 延迟500ms后发送完成信号
        QTimer.singleShot(500, self.emit_completion_signal)
        
    def emit_completion_signal(self):
        """发送完成信号"""
        self.transition_completed.emit()
        self.close()
        
    def cancel_transition(self):
        """取消过渡"""
        self.progress_timer.stop()
        self.completion_timer.stop()
        self.fade_timer.stop()
        self.close()
        
    def force_close_action(self):
        """强制关闭"""
        self.force_close.emit()
        self.close()
        
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.cancel_transition()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.force_close_action()
        super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """关闭事件"""
        self.progress_timer.stop()
        self.completion_timer.stop()
        self.fade_timer.stop()
        super().closeEvent(event)


# 使用示例
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建过渡页面
    transition = TransitionPage()
    
    # 连接信号
    def on_transition_completed():
        print("过渡完成！")
        app.quit()
    
    def on_force_close():
        print("强制关闭！")
        app.quit()
    
    transition.transition_completed.connect(on_transition_completed)
    transition.force_close.connect(on_force_close)
    
    # 开始过渡动画
    transition.start_transition(3000, "正在关闭网页...")
    
    sys.exit(app.exec_()) 