import sys
import os
import json
import subprocess
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLabel, QSystemTrayIcon, QMenu, 
                             QDesktopWidget, QToolButton, QFrame, QSizePolicy,
                             QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QFileSystemWatcher, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient
import config
from pet_widget import PetWidget
from chat_widget import ChatWidget
from transition_screen import TransitionScreen
from openai_api import OpenAIChat
from tuopo_widget import TuopoWidget
import api_config

class TaskSubmissionWorker(QThread):
    """任务提交工作线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(str)  # 进度更新信号
    task_completed = pyqtSignal(str)    # 任务完成信号
    error_occurred = pyqtSignal(str)    # 错误信号
    
    def __init__(self, api_base_url=None):
        super().__init__()
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """执行任务提交流程"""
        try:
            # 步骤1：获取访问令牌（这里需要用户名和密码，实际使用时需要从配置或输入获取）
            self.progress_updated.emit("正在获取访问令牌...")
            if not self.authenticate():
                self.error_occurred.emit("认证失败，请检查用户名和密码")
                return
            
            # 步骤2：获取当前用户的任务
            self.progress_updated.emit("正在获取任务列表...")
            tasks = self.get_my_tasks()
            if not tasks:
                self.task_completed.emit("没有找到待提交的任务")
                return
                
            # 步骤3：提交任务
            self.progress_updated.emit(f"找到 {len(tasks)} 个任务，正在提交...")
            submitted_count = 0
            
            for task in tasks:
                # 只提交状态为"进行中"的任务
                if task.get('status') == api_config.TASK_STATUS["PENDING"]:
                    if self.submit_task(task['id']):
                        submitted_count += 1
                        self.progress_updated.emit(f"已提交任务: {task.get('task_name', '未命名任务')}")
                        
            self.task_completed.emit(f"任务提交完成！共提交了 {submitted_count} 个任务")
            
        except Exception as e:
            self.error_occurred.emit(f"任务提交失败: {str(e)}")
            
    def authenticate(self):
        """用户认证"""
        try:
            # 使用配置文件中的认证信息
            auth_data = {
                "login_type": api_config.DEFAULT_LOGIN_TYPE,
                "username": api_config.DEFAULT_USERNAME,
                "password": api_config.DEFAULT_PASSWORD,
                "grant_type": "password"
            }
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['login']}",
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return True
            else:
                print(f"认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"认证异常: {str(e)}")
            return False
            
    def get_my_tasks(self):
        """获取当前用户的任务"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['my_tasks']}",
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取任务失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"获取任务异常: {str(e)}")
            return []
            
    def submit_task(self, assignment_id):
        """提交单个任务"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 更新任务状态为"已完成"，进度为100%
            update_data = {
                "status": api_config.TASK_STATUS["COMPLETED"],
                "progress": 100,
                "comments": "通过桌面管理器自动提交完成"
            }
            
            response = requests.put(
                f"{self.api_base_url}/api/my-tasks/{assignment_id}",
                json=update_data,
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"提交任务失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"提交任务异常: {str(e)}")
            return False

class DesktopManager(QWidget):
    """桌面管理器 - 在桌面顶部悬浮显示"""
    
    # 定义信号
    show_settings = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.pet_widget = None
        self.chat_widget = None
        self.tuopo_widget = None  # 添加拓扑图窗口实例
        self.transition_page = None
        self.openai_chat = None  # 添加OpenAI聊天实例
        self.is_expanded = False
        self.current_role_data = None  # 当前角色数据
        self.role_avatar_label = None  # 角色头像标签
        self.role_name_label = None  # 角色名称标签
        self.role_desc_label = None  # 角色描述标签
        self.file_watcher = None  # 文件监视器
        self.task_worker = None  # 任务提交工作线程
        self.setup_file_watcher()  # 设置文件监视器
        self.load_role_data()  # 加载角色数据
        self.setup_ui()
        self.setup_timer()
        self.setup_animations()
        self.position_at_top()
        
    def setup_file_watcher(self):
        """设置文件监视器来监听JSON文件变化"""
        self.file_watcher = QFileSystemWatcher()
        json_file_path = os.path.join(os.getcwd(), "received_data.json")
        if os.path.exists(json_file_path):
            self.file_watcher.addPath(json_file_path)
            self.file_watcher.fileChanged.connect(self.on_json_file_changed)
            
    def on_json_file_changed(self):
        """当JSON文件发生变化时的处理函数"""
        self.load_role_data()
        self.update_role_display()
        
    def load_role_data(self):
        """从JSON文件加载角色数据"""
        try:
            json_file_path = os.path.join(os.getcwd(), "received_data.json")
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_role_data = data
                    print(f"已加载角色数据: {data.get('selectedRole', {}).get('label', '未知角色')}")
            else:
                print("未找到received_data.json文件")
                self.current_role_data = None
        except Exception as e:
            print(f"加载角色数据失败: {str(e)}")
            self.current_role_data = None
            
    def get_role_image_path(self, role_name):
        """根据角色名称获取对应的图片路径"""
        # 角色名称到图片文件名的映射
        role_image_mapping = {
            "网络工程师": "network_engineer.jpg",
            "系统架构师": "system_architect.jpg", 
            "系统规划与管理师": "Network_Planning_and_Management_Engineer.jpg"
        }
        
        image_filename = role_image_mapping.get(role_name, "network_engineer.jpg")  # 默认使用网络工程师图片
        image_path = os.path.join("image", "engineer", image_filename)
        
        if os.path.exists(image_path):
            return image_path
        else:
            # 如果找不到对应图片，尝试使用默认图片
            default_path = os.path.join("image", "engineer", "network_engineer.jpg")
            return default_path if os.path.exists(default_path) else None
        
    def setup_ui(self):
        """设置UI界面"""
        # 设置窗口属性 - 桌面顶部悬浮
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口大小 - 增加宽度以容纳角色信息
        self.setFixedHeight(80)
        self.setMinimumWidth(1000)
        
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
        
        # 左侧 - 角色信息区域
        self.create_role_section(frame_layout)
        
        # 分隔符1
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("QFrame { color: rgba(255, 255, 255, 100); }")
        frame_layout.addWidget(separator1)
        
        # 中间 - 系统信息区域
        self.create_info_section(frame_layout)
        
        # 分隔符2
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("QFrame { color: rgba(255, 255, 255, 100); }")
        frame_layout.addWidget(separator2)
        
        # 右侧 - 功能按钮区域
        self.create_buttons_section(frame_layout)
        
        # 添加背景框架到主布局
        main_layout.addWidget(self.background_frame)
        self.setLayout(main_layout)
        
        # 初始化角色显示
        self.update_role_display()
        
    def create_role_section(self, layout):
        """创建角色信息显示区域"""
        role_layout = QHBoxLayout()
        role_layout.setSpacing(10)
        
        # 角色头像
        self.role_avatar_label = QLabel()
        self.role_avatar_label.setFixedSize(55, 55)
        self.role_avatar_label.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(255, 255, 255, 150);
                border-radius: 27px;
                background: rgba(255, 255, 255, 50);
            }
        """)
        self.role_avatar_label.setScaledContents(True)
        
        # 角色信息文本区域
        role_text_layout = QVBoxLayout()
        role_text_layout.setSpacing(2)
        role_text_layout.setContentsMargins(0, 0, 0, 0)
        
        # 角色名称
        self.role_name_label = QLabel("当前角色")
        self.role_name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.role_name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
            }
        """)
        
        # 角色描述
        self.role_desc_label = QLabel("等待加载...")
        self.role_desc_label.setFont(QFont("Microsoft YaHei", 8))
        self.role_desc_label.setStyleSheet("""
            QLabel {
                color: #dcdde1;
                background: transparent;
            }
        """)
        
        # 添加到文本布局
        role_text_layout.addWidget(self.role_name_label)
        role_text_layout.addWidget(self.role_desc_label)
        
        # 添加到角色布局
        role_layout.addWidget(self.role_avatar_label)
        role_layout.addLayout(role_text_layout)
        role_layout.addStretch()
        
        layout.addLayout(role_layout)
        
    def update_role_display(self):
        """更新角色显示信息"""
        if not self.current_role_data:
            # 显示默认信息
            self.role_name_label.setText("当前角色")
            self.role_desc_label.setText("等待加载...")
            # 设置默认头像
            self.set_default_avatar()
            return
            
        # 获取角色信息
        selected_role = self.current_role_data.get('selectedRole', {})
        user_info = self.current_role_data.get('user', {})
        
        role_name = selected_role.get('label', '未知角色')
        role_desc = selected_role.get('description', '无描述')
        
        # 更新显示
        self.role_name_label.setText(role_name)
        self.role_desc_label.setText(role_desc)
        
        # 更新头像
        self.update_role_avatar(role_name)
        
        # 更新状态标签
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"当前角色: {role_name}")
            
    def update_role_avatar(self, role_name):
        """更新角色头像"""
        image_path = self.get_role_image_path(role_name)
        
        if image_path and os.path.exists(image_path):
            try:
                # 加载图片
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 创建圆形头像
                    rounded_pixmap = self.create_rounded_pixmap(pixmap, 55)
                    self.role_avatar_label.setPixmap(rounded_pixmap)
                    print(f"已加载角色头像: {image_path}")
                else:
                    print(f"无法加载图片: {image_path}")
                    self.set_default_avatar()
            except Exception as e:
                print(f"设置头像失败: {str(e)}")
                self.set_default_avatar()
        else:
            print(f"未找到角色图片: {image_path}")
            self.set_default_avatar()
            
    def create_rounded_pixmap(self, pixmap, size):
        """创建圆形图片"""
        # 缩放图片
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        # 创建圆形遮罩
        rounded_pixmap = QPixmap(size, size)
        rounded_pixmap.fill(Qt.transparent)
        
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆形
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        # 设置混合模式并绘制图片
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()
        
        return rounded_pixmap
        
    def set_default_avatar(self):
        """设置默认头像"""
        # 创建默认头像 - 一个简单的用户图标
        pixmap = QPixmap(55, 55)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景圆
        painter.setBrush(QColor(100, 149, 237))  # 蓝色背景
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 55, 55)
        
        # 绘制用户图标 (简单的人形)
        painter.setPen(Qt.white)
        painter.setBrush(Qt.white)
        
        # 头部
        painter.drawEllipse(20, 12, 15, 15)
        # 身体
        painter.drawEllipse(16, 27, 23, 23)
        
        painter.end()
        
        self.role_avatar_label.setPixmap(pixmap)
        
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
            ("🗺️", "拓扑图", self.show_tuopo, "#3498db"),
            ("🐱", "宠物", self.show_pet, "#e74c3c"),
            ("💬", "聊天", self.show_chat, "#2ecc71"),
            ("⚙️", "设置", self.show_settings_action, "#f39c12"),
            ("📤", "任务提交", self.submit_tasks, "#9b59b6"),
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
        
    def show_tuopo(self):
        """显示/隐藏拓扑图"""
        if not self.tuopo_widget:
            self.tuopo_widget = TuopoWidget()
            
        if self.tuopo_widget.isVisible():
            self.tuopo_widget.hide()
            self.status_label.setText("拓扑图已隐藏")
        else:
            self.tuopo_widget.show()
            self.status_label.setText("拓扑图已显示")
            
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
        
    def submit_tasks(self):
        """提交任务"""
        # 如果已有任务在执行，不允许重复提交
        if self.task_worker and self.task_worker.isRunning():
            QMessageBox.information(self, "提示", "任务提交正在进行中，请稍等...")
            return
            
        # 创建任务工作线程
        self.task_worker = TaskSubmissionWorker()
        
        # 连接信号
        self.task_worker.progress_updated.connect(self.on_task_progress_updated)
        self.task_worker.task_completed.connect(self.on_task_completed)
        self.task_worker.error_occurred.connect(self.on_task_error)
        
        # 开始任务提交
        self.status_label.setText("正在准备任务提交...")
        self.task_worker.start()
        
    @pyqtSlot(str)
    def on_task_progress_updated(self, message):
        """任务进度更新回调"""
        self.status_label.setText(message)
        print(f"任务进度: {message}")
        
    @pyqtSlot(str) 
    def on_task_completed(self, message):
        """任务完成回调"""
        self.status_label.setText(message)
        print(f"任务完成: {message}")
        
        # 显示完成对话框
        QMessageBox.information(self, "任务提交完成", message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    @pyqtSlot(str)
    def on_task_error(self, error_message):
        """任务错误回调"""
        self.status_label.setText(f"任务提交失败")
        print(f"任务错误: {error_message}")
        
        # 显示错误对话框
        QMessageBox.warning(self, "任务提交失败", error_message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    def exit_application(self):
        """退出应用程序并启动全屏浏览器"""
        print("开始退出desktop_manager应用...")
        
        # 步骤1：清理资源 - 关闭所有子窗口
        self.close_all_windows()
        
        # 步骤2：启动独立过渡页面，然后启动全屏浏览器
        self.start_independent_transition_and_browser()
        
        # 步骤3：退出desktop_manager应用
        QTimer.singleShot(100, QApplication.quit)
        
    def close_all_windows(self):
        """关闭所有子窗口"""
        print("正在清理资源和关闭所有子窗口...")
        
        # 关闭所有子窗口
        if self.pet_widget:
            self.pet_widget.close()
            print("宠物窗口已关闭")
        if self.chat_widget:
            self.chat_widget.close()
            print("聊天窗口已关闭")
        if self.tuopo_widget:
            self.tuopo_widget.close()
            print("拓扑图窗口已关闭")
        if self.transition_page:
            self.transition_page.close()
            print("过渡页面已关闭")
            
        print("所有子窗口清理完成")
        
    def start_independent_transition_and_browser(self):
        """启动独立过渡页面，然后启动全屏浏览器"""
        try:
            # 查找独立过渡页面脚本
            script_path = os.path.join(os.path.dirname(__file__), "independent_transition.py")
            if not os.path.exists(script_path):
                script_path = "independent_transition.py"
            
            if not os.path.exists(script_path):
                print("警告：找不到independent_transition.py，直接启动全屏浏览器")
                self.launch_fullscreen_browser_directly()
                return
            
            # 启动独立过渡页面进程
            # 传递参数：信息文本、持续时间、启动浏览器标志
            subprocess.Popen([
                sys.executable, 
                script_path,
                "正在切换到全屏网页...",
                "3000",
                "--launch-browser"
            ])
            print("独立过渡页面已启动，将在3秒后启动全屏浏览器")
            
        except Exception as e:
            print(f"启动独立过渡页面失败: {str(e)}")
            print("回退到直接启动全屏浏览器")
            self.launch_fullscreen_browser_directly()
    
    def launch_fullscreen_browser_directly(self):
        """直接启动全屏浏览器（备用方案）"""
        try:
            subprocess.Popen([sys.executable, "fullscreen_browser.py"])
            print("全屏浏览器已直接启动")
        except Exception as e:
            print(f"启动全屏浏览器失败: {str(e)}")
        
    def launch_fullscreen_and_exit(self):
        """启动全屏浏览器并关闭桌面管理器 - 已弃用，保留兼容性"""
        print("注意：launch_fullscreen_and_exit方法已弃用，请使用新的退出流程")
        self.exit_application()
        
    def close_all_and_exit(self):
        """关闭所有窗口并退出 - 已弃用，保留兼容性"""
        print("注意：close_all_and_exit方法已弃用，请使用新的退出流程")
        self.exit_application()
        
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
            self.show_tuopo()
        super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """关闭事件"""
        # 清理任务工作线程
        if self.task_worker and self.task_worker.isRunning():
            self.task_worker.terminate()
            self.task_worker.wait()
            
        # 阻止默认的关闭行为
        event.ignore()
        # 调用退出应用程序方法，显示过渡页面并启动全屏浏览器
        self.exit_application()


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