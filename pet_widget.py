from PyQt5.QtWidgets import QLabel, QApplication, QDesktopWidget
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
import config

class PetWidget(QLabel):  # 确保类名为 PetWidget
    doubleClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口标志
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化动画
        self.animations = {
            "idle": QMovie(config.PET_IDLE),
            "wave": QMovie(config.PET_WAVE),
            "happy": QMovie(config.PET_HAPPY)
        }
        
        # 设置动画大小
        size = QSize(config.PET_SIZE[0], config.PET_SIZE[1])
        for movie in self.animations.values():
            movie.setScaledSize(size)
        
        # 设置窗口大小
        self.setFixedSize(config.PET_SIZE[0], config.PET_SIZE[1])
        
        # 设置默认动画
        self.current_animation = "idle"
        self.setMovie(self.animations[self.current_animation])
        self.animations[self.current_animation].start()
        
        # 初始化动画计时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.reset_animation)
        
        # 初始化拖动变量
        self._drag_pos = None
        
        # 设置宠物出现在屏幕的右侧中间靠下位置
        self.position_pet_at_start()

    def position_pet_at_start(self):
        """将宠物放置在屏幕右侧中间靠下位置"""
        # 获取屏幕尺寸
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        
        # 计算位置 (右侧中间靠下)
        # 右侧: x坐标为屏幕宽度减去宠物宽度再减去一些边距
        # 中间靠下: y坐标为屏幕高度的2/3位置
        x_pos = screen_width - self.width() - 20  # 20像素作为右边距
        y_pos = int(screen_height * 0.7)  # 屏幕高度的70%位置
        
        # 设置位置
        self.move(x_pos, y_pos)

    def play_animation(self, animation_name, duration=None):
        """播放指定的动画"""
        if animation_name in self.animations:
            self.current_animation = animation_name
            current_movie = self.animations[animation_name]
            self.setMovie(current_movie)
            current_movie.start()
            
            if duration:
                self.animation_timer.start(duration)

    def reset_animation(self):
        """重置为默认动画"""
        self.animation_timer.stop()
        self.play_animation("idle")

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.play_animation("wave", 1000)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self._drag_pos = None

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件"""
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
            self.play_animation("happy", 1000)