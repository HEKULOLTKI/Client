import sys
import os
import json
import subprocess
import requests
import csv
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QLabel, QSystemTrayIcon, QMenu, 
                             QDesktopWidget, QToolButton, QFrame, QSizePolicy,
                             QMessageBox, QDialog, QCheckBox, QScrollArea, 
                             QDialogButtonBox, QLineEdit, QComboBox, QFormLayout,
                             QTextEdit, QFileDialog, QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QFileSystemWatcher, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient
import config
from pet_widget import PetWidget
from chat_widget import ChatWidget
from online_chat_widget import OnlineChatWidget
from transition_screen import TransitionScreen
from openai_api import OpenAIChat
from tuopo_widget import TuopoWidget
import api_config
import logging
import time
from datetime import datetime
import re

# 禁用Flask的默认日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# 数据验证常量
class DataValidation:
    """数据验证常量和方法"""
    
    # 支持的任务状态
    VALID_ASSIGNMENT_STATUSES = [
        "待分配", "未分配", "进行中", "已完成", 
        "暂停", "取消", "pending", "in_progress", 
        "completed", "paused", "cancelled"
    ]
    
    # 支持的优先级
    VALID_PRIORITIES = [
        "high", "normal", "low", "urgent", 
        "高", "中", "低", "紧急"
    ]
    
    # 支持的用户状态
    VALID_USER_STATUSES = [
        "active", "inactive", "locked", "disabled",
        "激活", "未激活", "锁定", "禁用"
    ]
    
    # 支持的时间格式
    TIME_FORMATS = [
        "%Y-%m-%dT%H:%M:%S.%fZ",     # ISO 8601 带毫秒和时区
        "%Y-%m-%dT%H:%M:%SZ",        # ISO 8601 带时区
        "%Y-%m-%dT%H:%M:%S",         # ISO 8601 基本格式
        "%Y-%m-%d %H:%M:%S",         # 标准日期时间格式
    ]
    
    @staticmethod
    def validate_task_assignment_data(data):
        """验证任务分配数据格式"""
        try:
            # 检查顶级必需字段
            required_fields = ['action', 'deployment_info', 'assigned_tasks', 'deployment_summary']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 验证action字段
            if data['action'] != 'task_deployment':
                raise ValueError("action字段值必须为'task_deployment'")
            
            # 验证deployment_info
            deployment_info = data['deployment_info']
            required_deployment_fields = ['target_role', 'deployment_time', 'operator']
            for field in required_deployment_fields:
                if field not in deployment_info:
                    raise ValueError(f"deployment_info缺少字段: {field}")
            
            # 验证operator信息
            operator = deployment_info['operator']
            required_operator_fields = ['user_id', 'username', 'operator_role']
            for field in required_operator_fields:
                if field not in operator:
                    raise ValueError(f"operator缺少字段: {field}")
            
            # 验证user_id是数字类型
            if not isinstance(operator['user_id'], (int, float)):
                raise ValueError("user_id必须是数字类型")
            
            # 验证时间格式
            DataValidation.validate_time_format(deployment_info['deployment_time'])
            
            # 验证任务数组
            if not data['assigned_tasks']:
                raise ValueError("assigned_tasks不能为空")
            
            # 验证每个任务的必需字段
            for i, task in enumerate(data['assigned_tasks']):
                required_task_fields = [
                    'assignment_id', 'assignment_status', 'assigned_at',
                    'task_id', 'task_name', 'task_type'
                ]
                for field in required_task_fields:
                    if field not in task:
                        raise ValueError(f"任务{i}缺少字段: {field}")
                
                # 验证ID字段是数字类型
                for id_field in ['assignment_id', 'task_id']:
                    if not isinstance(task[id_field], (int, float)):
                        raise ValueError(f"任务{i}的{id_field}必须是数字类型")
                
                # 验证状态值
                if task['assignment_status'] not in DataValidation.VALID_ASSIGNMENT_STATUSES:
                    print(f"⚠️ 警告: 任务{i}的状态值'{task['assignment_status']}'不在标准列表中")
                
                # 验证优先级（如果存在）
                if 'priority' in task and task['priority'] not in DataValidation.VALID_PRIORITIES:
                    print(f"⚠️ 警告: 任务{i}的优先级'{task['priority']}'不在标准列表中")
                
                # 验证时间格式
                DataValidation.validate_time_format(task['assigned_at'])
                if 'last_update' in task and task['last_update']:
                    DataValidation.validate_time_format(task['last_update'])
            
            # 验证deployment_summary
            summary = data['deployment_summary']
            required_summary_fields = ['total_assigned_tasks', 'deployment_id', 'data_source']
            for field in required_summary_fields:
                if field not in summary:
                    raise ValueError(f"deployment_summary缺少字段: {field}")
            
            # 验证任务数量一致性
            if summary['total_assigned_tasks'] != len(data['assigned_tasks']):
                print(f"⚠️ 警告: deployment_summary中的任务数量({summary['total_assigned_tasks']})与实际任务数量({len(data['assigned_tasks'])})不一致")
            
            return True
            
        except Exception as e:
            raise ValueError(f"数据验证失败: {str(e)}")
    
    @staticmethod
    def validate_time_format(time_str):
        """验证时间格式"""
        if not time_str:
            return True  # 空时间允许
        
        # 尝试Unix时间戳
        try:
            if isinstance(time_str, (int, float)):
                datetime.fromtimestamp(time_str)
                return True
        except:
            pass
        
        # 尝试各种时间格式
        for fmt in DataValidation.TIME_FORMATS:
            try:
                datetime.strptime(time_str, fmt)
                return True
            except:
                continue
        
        raise ValueError(f"不支持的时间格式: {time_str}")
    
    @staticmethod
    def validate_user_data_sync(data):
        """验证用户数据同步格式"""
        try:
            # 检查顶级必需字段
            required_fields = ['action', 'sync_info', 'users', 'sync_summary']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 验证action字段
            if data['action'] != 'user_data_sync':
                raise ValueError("action字段值必须为'user_data_sync'")
            
            # 验证sync_info
            sync_info = data['sync_info']
            required_sync_fields = ['sync_type', 'sync_time', 'operator']
            for field in required_sync_fields:
                if field not in sync_info:
                    raise ValueError(f"sync_info缺少字段: {field}")
            
            # 验证operator信息
            operator = sync_info['operator']
            required_operator_fields = ['user_id', 'username', 'operator_role']
            for field in required_operator_fields:
                if field not in operator:
                    raise ValueError(f"operator缺少字段: {field}")
            
            # 验证user_id是数字类型
            if not isinstance(operator['user_id'], (int, float)):
                raise ValueError("user_id必须是数字类型")
            
            # 验证时间格式
            DataValidation.validate_time_format(sync_info['sync_time'])
            
            # 验证用户数组
            if not data['users']:
                raise ValueError("users不能为空")
            
            # 验证每个用户的必需字段
            for i, user in enumerate(data['users']):
                required_user_fields = ['id', 'username', 'role', 'type', 'status']
                for field in required_user_fields:
                    if field not in user:
                        raise ValueError(f"用户{i}缺少字段: {field}")
                
                # 验证用户ID是数字类型
                if not isinstance(user['id'], (int, float)):
                    raise ValueError(f"用户{i}的id必须是数字类型")
                
                # 验证用户状态
                status = user.get('status')
                if status and status not in DataValidation.VALID_USER_STATUSES:
                    print(f"⚠️ 警告: 用户{i}的状态值'{status}'不在标准列表中")
                
                # 验证时间格式
                for time_field in ['created_at', 'updated_at']:
                    if time_field in user and user[time_field]:
                        DataValidation.validate_time_format(user[time_field])
            
            # 验证sync_summary
            summary = data['sync_summary']
            required_summary_fields = ['total_users', 'sync_id']
            for field in required_summary_fields:
                if field not in summary:
                    raise ValueError(f"sync_summary缺少字段: {field}")
            
            # 验证用户数量一致性
            if summary['total_users'] != len(data['users']):
                print(f"⚠️ 警告: sync_summary中的用户数量({summary['total_users']})与实际用户数量({len(data['users'])})不一致")
            
            return True
            
        except Exception as e:
            raise ValueError(f"用户数据同步验证失败: {str(e)}")
    
    @staticmethod
    def validate_json_format(data):
        """验证JSON格式"""
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            json.loads(json_str)  # 验证能否正确解析
            return True
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON格式错误: {e}")

class DataProcessor:
    """数据处理器 - 处理不同格式的数据转换"""
    
    @staticmethod
    def detect_data_format(data):
        """检测数据格式"""
        if data.get('action') == 'task_deployment' and 'assigned_tasks' in data:
            return 'task_assignment'
        elif data.get('action') == 'user_data_sync' and 'users' in data:
            return 'user_data_sync'
        elif 'tasks' in data and data['tasks']:
            return 'legacy'
        else:
            return 'unknown'
    
    @staticmethod
    def process_task_assignment_format(data):
        """处理任务分配格式数据"""
        try:
            # 数据验证
            DataValidation.validate_task_assignment_data(data)
            print("✅ 任务分配数据验证通过")
            
            assigned_tasks = data['assigned_tasks']
            deployment_info = data['deployment_info']
            operator = deployment_info.get('operator', {})
            
            print(f"🆕 处理任务分配格式数据:")
            print(f"   📋 任务数量: {len(assigned_tasks)}")
            print(f"   🎯 目标角色: {deployment_info.get('target_role')}")
            print(f"   👤 操作员: {operator.get('username')}")
            
            # 转换任务数据格式
            converted_tasks = []
            for i, task in enumerate(assigned_tasks):
                try:
                    converted_task = DataProcessor.convert_assignment_task(task)
                    converted_tasks.append(converted_task)
                    print(f"   ✅ 任务{i+1}: {converted_task.get('name')} - 状态: {converted_task.get('status')}")
                except Exception as e:
                    print(f"   ❌ 任务{i+1}转换失败: {str(e)}")
                    continue
            
            # 创建用户信息结构
            user_info = DataProcessor.create_user_info_from_deployment(deployment_info, data.get('deployment_summary', {}))
            
            # 创建最终数据结构
            result = {
                'tasks': converted_tasks,
                'user_info': user_info,
                'updated_at': deployment_info.get('deployment_time', ''),
                'data_source': 'task_assignments_table',
                'original_format': 'task_deployment',
                'validation_passed': True,
                'processing_time': datetime.now().isoformat()
            }
            
            print(f"✅ 任务分配数据处理完成，转换了 {len(converted_tasks)} 个任务")
            return result
            
        except Exception as e:
            print(f"❌ 处理任务分配数据失败: {str(e)}")
            raise
    
    @staticmethod
    def convert_assignment_task(task):
        """转换单个任务分配数据"""
        return {
            # 任务基本信息
            'id': task.get('task_id'),
            'name': task.get('task_name', '未命名任务'),
            'task_name': task.get('task_name', '未命名任务'),
            'description': task.get('task_description', ''),
            'type': task.get('task_type', '未知类型'),
            'task_type': task.get('task_type', '未知类型'),
            'phase': task.get('task_phase', ''),
            'task_phase': task.get('task_phase', ''),
            'role_binding': task.get('role_binding', ''),
            
            # 任务分配信息
            'assignment_id': task.get('assignment_id'),
            'status': task.get('assignment_status', '未知状态'),
            'assignment_status': task.get('assignment_status', '未知状态'),
            'progress': task.get('assignment_progress', task.get('completion_percentage', 0)),
            'completion_percentage': task.get('completion_percentage', task.get('assignment_progress', 0)),
            'performance_score': task.get('performance_score', 0),
            'assigned_at': task.get('assigned_at'),
            'last_update': task.get('last_update'),
            'comments': task.get('comments', ''),
            
            # 任务执行参数
            'priority': task.get('priority', 'normal'),
            'estimated_duration': task.get('estimated_duration', ''),
            'requirements': task.get('requirements', []),
            'deliverables': task.get('deliverables', []),
            'execution_status': task.get('execution_status', 'pending'),
            
            # 元数据
            'original_data': task,  # 保留原始数据用于调试
            'converted_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def create_user_info_from_deployment(deployment_info, deployment_summary):
        """从部署信息创建用户信息结构"""
        operator = deployment_info.get('operator', {})
        
        return {
            'user': {
                'id': operator.get('user_id'),
                'username': operator.get('username', '未知用户'),
                'role': operator.get('operator_role', '未知角色'),
                'type': operator.get('operator_type', '操作员')
            },
            'selectedRole': {
                'label': deployment_info.get('target_role', '未知角色'),
                'value': deployment_info.get('target_role', '未知角色'),
                'description': f"当前任务角色：{deployment_info.get('target_role', '未知')}"
            },
            'session': deployment_info.get('session', {}),
            'deployment_info': deployment_info,
            'deployment_summary': deployment_summary,
            'timestamp': deployment_info.get('deployment_time', ''),
            'target_ip': deployment_summary.get('target_ip', ''),
            'deployment_id': deployment_summary.get('deployment_id', '')
        }
    
    @staticmethod
    def process_user_data_sync(data):
        """处理用户数据同步格式"""
        try:
            # 数据验证
            DataValidation.validate_user_data_sync(data)
            print("✅ 用户数据同步验证通过")
            
            users = data['users']
            sync_info = data['sync_info']
            operator = sync_info.get('operator', {})
            
            print(f"🔄 处理用户数据同步:")
            print(f"   👥 用户数量: {len(users)}")
            print(f"   🔄 同步类型: {sync_info.get('sync_type')}")
            print(f"   👤 操作员: {operator.get('username')}")
            
            # 获取当前用户信息（通常是第一个用户）
            current_user = users[0] if users else {}
            
            # 创建用户信息结构
            user_info = DataProcessor.create_user_info_from_sync(sync_info, current_user, data.get('sync_summary', {}))
            
            # 创建最终数据结构（不包含任务，需要通过API获取）
            result = {
                'tasks': [],  # 空任务列表，将通过API获取
                'user_info': user_info,
                'updated_at': sync_info.get('sync_time', ''),
                'data_source': 'user_data_sync',
                'original_format': 'user_data_sync',
                'validation_passed': True,
                'processing_time': datetime.now().isoformat(),
                'needs_api_fetch': True,  # 标记需要通过API获取任务
                'api_user_info': {
                    'user_id': current_user.get('id'),
                    'username': current_user.get('username'),
                    'password': current_user.get('password'),
                    'role': current_user.get('role'),
                    'type': current_user.get('type'),
                    'status': current_user.get('status')
                }
            }
            
            print(f"✅ 用户数据同步处理完成，用户: {current_user.get('username')}")
            return result
            
        except Exception as e:
            print(f"❌ 处理用户数据同步失败: {str(e)}")
            raise
    
    @staticmethod
    def create_user_info_from_sync(sync_info, user_data, sync_summary):
        """从同步信息创建用户信息结构"""
        operator = sync_info.get('operator', {})
        
        return {
            'user': {
                'id': user_data.get('id'),
                'username': user_data.get('username', '未知用户'),
                'role': user_data.get('role', '未知角色'),
                'type': user_data.get('type', '操作员'),
                'status': user_data.get('status', 'active'),
                'email': user_data.get('email'),
                'phone': user_data.get('phone'),
                'department': user_data.get('department'),
                'position': user_data.get('position')
            },
            'selectedRole': {
                'label': user_data.get('role', '未知角色'),
                'value': user_data.get('role', '未知角色'),
                'description': f"当前用户角色：{user_data.get('role', '未知')}"
            },
            'session': sync_info.get('session', {}),
            'sync_info': sync_info,
            'sync_summary': sync_summary,
            'timestamp': sync_info.get('sync_time', ''),
            'sync_id': sync_summary.get('sync_id', ''),
            'sync_type': sync_info.get('sync_type', '')
        }
    
    @staticmethod
    def process_legacy_format(data):
        """处理传统格式数据"""
        try:
            print(f"📜 处理传统格式数据:")
            print(f"   📋 任务数量: {len(data.get('tasks', []))}")
            
            # 创建user_info结构
            user_info = {
                'user': data.get('user', {}),
                'selectedRole': data.get('selectedRole', {}),
                'session': data.get('session', {}),
                'timestamp': data.get('timestamp', '')
            }
            
            # 创建最终数据结构
            result = {
                'tasks': data.get('tasks', []),
                'user_info': user_info,
                'updated_at': data.get('timestamp', ''),
                'data_source': 'legacy_format',
                'original_format': 'legacy',
                'validation_passed': True,
                'processing_time': datetime.now().isoformat()
            }
            
            print(f"✅ 传统格式数据处理完成")
            return result
            
        except Exception as e:
            print(f"❌ 处理传统格式数据失败: {str(e)}")
            raise

class APIClient:
    """API客户端 - 用于从后端API获取任务数据"""
    
    def __init__(self, base_url="http://172.18.122.8:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.access_token = None
    
    def authenticate(self, username, password, user_type=None, operator_type=None):
        """用户认证"""
        try:
            import requests
            
            # 根据operator_type或user_type确定登录类型
            # operator_type优先，因为它更准确地反映了用户的操作员类型
            login_type = operator_type or user_type or '操作员'  # 默认使用"操作员"而不是"password"
            
            # 准备登录数据
            login_data = {
                'login_type': login_type,
                'username': username,
                'password': password,
                'grant_type': 'password'  # grant_type始终为password
            }
            
            # 发送登录请求
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                print(f"✅ API认证成功，用户: {username}")
                return True
            else:
                print(f"❌ API认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ API认证异常: {str(e)}")
            return False
    
    def get_my_tasks(self, status=None):
        """获取当前用户的任务"""
        try:
            import requests
            
            if not self.access_token:
                print("❌ 未认证，无法获取任务")
                return []
            
            # 准备请求头
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # 准备查询参数
            params = {}
            if status:
                params['status'] = status
            
            # 发送请求
            response = requests.get(
                f"{self.base_url}/api/my-tasks",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                tasks = response.json()
                print(f"✅ 成功获取 {len(tasks)} 个任务")
                return tasks
            else:
                print(f"❌ 获取任务失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 获取任务异常: {str(e)}")
            return []
    
    def get_user_task_stats(self, user_id):
        """获取用户任务统计"""
        try:
            import requests
            
            if not self.access_token:
                print("❌ 未认证，无法获取任务统计")
                return {}
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/api/users/{user_id}/task-stats",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ 成功获取用户任务统计")
                return stats
            else:
                print(f"❌ 获取任务统计失败: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ 获取任务统计异常: {str(e)}")
            return {}

class DataReceiver:
    """数据接收器 - 支持多种数据接收方式"""
    
    def __init__(self, desktop_manager=None):
        self.desktop_manager = desktop_manager
        self.http_server = None
        self.websocket_server = None
        self.file_watcher = None
        
    def start_file_watcher(self):
        """启动文件监听器"""
        try:
            if self.file_watcher:
                return
                
            self.file_watcher = QFileSystemWatcher()
            
            # 监听received_data.json文件
            data_file_path = os.path.join(os.getcwd(), "received_data.json")
            if os.path.exists(data_file_path):
                self.file_watcher.addPath(data_file_path)
                print(f"📂 开始监听文件: {data_file_path}")
            
            # 监听工作目录
            self.file_watcher.addPath(os.getcwd())
            
            # 连接信号
            self.file_watcher.fileChanged.connect(self.on_file_changed)
            self.file_watcher.directoryChanged.connect(self.on_directory_changed)
            
            print("✅ 文件监听器启动成功")
            
        except Exception as e:
            print(f"❌ 启动文件监听器失败: {str(e)}")
    
    def on_file_changed(self, file_path):
        """文件变化处理"""
        try:
            print(f"📁 检测到文件变化: {file_path}")
            
            if file_path.endswith("received_data.json"):
                print("🔄 received_data.json 文件已更新，重新加载数据...")
                if self.desktop_manager:
                    # 延迟一点时间确保文件写入完成
                    QTimer.singleShot(1000, self.desktop_manager.load_role_data)
                    QTimer.singleShot(1500, self.desktop_manager.check_and_notify_tasks)
                    
        except Exception as e:
            print(f"❌ 处理文件变化失败: {str(e)}")
    
    def on_directory_changed(self, dir_path):
        """目录变化处理"""
        try:
            # 检查是否有新的received_data.json文件
            data_file_path = os.path.join(dir_path, "received_data.json")
            if os.path.exists(data_file_path):
                if data_file_path not in self.file_watcher.files():
                    self.file_watcher.addPath(data_file_path)
                    print(f"📂 开始监听新文件: {data_file_path}")
                    
                    # 立即处理新文件
                    if self.desktop_manager:
                        QTimer.singleShot(500, self.desktop_manager.load_role_data)
                        QTimer.singleShot(1000, self.desktop_manager.check_and_notify_tasks)
                        
        except Exception as e:
            print(f"❌ 处理目录变化失败: {str(e)}")
    
    def start_http_server(self, port=8080):
        """启动HTTP服务器接收数据"""
        try:
            from flask import Flask, request, jsonify
            from threading import Thread
            
            app = Flask(__name__)
            
            @app.route('/api/receive-data', methods=['POST'])
            def receive_data():
                try:
                    data = request.get_json()
                    if not data:
                        return jsonify({'error': '无效的JSON数据'}), 400
                    
                    print(f"📡 通过HTTP接收到数据")
                    
                    # 保存到文件
                    data_file_path = os.path.join(os.getcwd(), "received_data.json")
                    with open(data_file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ 数据已保存到: {data_file_path}")
                    
                    # 通知桌面管理器
                    if self.desktop_manager:
                        QTimer.singleShot(500, self.desktop_manager.load_role_data)
                        QTimer.singleShot(1000, self.desktop_manager.check_and_notify_tasks)
                    
                    return jsonify({'message': '数据接收成功', 'timestamp': datetime.now().isoformat()})
                    
                except Exception as e:
                    print(f"❌ HTTP数据接收失败: {str(e)}")
                    return jsonify({'error': str(e)}), 500
            
            @app.route('/api/status', methods=['GET'])
            def get_status():
                return jsonify({
                    'status': 'running',
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0'
                })
            
            # 在后台线程中运行服务器
            def run_server():
                app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
            
            server_thread = Thread(target=run_server, daemon=True)
            server_thread.start()
            
            print(f"🌐 HTTP服务器已启动，监听端口: {port}")
            print(f"📡 数据接收端点: http://localhost:{port}/api/receive-data")
            
        except Exception as e:
            print(f"❌ 启动HTTP服务器失败: {str(e)}")
    
    def save_received_data(self, data, source="unknown"):
        """保存接收到的数据"""
        try:
            # 添加接收时间戳和来源信息
            data['_received_at'] = datetime.now().isoformat()
            data['_received_from'] = source
            
            # 保存到received_data.json
            data_file_path = os.path.join(os.getcwd(), "received_data.json")
            with open(data_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 数据已保存 (来源: {source}): {data_file_path}")
            
            # 创建备份
            backup_path = f"{data_file_path}.backup_{int(time.time())}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存接收数据失败: {str(e)}")
            return False
    
    def stop_all_receivers(self):
        """停止所有接收器"""
        try:
            if self.file_watcher:
                self.file_watcher.deleteLater()
                self.file_watcher = None
                print("📂 文件监听器已停止")
            
            # HTTP服务器会在程序退出时自动停止（daemon线程）
            print("🌐 HTTP服务器已停止")
            
        except Exception as e:
            print(f"❌ 停止接收器失败: {str(e)}")

class TaskPreviewDialog(QDialog):
    """任务预览对话框 - 显示选中任务的详细信息"""
    
    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self.tasks = tasks
        self.setup_ui()
        
    def setup_ui(self):
        """设置预览界面"""
        self.setWindowTitle(f"📋 任务预览 - 共 {len(self.tasks)} 个任务")
        self.setFixedSize(900, 700)
        self.setModal(True)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 15px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(15)
        
        # 标题区域
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid rgba(102, 126, 234, 0.2);
                padding: 15px;
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        
        title_icon = QLabel("📋")
        title_icon.setFont(QFont("Segoe UI Emoji", 24))
        title_icon.setStyleSheet("background: transparent; color: #667eea;")
        
        title_text = QLabel(f"任务预览 - 共 {len(self.tasks)} 个任务")
        title_text.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title_text.setStyleSheet("color: #2d3436; background: transparent;")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        layout.addWidget(title_frame)
        
        # 任务统计信息
        self.create_task_statistics(layout)
        
        # 任务详情列表
        self.create_task_details_list(layout)
        
        # 底部按钮
        self.create_preview_buttons(layout)
        
    def create_task_statistics(self, layout):
        """创建任务统计信息"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid rgba(102, 126, 234, 0.2);
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        # 统计各种任务信息
        task_types = {}
        priority_counts = {"high": 0, "normal": 0, "low": 0}
        progress_total = 0
        
        for task in self.tasks:
            # 任务类型统计
            task_type = task.get('type', task.get('task_type', '未知类型'))
            task_types[task_type] = task_types.get(task_type, 0) + 1
            
            # 优先级统计
            priority = task.get('priority', 'normal').lower()
            if priority in ['high', '高', 'urgent', '紧急']:
                priority_counts["high"] += 1
            elif priority in ['low', '低']:
                priority_counts["low"] += 1
            else:
                priority_counts["normal"] += 1
            
            # 进度统计
            progress = task.get('progress', task.get('completion_percentage', 0))
            progress_total += progress
        
        avg_progress = progress_total / len(self.tasks) if self.tasks else 0
        
        # 任务数量
        count_label = QLabel(f"📊 任务总数：{len(self.tasks)}")
        count_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        count_label.setStyleSheet("""
            QLabel {
                color: #667eea;
                background: rgba(102, 126, 234, 0.1);
                padding: 8px 12px;
                border-radius: 8px;
            }
        """)
        
        # 平均进度
        progress_label = QLabel(f"📈 平均进度：{avg_progress:.1f}%")
        progress_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        progress_label.setStyleSheet("""
            QLabel {
                color: #00b894;
                background: rgba(0, 184, 148, 0.1);
                padding: 8px 12px;
                border-radius: 8px;
            }
        """)
        
        # 优先级分布
        priority_label = QLabel(f"⭐ 高优先级：{priority_counts['high']} 个")
        priority_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        priority_label.setStyleSheet("""
            QLabel {
                color: #e17055;
                background: rgba(225, 112, 85, 0.1);
                padding: 8px 12px;
                border-radius: 8px;
            }
        """)
        
        stats_layout.addWidget(count_label)
        stats_layout.addWidget(progress_label)
        stats_layout.addWidget(priority_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
        
    def create_task_details_list(self, layout):
        """创建任务详情列表"""
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                border-radius: 12px;
                background-color: white;
                padding: 5px;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a6fd8;
            }
        """)
        
        # 任务详情容器
        details_widget = QWidget()
        details_widget.setStyleSheet("background: transparent;")
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(10)
        
        # 为每个任务创建详情卡片
        for i, task in enumerate(self.tasks, 1):
            self.create_task_detail_card(details_layout, task, i)
        
        details_layout.addStretch()
        scroll_area.setWidget(details_widget)
        layout.addWidget(scroll_area)
        
    def create_task_detail_card(self, layout, task, index):
        """创建单个任务的详情卡片"""
        card_frame = QFrame()
        card_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fafbfc);
                border: 2px solid rgba(102, 126, 234, 0.1);
                border-radius: 12px;
                margin: 5px;
                padding: 15px;
            }
            QFrame:hover {
                border-color: #667eea;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9ff, stop:1 #f0f2ff);
            }
        """)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(10)
        
        # 任务标题行
        title_layout = QHBoxLayout()
        
        # 序号和任务名称
        task_name = task.get('name', task.get('task_name', '未命名任务'))
        title_label = QLabel(f"{index}. {task_name}")
        title_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2d3436; background: transparent;")
        
        # 任务状态
        status = task.get('status', task.get('assignment_status', '未知状态'))
        status_label = QLabel(f"📌 {status}")
        status_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        status_color = "#00b894" if status == "进行中" else "#fdcb6e" if status == "待开始" else "#74b9ff"
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                background: rgba({int(status_color[1:3], 16)}, {int(status_color[3:5], 16)}, {int(status_color[5:7], 16)}, 0.1);
                padding: 4px 8px;
                border-radius: 6px;
            }}
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(status_label)
        
        card_layout.addLayout(title_layout)
        
        # 任务详细信息
        info_layout = QGridLayout()
        info_layout.setSpacing(8)
        
        # 任务信息字段
        info_fields = [
            ("🔧 任务类型", task.get('type', task.get('task_type', '未知类型'))),
            ("📍 任务阶段", task.get('phase', task.get('task_phase', '未知阶段'))),
            ("⭐ 优先级", task.get('priority', 'normal')),
            ("📊 完成进度", f"{task.get('progress', task.get('completion_percentage', 0))}%"),
            ("🆔 分配ID", str(task.get('assignment_id', '无'))),
            ("⏰ 分配时间", task.get('assigned_at', '未知')),
            ("🎯 角色绑定", task.get('role_binding', '无')),
            ("⏱️ 预计时长", task.get('estimated_duration', '未知'))
        ]
        
        row = 0
        for label_text, value in info_fields:
            if value and value != '无' and value != '未知':
                label = QLabel(label_text)
                label.setFont(QFont("微软雅黑", 9))
                label.setStyleSheet("color: #6c757d; background: transparent;")
                
                value_label = QLabel(str(value))
                value_label.setFont(QFont("微软雅黑", 9, QFont.Bold))
                value_label.setStyleSheet("color: #495057; background: transparent;")
                
                info_layout.addWidget(label, row, 0)
                info_layout.addWidget(value_label, row, 1)
                row += 1
        
        card_layout.addLayout(info_layout)
        
        # 任务描述（如果有）
        description = task.get('description', task.get('task_description', ''))
        if description:
            desc_label = QLabel("📝 任务描述:")
            desc_label.setFont(QFont("微软雅黑", 9))
            desc_label.setStyleSheet("color: #6c757d; background: transparent; margin-top: 5px;")
            
            desc_content = QLabel(description)
            desc_content.setFont(QFont("微软雅黑", 9))
            desc_content.setStyleSheet("""
                QLabel {
                    color: #495057;
                    background: rgba(102, 126, 234, 0.05);
                    padding: 8px;
                    border-radius: 6px;
                    border-left: 3px solid #667eea;
                }
            """)
            desc_content.setWordWrap(True)
            
            card_layout.addWidget(desc_label)
            card_layout.addWidget(desc_content)
        
        layout.addWidget(card_frame)
        
    def create_preview_buttons(self, layout):
        """创建预览对话框底部按钮"""
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid rgba(102, 126, 234, 0.1);
                padding: 15px;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(20, 15, 20, 15)
        buttons_layout.setSpacing(15)
        
        # 导出按钮
        export_btn = QPushButton("📤 导出详情")
        export_btn.setFixedSize(120, 40)
        export_btn.setToolTip("导出任务详情到文件")
        export_btn.clicked.connect(self.export_task_details)
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0984e3, stop:1 #0770c4);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(116, 185, 255, 0.4);
            }
        """)
        buttons_layout.addWidget(export_btn)
        
        buttons_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("✅ 确定")
        close_btn.setFixedSize(100, 40)
        close_btn.setToolTip("关闭预览对话框")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00b894, stop:1 #00a085);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00a085, stop:1 #008f72);
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(0, 184, 148, 0.4);
            }
        """)
        buttons_layout.addWidget(close_btn)
        
        layout.addWidget(buttons_frame)
        
    def export_task_details(self):
        """导出任务详情到文件"""
        try:
            import json
            from datetime import datetime
            
            # 准备导出数据
            export_data = {
                "export_time": datetime.now().isoformat(),
                "task_count": len(self.tasks),
                "tasks": []
            }
            
            for task in self.tasks:
                task_data = {
                    "task_name": task.get('name', task.get('task_name', '未命名任务')),
                    "task_type": task.get('type', task.get('task_type', '未知类型')),
                    "task_phase": task.get('phase', task.get('task_phase', '未知阶段')),
                    "status": task.get('status', task.get('assignment_status', '未知状态')),
                    "priority": task.get('priority', 'normal'),
                    "progress": task.get('progress', task.get('completion_percentage', 0)),
                    "assignment_id": task.get('assignment_id'),
                    "assigned_at": task.get('assigned_at'),
                    "role_binding": task.get('role_binding'),
                    "estimated_duration": task.get('estimated_duration'),
                    "description": task.get('description', task.get('task_description', ''))
                }
                export_data["tasks"].append(task_data)
            
            # 保存到文件
            filename = f"task_preview_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "导出成功", f"任务详情已导出到文件：\n{filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出任务详情时出错：\n{str(e)}")


class TaskSelectionDialog(QDialog):
    """任务选择对话框"""
    
    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self.tasks = tasks
        self.selected_tasks = []
        self.task_checkboxes = {}
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("📋 任务提交管理")
        self.setFixedSize(800, 650)
        self.setModal(True)
        
        # 隐藏标题栏控制按钮
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        # 设置对话框背景样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 15px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(15)
        
        # 创建任务列表区域
        self.create_task_list_section(layout)
        
        # 创建底部按钮区域
        self.create_bottom_buttons_section(layout)
        

    def create_task_list_section(self, layout):
        """创建任务列表区域"""
        # 任务统计信息
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                border: 1px solid rgba(102, 126, 234, 0.2);
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 15, 20, 15)
        
        # 任务统计标签 - 使用统一的筛选条件
        pending_status_list = [api_config.TASK_STATUS.get("PENDING", "待分配"), "未分配", "进行中"]
        pending_tasks = [task for task in self.tasks if task.get('status') in pending_status_list]
        total_label = QLabel(f"📊 总任务数：{len(self.tasks)}")
        pending_label = QLabel(f"⏳ 待提交：{len(pending_tasks)}")
        
        for label in [total_label, pending_label]:
            label.setFont(QFont("微软雅黑", 10, QFont.Bold))
            label.setStyleSheet("""
                QLabel {
                    color: #495057;
                    background: transparent;
                    padding: 5px 10px;
                    border-radius: 5px;
                    background: #f8f9fa;
                }
            """)
        
        stats_layout.addWidget(total_label)
        stats_layout.addWidget(pending_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_frame)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                border-radius: 12px;
                background-color: white;
                padding: 5px;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #667eea;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a6fd8;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 任务列表容器
        tasks_widget = QWidget()
        tasks_widget.setStyleSheet("background: transparent;")
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(10, 10, 10, 10)
        tasks_layout.setSpacing(8)
        
        # 添加任务复选框 - 使用统一的筛选条件
        pending_count = 0
        for task in self.tasks:
            if task.get('status') in pending_status_list:
                self.create_task_item(tasks_layout, task)
                pending_count += 1
        
        if pending_count == 0:
            # 如果没有待提交的任务
            empty_frame = QFrame()
            empty_frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #fff5f5, stop:1 #ffe6e6);
                    border: 2px dashed #ff7675;
                    border-radius: 12px;
                    padding: 40px;
                    margin: 20px;
                }
            """)
            empty_layout = QVBoxLayout(empty_frame)
            
            empty_icon = QLabel("📭")
            empty_icon.setFont(QFont("Segoe UI Emoji", 48))
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_icon.setStyleSheet("background: transparent; color: #ff7675;")
            
            no_tasks_label = QLabel("暂无可提交的任务")
            no_tasks_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
            no_tasks_label.setAlignment(Qt.AlignCenter)
            no_tasks_label.setStyleSheet("color: #636e72; background: transparent; margin-top: 10px;")
            
            hint_label = QLabel("所有任务都已完成或正在进行中")
            hint_label.setFont(QFont("微软雅黑", 10))
            hint_label.setAlignment(Qt.AlignCenter)
            hint_label.setStyleSheet("color: #b2bec3; background: transparent; margin-top: 5px;")
            
            empty_layout.addWidget(empty_icon)
            empty_layout.addWidget(no_tasks_label)
            empty_layout.addWidget(hint_label)
            
            tasks_layout.addWidget(empty_frame)
        
        tasks_layout.addStretch()
        scroll_area.setWidget(tasks_widget)
        layout.addWidget(scroll_area)
        
    def create_bottom_buttons_section(self, layout):
        """创建底部按钮区域 - 完善版本"""
        # 单行按钮区域
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid rgba(102, 126, 234, 0.1);
                padding: 15px;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(20, 15, 20, 15)
        buttons_layout.setSpacing(15)
        
        # 智能选择选项组
        smart_select_group = QWidget()
        smart_layout = QHBoxLayout(smart_select_group)
        smart_layout.setContentsMargins(0, 0, 0, 0)
        smart_layout.setSpacing(10)
        
        # 全选按钮
        select_all_btn = QPushButton("✅ 全选")
        select_all_btn.setFixedSize(100, 40)
        select_all_btn.setToolTip("选择所有待提交的任务")
        select_all_btn.clicked.connect(self.select_all_tasks)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0984e3, stop:1 #0770c4);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(116, 185, 255, 0.4);
            }
            QPushButton:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 6px rgba(116, 185, 255, 0.3);
            }
        """)
        smart_layout.addWidget(select_all_btn)
        

        
        buttons_layout.addWidget(smart_select_group)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: rgba(102, 126, 234, 0.3); }")
        buttons_layout.addWidget(separator)
        
        # 选中数量指示器
        self.selected_count_label = QLabel("📋 未选中任务")
        self.selected_count_label.setFont(QFont("微软雅黑", 10, QFont.Bold))
        self.selected_count_label.setStyleSheet("""
            QLabel {
                color: #667eea;
                background: rgba(102, 126, 234, 0.1);
                padding: 8px 12px;
                border-radius: 8px;
                min-width: 120px;
            }
        """)
        buttons_layout.addWidget(self.selected_count_label)
        
        # 弹性空间
        buttons_layout.addStretch()
        
        # 操作按钮组
        action_group = QWidget()
        action_layout = QHBoxLayout(action_group)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(10)
        
        # 取消按钮
        cancel_btn = QPushButton("🚫 取消")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setToolTip("取消任务选择，返回上一级")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: #f8f9fa;
                border-color: #adb5bd;
                color: #495057;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(108, 117, 125, 0.15);
            }
            QPushButton:pressed {
                background: #e9ecef;
                transform: translateY(0px);
                box-shadow: 0 2px 4px rgba(108, 117, 125, 0.1);
            }
        """)
        action_layout.addWidget(cancel_btn)
        
        # 提交按钮
        submit_btn = QPushButton("🚀 提交选中任务")
        submit_btn.setFixedSize(140, 40)
        submit_btn.setToolTip("提交所选任务到服务器")
        submit_btn.clicked.connect(self.accept_selection)
        submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00b894, stop:1 #00a085);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00a085, stop:1 #008f72);
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(0, 184, 148, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #008f72, stop:1 #007d63);
                transform: translateY(0px);
                box-shadow: 0 2px 8px rgba(0, 184, 148, 0.3);
            }
        """)
        action_layout.addWidget(submit_btn)
        
        buttons_layout.addWidget(action_group)
        
        layout.addWidget(buttons_frame)
        
        # 连接复选框变化事件来更新选中数量
        self.update_selected_count()
        

        

        

        

    def create_task_item(self, layout, task):
        """创建任务项"""
        # 创建任务框架
        task_frame = QFrame()
        task_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fafbfc);
                border: 2px solid rgba(102, 126, 234, 0.1);
                border-radius: 12px;
                margin: 3px;
                padding: 8px;
            }
            QFrame:hover {
                border-color: #667eea;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9ff, stop:1 #f0f2ff);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
            }
        """)
        
        task_layout = QHBoxLayout(task_frame)
        task_layout.setContentsMargins(15, 12, 15, 12)
        task_layout.setSpacing(15)
        
        # 复选框
        checkbox = QCheckBox()
        checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #667eea;
                background-color: #f8f9ff;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #667eea;
                border-radius: 6px;
                background-color: #667eea;
                image: url(data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #5a6fd8;
                border-color: #5a6fd8;
            }
        """)
        task_layout.addWidget(checkbox)
        
        # 任务图标
        task_icon = QLabel("📋")
        task_icon.setFont(QFont("Segoe UI Emoji", 16))
        task_icon.setStyleSheet("background: transparent; color: #667eea;")
        task_layout.addWidget(task_icon)
        
        # 任务信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        
        # 任务名称 - 支持两种字段名格式
        task_name = task.get('name', task.get('task_name', '未命名任务'))
        name_label = QLabel(task_name)
        name_label.setFont(QFont("微软雅黑", 12, QFont.Bold))
        name_label.setStyleSheet("""
            QLabel {
                color: #2d3436;
                background: transparent;
            }
        """)
        info_layout.addWidget(name_label)
        
        # 任务详情
        details_layout = QHBoxLayout()
        details_layout.setSpacing(12)
        
        # 任务类型 - 支持两种字段名格式
        task_type = task.get('type', task.get('task_type', ''))
        if task_type:
            type_label = QLabel(f"🏷️ {task_type}")
            type_label.setFont(QFont("微软雅黑", 9))
            type_label.setStyleSheet("""
                QLabel {
                    color: #74b9ff;
                    background: rgba(116, 185, 255, 0.1);
                    border-radius: 8px;
                    padding: 2px 8px;
                }
            """)
            details_layout.addWidget(type_label)
        
        # 任务阶段 - 支持两种字段名格式
        task_phase = task.get('phase', task.get('task_phase', ''))
        if task_phase:
            phase_label = QLabel(f"📍 {task_phase}")
            phase_label.setFont(QFont("微软雅黑", 9))
            phase_label.setStyleSheet("""
                QLabel {
                    color: #fd79a8;
                    background: rgba(253, 121, 168, 0.1);
                    border-radius: 8px;
                    padding: 2px 8px;
                }
            """)
            details_layout.addWidget(phase_label)
        
        # 进度
        progress = task.get('progress', 0)
        progress_label = QLabel(f"📊 {progress}%")
        progress_label.setFont(QFont("微软雅黑", 9))
        progress_color = "#00b894" if progress >= 80 else "#fdcb6e" if progress >= 50 else "#e17055"
        progress_label.setStyleSheet(f"""
            QLabel {{
                color: {progress_color};
                background: rgba({int(progress_color[1:3], 16)}, {int(progress_color[3:5], 16)}, {int(progress_color[5:7], 16)}, 0.1);
                border-radius: 8px;
                padding: 2px 8px;
            }}
        """)
        details_layout.addWidget(progress_label)
        
        details_layout.addStretch()
        info_layout.addLayout(details_layout)
        
        task_layout.addLayout(info_layout)
        task_layout.addStretch()
        
        # 优先级指示器
        priority_indicator = QLabel("⭐")
        priority_indicator.setFont(QFont("Segoe UI Emoji", 12))
        priority_indicator.setStyleSheet("background: transparent; color: #fdcb6e;")
        task_layout.addWidget(priority_indicator)
        
        # 保存复选框引用 - 支持多种ID字段格式
        task_id = task.get('id') or task.get('task_id') or task.get('assignment_id', f"task_{len(self.task_checkboxes)}")
        self.task_checkboxes[task_id] = checkbox
        
        # 连接复选框变化事件
        checkbox.stateChanged.connect(self.update_selected_count)
        
        layout.addWidget(task_frame)
        
    def select_all_tasks(self):
        """全选任务"""
        for checkbox in self.task_checkboxes.values():
            checkbox.setChecked(True)
        self.update_selected_count()
            

        
    def update_selected_count(self):
        """更新选中任务数量"""
        if not hasattr(self, 'selected_count_label'):
            return
            
        selected_count = sum(1 for checkbox in self.task_checkboxes.values() if checkbox.isChecked())
        total_count = len(self.task_checkboxes)
        
        if selected_count == 0:
            self.selected_count_label.setText("📋 未选中任务")
            self.selected_count_label.setStyleSheet("""
                QLabel {
                    color: #b2bec3;
                    background: rgba(178, 190, 195, 0.1);
                    padding: 8px 15px;
                    border-radius: 8px;
                }
            """)
        elif selected_count == total_count:
            self.selected_count_label.setText(f"✅ 已全选 {selected_count} 个任务")
            self.selected_count_label.setStyleSheet("""
                QLabel {
                    color: #00b894;
                    background: rgba(0, 184, 148, 0.1);
                    padding: 8px 15px;
                    border-radius: 8px;
                }
            """)
        else:
            self.selected_count_label.setText(f"📊 已选中 {selected_count}/{total_count} 个任务")
            self.selected_count_label.setStyleSheet("""
                QLabel {
                    color: #667eea;
                    background: rgba(102, 126, 234, 0.1);
                    padding: 8px 15px;
                    border-radius: 8px;
                }
            """)
            
    def accept_selection(self):
        """确认选择"""
        self.selected_tasks = []
        for task_id, checkbox in self.task_checkboxes.items():
            if checkbox.isChecked():
                # 找到对应的任务
                for task in self.tasks:
                    if task['id'] == task_id:
                        self.selected_tasks.append(task)
                        break
        
        if not self.selected_tasks:
            QMessageBox.warning(self, "提示", "请至少选择一个任务进行提交！")
            return
            
        self.accept()
        
    def get_selected_tasks(self):
        """获取选中的任务"""
        return self.selected_tasks


class TaskSubmissionWorker(QThread):
    """任务提交工作线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(str)  # 进度更新信号
    task_completed = pyqtSignal(str)    # 任务完成信号
    error_occurred = pyqtSignal(str)    # 错误信号
    
    def __init__(self, selected_tasks=None, api_base_url=None):
        super().__init__()
        self.selected_tasks = selected_tasks or []
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """执行任务提交流程"""
        try:
            # 步骤1：获取访问令牌
            self.progress_updated.emit("正在获取访问令牌...")
            if not self.authenticate():
                # 刷新配置以获取最新的认证信息
                api_config.refresh_all_config()
                error_msg = f"认证失败，请检查配置信息：\n用户名: {api_config.DEFAULT_USERNAME}\n登录类型: {api_config.DEFAULT_LOGIN_TYPE}\n请确保用户类型与登录类型匹配"
                self.error_occurred.emit(error_msg)
                return
            
            # 步骤2：提交选中的任务
            if not self.selected_tasks:
                self.task_completed.emit("没有选择要提交的任务")
                return
                
            self.progress_updated.emit(f"开始提交 {len(self.selected_tasks)} 个任务...")
            submitted_count = 0
            
            for i, task in enumerate(self.selected_tasks, 1):
                self.progress_updated.emit(f"正在提交任务 {i}/{len(self.selected_tasks)}: {task.get('task_name', '未命名任务')}")
                
                if self.submit_task(task['id']):
                    submitted_count += 1
                    self.progress_updated.emit(f"✓ 已提交任务: {task.get('task_name', '未命名任务')}")
                else:
                    self.progress_updated.emit(f"✗ 提交失败: {task.get('task_name', '未命名任务')}")
                        
            self.task_completed.emit(f"任务提交完成！成功提交 {submitted_count}/{len(self.selected_tasks)} 个任务")
            
        except Exception as e:
            self.error_occurred.emit(f"任务提交失败: {str(e)}")
            
    def authenticate(self):
        """用户认证"""
        try:
            # 使用配置文件中的认证信息
            auth_data = {
                "login_type": api_config.DEFAULT_LOGIN_TYPE,
                "username": api_config.DEFAULT_USERNAME,
                "password": api_config.DEFAULT_PASSWORD,
                "grant_type": "password"
            }
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['login']}",
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return True
            else:
                print(f"认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"认证异常: {str(e)}")
            return False
            
    def get_my_tasks(self):
        """获取当前用户的任务"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['my_tasks']}",
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取任务失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"获取任务异常: {str(e)}")
            return []
            
    def submit_task(self, assignment_id):
        """提交单个任务"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 更新任务状态为"已完成"，进度为100%
            update_data = {
                "status": api_config.TASK_STATUS["COMPLETED"],
                "progress": 100,
                "comments": "通过桌面管理器选择提交完成"
            }
            
            response = requests.put(
                f"{self.api_base_url}/api/my-tasks/{assignment_id}",
                json=update_data,
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"提交任务失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"提交任务异常: {str(e)}")
            return False


class TaskListWorker(QThread):
    """获取任务列表的工作线程"""
    
    # 定义信号
    tasks_loaded = pyqtSignal(list)  # 任务加载完成信号
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, api_base_url=None):
        super().__init__()
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """获取任务列表"""
        try:
            # 认证
            if not self.authenticate():
                # 刷新配置以获取最新的认证信息
                api_config.refresh_all_config()
                error_msg = f"认证失败，请检查配置信息：\n用户名: {api_config.DEFAULT_USERNAME}\n登录类型: {api_config.DEFAULT_LOGIN_TYPE}\n请确保用户类型与登录类型匹配"
                self.error_occurred.emit(error_msg)
                return
            
            # 获取任务列表
            tasks = self.get_my_tasks()
            self.tasks_loaded.emit(tasks)
            
        except Exception as e:
            self.error_occurred.emit(f"获取任务列表失败: {str(e)}")
            
    def authenticate(self):
        """用户认证"""
        try:
            auth_data = {
                "login_type": api_config.DEFAULT_LOGIN_TYPE,
                "username": api_config.DEFAULT_USERNAME,
                "password": api_config.DEFAULT_PASSWORD,
                "grant_type": "password"
            }
            
            print(f"🔐 TaskListWorker认证: {auth_data['username']} / {auth_data['login_type']}")
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['login']}",
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                print(f"✅ TaskListWorker认证成功")
                return True
            else:
                print(f"❌ TaskListWorker认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ TaskListWorker认证异常: {str(e)}")
            return False
            
    def get_my_tasks(self):
        """获取当前用户的任务"""
        try:
            if not self.access_token:
                print("❌ TaskListWorker: 未认证，无法获取任务")
                return []
                
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            print(f"📋 TaskListWorker: 正在获取任务列表...")
            
            response = requests.get(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['my_tasks']}",
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                tasks = response.json()
                print(f"✅ TaskListWorker: 成功获取 {len(tasks)} 个任务")
                return tasks
            else:
                print(f"❌ TaskListWorker: 获取任务失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ TaskListWorker: 获取任务异常: {str(e)}")
            return []


class DeviceAddDialog(QDialog):
    """设备添加对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_data = {}
        self.batch_devices = []  # 批量设备数据
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("设备管理")
        self.setFixedSize(900, 700)
        self.setModal(True)
        
        # 隐藏标题栏控制按钮（最小化、最大化、关闭按钮）
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        # 设置对话框背景样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 10px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(15)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 10px;
                background: white;
            }
            QTabBar::tab {
                background: #e9ecef;
                color: #495057;
                padding: 15px 25px;
                margin-right: 5px;
                border-radius: 8px 8px 0 0;
                font-size: 14px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QTabBar::tab:selected {
                background: #667eea;
                color: white;
            }
            QTabBar::tab:hover {
                background: #adb5bd;
                color: white;
            }
        """)
        
        # 单个添加标签页
        self.single_tab = QWidget()
        self.setup_single_device_tab()
        self.tab_widget.addTab(self.single_tab, "🏷️ 单个添加")
        
        # 批量导入标签页
        self.batch_tab = QWidget()
        self.setup_batch_import_tab()
        self.tab_widget.addTab(self.batch_tab, "📋 批量导入")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮区域
        self.create_bottom_buttons(layout)
        
    def setup_single_device_tab(self):
        """设置单个设备添加标签页"""
        layout = QVBoxLayout(self.single_tab)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 表单容器
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(30, 25, 30, 25)
        form_layout.setVerticalSpacing(25)
        form_layout.setHorizontalSpacing(20)
        
        # 通用输入框样式
        input_style = """
            QLineEdit {
                padding: 15px 18px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 16px;
                font-family: '微软雅黑';
                background-color: #ffffff;
                color: #495057;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background-color: #f8f9ff;
            }
            QLineEdit:hover {
                border-color: #adb5bd;
            }
        """
        
        # 标签样式
        label_style = """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #495057;
                font-family: '微软雅黑';
            }
        """
        
        # 设备名称（必填）
        name_label = QLabel("设备名称*")
        name_label.setStyleSheet(label_style)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入添加设备的名称")
        self.name_edit.setStyleSheet(input_style)
        form_layout.addRow(name_label, self.name_edit)
        
        # 设备类型
        type_label = QLabel("设备类型")
        type_label.setStyleSheet(label_style)
        self.type_edit = QLineEdit()
        self.type_edit.setPlaceholderText("请输入设备类型，例如：路由器、交换机、防火墙等")
        self.type_edit.setStyleSheet(input_style)
        form_layout.addRow(type_label, self.type_edit)
        
        # IP地址
        ip_label = QLabel("IP地址")
        ip_label.setStyleSheet(label_style)
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("请输入IP地址，例如：192.168.1.100")
        self.ip_edit.setStyleSheet(input_style)
        form_layout.addRow(ip_label, self.ip_edit)
        
        # 设备位置
        location_label = QLabel("设备位置")
        location_label.setStyleSheet(label_style)
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("请输入设备位置，例如：机房A-机柜01-U10")
        self.location_edit.setStyleSheet(input_style)
        form_layout.addRow(location_label, self.location_edit)
        
        # 设备状态
        status_label = QLabel("设备状态")
        status_label.setStyleSheet(label_style)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["offline", "online", "maintenance"])
        self.status_combo.setCurrentText("offline")
        self.status_combo.setStyleSheet("""
            QComboBox {
                padding: 15px 18px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 16px;
                font-family: '微软雅黑';
                background-color: #ffffff;
                color: #495057;
                selection-background-color: #667eea;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #667eea;
                background-color: #f8f9ff;
            }
            QComboBox:hover {
                border-color: #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #667eea;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                font-size: 16px;
                font-family: '微软雅黑';
                selection-background-color: #667eea;
            }
        """)
        form_layout.addRow(status_label, self.status_combo)
        
        layout.addWidget(form_frame)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        # 清空表单按钮
        clear_btn = QPushButton("🗑️ 清空表单")
        clear_btn.setFixedSize(130, 45)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: #e9ecef;
                border-color: #adb5bd;
                color: #495057;
            }
        """)
        clear_btn.clicked.connect(self.clear_single_form)
        
        # 添加并继续按钮
        add_continue_btn = QPushButton("➕ 添加并继续")
        add_continue_btn.setFixedSize(150, 45)
        add_continue_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #28a745, stop:1 #20c997);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #218838, stop:1 #1ea087);
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
            }
        """)
        add_continue_btn.clicked.connect(self.add_device_and_continue)
        
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(add_continue_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
    def setup_batch_import_tab(self):
        """设置批量导入标签页"""
        layout = QVBoxLayout(self.batch_tab)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 顶部操作区域
        top_frame = QFrame()
        top_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
        """)
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 20, 20, 20)
        top_layout.setSpacing(15)
        
        # 说明文字
        info_label = QLabel("批量导入设备信息，支持Excel(.xlsx)和CSV(.csv)格式文件")
        info_label.setFont(QFont("微软雅黑", 12))
        info_label.setStyleSheet("color: #495057; font-weight: bold;")
        top_layout.addWidget(info_label)
        
        # 操作按钮行
        operation_layout = QHBoxLayout()
        
        # 下载模板按钮
        download_template_btn = QPushButton("📥 下载导入模板")
        download_template_btn.setFixedSize(150, 40)
        download_template_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
            }
        """)
        download_template_btn.clicked.connect(self.download_template)
        
        # 选择文件按钮
        select_file_btn = QPushButton("📁 选择导入文件")
        select_file_btn.setFixedSize(150, 40)
        select_file_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6f42c1, stop:1 #5a32a3);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a32a3, stop:1 #4c2a85);
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(111, 66, 193, 0.3);
            }
        """)
        select_file_btn.clicked.connect(self.select_import_file)
        
        # 导入批量设备按钮
        import_devices_btn = QPushButton("🚀 导入批量设备")
        import_devices_btn.setFixedSize(150, 40)
        import_devices_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fd7e14, stop:1 #e55100);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e55100, stop:1 #d84315);
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(253, 126, 20, 0.3);
            }
        """)
        import_devices_btn.clicked.connect(self.import_batch_devices)
        
        operation_layout.addWidget(download_template_btn)
        operation_layout.addWidget(select_file_btn)
        operation_layout.addWidget(import_devices_btn)
        operation_layout.addStretch()
        
        top_layout.addLayout(operation_layout)
        
        # 文件路径显示
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                font-family: '微软雅黑';
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
                border: 1px solid #dee2e6;
            }
        """)
        top_layout.addWidget(self.file_path_label)
        
        layout.addWidget(top_frame)
        
        # 预览表格
        self.preview_table = QTableWidget()
        self.preview_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #667eea;
                color: white;
            }
            QHeaderView::section {
                background-color: #495057;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                font-size: 12px;
                font-family: '微软雅黑';
            }
        """)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.preview_table)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
    def create_bottom_buttons(self, layout):
        """创建底部按钮"""
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 20, 0, 10)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(130, 55)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: '微软雅黑';
            }
            QPushButton:hover {
                background: #f8f9fa;
                border-color: #adb5bd;
                color: #495057;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(108, 117, 125, 0.15);
            }
            QPushButton:pressed {
                background: #e9ecef;
                transform: translateY(0px);
                box-shadow: 0 2px 4px rgba(108, 117, 125, 0.1);
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addWidget(button_frame)
        
    def clear_single_form(self):
        """清空单个设备表单"""
        self.name_edit.clear()
        self.type_edit.clear()
        self.ip_edit.clear()
        self.location_edit.clear()
        self.status_combo.setCurrentText("offline")
        
    def add_device_and_continue(self):
        """添加设备并继续"""
        # 验证必填字段
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "设备名称不能为空！")
            return
            
        # 收集设备数据
        self.device_data = {
            "name": self.name_edit.text().strip(),
            "type": self.type_edit.text().strip() if self.type_edit.text().strip() else None,
            "ip": self.ip_edit.text().strip() if self.ip_edit.text().strip() else None,
            "location": self.location_edit.text().strip() if self.location_edit.text().strip() else None,
            "status": self.status_combo.currentText()
        }
        
        # 发送添加单个设备的信号
        self.parent().start_single_device_addition(self.device_data)
        
        # 清空表单，准备继续添加
        self.clear_single_form()
        
    def download_template(self):
        """下载导入模板"""
        try:
            # 选择保存位置
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存模板文件", "设备导入模板.xlsx", 
                "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
            )
            
            if not file_path:
                return
                
            # 创建模板数据
            template_data = {
                "设备名称": ["路由器-01", "交换机-01", "防火墙-01"],
                "设备类型": ["路由器", "交换机", "防火墙"],
                "IP地址": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
                "设备位置": ["机房A-机柜01-U1", "机房A-机柜01-U2", "机房A-机柜01-U3"],
                "设备状态": ["online", "online", "offline"]
            }
            
            df = pd.DataFrame(template_data)
            
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False, engine='openpyxl')
            else:
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                
            QMessageBox.information(self, "成功", f"模板文件已保存到：\n{file_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存模板文件失败：{str(e)}")
            
    def select_import_file(self):
        """选择导入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", 
            "Excel文件 (*.xlsx);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_path_label.setText(f"已选择文件: {os.path.basename(file_path)}")
            self.file_path_label.setToolTip(file_path)
            self.import_file_path = file_path
            self.preview_import_file(file_path)
            
    def preview_import_file(self, file_path):
        """预览导入文件"""
        try:
            # 读取文件
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                
            # 标准化列名
            column_mapping = {
                '设备名称': 'name',
                '设备类型': 'type', 
                'IP地址': 'ip',
                '设备位置': 'location',
                '设备状态': 'status'
            }
            
            # 重命名列
            df = df.rename(columns=column_mapping)
            
            # 设置表格
            self.preview_table.setRowCount(len(df))
            self.preview_table.setColumnCount(len(df.columns))
            self.preview_table.setHorizontalHeaderLabels(df.columns.tolist())
            
            # 填充数据
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                    self.preview_table.setItem(i, j, item)
                    
            # 保存数据用于导入
            self.batch_devices = df.to_dict('records')
            
            # 显示文件信息
            self.file_path_label.setText(f"已加载 {len(df)} 条设备记录")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件失败：{str(e)}")
            self.file_path_label.setText("文件读取失败")
            
    def import_batch_devices(self):
        """导入批量设备"""
        if not hasattr(self, 'batch_devices') or not self.batch_devices:
            QMessageBox.warning(self, "提示", "请先选择并预览导入文件！")
            return
            
        reply = QMessageBox.question(
            self, "确认导入", 
            f"确定要导入 {len(self.batch_devices)} 个设备吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(self.batch_devices))
            self.progress_bar.setValue(0)
            
            # 发送批量导入信号
            self.parent().start_batch_device_addition(self.batch_devices)
            
    def update_progress(self, current, total):
        """更新进度条"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(current)
            self.progress_bar.setFormat(f"正在导入: {current}/{total} ({current/total*100:.1f}%)")
            
    def hide_progress(self):
        """隐藏进度条"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
            
    def get_device_data(self):
        """获取设备数据"""
        return self.device_data
        
    def get_batch_devices(self):
        """获取批量设备数据"""
        return self.batch_devices


class DeviceAddWorker(QThread):
    """设备添加工作线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(str)  # 进度更新信号
    device_added = pyqtSignal(str)      # 设备添加完成信号
    error_occurred = pyqtSignal(str)    # 错误信号
    
    def __init__(self, device_data=None, api_base_url=None):
        super().__init__()
        self.device_data = device_data or {}
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """执行设备添加流程"""
        try:
            # 步骤1：获取访问令牌
            self.progress_updated.emit("正在获取访问令牌...")
            if not self.authenticate():
                self.error_occurred.emit("认证失败，请检查管理员账号配置")
                return
            
            # 步骤2：添加设备
            self.progress_updated.emit("正在添加设备...")
            if self.add_device():
                self.device_added.emit(f"设备 '{self.device_data.get('name', '未知')}' 添加成功！")
            else:
                self.error_occurred.emit("设备添加失败，请检查服务器连接")
                
        except Exception as e:
            self.error_occurred.emit(f"设备添加失败: {str(e)}")
            
    def authenticate(self):
        """管理员认证（使用admin账号）"""
        try:
            # 使用admin账号进行认证
            auth_data = {
                "login_type": "管理员",  # 使用管理员登录类型
                "username": "admin",     # 强制使用admin用户名
                "password": api_config.DEFAULT_PASSWORD,
                "grant_type": "password"
            }
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['login']}",
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return True
            else:
                print(f"管理员认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"管理员认证异常: {str(e)}")
            return False
            
    def add_device(self):
        """添加设备"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['create_device']}",
                json=self.device_data,
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"添加设备失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"添加设备异常: {str(e)}")
            return False


class BatchDeviceAddWorker(QThread):
    """批量设备添加工作线程"""
    
    # 定义信号
    progress_updated = pyqtSignal(str)          # 进度更新信号
    batch_progress = pyqtSignal(int, int)       # 批量进度信号(当前数量, 总数量)
    device_added = pyqtSignal(str)              # 单个设备添加成功信号
    batch_completed = pyqtSignal(str)           # 批量添加完成信号
    error_occurred = pyqtSignal(str)            # 错误信号
    
    def __init__(self, batch_devices=None, api_base_url=None):
        super().__init__()
        self.batch_devices = batch_devices or []
        self.api_base_url = api_base_url or api_config.API_BASE_URL
        self.access_token = None
        
    def run(self):
        """执行批量设备添加流程"""
        try:
            # 步骤1：获取访问令牌
            self.progress_updated.emit("正在获取访问令牌...")
            if not self.authenticate():
                self.error_occurred.emit("认证失败，请检查管理员账号配置")
                return
            
            # 步骤2：批量添加设备
            if not self.batch_devices:
                self.error_occurred.emit("没有设备数据需要导入")
                return
                
            self.progress_updated.emit(f"开始批量添加 {len(self.batch_devices)} 个设备...")
            success_count = 0
            fail_count = 0
            
            for i, device in enumerate(self.batch_devices, 1):
                self.progress_updated.emit(f"正在添加设备 {i}/{len(self.batch_devices)}: {device.get('name', '未命名设备')}")
                self.batch_progress.emit(i, len(self.batch_devices))
                
                # 确保设备数据格式正确
                device_data = self.format_device_data(device)
                
                if self.add_single_device(device_data):
                    success_count += 1
                    self.device_added.emit(f"✓ 设备添加成功: {device.get('name', '未命名设备')}")
                else:
                    fail_count += 1
                    self.progress_updated.emit(f"✗ 设备添加失败: {device.get('name', '未命名设备')}")
                    
            # 完成通知
            self.batch_completed.emit(
                f"批量添加完成！成功添加 {success_count} 个设备，失败 {fail_count} 个设备"
            )
            
        except Exception as e:
            self.error_occurred.emit(f"批量设备添加失败: {str(e)}")
            
    def authenticate(self):
        """管理员认证（使用admin账号）"""
        try:
            # 使用admin账号进行认证
            auth_data = {
                "login_type": "管理员",  # 使用管理员登录类型
                "username": "admin",     # 强制使用admin用户名
                "password": api_config.DEFAULT_PASSWORD,
                "grant_type": "password"
            }
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['login']}",
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return True
            else:
                print(f"管理员认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"管理员认证异常: {str(e)}")
            return False
            
    def format_device_data(self, device):
        """格式化设备数据"""
        # 确保所有必需字段都存在，并处理None值
        formatted_device = {
            "name": str(device.get('name', '')).strip() if device.get('name') else '',
            "type": str(device.get('type', '')).strip() if device.get('type') else None,
            "ip": str(device.get('ip', '')).strip() if device.get('ip') else None,
            "location": str(device.get('location', '')).strip() if device.get('location') else None,
            "status": str(device.get('status', 'offline')).strip() if device.get('status') else 'offline'
        }
        
        # 验证设备名称不能为空
        if not formatted_device["name"]:
            formatted_device["name"] = f"设备-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
            
        # 确保状态值有效
        valid_statuses = ['online', 'offline', 'maintenance']
        if formatted_device["status"] not in valid_statuses:
            formatted_device["status"] = 'offline'
            
        return formatted_device
        
    def add_single_device(self, device_data):
        """添加单个设备"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_base_url}{api_config.API_ENDPOINTS['create_device']}",
                json=device_data,
                headers=headers,
                timeout=api_config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"添加设备失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"添加设备异常: {str(e)}")
            return False


class DesktopManager(QWidget):
    """桌面管理器 - 在桌面顶部悬浮显示"""
    
    # 定义信号
    show_settings = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.pet_widget = None
        self.chat_widget = None
        self.online_chat_widget = None  # 添加在线聊天窗口实例
        self.tuopo_widget = None  # 添加拓扑图窗口实例
        self.transition_page = None
        self.openai_chat = None  # 添加OpenAI聊天实例
        self.is_expanded = False
        self.current_role_data = None  # 当前角色数据
        self.role_avatar_label = None  # 角色头像标签
        self.role_name_label = None  # 角色名称标签
        self.role_desc_label = None  # 角色描述标签
        self.file_watcher = None  # 文件监视器
        self.task_worker = None  # 任务提交工作线程
        self.task_list_worker = None  # 任务列表获取工作线程
        self.device_worker = None  # 设备添加工作线程
        self.batch_device_worker = None  # 批量设备添加工作线程
        self.device_dialog = None  # 设备添加对话框实例
        
        # 初始化增强的数据接收器
        self.data_receiver = DataReceiver(self)
        
        # 配置选项 - 是否自动打开任务提交弹窗
        self.auto_open_task_dialog = True  # 设置为True表示启动后自动打开任务提交弹窗
        
        # 初始化UI和设置
        self.setup_data_receivers()  # 设置增强的数据接收器
        self.load_role_data()  # 加载角色数据
        self.setup_ui()
        self.setup_timer()
        self.setup_animations()
        self.position_at_top()
        
        # 延迟检查是否有待处理的任务，避免在初始化时阻塞界面
        print("🚀 Desktop Manager 已启动，将在1秒后检查任务通知...")
        print(f"📋 自动打开任务对话框: {'启用' if self.auto_open_task_dialog else '禁用'}")
        
        # 创建定时器并连接槽函数
        self.notification_timer = QTimer()
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self.check_and_notify_tasks)
        self.notification_timer.start(1000)
        print("⏰ 任务通知定时器已启动")
        
    def setup_data_receivers(self):
        """设置增强的数据接收器"""
        try:
            print("🔧 正在设置数据接收器...")
            
            # 启动文件监听器
            self.data_receiver.start_file_watcher()
            
            # 启动HTTP服务器（可选）
            try:
                self.data_receiver.start_http_server(port=8080)
            except Exception as e:
                print(f"⚠️ HTTP服务器启动失败（可能端口被占用）: {str(e)}")
                print("📂 将仅使用文件监听器接收数据")
            
            print("✅ 数据接收器设置完成")
            
        except Exception as e:
            print(f"❌ 设置数据接收器失败: {str(e)}")
            # 回退到简单的文件监听器
            self.setup_simple_file_watcher()
    
    def setup_simple_file_watcher(self):
        """设置简单的文件监听器（回退方案）"""
        try:
            self.file_watcher = QFileSystemWatcher()
            json_file_path = os.path.join(os.getcwd(), "received_data.json")
            if os.path.exists(json_file_path):
                self.file_watcher.addPath(json_file_path)
                self.file_watcher.fileChanged.connect(self.on_json_file_changed)
                print("📂 简单文件监听器已启动")
        except Exception as e:
            print(f"❌ 简单文件监听器启动失败: {str(e)}")
            
    def on_json_file_changed(self):
        """当JSON文件发生变化时的处理函数（兼容旧版本）"""
        print("📁 检测到received_data.json文件变化")
        self.load_role_data()
        self.update_role_display()
        
    def load_role_data(self):
        """从JSON文件加载角色数据 - 使用增强的数据处理器"""
        try:
            # 刷新API配置（从JSON文件重新获取用户名、密码、登录类型）
            api_config.refresh_all_config()
            
            json_file_path = os.path.join(os.getcwd(), "received_data.json")
            if os.path.exists(json_file_path):
                print(f"📂 正在加载角色数据: {json_file_path}")
                
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 使用数据处理器检测格式
                data_format = DataProcessor.detect_data_format(data)
                print(f"🔍 检测到数据格式: {data_format}")
                
                if data_format == 'task_assignment':
                    # 处理任务分配格式
                    try:
                        processed_data = DataProcessor.process_task_assignment_format(data)
                        user_info = processed_data['user_info']
                        
                        # 构建兼容的角色数据结构
                        role_data = {
                            'action': 'task_deployment',
                            'selectedRole': user_info['selectedRole'],
                            'user': user_info['user'],
                            'session': user_info.get('session', {}),
                            'deployment_time': user_info.get('timestamp'),
                            'assigned_tasks_count': len(processed_data.get('tasks', [])),
                            'data_source': processed_data.get('data_source'),
                            'deployment_id': user_info.get('deployment_id', ''),
                            'target_ip': user_info.get('target_ip', ''),
                            'validation_passed': processed_data.get('validation_passed', False),
                            'processing_time': processed_data.get('processing_time')
                        }
                        
                        self.current_role_data = role_data
                        
                        print(f"✅ 任务分配数据加载成功:")
                        print(f"   🎯 目标角色: {role_data['selectedRole']['label']}")
                        print(f"   👤 操作员: {role_data['user']['username']} (ID: {role_data['user']['id']})")
                        print(f"   📋 分配任务数: {role_data['assigned_tasks_count']}")
                        print(f"   📊 数据源: {role_data['data_source']}")
                        print(f"   🆔 部署ID: {role_data['deployment_id']}")
                        print(f"   ✅ 数据验证: {'通过' if role_data['validation_passed'] else '失败'}")
                        
                    except Exception as e:
                        print(f"❌ 处理任务分配数据失败: {str(e)}")
                        # 回退到简单处理
                        self.current_role_data = self._fallback_role_processing(data)
                        
                elif data_format == 'user_data_sync':
                    # 处理用户数据同步格式
                    try:
                        processed_data = DataProcessor.process_user_data_sync(data)
                        user_info = processed_data['user_info']
                        
                        # 构建兼容的角色数据结构
                        role_data = {
                            'action': 'user_data_sync',
                            'selectedRole': user_info['selectedRole'],
                            'user': user_info['user'],
                            'session': user_info.get('session', {}),
                            'sync_time': user_info.get('timestamp'),
                            'sync_type': user_info.get('sync_type'),
                            'sync_id': user_info.get('sync_id'),
                            'data_source': processed_data.get('data_source'),
                            'validation_passed': processed_data.get('validation_passed', False),
                            'processing_time': processed_data.get('processing_time'),
                            'needs_api_fetch': processed_data.get('needs_api_fetch', False)
                        }
                        
                        self.current_role_data = role_data
                        
                        print(f"✅ 用户数据同步加载成功:")
                        print(f"   👤 用户: {role_data['user']['username']} (ID: {role_data['user']['id']})")
                        print(f"   🎯 角色: {role_data['selectedRole']['label']}")
                        print(f"   🔄 同步类型: {role_data['sync_type']}")
                        print(f"   📊 数据源: {role_data['data_source']}")
                        print(f"   🆔 同步ID: {role_data['sync_id']}")
                        print(f"   ✅ 数据验证: {'通过' if role_data['validation_passed'] else '失败'}")
                        print(f"   🌐 需要API获取: {'是' if role_data['needs_api_fetch'] else '否'}")
                        
                    except Exception as e:
                        print(f"❌ 处理用户数据同步失败: {str(e)}")
                        # 回退到简单处理
                        self.current_role_data = self._fallback_user_sync_processing(data)
                        
                elif data_format == 'legacy':
                    # 处理传统格式
                    try:
                        processed_data = DataProcessor.process_legacy_format(data)
                        self.current_role_data = data
                        print(f"📜 传统格式数据加载成功: {data.get('selectedRole', {}).get('label', '未知角色')}")
                        
                    except Exception as e:
                        print(f"❌ 处理传统格式数据失败: {str(e)}")
                        self.current_role_data = data
                        
                else:
                    print(f"❌ 未知的数据格式，尝试兼容处理")
                    self.current_role_data = data
                    
            else:
                print("❌ 未找到received_data.json文件")
                self.current_role_data = None
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {str(e)}")
            self.current_role_data = None
        except Exception as e:
            print(f"❌ 加载角色数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.current_role_data = None
    
    def _fallback_role_processing(self, data):
        """回退的角色数据处理"""
        try:
            deployment_info = data.get('deployment_info', {})
            operator = deployment_info.get('operator', {})
            
            return {
                'action': 'task_deployment',
                'selectedRole': {
                    'label': deployment_info.get('target_role', '未知角色'),
                    'value': deployment_info.get('target_role', '未知角色'),
                    'description': f"当前任务角色：{deployment_info.get('target_role', '未知')}"
                },
                'user': {
                    'id': operator.get('user_id'),
                    'username': operator.get('username', '未知用户'),
                    'role': operator.get('operator_role', '未知角色'),
                    'type': operator.get('operator_type', '操作员')
                },
                'session': deployment_info.get('session', {}),
                'deployment_time': deployment_info.get('deployment_time'),
                'assigned_tasks_count': len(data.get('assigned_tasks', [])),
                'data_source': data.get('deployment_summary', {}).get('data_source', 'fallback'),
                'validation_passed': False
            }
        except Exception as e:
            print(f"❌ 回退处理也失败: {str(e)}")
            return None
    
    def _fallback_user_sync_processing(self, data):
        """回退的用户数据同步处理"""
        try:
            sync_info = data.get('sync_info', {})
            operator = sync_info.get('operator', {})
            users = data.get('users', [])
            current_user = users[0] if users else {}
            
            return {
                'action': 'user_data_sync',
                'selectedRole': {
                    'label': current_user.get('role', '未知角色'),
                    'value': current_user.get('role', '未知角色'),
                    'description': f"当前用户角色：{current_user.get('role', '未知')}"
                },
                'user': {
                    'id': current_user.get('id'),
                    'username': current_user.get('username', '未知用户'),
                    'role': current_user.get('role', '未知角色'),
                    'type': current_user.get('type', '操作员'),
                    'status': current_user.get('status', 'active')
                },
                'session': sync_info.get('session', {}),
                'sync_time': sync_info.get('sync_time'),
                'sync_type': sync_info.get('sync_type', 'unknown'),
                'sync_id': data.get('sync_summary', {}).get('sync_id', ''),
                'data_source': 'user_data_sync_fallback',
                'validation_passed': False,
                'needs_api_fetch': True
            }
        except Exception as e:
            print(f"❌ 用户数据同步回退处理也失败: {str(e)}")
            return None
        
    def get_role_image_path(self, role_name):
        """根据角色名称获取对应的图片路径"""
        # 角色名称到图片文件名的映射
        role_image_mapping = {
            "网络工程师": "network_engineer.jpg",
            "系统架构师": "system_architect.jpg", 
            "系统规划与管理师": "Network_Planning_and_Management_Engineer.jpg"
        }
        
        image_filename = role_image_mapping.get(role_name, "network_engineer.jpg")  # 默认使用网络工程师图片
        image_path = os.path.join("image", "engineer", image_filename)
        
        if os.path.exists(image_path):
            return image_path
        else:
            # 如果找不到对应图片，尝试使用默认图片
            default_path = os.path.join("image", "engineer", "network_engineer.jpg")
            return default_path if os.path.exists(default_path) else None
        
    def setup_ui(self):
        """设置UI界面"""
        # 设置窗口属性 - 桌面顶部悬浮
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口大小 - 增加宽度以容纳角色信息
        self.setFixedHeight(80)
        self.setMinimumWidth(1000)
        
        # 创建主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)
        
        # 创建背景框架
        self.background_frame = QFrame()
        self.background_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(45, 52, 54, 220),
                    stop:1 rgba(99, 110, 114, 200));
                border-radius: 25px;
                border: 1px solid rgba(116, 125, 140, 150);
            }
        """)
        
        # 背景框架布局
        frame_layout = QHBoxLayout(self.background_frame)
        frame_layout.setContentsMargins(15, 8, 15, 8)
        frame_layout.setSpacing(10)
        
        # 左侧 - 角色信息区域
        self.create_role_section(frame_layout)
        
        # 分隔符1
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("QFrame { color: rgba(255, 255, 255, 100); }")
        frame_layout.addWidget(separator1)
        
        # 中间 - 系统信息区域
        self.create_info_section(frame_layout)
        
        # 分隔符2
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("QFrame { color: rgba(255, 255, 255, 100); }")
        frame_layout.addWidget(separator2)
        
        # 右侧 - 功能按钮区域
        self.create_buttons_section(frame_layout)
        
        # 添加背景框架到主布局
        main_layout.addWidget(self.background_frame)
        self.setLayout(main_layout)
        
        # 初始化角色显示
        self.update_role_display()
        
    def create_role_section(self, layout):
        """创建角色信息显示区域"""
        role_layout = QHBoxLayout()
        role_layout.setSpacing(10)
        
        # 角色头像
        self.role_avatar_label = QLabel()
        self.role_avatar_label.setFixedSize(55, 55)
        self.role_avatar_label.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(255, 255, 255, 150);
                border-radius: 27px;
                background: rgba(255, 255, 255, 50);
            }
        """)
        self.role_avatar_label.setScaledContents(True)
        
        # 角色信息文本区域
        role_text_layout = QVBoxLayout()
        role_text_layout.setSpacing(2)
        role_text_layout.setContentsMargins(0, 0, 0, 0)
        
        # 角色名称
        self.role_name_label = QLabel("当前角色")
        self.role_name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.role_name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
            }
        """)
        
        # 角色描述
        self.role_desc_label = QLabel("等待加载...")
        self.role_desc_label.setFont(QFont("Microsoft YaHei", 8))
        self.role_desc_label.setStyleSheet("""
            QLabel {
                color: #dcdde1;
                background: transparent;
            }
        """)
        
        # 添加到文本布局
        role_text_layout.addWidget(self.role_name_label)
        role_text_layout.addWidget(self.role_desc_label)
        
        # 添加到角色布局
        role_layout.addWidget(self.role_avatar_label)
        role_layout.addLayout(role_text_layout)
        role_layout.addStretch()
        
        layout.addLayout(role_layout)
        
    def update_role_display(self):
        """更新角色显示信息"""
        if not self.current_role_data:
            # 显示默认信息
            self.role_name_label.setText("当前角色")
            self.role_desc_label.setText("等待加载...")
            # 设置默认头像
            self.set_default_avatar()
            return
            
        # 获取角色信息
        selected_role = self.current_role_data.get('selectedRole', {})
        user_info = self.current_role_data.get('user', {})
        
        role_name = selected_role.get('label', '未知角色')
        role_desc = selected_role.get('description', '无描述')
        
        # 更新显示
        self.role_name_label.setText(role_name)
        self.role_desc_label.setText(role_desc)
        
        # 更新头像
        self.update_role_avatar(role_name)
        
        # 更新状态标签
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"当前角色: {role_name}")
            
    def update_role_avatar(self, role_name):
        """更新角色头像"""
        image_path = self.get_role_image_path(role_name)
        
        if image_path and os.path.exists(image_path):
            try:
                # 加载图片
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 创建圆形头像
                    rounded_pixmap = self.create_rounded_pixmap(pixmap, 55)
                    self.role_avatar_label.setPixmap(rounded_pixmap)
                    print(f"已加载角色头像: {image_path}")
                else:
                    print(f"无法加载图片: {image_path}")
                    self.set_default_avatar()
            except Exception as e:
                print(f"设置头像失败: {str(e)}")
                self.set_default_avatar()
        else:
            print(f"未找到角色图片: {image_path}")
            self.set_default_avatar()
            
    def create_rounded_pixmap(self, pixmap, size):
        """创建圆形图片"""
        # 缩放图片
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        
        # 创建圆形遮罩
        rounded_pixmap = QPixmap(size, size)
        rounded_pixmap.fill(Qt.transparent)
        
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆形
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        # 设置混合模式并绘制图片
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()
        
        return rounded_pixmap
        
    def set_default_avatar(self):
        """设置默认头像"""
        # 创建默认头像 - 一个简单的用户图标
        pixmap = QPixmap(55, 55)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景圆
        painter.setBrush(QColor(100, 149, 237))  # 蓝色背景
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 55, 55)
        
        # 绘制用户图标 (简单的人形)
        painter.setPen(Qt.white)
        painter.setBrush(Qt.white)
        
        # 头部
        painter.drawEllipse(20, 12, 15, 15)
        # 身体
        painter.drawEllipse(16, 27, 23, 23)
        
        painter.end()
        
        self.role_avatar_label.setPixmap(pixmap)
        
    def create_info_section(self, layout):
        """创建信息显示区域"""
        info_layout = QHBoxLayout()
        
        # 时间显示
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.time_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                padding: 2px 8px;
            }
        """)
        
        # 日期显示
        self.date_label = QLabel()
        self.date_label.setFont(QFont("Microsoft YaHei", 9))
        self.date_label.setStyleSheet("""
            QLabel {
                color: #dcdde1;
                background: transparent;
                padding: 2px 8px;
            }
        """)
        
        # 系统状态
        self.status_label = QLabel("系统运行正常")
        self.status_label.setFont(QFont("Microsoft YaHei", 9))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00d2d3;
                background: transparent;
                padding: 2px 8px;
            }
        """)
        
        # 添加到布局
        info_layout.addWidget(self.time_label)
        info_layout.addWidget(self.date_label)
        info_layout.addWidget(self.status_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
    def create_buttons_section(self, layout):
        """创建功能按钮区域"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # 按钮配置
        buttons_config = [
            ("🗺️", "拓扑图", self.show_tuopo, "#3498db"),
            ("🐱", "宠物", self.show_pet, "#e74c3c"),
            ("💬", "聊天", self.show_chat, "#2ecc71"),
            ("⚙️", "设置", self.show_settings_action, "#f39c12"),
            ("📤", "智能任务列表", self.submit_tasks, "#9b59b6"),
            ("🖥️", "添加设备", self.add_device, "#34495e"),
            ("❌", "退出", self.exit_application, "#95a5a6")
        ]
        
        for icon, tooltip, handler, color in buttons_config:
            button = self.create_button(icon, tooltip, handler, color)
            buttons_layout.addWidget(button)
        
        layout.addLayout(buttons_layout)
        
    def create_button(self, text, tooltip, handler, color):
        """创建功能按钮"""
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setFixedSize(40, 40)
        button.setFont(QFont("Segoe UI Emoji", 12))
        button.clicked.connect(handler)
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color},
                    stop:1 {self.darken_color(color, 0.8)});
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.lighten_color(color, 1.2)},
                    stop:1 {color});
                transform: scale(1.05);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.darken_color(color, 0.7)},
                    stop:1 {self.darken_color(color, 0.9)});
            }}
        """)
        
        return button
        
    def darken_color(self, hex_color, factor=0.8):
        """使颜色变暗"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def lighten_color(self, hex_color, factor=1.2):
        """使颜色变亮"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lightened = tuple(min(255, int(c * factor)) for c in rgb)
        return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"
        
    def setup_timer(self):
        """设置定时器"""
        # 时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新
        
        # 初始化时间显示
        self.update_time()
        
    def setup_animations(self):
        """设置动画效果"""
        # 创建动画对象
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def position_at_top(self):
        """将管理器定位到屏幕顶部中央"""
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()
        
        # 计算位置 - 顶部中央
        x = (screen_rect.width() - self.width()) // 2
        y = 10  # 距离顶部10像素
        
        self.move(x, y)
        
    def update_time(self):
        """更新时间显示"""
        current_time = QTime.currentTime()
        time_text = current_time.toString("hh:mm:ss")
        self.time_label.setText(time_text)
        
        # 更新日期
        from datetime import datetime
        current_date = datetime.now()
        date_text = current_date.strftime("%Y年%m月%d日")
        self.date_label.setText(date_text)
        
    def show_tuopo(self):
        """显示/隐藏拓扑图"""
        if not self.tuopo_widget:
            self.tuopo_widget = TuopoWidget()
            
        if self.tuopo_widget.isVisible():
            self.tuopo_widget.hide()
            self.status_label.setText("拓扑图已隐藏")
        else:
            self.tuopo_widget.show()
            self.status_label.setText("拓扑图已显示")
            
    def show_pet(self):
        """显示/隐藏宠物"""
        if not self.pet_widget:
            self.pet_widget = PetWidget()
            self.pet_widget.doubleClicked.connect(self.show_chat)
            
        if self.pet_widget.isVisible():
            self.pet_widget.hide()
            self.status_label.setText("宠物已隐藏")
        else:
            self.pet_widget.show()
            self.status_label.setText("宠物已显示")
            
    def show_chat(self):
        """显示/隐藏在线聊天窗口"""
        if not self.online_chat_widget:
            # 创建在线聊天窗口实例
            self.online_chat_widget = OnlineChatWidget()
            
            # 设置用户信息（可以从角色数据中获取）
            if hasattr(self, 'current_role_data') and self.current_role_data:
                username = self.current_role_data.get('username', '当前用户')
                self.online_chat_widget.set_user_info(username)
            else:
                self.online_chat_widget.set_user_info('当前用户')
            
        if self.online_chat_widget.isVisible():
            self.online_chat_widget.hide()
            self.status_label.setText("在线聊天窗口已隐藏")
        else:
            self.online_chat_widget.show()
            self.status_label.setText("在线聊天窗口已显示")
            
    def show_settings_action(self):
        """显示设置"""
        self.status_label.setText("设置功能开发中...")
        # TODO: 实现设置界面
        
    def add_device(self):
        """添加设备"""
        # 检查是否有设备添加操作正在进行
        if (self.device_worker and self.device_worker.isRunning()) or \
           (self.batch_device_worker and self.batch_device_worker.isRunning()):
            QMessageBox.information(self, "提示", "设备添加正在进行中，请稍等...")
            return
            
        # 如果对话框已存在且可见，则显示并激活
        if self.device_dialog and self.device_dialog.isVisible():
            self.device_dialog.raise_()
            self.device_dialog.activateWindow()
            return
            
        # 创建新的设备添加对话框
        self.device_dialog = DeviceAddDialog(self)
        self.device_dialog.show()  # 使用show()而不是exec_()，这样对话框不会阻塞主程序
                
    def start_device_addition(self, device_data):
        """开始设备添加流程"""
        # 创建设备添加工作线程
        self.device_worker = DeviceAddWorker(device_data)
        
        # 连接信号
        self.device_worker.progress_updated.connect(self.on_device_progress_updated)
        self.device_worker.device_added.connect(self.on_device_added)
        self.device_worker.error_occurred.connect(self.on_device_error)
        
        # 开始设备添加
        self.status_label.setText("正在准备添加设备...")
        self.device_worker.start()
        
    @pyqtSlot(str)
    def on_device_progress_updated(self, message):
        """设备添加进度更新回调"""
        self.status_label.setText(message)
        print(f"设备添加进度: {message}")
        
    @pyqtSlot(str) 
    def on_device_added(self, message):
        """设备添加完成回调"""
        self.status_label.setText("设备添加成功")
        print(f"设备添加完成: {message}")
        
        # 显示完成对话框
        QMessageBox.information(self, "设备添加成功", message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    @pyqtSlot(str)
    def on_device_error(self, error_message):
        """设备添加错误回调"""
        self.status_label.setText("设备添加失败")
        print(f"设备添加错误: {error_message}")
        
        # 显示错误对话框
        QMessageBox.warning(self, "设备添加失败", error_message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    def start_single_device_addition(self, device_data):
        """开始单个设备添加流程"""
        # 检查是否有设备添加操作正在进行
        if self.device_worker and self.device_worker.isRunning():
            QMessageBox.information(self, "提示", "设备添加正在进行中，请稍等...")
            return
        
        # 创建设备添加工作线程
        self.device_worker = DeviceAddWorker(device_data)
        
        # 连接信号
        self.device_worker.progress_updated.connect(self.on_device_progress_updated)
        self.device_worker.device_added.connect(self.on_single_device_added)
        self.device_worker.error_occurred.connect(self.on_device_error)
        
        # 开始设备添加
        self.status_label.setText("正在准备添加设备...")
        self.device_worker.start()
        
    def start_batch_device_addition(self, batch_devices):
        """开始批量设备添加流程"""
        # 检查是否有设备添加操作正在进行
        if self.batch_device_worker and self.batch_device_worker.isRunning():
            QMessageBox.information(self, "提示", "批量设备添加正在进行中，请稍等...")
            return
        
        # 创建批量设备添加工作线程
        self.batch_device_worker = BatchDeviceAddWorker(batch_devices)
        
        # 连接信号
        self.batch_device_worker.progress_updated.connect(self.on_device_progress_updated)
        self.batch_device_worker.batch_progress.connect(self.on_batch_progress_updated)
        self.batch_device_worker.device_added.connect(self.on_batch_device_added)
        self.batch_device_worker.batch_completed.connect(self.on_batch_completed)
        self.batch_device_worker.error_occurred.connect(self.on_device_error)
        
        # 开始批量设备添加
        self.status_label.setText("正在准备批量添加设备...")
        self.batch_device_worker.start()
        
    @pyqtSlot(str)
    def on_single_device_added(self, message):
        """单个设备添加完成回调"""
        self.status_label.setText("设备添加成功")
        print(f"单个设备添加完成: {message}")
        
        # 不显示消息框，只显示简短提示，避免打断用户操作
        self.status_label.setText("设备添加成功，可继续添加")
        
        # 3秒后恢复状态显示
        QTimer.singleShot(3000, lambda: self.status_label.setText("系统运行正常"))
        
    @pyqtSlot(int, int)
    def on_batch_progress_updated(self, current, total):
        """批量进度更新回调"""
        if self.device_dialog and hasattr(self.device_dialog, 'update_progress'):
            self.device_dialog.update_progress(current, total)
        self.status_label.setText(f"正在导入设备: {current}/{total}")
        
    @pyqtSlot(str)
    def on_batch_device_added(self, message):
        """批量设备中单个设备添加成功回调"""
        print(f"批量设备添加进度: {message}")
        
    @pyqtSlot(str)
    def on_batch_completed(self, message):
        """批量设备添加完成回调"""
        self.status_label.setText("批量添加完成")
        print(f"批量设备添加完成: {message}")
        
        # 隐藏进度条
        if self.device_dialog and hasattr(self.device_dialog, 'hide_progress'):
            self.device_dialog.hide_progress()
        
        # 显示完成对话框
        QMessageBox.information(self, "批量添加完成", message)
        
        # 3秒后恢复状态显示
        QTimer.singleShot(3000, lambda: self.status_label.setText("系统运行正常"))
        
    def submit_tasks(self):
        """打开任务选择对话框"""
        # 如果已有任务在执行，不允许重复操作
        if self.task_worker and self.task_worker.isRunning():
            QMessageBox.information(self, "提示", "任务提交正在进行中，请稍等...")
            return
            
        if self.task_list_worker and self.task_list_worker.isRunning():
            QMessageBox.information(self, "提示", "正在获取任务列表，请稍等...")
            return
            
        # 显示加载状态
        self.status_label.setText("正在智能获取任务列表...")
        
        # 首先检查是否有从前端接收到的任务数据
        received_tasks = self.load_received_tasks()
        if received_tasks:
            print(f"✓ 使用从前端接收到的智能任务数据，共 {len(received_tasks)} 个任务")
            self.status_label.setText(f"已加载 {len(received_tasks)} 个智能推荐任务")
            # 延迟一下让用户看到状态信息
            QTimer.singleShot(500, lambda: self.on_tasks_loaded(received_tasks))
            return
        
        print("⚠ 未找到前端智能推荐任务，回退到API获取任务列表...")
        self.status_label.setText("正在从服务器获取任务列表...")
        # 创建任务列表获取工作线程
        self.task_list_worker = TaskListWorker()
        
        # 连接信号
        self.task_list_worker.tasks_loaded.connect(self.on_tasks_loaded)
        self.task_list_worker.error_occurred.connect(self.on_task_list_error)
        
        # 开始获取任务列表
        self.task_list_worker.start()
    
    def load_received_tasks(self):
        """加载从前端接收到的任务数据 - 使用增强的数据处理器"""
        try:
            task_file_path = os.path.join(os.getcwd(), 'received_tasks.json')
            data_file_path = os.path.join(os.getcwd(), 'received_data.json')
            
            print(f"📂 开始加载任务数据...")
            
            # 检查received_tasks.json文件是否存在
            if not os.path.exists(task_file_path):
                print("received_tasks.json 文件不存在，尝试从received_data.json处理...")
                
                if not os.path.exists(data_file_path):
                    print("❌ received_data.json 文件也不存在")
                    return None
                
                # 从received_data.json处理数据
                with open(data_file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # 使用数据处理器处理数据
                data_format = DataProcessor.detect_data_format(raw_data)
                print(f"🔍 检测到数据格式: {data_format}")
                
                if data_format == 'task_assignment':
                    try:
                        processed_data = DataProcessor.process_task_assignment_format(raw_data)
                        print(f"✅ 任务分配数据处理成功")
                    except Exception as e:
                        print(f"❌ 任务分配数据处理失败: {str(e)}")
                        return None
                        
                elif data_format == 'user_data_sync':
                    try:
                        processed_data = DataProcessor.process_user_data_sync(raw_data)
                        print(f"✅ 用户数据同步处理成功")
                        
                        # 如果需要通过API获取任务
                        if processed_data.get('needs_api_fetch'):
                            print(f"🌐 需要通过API获取任务数据...")
                            api_user_info = processed_data.get('api_user_info', {})
                            
                            # 使用API客户端获取任务
                            api_client = APIClient()
                            user_type = api_user_info.get('type', '操作员')  # 默认为操作员
                            operator_type = api_user_info.get('operator_type')  # 获取操作员类型
                            if api_client.authenticate(api_user_info.get('username'), api_user_info.get('password'), user_type, operator_type):
                                tasks = api_client.get_my_tasks()
                                if tasks:
                                    # 转换API任务格式为内部格式
                                    converted_tasks = []
                                    for task in tasks:
                                        converted_task = self._convert_api_task_to_internal_format(task)
                                        converted_tasks.append(converted_task)
                                    
                                    processed_data['tasks'] = converted_tasks
                                    processed_data['needs_api_fetch'] = False
                                    print(f"✅ 通过API成功获取 {len(converted_tasks)} 个任务")
                                else:
                                    print(f"⚠️ API返回空任务列表")
                            else:
                                print(f"❌ API认证失败，无法获取任务")
                                return None
                        
                    except Exception as e:
                        print(f"❌ 用户数据同步处理失败: {str(e)}")
                        return None
                        
                elif data_format == 'legacy':
                    try:
                        processed_data = DataProcessor.process_legacy_format(raw_data)
                        print(f"✅ 传统格式数据处理成功")
                    except Exception as e:
                        print(f"❌ 传统格式数据处理失败: {str(e)}")
                        return None
                        
                else:
                    print(f"❌ 未知的数据格式，无法处理")
                    return None
                
                # 保存处理后的数据
                try:
                    with open(task_file_path, 'w', encoding='utf-8') as f:
                        json.dump(processed_data, f, ensure_ascii=False, indent=2)
                    print(f"✅ 已将处理后的数据保存到 {task_file_path}")
                except Exception as e:
                    print(f"❌ 保存处理后的数据失败: {str(e)}")
                    # 即使保存失败，也继续使用内存中的数据
                
            else:
                # 直接读取已存在的received_tasks.json
                print(f"📖 读取已存在的任务文件: {task_file_path}")
                with open(task_file_path, 'r', encoding='utf-8') as f:
                    processed_data = json.load(f)
            
            # 提取任务数据
            tasks = processed_data.get('tasks', [])
            user_info = processed_data.get('user_info', {})
            data_source = processed_data.get('data_source', 'unknown')
            original_format = processed_data.get('original_format', 'unknown')
            validation_passed = processed_data.get('validation_passed', False)
            
            if not tasks:
                print("❌ 没有找到任务数据")
                return None
            
            # 输出加载结果
            print(f"✅ 任务数据加载成功:")
            print(f"   📋 任务数量: {len(tasks)}")
            print(f"   👤 用户: {user_info.get('user', {}).get('username', 'Unknown')}")
            print(f"   🎯 角色: {user_info.get('selectedRole', {}).get('label', 'Unknown')}")
            print(f"   📊 数据源: {data_source}")
            print(f"   📝 原始格式: {original_format}")
            print(f"   ✅ 验证状态: {'通过' if validation_passed else '未验证'}")
            
            # 输出任务详情
            print(f"📋 任务详情:")
            for i, task in enumerate(tasks, 1):
                task_name = task.get('name', task.get('task_name', '未命名任务'))
                task_status = task.get('status', task.get('assignment_status', '未知状态'))
                task_type = task.get('type', task.get('task_type', '未知类型'))
                assignment_id = task.get('assignment_id', '无')
                priority = task.get('priority', 'normal')
                progress = task.get('progress', task.get('completion_percentage', 0))
                
                print(f"   {i}. {task_name}")
                print(f"      状态: {task_status} | 类型: {task_type} | 优先级: {priority}")
                print(f"      进度: {progress}% | 分配ID: {assignment_id}")
                
                # 显示额外信息（如果存在）
                if task.get('estimated_duration'):
                    print(f"      预计时长: {task.get('estimated_duration')}")
                if task.get('requirements'):
                    print(f"      要求: {', '.join(task.get('requirements', []))}")
                if task.get('deliverables'):
                    print(f"      交付物: {', '.join(task.get('deliverables', []))}")
                print()
            
            # 数据质量检查
            self._validate_loaded_tasks(tasks)
            
            return tasks
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式错误: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ 加载任务数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _convert_api_task_to_internal_format(self, api_task):
        """将API返回的任务格式转换为内部格式"""
        try:
            # API任务格式转换为内部格式
            converted_task = {
                # 基本信息
                'id': api_task.get('id'),
                'assignment_id': api_task.get('id'),  # 使用任务分配ID
                'name': api_task.get('task_name', '未命名任务'),
                'task_name': api_task.get('task_name', '未命名任务'),
                'description': api_task.get('task_description', ''),
                'type': api_task.get('task_type', '未知类型'),
                'task_type': api_task.get('task_type', '未知类型'),
                'phase': api_task.get('task_phase', ''),
                'task_phase': api_task.get('task_phase', ''),
                
                # 状态信息
                'status': api_task.get('status', '未知状态'),
                'assignment_status': api_task.get('status', '未知状态'),
                'progress': api_task.get('progress', 0),
                'assignment_progress': api_task.get('progress', 0),
                'completion_percentage': api_task.get('progress', 0),
                'performance_score': api_task.get('performance_score', 0),
                
                # 时间信息
                'assigned_at': api_task.get('assigned_at'),
                'last_update': api_task.get('last_update'),
                'comments': api_task.get('comments', ''),
                
                # 任务属性
                'priority': 'normal',  # 默认优先级
                'estimated_duration': '',
                'requirements': [],
                'deliverables': [],
                'execution_status': api_task.get('status', 'pending'),
                'role_binding': '',
                
                # 元数据
                'original_data': api_task,
                'converted_at': datetime.now().isoformat(),
                'data_source': 'api'
            }
            
            return converted_task
            
        except Exception as e:
            print(f"❌ 转换API任务失败: {str(e)}")
            return None
    
    def _validate_loaded_tasks(self, tasks):
        """验证加载的任务数据质量"""
        try:
            print(f"🔍 开始任务数据质量检查...")
            
            issues = []
            
            for i, task in enumerate(tasks):
                task_issues = []
                
                # 检查必需字段
                required_fields = ['name', 'status']
                for field in required_fields:
                    if not task.get(field) and not task.get(f'task_{field}'):
                        task_issues.append(f"缺少{field}字段")
                
                # 检查ID字段
                if not any([task.get('id'), task.get('task_id'), task.get('assignment_id')]):
                    task_issues.append("缺少有效的ID字段")
                
                # 检查状态值
                status = task.get('status', task.get('assignment_status', ''))
                if status and status not in DataValidation.VALID_ASSIGNMENT_STATUSES:
                    task_issues.append(f"状态值'{status}'不在标准列表中")
                
                # 检查优先级
                priority = task.get('priority', '')
                if priority and priority not in DataValidation.VALID_PRIORITIES:
                    task_issues.append(f"优先级'{priority}'不在标准列表中")
                
                # 检查进度值
                progress = task.get('progress', task.get('completion_percentage', 0))
                if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
                    task_issues.append(f"进度值'{progress}'无效")
                
                if task_issues:
                    issues.append(f"任务{i+1}({task.get('name', '未命名')}): {', '.join(task_issues)}")
            
            if issues:
                print(f"⚠️ 发现 {len(issues)} 个数据质量问题:")
                for issue in issues[:5]:  # 只显示前5个问题
                    print(f"   - {issue}")
                if len(issues) > 5:
                    print(f"   ... 还有 {len(issues) - 5} 个问题")
            else:
                print(f"✅ 任务数据质量检查通过")
                
        except Exception as e:
            print(f"❌ 数据质量检查失败: {str(e)}")
    
    def mark_tasks_as_notified(self):
        """标记任务已通知，避免重复弹窗"""
        try:
            task_file_path = os.path.join(os.getcwd(), 'received_tasks.json')
            if os.path.exists(task_file_path):
                # 备份原始文件并添加已通知标记
                import shutil
                backup_path = f"{task_file_path}.notified_{int(time.time())}"
                shutil.copy2(task_file_path, backup_path)
                print(f"任务已通知，数据已备份到: {backup_path}")
                
                # 删除原文件，避免下次启动时重复通知
                os.remove(task_file_path)
                print("原任务文件已删除，避免重复通知")
                
        except Exception as e:
            print(f"标记任务已通知时出错: {str(e)}")
        
    @pyqtSlot(list)
    def on_tasks_loaded(self, tasks):
        """任务列表加载完成"""
        self.status_label.setText("系统运行正常")
        
        if not tasks:
            QMessageBox.information(self, "提示", "当前没有任务")
            return
            
        # 过滤出待提交的任务 - 使用与check_and_notify_tasks相同的筛选条件
        pending_status_list = [api_config.TASK_STATUS.get("PENDING", "待分配"), "未分配", "进行中"]
        pending_tasks = [task for task in tasks if task.get('status') in pending_status_list]
        
        print(f"📋 任务筛选结果：")
        print(f"   总任务数: {len(tasks)}")
        print(f"   待提交任务数: {len(pending_tasks)}")
        print(f"   筛选条件: {pending_status_list}")
        
        if not pending_tasks:
            # 显示所有任务的状态用于调试
            print("🔍 所有任务状态详情：")
            for i, task in enumerate(tasks, 1):
                task_name = task.get('name', task.get('task_name', '未命名'))
                print(f"   {i}. {task_name} - 状态: '{task.get('status', '未知')}'")
            QMessageBox.information(self, "提示", f"没有可提交的任务\n总任务数: {len(tasks)}\n待提交任务数: {len(pending_tasks)}")
            return
            
        # 显示任务选择对话框
        dialog = TaskSelectionDialog(tasks, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_tasks = dialog.get_selected_tasks()
            if selected_tasks:
                self.start_task_submission(selected_tasks)
                
    @pyqtSlot(str)
    def on_task_list_error(self, error_message):
        """获取任务列表失败"""
        self.status_label.setText("获取任务列表失败")
        QMessageBox.warning(self, "错误", f"获取任务列表失败：{error_message}")
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    def start_task_submission(self, selected_tasks):
        """开始提交选中的任务"""
        # 创建任务提交工作线程
        self.task_worker = TaskSubmissionWorker(selected_tasks)
        
        # 连接信号
        self.task_worker.progress_updated.connect(self.on_task_progress_updated)
        self.task_worker.task_completed.connect(self.on_task_completed)
        self.task_worker.error_occurred.connect(self.on_task_error)
        
        # 开始任务提交
        self.status_label.setText("正在准备任务提交...")
        self.task_worker.start()
        
    @pyqtSlot(str)
    def on_task_progress_updated(self, message):
        """任务进度更新回调"""
        self.status_label.setText(message)
        print(f"任务进度: {message}")
        
    @pyqtSlot(str) 
    def on_task_completed(self, message):
        """任务完成回调"""
        self.status_label.setText(message)
        print(f"任务完成: {message}")
        
        # 显示完成对话框
        QMessageBox.information(self, "任务提交完成", message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    @pyqtSlot(str)
    def on_task_error(self, error_message):
        """任务错误回调"""
        self.status_label.setText(f"任务提交失败")
        print(f"任务错误: {error_message}")
        
        # 显示错误对话框
        QMessageBox.warning(self, "任务提交失败", error_message)
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
    
    @pyqtSlot(list)
    def on_notification_tasks_loaded(self, tasks):
        """任务通知获取任务列表完成 - 专门用于任务通知"""
        self.status_label.setText("系统运行正常")
        
        if not tasks:
            print("⚠️ 没有从API获取到任务，显示暂无任务通知")
            self.show_no_task_notification()
            return
            
        # 过滤出待提交的任务 - 使用与提交任务相同的筛选条件
        pending_status_list = [api_config.TASK_STATUS.get("PENDING", "待分配"), "未分配", "进行中"]
        pending_tasks = [task for task in tasks if task.get('status') in pending_status_list]
        
        print(f"📋 API任务筛选结果：")
        print(f"   总任务数: {len(tasks)}")
        print(f"   待处理任务数: {len(pending_tasks)}")
        print(f"   筛选条件: {pending_status_list}")
        
        if pending_tasks:
            print(f"🎯 发现 {len(pending_tasks)} 个待处理任务，显示通知")
            self.show_task_notification(tasks, pending_tasks)
        else:
            # 显示所有任务的状态用于调试
            print("🔍 所有任务状态详情：")
            for i, task in enumerate(tasks, 1):
                task_name = task.get('name', task.get('task_name', '未命名'))
                print(f"   {i}. {task_name} - 状态: '{task.get('status', '未知')}'")
            print("⚠️ 没有待处理任务，显示暂无任务通知")
            self.show_no_task_notification()
                
    @pyqtSlot(str)
    def on_notification_task_list_error(self, error_message):
        """任务通知获取任务列表失败 - 专门用于任务通知"""
        self.status_label.setText("获取任务列表失败")
        print(f"❌ 任务通知获取任务列表失败：{error_message}")
        
        # 显示暂无任务通知，而不是错误弹窗
        print("🔔 因获取任务失败，显示暂无任务通知")
        self.show_no_task_notification()
        
        # 2秒后恢复状态显示
        QTimer.singleShot(2000, lambda: self.status_label.setText("系统运行正常"))
        
    def exit_application(self):
        """退出应用程序并启动全屏浏览器"""
        print("开始退出desktop_manager应用...")
        
        # 再次确保JSON文件被清理（双重保险）
        self.cleanup_json_files()
        
        # 步骤1：清理资源 - 关闭所有子窗口
        self.close_all_windows()
        
        # 步骤2：启动独立过渡页面，然后启动全屏浏览器
        self.start_independent_transition_and_browser()
        
        # 步骤3：退出desktop_manager应用
        QTimer.singleShot(100, QApplication.quit)
    
    def close_all_windows(self):
        """关闭所有子窗口"""
        print("正在清理资源和关闭所有子窗口...")
        
        # 关闭所有子窗口
        if self.pet_widget:
            self.pet_widget.close()
            print("宠物窗口已关闭")
        if self.chat_widget:
            self.chat_widget.close()
            print("AI宠物聊天窗口已关闭")
        if self.online_chat_widget:
            self.online_chat_widget.close()
            print("在线聊天窗口已关闭")
        if self.tuopo_widget:
            self.tuopo_widget.close()
            print("拓扑图窗口已关闭")
        if self.transition_page:
            self.transition_page.close()
            print("过渡页面已关闭")
            
        print("所有子窗口清理完成")
        
    def start_independent_transition_and_browser(self):
        """启动增强过渡页面（包含桌面图标还原），然后启动全屏浏览器"""
        try:
            # 优先查找增强过渡页面脚本
            enhanced_script_path = os.path.join(os.path.dirname(__file__), "enhanced_transition_screen.py")
            if not os.path.exists(enhanced_script_path):
                enhanced_script_path = "enhanced_transition_screen.py"
            
            if os.path.exists(enhanced_script_path):
                # 启动增强过渡页面进程（包含桌面图标还原）
                subprocess.Popen([
                    sys.executable, 
                    enhanced_script_path,
                    "正在关闭云桌面...",
                    "5000",  # 增加持续时间，因为需要执行图标还原
                    "--restore"
                ])
                print("增强过渡页面已启动，将执行桌面文件还原并启动全屏浏览器")
                return
            
            # 备用：查找原始过渡页面脚本
            script_path = os.path.join(os.path.dirname(__file__), "independent_transition.py")
            if not os.path.exists(script_path):
                script_path = "independent_transition.py"
            
            if not os.path.exists(script_path):
                print("警告：找不到任何过渡页面脚本，直接启动全屏浏览器")
                self.launch_fullscreen_browser_directly()
                return
            
            # 启动原始过渡页面进程
            # 传递参数：信息文本、持续时间、启动浏览器标志
            subprocess.Popen([
                sys.executable, 
                script_path,
                "正在关闭云桌面...",
                "3000",
                "--launch-browser"
            ])
            print("备用过渡页面已启动，将在3秒后启动全屏浏览器")
            
        except Exception as e:
            print(f"启动过渡页面失败: {str(e)}")
            print("回退到直接启动全屏浏览器")
            self.launch_fullscreen_browser_directly()
    
    def launch_fullscreen_browser_directly(self):
        """直接启动全屏浏览器（备用方案）"""
        try:
            subprocess.Popen([sys.executable, "fullscreen_browser.py"])
            print("全屏浏览器已直接启动")
        except Exception as e:
            print(f"启动全屏浏览器失败: {str(e)}")
        
    def launch_fullscreen_and_exit(self):
        """启动全屏浏览器并关闭桌面管理器 - 已弃用，保留兼容性"""
        print("注意：launch_fullscreen_and_exit方法已弃用，请使用新的退出流程")
        self.exit_application()
        
    def close_all_and_exit(self):
        """关闭所有窗口并退出 - 已弃用，保留兼容性"""
        print("注意：close_all_and_exit方法已弃用，请使用新的退出流程")
        self.exit_application()
        
    def mousePressEvent(self, event):
        """鼠标按下事件 - 支持拖拽"""
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽移动"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            new_pos = event.globalPos() - self.drag_pos
            # 限制在屏幕顶部区域
            desktop = QDesktopWidget()
            screen_rect = desktop.availableGeometry()
            if new_pos.y() < 0:
                new_pos.setY(0)
            elif new_pos.y() > 100:  # 限制在顶部100像素内
                new_pos.setY(100)
            self.move(new_pos)
            
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Escape:
            self.exit_application()
        elif event.key() == Qt.Key_F1:
            self.show_pet()
        elif event.key() == Qt.Key_F2:
            self.show_chat()
        elif event.key() == Qt.Key_F3:
            self.show_tuopo()
        super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """关闭事件"""
        try:
            print("🔔 Desktop Manager 正在关闭，开始清理JSON文件...")
            
            # 立即清理JSON文件
            self.cleanup_json_files()
            
            # 停止数据接收器
            if hasattr(self, 'data_receiver') and self.data_receiver:
                self.data_receiver.stop_all_receivers()
            
            # 停止简单文件监听器（如果存在）
            if hasattr(self, 'file_watcher') and self.file_watcher:
                self.file_watcher.deleteLater()
            
            # 清理任务工作线程
            if self.task_worker and self.task_worker.isRunning():
                self.task_worker.terminate()
                self.task_worker.wait()
                
            # 清理任务列表工作线程
            if self.task_list_worker and self.task_list_worker.isRunning():
                self.task_list_worker.terminate()
                self.task_list_worker.wait()
                
            # 清理设备工作线程
            if self.device_worker and self.device_worker.isRunning():
                self.device_worker.terminate()
                self.device_worker.wait()
                
            # 清理批量设备工作线程
            if self.batch_device_worker and self.batch_device_worker.isRunning():
                self.batch_device_worker.terminate()
                self.batch_device_worker.wait()
                
            # 关闭设备对话框
            if self.device_dialog:
                self.device_dialog.close()
            
            print("✅ 所有资源已清理")
            
        except Exception as e:
            print(f"❌ 清理资源时出错: {str(e)}")
            
        # 阻止默认的关闭行为
        event.ignore()
        # 调用退出应用程序方法，显示过渡页面并启动全屏浏览器
        self.exit_application()
    
    def cleanup_json_files(self):
        """清理JSON文件"""
        try:
            json_files = [
                'received_data.json',
                'received_tasks.json'
            ]
            
            deleted_files = []
            for file_path in json_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                        print(f"✅ 已删除JSON文件: {file_path}")
                    except Exception as e:
                        print(f"❌ 删除文件 {file_path} 失败: {str(e)}")
            
            # 清理备份文件（.notified_* 结尾的文件）
            current_dir = os.getcwd()
            for filename in os.listdir(current_dir):
                if filename.startswith('received_tasks.json.notified_'):
                    try:
                        backup_path = os.path.join(current_dir, filename)
                        os.remove(backup_path)
                        deleted_files.append(filename)
                        print(f"✅ 已删除备份文件: {filename}")
                    except Exception as e:
                        print(f"❌ 删除备份文件 {filename} 失败: {str(e)}")
            
            if deleted_files:
                print(f"🧹 JSON文件清理完成，共删除 {len(deleted_files)} 个文件")
            else:
                print("🧹 没有找到需要清理的JSON文件")
                
        except Exception as e:
            print(f"❌ 清理JSON文件时出错: {str(e)}")
    
    def check_and_notify_tasks(self):
        """检查是否有待处理的任务并弹出通知 - 与提交任务获取方式保持一致"""
        try:
            print("⏰ 定时器触发：正在检查是否有待处理的智能任务...")
            print(f"   当前工作目录: {os.getcwd()}")
            
            # 显示加载状态
            self.status_label.setText("正在智能获取任务列表...")
            
            # 使用与提交任务相同的获取方式 - 首先检查是否有从前端接收到的任务数据
            received_tasks = self.load_received_tasks()
            if received_tasks:
                print(f"✓ 使用从前端接收到的智能任务数据，共 {len(received_tasks)} 个任务")
                self.status_label.setText(f"已加载 {len(received_tasks)} 个智能推荐任务")
                
                # 过滤出待提交的任务 - 使用与提交任务相同的筛选条件
                pending_status_list = [api_config.TASK_STATUS.get("PENDING", "待分配"), "未分配", "进行中"]
                pending_tasks = [task for task in received_tasks if task.get('status') in pending_status_list]
                
                print(f"📋 任务筛选结果：")
                print(f"   总任务数: {len(received_tasks)}")
                print(f"   待处理任务数: {len(pending_tasks)}")
                print(f"   筛选条件: {pending_status_list}")
                
                if pending_tasks:
                    print(f"🎯 发现 {len(pending_tasks)} 个待处理的智能推荐任务，准备弹出通知")
                    self.show_task_notification(received_tasks, pending_tasks)
                else:
                    # 显示所有任务的状态用于调试
                    print("🔍 所有任务状态详情：")
                    for i, task in enumerate(received_tasks, 1):
                        task_name = task.get('name', task.get('task_name', '未命名'))
                        print(f"   {i}. {task_name} - 状态: '{task.get('status', '未知')}'")
                    print("⚠️ 没有待处理任务，弹出暂无任务通知")
                    self.show_no_task_notification()
                return
            
            print("⚠ 未找到前端智能推荐任务，回退到API获取任务列表...")
            self.status_label.setText("正在从服务器获取任务列表...")
            
            # 创建任务列表获取工作线程 - 与提交任务保持一致
            self.task_list_worker = TaskListWorker()
            
            # 连接信号 - 使用专门的通知处理方法
            self.task_list_worker.tasks_loaded.connect(self.on_notification_tasks_loaded)
            self.task_list_worker.error_occurred.connect(self.on_notification_task_list_error)
            
            # 开始获取任务列表
            self.task_list_worker.start()
            
        except Exception as e:
            print(f"❌ 检查任务时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_no_task_notification()

    def show_no_task_notification(self):
        """弹出暂无任务的通知弹窗"""
        try:
            print("🔔 准备显示暂无任务通知弹窗...")
            # 确保弹窗显示在最前面
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("任务通知")
            msg_box.setText("暂无待处理任务！\n\n系统已启动，当前没有需要处理的任务。")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # 设置窗口属性，确保显示在最前面
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
            
            print("🔔 正在显示暂无任务通知弹窗...")
            result = msg_box.exec_()
            print(f"🔔 弹窗已关闭，返回值: {result}")
            
            self.status_label.setText("暂无待处理任务")
        except Exception as e:
            print(f"❌ 显示暂无任务通知时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.status_label.setText("暂无待处理任务")
    

    
    def show_task_notification(self, all_tasks, pending_tasks):
        """显示任务通知弹窗 - 根据配置决定是否自动打开任务提交对话框"""
        try:
            # 获取用户信息用于日志显示
            user_info = None
            try:
                with open('received_tasks.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user_info = data.get('user_info', {})
            except:
                pass
            
            username = "用户"
            role_name = "未知角色"
            if user_info:
                username = user_info.get('user', {}).get('username', '用户')
                role_name = user_info.get('selectedRole', {}).get('label', '未知角色')
            
            print(f"🎯 智能任务推荐通知")
            print(f"👤 用户: {username}")
            print(f"🔧 角色: {role_name}")
            print(f"📋 发现 {len(pending_tasks)} 个智能推荐任务")
            
            # 列出前几个任务信息
            for i, task in enumerate(pending_tasks[:5], 1):
                task_name = task.get('name', task.get('task_name', '未命名任务'))  # 支持两种字段名
                task_type = task.get('type', task.get('task_type', '未知类型'))   # 支持两种字段名
                print(f"   {i}. {task_name} ({task_type})")
            
            if len(pending_tasks) > 5:
                print(f"   ... 还有 {len(pending_tasks) - 5} 个任务")
            
            if self.auto_open_task_dialog:
                # 自动打开任务提交对话框
                print("🚀 自动打开任务提交对话框...")
                self.status_label.setText(f"发现 {len(pending_tasks)} 个新任务，正在打开任务管理...")
                
                # 标记任务已通知
                self.mark_tasks_as_notified()
                
                # 延迟一下再显示任务列表，让初始化完成
                QTimer.singleShot(500, lambda: self.on_tasks_loaded(all_tasks))
            else:
                # 显示传统的通知弹窗让用户选择
                print("💡 显示任务通知弹窗，等待用户选择...")
                self.status_label.setText(f"发现 {len(pending_tasks)} 个新任务")
                self._show_traditional_notification(all_tasks, pending_tasks, username, role_name)
                
        except Exception as e:
            print(f"显示任务通知时出错: {str(e)}")
            # 如果通知失败，仍然可以通过按钮查看任务
            self.status_label.setText("有新任务可用")
    
    def _show_traditional_notification(self, all_tasks, pending_tasks, username, role_name):
        """显示传统的任务通知弹窗"""
        try:
            # 构建通知消息
            message = f"🎯 智能任务推荐通知\n\n"
            message += f"👤 用户: {username}\n"
            message += f"🔧 角色: {role_name}\n"
            message += f"📋 发现 {len(pending_tasks)} 个智能推荐任务\n\n"
            
            # 显示前3个任务的简要信息
            for i, task in enumerate(pending_tasks[:3], 1):
                task_name = task.get('name', task.get('task_name', '未命名任务'))  # 支持两种字段名
                task_type = task.get('type', task.get('task_type', '未知类型'))   # 支持两种字段名
                message += f"{i}. {task_name} ({task_type})\n"
            
            if len(pending_tasks) > 3:
                message += f"... 还有 {len(pending_tasks) - 3} 个任务\n"
            
            message += f"\n💡 这些任务是根据您的角色智能推荐的，点击确定查看详情。"
            
            # 创建自定义消息框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("🚀 智能任务推荐")
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Information)
            
            # 自定义按钮
            view_tasks_btn = msg_box.addButton("📋 查看任务列表", QMessageBox.ActionRole)
            later_btn = msg_box.addButton("⏰ 稍后处理", QMessageBox.RejectRole)
            
            # 设置样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f8f9fa;
                    color: #2d3436;
                    font-family: '微软雅黑';
                    font-size: 12px;
                }
                QMessageBox QLabel {
                    color: #2d3436;
                    font-size: 12px;
                    padding: 10px;
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #667eea, stop:1 #5a6fd8);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 8px 16px;
                    margin: 4px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5a6fd8, stop:1 #4c63d2);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4c63d2, stop:1 #3b4ec7);
                }
            """)
            
            # 执行对话框并处理结果
            msg_box.exec_()
            
            if msg_box.clickedButton() == view_tasks_btn:
                print("用户选择查看任务列表")
                # 标记任务已通知
                self.mark_tasks_as_notified()
                # 延迟一下再显示任务列表，让通知消息框完全关闭
                QTimer.singleShot(300, lambda: self.on_tasks_loaded(all_tasks))
            else:
                print("用户选择稍后处理任务")
                # 即使选择稍后处理，也标记为已通知，避免重复弹窗
                self.mark_tasks_as_notified()
                self.status_label.setText("任务待处理中...")
                # 3秒后恢复正常状态
                QTimer.singleShot(3000, lambda: self.status_label.setText("系统运行正常"))
                
        except Exception as e:
            print(f"显示传统任务通知时出错: {str(e)}")
            self.status_label.setText("有新任务可用")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("桌面管理器")
    app.setQuitOnLastWindowClosed(True)
    
    # 检查命令行参数
    auto_open_tasks = False
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--auto-open-tasks":
                auto_open_tasks = True
                print("🚀 检测到命令行参数：--auto-open-tasks，将自动打开任务提交对话框")
                break
    
    # 创建并显示桌面管理器
    desktop_manager = DesktopManager()
    
    # 如果有命令行参数，覆盖默认设置
    if auto_open_tasks:
        desktop_manager.auto_open_task_dialog = True
        print("✅ 已启用自动打开任务提交对话框")
    
    desktop_manager.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 