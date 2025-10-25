"""Agent配置系统单元测试"""

import pytest
from src.domain.agent import AgentConfig
from src.domain.agent.config import MemoryConfig


class TestAgentConfig:
    """AgentConfig测试类"""
    
    def test_agent_config_creation_with_required_fields(self):
        """测试使用必需字段创建Agent配置"""
        config = AgentConfig(
            name="test_agent",
            agent_type="react",
            system_prompt="Test system prompt"
        )
        
        assert config.name == "test_agent"
        assert config.agent_type == "react"
        assert config.system_prompt == "Test system prompt"
        assert config.description == ""
        assert config.tools == []
        assert config.tool_sets == []
    
    def test_agent_config_creation_with_all_fields(self):
        """测试使用所有字段创建Agent配置"""
        memory_config = MemoryConfig(
            max_tokens=1000,
            max_messages=10
        )
        
        config = AgentConfig(
            name="test_agent",
            description="A test agent for calculations",
            agent_type="plan_execute",
            system_prompt="Test system prompt",
            decision_strategy="sequential",
            memory_config=memory_config,
            tools=["calculator", "web_search"],
            tool_sets=["math_tools"],
            max_iterations=5,
            timeout=30,
            retry_count=2
        )
        
        assert config.name == "test_agent"
        assert config.description == "A test agent for calculations"
        assert config.agent_type == "plan_execute"
        assert config.system_prompt == "Test system prompt"
        assert config.decision_strategy == "sequential"
        assert config.memory_config.max_tokens == 1000
        assert config.memory_config.max_messages == 10
        assert config.tools == ["calculator", "web_search"]
        assert config.tool_sets == ["math_tools"]
        assert config.max_iterations == 5
        assert config.timeout == 30
        assert config.retry_count == 2
    
    def test_agent_config_default_values(self):
        """测试Agent配置的默认值"""
        config = AgentConfig(
            name="test_agent",
            agent_type="react",
            system_prompt="Test system prompt"
        )
        
        assert config.description == ""
        assert config.decision_strategy == "auto"
        assert config.memory_config.max_tokens == 2000
        assert config.memory_config.max_messages == 50
        assert config.tools == []
        assert config.tool_sets == []
        assert config.max_iterations == 10
        assert config.timeout == 60
        assert config.retry_count == 0
    
    def test_agent_config_validation(self):
        """测试Agent配置验证"""
        # 测试缺少必需字段
        with pytest.raises(ValueError):
            AgentConfig(
                name="test_agent",
                agent_type="react"
                # 缺少system_prompt
            )
        
        # 测试空名称
        with pytest.raises(ValueError):
            AgentConfig(
                name="",  # 空名称
                agent_type="react",
                system_prompt="Test system prompt"
            )
        
        # 测试空agent_type
        with pytest.raises(ValueError):
            AgentConfig(
                name="test_agent",
                agent_type="",  # 空agent_type
                system_prompt="Test system prompt"
            )
        
        # 测试空system_prompt
        with pytest.raises(ValueError):
            AgentConfig(
                name="test_agent",
                agent_type="react",
                system_prompt=""  # 空system_prompt
            )
    
    def test_memory_config_default_values(self):
        """测试MemoryConfig的默认值"""
        memory_config = MemoryConfig()
        
        assert memory_config.max_tokens == 2000
        assert memory_config.max_messages == 50
    
    def test_memory_config_custom_values(self):
        """测试MemoryConfig的自定义值"""
        memory_config = MemoryConfig(
            max_tokens=1500,
            max_messages=20
        )
        
        assert memory_config.max_tokens == 1500
        assert memory_config.max_messages == 20