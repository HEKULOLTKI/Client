#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动清理JSON文件脚本
当自动清理不工作时，可以手动运行此脚本来清理JSON文件
"""

import os
import json
import time
from datetime import datetime

def cleanup_json_files(verbose=True):
    """清理JSON文件"""
    try:
        if verbose:
            print("🧹 开始手动清理JSON文件...")
            print(f"   当前工作目录: {os.getcwd()}")
            print(f"   执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        json_files = [
            'received_data.json',
            'received_tasks.json'
        ]
        
        deleted_files = []
        
        # 检查并删除主要JSON文件
        for file_path in json_files:
            full_path = os.path.abspath(file_path)
            if verbose:
                print(f"🔍 检查文件: {full_path}")
            
            if os.path.exists(file_path):
                try:
                    # 先读取文件内容用于日志记录
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if verbose:
                            if file_path == 'received_tasks.json':
                                tasks_count = len(data.get('tasks', []))
                                print(f"   📋 文件包含 {tasks_count} 个任务")
                            elif file_path == 'received_data.json':
                                user_info = data.get('user', {}).get('username', '未知')
                                print(f"   👤 文件包含用户信息: {user_info}")
                    except:
                        if verbose:
                            print(f"   ⚠️  无法读取文件内容，但将继续删除")
                    
                    # 删除文件
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    if verbose:
                        print(f"✅ 已删除JSON文件: {file_path}")
                        
                except Exception as e:
                    if verbose:
                        print(f"❌ 删除文件 {file_path} 失败: {str(e)}")
            else:
                if verbose:
                    print(f"⚪ 文件不存在: {file_path}")
        
        # 清理备份文件（.notified_* 结尾的文件）
        current_dir = os.getcwd()
        if verbose:
            print(f"🔍 扫描备份文件目录: {current_dir}")
        
        backup_files = []
        try:
            for filename in os.listdir(current_dir):
                if filename.startswith('received_tasks.json.notified_'):
                    backup_files.append(filename)
            
            if verbose:
                print(f"🔍 找到 {len(backup_files)} 个备份文件")
            
            for filename in backup_files:
                try:
                    backup_path = os.path.join(current_dir, filename)
                    
                    # 获取文件创建时间
                    if verbose:
                        try:
                            stat_info = os.stat(backup_path)
                            create_time = datetime.fromtimestamp(stat_info.st_ctime)
                            print(f"   📅 备份文件 {filename} 创建于: {create_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        except:
                            pass
                    
                    os.remove(backup_path)
                    deleted_files.append(filename)
                    if verbose:
                        print(f"✅ 已删除备份文件: {filename}")
                        
                except Exception as e:
                    if verbose:
                        print(f"❌ 删除备份文件 {filename} 失败: {str(e)}")
                        
        except Exception as e:
            if verbose:
                print(f"❌ 扫描备份文件时出错: {str(e)}")
        
        # 清理结果
        if deleted_files:
            if verbose:
                print(f"\n🧹 JSON文件清理完成，共删除 {len(deleted_files)} 个文件:")
                for file in deleted_files:
                    print(f"   - {file}")
        else:
            if verbose:
                print("\n🧹 没有找到需要清理的JSON文件")
        
        return len(deleted_files), deleted_files
                
    except Exception as e:
        if verbose:
            print(f"❌ 清理JSON文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        return 0, []

def check_json_files():
    """检查JSON文件状态"""
    print("📋 检查JSON文件状态...")
    print(f"   当前工作目录: {os.getcwd()}")
    
    json_files = [
        'received_data.json',
        'received_tasks.json'
    ]
    
    found_files = []
    
    # 检查主要JSON文件
    for file_path in json_files:
        full_path = os.path.abspath(file_path)
        print(f"\n🔍 检查文件: {file_path}")
        
        if os.path.exists(file_path):
            try:
                stat_info = os.stat(file_path)
                file_size = stat_info.st_size
                modify_time = datetime.fromtimestamp(stat_info.st_mtime)
                
                print(f"   ✅ 文件存在")
                print(f"   📏 文件大小: {file_size} 字节")
                print(f"   📅 修改时间: {modify_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 尝试读取文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if file_path == 'received_tasks.json':
                        tasks_count = len(data.get('tasks', []))
                        user_info = data.get('user_info', {}).get('user', {}).get('username', '未知')
                        print(f"   📋 包含 {tasks_count} 个任务")
                        print(f"   👤 用户: {user_info}")
                    elif file_path == 'received_data.json':
                        user_info = data.get('user', {}).get('username', '未知')
                        role_info = data.get('selectedRole', {}).get('label', '未知')
                        print(f"   👤 用户: {user_info}")
                        print(f"   🎯 角色: {role_info}")
                        
                except Exception as e:
                    print(f"   ⚠️  无法读取文件内容: {str(e)}")
                
                found_files.append(file_path)
                
            except Exception as e:
                print(f"   ❌ 获取文件信息失败: {str(e)}")
        else:
            print(f"   ⚪ 文件不存在")
    
    # 检查备份文件
    print(f"\n🔍 检查备份文件...")
    current_dir = os.getcwd()
    backup_files = []
    
    try:
        for filename in os.listdir(current_dir):
            if filename.startswith('received_tasks.json.notified_'):
                backup_files.append(filename)
        
        if backup_files:
            print(f"   📦 找到 {len(backup_files)} 个备份文件:")
            for filename in backup_files:
                try:
                    backup_path = os.path.join(current_dir, filename)
                    stat_info = os.stat(backup_path)
                    file_size = stat_info.st_size
                    create_time = datetime.fromtimestamp(stat_info.st_ctime)
                    print(f"     - {filename} ({file_size} 字节, {create_time.strftime('%Y-%m-%d %H:%M:%S')})")
                except:
                    print(f"     - {filename} (无法获取详细信息)")
        else:
            print(f"   ⚪ 没有找到备份文件")
            
    except Exception as e:
        print(f"   ❌ 扫描备份文件时出错: {str(e)}")
    
    return found_files, backup_files

def interactive_cleanup():
    """交互式清理"""
    print("🚀 JSON文件清理工具")
    print("=" * 50)
    
    # 检查文件状态
    found_files, backup_files = check_json_files()
    
    total_files = len(found_files) + len(backup_files)
    
    print(f"\n📊 统计结果:")
    print(f"   主要JSON文件: {len(found_files)} 个")
    print(f"   备份文件: {len(backup_files)} 个")
    print(f"   总计: {total_files} 个")
    
    if total_files == 0:
        print("\n✅ 没有找到需要清理的文件，系统已干净!")
        return
    
    print(f"\n⚠️  发现 {total_files} 个文件需要清理")
    
    # 询问用户是否要清理
    while True:
        choice = input("\n是否要清理这些文件? (y/n): ").strip().lower()
        if choice in ['y', 'yes', '是', '1']:
            print("\n🧹 开始清理...")
            deleted_count, deleted_files = cleanup_json_files(verbose=True)
            
            if deleted_count > 0:
                print(f"\n🎉 清理完成! 共删除了 {deleted_count} 个文件")
            else:
                print(f"\n⚠️  没有删除任何文件")
            break
        elif choice in ['n', 'no', '否', '0']:
            print("\n❌ 用户取消了清理操作")
            break
        else:
            print("❌ 请输入 y 或 n")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--auto', '-a']:
            # 自动清理模式
            print("🤖 自动清理模式")
            deleted_count, deleted_files = cleanup_json_files(verbose=True)
            print(f"\n✅ 自动清理完成，删除了 {deleted_count} 个文件")
            
        elif sys.argv[1] in ['--check', '-c']:
            # 仅检查模式
            print("🔍 检查模式")
            found_files, backup_files = check_json_files()
            total_files = len(found_files) + len(backup_files)
            print(f"\n📊 发现 {total_files} 个文件")
            
        elif sys.argv[1] in ['--help', '-h']:
            # 帮助信息
            print("📖 JSON文件清理工具使用说明")
            print("=" * 40)
            print("python manual_cleanup.py          # 交互式清理")
            print("python manual_cleanup.py --auto   # 自动清理")
            print("python manual_cleanup.py --check  # 仅检查文件")
            print("python manual_cleanup.py --help   # 显示帮助")
            
        else:
            print(f"❌ 未知参数: {sys.argv[1]}")
            print("使用 --help 查看帮助信息")
    else:
        # 交互式模式
        interactive_cleanup()

if __name__ == "__main__":
    main() 