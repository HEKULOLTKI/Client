# 全屏浏览器

这是一个使用PyQt5创建的全屏浏览器程序，专门用于全屏显示localhost:3000网页。

## 功能特点

- 全屏显示网页
- 自动加载localhost:3000
- 键盘快捷键支持
- 简洁易用的界面

## 安装要求

确保您的系统已安装Python 3.6或更高版本。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python fullscreen_browser.py
```

## 快捷键

- **ESC键**: 退出程序
- **F11键**: 切换全屏/窗口模式
- **F5键**: 刷新页面

## 注意事项

1. 运行程序前，请确保localhost:3000服务正在运行
2. 如果网页加载失败，程序会在控制台显示错误信息
3. 程序启动后会自动进入全屏模式

## 系统要求

- Windows 10或更高版本
- Python 3.6+
- PyQt5和PyQtWebEngine

## 故障排除

如果遇到问题，请检查：
1. Python环境是否正确安装
2. 所有依赖包是否已安装
3. localhost:3000服务是否正常运行 