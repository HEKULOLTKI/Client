#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows工具箱管理器
管理Windows系统工具的快捷方式
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QLineEdit, QFileDialog, QMessageBox,
                             QListWidget, QListWidgetItem, QMenu, QInputDialog,
                             QScrollArea, QWidget, QGridLayout, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QPixmap, QKeySequence
from PyQt5.QtWidgets import QShortcut


class WindowsTool:
    """Windows工具类"""
    
    def __init__(self, name, path, icon="", description="", category="系统工具"):
        self.name = name
        self.path = path
        self.icon = icon
        self.description = description
        self.category = category
        
    def to_dict(self):
        """转换为字典"""
        return {
            "name": self.name,
            "path": self.path,
            "icon": self.icon,
            "description": self.description,
            "category": self.category
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            icon=data.get("icon", ""),
            description=data.get("description", ""),
            category=data.get("category", "系统工具")
        )


class ToolboxManager:
    """工具箱管理器"""
    
    def __init__(self):
        self.toolbox_dir = Path("toolbox")
        self.config_file = self.toolbox_dir / "tools_config.json"
        self.tools = []
        self.load_tools()
        
    def ensure_toolbox_dir(self):
        """确保工具箱目录存在"""
        self.toolbox_dir.mkdir(exist_ok=True)
        
    def load_tools(self):
        """加载工具配置"""
        self.ensure_toolbox_dir()
        
        # 默认Windows工具
        default_tools = [
            WindowsTool("命令提示符", "cmd.exe", "💻", "Windows命令行工具", "系统工具"),
            WindowsTool("PowerShell", "powershell.exe", "⚡", "PowerShell命令行", "系统工具"),
            WindowsTool("控制面板", "control.exe", "⚙️", "Windows控制面板", "系统设置"),
            WindowsTool("任务管理器", "taskmgr.exe", "📊", "系统任务管理器", "系统工具"),
            WindowsTool("设备管理器", "devmgmt.msc", "🔧", "硬件设备管理", "系统工具"),
            WindowsTool("服务管理", "services.msc", "🔄", "Windows服务管理", "系统工具"),
            WindowsTool("注册表编辑器", "regedit.exe", "🔐", "系统注册表编辑", "高级工具"),
            WindowsTool("组策略编辑器", "gpedit.msc", "📋", "组策略管理", "高级工具"),
            WindowsTool("磁盘管理", "diskmgmt.msc", "💾", "磁盘分区管理", "系统工具"),
            WindowsTool("事件查看器", "eventvwr.msc", "📝", "系统日志查看", "系统工具"),
            WindowsTool("计算机管理", "compmgmt.msc", "🖥️", "计算机综合管理", "系统工具"),
            WindowsTool("系统信息", "msinfo32.exe", "ℹ️", "系统详细信息", "系统工具"),
            WindowsTool("DirectX诊断", "dxdiag.exe", "🎮", "DirectX诊断工具", "系统工具"),
            WindowsTool("系统配置", "msconfig.exe", "🔧", "系统启动配置", "系统工具"),
            WindowsTool("性能监视器", "perfmon.exe", "📈", "系统性能监控", "系统工具"),
            WindowsTool("资源监视器", "resmon.exe", "📊", "系统资源监控", "系统工具"),
            WindowsTool("计算器", "calc.exe", "🧮", "Windows计算器", "实用工具"),
            WindowsTool("记事本", "notepad.exe", "📝", "文本编辑器", "实用工具"),
            WindowsTool("画图", "mspaint.exe", "🎨", "图像编辑器", "实用工具"),
            WindowsTool("截图工具", "snippingtool.exe", "📸", "屏幕截图工具", "实用工具"),
        ]
        
        # 尝试加载保存的配置
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    self.tools = [WindowsTool.from_dict(tool_data) for tool_data in saved_data]
            except Exception as e:
                print(f"加载工具配置失败: {e}")
                self.tools = default_tools
        else:
            self.tools = default_tools
            self.save_tools()
    
    def save_tools(self):
        """保存工具配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump([tool.to_dict() for tool in self.tools], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存工具配置失败: {e}")
    
    def add_tool(self, tool):
        """添加工具"""
        self.tools.append(tool)
        self.save_tools()
    
    def remove_tool(self, tool_name):
        """移除工具"""
        self.tools = [tool for tool in self.tools if tool.name != tool_name]
        self.save_tools()
    
    def get_tools_by_category(self):
        """按分类获取工具"""
        categories = {}
        for tool in self.tools:
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)
        return categories


class ToolExecutor(QThread):
    """工具执行器"""
    
    # 添加信号用于错误反馈
    error_occurred = pyqtSignal(str)
    
    def __init__(self, tool_path):
        super().__init__()
        self.tool_path = tool_path
        
    def run(self):
        """执行工具"""
        try:
            # 针对cmd和powershell特殊处理
            if self.tool_path.lower() == 'cmd.exe':
                # 使用更安全的方式启动cmd
                process = subprocess.Popen(['cmd.exe'], 
                                         creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif self.tool_path.lower() == 'powershell.exe':
                # 使用更安全的方式启动powershell
                process = subprocess.Popen(['powershell.exe'], 
                                         creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # 对于其他工具，使用shell=True确保正确启动
                process = subprocess.Popen(self.tool_path, 
                                         shell=True)
            
            # 检查进程是否成功启动
            if process.poll() is not None:
                raise Exception("进程启动失败")
                
        except FileNotFoundError:
            error_msg = f"找不到可执行文件: {self.tool_path}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
        except PermissionError:
            error_msg = f"权限不足，无法执行: {self.tool_path}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"执行工具失败: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)


class WindowsToolboxDialog(QDialog):
    """Windows工具箱对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.toolbox_manager = ToolboxManager()
        self.executors = []  # 存储所有执行器线程
        
        # 确保在UI设置之前初始化
        try:
            self.setup_ui()
            self.setup_animations()
            self.setup_shortcuts()
        except Exception as e:
            print(f"工具箱初始化失败: {e}")
            import traceback
            traceback.print_exc()
            # 如果初始化失败，尝试重新初始化
            try:
                self.setup_ui()
                self.setup_animations()
                self.setup_shortcuts()
            except Exception as e2:
                print(f"工具箱重新初始化也失败: {e2}")
                raise
        
    def setup_ui(self):
        """设置界面"""
        try:
            self.setWindowTitle("Windows工具箱")
            self.setFixedSize(800, 600)  # 修改窗口尺寸为800x600
            self.setModal(True)
            
            # 隐藏标题栏控制按钮
            self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
            
            # 设置朴素背景样式
            self.setStyleSheet("""
                QDialog {
                    background-color: #f5f5f5;
                    border: 1px solid #d0d0d0;
                }
            """)
            
            # 主布局
            layout = QVBoxLayout(self)
            layout.setContentsMargins(15, 15, 15, 15)  # 缩小边距
            layout.setSpacing(10)  # 缩小间距
            
            # 创建标题区域
            self.create_header_section(layout)
            
            # 创建搜索区域
            self.create_search_section(layout)
            
            # 创建工具区域
            self.create_tools_section(layout)
            
            # 创建底部按钮
            self.create_bottom_buttons(layout)
            
        except Exception as e:
            print(f"设置UI失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        
    def create_header_section(self, layout):
        """创建标题区域（已移除标题内容）"""
        # 不添加任何内容，直接返回
        return
        
    def create_search_section(self, layout):
        """创建搜索区域"""
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)
        
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 10, 15, 10)
        
        # 搜索图标
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #666666;
                padding: 5px;
            }
        """)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索Windows工具...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 8px 12px;
                font-size: 14px;
                color: #333333;
                font-family: '微软雅黑';
            }
            QLineEdit:focus {
                border-color: #4a90e2;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
        """)
        self.search_input.textChanged.connect(self.filter_tools)
        
        # 添加工具按钮
        add_tool_btn = QPushButton("添加工具")
        add_tool_btn.setFixedSize(100, 35)
        add_tool_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: 1px solid #4a90e2;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background-color: #357abd;
                border-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2e6da4;
            }
        """)
        add_tool_btn.clicked.connect(self.add_custom_tool)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(add_tool_btn)
        
        layout.addWidget(search_frame)
        
    def create_tools_section(self, layout):
        """创建工具区域"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        # 创建工具容器
        tools_widget = QWidget()
        self.tools_layout = QVBoxLayout(tools_widget)
        self.tools_layout.setContentsMargins(15, 15, 15, 15)
        self.tools_layout.setSpacing(10)
        
        scroll_area.setWidget(tools_widget)
        layout.addWidget(scroll_area)
        
        # 加载工具
        self.load_tools_display()
        
    def load_tools_display(self):
        """加载工具显示"""
        # 清除现有工具
        for i in reversed(range(self.tools_layout.count())):
            self.tools_layout.itemAt(i).widget().setParent(None)
        
        # 按分类组织工具
        categories = self.toolbox_manager.get_tools_by_category()
        
        for category, tools in categories.items():
            # 创建分类标题
            category_label = QLabel(f"{category}")
            category_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #333333;
                    font-family: '微软雅黑';
                    padding: 8px;
                    background-color: #f8f9fa;
                    border: 1px solid #e0e0e0;
                    border-radius: 3px;
                }
            """)
            self.tools_layout.addWidget(category_label)
            
            # 创建工具网格
            tools_frame = QFrame()
            tools_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 3px;
                }
            """)
            
            tools_grid = QGridLayout(tools_frame)
            tools_grid.setContentsMargins(10, 10, 10, 10)
            tools_grid.setSpacing(8)
            
            # 添加工具按钮
            for i, tool in enumerate(tools):
                row = i // 3
                col = i % 3
                tool_button = self.create_tool_button(tool)
                tools_grid.addWidget(tool_button, row, col)
            
            self.tools_layout.addWidget(tools_frame)
            
    def create_tool_button(self, tool):
        """创建工具按钮"""
        button = QPushButton()
        button.setFixedSize(220, 60)  # 缩小按钮尺寸
        button.setCursor(Qt.PointingHandCursor)
        
        # 设置按钮内容
        content_layout = QVBoxLayout(button)
        content_layout.setContentsMargins(10, 6, 10, 6)  # 缩小内边距
        content_layout.setSpacing(3)
        
        # 工具图标和名称
        icon_name_layout = QHBoxLayout()
        
        icon_label = QLabel(tool.icon)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #333333;
                border: none;
                background: none;
            }
        """)
        
        name_label = QLabel(tool.name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #333333;
                font-family: '微软雅黑';
                border: none;
                background: none;
            }
        """)
        
        icon_name_layout.addWidget(icon_label)
        icon_name_layout.addWidget(name_label)
        icon_name_layout.addStretch()
        
        # 工具描述
        desc_label = QLabel(tool.description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666666;
                font-family: '微软雅黑';
                border: none;
                background: none;
            }
        """)
        desc_label.setWordWrap(True)
        
        content_layout.addLayout(icon_name_layout)
        content_layout.addWidget(desc_label)
        
        # 设置按钮样式
        button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #4a90e2;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
                border-color: #357abd;
            }
        """)
        
        # 连接点击事件
        button.clicked.connect(lambda: self.execute_tool(tool))
        
        # 设置右键菜单
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, t=tool: self.show_tool_menu(pos, t))
        
        # 设置工具提示
        button.setToolTip(f"{tool.name}\n{tool.description}\n路径: {tool.path}")
        
        return button
        
    def execute_tool(self, tool):
        """执行工具"""
        try:
            # 创建执行器线程
            executor = ToolExecutor(tool.path)
            # 添加到执行器列表
            self.executors.append(executor)
            # 连接错误信号
            executor.error_occurred.connect(lambda msg: self.handle_execution_error(tool.name, msg))
            # 连接线程完成信号，确保线程正确清理
            executor.finished.connect(lambda: self.cleanup_executor(executor))
            executor.start()
        except Exception as e:
            QMessageBox.warning(self, "执行失败", f"启动 {tool.name} 失败:\n{str(e)}")
    
    def cleanup_executor(self, executor):
        """清理执行器线程"""
        try:
            if executor in self.executors:
                self.executors.remove(executor)
            executor.deleteLater()
        except Exception as e:
            print(f"清理执行器时出错: {e}")
    
    def handle_execution_error(self, tool_name, error_msg):
        """处理执行错误"""
        QMessageBox.warning(self, "执行失败", f"启动 {tool_name} 失败:\n{error_msg}")
            
    def show_tool_menu(self, position, tool):
        """显示工具右键菜单"""
        menu = QMenu(self)
        
        # 编辑工具
        edit_action = menu.addAction("✏️ 编辑")
        edit_action.triggered.connect(lambda: self.edit_tool(tool))
        
        # 删除工具（仅自定义工具）
        if tool.path not in ["cmd.exe", "powershell.exe", "control.exe"]:  # 保护系统默认工具
            menu.addSeparator()
            delete_action = menu.addAction("🗑️ 删除")
            delete_action.triggered.connect(lambda: self.delete_tool(tool))
        
        menu.exec_(self.sender().mapToGlobal(position))
        
    def add_custom_tool(self):
        """添加自定义工具"""
        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择可执行文件", "", "可执行文件 (*.exe *.msc *.bat *.cmd);;所有文件 (*)"
        )
        
        if file_path:
            # 获取文件名作为默认名称
            file_name = os.path.basename(file_path)
            name, ext = os.path.splitext(file_name)
            
            # 输入工具信息
            tool_name, ok = QInputDialog.getText(self, "工具名称", "请输入工具名称:", text=name)
            if ok and tool_name:
                tool_desc, ok = QInputDialog.getText(self, "工具描述", "请输入工具描述:")
                if ok:
                    tool_category, ok = QInputDialog.getItem(
                        self, "工具分类", "请选择工具分类:",
                        ["系统工具", "实用工具", "开发工具", "网络工具", "安全工具", "自定义工具"],
                        0, False
                    )
                    if ok:
                        # 创建新工具
                        new_tool = WindowsTool(
                            name=tool_name,
                            path=file_path,
                            icon="🔧",
                            description=tool_desc,
                            category=tool_category
                        )
                        
                        # 添加到管理器
                        self.toolbox_manager.add_tool(new_tool)
                        
                        # 重新加载显示
                        self.load_tools_display()
                        
                        QMessageBox.information(self, "添加成功", f"已添加工具: {tool_name}")
                        
    def edit_tool(self, tool):
        """编辑工具"""
        # 输入新的工具信息
        new_name, ok = QInputDialog.getText(self, "编辑工具", "工具名称:", text=tool.name)
        if ok and new_name:
            new_desc, ok = QInputDialog.getText(self, "编辑工具", "工具描述:", text=tool.description)
            if ok:
                new_category, ok = QInputDialog.getItem(
                    self, "编辑工具", "工具分类:",
                    ["系统工具", "实用工具", "开发工具", "网络工具", "安全工具", "自定义工具"],
                    ["系统工具", "实用工具", "开发工具", "网络工具", "安全工具", "自定义工具"].index(tool.category),
                    False
                )
                if ok:
                    # 更新工具信息
                    tool.name = new_name
                    tool.description = new_desc
                    tool.category = new_category
                    
                    # 保存配置
                    self.toolbox_manager.save_tools()
                    
                    # 重新加载显示
                    self.load_tools_display()
                    
                    QMessageBox.information(self, "编辑成功", f"已更新工具: {new_name}")
                    
    def delete_tool(self, tool):
        """删除工具"""
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除工具 '{tool.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.toolbox_manager.remove_tool(tool.name)
            self.load_tools_display()
            QMessageBox.information(self, "删除成功", f"已删除工具: {tool.name}")
            
    def filter_tools(self, text):
        """过滤工具"""
        # 这里可以实现搜索过滤逻辑
        # 暂时保留简单实现
        pass
        
    def create_bottom_buttons(self, layout):
        """创建底部按钮"""
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)
        
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(15, 10, 15, 10)
        button_layout.setSpacing(10)
        
        # 统计信息
        stats_label = QLabel(f"共 {len(self.toolbox_manager.tools)} 个工具")
        stats_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
                font-family: '微软雅黑';
            }
        """)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedSize(80, 35)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: 1px solid #6c757d;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background-color: #5a6268;
                border-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        refresh_btn.clicked.connect(self.load_tools_display)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(80, 35)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: 1px solid #dc3545;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background-color: #c82333;
                border-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        close_btn.clicked.connect(self.close_toolbox_only)
        
        button_layout.addWidget(stats_label)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(button_frame)
        
    def setup_animations(self):
        """设置动画效果"""
        # 创建窗口出现动画
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 启动动画
        self.opacity_animation.start()
        
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+F 聚焦搜索框
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.focus_search)
        
        # Escape 关闭对话框
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.close_toolbox_only)
        
        # Ctrl+R 刷新
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.load_tools_display)
        
    def focus_search(self):
        """聚焦搜索框"""
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def showEvent(self, event):
        """显示事件处理"""
        try:
            super().showEvent(event)
            # 确保窗口在最前面
            self.raise_()
            self.activateWindow()
        except Exception as e:
            print(f"显示工具箱时出错: {e}")
    
    def close_toolbox_only(self):
        """只关闭工具箱，不影响其他窗口"""
        try:
            print("🔧 正在关闭工具箱...")
            
            # 停止动画
            if hasattr(self, 'opacity_animation'):
                self.opacity_animation.stop()
            
            # 清理所有执行器线程
            for executor in self.executors[:]:  # 使用副本进行迭代
                try:
                    if executor.isRunning():
                        executor.quit()
                        executor.wait(1000)  # 等待最多1秒
                    executor.deleteLater()
                except Exception as e:
                    print(f"清理执行器时出错: {e}")
            
            # 清空执行器列表
            self.executors.clear()
            
            # 只关闭工具箱窗口，不影响父窗口
            self.hide()
            self.deleteLater()
            
            print("✅ 工具箱已关闭")
            
        except Exception as e:
            print(f"❌ 关闭工具箱时出错: {e}")
            # 即使出错也要确保窗口关闭
            self.hide()
            self.deleteLater()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        try:
            # 停止动画
            if hasattr(self, 'opacity_animation'):
                self.opacity_animation.stop()
            
            # 清理所有执行器线程
            for executor in self.executors[:]:  # 使用副本进行迭代
                try:
                    if executor.isRunning():
                        executor.quit()
                        executor.wait(1000)  # 等待最多1秒
                    executor.deleteLater()
                except Exception as e:
                    print(f"清理执行器时出错: {e}")
            
            # 清空执行器列表
            self.executors.clear()
            
            event.accept()
        except Exception as e:
            print(f"关闭工具箱时出错: {e}")
            event.accept()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = WindowsToolboxDialog()
    dialog.show()
    sys.exit(app.exec_()) 