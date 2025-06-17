import os
import hashlib
import mimetypes
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QProgressBar, QFrame, QScrollArea, QFileDialog, QMessageBox,
                           QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QMimeData
from PyQt5.QtGui import QFont, QPixmap, QDragEnterEvent, QDropEvent, QPainter, QColor
import requests
import online_chat_config as config

class FileUploadThread(QThread):
    """文件上传线程"""
    progress_updated = pyqtSignal(int)  # 上传进度
    upload_completed = pyqtSignal(dict)  # 上传完成
    upload_failed = pyqtSignal(str)  # 上传失败
    
    def __init__(self, file_path, upload_url, headers=None):
        super().__init__()
        self.file_path = file_path
        self.upload_url = upload_url
        self.headers = headers or {}
        self.is_cancelled = False
        
    def run(self):
        """执行文件上传"""
        try:
            file_size = os.path.getsize(self.file_path)
            filename = os.path.basename(self.file_path)
            
            # 检查文件大小
            if file_size > config.UPLOAD_MAX_SIZE:
                self.upload_failed.emit(f"文件 {filename} 超过大小限制 {config.format_file_size(config.UPLOAD_MAX_SIZE)}")
                return
                
            # 检查文件类型
            if not config.is_file_allowed(filename):
                self.upload_failed.emit(f"不支持的文件类型: {filename}")
                return
            
            # 计算文件哈希
            file_hash = self.calculate_file_hash(self.file_path)
            
            # 准备上传数据
            with open(self.file_path, 'rb') as file:
                files = {'file': (filename, file, self.get_mime_type(filename))}
                data = {
                    'file_hash': file_hash,
                    'file_size': file_size,
                    'chunk_size': config.UPLOAD_CHUNK_SIZE
                }
                
                # 如果文件较大，使用分块上传
                if file_size > config.UPLOAD_CHUNK_SIZE:
                    self.upload_large_file(file, filename, file_hash, file_size)
                else:
                    self.upload_small_file(files, data)
                    
        except Exception as e:
            self.upload_failed.emit(f"上传失败: {str(e)}")
    
    def upload_small_file(self, files, data):
        """上传小文件"""
        try:
            response = requests.post(
                self.upload_url,
                files=files,
                data=data,
                headers=self.headers,
                timeout=config.CHAT_API_TIMEOUT * 3  # 上传超时时间更长
            )
            
            if response.status_code == 200:
                result = response.json()
                self.progress_updated.emit(100)
                self.upload_completed.emit(result)
            else:
                self.upload_failed.emit(f"上传失败: HTTP {response.status_code}")
                
        except Exception as e:
            self.upload_failed.emit(f"上传失败: {str(e)}")
    
    def upload_large_file(self, file, filename, file_hash, file_size):
        """分块上传大文件"""
        try:
            chunk_size = config.UPLOAD_CHUNK_SIZE
            chunks_total = (file_size + chunk_size - 1) // chunk_size
            
            for chunk_index in range(chunks_total):
                if self.is_cancelled:
                    return
                    
                # 读取数据块
                file.seek(chunk_index * chunk_size)
                chunk_data = file.read(chunk_size)
                
                # 上传数据块
                files = {'chunk': (f"{filename}.part{chunk_index}", chunk_data)}
                data = {
                    'file_hash': file_hash,
                    'chunk_index': chunk_index,
                    'chunks_total': chunks_total,
                    'filename': filename
                }
                
                response = requests.post(
                    f"{self.upload_url}/chunk",
                    files=files,
                    data=data,
                    headers=self.headers,
                    timeout=config.CHAT_API_TIMEOUT
                )
                
                if response.status_code != 200:
                    self.upload_failed.emit(f"上传块 {chunk_index + 1}/{chunks_total} 失败")
                    return
                
                # 更新进度
                progress = int((chunk_index + 1) * 100 / chunks_total)
                self.progress_updated.emit(progress)
            
            # 完成上传，请求合并文件
            response = requests.post(
                f"{self.upload_url}/merge",
                json={
                    'file_hash': file_hash,
                    'filename': filename,
                    'chunks_total': chunks_total
                },
                headers=self.headers,
                timeout=config.CHAT_API_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                self.upload_completed.emit(result)
            else:
                self.upload_failed.emit("文件合并失败")
                
        except Exception as e:
            self.upload_failed.emit(f"分块上传失败: {str(e)}")
    
    def calculate_file_hash(self, file_path):
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_mime_type(self, filename):
        """获取文件MIME类型"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def cancel(self):
        """取消上传"""
        self.is_cancelled = True

class FileUploadItem(QFrame):
    """文件上传项目"""
    remove_requested = pyqtSignal(object)  # 请求移除
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.upload_thread = None
        self.is_uploaded = False
        self.file_info = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin: 2px;
            }
            QFrame:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # 文件图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background-color: white;
                border-radius: 20px;
                border: 2px solid #dee2e6;
            }
        """)
        
        filename = os.path.basename(self.file_path)
        icon_text = config.get_file_type_icon(filename)
        self.icon_label.setText(icon_text)
        
        # 文件信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # 文件名
        self.name_label = QLabel(filename)
        self.name_label.setFont(QFont(config.FONTS['default'], 10, QFont.Bold))
        self.name_label.setStyleSheet("color: #495057;")
        
        # 文件大小和状态
        file_size = os.path.getsize(self.file_path)
        size_text = config.format_file_size(file_size)
        
        self.status_label = QLabel(f"{size_text} • 等待上传")
        self.status_label.setFont(QFont(config.FONTS['default'], 9))
        self.status_label.setStyleSheet("color: #6c757d;")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e9ecef;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        
        info_layout.addWidget(self.progress_bar)
        
        # 操作按钮
        self.action_btn = QPushButton("上传")
        self.action_btn.setFixedHeight(32)
        self.action_btn.setFixedWidth(60)
        self.action_btn.setFont(QFont(config.FONTS['default'], 9))
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 16px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.action_btn.clicked.connect(self.start_upload)
        
        # 删除按钮
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        
        layout.addWidget(self.icon_label)
        layout.addLayout(info_layout, 1)
        layout.addWidget(self.action_btn)
        layout.addWidget(self.remove_btn)
        
    def start_upload(self):
        """开始上传"""
        if self.is_uploaded:
            return
            
        self.action_btn.setText("上传中")
        self.action_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建上传线程
        upload_url = f"{config.CHAT_API_BASE_URL}/api/chat/upload"
        # 这里应该从父组件获取headers，包含JWT token
        self.upload_thread = FileUploadThread(self.file_path, upload_url)
        
        # 连接信号
        self.upload_thread.progress_updated.connect(self.on_progress_updated)
        self.upload_thread.upload_completed.connect(self.on_upload_completed)
        self.upload_thread.upload_failed.connect(self.on_upload_failed)
        
        # 开始上传
        self.upload_thread.start()
        
    def on_progress_updated(self, progress):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"{config.format_file_size(os.path.getsize(self.file_path))} • 上传中 {progress}%")
        
    def on_upload_completed(self, result):
        """上传完成"""
        self.is_uploaded = True
        self.file_info = result
        
        self.action_btn.setText("已上传")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 16px;
                padding: 5px 10px;
            }
        """)
        
        self.status_label.setText(f"{config.format_file_size(os.path.getsize(self.file_path))} • 上传成功")
        self.progress_bar.setValue(100)
        
    def on_upload_failed(self, error_message):
        """上传失败"""
        self.action_btn.setText("重试")
        self.action_btn.setEnabled(True)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 16px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        self.status_label.setText(f"上传失败: {error_message}")
        self.progress_bar.setVisible(False)
        
    def cancel_upload(self):
        """取消上传"""
        if self.upload_thread and self.upload_thread.isRunning():
            self.upload_thread.cancel()
            self.upload_thread.quit()
            self.upload_thread.wait()

class FileUploadWidget(QWidget):
    """文件上传组件"""
    file_uploaded = pyqtSignal(dict)  # 文件上传完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.upload_items = []
        self.headers = {}  # JWT认证头
        
        self.setup_ui()
        self.setAcceptDrops(True)  # 启用拖拽
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("文件上传")
        title.setFont(QFont(config.FONTS['default'], 12, QFont.Bold))
        title.setStyleSheet("color: #495057;")
        layout.addWidget(title)
        
        # 拖拽区域
        self.drop_area = QFrame()
        self.drop_area.setFixedHeight(120)
        self.drop_area.setStyleSheet("""
            QFrame {
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            QFrame:hover {
                border-color: #007bff;
                background-color: #e7f3ff;
            }
        """)
        
        drop_layout = QVBoxLayout(self.drop_area)
        drop_layout.setAlignment(Qt.AlignCenter)
        
        drop_icon = QLabel("📁")
        drop_icon.setAlignment(Qt.AlignCenter)
        drop_icon.setFont(QFont("Arial", 32))
        
        drop_text = QLabel("拖拽文件到此处或点击选择文件")
        drop_text.setAlignment(Qt.AlignCenter)
        drop_text.setFont(QFont(config.FONTS['default'], 10))
        drop_text.setStyleSheet("color: #6c757d;")
        
        drop_layout.addWidget(drop_icon)
        drop_layout.addWidget(drop_text)
        
        # 添加点击事件
        self.drop_area.mousePressEvent = self.select_files
        
        layout.addWidget(self.drop_area)
        
        # 文件列表滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f8f9fa;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #dee2e6;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #adb5bd;
            }
        """)
        
        self.file_list_widget = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_widget)
        self.file_list_layout.setAlignment(Qt.AlignTop)
        self.file_list_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.file_list_widget)
        layout.addWidget(self.scroll_area)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.upload_all_btn = QPushButton("全部上传")
        self.upload_all_btn.setFixedHeight(40)
        self.upload_all_btn.setFont(QFont(config.FONTS['default'], 10))
        self.upload_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.upload_all_btn.clicked.connect(self.upload_all_files)
        self.upload_all_btn.setEnabled(False)
        
        self.clear_all_btn = QPushButton("清空列表")
        self.clear_all_btn.setFixedHeight(40)
        self.clear_all_btn.setFont(QFont(config.FONTS['default'], 10))
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        self.clear_all_btn.clicked.connect(self.clear_all_files)
        
        button_layout.addWidget(self.upload_all_btn)
        button_layout.addWidget(self.clear_all_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def set_headers(self, headers):
        """设置请求头（包含JWT token）"""
        self.headers = headers
        
    def select_files(self, event=None):
        """选择文件"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        
        # 设置文件过滤器
        filters = []
        filters.append("所有支持的文件 (*" + " *".join(config.UPLOAD_ALLOWED_EXTENSIONS) + ")")
        filters.append("图片文件 (*.png *.jpg *.jpeg *.gif *.webp *.bmp *.svg)")
        filters.append("文档文件 (*.pdf *.txt *.doc *.docx *.xls *.xlsx *.ppt *.pptx)")
        filters.append("代码文件 (*.py *.js *.html *.css *.json *.xml *.yaml *.yml)")
        filters.append("所有文件 (*.*)")
        
        file_dialog.setNameFilters(filters)
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            self.add_files(file_paths)
    
    def add_files(self, file_paths):
        """添加文件到上传列表"""
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            # 检查文件是否已存在
            if any(item.file_path == file_path for item in self.upload_items):
                continue
                
            # 检查文件类型和大小
            filename = os.path.basename(file_path)
            if not config.is_file_allowed(filename):
                QMessageBox.warning(self, "文件类型错误", f"不支持的文件类型: {filename}")
                continue
                
            file_size = os.path.getsize(file_path)
            if file_size > config.UPLOAD_MAX_SIZE:
                QMessageBox.warning(self, "文件太大", 
                                  f"文件 {filename} 大小为 {config.format_file_size(file_size)}，"
                                  f"超过限制 {config.format_file_size(config.UPLOAD_MAX_SIZE)}")
                continue
            
            # 创建上传项目
            upload_item = FileUploadItem(file_path)
            upload_item.remove_requested.connect(self.remove_file_item)
            
            self.upload_items.append(upload_item)
            self.file_list_layout.addWidget(upload_item)
            
        self.update_buttons()
    
    def remove_file_item(self, item):
        """移除文件项目"""
        if item in self.upload_items:
            item.cancel_upload()
            self.upload_items.remove(item)
            self.file_list_layout.removeWidget(item)
            item.deleteLater()
            
        self.update_buttons()
    
    def upload_all_files(self):
        """上传所有文件"""
        for item in self.upload_items:
            if not item.is_uploaded:
                # 设置认证头
                if hasattr(item, 'upload_thread') and item.upload_thread:
                    item.upload_thread.headers = self.headers
                item.start_upload()
                
        self.upload_all_btn.setEnabled(False)
    
    def clear_all_files(self):
        """清空所有文件"""
        for item in self.upload_items[:]:
            self.remove_file_item(item)
    
    def update_buttons(self):
        """更新按钮状态"""
        has_files = len(self.upload_items) > 0
        has_unuploaded = any(not item.is_uploaded for item in self.upload_items)
        
        self.upload_all_btn.setEnabled(has_files and has_unuploaded)
        
    # 拖拽事件处理
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                self.add_files(file_paths)
                
            event.acceptProposedAction()
        else:
            event.ignore()

# 测试代码
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    widget = FileUploadWidget()
    widget.setWindowTitle("文件上传测试")
    widget.resize(600, 500)
    widget.show()
    
    sys.exit(app.exec_()) 