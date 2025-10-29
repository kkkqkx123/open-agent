"""基础状态管理器

提供基本的状态管理功能，作为其他状态管理器的基类。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import copy

from .interface import IStateManager


class BaseStateManager(IStateManager):
    """基础状态管理器，提供基本的状态管理功能"""
    
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态
        
        Args:
            state_id: 状态ID
            initial_state: 初始状态
            
        Returns:
            创建的状态副本
        """
        state_copy = copy.deepcopy(initial_state) if initial_state else {}
        self._states[state_id] = state_copy
        return state_copy
    
    def update_state(self, state_id: str, current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态
        
        Args:
            state_id: 状态ID
            current_state: 当前状态
            updates: 更新内容
            
        Returns:
            更新后的状态
        """
        new_state = copy.deepcopy(current_state)
        new_state.update(updates)
        self._states[state_id] = new_state
        return new_state
    
    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态对象，如果不存在则返回None
        """
        if state_id in self._states:
            return copy.deepcopy(self._states[state_id])
        return None
    
    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个状态的差异
        
        Args:
            state1: 第一个状态
            state2: 第二个状态
            
        Returns:
            差异字典
        """
        differences = {}
        all_keys = set(state1.keys()) | set(state2.keys())
        
        for key in all_keys:
            value1 = state1.get(key)
            value2 = state2.get(key)
            
            if value1 != value2:
                differences[key] = {
                    "old_value": value1,
                    "new_value": value2,
                    "type_changed": type(value1) != type(value2)
                }
        
        return differences
    
    def serialize_state(self, state: Dict[str, Any]) -> str:
        """序列化状态
        
        Args:
            state: 要序列化的状态
            
        Returns:
            序列化后的字符串
        """
        import json
        return json.dumps(state, ensure_ascii=False, default=str)
    
    def deserialize_state(self, serialized_data: str) -> Dict[str, Any]:
        """反序列化状态
        
        Args:
            serialized_data: 序列化的数据
            
        Returns:
            反序列化后的状态
        """
        import json
        return json.loads(serialized_data)