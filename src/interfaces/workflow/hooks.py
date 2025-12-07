"""Hook系统接口定义

定义了Hook系统的核心接口，包括Hook执行器、Hook系统等。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..state import IWorkflowState
    from .graph import NodeExecutionResult


class HookPoint(Enum):
    """Hook执行点枚举"""
    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"
    ON_ERROR = "on_error"
    BEFORE_COMPILE = "before_compile"
    AFTER_COMPILE = "after_compile"


@dataclass
class HookContext:
    """Hook执行上下文"""
    hook_point: HookPoint
    config: Dict[str, Any]
    node_type: Optional[str] = None
    state: Optional[Any] = None  # Can be IWorkflowState or Dict[str, Any]
    error: Optional[Exception] = None
    execution_result: Optional['NodeExecutionResult'] = None
    metadata: Optional[Dict[str, Any]] = None
    graph_id: Optional[str] = None


class HookExecutionResult:
    """Hook执行结果"""
    
    def __init__(
        self,
        should_continue: bool = True,
        modified_state: Optional['IWorkflowState'] = None,
        modified_result: Optional[Any] = None,
        force_next_node: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化Hook执行结果
        
        Args:
            should_continue: 是否继续执行后续Hook和节点逻辑
            modified_state: 修改后的状态
            modified_result: 修改后的节点执行结果
            force_next_node: 强制指定的下一个节点
            metadata: Hook执行元数据
        """
        self.should_continue = should_continue
        self.modified_state = modified_state
        self.modified_result = modified_result
        self.force_next_node = force_next_node
        self.metadata = metadata or {}
    
    def __bool__(self) -> bool:
        """布尔值转换，表示是否继续执行"""
        return self.should_continue


class IHook(ABC):
    """Hook接口
    
    独立的Hook接口，不依赖插件系统。
    """
    
    @property
    @abstractmethod
    def hook_id(self) -> str:
        """获取Hook ID
        
        Returns:
            str: Hook的唯一标识符
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """获取Hook名称
        
        Returns:
            str: Hook的名称
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """获取Hook描述
        
        Returns:
            str: Hook的描述
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """获取Hook版本
        
        Returns:
            str: Hook的版本
        """
        pass
    
    @abstractmethod
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点
        
        Returns:
            List[HookPoint]: 支持的Hook执行点列表
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化Hook
        
        Args:
            config: Hook配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行前Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行后Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    def before_compile(self, context: HookContext) -> HookExecutionResult:
        """编译前Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    def after_compile(self, context: HookContext) -> HookExecutionResult:
        """编译后Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        return HookExecutionResult(should_continue=True)
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理Hook资源
        
        Returns:
            bool: 清理是否成功
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Hook配置
        
        Args:
            config: Hook配置
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 基础验证
        if not isinstance(config, dict):
            errors.append("配置必须是字典类型")
            return errors
        
        return errors


class IHookRegistry(ABC):
    """Hook注册表接口"""
    
    @abstractmethod
    def register_hook(
        self,
        hook_point: HookPoint,
        hook: IHook,
        priority: int = 50
    ) -> None:
        """注册Hook
        
        Args:
            hook_point: Hook点
            hook: Hook实例
            priority: 优先级，数值越小优先级越高
        """
        pass
    
    @abstractmethod
    def unregister_hook(
        self,
        hook_point: HookPoint,
        hook_id: str
    ) -> bool:
        """注销Hook
        
        Args:
            hook_point: Hook点
            hook_id: Hook ID
            
        Returns:
            bool: 是否成功注销
        """
        pass
    
    @abstractmethod
    def get_hooks_for_point(self, hook_point: HookPoint) -> List[IHook]:
        """获取指定Hook点的所有Hook
        
        Args:
            hook_point: Hook点
            
        Returns:
            List[IHook]: Hook列表
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
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        pass


class IHookExecutor(ABC):
    """Hook执行器接口
    
    负责Hook的执行逻辑，包括Hook的获取和过滤、Hook点的执行等。
    """
    
    @abstractmethod
    def set_hook_configs(self, configs: Dict[str, Any]) -> None:
        """设置Hook配置
        
        Args:
            configs: Hook配置字典
        """
        pass
    
    @abstractmethod
    def get_enabled_hooks(self, node_type: str) -> List[IHook]:
        """获取指定节点的Hook列表
        
        Args:
            node_type: 节点类型
            
        Returns:
            List[IHook]: Hook列表
        """
        pass
    
    @abstractmethod
    def execute_hooks(self, hook_point: HookPoint, context: HookContext) -> HookExecutionResult:
        """执行指定Hook点的所有Hook
        
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
        """清空Hook缓存"""
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
        hook: IHook,
        priority: int = 50
    ) -> None:
        """注册Hook
        
        Args:
            hook_point: Hook点
            hook: Hook实例
            priority: 优先级，数值越小优先级越高
        """
        pass
    
    @abstractmethod
    def unregister_hook(
        self,
        hook_point: HookPoint,
        hook_id: str
    ) -> bool:
        """注销Hook
        
        Args:
            hook_point: Hook点
            hook_id: Hook ID
            
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
    def get_hooks_for_point(self, hook_point: HookPoint) -> List[IHook]:
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
