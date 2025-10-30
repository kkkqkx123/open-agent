"""Hook系统接口定义

定义Hook系统的核心接口和抽象类。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING, Callable
from dataclasses import dataclass
from enum import Enum

from src.domain.agent.state import AgentState
from ..registry import NodeExecutionResult


class HookExecutionResult:
    """Hook执行结果"""
    
    def __init__(
        self,
        should_continue: bool = True,
        modified_state: Optional[AgentState] = None,
        modified_result: Optional[NodeExecutionResult] = None,
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


class HookPoint(Enum):
    """Hook执行点"""
    BEFORE_EXECUTE = "before_execute"
    AFTER_EXECUTE = "after_execute"
    ON_ERROR = "on_error"


@dataclass
class HookContext:
    """Hook执行上下文"""
    node_type: str
    state: AgentState
    config: Dict[str, Any]
    hook_point: HookPoint
    error: Optional[Exception] = None
    execution_result: Optional[NodeExecutionResult] = None
    metadata: Optional[Dict[str, Any]] = None


class INodeHook(ABC):
    """节点Hook接口"""
    
    def __init__(self, hook_config: Dict[str, Any]) -> None:
        """初始化Hook
        
        Args:
            hook_config: Hook配置
        """
        self.config = hook_config
        self.enabled = hook_config.get("enabled", True)
        self._execution_service: Optional[IHookExecutionService] = None
    
    def set_execution_service(self, service: 'IHookExecutionService') -> None:
        """设置执行服务
        
        Args:
            service: Hook执行服务实例
        """
        self._execution_service = service
    
    @property
    @abstractmethod
    def hook_type(self) -> str:
        """Hook类型标识"""
        pass
    
    @abstractmethod
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行前Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        pass
    
    @abstractmethod
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        """节点执行后Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        pass
    
    @abstractmethod
    def on_error(self, context: HookContext) -> HookExecutionResult:
        """错误处理Hook
        
        Args:
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: Hook执行结果
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查Hook是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.enabled
    
    def validate_config(self) -> List[str]:
        """验证Hook配置
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        return []
    
    def get_supported_hook_points(self) -> List[HookPoint]:
        """获取支持的Hook执行点
        
        Returns:
            List[HookPoint]: 支持的Hook执行点列表
        """
        return [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE, HookPoint.ON_ERROR]


class IHookExecutionService(ABC):
    """Hook执行服务接口"""
    
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


class IHookManager(ABC):
    """Hook管理器接口"""
    
    @abstractmethod
    def register_hook(self, hook: INodeHook, node_types: Optional[List[str]] = None) -> None:
        """注册Hook
        
        Args:
            hook: Hook实例
            node_types: 适用的节点类型列表，None表示适用于所有节点
        """
        pass
    
    @abstractmethod
    def get_hooks_for_node(self, node_type: str) -> List[INodeHook]:
        """获取指定节点的Hook列表
        
        Args:
            node_type: 节点类型
            
        Returns:
            List[INodeHook]: Hook列表
        """
        pass
    
    @abstractmethod
    def execute_hooks(
        self,
        hook_point: HookPoint,
        context: HookContext
    ) -> HookExecutionResult:
        """执行指定Hook点的所有Hook
        
        Args:
            hook_point: Hook执行点
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: 合并后的Hook执行结果
        """
        pass
    
    def execute_with_hooks(
        self,
        node_type: str,
        state,
        config: Dict[str, Any],
        node_executor_func: Callable
    ) -> NodeExecutionResult:
        """统一的Hook执行接口
        
        Args:
            node_type: 节点类型
            state: 当前状态
            config: 节点配置
            node_executor_func: 节点执行函数
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 创建前置Hook上下文
        before_context = HookContext(
            node_type=node_type,
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        # 执行前置Hook
        before_result = self.execute_hooks(HookPoint.BEFORE_EXECUTE, before_context)
        
        # 检查是否需要中断执行
        if not before_result.should_continue:
            from ..registry import NodeExecutionResult
            return NodeExecutionResult(
                state=before_result.modified_state or state,
                next_node=before_result.force_next_node,
                metadata={
                    "interrupted_by_hooks": True,
                    "hook_metadata": before_result.metadata
                }
            )
        
        # 更新状态（如果Hook修改了状态）
        if before_result.modified_state:
            state = before_result.modified_state
        
        # 执行节点逻辑
        try:
            result = node_executor_func(state, config)
            
            # 创建后置Hook上下文
            after_context = HookContext(
                node_type=node_type,
                state=result.state,
                config=config,
                hook_point=HookPoint.AFTER_EXECUTE,
                execution_result=result
            )
            
            # 执行后置Hook
            after_result = self.execute_hooks(HookPoint.AFTER_EXECUTE, after_context)
            
            # 应用Hook结果
            if after_result.modified_state:
                result.state = after_result.modified_state
            
            if after_result.force_next_node:
                result.next_node = after_result.force_next_node
            
            if after_result.metadata:
                if result.metadata is None:
                    result.metadata = {}
                result.metadata.update(after_result.metadata)
            
            return result
            
        except Exception as e:
            # 创建错误Hook上下文
            error_context = HookContext(
                node_type=node_type,
                state=state,
                config=config,
                hook_point=HookPoint.ON_ERROR,
                error=e
            )
            
            # 执行错误Hook
            error_result = self.execute_hooks(HookPoint.ON_ERROR, error_context)
            
            # 检查Hook是否处理了错误
            if not error_result.should_continue:
                from ..registry import NodeExecutionResult
                return NodeExecutionResult(
                    state=error_result.modified_state or state,
                    next_node=error_result.force_next_node or "error_handler",
                    metadata={
                        "error_handled_by_hooks": True,
                        "original_error": str(e),
                        "hook_metadata": error_result.metadata
                    }
                )
            
            # 如果Hook没有处理错误，重新抛出异常
            raise e
    
    @abstractmethod
    def load_hooks_from_config(self, config_path: Optional[str] = None) -> None:
        """从配置文件加载Hook

        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        pass

    @abstractmethod
    def load_node_hooks_from_config(self, node_type: str) -> None:
        """从配置文件加载指定节点的Hook

        Args:
            node_type: 节点类型
        """
        pass

    @abstractmethod
    def clear_hooks(self) -> None:
        """清除所有Hook"""
        pass

    @abstractmethod
    def get_global_hooks_count(self) -> int:
        """获取全局Hook数量
        
        Returns:
            int: 全局Hook数量
        """
        pass

    @abstractmethod
    def get_node_hooks_count(self, node_type: str) -> int:
        """获取指定节点的Hook数量
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: Hook数量
        """
        pass

    @abstractmethod
    def get_all_node_hooks_counts(self) -> Dict[str, int]:
        """获取所有节点的Hook数量
        
        Returns:
            Dict[str, int]: 节点类型到Hook数量的映射
        """
        pass

    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 节点类型到性能统计的映射
        """
        pass


class IHookConfigLoader(ABC):
    """Hook配置加载器接口"""
    
    @abstractmethod
    def load_global_hooks(self) -> List[Dict[str, Any]]:
        """加载全局Hook配置
        
        Returns:
            List[Dict[str, Any]]: 全局Hook配置列表
        """
        pass
    
    @abstractmethod
    def load_node_hooks(self, node_type: str) -> List[Dict[str, Any]]:
        """加载指定节点的Hook配置
        
        Args:
            node_type: 节点类型
            
        Returns:
            List[Dict[str, Any]]: 节点Hook配置列表
        """
        pass
    
    @abstractmethod
    def merge_hook_configs(
        self, 
        global_configs: List[Dict[str, Any]], 
        node_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并全局和节点Hook配置
        
        Args:
            global_configs: 全局Hook配置
            node_configs: 节点Hook配置
            
        Returns:
            List[Dict[str, Any]]: 合并后的Hook配置
        """
        pass