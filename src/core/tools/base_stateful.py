"""
有状态工具基类实现

定义了有状态工具的基础抽象类，提供状态管理功能。
"""
import time
import uuid
from typing import Any, Dict, Optional, Union
from abc import ABC, abstractmethod

from .base import BaseTool
from src.interfaces.tool.state_manager import IToolStateManager, StateType


class StatefulBaseTool(BaseTool, ABC):
    """状态感知工具基类"""
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any], 
                 state_manager: IToolStateManager, config: Any):
        """初始化状态感知工具"""
        super().__init__(name, description, parameters_schema)
        self.state_manager = state_manager
        self.config = config
        self._context_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._initialized = False
    
    def initialize_context(self, session_id: Optional[str] = None) -> str:
        """初始化工具上下文"""
        if self._initialized and self._context_id:
            return self._context_id
        
        # 生成或使用提供的会话ID
        self._session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        
        # 创建上下文ID
        self._context_id = f"{self._session_id}_{self.name}_{uuid.uuid4().hex[:8]}"
        
        # 在状态管理器中创建上下文
        self.state_manager.create_context(self._context_id, self.__class__.__name__)
        
        # 初始化各种状态
        self._initialize_connection_state()
        self._initialize_session_state()
        self._initialize_business_state()
        
        self._initialized = True
        return self._context_id
    
    def _initialize_connection_state(self) -> None:
        """初始化连接状态"""
        if not self._context_id:
            return
        initial_state = {
            'active': False,
            'created_at': time.time(),
            'last_used': time.time(),
            'error_count': 0,
            'last_error': None
        }
        self.state_manager.set_state(self._context_id, StateType.CONNECTION, initial_state)
    
    def _initialize_session_state(self) -> None:
        """初始化会话状态"""
        if not self._context_id:
            return
        initial_state = {
            'session_id': self._session_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'user_id': None,
            'permissions': [],
            'auth_token': None
        }
        self.state_manager.set_state(self._context_id, StateType.SESSION, initial_state)
    
    def _initialize_business_state(self) -> None:
        """初始化业务状态"""
        if not self._context_id:
            return
        initial_state = {
            'created_at': time.time(),
            'version': 1,
            'data': {},
            'history': [],
            'metadata': {}
        }
        self.state_manager.set_state(self._context_id, StateType.BUSINESS, initial_state)
    
    def get_connection_state(self) -> Optional[Dict[str, Any]]:
        """获取连接状态"""
        if not self._context_id:
            return None
        return self.state_manager.get_state(self._context_id, StateType.CONNECTION)
    
    def get_session_state(self) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if not self._context_id:
            return None
        return self.state_manager.get_state(self._context_id, StateType.SESSION)
    
    def get_business_state(self) -> Optional[Dict[str, Any]]:
        """获取业务状态"""
        if not self._context_id:
            return None
        return self.state_manager.get_state(self._context_id, StateType.BUSINESS)
    
    def update_connection_state(self, updates: Dict[str, Any]) -> bool:
        """更新连接状态"""
        if not self._context_id:
            return False
        
        # 添加最后使用时间
        updates['last_used'] = time.time()
        return self.state_manager.update_state(self._context_id, StateType.CONNECTION, updates)
    
    def update_session_state(self, updates: Dict[str, Any]) -> bool:
        """更新会话状态"""
        if not self._context_id:
            return False
        
        # 添加最后活动时间
        updates['last_activity'] = time.time()
        return self.state_manager.update_state(self._context_id, StateType.SESSION, updates)
    
    def update_business_state(self, updates: Dict[str, Any]) -> bool:
        """更新业务状态"""
        if not self._context_id:
            return False
        
        # 获取当前状态
        current_state = self.get_business_state()
        if not current_state:
            return False
        
        # 更新数据和版本
        if 'data' in updates:
            current_state['data'].update(updates.pop('data'))
        
        # 添加到历史记录
        if current_state.get('history') is not None:
            current_state['history'].append({
                'timestamp': time.time(),
                'updates': updates,
                'version': current_state.get('version', 1)
            })
            
            # 限制历史记录大小
            max_history = self.config.get('business_config', {}).get('max_history_size', 1000)
            if len(current_state['history']) > max_history:
                current_state['history'] = current_state['history'][-max_history:]
        
        # 更新版本
        current_state['version'] = current_state.get('version', 1) + 1
        
        # 应用其他更新
        current_state.update(updates)
        
        return self.state_manager.set_state(self._context_id, StateType.BUSINESS, current_state)
    
    def add_to_history(self, event_type: str, data: Dict[str, Any]) -> bool:
        """添加事件到历史记录"""
        if not self._context_id:
            return False
        
        current_state = self.get_business_state()
        if not current_state or 'history' not in current_state:
            return False
        
        history_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'data': data,
            'version': current_state.get('version', 1)
        }
        
        current_state['history'].append(history_entry)
        
        # 限制历史记录大小
        max_history = self.config.get('business_config', {}).get('max_history_size', 1000)
        if len(current_state['history']) > max_history:
            current_state['history'] = current_state['history'][-max_history:]
        
        return self.state_manager.update_state(self._context_id, StateType.BUSINESS, {
            'history': current_state['history']
        })
    
    def get_context_info(self) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        if not self._context_id:
            return None
        return self.state_manager.get_context_info(self._context_id)
    
    def cleanup_context(self) -> bool:
        """清理上下文"""
        if not self._context_id:
            return False
        
        result = self.state_manager.cleanup_context(self._context_id)
        self._context_id = None
        self._session_id = None
        self._initialized = False
        return result
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    @property
    def context_id(self) -> Optional[str]:
        """获取上下文ID"""
        return self._context_id
    
    @property
    def session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self._session_id
    
    def __del__(self):
        """析构函数"""
        if self._initialized:
            self.cleanup_context()