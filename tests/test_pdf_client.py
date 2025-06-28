#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端PDF预览功能测试脚本
用于测试8800端口的/pdf-preview接口
"""

import requests
import json
import time
import os

def test_pdf_client():
    """测试PDF客户端接收功能"""
    print("🧪 开始测试客户端PDF预览功能")
    print("=" * 50)
    
    # 测试数据 - 无需认证的简化JSON格式
    test_data = {
        "action": "pdf_download_and_preview",
        "data": {
            "filename": "项目任务汇报单子（测试）.pdf",
            "download_url": "http://localhost:8000/api/pdf/download/test.pdf",
            "file_size": 105874,
            "modification_time": time.time(),
            "preview_type": "pdf_document",
            "request_time": time.time(),
            "server_info": {
                "host": "localhost",
                "port": 8000,
                "protocol": "http"
            },
            "requester": {
                "user_id": 1,
                "username": "admin",
                "role": "管理员",
                "type": "管理员"
            }
        },
        "instructions": {
            "action_required": "download_and_open_pdf",
            "download_url": "http://localhost:8000/api/pdf/download/test.pdf",
            "display_mode": "default_viewer",
            "cache_policy": "download_fresh"
        }
    }
    
    # 客户端URL
    client_url = "http://localhost:8800/pdf-preview"
    
    print(f"🎯 目标地址: {client_url}")
    print(f"📋 测试文件: {test_data['data']['filename']}")
    
    try:
        # 首先检查客户端服务是否可用
        print("\n🔍 检查客户端服务状态...")
        status_response = requests.get("http://localhost:8800/status", timeout=5)
        
        if status_response.status_code == 200:
            print("✅ 客户端服务运行正常")
            print(f"📊 状态响应: {status_response.json()}")
        else:
            print(f"⚠️ 客户端服务状态异常: {status_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到客户端服务")
        print("   请确保fullscreen_browser已启动并正在监听8800端口")
        return False
    except Exception as e:
        print(f"❌ 检查服务状态时出错: {str(e)}")
        return False
    
    try:
        print("\n📤 发送PDF预览请求...")
        print(f"📦 请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        
        # 发送PDF预览请求
        response = requests.post(
            client_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\n📨 响应状态码: {response.status_code}")
        print(f"📋 响应内容: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("\n✅ PDF预览请求发送成功！")
            print(f"📊 服务器响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            if response_data.get('status') == 'success':
                print("🎉 客户端已接收PDF预览请求")
                print("📥 客户端将在后台下载并打开PDF文件")
                return True
            else:
                print("❌ 客户端返回错误状态")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"❌ 错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接被拒绝")
        print("   请确保客户端服务正在运行并监听8800端口")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 发送请求时出错: {str(e)}")
        return False

def test_with_real_pdf():
    """测试使用项目中真实的PDF文件"""
    print("\n🔄 测试使用真实PDF文件")
    print("=" * 50)
    
    # 检查项目中的PDF文件
    pdf_path = "resources/documents/Project_Management/项目任务汇报单子(系统分析师).pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF文件不存在: {pdf_path}")
        return False
    
    file_size = os.path.getsize(pdf_path)
    print(f"✅ 找到PDF文件: {pdf_path}")
    print(f"📏 文件大小: {file_size} bytes")
    
    # 构建测试数据（使用文件路径代替URL进行测试，无需认证）
    test_data = {
        "action": "pdf_download_and_preview",
        "data": {
            "filename": "项目任务汇报单子(系统分析师).pdf",
            "download_url": f"file://{os.path.abspath(pdf_path)}",
            "file_size": file_size,
            "modification_time": os.path.getmtime(pdf_path),
            "preview_type": "pdf_document",
            "request_time": time.time(),
            "server_info": {
                "host": "localhost",
                "port": 8000,
                "protocol": "file"
            },
            "requester": {
                "user_id": 1,
                "username": "test_user",
                "role": "系统分析师",
                "type": "test"
            }
        },
        "instructions": {
            "action_required": "download_and_open_pdf",
            "download_url": f"file://{os.path.abspath(pdf_path)}",
            "display_mode": "default_viewer",
            "cache_policy": "download_fresh"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8800/pdf-preview",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📨 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ 真实PDF测试成功！")
            print(f"📊 响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 真实PDF测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 真实PDF测试出错: {str(e)}")
        return False

def test_direct_download():
    """测试直接下载功能（无需认证）"""
    print("\n🔓 测试直接下载功能")
    print("=" * 50)
    
    # 构建直接下载测试数据
    test_data = {
        "action": "pdf_download_and_preview",
        "data": {
            "filename": "项目任务汇报单子（直接下载测试）.pdf",
            "download_url": "http://localhost:8000/api/pdf/download/test.pdf",
            "file_size": 105874,
            "modification_time": time.time(),
            "preview_type": "pdf_document",
            "request_time": time.time(),
            "server_info": {
                "host": "localhost",
                "port": 8000,
                "protocol": "http"
            },
            "requester": {
                "user_id": 1,
                "username": "test_user",
                "role": "测试用户",
                "type": "test"
            }
        },
        "instructions": {
            "action_required": "download_and_open_pdf",
            "download_url": "http://localhost:8000/api/pdf/download/test.pdf",
            "display_mode": "default_viewer",
            "cache_policy": "download_fresh"
        }
    }
    
    try:
        print("📤 发送直接下载测试请求...")
        print("   ✅ 无需认证，应该可以直接下载")
        
        response = requests.post(
            "http://localhost:8800/pdf-preview",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📨 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ 直接下载测试请求发送成功！")
            print("📝 客户端应该能够直接下载PDF文件")
            print(f"📊 响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ 直接下载测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 直接下载测试出错: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 客户端PDF预览功能测试 (无需认证版)")
    print("=" * 60)
    
    # 基础功能测试
    basic_test_result = test_pdf_client()
    
    # 真实文件测试
    real_pdf_test_result = test_with_real_pdf()
    
    # 直接下载测试
    direct_download_test_result = test_direct_download()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   📋 基础功能测试: {'✅ 通过' if basic_test_result else '❌ 失败'}")
    print(f"   📄 真实PDF测试: {'✅ 通过' if real_pdf_test_result else '❌ 失败'}")
    print(f"   🔓 直接下载测试: {'✅ 通过' if direct_download_test_result else '❌ 失败'}")
    
    all_tests_passed = basic_test_result and real_pdf_test_result and direct_download_test_result
    
    if all_tests_passed:
        print("\n🎉 所有测试通过！客户端PDF预览功能工作正常")
    else:
        print("\n❌ 部分测试失败，请检查配置")
        
    print("\n💡 功能说明:")
    print("   ✅ 无需认证：PDF下载已移除认证要求，简化流程")
    print("   ✅ 错误处理：404、403、timeout等错误的详细处理")
    print("   ✅ 重试机制：最多3次重试，递增等待时间")
    print("   ✅ 统计监控：下载成功/失败统计和详细日志")
    print("   ✅ 安全验证：URL和文件类型安全检查")
    print("   ✅ 目录限制：仅允许访问指定目录的PDF文件")
    
    print("\n🛠️ 使用说明:")
    print("   1. 确保fullscreen_browser程序已启动")
    print("   2. 客户端监听8800端口接收PDF预览请求")
    print("   3. 后端发送简化的JSON数据（无需token）")
    print("   4. 客户端直接下载并打开PDF文件")
    print("   5. 查看pdf_client.log获取详细日志")
    
    print("\n🔒 安全措施:")
    print("   • 文件类型限制：仅允许.pdf文件")
    print("   • 目录限制：仅允许访问指定目录")
    print("   • 路径安全：防止目录遍历攻击")
    print("   • 文件名验证：防止特殊字符攻击")

if __name__ == "__main__":
    main() 