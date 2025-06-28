#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime

class TokenManager:
    """Token管理器 - 负责从JSON配置文件中获取和管理token"""
    
    def __init__(self, config_file: str = "received_data.json"):
        """
        初始化Token管理器
        
        Args:
            config_file: 配置文件路径，默认为 received_data.json
        """
        self.config_file = config_file
        self.token_cache = {}
        self.cache_timestamp = 0
        self.cache_duration = 300  # 缓存5分钟
        
    def get_token(self, refresh_cache: bool = False) -> Optional[str]:
        """
        从JSON文件中获取token
        
        Args:
            refresh_cache: 是否强制刷新缓存
            
        Returns:
            token字符串，如果获取失败返回None
        """
        try:
            # 检查缓存是否有效
            current_time = time.time()
            if (not refresh_cache and 
                self.token_cache and 
                current_time - self.cache_timestamp < self.cache_duration):
                return self.token_cache.get('token')
            
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file):
                print(f"配置文件不存在: {self.config_file}")
                return None
            
            # 读取配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 尝试从不同的路径获取token
            token = None
            
            # 方法1: 从sync_info.operator.token获取
            if 'sync_info' in data and 'operator' in data['sync_info']:
                token = data['sync_info']['operator'].get('token')
            
            # 方法2: 从根级别的token字段获取
            if not token and 'token' in data:
                token = data['token']
            
            # 方法3: 从user对象中获取
            if not token and 'user' in data and 'token' in data['user']:
                token = data['user']['token']
            
            # 方法4: 从users数组第一个用户获取
            if not token and 'users' in data and isinstance(data['users'], list) and len(data['users']) > 0:
                first_user = data['users'][0]
                if 'token' in first_user:
                    token = first_user['token']
            
            # 更新缓存
            if token:
                self.token_cache = {
                    'token': token,
                    'username': self._get_username_from_data(data),
                    'user_id': self._get_user_id_from_data(data),
                    'role': self._get_role_from_data(data),
                    'type': self._get_type_from_data(data)
                }
                self.cache_timestamp = current_time
                print(f"Token获取成功，用户: {self.token_cache.get('username', 'Unknown')}")
            else:
                print("未能从配置文件中找到token")
            
            return token
            
        except Exception as e:
            print(f"获取token时出错: {str(e)}")
            return None
    
    def _get_username_from_data(self, data: Dict[str, Any]) -> str:
        """从配置数据中提取用户名"""
        # 从sync_info.operator获取
        if 'sync_info' in data and 'operator' in data['sync_info']:
            username = data['sync_info']['operator'].get('username')
            if username:
                return username
        
        # 从users数组获取
        if 'users' in data and isinstance(data['users'], list) and len(data['users']) > 0:
            username = data['users'][0].get('username')
            if username:
                return username
        
        # 从user对象获取
        if 'user' in data and 'username' in data['user']:
            return data['user']['username']
        
        return "Unknown"
    
    def _get_user_id_from_data(self, data: Dict[str, Any]) -> Optional[int]:
        """从配置数据中提取用户ID"""
        # 从sync_info.operator获取
        if 'sync_info' in data and 'operator' in data['sync_info']:
            user_id = data['sync_info']['operator'].get('user_id')
            if user_id:
                return user_id
        
        # 从users数组获取
        if 'users' in data and isinstance(data['users'], list) and len(data['users']) > 0:
            user_id = data['users'][0].get('id')
            if user_id:
                return user_id
        
        # 从user对象获取
        if 'user' in data and 'id' in data['user']:
            return data['user']['id']
        
        return None
    
    def _get_role_from_data(self, data: Dict[str, Any]) -> str:
        """从配置数据中提取用户角色"""
        # 从sync_info.operator获取
        if 'sync_info' in data and 'operator' in data['sync_info']:
            role = data['sync_info']['operator'].get('operator_role')
            if role:
                return role
        
        # 从users数组获取
        if 'users' in data and isinstance(data['users'], list) and len(data['users']) > 0:
            role = data['users'][0].get('role')
            if role:
                return role
        
        # 从user对象获取
        if 'user' in data and 'role' in data['user']:
            return data['user']['role']
        
        return "未知角色"
    
    def _get_type_from_data(self, data: Dict[str, Any]) -> str:
        """从配置数据中提取用户类型"""
        # 从sync_info.operator获取
        if 'sync_info' in data and 'operator' in data['sync_info']:
            user_type = data['sync_info']['operator'].get('operator_type')
            if user_type:
                return user_type
        
        # 从users数组获取
        if 'users' in data and isinstance(data['users'], list) and len(data['users']) > 0:
            user_type = data['users'][0].get('type')
            if user_type:
                return user_type
        
        # 从user对象获取
        if 'user' in data and 'type' in data['user']:
            return data['user']['type']
        
        return "未知类型"
    
    def get_user_info(self, refresh_cache: bool = False) -> Dict[str, Any]:
        """
        获取完整的用户信息
        
        Args:
            refresh_cache: 是否强制刷新缓存
            
        Returns:
            包含用户信息的字典
        """
        # 确保获取最新的token和用户信息
        token = self.get_token(refresh_cache)
        
        if not token:
            return {}
        
        return {
            'token': token,
            'username': self.token_cache.get('username', 'Unknown'),
            'user_id': self.token_cache.get('user_id'),
            'role': self.token_cache.get('role', '未知角色'),
            'type': self.token_cache.get('type', '未知类型'),
            'timestamp': datetime.now().isoformat()
        }
    
    def is_token_valid(self) -> bool:
        """
        检查token是否有效（简单的格式验证）
        
        Returns:
            True如果token格式看起来有效，否则False
        """
        token = self.get_token()
        if not token:
            return False
        
        # JWT token通常由三部分组成，用.分隔
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        # 检查每部分是否为Base64编码
        try:
            import base64
            for part in parts:
                # 添加padding
                missing_padding = len(part) % 4
                if missing_padding:
                    part += '=' * (4 - missing_padding)
                base64.b64decode(part, validate=True)
            return True
        except Exception:
            return False
    
    def get_authorization_header(self) -> Dict[str, str]:
        """
        获取HTTP Authorization头部
        
        Returns:
            包含Authorization头部的字典
        """
        token = self.get_token()
        if not token:
            return {}
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def refresh_token_from_file(self) -> bool:
        """
        强制从文件刷新token
        
        Returns:
            True如果刷新成功，否则False
        """
        token = self.get_token(refresh_cache=True)
        return token is not None
    
    def clear_cache(self):
        """清除token缓存"""
        self.token_cache = {}
        self.cache_timestamp = 0
        print("Token缓存已清除")
    
    def set_config_file(self, config_file: str):
        """
        设置配置文件路径
        
        Args:
            config_file: 新的配置文件路径
        """
        self.config_file = config_file
        self.clear_cache()
        print(f"配置文件路径已更新为: {config_file}")
    
    def export_token_info(self) -> Dict[str, Any]:
        """
        导出token信息（用于调试）
        
        Returns:
            包含token信息的字典
        """
        user_info = self.get_user_info()
        return {
            'config_file': self.config_file,
            'cache_duration': self.cache_duration,
            'cache_timestamp': self.cache_timestamp,
            'is_cached': bool(self.token_cache),
            'is_token_valid': self.is_token_valid(),
            'user_info': user_info
        }


# 使用示例和测试
if __name__ == "__main__":
    # 创建Token管理器实例
    token_manager = TokenManager()
    
    print("=== Token管理器测试 ===")
    print(f"配置文件: {token_manager.config_file}")
    
    # 获取token
    token = token_manager.get_token()
    if token:
        print(f"Token获取成功: {token[:20]}...")
        print(f"Token是否有效: {token_manager.is_token_valid()}")
    else:
        print("Token获取失败")
    
    # 获取用户信息
    print("\n=== 用户信息 ===")
    user_info = token_manager.get_user_info()
    for key, value in user_info.items():
        if key == 'token':
            print(f"{key}: {value[:20]}..." if value else f"{key}: {value}")
        else:
            print(f"{key}: {value}")
    
    # 获取Authorization头部
    print("\n=== Authorization头部 ===")
    headers = token_manager.get_authorization_header()
    for key, value in headers.items():
        if key == 'Authorization':
            print(f"{key}: {value[:30]}..." if len(value) > 30 else f"{key}: {value}")
        else:
            print(f"{key}: {value}")
    
    # 导出详细信息
    print("\n=== 详细信息 ===")
    info = token_manager.export_token_info()
    for key, value in info.items():
        if key == 'user_info':
            print(f"{key}:")
            for k, v in value.items():
                if k == 'token':
                    print(f"  {k}: {v[:20]}..." if v else f"  {k}: {v}")
                else:
                    print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}") 