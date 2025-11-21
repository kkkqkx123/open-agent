"""节点构建器

负责节点的构建和管理。
"""

from typing import Any, Callable, Dict, Optional, Union
import logging

from src.core.workflow.config.config import GraphConfig, NodeConfig
from src.core.workflow.states.workflow import WorkflowState
from src.interfaces.state import IStateLifecycleManager

logger = logging.getLogger(__name__)


class NodeBuilder:
    """节点构建器
    
    负责节点的构建和管理。
    """
    
    def __init__(self, function_resolver):
        """初始化节点构建器
        
        Args:
            function_resolver: 函数解析器
        """
        self._function_resolver = function_resolver
    
    def add_nodes(self, builder: Any, config: GraphConfig, state_manager: Optional[IStateLifecycleManager] = None) -> None:
        """添加节点到图
        
        Args:
            builder: LangGraph构建器
            config: 图配置
            state_manager: 状态管理器
        """
        for node_name, node_config in config.nodes.items():
            node_function = self._get_node_function(node_config, state_manager)
            if node_function:
                builder.add_node(node_name, node_function)
                logger.debug(f"添加节点: {node_name}")
            else:
                logger.warning(f"无法找到节点函数: {node_config.function_name}")
    
    def _get_node_function(
        self,
        node_config: NodeConfig,
        state_manager: Optional[IStateLifecycleManager] = None,
    ) -> Optional[Callable]:
        """获取节点函数
        
        Args:
            node_config: 节点配置
            state_manager: 状态管理器
            
        Returns:
            Optional[Callable]: 节点函数
        """
        function_name = node_config.function_name
        
        # 从函数解析器获取函数
        node_function = self._function_resolver.get_node_function(function_name)
        if node_function:
            logger.debug(f"从函数解析器获取节点函数: {function_name}")
            return self._wrap_node_function(node_function, state_manager, node_config.name)
        
        logger.warning(f"无法找到节点函数: {function_name}")
        return None
    
    def _wrap_node_function(
        self,
        function: Callable,
        state_manager: Optional[IStateLifecycleManager] = None,
        node_name: str = "unknown",
    ) -> Callable:
        """包装节点函数以支持状态管理
        
        Args:
            function: 原始节点函数
            state_manager: 状态管理器
            node_name: 节点名称
            
        Returns:
            Callable: 包装后的函数
        """
        # 如果有状态管理器，使用状态管理包装
        if state_manager is not None:
            def state_wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
                """状态管理包装的节点函数"""
                # 使用状态管理器执行
                return function(state)
            
            wrapped_function = state_wrapped_function
        else:
            # 如果没有状态管理器，直接使用原函数
            wrapped_function = function
        
        return wrapped_function