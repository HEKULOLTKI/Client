#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import json
import glob
from pathlib import Path
import winreg
import sys
from typing import List, Dict, Optional
import time

class DesktopIconManager:
    """桌面图标管理器 - 负责备份和还原桌面图标"""
    
    def __init__(self):
        self.desktop_path = self.get_desktop_path()
        self.backup_folder = os.path.join(os.getcwd(), "desktop_backup")
        self.backup_info_file = os.path.join(self.backup_folder, "backup_info.json")
        
        # 支持的文件扩展名（包括图标和其他文件）
        self.supported_extensions = [
            # 图标和快捷方式
            '.lnk', '.url', 
            # 可执行文件
            '.exe', '.bat', '.cmd', '.msi', '.com',
            # 文档文件
            '.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx',
            '.rtf', '.odt', '.ods', '.odp',
            # 图片文件
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.svg',
            # 音频文件
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma',
            # 视频文件
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            # 压缩文件
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            # 代码文件
            '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h',
            # 其他常见文件
            '.json', '.xml', '.csv', '.log', '.ini', '.cfg', '.conf'
        ]
        
        # 系统文件和文件夹（需要排除的）
        self.system_files = {
            # Windows系统文件
            'desktop.ini', 'thumbs.db', 'desktop.db', 'folder.htt',
            # 系统文件夹
            '$recycle.bin', 'system volume information',
            # 隐藏文件标识
            '.ds_store',  # macOS
            '.directory',  # Linux KDE
            '.trash'  # Linux
        }
        
        # 系统文件夹（需要排除的）
        self.system_folders = {
            '$recycle.bin', 'system volume information', 'recovery',
            '.trash-1000', '.local', '.config'  # Linux 相关
        }
        
    def get_desktop_path(self) -> str:
        """获取桌面路径"""
        if sys.platform == "win32":
            try:
                # 获取当前用户的桌面路径
                import ctypes.wintypes
                CSIDL_DESKTOP = 0
                
                # 使用Windows API获取桌面路径
                dll = ctypes.windll.shell32
                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                dll.SHGetSpecialFolderPathW(None, buf, CSIDL_DESKTOP, False)
                return buf.value
            except:
                # 备用方法
                return os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            # Linux/Mac
            return os.path.join(os.path.expanduser("~"), "Desktop")
    
    def create_backup_folder(self):
        """创建备份文件夹"""
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
                print(f"已创建备份文件夹: {self.backup_folder}")
            return True
        except Exception as e:
            print(f"创建备份文件夹失败: {str(e)}")
            return False
    
    def is_system_file(self, file_path: str) -> bool:
        """检查是否是系统文件"""
        file_name = os.path.basename(file_path).lower()
        
        # 检查是否是系统文件
        if file_name in self.system_files:
            return True
        
        # 检查是否是隐藏文件（以.开头的文件，除了一些特殊情况）
        if file_name.startswith('.') and file_name not in {'.gitignore', '.htaccess'}:
            return True
        
        # 检查是否是临时文件
        if file_name.startswith('~') or file_name.endswith('.tmp') or file_name.endswith('.temp'):
            return True
        
        # 检查是否是系统文件夹
        if os.path.isdir(file_path):
            if file_name in self.system_folders:
                return True
        
        return False
    
    def scan_desktop_files(self) -> List[Dict]:
        """扫描桌面上的所有文件（排除系统文件）"""
        files = []
        try:
            if not os.path.exists(self.desktop_path):
                print(f"桌面路径不存在: {self.desktop_path}")
                return files
            
            # 获取桌面上的所有项目
            desktop_items = os.listdir(self.desktop_path)
            
            for item_name in desktop_items:
                item_path = os.path.join(self.desktop_path, item_name)
                
                # 跳过系统文件和文件夹
                if self.is_system_file(item_path):
                    print(f"跳过系统文件: {item_name}")
                    continue
                
                # 处理文件
                if os.path.isfile(item_path):
                    # 获取文件扩展名
                    _, ext = os.path.splitext(item_name.lower())
                    
                    # 如果是支持的扩展名或者没有扩展名的文件也备份
                    if ext in self.supported_extensions or ext == '':
                        try:
                            file_info = {
                                'name': item_name,
                                'path': item_path,
                                'extension': ext,
                                'size': os.path.getsize(item_path),
                                'modified_time': os.path.getmtime(item_path),
                                'type': 'file'
                            }
                            files.append(file_info)
                        except Exception as e:
                            print(f"获取文件信息失败 {item_name}: {str(e)}")
                            continue
                
                # 处理文件夹（非系统文件夹）
                elif os.path.isdir(item_path):
                    try:
                        # 计算文件夹大小（递归计算）
                        folder_size = self.get_folder_size(item_path)
                        
                        folder_info = {
                            'name': item_name,
                            'path': item_path,
                            'extension': '',
                            'size': folder_size,
                            'modified_time': os.path.getmtime(item_path),
                            'type': 'folder'
                        }
                        files.append(folder_info)
                    except Exception as e:
                        print(f"获取文件夹信息失败 {item_name}: {str(e)}")
                        continue
            
            print(f"扫描到 {len(files)} 个桌面文件/文件夹")
            return files
        except Exception as e:
            print(f"扫描桌面文件失败: {str(e)}")
            return []
    
    def get_folder_size(self, folder_path: str) -> int:
        """计算文件夹大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        # 忽略无法访问的文件
                        continue
        except Exception:
            # 如果无法计算，返回0
            pass
        return total_size
    
    def scan_desktop_icons(self) -> List[Dict]:
        """扫描桌面上的图标文件（为了向后兼容保留此方法）"""
        return self.scan_desktop_files()
    
    def backup_desktop_files(self, callback=None) -> bool:
        """备份桌面文件到指定文件夹"""
        try:
            print("开始备份桌面文件...")
            
            # 创建备份文件夹
            if not self.create_backup_folder():
                return False
            
            # 扫描桌面文件
            files = self.scan_desktop_files()
            if not files:
                print("没有找到需要备份的文件")
                return True
            
            backup_info = {
                'backup_time': time.time(),
                'desktop_path': self.desktop_path,
                'files': []
            }
            
            successful_backups = 0
            total_files = len(files)
            
            for i, file_item in enumerate(files):
                try:
                    # 更新进度回调
                    if callback:
                        progress = int((i / total_files) * 50)  # 备份占50%进度
                        callback(f"正在备份: {file_item['name']}", progress)
                    
                    source_path = file_item['path']
                    backup_name = file_item['name']
                    backup_path = os.path.join(self.backup_folder, backup_name)
                    
                    # 如果备份文件已存在，添加序号
                    counter = 1
                    original_backup_path = backup_path
                    while os.path.exists(backup_path):
                        if file_item['type'] == 'folder':
                            backup_path = f"{original_backup_path}_{counter}"
                        else:
                            name, ext = os.path.splitext(original_backup_path)
                            backup_path = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    # 复制文件或文件夹
                    if file_item['type'] == 'folder':
                        shutil.copytree(source_path, backup_path)
                        print(f"已备份文件夹: {file_item['name']}")
                    else:
                        shutil.copy2(source_path, backup_path)
                        print(f"已备份文件: {file_item['name']}")
                    
                    # 记录备份信息
                    backup_info['files'].append({
                        'original_path': source_path,
                        'backup_path': backup_path,
                        'name': file_item['name'],
                        'extension': file_item['extension'],
                        'size': file_item['size'],
                        'modified_time': file_item['modified_time'],
                        'type': file_item['type']
                    })
                    
                    successful_backups += 1
                    
                except Exception as e:
                    print(f"备份 {file_item['name']} 失败: {str(e)}")
                    continue
            
            # 保存备份信息
            with open(self.backup_info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 移动桌面文件（备份完成后）
            moved_count = 0
            for i, file_info in enumerate(backup_info['files']):
                try:
                    if callback:
                        progress = 50 + int((i / len(backup_info['files'])) * 50)  # 移动占50%进度
                        callback(f"正在移动: {file_info['name']}", progress)
                    
                    if os.path.exists(file_info['original_path']):
                        if file_info['type'] == 'folder':
                            shutil.rmtree(file_info['original_path'])
                        else:
                            os.remove(file_info['original_path'])
                        moved_count += 1
                        print(f"已移动: {file_info['name']}")
                except Exception as e:
                    print(f"移动 {file_info['name']} 失败: {str(e)}")
            
            print(f"桌面文件备份完成！成功备份 {successful_backups} 个文件/文件夹，移动 {moved_count} 个项目")
            return True
            
        except Exception as e:
            print(f"备份桌面文件失败: {str(e)}")
            return False
    
    def backup_desktop_icons(self, callback=None) -> bool:
        """备份桌面图标到指定文件夹（为了向后兼容保留此方法）"""
        return self.backup_desktop_files(callback)
    
    def restore_desktop_files(self, callback=None) -> bool:
        """从备份文件夹还原桌面文件"""
        try:
            print("开始还原桌面文件...")
            
            # 检查备份信息文件是否存在
            if not os.path.exists(self.backup_info_file):
                print("没有找到备份信息文件，无法还原")
                return False
            
            # 读取备份信息
            with open(self.backup_info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            # 兼容旧版本的备份格式
            files = backup_info.get('files', backup_info.get('icons', []))
            if not files:
                print("备份信息中没有文件记录")
                return True
            
            successful_restores = 0
            total_files = len(files)
            
            for i, file_info in enumerate(files):
                try:
                    # 更新进度回调
                    if callback:
                        progress = int((i / total_files) * 100)
                        callback(f"正在还原: {file_info['name']}", progress)
                    
                    backup_path = file_info['backup_path']
                    original_path = file_info['original_path']
                    file_type = file_info.get('type', 'file')  # 默认为文件类型
                    
                    # 检查备份文件是否存在
                    if not os.path.exists(backup_path):
                        print(f"备份文件不存在: {backup_path}")
                        continue
                    
                    # 如果原位置已存在文件，先删除
                    if os.path.exists(original_path):
                        if os.path.isdir(original_path):
                            shutil.rmtree(original_path)
                        else:
                            os.remove(original_path)
                    
                    # 复制文件或文件夹回桌面
                    if file_type == 'folder':
                        shutil.copytree(backup_path, original_path)
                        print(f"已还原文件夹: {file_info['name']}")
                    else:
                        shutil.copy2(backup_path, original_path)
                        print(f"已还原文件: {file_info['name']}")
                    
                    # 设置文件时间
                    modified_time = file_info['modified_time']
                    os.utime(original_path, (modified_time, modified_time))
                    
                    successful_restores += 1
                    
                except Exception as e:
                    print(f"还原 {file_info['name']} 失败: {str(e)}")
                    continue
            
            # 清理备份文件夹（可选）
            # self.cleanup_backup()
            
            print(f"桌面文件还原完成！成功还原 {successful_restores} 个文件/文件夹")
            return True
            
        except Exception as e:
            print(f"还原桌面文件失败: {str(e)}")
            return False
    
    def restore_desktop_icons(self, callback=None) -> bool:
        """从备份文件夹还原桌面图标（为了向后兼容保留此方法）"""
        return self.restore_desktop_files(callback)
    
    def cleanup_backup(self):
        """清理备份文件夹"""
        try:
            if os.path.exists(self.backup_folder):
                shutil.rmtree(self.backup_folder)
                print("已清理备份文件夹")
        except Exception as e:
            print(f"清理备份文件夹失败: {str(e)}")
    
    def has_backup(self) -> bool:
        """检查是否存在备份"""
        return os.path.exists(self.backup_info_file)
    
    def get_backup_info(self) -> Optional[Dict]:
        """获取备份信息"""
        try:
            if self.has_backup():
                with open(self.backup_info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"读取备份信息失败: {str(e)}")
        return None


# 测试代码
if __name__ == "__main__":
    manager = DesktopIconManager()
    
    def progress_callback(message, progress):
        print(f"进度 {progress}%: {message}")
    
    print("桌面图标管理器测试")
    print(f"桌面路径: {manager.desktop_path}")
    print(f"备份文件夹: {manager.backup_folder}")
    
    # 测试备份
    print("\n开始备份测试...")
    success = manager.backup_desktop_icons(progress_callback)
    print(f"备份结果: {'成功' if success else '失败'}")
    
    # 等待用户确认
    input("\n按回车键开始还原测试...")
    
    # 测试还原
    print("\n开始还原测试...")
    success = manager.restore_desktop_icons(progress_callback)
    print(f"还原结果: {'成功' if success else '失败'}") 