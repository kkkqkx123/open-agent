"""
内存状态管理器实现
"""

import threading
import uuid
from typing import Dict, List, Optional, Any
from collections import defaultdict
import time

from src.interfaces.tool.state_manager import IToolStateManager, StateType, StateEntry


class MemoryStateManager(IToolStateManager):
    """内存状态管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存状态管理器"""
        self.config = config
        self._states: Dict[str, Dict[StateType, StateEntry]] = defaultdict(dict)
        self._lock = threading.RLock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # 启动清理线程
        if config.get('auto_cleanup', True):
            self._start_cleanup_thread()
    
    def create_context(self, context_id: str, tool_type: str) -> str:
        """创建工具上下文"""
        with self._lock:
            # 生成唯一的状态ID
            state_id = f"{context_id}_{uuid.uuid4().hex[:8]}"
            
            # 初始化上下文状态
            if context_id not in self._states:
                self._states[context_id] = {}
            
            return state_id
    
    def get_state(self, context_id: str, state_type: StateType) -> Optional[Dict[str, Any]]:
        """获取状态数据"""
        with self._lock:
            if context_id not in self._states:
                return None
            
            state_entry = self._states[context_id].get(state_type)
            if not state_entry:
                return None
            
            # 检查是否过期
            if state_entry.is_expired():
                del self._states[context_id][state_type]
                return None
            
            return state_entry.data.copy()
    
    def set_state(self, context_id: str, state_type: StateType, state_data: Dict[str, Any], 
                  ttl: Optional[int] = None) -> bool:
        """设置状态数据"""
        with self._lock:
            now = time.time()
            expires_at = now + ttl if ttl else None
            
            state_entry = StateEntry(
                state_id=f"{context_id}_{state_type.value}_{uuid.uuid4().hex[:8]}",
                context_id=context_id,
                state_type=state_type,
                data=state_data.copy(),
                created_at=now,
                updated_at=now,
                expires_at=expires_at
            )
            
            self._states[context_id][state_type] = state_entry
            return True
    
    def update_state(self, context_id: str, state_type: StateType, updates: Dict[str, Any]) -> bool:
        """更新状态数据"""
        with self._lock:
            if context_id not in self._states:
                return False
            
            state_entry = self._states[context_id].get(state_type)
            if not state_entry:
                return False
            
            # 检查是否过期
            if state_entry.is_expired():
                del self._states[context_id][state_type]
                return False
            
            # 更新数据
            state_entry.data.update(updates)
            state_entry.updated_at = time.time()
            state_entry.version += 1
            
            return True
    
    def delete_state(self, context_id: str, state_type: StateType) -> bool:
        """删除状态"""
        with self._lock:
            if context_id not in self._states:
                return False
            
            if state_type in self._states[context_id]:
                del self._states[context_id][state_type]
                return True
            
            return False
    
    def cleanup_context(self, context_id: str) -> bool:
        """清理上下文"""
        with self._lock:
            if context_id in self._states:
                del self._states[context_id]
                return True
            return False
    
    def list_contexts(self, tool_type: Optional[str] = None) -> List[str]:
        """列出上下文"""
        with self._lock:
            contexts = list(self._states.keys())
            
            if tool_type:
                # 过滤特定工具类型的上下文
                filtered_contexts = []
                for context_id in contexts:
                    if tool_type in context_id:
                        filtered_contexts.append(context_id)
                return filtered_contexts
            
            return contexts
    
    def get_context_info(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文信息"""
        with self._lock:
            if context_id not in self._states:
                return None
            
            states = self._states[context_id]
            info = {
                'context_id': context_id,
                'state_count': len(states),
                'states': {}
            }
            
            for state_type, state_entry in states.items():
                info['states'][state_type.value] = {
                    'state_id': state_entry.state_id,
                    'created_at': state_entry.created_at,
                    'updated_at': state_entry.updated_at,
                    'expires_at': state_entry.expires_at,
                    'version': state_entry.version,
                    'is_expired': state_entry.is_expired(),
                    'data_size': len(str(state_entry.data))
                }
            
            return info
    
    def _start_cleanup_thread(self) -> None:
        """启动清理线程"""
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_worker(self) -> None:
        """清理工作线程"""
        cleanup_interval = self.config.get('cleanup_interval', 300)
        
        while not self._stop_cleanup.wait(cleanup_interval):
            self._cleanup_expired_states()
    
    def _cleanup_expired_states(self) -> None:
        """清理过期状态"""
        with self._lock:
            now = time.time()
            expired_contexts = []
            
            for context_id, states in self._states.items():
                expired_states = []
                
                for state_type, state_entry in states.items():
                    if state_entry.is_expired():
                        expired_states.append(state_type)
                
                # 删除过期状态
                for state_type in expired_states:
                    del states[state_type]
                
                # 如果上下文没有状态了，标记为删除
                if not states:
                    expired_contexts.append(context_id)
            
            # 删除空的上下文
            for context_id in expired_contexts:
                del self._states[context_id]
    
    def __del__(self):
        """析构函数"""
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)