#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF查看器弹窗组件
使用PyMuPDF渲染PDF为图像显示
"""

import sys
import os
import fitz  # PyMuPDF
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QScrollArea, QSpinBox, QSlider, QLineEdit,
                           QMessageBox, QProgressBar, QFrame, QToolBar, QAction,
                           QSizePolicy, QWidget, QApplication, QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QPixmap, QImage, QPainter, QFont, QIcon, QKeySequence


class PDFRenderThread(QThread):
    """PDF渲染线程，避免界面阻塞"""
    page_rendered = pyqtSignal(int, QPixmap)  # 页码, 渲染的图像
    render_progress = pyqtSignal(int)  # 渲染进度
    render_error = pyqtSignal(str)  # 渲染错误
    
    def __init__(self, pdf_document, page_num, zoom_factor=1.0):
        super().__init__()
        self.pdf_document = pdf_document
        self.page_num = page_num
        self.zoom_factor = zoom_factor
        self._stop_flag = False
    
    def run(self):
        """渲染PDF页面"""
        try:
            if self._stop_flag:
                return
                
            # 获取PDF页面
            page = self.pdf_document[self.page_num]
            
            # 设置渲染参数
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            
            self.render_progress.emit(25)
            
            if self._stop_flag:
                return
                
            # 渲染为图像
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            self.render_progress.emit(50)
            
            if self._stop_flag:
                return
            
            # 转换为QImage
            img_data = pix.tobytes("ppm")
            qimg = QImage.fromData(img_data)
            
            self.render_progress.emit(75)
            
            if self._stop_flag:
                return
            
            # 转换为QPixmap
            pixmap = QPixmap.fromImage(qimg)
            
            self.render_progress.emit(100)
            
            if not self._stop_flag:
                self.page_rendered.emit(self.page_num, pixmap)
                
        except Exception as e:
            if not self._stop_flag:
                self.render_error.emit(f"渲染第{self.page_num + 1}页时出错: {str(e)}")
    
    def stop(self):
        """停止渲染"""
        self._stop_flag = True


class PDFViewerWidget(QDialog):
    """PDF查看器弹窗"""
    
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        self.render_thread = None
        
        # 设置窗口属性
        self.setWindowTitle("PDF预览 - 加载中...")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        self.resize(800, 900)
        
        # 尝试加载PDF
        if not self.load_pdf():
            return
            
        self.setup_ui()
        self.setup_shortcuts()
        self.render_current_page()
        
        # 设置窗口标题
        filename = os.path.basename(self.pdf_path)
        self.setWindowTitle(f"PDF预览 - {filename} ({self.total_pages}页)")
    
    def load_pdf(self):
        """加载PDF文档"""
        try:
            print(f"📄 正在加载PDF文件: {self.pdf_path}")
            
            if not os.path.exists(self.pdf_path):
                QMessageBox.critical(self, "错误", f"文件不存在:\n{self.pdf_path}")
                return False
            
            # 打开PDF文档
            self.pdf_document = fitz.open(self.pdf_path)
            self.total_pages = len(self.pdf_document)
            
            if self.total_pages == 0:
                QMessageBox.critical(self, "错误", "PDF文件为空或损坏")
                return False
            
            print(f"✅ PDF加载成功，共 {self.total_pages} 页")
            return True
            
        except Exception as e:
            error_msg = f"加载PDF文件失败:\n{str(e)}"
            print(f"❌ {error_msg}")
            QMessageBox.critical(self, "错误", error_msg)
            return False
    
    def setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 工具栏
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.StyledPanel)
        toolbar_frame.setMaximumHeight(50)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # 页面导航控件
        self.prev_btn = QPushButton("◀ 上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setRange(1, self.total_pages)
        self.page_spinbox.setValue(1)
        self.page_spinbox.valueChanged.connect(self.goto_page)
        self.page_spinbox.setMaximumWidth(80)
        
        self.page_label = QLabel(f"/ {self.total_pages}")
        self.page_label.setMinimumWidth(50)
        
        self.next_btn = QPushButton("下一页 ▶")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(self.total_pages > 1)
        
        # 缩放控件
        zoom_label = QLabel("缩放:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(25, 400)  # 25% - 400%
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        self.zoom_slider.setMaximumWidth(150)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(40)
        
        self.fit_width_btn = QPushButton("适应宽度")
        self.fit_width_btn.clicked.connect(self.fit_width)
        
        self.fit_page_btn = QPushButton("适应页面")
        self.fit_page_btn.clicked.connect(self.fit_page)
        
        # 搜索控件
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索文本...")
        self.search_edit.returnPressed.connect(self.search_text)
        self.search_edit.setMaximumWidth(200)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.search_text)
        
        # 关闭按钮
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        # 添加控件到工具栏
        toolbar_layout.addWidget(self.prev_btn)
        toolbar_layout.addWidget(self.page_spinbox)
        toolbar_layout.addWidget(self.page_label)
        toolbar_layout.addWidget(self.next_btn)
        toolbar_layout.addWidget(QFrame())  # 分隔符
        toolbar_layout.addWidget(zoom_label)
        toolbar_layout.addWidget(self.zoom_slider)
        toolbar_layout.addWidget(self.zoom_label)
        toolbar_layout.addWidget(self.fit_width_btn)
        toolbar_layout.addWidget(self.fit_page_btn)
        toolbar_layout.addWidget(QFrame())  # 分隔符
        toolbar_layout.addWidget(self.search_edit)
        toolbar_layout.addWidget(self.search_btn)
        toolbar_layout.addStretch()  # 弹性空间
        toolbar_layout.addWidget(self.close_btn)
        
        # PDF显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignCenter)
        self.pdf_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.pdf_label.setText("正在加载PDF...")
        
        self.scroll_area.setWidget(self.pdf_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        
        # 状态栏
        self.status_bar = QLabel()
        self.status_bar.setFrameStyle(QFrame.StyledPanel)
        self.status_bar.setMaximumHeight(25)
        self.update_status()
        
        # 添加到主布局
        main_layout.addWidget(toolbar_frame)
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_bar)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # 页面导航
        self.prev_shortcut = QKeySequence(Qt.Key_Left)
        self.next_shortcut = QKeySequence(Qt.Key_Right)
        self.first_page_shortcut = QKeySequence(Qt.Key_Home)
        self.last_page_shortcut = QKeySequence(Qt.Key_End)
        
        # 缩放
        self.zoom_in_shortcut = QKeySequence(Qt.CTRL + Qt.Key_Plus)
        self.zoom_out_shortcut = QKeySequence(Qt.CTRL + Qt.Key_Minus)
        self.zoom_fit_shortcut = QKeySequence(Qt.CTRL + Qt.Key_0)
        
        # 搜索
        self.search_shortcut = QKeySequence(Qt.CTRL + Qt.Key_F)
    
    def keyPressEvent(self, event):
        """处理键盘快捷键"""
        if event.key() == Qt.Key_Left and self.current_page > 0:
            self.prev_page()
        elif event.key() == Qt.Key_Right and self.current_page < self.total_pages - 1:
            self.next_page()
        elif event.key() == Qt.Key_Home:
            self.goto_page_num(0)
        elif event.key() == Qt.Key_End:
            self.goto_page_num(self.total_pages - 1)
        elif event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Plus:
                self.zoom_in()
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
            elif event.key() == Qt.Key_0:
                self.fit_page()
            elif event.key() == Qt.Key_F:
                self.search_edit.setFocus()
        else:
            super().keyPressEvent(event)
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.page_spinbox.setValue(self.current_page + 1)
            self.render_current_page()
            self.update_navigation_buttons()
            self.update_status()
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.page_spinbox.setValue(self.current_page + 1)
            self.render_current_page()
            self.update_navigation_buttons()
            self.update_status()
    
    def goto_page(self, page_num):
        """跳转到指定页面（从SpinBox）"""
        self.goto_page_num(page_num - 1)  # SpinBox是1开始的
    
    def goto_page_num(self, page_index):
        """跳转到指定页面索引（从0开始）"""
        if 0 <= page_index < self.total_pages:
            self.current_page = page_index
            self.page_spinbox.setValue(self.current_page + 1)
            self.render_current_page()
            self.update_navigation_buttons()
            self.update_status()
    
    def zoom_changed(self, value):
        """缩放改变"""
        self.zoom_factor = value / 100.0
        self.zoom_label.setText(f"{value}%")
        self.render_current_page()
    
    def zoom_in(self):
        """放大"""
        current_value = self.zoom_slider.value()
        new_value = min(400, current_value + 25)
        self.zoom_slider.setValue(new_value)
    
    def zoom_out(self):
        """缩小"""
        current_value = self.zoom_slider.value()
        new_value = max(25, current_value - 25)
        self.zoom_slider.setValue(new_value)
    
    def fit_width(self):
        """适应宽度"""
        try:
            # 获取当前页面
            page = self.pdf_document[self.current_page]
            page_rect = page.rect
            
            # 计算适应宽度的缩放因子
            scroll_width = self.scroll_area.width() - 20  # 减去边距
            zoom = scroll_width / page_rect.width
            
            # 限制缩放范围
            zoom = max(0.25, min(4.0, zoom))
            
            self.zoom_slider.setValue(int(zoom * 100))
            
        except Exception as e:
            print(f"❌ 适应宽度失败: {str(e)}")
    
    def fit_page(self):
        """适应页面"""
        try:
            # 获取当前页面
            page = self.pdf_document[self.current_page]
            page_rect = page.rect
            
            # 计算适应页面的缩放因子
            scroll_width = self.scroll_area.width() - 20
            scroll_height = self.scroll_area.height() - 20
            
            zoom_w = scroll_width / page_rect.width
            zoom_h = scroll_height / page_rect.height
            zoom = min(zoom_w, zoom_h)
            
            # 限制缩放范围
            zoom = max(0.25, min(4.0, zoom))
            
            self.zoom_slider.setValue(int(zoom * 100))
            
        except Exception as e:
            print(f"❌ 适应页面失败: {str(e)}")
    
    def search_text(self):
        """搜索文本"""
        search_text = self.search_edit.text().strip()
        if not search_text:
            return
        
        try:
            # 在当前页面搜索
            page = self.pdf_document[self.current_page]
            text_instances = page.search_for(search_text)
            
            if text_instances:
                QMessageBox.information(self, "搜索结果", 
                                      f"在第{self.current_page + 1}页找到 {len(text_instances)} 个匹配项")
            else:
                # 在所有页面中搜索
                found_pages = []
                for i in range(self.total_pages):
                    page = self.pdf_document[i]
                    if page.search_for(search_text):
                        found_pages.append(i + 1)
                
                if found_pages:
                    pages_str = ", ".join(map(str, found_pages))
                    result = QMessageBox.question(self, "搜索结果", 
                                                f"在以下页面找到匹配项: {pages_str}\n\n是否跳转到第一个匹配页面?",
                                                QMessageBox.Yes | QMessageBox.No)
                    if result == QMessageBox.Yes:
                        self.goto_page_num(found_pages[0] - 1)
                else:
                    QMessageBox.information(self, "搜索结果", "未找到匹配的文本")
                    
        except Exception as e:
            QMessageBox.critical(self, "搜索错误", f"搜索时出错: {str(e)}")
    
    def render_current_page(self):
        """渲染当前页面"""
        if not self.pdf_document:
            return
        
        # 停止之前的渲染线程
        if self.render_thread and self.render_thread.isRunning():
            self.render_thread.stop()
            self.render_thread.wait(1000)  # 等待最多1秒
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.pdf_label.setText("正在渲染页面...")
        
        # 启动渲染线程
        self.render_thread = PDFRenderThread(self.pdf_document, self.current_page, self.zoom_factor)
        self.render_thread.page_rendered.connect(self.on_page_rendered)
        self.render_thread.render_progress.connect(self.progress_bar.setValue)
        self.render_thread.render_error.connect(self.on_render_error)
        self.render_thread.start()
    
    def on_page_rendered(self, page_num, pixmap):
        """页面渲染完成"""
        if page_num == self.current_page:  # 确保是当前页面
            self.pdf_label.setPixmap(pixmap)
            self.pdf_label.resize(pixmap.size())
        
        self.progress_bar.setVisible(False)
        self.update_status()
    
    def on_render_error(self, error_msg):
        """渲染错误"""
        self.progress_bar.setVisible(False)
        self.pdf_label.setText(f"渲染错误:\n{error_msg}")
        QMessageBox.critical(self, "渲染错误", error_msg)
    
    def update_navigation_buttons(self):
        """更新导航按钮状态"""
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < self.total_pages - 1)
    
    def update_status(self):
        """更新状态栏"""
        if self.pdf_document:
            filename = os.path.basename(self.pdf_path)
            status_text = f"文件: {filename} | 第 {self.current_page + 1} 页，共 {self.total_pages} 页 | 缩放: {int(self.zoom_factor * 100)}%"
            
            # 添加文件信息
            try:
                file_size = os.path.getsize(self.pdf_path)
                if file_size > 1024 * 1024:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{file_size / 1024:.1f} KB"
                status_text += f" | 大小: {size_str}"
            except:
                pass
            
            self.status_bar.setText(status_text)
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止渲染线程
        if self.render_thread and self.render_thread.isRunning():
            self.render_thread.stop()
            self.render_thread.wait(1000)
        
        # 关闭PDF文档
        if self.pdf_document:
            self.pdf_document.close()
        
        event.accept()


def show_pdf_viewer(pdf_path, parent=None):
    """显示PDF查看器的便利函数"""
    try:
        viewer = PDFViewerWidget(pdf_path, parent)
        return viewer.exec_()
    except Exception as e:
        print(f"❌ 显示PDF查看器失败: {str(e)}")
        if parent:
            QMessageBox.critical(parent, "错误", f"无法打开PDF查看器:\n{str(e)}")
        return None


# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 测试PDF文件路径
    import tempfile
    test_pdf = os.path.join(tempfile.gettempdir(), "test.pdf")
    
    if os.path.exists(test_pdf):
        viewer = PDFViewerWidget(test_pdf)
        viewer.show()
        sys.exit(app.exec_())
    else:
        print("请提供测试PDF文件路径") 