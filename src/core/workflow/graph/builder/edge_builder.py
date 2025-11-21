"""边构建器

负责边的构建和管理。
"""

from typing import Any, Callable, Dict, Optional
import logging

from src.core.workflow.config.config import GraphConfig, EdgeConfig, EdgeType

logger = logging.getLogger(__name__)


class EdgeBuilder:
    """边构建器
    
    负责边的构建和管理。
    """
    
    def __init__(self, function_resolver):
        """初始化边构建器
        
        Args:
            function_resolver: 函数解析器
        """
        self._function_resolver = function_resolver
    
    def add_edges(self, builder: Any, config: GraphConfig) -> None:
        """添加边到图
        
        Args:
            builder: LangGraph构建器
            config: 图配置
        """
        for edge in config.edges:
            if edge.type == EdgeType.SIMPLE:
                self._add_simple_edge(builder, edge)
            elif edge.type == EdgeType.CONDITIONAL:
                self._add_conditional_edge(builder, edge)
            
            logger.debug(f"添加边: {edge.from_node} -> {edge.to_node}")
    
    def _add_simple_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加简单边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        from langgraph.graph import END
        
        if edge.to_node == "__end__":
            builder.add_edge(edge.from_node, END)
        else:
            builder.add_edge(edge.from_node, edge.to_node)
    
    def _add_conditional_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加条件边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        try:
            # 检查是否为灵活条件边
            if edge.is_flexible_conditional():
                self._add_flexible_conditional_edge(builder, edge)
            else:
                # 传统条件边
                self._add_legacy_conditional_edge(builder, edge)
        except Exception as e:
            logger.error(f"添加条件边失败 {edge.from_node} -> {edge.to_node}: {e}")
            raise
    
    def _add_flexible_conditional_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加灵活条件边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        try:
            # 灵活条件边功能暂未启用
            logger.debug(f"灵活条件边功能暂未启用: {edge.from_node}")
            logger.debug(f"添加灵活条件边: {edge.from_node}")
            
        except Exception as e:
            logger.error(f"创建灵活条件边失败: {e}")
            raise
    
    def _add_legacy_conditional_edge(self, builder: Any, edge: EdgeConfig) -> None:
        """添加传统条件边
        
        Args:
            builder: LangGraph构建器
            edge: 边配置
        """
        if edge.condition is not None:
            condition_function = self._get_condition_function(edge.condition)
            if condition_function:
                if edge.path_map:
                    builder.add_conditional_edges(
                        edge.from_node, 
                        condition_function,
                        path_map=edge.path_map
                    )
                else:
                    builder.add_conditional_edges(edge.from_node, condition_function)
            else:
                logger.warning(f"无法找到条件函数: {edge.condition}")
        else:
            logger.warning(f"条件边缺少条件表达式: {edge.from_node} -> {edge.to_node}")
    
    def _get_condition_function(self, condition_name: str) -> Optional[Callable]:
        """获取条件函数
        
        Args:
            condition_name: 条件函数名称
            
        Returns:
            Optional[Callable]: 条件函数
        """
        # 从函数解析器获取条件函数
        condition_function = self._function_resolver.get_condition_function(condition_name)
        if condition_function:
            logger.debug(f"从函数解析器获取条件函数: {condition_name}")
            return condition_function
        
        logger.warning(f"无法找到条件函数: {condition_name}")
        return None