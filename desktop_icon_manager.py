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
        self.backup_folder = os.path.join(os.getcwd(), "desktop_icons_backup")
        self.backup_info_file = os.path.join(self.backup_folder, "backup_info.json")
        self.supported_extensions = ['.lnk', '.url', '.exe', '.bat', '.cmd']
        
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
    
    def scan_desktop_icons(self) -> List[Dict]:
        """扫描桌面上的图标文件"""
        icons = []
        try:
            if not os.path.exists(self.desktop_path):
                print(f"桌面路径不存在: {self.desktop_path}")
                return icons
            
            # 扫描桌面上的所有支持的文件类型
            for extension in self.supported_extensions:
                pattern = os.path.join(self.desktop_path, f"*{extension}")
                files = glob.glob(pattern)
                
                for file_path in files:
                    if os.path.isfile(file_path):
                        file_info = {
                            'name': os.path.basename(file_path),
                            'path': file_path,
                            'extension': extension,
                            'size': os.path.getsize(file_path),
                            'modified_time': os.path.getmtime(file_path)
                        }
                        icons.append(file_info)
            
            print(f"扫描到 {len(icons)} 个桌面图标")
            return icons
        except Exception as e:
            print(f"扫描桌面图标失败: {str(e)}")
            return []
    
    def backup_desktop_icons(self, callback=None) -> bool:
        """备份桌面图标到指定文件夹"""
        try:
            print("开始备份桌面图标...")
            
            # 创建备份文件夹
            if not self.create_backup_folder():
                return False
            
            # 扫描桌面图标
            icons = self.scan_desktop_icons()
            if not icons:
                print("没有找到需要备份的图标")
                return True
            
            backup_info = {
                'backup_time': time.time(),
                'desktop_path': self.desktop_path,
                'icons': []
            }
            
            successful_backups = 0
            total_icons = len(icons)
            
            for i, icon in enumerate(icons):
                try:
                    # 更新进度回调
                    if callback:
                        progress = int((i / total_icons) * 50)  # 备份占50%进度
                        callback(f"正在备份图标: {icon['name']}", progress)
                    
                    source_path = icon['path']
                    backup_path = os.path.join(self.backup_folder, icon['name'])
                    
                    # 如果备份文件已存在，添加序号
                    counter = 1
                    original_backup_path = backup_path
                    while os.path.exists(backup_path):
                        name, ext = os.path.splitext(original_backup_path)
                        backup_path = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    # 复制文件
                    shutil.copy2(source_path, backup_path)
                    
                    # 记录备份信息
                    backup_info['icons'].append({
                        'original_path': source_path,
                        'backup_path': backup_path,
                        'name': icon['name'],
                        'extension': icon['extension'],
                        'size': icon['size'],
                        'modified_time': icon['modified_time']
                    })
                    
                    successful_backups += 1
                    print(f"已备份: {icon['name']}")
                    
                except Exception as e:
                    print(f"备份图标 {icon['name']} 失败: {str(e)}")
                    continue
            
            # 保存备份信息
            with open(self.backup_info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 移动桌面图标（备份完成后）
            moved_count = 0
            for i, icon_info in enumerate(backup_info['icons']):
                try:
                    if callback:
                        progress = 50 + int((i / len(backup_info['icons'])) * 50)  # 移动占50%进度
                        callback(f"正在移动图标: {icon_info['name']}", progress)
                    
                    if os.path.exists(icon_info['original_path']):
                        os.remove(icon_info['original_path'])
                        moved_count += 1
                        print(f"已移动: {icon_info['name']}")
                except Exception as e:
                    print(f"移动图标 {icon_info['name']} 失败: {str(e)}")
            
            print(f"桌面图标备份完成！成功备份 {successful_backups} 个图标，移动 {moved_count} 个图标")
            return True
            
        except Exception as e:
            print(f"备份桌面图标失败: {str(e)}")
            return False
    
    def restore_desktop_icons(self, callback=None) -> bool:
        """从备份文件夹还原桌面图标"""
        try:
            print("开始还原桌面图标...")
            
            # 检查备份信息文件是否存在
            if not os.path.exists(self.backup_info_file):
                print("没有找到备份信息文件，无法还原")
                return False
            
            # 读取备份信息
            with open(self.backup_info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            icons = backup_info.get('icons', [])
            if not icons:
                print("备份信息中没有图标记录")
                return True
            
            successful_restores = 0
            total_icons = len(icons)
            
            for i, icon_info in enumerate(icons):
                try:
                    # 更新进度回调
                    if callback:
                        progress = int((i / total_icons) * 100)
                        callback(f"正在还原图标: {icon_info['name']}", progress)
                    
                    backup_path = icon_info['backup_path']
                    original_path = icon_info['original_path']
                    
                    # 检查备份文件是否存在
                    if not os.path.exists(backup_path):
                        print(f"备份文件不存在: {backup_path}")
                        continue
                    
                    # 如果原位置已存在文件，先删除
                    if os.path.exists(original_path):
                        os.remove(original_path)
                    
                    # 复制文件回桌面
                    shutil.copy2(backup_path, original_path)
                    
                    # 设置文件时间
                    os.utime(original_path, (icon_info['modified_time'], icon_info['modified_time']))
                    
                    successful_restores += 1
                    print(f"已还原: {icon_info['name']}")
                    
                except Exception as e:
                    print(f"还原图标 {icon_info['name']} 失败: {str(e)}")
                    continue
            
            # 清理备份文件夹（可选）
            # self.cleanup_backup()
            
            print(f"桌面图标还原完成！成功还原 {successful_restores} 个图标")
            return True
            
        except Exception as e:
            print(f"还原桌面图标失败: {str(e)}")
            return False
    
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