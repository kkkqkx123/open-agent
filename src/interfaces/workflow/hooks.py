"""Hook系统接口定义

定义了Hook系统的核心接口，包括Hook执行器、Hook系统等。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from enum import Enum

from .plugins import HookPoint, HookContext, HookExecutionResult

if TYPE_CHECKING:
    from .plugins import IHookPlugin
    from ..state import IWorkflowState
    from .graph import NodeExecutionResult


class IHookExecutor(ABC):
    """Hook执行器接口
    
    负责Hook插件的执行逻辑，包括Hook插件的获取和过滤、Hook点的执行等。
    """
    
    @abstractmethod
    def set_hook_configs(self, configs: Dict[str, Any]) -> None:
        """设置Hook配置
        
        Args:
            configs: Hook配置字典
        """
        pass
    
    @abstractmethod
    def get_enabled_hook_plugins(self, node_type: str) -> List['IHookPlugin']:
        """获取指定节点的Hook插件列表
        
        Args:
            node_type: 节点类型
            
        Returns:
            List[IHookPlugin]: Hook插件列表
        """
        pass
    
    @abstractmethod
    def execute_hooks(self, hook_point: HookPoint, context: HookContext) -> HookExecutionResult:
        """执行指定Hook点的所有Hook插件
        
        Args:
            hook_point: Hook执行点
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: 合并后的Hook执行结果
        """
        pass
    
    @abstractmethod
    def execute_with_hooks(
        self,
        node_type: str,
        state: 'IWorkflowState',
        config: Dict[str, Any],
        node_executor_func: Callable[['IWorkflowState', Dict[str, Any]], 'NodeExecutionResult']
    ) -> 'NodeExecutionResult':
        """统一的Hook执行接口
        
        Args:
            node_type: 节点类型
            state: 当前状态
            config: 节点配置
            node_executor_func: 节点执行函数
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    def get_execution_count(self, node_type: str) -> int:
        """获取节点执行次数
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: 执行次数
        """
        pass
    
    @abstractmethod
    def increment_execution_count(self, node_type: str) -> int:
        """增加节点执行计数
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: 增加后的执行次数
        """
        pass
    
    @abstractmethod
    def update_performance_stats(
        self, 
        node_type: str, 
        execution_time: float, 
        success: bool = True
    ) -> None:
        """更新性能统计
        
        Args:
            node_type: 节点类型
            execution_time: 执行时间
            success: 是否成功
        """
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 性能统计信息
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """清空Hook插件缓存"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理Hook执行器资源"""
        pass


class IHookSystem(ABC):
    """Hook系统接口
    
    管理所有Hook的注册和执行。
    """
    
    @abstractmethod
    def register_hook(
        self,
        hook_point: HookPoint,
        hook: 'IHookPlugin',
        priority: int = 50
    ) -> None:
        """注册Hook
        
        Args:
            hook_point: Hook点
            hook: Hook插件
            priority: 优先级，数值越小优先级越高
        """
        pass
    
    @abstractmethod
    def unregister_hook(
        self,
        hook_point: HookPoint,
        hook_name: str
    ) -> bool:
        """注销Hook
        
        Args:
            hook_point: Hook点
            hook_name: Hook名称
            
        Returns:
            是否成功注销
        """
        pass
    
    @abstractmethod
    async def execute_hooks(
        self,
        hook_point: HookPoint,
        context: HookContext
    ) -> HookExecutionResult:
        """执行Hook
        
        Args:
            hook_point: Hook点
            context: Hook执行上下文
            
        Returns:
            Hook执行结果
        """
        pass
    
    @abstractmethod
    def get_hooks_for_point(self, hook_point: HookPoint) -> List['IHookPlugin']:
        """获取指定Hook点的所有Hook
        
        Args:
            hook_point: Hook点
            
        Returns:
            Hook列表
        """
        pass
    
    @abstractmethod
    def clear_hooks(self, hook_point: Optional[HookPoint] = None) -> None:
        """清除Hook
        
        Args:
            hook_point: 要清除的Hook点，如果为None则清除所有
        """
        pass
    
    @abstractmethod
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            统计信息字典
        """
        pass
