#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
桌面图标备份还原系统测试脚本
用于验证系统各个组件是否正常工作
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from desktop_icon_manager import DesktopIconManager
from enhanced_transition_screen import EnhancedTransitionScreen, create_backup_transition, create_restore_transition

def test_desktop_icon_manager():
    """测试桌面文件管理器"""
    print("=" * 60)
    print("测试桌面文件管理器")
    print("=" * 60)
    
    manager = DesktopIconManager()
    
    print(f"桌面路径: {manager.desktop_path}")
    print(f"备份文件夹: {manager.backup_folder}")
    print(f"备份信息文件: {manager.backup_info_file}")
    
    # 测试扫描桌面文件
    print("\n扫描桌面文件...")
    files = manager.scan_desktop_files()
    print(f"找到 {len(files)} 个文件/文件夹")
    
    for i, file_item in enumerate(files[:5]):  # 只显示前5个
        file_type = file_item.get('type', 'file')
        size_str = f"{file_item['size']} bytes" if file_item['size'] > 0 else "0 bytes"
        print(f"  {i+1}. {file_item['name']} ({file_type}, {file_item['extension']}, {size_str})")
    
    if len(files) > 5:
        print(f"  ... 还有 {len(files) - 5} 个文件/文件夹")
    
    # 检查是否有备份
    has_backup = manager.has_backup()
    print(f"\n当前是否有备份: {'是' if has_backup else '否'}")
    
    if has_backup:
        backup_info = manager.get_backup_info()
        if backup_info:
            backup_time = time.ctime(backup_info.get('backup_time', 0))
            # 兼容新旧版本的备份格式
            file_count = len(backup_info.get('files', backup_info.get('icons', [])))
            print(f"备份时间: {backup_time}")
            print(f"备份文件数量: {file_count}")
    
    return manager, files

def test_enhanced_transition_screen():
    """测试增强过渡界面"""
    print("\n" + "=" * 60)
    print("测试增强过渡界面")
    print("=" * 60)
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    print("创建备份过渡界面...")
    backup_screen = create_backup_transition()
    print("备份过渡界面创建成功")
    
    print("创建还原过渡界面...")
    restore_screen = create_restore_transition()
    print("还原过渡界面创建成功")
    
    return backup_screen, restore_screen

def test_file_permissions():
    """测试文件权限"""
    print("\n" + "=" * 60)
    print("测试文件权限")
    print("=" * 60)
    
    manager = DesktopIconManager()
    
    # 测试创建备份文件夹
    print("测试创建备份文件夹...")
    success = manager.create_backup_folder()
    print(f"创建备份文件夹: {'成功' if success else '失败'}")
    
    # 测试写入权限
    test_file = os.path.join(manager.backup_folder, "test_permissions.txt")
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("权限测试文件")
        print("写入权限: 正常")
        
        # 清理测试文件
        os.remove(test_file)
        print("删除权限: 正常")
    except Exception as e:
        print(f"文件操作权限异常: {str(e)}")
    
    # 测试桌面读取权限
    try:
        desktop_files = os.listdir(manager.desktop_path)
        print(f"桌面读取权限: 正常 (找到 {len(desktop_files)} 个项目)")
    except Exception as e:
        print(f"桌面读取权限异常: {str(e)}")

def test_dependencies():
    """测试依赖项"""
    print("\n" + "=" * 60)
    print("测试依赖项")
    print("=" * 60)
    
    dependencies = [
        ('PyQt5', 'PyQt5'),
        ('os', 'os'),
        ('sys', 'sys'),
        ('shutil', 'shutil'),
        ('json', 'json'),
        ('glob', 'glob'),
        ('subprocess', 'subprocess'),
        ('threading', 'threading'),
        ('time', 'time')
    ]
    
    missing_deps = []
    
    for dep_name, module_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {dep_name}: 已安装")
        except ImportError:
            print(f"✗ {dep_name}: 未安装")
            missing_deps.append(dep_name)
    
    if missing_deps:
        print(f"\n警告: 缺少以下依赖项: {', '.join(missing_deps)}")
        return False
    else:
        print("\n所有依赖项都已安装")
        return True

def test_system_compatibility():
    """测试系统兼容性"""
    print("\n" + "=" * 60)
    print("测试系统兼容性")
    print("=" * 60)
    
    print(f"操作系统: {sys.platform}")
    print(f"Python版本: {sys.version}")
    
    if sys.platform == "win32":
        print("Windows系统兼容性: ✓")
        
        # 测试Windows API
        try:
            import ctypes.wintypes
            print("Windows API支持: ✓")
        except ImportError:
            print("Windows API支持: ✗")
    else:
        print(f"其他系统 ({sys.platform}) 兼容性: ✓")

def run_full_test():
    """运行完整测试"""
    print("桌面文件备份还原系统 - 完整测试")
    print("=" * 80)
    
    # 1. 测试依赖项
    deps_ok = test_dependencies()
    if not deps_ok:
        print("\n测试中止: 依赖项不完整")
        return False
    
    # 2. 测试系统兼容性
    test_system_compatibility()
    
    # 3. 测试文件权限
    test_file_permissions()
    
    # 4. 测试桌面文件管理器
    try:
        manager, files = test_desktop_icon_manager()
        print("✓ 桌面文件管理器测试通过")
    except Exception as e:
        print(f"✗ 桌面文件管理器测试失败: {str(e)}")
        return False
    
    # 5. 测试增强过渡界面
    try:
        backup_screen, restore_screen = test_enhanced_transition_screen()
        print("✓ 增强过渡界面测试通过")
    except Exception as e:
        print(f"✗ 增强过渡界面测试失败: {str(e)}")
        return False
    
    print("\n" + "=" * 80)
    print("所有测试完成")
    print("=" * 80)
    
    return True

def interactive_test():
    """交互式测试"""
    print("桌面文件备份还原系统 - 交互式测试")
    print("=" * 80)
    
    while True:
        print("\n选择测试项目:")
        print("1. 测试桌面文件管理器")
        print("2. 测试增强过渡界面")
        print("3. 测试文件权限")
        print("4. 测试依赖项")
        print("5. 测试系统兼容性")
        print("6. 运行完整测试")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            test_desktop_icon_manager()
        elif choice == '2':
            test_enhanced_transition_screen()
        elif choice == '3':
            test_file_permissions()
        elif choice == '4':
            test_dependencies()
        elif choice == '5':
            test_system_compatibility()
        elif choice == '6':
            run_full_test()
        else:
            print("无效选择，请重试")
    
    print("测试结束")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_test()
    else:
        run_full_test()

if __name__ == "__main__":
    main() 