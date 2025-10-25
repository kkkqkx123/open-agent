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
        self.mock_config_loader.load_config.return_value = {
            "name": "test_agent",
            "agent_type": "react",
            "system_prompt": "Test system prompt",
            "tools": ["calculator", "web_search"]
        }
        
        # 加载配置
        config = self.config_loader.load_config("test_agent")
        
        # 验证配置加载器被调用
        self.mock_config_loader.load_config.assert_called_once_with("agents/test_agent.yaml")
        
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
        self.mock_config_loader.load_config.return_value = {
            "name": "test_agent",
            "agent_type": "plan_execute",
            "system_prompt": "Test system prompt for plan-execute",
            "decision_strategy": "sequential",
            "max_iterations": 5,
            "timeout": 30
        }
        
        # 加载配置
        config = self.config_loader.load_config("test_agent")
        
        # 验证返回的配置
        assert isinstance(config, AgentConfig)
        assert config.name == "test_agent"
        assert config.agent_type == "plan_execute"
        assert config.system_prompt == "Test system prompt for plan-execute"
        assert config.decision_strategy == "sequential"
        assert config.max_iterations == 5
        assert config.timeout == 30
    
    def test_load_config_with_missing_required_fields(self):
        """测试加载缺少必需字段的配置"""
        # 配置mock返回值（缺少必需字段）
        self.mock_config_loader.load_config.return_value = {
            "name": "test_agent",
            "agent_type": "react"
            # 缺少system_prompt
        }
        
        # 应该抛出验证错误
        with pytest.raises(ValueError, match="system_prompt"):
            self.config_loader.load_config("test_agent")
    
    def test_load_nonexistent_config(self):
        """测试加载不存在的配置"""
        # 配置mock抛出异常
        self.mock_config_loader.load_config.side_effect = FileNotFoundError("Config file not found")
        
        # 应该抛出FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.config_loader.load_config("nonexistent_agent")
    
    def test_load_config_with_environment_variables(self):
        """测试加载包含环境变量的配置"""
        # 配置mock返回值（包含环境变量占位符）
        self.mock_config_loader.load_config.return_value = {
            "name": "test_agent",
            "agent_type": "react",
            "system_prompt": "Test system prompt with ${API_KEY}",
            "tools": ["${TOOL_NAME}"]
        }
        
        # 模拟环境变量
        with patch.dict("os.environ", {"API_KEY": "test_key", "TOOL_NAME": "calculator"}):
            # 加载配置
            config = self.config_loader.load_config("test_agent")
            
            # 验证配置加载器被调用
            self.mock_config_loader.load_config.assert_called_once_with("agents/test_agent.yaml")
            
            # 验证返回的配置（环境变量应该被替换）
            assert isinstance(config, AgentConfig)
            assert config.system_prompt == "Test system prompt with test_key"
            assert config.tools == ["calculator"]