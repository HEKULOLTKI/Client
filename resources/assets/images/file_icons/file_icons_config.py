"""
文件图标配置文件
映射文件扩展名到对应的 SVG 图标文件
"""

import os

# 获取文件图标目录路径
FILE_ICONS_DIR = os.path.dirname(os.path.abspath(__file__))

# 文件类型到图标的映射
FILE_TYPE_ICONS = {
    # PDF 文件
    '.pdf': os.path.join(FILE_ICONS_DIR, 'PDF.svg'),
    
    # Word 文档
    '.doc': os.path.join(FILE_ICONS_DIR, 'word.svg'),
    '.docx': os.path.join(FILE_ICONS_DIR, 'word.svg'),
    
    # Excel 表格
    '.xls': os.path.join(FILE_ICONS_DIR, 'excel.svg'),
    '.xlsx': os.path.join(FILE_ICONS_DIR, 'excel.svg'),
    
    # PowerPoint 演示文稿
    '.ppt': os.path.join(FILE_ICONS_DIR, 'PPT.svg'),
    '.pptx': os.path.join(FILE_ICONS_DIR, 'PPT.svg'),
    
    # 文本文件
    '.txt': os.path.join(FILE_ICONS_DIR, 'TXT.svg'),
    '.md': os.path.join(FILE_ICONS_DIR, 'TXT.svg'),
    '.rtf': os.path.join(FILE_ICONS_DIR, 'TXT.svg'),
    
    # 脚本/代码文件
    '.py': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.js': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.html': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.css': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.json': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.xml': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.yml': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.yaml': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.java': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.cpp': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.c': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.sh': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    '.bat': os.path.join(FILE_ICONS_DIR, '脚本.svg'),
    
    # 压缩文件（暂时使用未知图标）
    '.zip': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.rar': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.7z': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.tar': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.gz': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.bz2': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    
    # 音频文件（暂时使用未知图标）
    '.mp3': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.wav': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.flac': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.aac': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.ogg': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.wma': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    
    # 视频文件（暂时使用未知图标）
    '.mp4': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.avi': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.mov': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.mkv': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.flv': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.wmv': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.webm': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    
    # 图片文件（暂时使用未知图标）
    '.jpg': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.jpeg': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.png': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.gif': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.webp': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.bmp': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    '.svg': os.path.join(FILE_ICONS_DIR, '未知.svg'),
    
    # 默认图标
    'default': os.path.join(FILE_ICONS_DIR, '未知.svg')
}

def get_file_icon_path(file_name):
    """
    根据文件名获取对应的图标路径
    
    Args:
        file_name: 文件名
        
    Returns:
        图标文件的完整路径
    """
    if not file_name:
        return FILE_TYPE_ICONS['default']
    
    file_ext = os.path.splitext(file_name.lower())[1]
    return FILE_TYPE_ICONS.get(file_ext, FILE_TYPE_ICONS['default']) 