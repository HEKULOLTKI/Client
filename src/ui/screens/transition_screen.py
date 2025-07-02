from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar, 
                            QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QRectF, QEasingCurve, QSize, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QPainterPath
import random
import math

class LoadingDotsWidget(QWidget):
    def __init__(self, parent=None, dot_count=5, dot_size=15, color=QColor(0, 176, 255)):
        super().__init__(parent)
        self.dot_count = dot_count
        self.dot_size = dot_size
        self.color = color
        self.positions = [0] * dot_count
        self.offset = 0
        
        # 创建动画定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(80)
        
        # 设置合适的大小
        self.setFixedHeight(dot_size * 3)
        self.setMinimumWidth(dot_count * dot_size * 3)
    
    def update_animation(self):
        self.offset = (self.offset + 1) % 60
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_y = self.height() / 2
        width = self.width()
        dot_spacing = width / (self.dot_count + 1)
        
        for i in range(self.dot_count):
            # 计算偏移的相位，使点按顺序上下移动
            phase = (self.offset + i * 10) % 60
            if phase > 30:
                phase = 60 - phase
            
            # 计算垂直位置
            y_offset = math.sin(phase * math.pi / 30) * self.dot_size
            
            # 设置颜色，带透明度变化
            alpha = 100 + 155 * (phase / 30.0)
            dot_color = QColor(self.color.red(), self.color.green(), self.color.blue(), int(alpha))
            
            # 绘制点
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.NoPen)
            
            x = (i + 1) * dot_spacing
            y = center_y + y_offset
            
            # 将点大小也随相位变化
            size_factor = 0.6 + 0.4 * (phase / 30.0)
            current_size = self.dot_size * size_factor
            
            painter.drawEllipse(QRectF(x - current_size/2, y - current_size/2, current_size, current_size))
    
    def start(self):
        self.timer.start()
    
    def stop(self):
        self.timer.stop()

class CircularProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self._max_progress = 100
        
        # 创建动画定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)
        
        # 动画参数
        self.rotation_angle = 0
        self.dot_size = 0
        self.dot_direction = 1
        
        # 设置合适的大小
        self.setFixedSize(120, 120)
    
    def update_animation(self):
        # 更新旋转角度
        self.rotation_angle = (self.rotation_angle + 5) % 360
        
        # 更新圆点大小（脉冲效果）
        self.dot_size += 0.2 * self.dot_direction
        if self.dot_size > 5 or self.dot_size < 1:
            self.dot_direction *= -1
        
        self.update()
    
    def set_progress(self, value):
        self._progress = max(0, min(value, self._max_progress))
        self.update()
    
    def get_progress(self):
        return self._progress
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - 10
        
        # 绘制背景圆环
        painter.setPen(QPen(QColor(100, 150, 200, 50), 6))
        painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius*2, radius*2))
        
        # 绘制进度圆环
        arc_rect = QRectF(center_x - radius, center_y - radius, radius*2, radius*2)
        progress_pen = QPen(QColor(0, 160, 233), 6)
        progress_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(progress_pen)
        
        # 计算进度角度
        progress_angle = int(360 * self._progress / self._max_progress)
        
        # 绘制进度扇形
        painter.drawArc(arc_rect, (90 - self.rotation_angle) * 16, -progress_angle * 16)
        
        # 绘制旋转中的小圆点
        dot_angle = math.radians(self.rotation_angle)
        dot_x = center_x + radius * math.cos(dot_angle)
        dot_y = center_y - radius * math.sin(dot_angle)
        
        painter.setBrush(QBrush(QColor(0, 200, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(dot_x - self.dot_size, dot_y - self.dot_size, self.dot_size*2, self.dot_size*2))
        
        # 绘制百分比文本
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(200, 230, 250))
        painter.drawText(arc_rect, Qt.AlignCenter, f"{int(self._progress)}%")
    
    def start(self):
        self.timer.start()
    
    def stop(self):
        self.timer.stop()

class GlowingBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0
        self._max_progress = 100
        
        # 动画参数
        self.glow_pos = 0
        self.glow_direction = 1
        
        # 创建动画定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)
        
        # 设置合适的大小
        self.setFixedHeight(30)
        self.setMinimumWidth(300)
    
    def update_animation(self):
        # 更新光晕位置
        if self._progress < 100:
            self.glow_pos += 5
            if self.glow_pos > self.width() + 100:
                self.glow_pos = -100
        else:
            # 当进度达到100%时，使用不同的动画效果
            self.glow_pos = (self.glow_pos + 10) % self.width()
        
        self.update()
    
    def set_progress(self, value):
        self._progress = max(0, min(value, self._max_progress))
        self.update()
    
    def get_progress(self):
        return self._progress
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 绘制背景
        bg_rect = QRectF(0, 0, width, height)
        bg_brush = QBrush(QColor(10, 35, 60, 100))
        painter.setPen(QPen(QColor(0, 120, 200, 120), 2))
        painter.setBrush(bg_brush)
        painter.drawRoundedRect(bg_rect, height/2, height/2)
        
        # 绘制进度
        if self._progress > 0:
            progress_width = (width - 4) * self._progress / self._max_progress
            progress_rect = QRectF(2, 2, progress_width, height - 4)
            
            # 进度条渐变
            progress_gradient = QLinearGradient(0, 0, width, 0)
            progress_gradient.setColorAt(0, QColor(0, 100, 200, 200))
            progress_gradient.setColorAt(0.5, QColor(0, 150, 230, 230))
            progress_gradient.setColorAt(1, QColor(0, 120, 210, 200))
            
            progress_brush = QBrush(progress_gradient)
            painter.setPen(Qt.NoPen)
            painter.setBrush(progress_brush)
            painter.drawRoundedRect(progress_rect, (height-4)/2, (height-4)/2)
            
            # 绘制光晕效果
            if self.glow_pos > -50 and self.glow_pos < width + 50:
                glow_gradient = QLinearGradient(self.glow_pos - 50, 0, self.glow_pos + 50, 0)
                glow_gradient.setColorAt(0, QColor(100, 200, 255, 0))
                glow_gradient.setColorAt(0.5, QColor(150, 230, 255, 150))
                glow_gradient.setColorAt(1, QColor(100, 200, 255, 0))
                
                painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
                painter.setBrush(QBrush(glow_gradient))
                painter.drawRoundedRect(progress_rect, (height-4)/2, (height-4)/2)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # 绘制文本
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(220, 240, 255))
        painter.drawText(bg_rect, Qt.AlignCenter, f"{int(self._progress)}%")
    
    def start(self):
        self.timer.start()
    
    def stop(self):
        self.timer.stop()

class TransitionScreen(QDialog):
    # 添加完成信号
    finished = pyqtSignal()
    
    def __init__(self, message="正在加载，请稍候...", duration=2000):
        """
        创建高级科技感过渡界面
        
        参数:
            message: 显示的消息文本
            duration: 自动关闭的时间（毫秒）
        """
        super().__init__()
        self.duration = duration
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        
        # 更新背景样式为更高级的科技风
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #0c1a30, stop:0.5 #0d2048, stop:1 #0a1f3f);
                border: 2px solid #00a0e9;
                border-radius: 15px;
            }
            QLabel {
                background: transparent;
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.setSpacing(25)
        
        # 添加顶部装饰条
        top_line = QWidget()
        top_line.setFixedHeight(3)
        top_line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                     stop:0 rgba(0, 100, 255, 0), 
                                     stop:0.5 rgba(0, 160, 233, 255), 
                                     stop:1 rgba(0, 100, 255, 0));
        """)
        main_layout.addWidget(top_line)
        
        # 添加标题标签
        self.title_label = QLabel(message)
        self.title_label.setStyleSheet("""
            color: #00ccff;
            font-size: 38px;
            font-weight: bold;
            text-shadow: 0 0 15px rgba(0, 180, 255, 150);
            letter-spacing: 2px;
            padding: 15px;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)
        
        # 添加二进制码标签
        self.binary_label = QLabel()
        self.binary_label.setAlignment(Qt.AlignCenter)
        self.binary_label.setStyleSheet("""
            color: rgba(0, 190, 255, 0.4);
            font-family: 'Courier New', monospace;
            font-size: 16px;
            letter-spacing: 1px;
            margin: 5px 0 15px 0;
        """)
        self.update_binary_code()
        main_layout.addWidget(self.binary_label)
        
        # 创建加载动画容器
        loading_container = QWidget()
        loading_container.setStyleSheet("background: transparent;")
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setContentsMargins(40, 0, 40, 0)
        loading_layout.setSpacing(5)
        
        # 创建不同的加载动画部件
        self.loading_style = 0  # 默认使用点阵动画
        
        # 1. 波动的点阵
        self.dots_widget = LoadingDotsWidget(dot_count=7, dot_size=12, color=QColor(0, 200, 255))
        loading_layout.addWidget(self.dots_widget, 0, Qt.AlignCenter)
        
        # 2. 圆形进度条
        self.circular_widget = CircularProgressWidget()
        loading_layout.addWidget(self.circular_widget, 0, Qt.AlignCenter)
        self.circular_widget.hide()  # 默认隐藏
        
        # 3. 高级进度条
        self.glowing_bar = GlowingBarWidget()
        loading_layout.addWidget(self.glowing_bar, 0, Qt.AlignCenter)
        self.glowing_bar.hide()  # 默认隐藏
        
        main_layout.addWidget(loading_container)
        
        # 添加额外的信息标签
        self.info_label = QLabel("正在初始化...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            color: #80d8ff;
            font-size: 22px;
            margin-top: 10px;
            font-weight: normal;
        """)
        main_layout.addWidget(self.info_label)
        
        # 添加底部装饰条
        bottom_line = QWidget()
        bottom_line.setFixedHeight(3)
        bottom_line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                     stop:0 rgba(0, 100, 255, 0), 
                                     stop:0.5 rgba(0, 160, 233, 255), 
                                     stop:1 rgba(0, 100, 255, 0));
        """)
        main_layout.addWidget(bottom_line)
        
        # 进度信息
        self.progress_texts = [
            "正在关闭全屏网页...",
            "正在清理浏览器资源...",
            "正在启动云桌面...",
            "云桌面即将启动..."
        ]
        
        # 创建更新二进制码的计时器
        self.binary_timer = QTimer(self)
        self.binary_timer.timeout.connect(self.update_binary_code)
        
        # 创建进度更新计时器
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        
        # 创建自动关闭计时器
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self._on_close_timeout)
        
        # 为标题创建闪烁效果
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_value = 0
        self.glow_direction = 1
        
        # 当前进度值
        self.current_progress = 0
    
    def set_loading_style(self, style):
        """设置加载动画的样式
        
        参数:
            style: 0=波动点阵, 1=圆形进度条, 2=发光进度条
        """
        self.loading_style = style
        
        # 隐藏所有加载动画
        self.dots_widget.hide()
        self.circular_widget.hide()
        self.glowing_bar.hide()
        
        # 显示选择的动画
        if style == 0:
            self.dots_widget.show()
        elif style == 1:
            self.circular_widget.show()
        elif style == 2:
            self.glowing_bar.show()
    
    def update_binary_code(self):
        """更新二进制码标签内容"""
        binary_code = ' '.join([''.join([str(random.randint(0, 1)) for _ in range(8)]) for _ in range(6)])
        self.binary_label.setText(binary_code)
    
    def update_progress(self):
        """更新进度条和信息标签"""
        if self.current_progress < 100:
            self.current_progress += 1
            
            # 更新所有进度控件（无论是否可见）
            self.circular_widget.set_progress(self.current_progress)
            self.glowing_bar.set_progress(self.current_progress)
            
            # 根据进度更新信息文本
            if self.current_progress < 25:
                self.info_label.setText(self.progress_texts[0])
            elif self.current_progress < 50:
                self.info_label.setText(self.progress_texts[1])
            elif self.current_progress < 75:
                self.info_label.setText(self.progress_texts[2])
            else:
                self.info_label.setText(self.progress_texts[3])
        else:
            pass  # 保持动画直到关闭
    
    def update_glow(self):
        """更新标题闪烁效果"""
        self.glow_value += 5 * self.glow_direction
        if self.glow_value > 150 or self.glow_value < 50:
            self.glow_direction *= -1
        
        # 更新标题文字阴影
        self.title_label.setStyleSheet(f"""
            color: #00ccff;
            font-size: 38px;
            font-weight: bold;
            text-shadow: 0 0 15px rgba(0, 180, 255, {self.glow_value});
            letter-spacing: 2px;
            padding: 15px;
        """)
    
    def show_transition(self, custom_message=None, custom_duration=None, loading_style=None):
        """显示过渡界面并开始动画
        
        参数:
            custom_message: 自定义消息
            custom_duration: 自定义持续时间
            loading_style: 加载样式 (0=点阵, 1=圆形, 2=进度条)
        """
        if custom_message:
            self.title_label.setText(custom_message)
        
        duration = custom_duration if custom_duration is not None else self.duration
        
        # 设置加载样式
        if loading_style is not None:
            self.set_loading_style(loading_style)
        
        # 启动二进制码更新计时器
        self.binary_timer.start(400)
        
        # 启动进度更新计时器
        self.current_progress = 0
        update_interval = min(30, duration // 100)  # 确保进度条能在指定时间内完成
        self.progress_timer.start(update_interval)
        
        # 启动闪烁效果
        self.glow_timer.start(100)
        
        # 设置自动关闭计时器
        self.close_timer.start(duration)
        
        # 显示对话框（非阻塞）
        self.showFullScreen()
        self.show()
    
    def paintEvent(self, event):
        """自定义绘制，添加简单的装饰效果"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制四个角的装饰
        pen = QPen(QColor(0, 160, 233, 180))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # 左上角
        painter.drawLine(20, 20, 50, 20)
        painter.drawLine(20, 20, 20, 50)
        
        # 右上角
        painter.drawLine(self.width() - 50, 20, self.width() - 20, 20)
        painter.drawLine(self.width() - 20, 20, self.width() - 20, 50)
        
        # 左下角
        painter.drawLine(20, self.height() - 20, 50, self.height() - 20)
        painter.drawLine(20, self.height() - 50, 20, self.height() - 20)
        
        # 右下角
        painter.drawLine(self.width() - 50, self.height() - 20, self.width() - 20, self.height() - 20)
        painter.drawLine(self.width() - 20, self.height() - 50, self.width() - 20, self.height() - 20)
    
    def _on_close_timeout(self):
        """计时器超时回调，发出完成信号并关闭对话框"""
        print("⏰ 过渡页面计时器超时，准备关闭...")
        print("📡 正在发出finished信号...")
        self.finished.emit()  # 发出完成信号
        print("✅ finished信号已发出")
        print("🚪 正在关闭过渡页面...")
        self.close()  # 关闭对话框
        print("✅ 过渡页面已关闭")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止所有计时器
        self.binary_timer.stop()
        self.progress_timer.stop()
        self.close_timer.stop()
        self.glow_timer.stop()
        
        # 停止所有加载动画
        self.dots_widget.stop()
        self.circular_widget.stop()
        self.glowing_bar.stop()
        
        event.accept() 