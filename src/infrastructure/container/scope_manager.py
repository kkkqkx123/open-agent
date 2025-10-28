"""作用域管理器实现"""

import threading
from typing import Type, Any, Optional, Dict
from contextlib import contextmanager

from ..container_interfaces import IScopeManager, ILifecycleAware


class ScopeManager(IScopeManager):
    """作用域管理器实现"""
    
    def __init__(self):
        """初始化作用域管理器"""
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope_id: Optional[str] = None
        self._scope_counter = 0
        self._lock = threading.RLock()
    
    def create_scope(self) -> str:
        """创建新作用域
        
        Returns:
            作用域ID
        """
        with self._lock:
            self._scope_counter += 1
            scope_id = f"scope_{self._scope_counter}"
            self._scoped_instances[scope_id] = {}
            return scope_id
    
    def dispose_scope(self, scope_id: str) -> None:
        """释放作用域
        
        Args:
            scope_id: 作用域ID
        """
        with self._lock:
            if scope_id in self._scoped_instances:
                # 释放作用域内的所有实例
                for service_type, instance in self._scoped_instances[scope_id].items():
                    if isinstance(instance, ILifecycleAware):
                        try:
                            instance.dispose()
                        except Exception:
                            pass  # 忽略释放过程中的异常
                
                del self._scoped_instances[scope_id]
    
    def get_current_scope_id(self) -> Optional[str]:
        """获取当前作用域ID
        
        Returns:
            当前作用域ID
        """
        return self._current_scope_id
    
    def set_current_scope_id(self, scope_id: Optional[str]) -> None:
        """设置当前作用域ID
        
        Args:
            scope_id: 作用域ID
        """
        self._current_scope_id = scope_id
    
    def get_scoped_instance(self, scope_id: str, service_type: Type) -> Optional[Any]:
        """获取作用域内的服务实例
        
        Args:
            scope_id: 作用域ID
            service_type: 服务类型
            
        Returns:
            服务实例，如果不存在则返回None
        """
        with self._lock:
            if scope_id in self._scoped_instances:
                return self._scoped_instances[scope_id].get(service_type)
            return None
    
    def set_scoped_instance(self, scope_id: str, service_type: Type, instance: Any) -> None:
        """设置作用域内的服务实例
        
        Args:
            scope_id: 作用域ID
            service_type: 服务类型
            instance: 服务实例
        """
        with self._lock:
            if scope_id not in self._scoped_instances:
                self._scoped_instances[scope_id] = {}
            self._scoped_instances[scope_id][service_type] = instance
    
    @contextmanager
    def scope_context(self):
        """作用域上下文管理器"""
        old_scope_id = self._current_scope_id
        scope_id = self.create_scope()
        try:
            self._current_scope_id = scope_id
            yield scope_id
        finally:
            self._current_scope_id = old_scope_id
            self.dispose_scope(scope_id)