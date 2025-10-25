"""连接池配置模型单元测试"""

import pytest
from src.infrastructure.config.models.connection_pool_config import ConnectionPoolConfig


class TestConnectionPoolConfig:
    """连接池配置模型测试"""
    
    def test_default_values(self):
        """测试默认值"""
        config = ConnectionPoolConfig()
        
        assert config.max_connections == 10
        assert config.max_keepalive == 10
        assert config.timeout == 30.0
        assert config.keepalive_expiry == 300.0
        assert config.enabled is True
    
    def test_custom_values(self):
        """测试自定义值"""
        config = ConnectionPoolConfig(
            max_connections=20,
            max_keepalive=15,
            timeout=60.0,
            keepalive_expiry=600.0,
            enabled=False
        )
        
        assert config.max_connections == 20
        assert config.max_keepalive == 15
        assert config.timeout == 60.0
        assert config.keepalive_expiry == 600.0
        assert config.enabled is False
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = ConnectionPoolConfig(
            max_connections=20,
            max_keepalive=15,
            timeout=60.0,
            keepalive_expiry=600.0,
            enabled=False
        )
        
        config_dict = config.model_dump()
        
        assert config_dict["max_connections"] == 20
        assert config_dict["max_keepalive"] == 15
        assert config_dict["timeout"] == 60.0
        assert config_dict["keepalive_expiry"] == 600.0
        assert config_dict["enabled"] is False
    
    def test_hashable(self):
        """测试可哈希性"""
        config1 = ConnectionPoolConfig(max_connections=10)
        config2 = ConnectionPoolConfig(max_connections=10)
        config3 = ConnectionPoolConfig(max_connections=20)
        
        # 验证可以作为字典键使用
        test_dict = {config1: "value1"}
        
        # 相同配置应该有相同的哈希值
        assert hash(config1) == hash(config2)
        
        # 不同配置应该有不同的哈希值
        assert hash(config1) != hash(config3)