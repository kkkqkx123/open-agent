"""统一图构建器

使用组合模式组织各个专门的构建器。
"""

from typing import Any, Dict, Optional, Protocol
import logging

from src.core.workflow.config.config import GraphConfig
from src.core.workflow.graph.registry import NodeRegistry, get_global_registry
from src.interfaces.state import IStateLifecycleManager
from .graph_builder import GraphBuilder
from .node_builder import NodeBuilder
from .edge_builder import EdgeBuilder
from .compiler import GraphCompiler
from .function_resolver import FunctionResolver, FunctionRegistryProtocol

logger = logging.getLogger(__name__)


class GraphOrchestrator:
    """统一图构建器
    
    使用组合模式组织各个专门的构建器。
    """
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        function_registry: Optional[FunctionRegistryProtocol] = None,
        enable_function_fallback: bool = True,
    ) -> None:
        """初始化统一图构建器
        
        Args:
            node_registry: 节点注册表
            function_registry: 函数注册表
            enable_function_fallback: 是否启用函数回退机制
        """
        # 创建函数解析器
        self._function_resolver = FunctionResolver(
            node_registry=node_registry,
            function_registry=function_registry,
            enable_function_fallback=enable_function_fallback
        )
        
        # 创建专门的构建器
        self._node_builder = NodeBuilder(self._function_resolver)
        self._edge_builder = EdgeBuilder(self._function_resolver)
        self._compiler = GraphCompiler()
        
        # 创建主图构建器
        self._graph_builder = GraphBuilder(
            self._node_builder,
            self._edge_builder,
            self._compiler
        )
        
        logger.debug(f"统一图构建器初始化完成，函数回退: {enable_function_fallback}")
    
    def build_graph(self, config: GraphConfig, state_manager: Optional[IStateLifecycleManager] = None) -> Any:
        """构建图
        
        Args:
            config: 图配置
            state_manager: 状态管理器
            
        Returns:
            编译后的图
        """
        return self._graph_builder.build_graph(config, state_manager)
    
    @property
    def function_resolver(self) -> FunctionResolver:
        """获取函数解析器
        
        Returns:
            FunctionResolver: 函数解析器
        """
        return self._function_resolver
    
    @property
    def node_builder(self) -> NodeBuilder:
        """获取节点构建器
        
        Returns:
            NodeBuilder: 节点构建器
        """
        return self._node_builder
    
    @property
    def edge_builder(self) -> EdgeBuilder:
        """获取边构建器
        
        Returns:
            EdgeBuilder: 边构建器
        """
        return self._edge_builder
    
    @property
    def compiler(self) -> GraphCompiler:
        """获取图编译器
        
        Returns:
            GraphCompiler: 图编译器
        """
        return self._compiler
