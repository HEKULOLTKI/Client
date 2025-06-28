#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tuopo图悬浮窗口组件
显示网络拓扑图的悬浮窗口（极简图片展示版）
"""

import os
from PyQt5.QtWidgets import (QLabel, QWidget, QVBoxLayout)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDesktopWidget

class TuopoWidget(QWidget):
    """拓扑图悬浮窗口（纯图片展示）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化拖动变量
        self._drag_pos = None
        
        # 设置UI
        self.setup_ui()
        
        # 加载拓扑图
        self.load_tuopo_image()
        
        # 设置初始位置
        self.position_at_center()
        
    def setup_ui(self):
        """设置UI界面（仅图片）"""
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        
        # 添加图片标签到主布局
        main_layout.addWidget(self.image_label)
        self.setLayout(main_layout)
        
    def load_tuopo_image(self):
        """加载拓扑图"""
        # 拓扑图路径
        image_path = os.path.join("image", "tuopu", "topu.png")
        
        if os.path.exists(image_path):
            try:
                # 加载图片
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 设置图片
                    self.image_label.setPixmap(pixmap)
                    
                    # 调整窗口大小为图片大小
                    self.resize(pixmap.size())
                    
                    print(f"已加载拓扑图: {image_path}")
                else:
                    self.show_error_message("无法加载图片文件")
            except Exception as e:
                self.show_error_message(f"加载图片时出错: {str(e)}")
        else:
            self.show_error_message("未找到拓扑图文件\n路径: " + image_path)
            
    def show_error_message(self, message):
        """显示错误信息"""
        self.image_label.setText(message)
        self.image_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 200);
                color: #e74c3c;
                font-size: 14px;
                font-weight: bold;
                padding: 20px;
                border: 2px solid #e74c3c;
                border-radius: 10px;
            }
        """)
        # 设置固定大小以显示错误信息
        self.resize(300, 100)
            
    def position_at_center(self):
        """将窗口定位到屏幕中央"""
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        
        # 计算中央位置
        x = (screen_rect.width() - self.width()) // 2
        y = (screen_rect.height() - self.height()) // 2
        
        self.move(x, y)
        
    def mousePressEvent(self, event):
        """鼠标按下事件 - 支持拖拽"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            # 右键点击关闭窗口
            self.hide()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽移动"""
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
            
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
        
    def wheelEvent(self, event):
        """鼠标滚轮事件 - 缩放图片"""
        if hasattr(self, 'image_label') and self.image_label.pixmap():
            # 获取当前图片
            current_pixmap = self.image_label.pixmap()
            
            # 计算缩放因子
            if event.angleDelta().y() > 0:
                # 向上滚动，放大
                scale_factor = 1.1
            else:
                # 向下滚动，缩小
                scale_factor = 0.9
            
            # 计算新的尺寸
            new_size = current_pixmap.size() * scale_factor
            
            # 限制最大和最小尺寸
            if new_size.width() > 2000 or new_size.height() > 2000:
                return  # 太大了，不缩放
            if new_size.width() < 50 or new_size.height() < 50:
                return  # 太小了，不缩放
            
            # 缩放图片
            scaled_pixmap = current_pixmap.scaled(
                new_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # 更新显示
            self.image_label.setPixmap(scaled_pixmap)
            self.resize(scaled_pixmap.size())
            
            event.accept() 