#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试在线聊天框功能
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from online_chat_widget import OnlineChatWidget

def main():
    """主函数 - 测试在线聊天框"""
    app = QApplication(sys.argv)
    
    # 创建在线聊天窗口
    chat_window = OnlineChatWidget()
    
    # 设置测试用户信息
    chat_window.set_user_info("测试用户", "your_jwt_token_here")
    
    # 添加一些测试消息
    chat_window.add_message("欢迎来到在线聊天室！", is_user=False, sender_name="系统", timestamp="10:00")
    chat_window.add_message("大家好！", is_user=False, sender_name="用户A", timestamp="10:01")
    chat_window.add_message("你好，很高兴见到大家！", is_user=True, sender_name="测试用户", timestamp="10:02")
    
    # 添加一些测试在线用户
    test_users = [
        {"username": "用户A", "user_id": 1},
        {"username": "用户B", "user_id": 2},
        {"username": "管理员", "user_id": 3},
        {"username": "测试用户", "user_id": 4}
    ]
    
    for user in test_users:
        chat_window.add_online_user(user)
    
    # 更新在线用户数量
    chat_window.online_count_label.setText(f"在线: {len(test_users)}")
    chat_window.status_label.setText("已连接")
    
    # 显示窗口
    chat_window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 