"""Checkpoint配置测试

测试checkpoint配置的创建、验证和转换功能。
"""

import pytest
from src.domain.checkpoint.config import CheckpointConfig, CheckpointMetadata


class TestCheckpointConfig:
    """Checkpoint配置测试类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = CheckpointConfig()
        
        assert config.enabled is True
        assert config.storage_type == "sqlite"
        assert config.auto_save is True
        assert config.save_interval == 5
        assert config.max_checkpoints == 100
        assert config.retention_days == 30
        assert config.trigger_conditions == ["tool_call", "state_change"]
        assert config.db_path is None
        assert config.compression is False
    
    def test_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "enabled": False,
            "storage_type": "memory",
            "auto_save": False,
            "save_interval": 10,
            "max_checkpoints": 50,
            "retention_days": 7,
            "trigger_conditions": ["manual"],
            "db_path": "/tmp/test.db",
            "compression": True
        }
        
        config = CheckpointConfig.from_dict(data)
        
        assert config.enabled is False
        assert config.storage_type == "memory"
        assert config.auto_save is False
        assert config.save_interval == 10
        assert config.max_checkpoints == 50
        assert config.retention_days == 7
        assert config.trigger_conditions == ["manual"]
        assert config.db_path == "/tmp/test.db"
        assert config.compression is True
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = CheckpointConfig(
            enabled=False,
            storage_type="memory",
            auto_save=False,
            save_interval=10,
            max_checkpoints=50,
            retention_days=7,
            trigger_conditions=["manual"],
            db_path="/tmp/test.db",
            compression=True
        )
        
        data = config.to_dict()
        
        assert data["enabled"] is False
        assert data["storage_type"] == "memory"
        assert data["auto_save"] is False
        assert data["save_interval"] == 10
        assert data["max_checkpoints"] == 50
        assert data["retention_days"] == 7
        assert data["trigger_conditions"] == ["manual"]
        assert data["db_path"] == "/tmp/test.db"
        assert data["compression"] is True
    
    def test_validate_valid_config(self):
        """测试有效配置验证"""
        config = CheckpointConfig(
            storage_type="sqlite",
            db_path="/tmp/test.db",
            save_interval=5,
            max_checkpoints=100,
            retention_days=30
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_validate_invalid_storage_type(self):
        """测试无效存储类型"""
        config = CheckpointConfig(storage_type="invalid")
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("不支持的存储类型" in error for error in errors)
    
    def test_validate_invalid_save_interval(self):
        """测试无效保存间隔"""
        config = CheckpointConfig(save_interval=0)
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("保存间隔必须大于0" in error for error in errors)
    
    def test_validate_invalid_max_checkpoints(self):
        """测试无效最大checkpoint数量"""
        config = CheckpointConfig(max_checkpoints=0)
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("最大checkpoint数量必须大于0" in error for error in errors)
    
    def test_validate_invalid_retention_days(self):
        """测试无效保留天数"""
        config = CheckpointConfig(retention_days=0)
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("保留天数必须大于0" in error for error in errors)
    
    def test_validate_sqlite_without_db_path(self):
        """测试SQLite存储缺少数据库路径"""
        config = CheckpointConfig(storage_type="sqlite", db_path=None)
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("SQLite存储需要指定数据库路径" in error for error in errors)


class TestCheckpointMetadata:
    """Checkpoint元数据测试类"""
    
    def test_default_metadata(self):
        """测试默认元数据"""
        metadata = CheckpointMetadata(
            checkpoint_id="test-123",
            session_id="session-456",
            workflow_id="workflow-789"
        )
        
        assert metadata.checkpoint_id == "test-123"
        assert metadata.session_id == "session-456"
        assert metadata.workflow_id == "workflow-789"
        assert metadata.step_count == 0
        assert metadata.node_name is None
        assert metadata.trigger_reason is None
        assert metadata.tags == []
        assert metadata.custom_data == {}
    
    def test_metadata_with_values(self):
        """测试带值的元数据"""
        metadata = CheckpointMetadata(
            checkpoint_id="test-123",
            session_id="session-456",
            workflow_id="workflow-789",
            step_count=5,
            node_name="analysis",
            trigger_reason="tool_call",
            tags=["important", "debug"],
            custom_data={"user": "alice", "debug": True}
        )
        
        assert metadata.step_count == 5
        assert metadata.node_name == "analysis"
        assert metadata.trigger_reason == "tool_call"
        assert metadata.tags == ["important", "debug"]
        assert metadata.custom_data == {"user": "alice", "debug": True}
    
    def test_from_dict(self):
        """测试从字典创建元数据"""
        data = {
            "checkpoint_id": "test-123",
            "session_id": "session-456",
            "workflow_id": "workflow-789",
            "step_count": 5,
            "node_name": "analysis",
            "trigger_reason": "tool_call",
            "tags": ["important", "debug"],
            "custom_data": {"user": "alice", "debug": True}
        }
        
        metadata = CheckpointMetadata.from_dict(data)
        
        assert metadata.checkpoint_id == "test-123"
        assert metadata.session_id == "session-456"
        assert metadata.workflow_id == "workflow-789"
        assert metadata.step_count == 5
        assert metadata.node_name == "analysis"
        assert metadata.trigger_reason == "tool_call"
        assert metadata.tags == ["important", "debug"]
        assert metadata.custom_data == {"user": "alice", "debug": True}
    
    def test_to_dict(self):
        """测试转换为字典"""
        metadata = CheckpointMetadata(
            checkpoint_id="test-123",
            session_id="session-456",
            workflow_id="workflow-789",
            step_count=5,
            node_name="analysis",
            trigger_reason="tool_call",
            tags=["important", "debug"],
            custom_data={"user": "alice", "debug": True}
        )
        
        data = metadata.to_dict()
        
        assert data["checkpoint_id"] == "test-123"
        assert data["session_id"] == "session-456"
        assert data["workflow_id"] == "workflow-789"
        assert data["step_count"] == 5
        assert data["node_name"] == "analysis"
        assert data["trigger_reason"] == "tool_call"
        assert data["tags"] == ["important", "debug"]
        assert data["custom_data"] == {"user": "alice", "debug": True}