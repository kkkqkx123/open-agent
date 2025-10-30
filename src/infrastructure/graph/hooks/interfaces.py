"""Hook系统接口定义

定义Hook系统的核心接口和抽象类。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
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
    
    @abstractmethod
    def load_hooks_from_config(self, config_path: str) -> None:
        """从配置文件加载Hook
        
        Args:
            config_path: 配置文件路径
        """
        pass
    
    @abstractmethod
    def clear_hooks(self) -> None:
        """清除所有Hook"""
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