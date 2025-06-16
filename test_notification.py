#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget

def test_notification():
    """测试弹窗功能"""
    app = QApplication(sys.argv)
    
    # 创建一个隐藏的主窗口作为父窗口
    main_window = QWidget()
    
    # 测试简单的信息弹窗
    QMessageBox.information(main_window, "测试通知", "这是一个测试弹窗！\n如果你看到这个消息，说明弹窗功能正常。")
    
    print("弹窗测试完成")
    
    # 不需要进入事件循环，弹窗显示后就退出
    sys.exit(0)

if __name__ == "__main__":
    test_notification() 