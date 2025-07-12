# 智能桌面助手文档

欢迎使用智能桌面助手！这是一个集成了多种功能的统一桌面应用程序。

## 🏗️ 项目结构

```
智能桌面助手/
├── main.py                    # 主程序入口（统一应用程序）
├── requirements.txt           # Python依赖包列表
├── 启动智能桌面助手.bat      # Windows快速启动脚本
├── 启动菜单.bat              # 交互式启动菜单
├── test_main.py              # 程序测试脚本
│
├── src/                      # 源代码目录
│   ├── api/                  # API相关模块
│   │   ├── openai_api.py     # OpenAI聊天接口
│   │   └── token_manager.py  # Token管理
│   │
│   ├── browser/              # 浏览器模块
│   │   └── fullscreen_browser.py  # 全屏浏览器
│   │
│   ├── core/                 # 核心配置
│   │   ├── config.py         # 主配置文件
│   │   └── api_config.py     # API配置
│   │
│   ├── desktop/              # 桌面管理器
│   │   ├── desktop_manager.py      # 桌面管理器主程序
│   │   └── desktop_icon_manager.py # 桌面图标管理
│   │
│   ├── reports/              # 报告管理
│   │   └── progress_report_manager.py  # 进度报告管理
│   │
│   └── ui/                   # UI组件
│       ├── dialogs/          # 对话框
│       ├── screens/          # 屏幕/页面
│       │   ├── transition_screen.py          # 过渡屏幕
│       │   ├── enhanced_transition_screen.py # 增强过渡屏幕
│       │   └── independent_transition.py     # 独立过渡屏幕
│       └── widgets/          # UI部件
│           ├── chat_widget.py         # AI聊天窗口
│           ├── online_chat_widget.py  # 在线聊天窗口
│           ├── pet_widget.py          # 桌面宠物
│           ├── pdf_viewer_widget.py   # PDF查看器
│           ├── tuopo_widget.py        # 拓扑图部件
│           └── file_upload_widget.py  # 文件上传部件
│
├── resources/                # 资源文件
│   ├── assets/              # 静态资源
│   │   ├── config/          # 配置文件
│   │   └── images/          # 图片资源
│   │       ├── icons/       # 图标
│   │       ├── pets/        # 宠物动画
│   │       └── roles/       # 角色图片
│   └── documents/           # 文档资源
│
├── data/                    # 数据目录
│   ├── cache/              # 缓存文件
│   ├── exports/            # 导出文件
│   └── logs/               # 日志文件
│
├── desktop_backup/         # 桌面备份
└── docs/                   # 项目文档
    ├── README.md          # 本文档
    ├── 使用说明.md        # 详细使用说明
    └── 工具箱功能说明.md  # 工具箱功能详细说明

```

## 🚀 快速开始

### 方式一：使用批处理文件（推荐）
1. 双击 `启动智能桌面助手.bat` - 直接启动完整程序
2. 双击 `启动菜单.bat` - 显示交互式菜单选择功能

### 方式二：命令行启动
```bash
# 启动完整程序
python main.py

# 启动特定模块
python main.py browser      # 全屏浏览器
python main.py desktop     # 桌面管理器
python main.py pet         # 桌面宠物
python main.py chat        # AI聊天
```

## 📚 详细文档

- [使用说明](使用说明.md) - 详细的功能说明和使用指南

## 🔧 主要功能

1. **全屏浏览器** - 支持全屏Web浏览，集成API服务器
2. **桌面管理器** - 任务管理、角色管理、进度报告
3. **智能工具箱** - 系统诊断、文件管理、网络工具等实用功能
4. **AI聊天助手** - 智能对话功能
5. **桌面宠物** - 可爱的桌面伴侣
6. **在线聊天** - 实时通讯功能

## 💡 特色功能

- **统一管理**：所有功能集成在一个程序中
- **系统托盘**：后台运行，随时切换功能
- **数据共享**：模块间自动同步数据
- **灵活启动**：支持整体启动或单独模块启动

## 📝 更新日志

### v2.0.0 (2024-01)
- 重构为统一的集成应用程序
- 添加系统托盘功能
- 优化模块间数据共享
- 改进用户体验

### v1.0.0 (2024-01)
- 初始版本发布