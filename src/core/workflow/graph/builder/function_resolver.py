"""函数解析器

负责解析节点函数和条件函数。
"""

from typing import Callable, Dict, Optional, Union, Protocol
import logging

from src.core.workflow.states.workflow import WorkflowState
from src.core.workflow.graph.registry import NodeRegistry, get_global_registry

logger = logging.getLogger(__name__)


class FunctionRegistryProtocol(Protocol):
    """函数注册表协议，用于类型检查"""
    
    def get_node_function(self, name: str) -> Optional[Callable]: ...
    def get_condition_function(self, name: str) -> Optional[Callable]: ...


class FunctionResolver:
    """函数解析器
    
    负责解析节点函数和条件函数。
    """
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        function_registry: Optional[FunctionRegistryProtocol] = None,
        enable_function_fallback: bool = True,
    ) -> None:
        """初始化函数解析器
        
        Args:
            node_registry: 节点注册表
            function_registry: 函数注册表
            enable_function_fallback: 是否启用函数回退机制
        """
        self.node_registry = node_registry or get_global_registry()
        
        # 延迟导入FunctionRegistry避免循环依赖
        if function_registry is not None:
            self.function_registry: Optional[FunctionRegistryProtocol] = function_registry
        else:
            try:
                from src.services.workflow.function_registry import get_global_function_registry
                self.function_registry = get_global_function_registry()
            except ImportError:
                logger.warning("无法导入FunctionRegistry，将不使用函数注册表")
                self.function_registry = None
        
        self.enable_function_fallback = enable_function_fallback
        
        logger.debug(f"函数解析器初始化完成，函数回退: {enable_function_fallback}")
    
    def get_node_function(self, function_name: str) -> Optional[Callable]:
        """获取节点函数
        
        优先级：函数注册表 -> 节点注册表 -> 内置函数
        
        Args:
            function_name: 函数名称
            
        Returns:
            Optional[Callable]: 节点函数
        """
        # 1. 优先从函数注册表获取
        if self.function_registry and hasattr(self.function_registry, 'get_node_function'):
            node_function = self.function_registry.get_node_function(function_name)
            if node_function:
                logger.debug(f"从函数注册表获取节点函数: {function_name}")
                return node_function
        
        # 2. 尝试从节点注册表获取
        if self.node_registry:
            try:
                node_class = self.node_registry.get_node_class(function_name)
                if node_class:
                    node_instance = node_class()
                    logger.debug(f"从节点注册表获取节点函数: {function_name}")
                    return node_instance.execute
            except ValueError:
                # 节点类型不存在，继续尝试其他方法
                pass
        
        # 3. 如果启用回退，尝试内置实现
        if self.enable_function_fallback:
            fallback_function = self._get_fallback_node_function(function_name)
            if fallback_function:
                logger.debug(f"从内置回退函数获取节点函数: {function_name}")
                return fallback_function
        
        logger.warning(f"无法找到节点函数: {function_name}")
        return None
    
    def get_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取条件函数
        
        优先级：函数注册表 -> 内置条件
        
        Args:
            condition_name: 条件函数名称
            
        Returns:
            Optional[Callable]: 条件函数
        """
        # 1. 尝试从函数注册表获取
        if self.function_registry and hasattr(self.function_registry, 'get_condition_function'):
            condition_function = self.function_registry.get_condition_function(condition_name)
            if condition_function:
                logger.debug(f"从函数注册表获取条件函数: {condition_name}")
                return condition_function
        
        # 2. 如果启用回退，尝试内置实现
        if self.enable_function_fallback:
            fallback_function = self._get_fallback_condition_function(condition_name)
            if fallback_function:
                logger.debug(f"从内置回退函数获取条件函数: {condition_name}")
                return fallback_function
        
        logger.warning(f"无法找到条件函数: {condition_name}")
        return None
    
    def _get_fallback_node_function(self, function_name: str) -> Optional[Callable]:
        """获取内置节点函数
        
        Args:
            function_name: 函数名称
            
        Returns:
            Optional[Callable]: 节点函数
        """
        fallback_functions = {
            "llm_node": self._create_llm_node,
            "tool_node": self._create_tool_node,
            "analysis_node": self._create_analysis_node,
            "condition_node": self._create_condition_node,
            "wait_node": self._create_wait_node,
        }
        return fallback_functions.get(function_name)
    
    def _get_fallback_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取内置条件函数
        
        Args:
            condition_name: 条件函数名称
            
        Returns:
            Optional[Callable]: 条件函数
        """
        fallback_conditions = {
            "has_tool_calls": self._condition_has_tool_calls,
            "needs_more_info": self._condition_needs_more_info,
            "is_complete": self._condition_is_complete,
        }
        return fallback_conditions.get(condition_name)
    
    # 内置节点函数实现
    def _create_llm_node(self, state: WorkflowState, config: Optional[Dict] = None) -> WorkflowState:
        """创建LLM节点"""
        logger.debug("执行LLM节点")
        return state
    
    def _create_tool_node(self, state: WorkflowState, config: Optional[Dict] = None) -> WorkflowState:
        """创建工具节点"""
        logger.debug("执行工具节点")
        return state
    
    def _create_analysis_node(self, state: WorkflowState, config: Optional[Dict] = None) -> WorkflowState:
        """创建分析节点"""
        logger.debug("执行分析节点")
        return state
    
    def _create_condition_node(self, state: WorkflowState, config: Optional[Dict] = None) -> WorkflowState:
        """创建条件节点"""
        logger.debug("执行条件节点")
        return state
    
    def _create_wait_node(self, state: WorkflowState, config: Optional[Dict] = None) -> WorkflowState:
        """创建等待节点"""
        logger.debug("执行等待节点")
        return state
    
    # 内置条件函数实现
    def _condition_has_tool_calls(self, state: WorkflowState) -> str:
        """检查是否有工具调用"""
        messages = state.get("messages", [])
        if not messages:
            return "end"

        last_message = messages[-1]
        # 检查LangChain消息的tool_calls属性
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
            return "continue"

        # 检查消息的metadata中的tool_calls
        if hasattr(last_message, 'metadata'):
            metadata = getattr(last_message, 'metadata', {})
            if isinstance(metadata, dict) and metadata.get("tool_calls"):
                return "continue"

        # 检查消息内容
        if hasattr(last_message, 'content'):
            content = str(getattr(last_message, 'content', ''))
            return "continue" if "tool_call" in content.lower() or "调用工具" in content else "end"

        return "end"

    def _condition_needs_more_info(self, state: WorkflowState) -> str:
        """检查是否需要更多信息"""
        # 这里应该实现具体的条件逻辑
        return "continue"

    def _condition_is_complete(self, state: WorkflowState) -> str:
         """检查是否完成"""
         # 这里应该实现具体的条件逻辑
         return "end"