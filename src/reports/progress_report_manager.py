# -*- coding: utf-8 -*-
"""
进度报告导出管理模块
用于生成、导出和管理进度报告
"""

import os
import json
import pandas as pd
from datetime import datetime
import shutil
import subprocess
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QListWidgetItem, QMessageBox,
                             QFileDialog, QTabWidget, QWidget, QTextEdit,
                             QProgressBar, QComboBox, QCheckBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

class ProgressReportManager:
    """进度报告管理器"""
    
    def __init__(self):
        self.export_folder = "进度报告导出"
        self.ensure_export_folder()
        
    def ensure_export_folder(self):
        """确保导出文件夹存在"""
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder)
            
    def get_current_user_info(self):
        """获取当前用户信息"""
        try:
            if os.path.exists('received_tasks.json'):
                with open('received_tasks.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_info = data.get('user_info', {})
                    return {
                        'username': user_info.get('user', {}).get('username', '未知用户'),
                        'role': user_info.get('selectedRole', {}).get('label', '未知角色'),
                        'user_id': user_info.get('user', {}).get('id', ''),
                        'timestamp': user_info.get('timestamp', '')
                    }
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            
        return {
            'username': '未知用户',
            'role': '未知角色',
            'user_id': '',
            'timestamp': ''
        }
    
    def get_task_data(self):
        """获取任务数据"""
        try:
            if os.path.exists('received_tasks.json'):
                with open('received_tasks.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('tasks', [])
        except Exception as e:
            print(f"获取任务数据失败: {str(e)}")
        return []
    
    def calculate_task_statistics(self, tasks):
        """计算任务统计信息"""
        if not tasks:
            return {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'completion_rate': 0,
                'average_progress': 0
            }
        
        total = len(tasks)
        completed = 0
        in_progress = 0
        pending = 0
        total_progress = 0
        
        for task in tasks:
            status = task.get('status', task.get('assignment_status', '')).lower()
            progress = task.get('progress', task.get('completion_percentage', 0))
            
            total_progress += progress
            
            if status in ['已完成', 'completed', '完成']:
                completed += 1
            elif status in ['进行中', 'in_progress', '执行中']:
                in_progress += 1
            else:
                pending += 1
        
        completion_rate = (completed / total * 100) if total > 0 else 0
        average_progress = (total_progress / total) if total > 0 else 0
        
        return {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'completion_rate': completion_rate,
            'average_progress': average_progress
        }
    
    def generate_text_report(self, user_info, tasks, stats):
        """生成文本格式报告"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_content = f"""📊 进度报告 - {user_info['role']}

=====================================
项目进度报告
=====================================

📋 基本信息
-----------
角色名称: {user_info['role']}
操作员: {user_info['username']}
用户ID: {user_info['user_id']}
生成时间: {current_time}
报告类型: 系统自动生成

📈 任务统计
-----------
总任务数: {stats['total']}
已完成: {stats['completed']}
进行中: {stats['in_progress']}
待开始: {stats['pending']}

完成率: {stats['completion_rate']:.1f}%
平均进度: {stats['average_progress']:.1f}%

📋 任务详情
-----------
序号 | 任务名称                    | 任务类型        | 状态       | 进度   | 分配时间
-----|---------------------------|----------------|-----------|--------|----------
"""
        
        for i, task in enumerate(tasks, 1):
            task_name = task.get('name', task.get('task_name', '未命名任务'))[:20]
            task_type = task.get('type', task.get('task_type', '未知类型'))[:10]
            status = task.get('status', task.get('assignment_status', '未知状态'))[:8]
            progress = task.get('progress', task.get('completion_percentage', 0))
            assigned_time = task.get('assigned_time', task.get('created_at', '未知时间'))[:10]
            
            report_content += f"{i:4d} | {task_name:25s} | {task_type:12s} | {status:8s} | {progress:5.1f}% | {assigned_time}\n"
        
        report_content += f"""

📊 进度分析
-----------
- 任务执行效率: {'优秀' if stats['completion_rate'] >= 80 else '良好' if stats['completion_rate'] >= 60 else '需改进'}
- 任务完成率: {stats['completion_rate']:.1f}%
- 平均任务进度: {stats['average_progress']:.1f}%
- 风险评估: {'低风险' if stats['completion_rate'] >= 70 else '中等风险' if stats['completion_rate'] >= 50 else '高风险'}

💡 改进建议
-----------
1. {'继续保持当前工作节奏' if stats['completion_rate'] >= 80 else '建议加快任务执行速度'}
2. {'任务质量控制良好' if stats['average_progress'] >= 75 else '建议加强任务质量控制'}
3. 定期进行进度检查和状态更新
4. 及时处理遇到的问题和障碍

📝 备注说明
-----------
- 此报告为系统自动生成，数据来源于任务管理系统
- 用户可在"进度报告导出"文件夹中添加自定义报告
- 建议定期导出备份重要数据
- 如有疑问请联系系统管理员

=====================================
报告生成时间: {current_time}
系统版本: 多智能体协作运维系统 v1.0
=====================================
"""
        
        return report_content
    
    def generate_excel_report(self, user_info, tasks, stats):
        """生成Excel格式报告"""
        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"进度报告_{user_info['role']}_{current_time}.xlsx"
            filepath = os.path.join(self.export_folder, filename)
            
            # 创建Excel写入器
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 基本信息表
                basic_info = pd.DataFrame([
                    ['角色名称', user_info['role']],
                    ['操作员', user_info['username']],
                    ['用户ID', user_info['user_id']],
                    ['生成时间', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    ['报告类型', '系统自动生成']
                ], columns=['项目', '内容'])
                basic_info.to_excel(writer, sheet_name='基本信息', index=False)
                
                # 统计信息表
                stats_info = pd.DataFrame([
                    ['总任务数', stats['total']],
                    ['已完成', stats['completed']],
                    ['进行中', stats['in_progress']],
                    ['待开始', stats['pending']],
                    ['完成率(%)', f"{stats['completion_rate']:.1f}"],
                    ['平均进度(%)', f"{stats['average_progress']:.1f}"]
                ], columns=['指标', '数值'])
                stats_info.to_excel(writer, sheet_name='统计信息', index=False)
                
                # 任务详情表
                if tasks:
                    task_details = []
                    for i, task in enumerate(tasks, 1):
                        task_details.append({
                            '序号': i,
                            '任务名称': task.get('name', task.get('task_name', '未命名任务')),
                            '任务类型': task.get('type', task.get('task_type', '未知类型')),
                            '状态': task.get('status', task.get('assignment_status', '未知状态')),
                            '进度(%)': task.get('progress', task.get('completion_percentage', 0)),
                            '分配时间': task.get('assigned_time', task.get('created_at', '未知时间')),
                            '任务描述': task.get('description', '无描述')
                        })
                    
                    task_df = pd.DataFrame(task_details)
                    task_df.to_excel(writer, sheet_name='任务详情', index=False)
                
                # 分析建议表
                analysis = pd.DataFrame([
                    ['任务执行效率', '优秀' if stats['completion_rate'] >= 80 else '良好' if stats['completion_rate'] >= 60 else '需改进'],
                    ['完成率评估', f"{stats['completion_rate']:.1f}%"],
                    ['风险评估', '低风险' if stats['completion_rate'] >= 70 else '中等风险' if stats['completion_rate'] >= 50 else '高风险'],
                    ['改进建议1', '继续保持当前工作节奏' if stats['completion_rate'] >= 80 else '建议加快任务执行速度'],
                    ['改进建议2', '任务质量控制良好' if stats['average_progress'] >= 75 else '建议加强任务质量控制'],
                    ['改进建议3', '定期进行进度检查和状态更新']
                ], columns=['分析项目', '评估结果'])
                analysis.to_excel(writer, sheet_name='分析建议', index=False)
            
            return filepath
            
        except Exception as e:
            print(f"生成Excel报告失败: {str(e)}")
            return None
    
    def export_report(self, format_type='both'):
        """导出报告"""
        try:
            user_info = self.get_current_user_info()
            tasks = self.get_task_data()
            stats = self.calculate_task_statistics(tasks)
            
            exported_files = []
            
            # 导出文本报告
            if format_type in ['both', 'text']:
                text_content = self.generate_text_report(user_info, tasks, stats)
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                text_filename = f"进度报告_{user_info['role']}_{current_time}.txt"
                text_filepath = os.path.join(self.export_folder, text_filename)
                
                with open(text_filepath, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                exported_files.append(text_filepath)
            
            # 导出Excel报告
            if format_type in ['both', 'excel']:
                excel_filepath = self.generate_excel_report(user_info, tasks, stats)
                if excel_filepath:
                    exported_files.append(excel_filepath)
            
            return exported_files
            
        except Exception as e:
            print(f"导出报告失败: {str(e)}")
            return []
    
    def get_export_files(self):
        """获取导出文件列表"""
        try:
            if not os.path.exists(self.export_folder):
                return []
            
            files = []
            for filename in os.listdir(self.export_folder):
                filepath = os.path.join(self.export_folder, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # 按修改时间排序
            files.sort(key=lambda x: x['modified'], reverse=True)
            return files
            
        except Exception as e:
            print(f"获取导出文件列表失败: {str(e)}")
            return []
    
    def open_export_folder(self):
        """打开导出文件夹"""
        try:
            if os.path.exists(self.export_folder):
                if os.name == 'nt':  # Windows
                    os.startfile(self.export_folder)
                else:  # macOS 和 Linux
                    subprocess.run(['open', self.export_folder])
            else:
                print("导出文件夹不存在")
        except Exception as e:
            print(f"打开导出文件夹失败: {str(e)}")


class ProgressReportDialog(QDialog):
    """进度报告管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_manager = ProgressReportManager()
        self.setup_ui()
        self.refresh_file_list()
        
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("📊 进度报告管理")
        self.setFixedSize(900, 700)
        self.setModal(True)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 15px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(15)
        
        # 标题区域
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid rgba(102, 126, 234, 0.2);
                padding: 15px;
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        
        title_icon = QLabel("📊")
        title_icon.setFont(QFont("Segoe UI Emoji", 24))
        title_icon.setStyleSheet("background: transparent; color: #667eea;")
        
        title_text = QLabel("进度报告管理")
        title_text.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title_text.setStyleSheet("color: #2d3436; background: transparent;")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        layout.addWidget(title_frame)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 10px;
                background: white;
            }
            QTabBar::tab {
                background: #e9ecef;
                color: #495057;
                padding: 12px 20px;
                margin-right: 3px;
                border-radius: 8px 8px 0 0;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QTabBar::tab:selected {
                background: #667eea;
                color: white;
            }
            QTabBar::tab:hover {
                background: #adb5bd;
                color: white;
            }
        """)
        
        # 导出报告标签页
        self.export_tab = QWidget()
        self.setup_export_tab()
        self.tab_widget.addTab(self.export_tab, "📤 导出报告")
        
        # 文件管理标签页
        self.files_tab = QWidget()
        self.setup_files_tab()
        self.tab_widget.addTab(self.files_tab, "📁 文件管理")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        self.create_bottom_buttons(layout)
        
    def setup_export_tab(self):
        """设置导出报告标签页"""
        layout = QVBoxLayout(self.export_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 导出选项
        options_frame = QFrame()
        options_frame.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #dee2e6;
            }
        """)
        options_layout = QVBoxLayout(options_frame)
        
        # 导出格式选择
        format_layout = QHBoxLayout()
        format_label = QLabel("📋 导出格式:")
        format_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        
        self.format_combo = QComboBox()
        self.format_combo.addItem("📊 Excel + 文本 (推荐)", "both")
        self.format_combo.addItem("📊 仅Excel格式", "excel")
        self.format_combo.addItem("📄 仅文本格式", "text")
        self.format_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background: white;
                font-family: '微软雅黑';
            }
        """)
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        
        options_layout.addLayout(format_layout)
        
        # 包含内容选项
        self.include_tasks = QCheckBox("包含详细任务列表")
        self.include_analysis = QCheckBox("包含进度分析")
        self.include_suggestions = QCheckBox("包含改进建议")
        
        for checkbox in [self.include_tasks, self.include_analysis, self.include_suggestions]:
            checkbox.setChecked(True)
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-family: '微软雅黑';
                    font-size: 10px;
                    color: #495057;
                }
            """)
            options_layout.addWidget(checkbox)
        
        layout.addWidget(options_frame)
        
        # 导出按钮
        export_button = QPushButton("🚀 生成并导出报告")
        export_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5a6fd8, stop:1 #6a5acd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a5fb8, stop:1 #5a4fad);
            }
        """)
        export_button.clicked.connect(self.export_report)
        
        layout.addWidget(export_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
                font-family: '微软雅黑';
            }
            QProgressBar::chunk {
                background: #667eea;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 状态信息
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-family: '微软雅黑';
                font-size: 10px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
    def setup_files_tab(self):
        """设置文件管理标签页"""
        layout = QVBoxLayout(self.files_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 文件列表
        list_frame = QFrame()
        list_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(10, 10, 10, 10)
        
        list_label = QLabel("📁 导出文件列表")
        list_label.setFont(QFont("微软雅黑", 12, QFont.Bold))
        list_label.setStyleSheet("color: #495057; padding: 5px;")
        list_layout.addWidget(list_label)
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background: #f8f9fa;
                font-family: '微软雅黑';
                font-size: 10px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:selected {
                background: #667eea;
                color: white;
            }
            QListWidget::item:hover {
                background: #f1f3f4;
            }
        """)
        self.file_list.itemDoubleClicked.connect(self.open_selected_file)
        list_layout.addWidget(self.file_list)
        
        layout.addWidget(list_frame)
        
        # 文件操作按钮
        file_buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 刷新列表")
        open_folder_button = QPushButton("📁 打开文件夹")
        open_file_button = QPushButton("📖 打开文件")
        
        for button in [refresh_button, open_folder_button, open_file_button]:
            button.setStyleSheet("""
                QPushButton {
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-size: 10px;
                    font-family: '微软雅黑';
                }
                QPushButton:hover {
                    background: #5a6268;
                }
                QPushButton:pressed {
                    background: #495057;
                }
            """)
        
        refresh_button.clicked.connect(self.refresh_file_list)
        open_folder_button.clicked.connect(self.open_export_folder)
        open_file_button.clicked.connect(self.open_selected_file)
        
        file_buttons_layout.addWidget(refresh_button)
        file_buttons_layout.addWidget(open_folder_button)
        file_buttons_layout.addWidget(open_file_button)
        file_buttons_layout.addStretch()
        
        layout.addLayout(file_buttons_layout)
        
    def create_bottom_buttons(self, layout):
        """创建底部按钮"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
    def export_report(self):
        """导出报告"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 无限进度条
            self.status_label.setText("正在生成报告...")
            
            # 获取导出格式
            format_type = self.format_combo.currentData()
            
            # 执行导出
            exported_files = self.report_manager.export_report(format_type)
            
            self.progress_bar.setVisible(False)
            
            if exported_files:
                self.status_label.setText(f"✅ 成功导出 {len(exported_files)} 个文件")
                
                # 显示成功消息
                file_list = "\n".join([os.path.basename(f) for f in exported_files])
                QMessageBox.information(self, "导出成功", 
                                      f"报告已成功导出！\n\n导出文件:\n{file_list}\n\n文件保存在: {self.report_manager.export_folder}")
                
                # 刷新文件列表
                self.refresh_file_list()
            else:
                self.status_label.setText("❌ 导出失败")
                QMessageBox.warning(self, "导出失败", "报告导出失败，请检查任务数据是否存在。")
                
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText("❌ 导出异常")
            QMessageBox.critical(self, "导出异常", f"导出过程中发生异常:\n{str(e)}")
            print(f"导出报告异常: {str(e)}")
            
    def refresh_file_list(self):
        """刷新文件列表"""
        try:
            self.file_list.clear()
            files = self.report_manager.get_export_files()
            
            for file_info in files:
                size_kb = file_info['size'] / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                
                item_text = f"📄 {file_info['name']}\n    📅 {file_info['modified']} | 📦 {size_str}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, file_info['path'])
                self.file_list.addItem(item)
                
        except Exception as e:
            print(f"刷新文件列表失败: {str(e)}")
            
    def open_selected_file(self):
        """打开选中的文件"""
        try:
            current_item = self.file_list.currentItem()
            if current_item:
                file_path = current_item.data(Qt.UserRole)
                if file_path and os.path.exists(file_path):
                    if os.name == 'nt':  # Windows
                        os.startfile(file_path)
                    else:  # macOS 和 Linux
                        subprocess.run(['open', file_path])
                else:
                    QMessageBox.warning(self, "文件不存在", "选中的文件不存在或已被删除。")
            else:
                QMessageBox.information(self, "未选择文件", "请先选择要打开的文件。")
                
        except Exception as e:
            QMessageBox.critical(self, "打开失败", f"打开文件失败:\n{str(e)}")
            print(f"打开文件失败: {str(e)}")
    
    def open_export_folder(self):
        """打开导出文件夹"""
        self.report_manager.open_export_folder() 