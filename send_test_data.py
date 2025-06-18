#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的数字孪生平台测试脚本
"""

import requests
import json

# 测试数据
test_data = {
    "system_info": {
        "description": "数字孪生平台系统访问地址",
        "url": "http://localhost:3001"
    }
}

try:
    print("发送测试数据...")
    response = requests.post(
        "http://localhost:8800/upload",
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=5
    )
    print(f"响应状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
except Exception as e:
    print(f"发送失败: {str(e)}") 