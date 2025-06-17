
import time
import sys
import os

print("模拟desktop_manager已启动...")
print(f"进程PID: {os.getpid()}")

# 运行5秒后退出
for i in range(5):
    print(f"模拟desktop_manager运行中... {i+1}/5")
    time.sleep(1)

print("模拟desktop_manager即将退出...")
