# 桌面文件备份还原系统

这是一个集成在过渡界面中的桌面文件备份还原系统，能够在程序切换过程中无缝管理桌面上的所有文件和文件夹（排除系统文件）。

## 功能特点

- **全面备份**: 在启动 `desktop_manager` 时自动备份桌面上的所有文件和文件夹
- **智能过滤**: 自动排除系统文件和临时文件，只处理用户文件
- **自动还原**: 在关闭 `desktop_manager` 时自动还原桌面文件
- **支持文件夹**: 完整支持文件夹的递归备份和还原
- **无缝集成**: 操作过程隐藏在过渡界面中，用户体验流畅
- **进度显示**: 实时显示备份/还原进度
- **错误处理**: 完善的错误处理机制
- **广泛兼容**: 支持多种文件格式（文档、图片、音频、视频、压缩包等）

## 系统组件

### 1. 桌面文件管理器 (`desktop_icon_manager.py`)

负责核心的文件备份和还原功能：

- 自动检测桌面路径（Windows/Linux/Mac兼容）
- 扫描桌面上的所有文件和文件夹
- 智能过滤系统文件和临时文件
- 支持多种文件格式（图标、文档、图片、音频、视频等）
- 完整的文件夹递归备份
- 备份文件到专用文件夹
- 从备份还原文件和文件夹
- 保存详细备份信息的 JSON 文件
- 保持文件时间戳和属性

### 2. 增强过渡界面 (`enhanced_transition_screen.py`)

在原有过渡界面基础上增加文件操作功能：

- 继承原有的科技感过渡界面样式
- 后台执行文件和文件夹备份/还原操作
- 实时更新操作进度和状态信息
- 支持独立进程运行
- 多线程处理确保界面响应

### 3. 集成修改

- **fullscreen_browser.py**: 修改为启动带备份功能的过渡界面
- **desktop_manager.py**: 修改为启动带还原功能的过渡界面

## 工作流程

### 启动 Desktop Manager 流程

1. 用户在 `fullscreen_browser` 中选择角色
2. 系统检测到角色选择，开始关闭流程
3. 启动 `enhanced_transition_screen.py --backup`
4. 过渡界面显示，同时后台执行：
   - 扫描桌面图标
   - 备份图标到 `desktop_icons_backup` 文件夹
   - 从桌面移除图标
   - 保存备份信息
5. 备份完成后启动 `desktop_manager`
6. 过渡界面关闭

### 关闭 Desktop Manager 流程

1. 用户在 `desktop_manager` 中点击退出
2. 系统开始退出流程
3. 启动 `enhanced_transition_screen.py --restore`
4. 过渡界面显示，同时后台执行：
   - 读取备份信息
   - 从备份文件夹还原图标到桌面
   - 恢复图标的原始属性和时间戳
5. 还原完成后启动 `fullscreen_browser`
6. 过渡界面关闭

## 文件结构

```
项目根目录/
├── desktop_icon_manager.py          # 桌面文件管理器
├── enhanced_transition_screen.py    # 增强过渡界面
├── fullscreen_browser.py            # 修改后的全屏浏览器
├── desktop_manager.py               # 修改后的桌面管理器
├── transition_screen.py             # 原始过渡界面（被继承）
├── desktop_backup/                  # 自动创建的备份文件夹
│   ├── backup_info.json            # 备份信息文件
│   ├── [备份的文件...]              # 备份的各种文件
│   └── [备份的文件夹...]            # 备份的文件夹
├── test_desktop_icon_system.py     # 系统测试脚本
└── desktop_icon_backup_readme.md   # 本说明文档
```

## 使用方法

### 自动使用

系统已集成到现有程序中，无需手动操作：

1. 正常启动 `fullscreen_browser.py`
2. 选择角色后系统自动进入备份流程
3. 在 `desktop_manager` 中点击退出自动进入还原流程

### 手动测试

可以单独测试图标管理功能：

```bash
# 测试桌面图标管理器
python desktop_icon_manager.py

# 测试带备份的过渡界面
python enhanced_transition_screen.py "正在备份桌面图标..." 5000 --backup

# 测试带还原的过渡界面
python enhanced_transition_screen.py "正在还原桌面图标..." 5000 --restore
```

## 配置说明

### 支持的文件类型

系统支持广泛的文件类型，包括但不限于：

**图标和快捷方式**：
- `.lnk` - Windows 快捷方式
- `.url` - 网页快捷方式

**可执行文件**：
- `.exe`, `.bat`, `.cmd`, `.msi`, `.com`

**文档文件**：
- `.txt`, `.doc`, `.docx`, `.pdf`, `.xls`, `.xlsx`, `.ppt`, `.pptx`
- `.rtf`, `.odt`, `.ods`, `.odp`

**媒体文件**：
- 图片：`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.ico`, `.svg`
- 音频：`.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.wma`
- 视频：`.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`

**压缩文件**：
- `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`

**代码文件**：
- `.py`, `.js`, `.html`, `.css`, `.java`, `.cpp`, `.c`, `.h`

**其他文件**：
- `.json`, `.xml`, `.csv`, `.log`, `.ini`, `.cfg`, `.conf`
- 文件夹和无扩展名文件

### 系统文件过滤

自动排除以下类型的系统文件：
- `desktop.ini`, `thumbs.db`, `desktop.db` (Windows)
- `.ds_store` (macOS), `.directory` (Linux KDE)
- `$recycle.bin`, `system volume information` (Windows)
- 以 `.` 开头的隐藏文件（除特殊情况）
- 临时文件（`.tmp`, `.temp`）
- 以 `~` 开头的临时文件

### 备份位置

- 备份文件夹：`项目根目录/desktop_backup/`
- 备份信息：`desktop_backup/backup_info.json`

### 过渡界面样式

- 保持原有的科技感蓝色主题
- 动态进度显示
- 实时状态更新
- 二进制码动画效果

## 安全特性

1. **非破坏性备份**: 先备份再移动，确保数据安全
2. **完整性验证**: 备份信息包含文件大小和修改时间
3. **错误恢复**: 操作失败时保留原始状态
4. **时间戳保持**: 还原时保持文件的原始时间属性

## 故障排除

### 常见问题

1. **桌面路径检测失败**
   - 系统会自动尝试多种方法获取桌面路径
   - 支持 Windows、Linux、Mac 多平台

2. **权限不足**
   - 确保程序有读写桌面和创建文件夹的权限
   - Windows 下可能需要管理员权限

3. **备份文件丢失**
   - 检查 `desktop_icons_backup` 文件夹是否存在
   - 查看 `backup_info.json` 文件内容

4. **过渡界面不显示**
   - 检查 PyQt5 是否正确安装
   - 确认所有依赖文件存在

### 调试信息

程序运行时会输出详细的调试信息：
- 桌面路径检测结果
- 扫描到的图标数量
- 备份/还原操作进度
- 错误信息和堆栈跟踪

## 版本历史

- **v1.0.0**: 初始版本，基本的备份还原功能
- 集成到现有的过渡界面系统
- 支持自动化工作流程

## 技术实现

- **语言**: Python 3.x
- **GUI框架**: PyQt5
- **多线程**: QThread 用于后台操作
- **文件操作**: shutil, os, glob
- **数据存储**: JSON 格式的备份信息
- **进程管理**: subprocess 用于启动独立过渡界面

## 贡献指南

如需扩展功能，请注意：

1. 保持与现有过渡界面样式的一致性
2. 确保所有操作都是非阻塞的
3. 添加适当的错误处理和日志记录
4. 遵循现有的代码风格和命名规范

## 许可证

本项目遵循与主项目相同的许可证。 