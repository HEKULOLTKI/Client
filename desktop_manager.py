import sys
import os
import json
import subprocess
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLabel, QSystemTrayIcon, QMenu, 
                             QDesktopWidget, QToolButton, QFrame, QSizePolicy,
                             QMessageBox, QDialog, QCheckBox, QScrollArea, 
                             QDialogButtonBox, QLineEdit, QComboBox, QFormLayout,
                             QTextEdit)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QFileSystemWatcher, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient
import config
from pet_widget import PetWidget
from chat_widget import ChatWidget
from transition_screen import TransitionScreen
from openai_api import OpenAIChat
from tuopo_widget import TuopoWidget
import api_config
import logging

# 禁用Flask的默认日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class TaskSelectionDialog(QDialog):
    """任务选择对话框"""
    
    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self.tasks = tasks
        self.selected_tasks = []
        self.task_checkboxes = {}
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("选择要提交的任务")
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel("请选择要提交的任务：")
        info_label.setFont(QFont("微软雅黑", 12))
        info_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #95a5a6;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7f8c8d;
            }
        """)
        
        # 任务列表容器
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        
        # 添加任务复选框
        for task in self.tasks:
            if task.get('status') == api_config.TASK_STATUS["PENDING"]:
                self.create_task_item(tasks_layout, task)
        
        if not self.task_checkboxes:
            # 如果没有待提交的任务
            no_tasks_label = QLabel("没有可提交的任务")
            no_tasks_label.setAlignment(Qt.AlignCenter)
            no_tasks_label.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
            tasks_layout.addWidget(no_tasks_label)
        
        scroll_area.setWidget(tasks_widget)
        layout.addWidget(scroll_area)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 全选/取消全选按钮
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all_tasks)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        button_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("取消全选")
        clear_all_btn.clicked.connect(self.clear_all_tasks)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(clear_all_btn)
        
        button_layout.addStretch()
        
        # 确定和取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("提交选中任务")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        button_box.button(QDialogButtonBox.Ok).setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_box.button(QDialogButtonBox.Cancel).setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(button_box)
        layout.addLayout(button_layout)
        
    def create_task_item(self, layout, task):
        """创建任务项"""
        # 创建任务框架
        task_frame = QFrame()
        task_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin: 2px;
                padding: 5px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f7f9fc;
            }
        """)
        
        task_layout = QHBoxLayout(task_frame)
        task_layout.setContentsMargins(10, 8, 10, 8)
        
        # 复选框
        checkbox = QCheckBox()
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 3px;
                background-color: #3498db;
                image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>);
            }
        """)
        task_layout.addWidget(checkbox)
        
        # 任务信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 任务名称
        name_label = QLabel(task.get('task_name', '未命名任务'))
        name_label.setFont(QFont("微软雅黑", 11, QFont.Bold))
        name_label.setStyleSheet("color: #2c3e50;")
        info_layout.addWidget(name_label)
        
        # 任务详情
        details = []
        if task.get('task_type'):
            details.append(f"类型: {task['task_type']}")
        if task.get('task_phase'):
            details.append(f"阶段: {task['task_phase']}")
        details.append(f"进度: {task.get('progress', 0)}%")
        
        details_label = QLabel(" | ".join(details))
        details_label.setFont(QFont("微软雅黑", 9))
        details_label.setStyleSheet("color: #7f8c8d;")
        info_layout.addWidget(details_label)
        
        task_layout.addLayout(info_layout)
        task_layout.addStretch()
        
        # 保存复选框引用
        self.task_checkboxes[task['id']] = checkbox
        
        layout.addWidget(task_frame)
        
    def select_all_tasks(self):
        """全选任务"""
        for checkbox in self.task_checkboxes.values():
            checkbox.setChecked(True)
            
    def clear_all_tasks(self):
        """取消全选"""
        for checkbox in self.task_checkboxes.values():
            checkbox.setChecked(False)
            
    def accept_selection(self):
        """确认选择"""
        self.selected_tasks = []
        for task_id, checkbox in self.task_checkboxes.items():
            if checkbox.isChecked():
                # 找到对应的任务
                for task in self.tasks:
                    if task['id'] == task_id:
                        self.selected_tasks.append(task)
                        break
        
        if not self.selected_tasks:
            QMessageBox.warning(self, "提示", "请至少选择一个任务进行提交！")
            return
            
        self.accept()
        
    def get_selected_tasks(self):
        """获取选中的任务"""
        return self.selected_tasks


class TaskSubmissionWorker(QThread):
    """任务提交工作线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(str)  # 进度更新信号
    task_completed = pyqtSignal(str)    # 任务完成信号
    error_occurred = pyqtSignal(str)    # 错误信号
    
    def __init__(self, selected_tasks=None, api_base_url=None):
        super().__init__()
        self.selected_tasks = selected_tasks or []
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """执行任务提交流程"""
        try:
            # 步骤1：获取访问令牌
            self.progress_updated.emit("正在获取访问令牌...")
            if not self.authenticate():
                self.error_occurred.emit("认证失败，请检查用户名和密码")
                return
            
            # 步骤2：提交选中的任务
            if not self.selected_tasks:
                self.task_completed.emit("没有选择要提交的任务")
                return
                
            self.progress_updated.emit(f"开始提交 {len(self.selected_tasks)} 个任务...")
            submitted_count = 0
            
            for i, task in enumerate(self.selected_tasks, 1):
                self.progress_updated.emit(f"正在提交任务 {i}/{len(self.selected_tasks)}: {task.get('task_name', '未命名任务')}")
                
                if self.submit_task(task['id']):
                    submitted_count += 1
                    self.progress_updated.emit(f"✓ 已提交任务: {task.get('task_name', '未命名任务')}")
                else:
                    self.progress_updated.emit(f"✗ 提交失败: {task.get('task_name', '未命名任务')}")
                        
            self.task_completed.emit(f"任务提交完成！成功提交 {submitted_count}/{len(self.selected_tasks)} 个任务")
            
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
                "comments": "通过桌面管理器选择提交完成"
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


class TaskListWorker(QThread):
    """获取任务列表的工作线程"""
    
    # 定义信号
    tasks_loaded = pyqtSignal(list)  # 任务加载完成信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, api_base_url=None):
        super().__init__()
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """获取任务列表"""
        try:
            # 认证
            if not self.authenticate():
                self.error_occurred.emit("认证失败，请检查用户名和密码")
                return
            
            # 获取任务列表
            tasks = self.get_my_tasks()
            self.tasks_loaded.emit(tasks)
            
        except Exception as e:
            self.error_occurred.emit(f"获取任务列表失败: {str(e)}")
            
    def authenticate(self):
        """用户认证"""
        try:
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
                return False
                
        except Exception as e:
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
                return []
                
        except Exception as e:
            return []


class DeviceAddDialog(QDialog):
    """设备添加对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("添加设备")
        self.setFixedSize(700, 550)
        self.setModal(True)
        
        # 设置对话框背景样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 10px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(15)
        

        
        # 表单容器
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(30, 25, 30, 25)
        form_layout.setVerticalSpacing(25)
        form_layout.setHorizontalSpacing(20)
        
        # 通用输入框样式
        input_style = """
            QLineEdit {
                padding: 15px 18px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 16px;
                font-family: '微软雅黑';
                background-color: #ffffff;
                color: #495057;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background-color: #f8f9ff;
            }
            QLineEdit:hover {
                border-color: #adb5bd;
            }
        """
        
        # 标签样式
        label_style = """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #495057;
                font-family: '微软雅黑';
            }
        """
        
        # 设备名称（必填）
        name_label = QLabel("设备名称*")
        name_label.setStyleSheet(label_style)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入添加设备的名称")
        self.name_edit.setStyleSheet(input_style)
        form_layout.addRow(name_label, self.name_edit)
        
        # 设备类型（改为输入框）
        type_label = QLabel("设备类型")
        type_label.setStyleSheet(label_style)
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("请输入设备类型，例如：路由器、交换机、防火墙等")
        self.type_edit.setStyleSheet(input_style)
        form_layout.addRow(type_label, self.type_edit)
        
        # IP地址
        ip_label = QLabel("IP地址")
        ip_label.setStyleSheet(label_style)
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("请输入IP地址，例如：192.168.1.100")
        self.ip_edit.setStyleSheet(input_style)
        form_layout.addRow(ip_label, self.ip_edit)
        
        # 设备位置
        location_label = QLabel("设备位置")
        location_label.setStyleSheet(label_style)
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("请输入设备位置，例如：机房A-机柜01-U10")
        self.location_edit.setStyleSheet(input_style)
        form_layout.addRow(location_label, self.location_edit)
        
        # 设备状态
        status_label = QLabel("设备状态")
        status_label.setStyleSheet(label_style)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["offline", "online", "maintenance"])
        self.status_combo.setCurrentText("offline")
        self.status_combo.setStyleSheet("""
            QComboBox {
                padding: 15px 18px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 16px;
                font-family: '微软雅黑';
                background-color: #ffffff;
                color: #495057;
                selection-background-color: #667eea;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #667eea;
                background-color: #f8f9ff;
            }
            QComboBox:hover {
                border-color: #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #667eea;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                font-size: 16px;
                font-family: '微软雅黑';
                selection-background-color: #667eea;
            }
        """)
        form_layout.addRow(status_label, self.status_combo)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        
        # 按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 20, 0, 10)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(130, 55)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: #f8f9fa;
                border-color: #adb5bd;
                color: #495057;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(108, 117, 125, 0.15);
            }
            QPushButton:pressed {
                background: #e9ecef;
                transform: translateY(0px);
                box-shadow: 0 2px 4px rgba(108, 117, 125, 0.1);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        # 添加设备按钮
        add_btn = QPushButton("🚀 添加设备")
        add_btn.setFixedSize(150, 55)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:0.5 #6a4190, stop:1 #e084e9);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5865c6, stop:0.5 #5e3d7e, stop:1 #d275d7);
                transform: translateY(0px);
                box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
            }
        """)
        add_btn.clicked.connect(self.accept_device)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addSpacing(20)
        button_layout.addWidget(add_btn)
        
        layout.addWidget(button_frame)
        
    def accept_device(self):
        """确认添加设备"""
        # 验证必填字段
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "设备名称不能为空！")
            return
            
        # 收集设备数据
        self.device_data = {
            "name": self.name_edit.text().strip(),
            "type": self.type_edit.text().strip() if self.type_edit.text().strip() else None,
            "ip": self.ip_edit.text().strip() if self.ip_edit.text().strip() else None,
            "location": self.location_edit.text().strip() if self.location_edit.text().strip() else None,
            "status": self.status_combo.currentText()
        }
        
        self.accept()
        
    def get_device_data(self):
        """获取设备数据"""
        return self.device_data


class DeviceAddWorker(QThread):
    """设备添加工作线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(str)  # 进度更新信号
    device_added = pyqtSignal(str)      # 设备添加完成信号
    error_occurred = pyqtSignal(str)    # 错误信号
    
    def __init__(self, device_data=None, api_base_url=None):
        super().__init__()
        self.device_data = device_data or {}
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """执行设备添加流程"""
        try:
            # 步骤1：获取访问令牌
            self.progress_updated.emit("正在获取访问令牌...")
            if not self.authenticate():
                self.error_occurred.emit("认证失败，请检查管理员账号配置")
                return
            
            # 步骤2：添加设备
            self.progress_updated.emit("正在添加设备...")
            if self.add_device():
                self.device_added.emit(f"设备 '{self.device_data.get('name', '未知')}' 添加成功！")
            else:
                self.error_occurred.emit("设备添加失败，请检查服务器连接")
                
        except Exception as e:
            self.error_occurred.emit(f"设备添加失败: {str(e)}")
            
    def authenticate(self):
        """管理员认证（使用admin账号）"""
        try:
            # 使用admin账号进行认证
            auth_data = {
                "login_type": "管理员",  # 使用管理员登录类型
                "username": "admin",     # 强制使用admin用户名
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
                print(f"管理员认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"管理员认证异常: {str(e)}")
            return False
            
    def add_device(self):
        """添加设备"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['create_device']}",
                json=self.device_data,
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"添加设备失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"添加设备异常: {str(e)}")
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
        self.task_list_worker = None  # 任务列表获取工作线程
        self.device_worker = None  # 设备添加工作线程
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
            ("📤", "任务列表", self.submit_tasks, "#9b59b6"),
            ("🖥️", "添加设备", self.add_device, "#34495e"),
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
        
    def add_device(self):
        """添加设备"""
        # 检查是否有设备添加操作正在进行
        if self.device_worker and self.device_worker.isRunning():
            QMessageBox.information(self, "提示", "设备添加正在进行中，请稍等...")
            return
            
        # 显示设备添加对话框
        dialog = DeviceAddDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            device_data = dialog.get_device_data()
            if device_data:
                self.start_device_addition(device_data)
                
    def start_device_addition(self, device_data):
        """开始设备添加流程"""
        # 创建设备添加工作线程
        self.device_worker = DeviceAddWorker(device_data)
        
        # 连接信号
        self.device_worker.progress_updated.connect(self.on_device_progress_updated)
        self.device_worker.device_added.connect(self.on_device_added)
        self.device_worker.error_occurred.connect(self.on_device_error)
        
        # 开始设备添加
        self.status_label.setText("正在准备添加设备...")
        self.device_worker.start()
        
    @pyqtSlot(str)
    def on_device_progress_updated(self, message):
        """设备添加进度更新回调"""
        self.status_label.setText(message)
        print(f"设备添加进度: {message}")
        
    @pyqtSlot(str) 
    def on_device_added(self, message):
        """设备添加完成回调"""
        self.status_label.setText("设备添加成功")
        print(f"设备添加完成: {message}")
        
        # 显示完成对话框
        QMessageBox.information(self, "设备添加成功", message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    @pyqtSlot(str)
    def on_device_error(self, error_message):
        """设备添加错误回调"""
        self.status_label.setText("设备添加失败")
        print(f"设备添加错误: {error_message}")
        
        # 显示错误对话框
        QMessageBox.warning(self, "设备添加失败", error_message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    def submit_tasks(self):
        """打开任务选择对话框"""
        # 如果已有任务在执行，不允许重复操作
        if self.task_worker and self.task_worker.isRunning():
            QMessageBox.information(self, "提示", "任务提交正在进行中，请稍等...")
            return
            
        if self.task_list_worker and self.task_list_worker.isRunning():
            QMessageBox.information(self, "提示", "正在获取任务列表，请稍等...")
            return
            
        # 显示加载状态
        self.status_label.setText("正在获取任务列表...")
        
        # 创建任务列表获取工作线程
        self.task_list_worker = TaskListWorker()
        
        # 连接信号
        self.task_list_worker.tasks_loaded.connect(self.on_tasks_loaded)
        self.task_list_worker.error_occurred.connect(self.on_task_list_error)
        
        # 开始获取任务列表
        self.task_list_worker.start()
        
    @pyqtSlot(list)
    def on_tasks_loaded(self, tasks):
        """任务列表加载完成"""
        self.status_label.setText("系统运行正常")
        
        if not tasks:
            QMessageBox.information(self, "提示", "当前没有任务")
            return
            
        # 过滤出待提交的任务
        pending_tasks = [task for task in tasks if task.get('status') == api_config.TASK_STATUS["PENDING"]]
        
        if not pending_tasks:
            QMessageBox.information(self, "提示", "没有可提交的任务")
            return
            
        # 显示任务选择对话框
        dialog = TaskSelectionDialog(tasks, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_tasks = dialog.get_selected_tasks()
            if selected_tasks:
                self.start_task_submission(selected_tasks)
                
    @pyqtSlot(str)
    def on_task_list_error(self, error_message):
        """获取任务列表失败"""
        self.status_label.setText("获取任务列表失败")
        QMessageBox.warning(self, "错误", f"获取任务列表失败：{error_message}")
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    def start_task_submission(self, selected_tasks):
        """开始提交选中的任务"""
        # 创建任务提交工作线程
        self.task_worker = TaskSubmissionWorker(selected_tasks)
        
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
            
        # 清理任务列表工作线程
        if self.task_list_worker and self.task_list_worker.isRunning():
            self.task_list_worker.terminate()
            self.task_list_worker.wait()
            
        # 清理设备工作线程
        if self.device_worker and self.device_worker.isRunning():
            self.device_worker.terminate()
            self.device_worker.wait()
            
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