from typing import Dict, Any, List, Callable, Union
from datetime import datetime
import logging
from src.domain.agent.state import AgentState as DomainAgentState
from src.infrastructure.graph.adapters.state_adapter import StateAdapter
from src.domain.state.interfaces import IStateCollaborationManager

logger = logging.getLogger(__name__)


class CollaborationStateAdapter:
    """协作状态适配器 - 重构版本"""
    
    def __init__(self, collaboration_manager: IStateCollaborationManager):
        self.state_adapter = StateAdapter()
        self.collaboration_manager = collaboration_manager
    
    def execute_with_collaboration(
        self,
        graph_state: Union[Dict[str, Any], Any],
        node_executor: Callable[[DomainAgentState], DomainAgentState]
    ) -> Union[Dict[str, Any], Any]:
        """带协作机制的状态转换
        
        Args:
            graph_state: 图系统状态
            node_executor: 节点执行函数，接收域状态并返回修改后的域状态
            
        Returns:
            转换后的图系统状态
        """
        # 1. 转换为域状态
        domain_state = self.state_adapter.from_graph_state(graph_state)
        
        # 2. 状态验证
        validation_errors = self._validate_state(domain_state)
        
        # 3. 记录状态变化开始
        snapshot_id = self._create_pre_execution_snapshot(domain_state)
        
        # 4. 执行业务逻辑（关键修复）
        try:
            result_domain_state = node_executor(domain_state)
            logger.debug(f"节点执行成功，agent_id: {domain_state.agent_id}")
        except Exception as e:
            logger.error(f"节点执行失败，agent_id: {domain_state.agent_id}, 错误: {str(e)}")
            # 记录执行错误
            self._record_execution_error(domain_state, snapshot_id, str(e))
            raise
        
        # 5. 记录状态变化结束
        self._record_state_completion(result_domain_state, snapshot_id, validation_errors)
        
        # 6. 转换回图状态
        result_state = self.state_adapter.to_graph_state(result_domain_state)
        
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
    
    def _record_execution_error(self, domain_state: DomainAgentState,
                               snapshot_id: str, error_message: str):
        """记录执行错误"""
        try:
            self.collaboration_manager.record_state_change(
                domain_state.agent_id,
                "execution_error",
                {},
                {"error": error_message, "snapshot_id": snapshot_id}
            )
        except Exception as e:
            logger.error(f"记录执行错误失败: {str(e)}")
    
    def _record_state_completion(self, domain_state: DomainAgentState,
                               snapshot_id: str, validation_errors: List[str]):
        """记录状态完成"""
        try:
            # 记录执行完成
            self.collaboration_manager.record_state_change(
                domain_state.agent_id,
                "execution_completed",
                {"snapshot_id": snapshot_id, "validation_errors": validation_errors},
                domain_state.to_dict() if hasattr(domain_state, 'to_dict') else vars(domain_state)
            )
        except Exception as e:
            logger.error(f"记录状态完成失败: {str(e)}")
    
    def _add_collaboration_metadata(self, graph_state: Dict[str, Any],
                                  snapshot_id: str, validation_errors: List[str]) -> Dict[str, Any]:
        """添加协作元数据"""
        if "metadata" not in graph_state:
            graph_state["metadata"] = {}
        
        graph_state["metadata"].update({
            "collaboration_snapshot_id": snapshot_id,
            "validation_errors": validation_errors,
            "collaboration_timestamp": datetime.now().isoformat(),
            "collaboration_enabled": True
        })
        
        return graph_state