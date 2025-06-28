# PDF弹窗查看器使用指南

## 概述

本项目已升级PDF预览功能，现在使用PyMuPDF渲染PDF为图像显示的弹窗查看器，替代之前的系统默认程序打开方式。新的PDF查看器提供了更好的用户体验和更多功能。

## 主要特性

### 🎯 核心功能
- **高质量渲染**: 使用PyMuPDF将PDF页面渲染为高质量图像
- **弹窗显示**: 在独立弹窗中显示PDF，无需依赖系统默认PDF阅读器
- **多线程渲染**: 使用后台线程渲染，避免界面卡顿
- **中文支持**: 完美支持中文文件名和中文内容显示

### 📖 查看功能
- **页面导航**: 支持上一页/下一页、跳转到指定页面
- **缩放控制**: 25%-400%自由缩放，支持适应宽度/适应页面
- **全文搜索**: 支持在PDF中搜索文本，跨页面查找
- **状态显示**: 实时显示当前页码、总页数、缩放比例等信息

### ⌨️ 快捷键支持
- **页面导航**:
  - `←` / `→`: 上一页/下一页
  - `Home`: 第一页
  - `End`: 最后一页
- **缩放操作**:
  - `Ctrl + +`: 放大
  - `Ctrl + -`: 缩小
  - `Ctrl + 0`: 适应页面
- **其他功能**:
  - `Ctrl + F`: 搜索文本
  - `ESC`: 关闭查看器

## 技术实现

### 🔧 核心组件

#### 1. PDF查看器组件 (`src/ui/widgets/pdf_viewer_widget.py`)
```python
class PDFViewerWidget(QDialog):
    """主要的PDF查看器弹窗"""
    
class PDFRenderThread(QThread):
    """PDF渲染线程，避免界面阻塞"""
    
def show_pdf_viewer(pdf_path, parent=None):
    """便利函数，显示PDF查看器"""
```

#### 2. 修改的文件
- `src/browser/fullscreen_browser.py` - 原始版本客户端
- `src/browser/fullscreen_browser_fixed.py` - 修复版本客户端

### 🔄 工作流程

1. **接收PDF预览请求**
   - 客户端接收包含PDF信息的JSON请求
   - 提取文件名、下载URL等信息

2. **下载PDF文件**
   - 从指定URL下载PDF文件
   - 处理中文文件名编码问题
   - 保存到临时目录

3. **显示PDF查看器**
   - 调用PyMuPDF弹窗查看器
   - 在后台线程中渲染PDF页面
   - 提供完整的交互功能

4. **资源清理**
   - 查看器关闭时自动清理资源
   - 停止渲染线程
   - 关闭PDF文档句柄

## 使用方法

### 🚀 启动客户端

#### 使用修复版本（推荐）:
```bash
python src/browser/fullscreen_browser_fixed.py
```

#### 使用原始版本:
```bash
python src/browser/fullscreen_browser.py
```

### 📄 PDF预览请求格式

发送POST请求到 `http://localhost:8800/pdf-preview`:

```json
{
    "action": "pdf_download_and_preview",
    "data": {
        "filename": "项目任务汇报单子（系统分析师）.pdf",
        "download_url": "http://localhost:8000/api/pdf/download/项目任务汇报单子（系统分析师）.pdf",
        "file_size": 12345,
        "modification_time": 1703123456.789,
        "preview_type": "pdf_document"
    },
    "instructions": {
        "action_required": "download_and_open_pdf",
        "display_mode": "default_viewer",
        "cache_policy": "download_fresh"
    }
}
```

### 🧪 功能测试

运行测试脚本验证功能:
```bash
python test_pdf_viewer.py
```

测试脚本提供以下选项:
1. 测试PyMuPDF弹窗查看器
2. 测试系统默认PDF查看器
3. 同时测试两种查看器
4. 选择现有PDF文件测试

## 依赖要求

### 📦 Python包依赖

确保已安装以下包:
```bash
pip install PyMuPDF>=1.23.0
pip install PyQt5>=5.15.7
pip install PyQtWebEngine>=5.15.6
pip install requests>=2.28.0
pip install flask>=2.2.0
pip install flask-cors>=3.0.0
```

或者使用requirements.txt:
```bash
pip install -r requirements.txt
```

### 🔧 系统要求
- Python 3.7+
- Windows 10/Linux/macOS
- 支持PyQt5的图形环境

## 错误处理

### 🛡️ 回退机制

如果PyMuPDF弹窗查看器失败，系统会自动回退到系统默认PDF阅读器:

```python
def open_pdf_file(self, file_path):
    try:
        # 尝试使用PyMuPDF弹窗查看器
        show_pdf_viewer(file_path, None)
    except Exception as e:
        # 回退到系统默认程序
        self._fallback_open_pdf(file_path)
```

### 🐛 常见问题

#### 1. PyMuPDF导入失败
```
❌ 无法导入PDF查看器组件: No module named 'fitz'
```
**解决方案**: 安装PyMuPDF
```bash
pip install PyMuPDF
```

#### 2. PDF文件打不开
```
❌ 加载PDF文件失败: [Errno 2] No such file or directory
```
**解决方案**: 检查文件路径是否正确，确保文件存在

#### 3. 中文文件名乱码
系统已经内置了中文文件名处理功能，会自动:
- URL解码文件名
- 清理不安全字符
- 确保文件名在文件系统中有效

## 性能优化

### ⚡ 渲染优化
- **多线程渲染**: 在后台线程中渲染PDF页面
- **按需渲染**: 只渲染当前显示的页面
- **进度显示**: 提供渲染进度反馈

### 💾 内存管理
- **资源清理**: 查看器关闭时自动清理PDF文档和图像资源
- **线程管理**: 正确停止和清理渲染线程
- **临时文件**: 自动清理下载的临时PDF文件

## 扩展功能

### 🔮 未来可能的改进
- **页面缩略图**: 添加页面缩略图导航
- **注释支持**: 支持PDF注释的显示
- **打印功能**: 添加PDF打印功能
- **导出功能**: 支持导出页面为图片
- **书签支持**: 显示和导航PDF书签

### 🎨 界面定制
可以通过修改`PDFViewerWidget`类来定制:
- 工具栏布局
- 颜色主题
- 按钮样式
- 快捷键绑定

## 总结

新的PDF弹窗查看器提供了:
- ✅ 更好的用户体验
- ✅ 完整的功能支持
- ✅ 可靠的错误处理
- ✅ 高性能渲染
- ✅ 完美的中文支持

这个升级大大改善了PDF预览功能的可用性和用户体验，同时保持了良好的向后兼容性。 