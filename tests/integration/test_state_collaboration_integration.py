"""状态协作功能集成测试"""

import pytest
from typing import List, Optional, Dict, Any
from src.domain.state.enhanced_manager import EnhancedStateManager
from src.infrastructure.state.snapshot_store import StateSnapshotStore
from src.infrastructure.state.history_manager import StateHistoryManager
from src.infrastructure.graph.adapters.collaboration_adapter import CollaborationStateAdapter
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.di_config import DIConfig
from src.domain.state.interfaces import IStateCollaborationManager
from src.infrastructure.graph.states import WorkflowState as DomainAgentState


class MockDomainState:
    """模拟域状态对象"""
    def __init__(self, agent_id: str = "test_agent", messages: Optional[List[str]] = None):
        self.agent_id = agent_id
        self.messages = messages or []
        self.iteration_count = 0
        self.max_iterations = 10
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "messages": self.messages,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations
        }


def test_full_state_collaboration_workflow() -> None:
    """测试完整的状态协作工作流"""
    # 1. 创建状态管理组件
    snapshot_store = StateSnapshotStore()
    history_manager = StateHistoryManager()
    state_manager = EnhancedStateManager(snapshot_store, history_manager)
    
    # 2. 创建协作适配器
    adapter = CollaborationStateAdapter(state_manager)
    
    # 3. 测试状态验证
    domain_state = MockDomainState(agent_id="test_agent", messages=["hello"])
    errors = state_manager.validate_domain_state(domain_state)
    assert len(errors) == 0
    
    # 4. 测试快照功能
    snapshot_id = state_manager.save_snapshot(domain_state, "initial_state")
    assert snapshot_id is not None
    
    # 5. 测试历史记录功能
    history_id = state_manager.create_state_history_entry(domain_state, "initial_state_action")
    assert history_id is not None
    
    # 6. 测试协作适配器
    graph_state = {
        "messages": [],
        "tool_results": [],
        "current_step": "test_step",
        "max_iterations": 10,
        "iteration_count": 0,
        "workflow_name": "test_workflow",
        "start_time": None,
        "errors": [],
        "input": "test input",
        "output": None,
        "tool_calls": [],
        "complete": False,
        "metadata": {}
    }
    
    # 定义节点执行函数
    def mock_node_executor(domain_state: DomainAgentState) -> DomainAgentState:
        return domain_state
    
    result = adapter.execute_with_collaboration(graph_state, mock_node_executor)
    assert result is not None
    assert "metadata" in result
    assert "collaboration_snapshot_id" in result["metadata"]
    
    # 7. 验证历史记录
    history = state_manager.get_state_history("test_agent")
    assert len(history) >= 1
    
    # 8. 验证快照历史
    snapshot_history = state_manager.get_snapshot_history("test_agent")
    assert len(snapshot_history) >= 1
    
    print("集成测试通过：完整的状态协作工作流正常运行")


def test_di_config_integration() -> None:
    """测试依赖注入配置集成"""
    # 创建依赖注入配置
    di_config = DIConfig()
    
    # 配置核心服务
    container = di_config.configure_core_services()
    
    # 验证状态协作管理器是否已注册
    assert container.has_service(IStateCollaborationManager)
    
    print("集成测试通过：依赖注入配置正确注册了状态协作管理器")


if __name__ == "__main__":
    test_full_state_collaboration_workflow()
    test_di_config_integration()
    print("所有集成测试通过！")