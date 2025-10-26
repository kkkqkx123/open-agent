"""Agent配置加载器单元测试"""

import pytest
from unittest.mock import Mock, patch, mock_open
from src.domain.agent.config_loader import AgentConfigLoader
from src.domain.agent import AgentConfig


class TestAgentConfigLoader:
    """AgentConfigLoader测试类"""
    
    def setup_method(self):
        """测试方法初始化"""
        self.mock_config_loader = Mock()
        self.config_loader = AgentConfigLoader(self.mock_config_loader)
    
    @patch("builtins.open", new_callable=mock_open, read_data="""
name: test_agent
agent_type: react
system_prompt: Test system prompt
tools:
  - calculator
  - web_search
""")
    def test_load_config_from_yaml_file(self, mock_file):
        """测试从YAML文件加载配置"""
        # 配置mock返回值
        self.mock_config_loader.load.return_value = {
            "name": "test_agent",
            "agent_type": "react",
            "system_prompt": "Test system prompt",
            "tools": ["calculator", "web_search"]
        }
        
        # 加载配置
        config = self.config_loader.load_agent_config("test_agent")
        
        # 验证配置加载器被调用
        self.mock_config_loader.load.assert_called_once_with("agents/test_agent.yaml")

        # 验证返回的配置
        assert isinstance(config, AgentConfig)
        assert config.name == "test_agent"
        assert config.agent_type == "react"
        assert config.system_prompt == "Test system prompt"
        assert config.tools == ["calculator", "web_search"]

    @patch("builtins.open", new_callable=mock_open, read_data="""
name: test_agent
agent_type: plan_execute
system_prompt: Test system prompt for plan-execute
decision_strategy: sequential
max_iterations: 5
timeout: 30
""")
    def test_load_config_with_all_fields(self, mock_file):
        """测试加载包含所有字段的配置"""
        # 配置mock返回值
        self.mock_config_loader.load.return_value = {
            "name": "test_agent",
            "agent_type": "plan_execute",
            "system_prompt": "Test system prompt for plan-execute",
            "decision_strategy": "sequential",
            "max_iterations": 5,
            "timeout": 30
        }

        # 加载配置
        config = self.config_loader.load_agent_config("test_agent")
        
        # 验证返回的配置
        assert isinstance(config, AgentConfig)
        assert config.name == "test_agent"
        assert config.agent_type == "plan_execute"
        assert config.system_prompt == "Test system prompt for plan-execute"
        assert config.decision_strategy == "sequential"
        assert config.max_iterations == 5
        assert config.timeout == 30
    
    def test_load_config_with_invalid_field_types(self):
        """测试加载包含无效字段类型的配置"""
        # 配置mock返回值（包含无效字段类型）
        self.mock_config_loader.load.return_value = {
            "name": "test_agent",
            "agent_type": "react",
            "system_prompt": 123,  # 应该是字符串，不是整数
            "tools": "not_a_list"  # 应该是列表，不是字符串
        }
        
        # 应该抛出验证错误
        with pytest.raises(Exception):  # Pydantic会抛出ValidationError
            self.config_loader.load_agent_config("test_agent")
    
    def test_load_nonexistent_config(self):
        """测试加载不存在的配置"""
        # 配置mock抛出异常
        self.mock_config_loader.load.side_effect = FileNotFoundError("Config file not found")
        
        # 应该抛出FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.config_loader.load_agent_config("nonexistent_agent")
    
    def test_load_config_with_environment_variables(self):
        """测试加载包含环境变量的配置"""
        # 配置mock返回值（包含环境变量占位符）
        self.mock_config_loader.load.return_value = {
            "name": "test_agent",
            "agent_type": "react",
            "system_prompt": "Test system prompt with test_key",  # 预处理后的值
            "tools": ["calculator"]  # 预处理后的值
        }
        
        # 模拟环境变量
        with patch.dict("os.environ", {"API_KEY": "test_key", "TOOL_NAME": "calculator"}):
            # 加载配置
            config = self.config_loader.load_agent_config("test_agent")
            
            # 验证配置加载器被调用
            self.mock_config_loader.load.assert_called_once_with("agents/test_agent.yaml")
            
            # 验证返回的配置
            assert isinstance(config, AgentConfig)
            assert config.system_prompt == "Test system prompt with test_key"
            assert config.tools == ["calculator"]
    
    def test_load_config_with_memory_config(self):
        """测试加载包含记忆配置的配置"""
        # 配置mock返回值（包含记忆配置）
        self.mock_config_loader.load.return_value = {
            "name": "test_agent",
            "agent_type": "react",
            "system_prompt": "Test system prompt",
            "memory_config": {
                "enabled": False,
                "max_tokens": 1000,
                "max_messages": 20,
                "retention_time": 1800
            }
        }
        
        # 加载配置
        config = self.config_loader.load_agent_config("test_agent")
        
        # 验证返回的配置
        assert isinstance(config, AgentConfig)
        assert config.name == "test_agent"
        assert config.memory_config.enabled is False
        assert config.memory_config.max_tokens == 1000
        assert config.memory_config.max_messages == 20
        assert config.memory_config.retention_time == 1800