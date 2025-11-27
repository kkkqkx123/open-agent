"""
作用域管理接口

定义服务作用域管理的相关接口，支持作用域生命周期和实例隔离。
"""

from abc import ABC, abstractmethod
from typing import Type, Optional, Any, Dict, List, ContextManager
from contextlib import contextmanager
from enum import Enum


'''
作用域状态枚举
'''

class ScopeStatus(Enum):
    """
    作用域状态枚举
    """
    ACTIVE = "active"      # 活跃状态
    DISPOSED = "disposed"  # 已释放
    ERROR = "error"        # 错误状态


'''
作用域接口
'''

class IScope(ABC):
    """
    作用域接口
    
    定义作用域的基本契约，包含作用域的生命周期和实例管理。
    """
    
    @property
    @abstractmethod
    def scope_id(self) -> str:
        """
        获取作用域ID
        
        Returns:
            str: 作用域唯一标识
        """
        pass
    
    @property
    @abstractmethod
    def parent_scope_id(self) -> Optional[str]:
        """
        获取父作用域ID
        
        Returns:
            Optional[str]: 父作用域ID，如果没有父作用域则返回None
        """
        pass
    
    @property
    @abstractmethod
    def status(self) -> ScopeStatus:
        """
        获取作用域状态
        
        Returns:
            ScopeStatus: 作用域状态
        """
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> float:
        """
        获取创建时间戳
        
        Returns:
            float: 创建时间戳
        """
        pass
    
    @abstractmethod
    def get_service(self, service_type: Type) -> Optional[Any]:
        """
        获取作用域内的服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[Any]: 服务实例，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def set_service(self, service_type: Type, instance: Any) -> None:
        """
        设置作用域内的服务实例
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        pass
    
    @abstractmethod
    def remove_service(self, service_type: Type) -> bool:
        """
        移除作用域内的服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否成功移除
        """
        pass
    
    @abstractmethod
    def list_services(self) -> List[Type]:
        """
        列出作用域内的所有服务类型
        
        Returns:
            List[Type]: 服务类型列表
        """
        pass
    
    @abstractmethod
    def clear_services(self) -> int:
        """
        清除作用域内的所有服务
        
        Returns:
            int: 清除的服务数量
        """
        pass
    
    @abstractmethod
    def get_service_count(self) -> int:
        """
        获取作用域内的服务数量
        
        Returns:
            int: 服务数量
        """
        pass
    
    @abstractmethod
    def dispose(self) -> None:
        """
        释放作用域资源
        
        清除所有服务实例并标记为已释放状态。
        """
        pass


'''
作用域管理器接口
'''

class IScopeManager(ABC):
    """
    作用域管理器接口
    
    负责管理服务的作用域生命周期，支持作用域的创建、释放和上下文管理。
    这是依赖注入容器的高级功能，用于实现作用域模式。
    
    主要功能：
    - 作用域创建和释放
    - 作用域上下文管理
    - 作用域层次管理
    - 服务实例隔离
    - 作用域生命周期跟踪
    
    使用示例：
        ```python
        # 创建作用域
        scope_id = scope_manager.create_scope()
        
        # 使用作用域上下文
        with scope_manager.scope_context() as current_scope:
            # 在当前作用域中操作
            scope_manager.set_scoped_instance(IUserService, user_instance)
            user_service = scope_manager.get_scoped_instance(IUserService)
        
        # 释放作用域
        scope_manager.dispose_scope(scope_id)
        ```
    """
    
    @abstractmethod
    def create_scope(self, parent_scope_id: Optional[str] = None) -> str:
        """
        创建新作用域
        
        Args:
            parent_scope_id: 父作用域ID，None表示根作用域
            
        Returns:
            str: 新创建的作用域ID
            
        Raises:
            ScopeCreationException: 作用域创建失败时抛出
            ParentScopeNotFoundException: 父作用域不存在时抛出
            
        Examples:
            ```python
            # 创建根作用域
            root_scope_id = scope_manager.create_scope()
            
            # 创建子作用域
            child_scope_id = scope_manager.create_scope(root_scope_id)
            
            # 创建嵌套作用域
            with scope_manager.scope_context() as parent:
                with scope_manager.scope_context() as child:
                    # child是parent的子作用域
                    pass
            ```
        """
        pass
    
    @abstractmethod
    def dispose_scope(self, scope_id: str) -> bool:
        """
        释放作用域
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            bool: 是否成功释放
            
        Raises:
            ScopeNotFoundException: 作用域不存在时抛出
            ScopeDisposalException: 作用域释放失败时抛出
            
        Examples:
            ```python
            # 释放特定作用域
            success = scope_manager.dispose_scope(scope_id)
            
            # 释放所有子作用域
            scope_id = scope_manager.get_current_scope_id()
            if scope_id:
                scope_manager.dispose_scope(scope_id)
            ```
        """
        pass
    
    @abstractmethod
    def get_current_scope_id(self) -> Optional[str]:
        """
        获取当前作用域ID
        
        Returns:
            Optional[str]: 当前作用域ID，如果没有当前作用域则返回None
            
        Examples:
            ```python
            current_scope = scope_manager.get_current_scope_id()
            if current_scope:
                print(f"Current scope: {current_scope}")
            else:
                print("No active scope")
            ```
        """
        pass
    
    @abstractmethod
    def set_current_scope_id(self, scope_id: Optional[str]) -> None:
        """
        设置当前作用域ID
        
        Args:
            scope_id: 作用域ID，None表示清除当前作用域
            
        Examples:
            ```python
            # 切换到指定作用域
            scope_manager.set_current_scope_id("request_123")
            
            # 清除当前作用域
            scope_manager.set_current_scope_id(None)
            
            # 在上下文中自动管理
            with scope_manager.scope_context("request_123"):
                # 在此作用域中执行
                pass
            ```
        """
        pass
    
    @abstractmethod
    def get_scoped_instance(self, scope_id: str, service_type: Type) -> Optional[Any]:
        """
        获取作用域内的服务实例
        
        Args:
            scope_id: 作用域ID
            service_type: 服务类型
            
        Returns:
            Optional[Any]: 服务实例，如果不存在则返回None
            
        Examples:
            ```python
            # 获取特定作用域的服务
            user_service = scope_manager.get_scoped_instance(
                "request_123", 
                IUserService
            )
            
            # 安全获取
            if user_service:
                user_service.process_request()
            else:
                print("UserService not found in scope")
            ```
        """
        pass
    
    @abstractmethod
    def set_scoped_instance(self, scope_id: str, service_type: Type, instance: Any) -> None:
        """
        设置作用域内的服务实例
        
        Args:
            scope_id: 作用域ID
            service_type: 服务类型
            instance: 服务实例
            
        Raises:
            ScopeNotFoundException: 作用域不存在时抛出
            
        Examples:
            ```python
            # 在作用域中设置服务
            scope_manager.set_scoped_instance(
                "request_123",
                IUserService,
                UserService()
            )
            
            # 设置当前作用域的服务
            current_scope = scope_manager.get_current_scope_id()
            if current_scope:
                scope_manager.set_scoped_instance(
                    current_scope,
                    ILogger,
                    Logger()
                )
            ```
        """
        pass
    
    @abstractmethod
    def remove_scoped_instance(self, scope_id: str, service_type: Type) -> bool:
        """
        移除作用域内的服务实例
        
        Args:
            scope_id: 作用域ID
            service_type: 服务类型
            
        Returns:
            bool: 是否成功移除
            
        Examples:
            ```python
            # 移除服务实例
            success = scope_manager.remove_scoped_instance(
                "request_123",
                IUserService
            )
            
            if success:
                print("UserService removed from scope")
            ```
        """
        pass
    
    @abstractmethod
    def scope_context(self, scope_id: Optional[str] = None) -> ContextManager[str]:
        """
        作用域上下文管理器
        
        Args:
            scope_id: 作用域ID，None表示创建新作用域
            
        Returns:
            ContextManager[str]: 上下文管理器，进入时返回作用域ID
            
        Examples:
            ```python
            # 使用现有作用域
            with scope_manager.scope_context("request_123") as scope_id:
                # 在作用域中执行
                scope_manager.set_scoped_instance(scope_id, IUserService, UserService())
                user_service = scope_manager.get_scoped_instance(scope_id, IUserService)
            
            # 创建新作用域
            with scope_manager.scope_context() as scope_id:
                # 在新作用域中执行
                print(f"Created scope: {scope_id}")
            ```
        """
        pass
    
    @abstractmethod
    def get_scope(self, scope_id: str) -> Optional[IScope]:
        """
        获取作用域对象
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            Optional[IScope]: 作用域对象，如果不存在则返回None
            
        Examples:
            ```python
            scope = scope_manager.get_scope("request_123")
            if scope:
                print(f"Scope status: {scope.status}")
                print(f"Service count: {scope.get_service_count()}")
            ```
        """
        pass
    
    @abstractmethod
    def list_scopes(self, parent_scope_id: Optional[str] = None) -> List[str]:
        """
        列出作用域
        
        Args:
            parent_scope_id: 父作用域ID过滤，None表示所有作用域
            
        Returns:
            List[str]: 作用域ID列表
            
        Examples:
            ```python
            # 列出所有作用域
            all_scopes = scope_manager.list_scopes()
            
            # 列出根作用域的子作用域
            root_scopes = scope_manager.list_scopes("root")
            
            # 列出当前作用域的子作用域
            current = scope_manager.get_current_scope_id()
            if current:
                child_scopes = scope_manager.list_scopes(current)
            ```
        """
        pass
    
    @abstractmethod
    def get_parent_scope_id(self, scope_id: str) -> Optional[str]:
        """
        获取父作用域ID
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            Optional[str]: 父作用域ID，如果是根作用域则返回None
            
        Examples:
            ```python
            parent_id = scope_manager.get_parent_scope_id("request_123")
            if parent_id:
                print(f"Parent scope: {parent_id}")
            else:
                print("Root scope")
            ```
        """
        pass
    
    @abstractmethod
    def get_child_scope_ids(self, scope_id: str) -> List[str]:
        """
        获取子作用域ID列表
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            List[str]: 子作用域ID列表
            
        Examples:
            ```python
            children = scope_manager.get_child_scope_ids("request_123")
            for child_id in children:
                print(f"Child scope: {child_id}")
            ```
        """
        pass
    
    @abstractmethod
    def get_scope_hierarchy(self, scope_id: str) -> List[str]:
        """
        获取作用域层次路径
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            List[str]: 从根作用域到指定作用域的路径
            
        Examples:
            ```python
            hierarchy = scope_manager.get_scope_hierarchy("request_123")
            print(" -> ".join(hierarchy))
            # 输出: root -> session_456 -> request_123
            ```
        """
        pass
    
    @abstractmethod
    def is_scope_active(self, scope_id: str) -> bool:
        """
        检查作用域是否活跃
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            bool: 是否活跃
            
        Examples:
            ```python
            if scope_manager.is_scope_active("request_123"):
                print("Scope is active")
            else:
                print("Scope is not active or doesn't exist")
            ```
        """
        pass
    
    @abstractmethod
    def cleanup_expired_scopes(self, max_age_seconds: int = 3600) -> int:
        """
        清理过期的作用域
        
        Args:
            max_age_seconds: 最大存活时间（秒）
            
        Returns:
            int: 清理的作用域数量
            
        Examples:
            ```python
            # 清理1小时前的作用域
            cleaned = scope_manager.cleanup_expired_scopes(3600)
            print(f"Cleaned {cleaned} expired scopes")
            
            # 定期清理
            import threading
            import time
            
            def cleanup_worker():
                while True:
                    time.sleep(300)  # 5分钟
                    scope_manager.cleanup_expired_scopes()
            
            cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
            cleanup_thread.start()
            ```
        """
        pass
    
    @abstractmethod
    def get_scope_statistics(self) -> Dict[str, Any]:
        """
        获取作用域统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
            
        Examples:
            ```python
            stats = scope_manager.get_scope_statistics()
            print(f"Total scopes: {stats['total_scopes']}")
            print(f"Active scopes: {stats['active_scopes']}")
            print(f"Total instances: {stats['total_instances']}")
            print(f"Average instances per scope: {stats['avg_instances_per_scope']:.2f}")
            ```
        """
        pass
    
    @abstractmethod
    def export_scope_state(self, scope_id: str) -> Dict[str, Any]:
        """
        导出作用域状态
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            Dict[str, Any]: 作用域状态数据
            
        Examples:
            ```python
            # 导出作用域状态
            state = scope_manager.export_scope_state("request_123")
            
            # 保存到文件
            import json
            with open(f"scope_{scope_id}.json", "w") as f:
                json.dump(state, f, indent=2)
            ```
        """
        pass
    
    @abstractmethod
    def import_scope_state(self, scope_data: Dict[str, Any]) -> str:
        """
        导入作用域状态
        
        Args:
            scope_data: 作用域状态数据
            
        Returns:
            str: 导入的作用域ID
            
        Examples:
            ```python
            # 从文件导入作用域状态
            import json
            
            with open("scope_request_123.json", "r") as f:
                scope_data = json.load(f)
            
            scope_id = scope_manager.import_scope_state(scope_data)
            print(f"Imported scope: {scope_id}")
            ```
        """
        pass


'''
作用域工厂接口
'''

class IScopeFactory(ABC):
    """
    作用域工厂接口
    
    定义作用域实例创建的契约。
    """
    
    @abstractmethod
    def create_scope(self, scope_id: str, parent_scope_id: Optional[str] = None) -> IScope:
        """
        创建作用域实例
        
        Args:
            scope_id: 作用域ID
            parent_scope_id: 父作用域ID
            
        Returns:
            IScope: 作用域实例
        """
        pass
    
    @abstractmethod
    def create_root_scope(self, scope_id: str) -> IScope:
        """
        创建根作用域实例
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            IScope: 根作用域实例
        """
        pass
    
    @abstractmethod
    def create_child_scope(self, scope_id: str, parent_scope_id: str) -> IScope:
        """
        创建子作用域实例
        
        Args:
            scope_id: 作用域ID
            parent_scope_id: 父作用域ID
            
        Returns:
            IScope: 子作用域实例
        """
        pass