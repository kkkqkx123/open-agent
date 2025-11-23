"""下一节点解析器

提供工作流执行中下一节点解析的公共逻辑。
"""

from typing import Dict, Any, List
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state import IWorkflowState, IState


class NextNodesResolver:
    """下一节点解析器
    
    负责根据当前节点和状态解析下一个可执行的节点列表。
    """
    
    @staticmethod
    def get_next_nodes(workflow: IWorkflow, node_id: str, 
                      state: IWorkflowState, config: Dict[str, Any]) -> List[str]:
        """获取下一个节点列表
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        next_nodes = []
        
        # 获取所有出边
        for edge in workflow._edges.values():
            if edge.from_node == node_id:
                # 检查是否可以遍历
                # 直接使用状态，因为接口已经统一
                # IWorkflowState 现在兼容 IState 接口
                if hasattr(edge, 'can_traverse_with_config'):
                    if edge.can_traverse_with_config(state, config):  # type: ignore
                        next_node_ids = edge.get_next_nodes(state, config)  # type: ignore
                        next_nodes.extend(next_node_ids)
        
        return next_nodes
    
    @staticmethod
    async def get_next_nodes_async(workflow: IWorkflow, node_id: str, 
                                 state: IWorkflowState, config: Dict[str, Any]) -> List[str]:
        """异步获取下一个节点列表
        
        Args:
            workflow: 工作流实例
            node_id: 当前节点ID
            state: 当前状态
            config: 配置
            
        Returns:
            List[str]: 下一个节点ID列表
        """
        next_nodes = []
        
        # 获取所有出边
        for edge in workflow._edges.values():
            if edge.from_node == node_id:
                # 检查是否可以遍历
                # 直接使用状态，因为接口已经统一
                # IWorkflowState 现在兼容 IState 接口
                if hasattr(edge, 'can_traverse_async'):
                    can_traverse = await edge.can_traverse_async(state, config)  # type: ignore
                else:
                    can_traverse = edge.can_traverse_with_config(state, config)  # type: ignore
                
                if can_traverse:
                    if hasattr(edge, 'get_next_nodes_async'):
                        next_node_ids = await edge.get_next_nodes_async(state, config)  # type: ignore
                    else:
                        next_node_ids = edge.get_next_nodes(state, config)  # type: ignore
                    next_nodes.extend(next_node_ids)
        
        return next_nodes