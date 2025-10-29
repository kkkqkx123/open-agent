"""测试增强状态管理器功能"""

import pytest
from datetime import datetime
from typing import Dict, Any
from src.domain.state.enhanced_manager import EnhancedStateManager
from src.infrastructure.state.snapshot_store import StateSnapshotStore
from src.infrastructure.state.history_manager import StateHistoryManager


class MockDomainState:
    """模拟域状态对象"""
    def __init__(self, agent_id: str = "test_agent", messages: list = None):
        self.agent_id = agent_id
        self.messages = messages or []
        self.iteration_count = 0
        self.max_iterations = 10
    
    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "messages": self.messages,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations
        }


class TestEnhancedStateManager:
    """测试增强状态管理器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.snapshot_store = StateSnapshotStore()
        self.history_manager = StateHistoryManager()
        self.state_manager = EnhancedStateManager(
            snapshot_store=self.snapshot_store,
            history_manager=self.history_manager
        )
    
    def test_validate_domain_state_valid(self):
        """测试有效的域状态验证"""
        domain_state = MockDomainState(agent_id="test_agent", messages=["hello"])
        
        errors = self.state_manager.validate_domain_state(domain_state)
        assert len(errors) == 0, f"验证失败: {errors}"
    
    def test_validate_domain_state_missing_agent_id(self):
        """测试缺少agent_id的验证"""
        domain_state = MockDomainState(agent_id="", messages=["hello"])
        
        errors = self.state_manager.validate_domain_state(domain_state)
        assert "缺少agent_id字段" in errors
    
    def test_validate_domain_state_missing_messages(self):
        """测试缺少messages的验证"""
        domain_state = MockDomainState(agent_id="test_agent", messages=None)
        # 修改对象以测试验证
        domain_state.messages = None
        
        errors = self.state_manager.validate_domain_state(domain_state)
        assert len(errors) > 0  # 预期会有一些错误
    
    def test_save_and_load_snapshot(self):
        """测试保存和加载快照"""
        domain_state = MockDomainState(agent_id="test_agent", messages=["test message"])
        
        # 保存快照
        snapshot_id = self.state_manager.save_snapshot(domain_state, "test_snapshot")
        assert snapshot_id is not None
        
        # 加载快照
        loaded_state = self.state_manager.load_snapshot(snapshot_id)
        assert loaded_state is not None
        assert loaded_state["agent_id"] == "test_agent"
        assert loaded_state["messages"] == ["test message"]
    
    def test_create_state_history_entry(self):
        """测试创建状态历史记录"""
        domain_state = MockDomainState(agent_id="test_agent", messages=["test message"])
        
        history_id = self.state_manager.create_state_history_entry(domain_state, "test_action")
        assert history_id is not None
        
        # 检查历史记录
        history = self.state_manager.get_state_history("test_agent")
        assert len(history) > 0
        assert history[0]["action"] == "test_action"
    
    def test_get_snapshot_history(self):
        """测试获取快照历史"""
        domain_state = MockDomainState(agent_id="test_agent", messages=["test message"])
        
        # 创建多个快照
        snapshot_id1 = self.state_manager.save_snapshot(domain_state, "snapshot_1")
        snapshot_id2 = self.state_manager.save_snapshot(domain_state, "snapshot_2")
        
        # 获取快照历史
        history = self.state_manager.get_snapshot_history("test_agent")
        assert len(history) >= 2
        snapshot_ids = [item["snapshot_id"] for item in history]
        assert snapshot_id1 in snapshot_ids
        assert snapshot_id2 in snapshot_ids


if __name__ == "__main__":
    pytest.main([__file__])