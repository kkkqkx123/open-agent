"""测试协作适配器功能"""

import pytest
from unittest.mock import Mock, MagicMock
from src.infrastructure.graph.adapters.collaboration_adapter import CollaborationStateAdapter
from src.domain.state.interfaces import IStateCollaborationManager
from src.infrastructure.graph.state import AgentState


class MockDomainState:
    """模拟域状态对象"""
    def __init__(self, agent_id: str = "test_agent", messages: list = None):
        self.agent_id = agent_id
        self.messages = messages or []


class MockStateCollaborationManager:
    """模拟状态协作管理器"""
    
    def __init__(self):
        self.validation_errors = []
        self.snapshot_created = False
        self.snapshot_id = "test_snapshot_id"
    
    def validate_domain_state(self, domain_state):
        """模拟状态验证"""
        return self.validation_errors
    
    def create_snapshot(self, domain_state, description=""):
        """模拟创建快照"""
        self.snapshot_created = True
        return self.snapshot_id
    
    def restore_snapshot(self, snapshot_id):
        """模拟恢复快照"""
        return MockDomainState()
    
    def record_state_change(self, agent_id, action, old_state, new_state):
        """模拟记录状态变化"""
        return "test_history_id"


class TestCollaborationStateAdapter:
    """测试协作状态适配器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_collaboration_manager = MockStateCollaborationManager()
        self.adapter = CollaborationStateAdapter(self.mock_collaboration_manager)
    
    def test_execute_with_collaboration(self):
        """测试带协作机制的状态转换"""
        # 准备图状态，使用符合实际格式的消息
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
        
        # 执行协作转换
        result = self.adapter.execute_with_collaboration(graph_state)
        
        # 验证结果
        assert result is not None
        assert "metadata" in result
        assert "collaboration_snapshot_id" in result["metadata"]
        assert result["metadata"]["collaboration_snapshot_id"] == "test_snapshot_id"
        
        # 验证快照被创建
        assert self.mock_collaboration_manager.snapshot_created is True
    
    def test_validation_errors_handling(self):
        """测试验证错误处理"""
        # 设置验证错误
        self.mock_collaboration_manager.validation_errors = ["Test validation error"]
        
        # 准备图状态，使用符合实际格式的消息
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
        
        # 执行协作转换
        result = self.adapter.execute_with_collaboration(graph_state)
        
        # 验证错误被记录
        assert "validation_errors" in result["metadata"]
        assert "Test validation error" in result["metadata"]["validation_errors"]


if __name__ == "__main__":
    pytest.main([__file__])