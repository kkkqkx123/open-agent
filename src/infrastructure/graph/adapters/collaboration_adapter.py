from typing import Dict, Any, List
from datetime import datetime
from src.domain.agent.state import AgentState as DomainAgentState
from src.infrastructure.graph.adapters.state_adapter import StateAdapter
from src.domain.state.interfaces import IStateCollaborationManager


class CollaborationStateAdapter:
    """协作状态适配器"""
    
    def __init__(self, collaboration_manager: IStateCollaborationManager):
        self.state_adapter = StateAdapter()
        self.collaboration_manager = collaboration_manager
    
    def execute_with_collaboration(self, graph_state: Dict[str, Any]) -> Dict[str, Any]:
        """带协作机制的状态转换"""
        # 1. 转换为域状态
        domain_state = self.state_adapter.from_graph_state(graph_state)
        
        # 2. 状态验证
        validation_errors = self._validate_state(domain_state)
        
        # 3. 记录状态变化开始
        snapshot_id = self._create_pre_execution_snapshot(domain_state)
        
        # 4. 执行业务逻辑（由具体节点实现）
        # 这里domain_state会被节点修改
        
        # 5. 记录状态变化结束
        self._record_state_completion(domain_state, snapshot_id, validation_errors)
        
        # 6. 转换回图状态
        result_state = self.state_adapter.to_graph_state(domain_state)
        
        # 7. 添加协作元数据
        return self._add_collaboration_metadata(result_state, snapshot_id, validation_errors)
    
    def _validate_state(self, domain_state: DomainAgentState) -> List[str]:
        """状态验证"""
        return self.collaboration_manager.validate_domain_state(domain_state)
    
    def _create_pre_execution_snapshot(self, domain_state: DomainAgentState) -> str:
        """创建执行前快照"""
        return self.collaboration_manager.create_snapshot(
            domain_state, "pre_execution"
        )
    
    def _record_state_completion(self, domain_state: DomainAgentState, 
                               snapshot_id: str, validation_errors: List[str]):
        """记录状态完成"""
        # 可以在这里添加完成后的处理逻辑
        pass
    
    def _add_collaboration_metadata(self, graph_state: Dict[str, Any], 
                                  snapshot_id: str, validation_errors: List[str]) -> Dict[str, Any]:
        """添加协作元数据"""
        if "metadata" not in graph_state:
            graph_state["metadata"] = {}
        
        graph_state["metadata"].update({
            "collaboration_snapshot_id": snapshot_id,
            "validation_errors": validation_errors,
            "collaboration_timestamp": datetime.now().isoformat()
        })
        
        return graph_state