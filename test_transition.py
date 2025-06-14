import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from transition_page import TransitionPage

class TestWindow(QMainWindow):
    """测试窗口，用于演示过渡页面功能"""
    
    def __init__(self):
        super().__init__()
        self.transition_page = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置测试界面"""
        self.setWindowTitle("过渡页面测试程序")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("过渡页面演示程序")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        
        # 说明文字
        info_label = QLabel("点击下面的按钮测试不同的过渡效果：")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                padding: 5px;
            }
        """)
        
        # 创建按钮
        self.create_buttons(layout)
        
        # 添加组件到布局
        layout.addWidget(title_label)
        layout.addWidget(info_label)
        layout.addStretch()
        
    def create_buttons(self, layout):
        """创建测试按钮"""
        buttons_info = [
            ("关闭网页过渡", self.test_close_webpage, "#3498db"),
            ("退出程序过渡", self.test_exit_program, "#e74c3c"),
            ("保存数据过渡", self.test_save_data, "#2ecc71"),
            ("处理中过渡", self.test_processing, "#f39c12"),
            ("直接退出", self.close, "#95a5a6")
        ]
        
        for text, handler, color in buttons_info:
            button = QPushButton(text)
            button.clicked.connect(handler)
            button.setFixedHeight(40)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color, 0.8)};
                }}
            """)
            layout.addWidget(button)
            
    def darken_color(self, hex_color, factor=0.9):
        """使颜色变暗"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def test_close_webpage(self):
        """测试关闭网页过渡"""
        self.show_transition(3000, "正在关闭网页...")
        
    def test_exit_program(self):
        """测试退出程序过渡"""
        self.show_transition(2000, "正在退出程序...")
        
    def test_save_data(self):
        """测试保存数据过渡"""
        self.show_transition(4000, "正在保存数据...")
        
    def test_processing(self):
        """测试处理中过渡"""
        self.show_transition(5000, "正在处理中...")
        
    def show_transition(self, duration, message):
        """显示过渡页面"""
        if not self.transition_page:
            self.transition_page = TransitionPage()
            self.transition_page.transition_completed.connect(self.on_transition_completed)
            self.transition_page.force_close.connect(self.on_force_close)
        
        # 显示过渡页面并开始动画
        self.transition_page.start_transition(duration, message)
        
    def on_transition_completed(self):
        """过渡完成回调"""
        print("过渡动画完成！")
        
    def on_force_close(self):
        """强制关闭回调"""
        print("用户选择强制关闭！")
        self.close()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建并显示测试窗口
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 