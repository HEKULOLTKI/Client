# 客户端PDF预览功能使用指南

## 概述

客户端PDF预览功能已成功集成到现有的8800端口HTTP服务器中。该功能允许后端服务器通过发送JSON数据来触发客户端自动下载和打开PDF文件。

## 功能特点

✅ **自动接收**: 客户端监听8800端口的`/pdf-preview`路由
✅ **JSON解析**: 支持标准格式的PDF预览请求数据
✅ **安全验证**: URL和文件类型安全验证
✅ **自动下载**: 支持HTTP/HTTPS协议的文件下载
✅ **自动打开**: 使用系统默认程序打开PDF文件
✅ **错误处理**: 完善的错误处理和日志记录
✅ **测试支持**: 支持本地文件协议（用于测试）

## 启动客户端

### 1. 运行浏览器客户端
```bash
cd 项目根目录
python src/browser/fullscreen_browser.py
```

### 2. 通过主程序启动
```bash
python main.py browser
```

客户端启动后会显示：
```
API服务器启动中，监听8800端口...
API服务器地址: http://localhost:8800
上传JSON数据: POST http://localhost:8800/upload
检查API状态: GET http://localhost:8800/status
```

## API接口说明

### PDF预览接口
- **URL**: `http://localhost:8800/pdf-preview`
- **方法**: `POST`
- **内容类型**: `application/json`

### 请求数据格式

```json
{
    "action": "pdf_download_and_preview",
    "data": {
        "filename": "项目任务汇报单子（运维）.pdf",
        "download_url": "http://localhost:8000/api/pdf/download/report.pdf",
        "file_size": 105874,
        "modification_time": 1703123456.789,
        "preview_type": "pdf_document",
        "request_time": 1703123456.789,
        "server_info": {
            "host": "localhost",
            "port": 8000,
            "protocol": "http"
        },
        "requester": {
            "user_id": 1,
            "username": "admin",
            "role": "admin",
            "type": "admin"
        }
    },
    "instructions": {
        "action_required": "download_and_open_pdf",
        "download_url": "http://localhost:8000/api/pdf/download/report.pdf",
        "display_mode": "default_viewer",
        "cache_policy": "download_fresh"
    }
}
```

### 响应数据格式

```json
{
    "status": "success",
    "message": "PDF预览请求已接收",
    "timestamp": 1703123456.789,
    "received_data": {
        "filename": "项目任务汇报单子（运维）.pdf",
        "file_size": 105874
    }
}
```

## 测试功能

### 运行测试脚本
```bash
python tests/test_pdf_client.py
```

测试脚本会：
1. 检查客户端服务状态
2. 发送标准PDF预览请求
3. 使用项目中的真实PDF文件进行测试
4. 显示详细的测试结果

### 手动测试

使用curl命令测试：
```bash
curl -X POST http://localhost:8800/pdf-preview \
  -H "Content-Type: application/json" \
  -d '{
    "action": "pdf_download_and_preview",
    "data": {
      "filename": "test.pdf",
      "download_url": "http://example.com/test.pdf",
      "file_size": 12345
    },
    "instructions": {
      "action_required": "download_and_open_pdf"
    }
  }'
```

## 工作流程

1. **接收请求**: 客户端在8800端口接收POST请求
2. **验证数据**: 验证JSON格式和必要字段
3. **安全检查**: 验证URL和文件类型的安全性
4. **下载文件**: 从指定URL下载PDF文件到临时目录
5. **打开文件**: 使用系统默认程序打开PDF文件
6. **返回响应**: 向发送方返回处理结果

## 安全特性

### URL验证
- 只允许HTTP、HTTPS和file（测试用）协议
- 验证主机名白名单
- 支持私网地址访问

### 文件类型验证
- 只允许`.pdf`文件扩展名
- 防止恶意文件执行

### 临时文件管理
- 文件下载到系统临时目录
- 使用专用文件夹`ACO_PDF_Preview`
- 避免文件路径冲突

## 错误处理

常见错误及解决方案：

### 连接被拒绝
```
❌ 连接被拒绝
   请确保客户端服务正在运行并监听8800端口
```
**解决**: 启动fullscreen_browser程序

### 无效的操作类型
```
❌ 无效的操作类型
```
**解决**: 确保JSON中`action`字段为`"pdf_download_and_preview"`

### 下载失败
```
❌ 下载PDF文件时网络错误
```
**解决**: 检查网络连接和URL是否可访问

### 文件打开失败
```
❌ 打开PDF文件失败
📁 请手动打开文件: /path/to/file.pdf
```
**解决**: 确保系统安装了PDF阅读器

## 日志监控

客户端会输出详细的日志信息：

```
📄 接收到PDF预览请求
📋 文件名: 项目任务汇报单子（测试）.pdf
🔗 下载URL: http://localhost:8000/api/pdf/download/test.pdf
📏 文件大小: 105874 bytes
📥 开始下载PDF文件: 项目任务汇报单子（测试）.pdf
💾 保存路径: /tmp/ACO_PDF_Preview/项目任务汇报单子（测试）.pdf
📊 下载进度: 100.0%
✅ PDF文件下载成功！
🖥️ 检测到操作系统: Windows
📄 准备打开PDF文件: /tmp/ACO_PDF_Preview/项目任务汇报单子（测试）.pdf
✅ 已使用Windows默认程序打开PDF
🎉 PDF文件已成功打开
```

## 集成说明

### 后端集成
后端服务器需要：
1. 获取客户端IP地址
2. 构建符合格式的JSON数据
3. 向`http://客户端IP:8800/pdf-preview`发送POST请求

### 前端集成
前端可以通过：
1. 按钮点击触发后端API
2. 后端处理PDF生成和发送
3. 客户端自动接收和处理

## 故障排除

### 检查服务状态
```bash
curl http://localhost:8800/status
```

### 查看日志
客户端会在控制台输出详细日志，包括：
- 请求接收情况
- 文件下载进度
- 错误信息和堆栈跟踪

### 常见问题
1. **端口占用**: 确保8800端口没有被其他程序占用
2. **防火墙**: 确保防火墙允许8800端口的入站连接
3. **网络连接**: 确保客户端可以访问PDF下载URL
4. **文件权限**: 确保有临时目录的写入权限

## 总结

客户端PDF预览功能提供了一个完整的解决方案，支持：
- 标准化的JSON数据格式
- 安全的文件下载和验证
- 跨平台的文件打开支持
- 完善的错误处理和日志记录

该功能已完全集成到现有的HTTP服务器中，可以与其他功能（如任务数据接收、数字孪生平台切换）无缝协作。 