"""LangGraph适配器

提供与LangGraph框架的集成，将核心工作流模型转换为LangGraph格式。
这是纯适配器，不包含业务逻辑，只负责框架集成。
"""

from typing import Dict, Any, Optional, List
import logging
from langgraph.graph import START, END

logger = logging.getLogger(__name__)


class LangGraphAdapter:
    """LangGraph适配器
    
    将核心工作流模型转换为LangGraph格式，提供框架特定的优化。
    """
    
    def __init__(self):
        """初始化适配器"""
        self._compiled_graphs: Dict[str, Any] = {}
    
    def convert_to_langgraph(self, core_graph: Any) -> Any:
        """将核心图转换为LangGraph格式
        
        Args:
            core_graph: 核心图实例（由GraphBuilder构建）
            
        Returns:
            Any: 编译后的LangGraph图
        """
        # 由于核心层的GraphBuilder已经构建了LangGraph图
        # 这里主要是提供缓存和适配功能
        if hasattr(core_graph, 'compiled') and core_graph.compiled:
            # 如果已经是编译后的图，直接返回
            return core_graph
        else:
            # 如果不是编译后的图，进行编译
            compiled_graph = core_graph.compile()
            return compiled_graph
    
    def get_compiled_graph(self, workflow_id: str) -> Optional[Any]:
        """获取编译后的图
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[Any]: 编译后的图，如果不存在则返回None
        """
        return self._compiled_graphs.get(workflow_id)
    
    def cache_graph(self, workflow_id: str, graph: Any) -> None:
        """缓存编译后的图
        
        Args:
            workflow_id: 工作流ID
            graph: 编译后的图
        """
        self._compiled_graphs[workflow_id] = graph
        logger.debug(f"缓存LangGraph图: {workflow_id}")
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._compiled_graphs.clear()
        logger.info("清除LangGraph图缓存")
    
    def get_cached_graph_ids(self) -> List[str]:
        """获取缓存的图ID列表
        
        Returns:
            List[str]: 缓存的图ID列表
        """
        return list(self._compiled_graphs.keys())