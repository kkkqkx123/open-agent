"""图构建器

负责图的构建和编译。
"""

from typing import Any, Dict, Optional
import logging

from src.core.workflow.config.config import GraphConfig
from src.interfaces.state import IStateLifecycleManager

logger = logging.getLogger(__name__)


class GraphBuilder:
    """图构建器
    
    负责图的构建和编译。
    """
    
    def __init__(self, node_builder, edge_builder, compiler):
        """初始化图构建器
        
        Args:
            node_builder: 节点构建器
            edge_builder: 边构建器
            compiler: 图编译器
        """
        self._node_builder = node_builder
        self._edge_builder = edge_builder
        self._compiler = compiler
    
    def build_graph(self, config: GraphConfig, state_manager: Optional[IStateLifecycleManager] = None) -> Any:
        """构建图
        
        Args:
            config: 图配置
            state_manager: 状态管理器
            
        Returns:
            编译后的图
        """
        # 验证配置
        errors = config.validate()
        if errors:
            raise ValueError(f"图配置验证失败: {errors}")
        
        # 获取状态类
        state_class = config.get_state_class()
        
        # 创建StateGraph
        from langgraph.graph import StateGraph
        from typing import cast
        builder = StateGraph(cast(Any, state_class))
        
        # 添加节点
        self._node_builder.add_nodes(builder, config, state_manager)
        
        # 添加边
        self._edge_builder.add_edges(builder, config)
        
        # 设置入口点
        if config.entry_point:
            from langgraph.graph import START
            builder.add_edge(START, config.entry_point)
        
        # 编译图
        compiled_graph = self._compiler.compile(builder, config)
        
        logger.debug(f"图构建完成: {config.name}")
        return compiled_graph