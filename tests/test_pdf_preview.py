#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF预览功能测试脚本
用于验证PyMuPDF集成和PDF路径修复是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from src.desktop.desktop_manager import PDFPreviewDialog

class TestPDFPreview(QWidget):
    """PDF预览测试界面"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置测试界面"""
        self.setWindowTitle("PDF预览功能测试")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("PDF预览功能测试\n(增强版本 - 支持滚动和滚轮缩放)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2d3436;
                padding: 20px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(title)
        
        # 测试按钮
        roles = [
            ("系统分析师", "系统分析师"),
            ("系统架构设计师", "系统架构设计师"),
            ("系统规划与管理师", "系统规划与管理师"),
            ("网络规划设计师", "网络规划设计师")
        ]
        
        for role_display, role_file in roles:
            btn = QPushButton(f"测试 {role_display} PDF预览")
            btn.clicked.connect(lambda checked, r=role_file: self.test_pdf_preview(r))
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 12px;
                    font-weight: bold;
                    margin: 5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #764ba2, stop:1 #667eea);
                }
            """)
            layout.addWidget(btn)
            
        # 路径测试按钮
        path_test_btn = QPushButton("测试PDF路径检查")
        path_test_btn.clicked.connect(self.test_pdf_paths)
        path_test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00b894, stop:1 #00a085);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00a085, stop:1 #008f72);
            }
        """)
        layout.addWidget(path_test_btn)
        
    def test_pdf_preview(self, role_name):
        """测试PDF预览功能"""
        print(f"\n🧪 开始测试 {role_name} 的PDF预览...")
        
        # 构建PDF路径
        pdf_filename = f"项目任务汇报单子({role_name}).pdf"
        new_path = os.path.join("resources", "documents", "Project_Management", pdf_filename)
        old_path = os.path.join("Project_Management", pdf_filename)
        
        # 检查文件是否存在
        if os.path.exists(new_path):
            pdf_path = new_path
            print(f"✅ 找到PDF文件（新路径）: {pdf_path}")
        elif os.path.exists(old_path):
            pdf_path = old_path
            print(f"✅ 找到PDF文件（旧路径）: {pdf_path}")
        else:
            print(f"❌ 未找到PDF文件")
            print(f"   新路径: {new_path}")
            print(f"   旧路径: {old_path}")
            return
            
        try:
            # 创建并显示PDF预览对话框
            dialog = PDFPreviewDialog(pdf_path, role_name, self)
            dialog.exec_()
            print(f"✅ {role_name} PDF预览测试完成")
            
        except Exception as e:
            print(f"❌ {role_name} PDF预览测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def test_pdf_paths(self):
        """测试所有PDF文件路径"""
        print("\n🔍 开始检查所有PDF文件路径...")
        
        roles = ["系统分析师", "系统架构设计师", "系统规划与管理师", "网络规划设计师"]
        
        for role in roles:
            pdf_filename = f"项目任务汇报单子({role}).pdf"
            new_path = os.path.join("resources", "documents", "Project_Management", pdf_filename)
            old_path = os.path.join("Project_Management", pdf_filename)
            
            print(f"\n📄 {role}:")
            print(f"   新路径: {new_path}")
            print(f"   新路径存在: {'✅' if os.path.exists(new_path) else '❌'}")
            print(f"   旧路径: {old_path}")
            print(f"   旧路径存在: {'✅' if os.path.exists(old_path) else '❌'}")
            
            if os.path.exists(new_path):
                size = os.path.getsize(new_path) // 1024
                print(f"   文件大小: {size} KB")
                
        # 检查PyMuPDF是否可用
        try:
            import fitz
            print(f"\n📚 PyMuPDF状态: ✅ 已安装 (版本 {fitz.version[0]})")
        except ImportError:
            print(f"\n📚 PyMuPDF状态: ❌ 未安装")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyleSheet("""
        QWidget {
            background: #f8f9fa;
            font-family: '微软雅黑';
        }
    """)
    
    test_window = TestPDFPreview()
    test_window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 