"""提示词代理模板测试

测试新的提示词代理模板功能。
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Any, cast
from src.core.workflow.templates.prompt_agent import PromptAgentTemplate, SimplePromptAgentTemplate
from src.services.prompts.injector import PromptInjector
from src.services.prompts.loader import PromptLoader
from src.services.prompts.registry import PromptRegistry
from src.interfaces.prompts import PromptConfig
from src.interfaces.state import IWorkflowState


class TestPromptAgentTemplate:
    """测试提示词代理模板"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建模拟的提示词注入器
        self.mock_injector = Mock(spec=PromptInjector)
        self.mock_injector.inject_prompts.return_value = {"messages": []}
        
        # 创建模板实例
        self.template = PromptAgentTemplate(prompt_injector=self.mock_injector)
    
    def test_template_creation(self):
        """测试模板创建"""
        assert self.template.name == "prompt_agent"
        assert self.template.category == "agent"
        assert self.template.version == "1.0"
        assert "基于提示词注入的代理工作流模板" in self.template.description
    
    def test_template_parameters(self):
        """测试模板参数"""
        params = self.template.get_parameters()
        param_names = [p["name"] for p in params]
        
        assert "llm_client" in param_names
        assert "system_prompt" in param_names
        assert "rules" in param_names
        assert "user_command" in param_names
        assert "cache_enabled" in param_names
    
    def test_default_prompt_config(self):
        """测试默认提示词配置"""
        config = self.template.get_default_prompt_config()
        
        assert isinstance(config, PromptConfig)
        assert config.system_prompt == "assistant"
        assert config.rules == ["safety", "format"]
        assert config.user_command == "data_analysis"
        assert config.cache_enabled is True
    
    def test_inject_prompts_to_state(self):
        """测试提示词注入到状态"""
        state: dict[str, Any] = {"messages": []}
        # 配置 Mock 返回相同的状态对象
        self.mock_injector.inject_prompts.return_value = cast(IWorkflowState, state)
        
        config = PromptConfig(
            system_prompt="test",
            rules=["rule1"],
            user_command="test_command",
            cache_enabled=True
        )
        
        result = self.template.inject_prompts_to_state(state, config)
        
        # 验证注入器被调用
        self.mock_injector.inject_prompts.assert_called_once()
        assert result is not None
    
    def test_inject_prompts_to_state_without_injector(self):
        """测试没有注入器时的提示词注入"""
        template = PromptAgentTemplate(prompt_injector=None)
        state: dict[str, Any] = {"messages": []}
        
        result = template.inject_prompts_to_state(state)
        
        # 应该返回原始状态
        assert result is state
    
    def test_create_prompt_config(self):
        """测试从配置创建提示词配置"""
        config_dict = {
            "system_prompt": "test_system",
            "rules": ["rule1", "rule2"],
            "user_command": "test_command",
            "cache_enabled": False
        }
        
        config = self.template.create_prompt_config(config_dict)
        
        assert config.system_prompt == "test_system"
        assert config.rules == ["rule1", "rule2"]
        assert config.user_command == "test_command"
        assert config.cache_enabled is False
    
    def test_workflow_creation(self):
        """测试工作流创建"""
        config = {
            "llm_client": "test_llm",
            "system_prompt": "test_system",
            "rules": ["rule1"],
            "user_command": "test_command",
            "cache_enabled": True
        }
        
        workflow = self.template.create_workflow(
            name="test_workflow",
            description="测试工作流",
            config=config
        )
        
        assert workflow.name == "test_workflow"
        assert workflow.description == "测试工作流"
        assert workflow.entry_point == "inject_prompts"
    
    def test_workflow_validation(self):
        """测试工作流验证"""
        # 测试有效配置
        valid_config = {
            "llm_client": "test_llm",
            "system_prompt": "test_system"
        }
        
        errors = self.template.validate_parameters(valid_config)
        assert len(errors) == 0
        
        # 测试无效配置
        invalid_config = {
            "cache_enabled": "not_boolean"  # 应该是布尔值
        }
        
        errors = self.template.validate_parameters(invalid_config)
        assert len(errors) > 0


class TestSimplePromptAgentTemplate:
    """测试简单提示词代理模板"""
    
    def setup_method(self):
        """设置测试环境"""
        self.mock_injector = Mock(spec=PromptInjector)
        self.mock_injector.inject_prompts.return_value = {"messages": []}
        
        self.template = SimplePromptAgentTemplate(prompt_injector=self.mock_injector)
    
    def test_template_creation(self):
        """测试模板创建"""
        assert self.template.name == "simple_prompt_agent"
        assert self.template.category == "agent"
        assert "简化的提示词代理工作流模板" in self.template.description
    
    def test_simplified_parameters(self):
        """测试简化参数"""
        params = self.template.get_parameters()
        param_names = [p["name"] for p in params]
        
        # 简化模板只有基本参数
        assert "llm_client" in param_names
        assert "system_prompt" in param_names
        assert len(params) == 2
    
    def test_simplified_default_config(self):
        """测试简化默认配置"""
        config = self.template.get_default_prompt_config()
        
        assert config.system_prompt == "assistant"
        assert config.rules == ["safety"]  # 简化的规则
        assert config.user_command == "general"  # 通用命令
        assert config.cache_enabled is True


class TestPromptIntegration:
    """测试提示词集成功能"""
    
    def setup_method(self):
        """设置测试环境"""
        # 创建真实的提示词组件（使用模拟）
        self.mock_registry = Mock(spec=PromptRegistry)
        self.mock_loader = Mock(spec=PromptLoader)
        self.mock_injector = PromptInjector(self.mock_loader)
    
    def test_end_to_end_workflow_creation(self):
        """测试端到端工作流创建"""
        # 模拟提示词加载
        self.mock_loader.load_prompt.return_value = "测试提示词内容"
        
        # 创建模板
        template = PromptAgentTemplate(prompt_injector=self.mock_injector)
        
        # 创建工作流
        config = {
            "llm_client": "test_llm",
            "system_prompt": "test_system",
            "rules": ["rule1"],
            "user_command": "test_command"
        }
        
        workflow = template.create_workflow(
            name="end_to_end_test",
            description="端到端测试",
            config=config
        )
        
        # 验证工作流创建成功
        assert workflow is not None
        assert workflow.name == "end_to_end_test"
        assert len(workflow._nodes) > 0
        assert len(workflow._edges) > 0
    
    def test_prompt_injection_integration(self):
        """测试提示词注入集成"""
        # 模拟提示词加载
        self.mock_loader.load_prompt.return_value = "测试提示词内容"
        
        # 创建状态字典（真实注入会使用 IWorkflowState，但此处用字典表示）
        state_dict: dict[str, Any] = {"messages": []}
        
        # 创建配置
        config = PromptConfig(
            system_prompt="test_system",
            rules=["rule1"],
            user_command="test_command"
        )
        
        # 注入提示词（使用类型转换处理 IWorkflowState）
        result = self.mock_injector.inject_prompts(
            cast(IWorkflowState, state_dict),
            config
        )
        
        # 验证结果 - 由于 inject_prompts 返回 IWorkflowState，检查返回值是否存在
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__])