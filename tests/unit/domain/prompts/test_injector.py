"""提示词注入器测试"""

import pytest
from unittest.mock import Mock

from src.domain.prompts.injector import PromptInjector
from src.domain.prompts.interfaces import IPromptLoader
from src.domain.prompts.models import PromptConfig
from src.application.workflow.state import AgentState, SystemMessage, HumanMessage


class TestPromptInjector:
    """提示词注入器测试类"""
    
    @pytest.fixture
    def mock_loader(self):
        """模拟提示词加载器"""
        loader = Mock(spec=IPromptLoader)
        
        # 模拟加载不同类型的提示词
        loader.load_prompt.side_effect = lambda category, name: {
            ("system", "assistant"): "你是一个通用助手。",
            ("system", "coder"): "你是一个代码生成专家。",
            ("rules", "safety"): "请遵循安全规则。",
            ("rules", "format"): "请遵循格式规则。",
            ("user_commands", "data_analysis"): "请分析数据。",
            ("user_commands", "code_review"): "请审查代码。"
        }.get((category, name))
        
        return loader
    
    @pytest.fixture
    def injector(self, mock_loader):
        """创建提示词注入器实例"""
        return PromptInjector(mock_loader)
    
    @pytest.fixture
    def empty_state(self):
        """创建空的Agent状态"""
        return {
            "messages": [],
            "input": "",
            "output": None,
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False,
            "metadata": {}
        }
    
    def test_inject_system_prompt(self, injector, empty_state) -> None:
        """测试注入系统提示词"""
        state = injector.inject_system_prompt(empty_state, "assistant")
        
        assert len(state.messages) == 1
        assert isinstance(state.messages[0], SystemMessage)
        assert state.messages[0].content == "你是一个通用助手。"
    
    def test_inject_rule_prompts(self, injector, empty_state) -> None:
        """测试注入规则提示词"""
        state = injector.inject_rule_prompts(empty_state, ["safety", "format"])
        
        assert len(state.messages) == 2
        assert all(isinstance(msg, SystemMessage) for msg in state.messages)
        assert state.messages[0].content == "请遵循安全规则。"
        assert state.messages[1].content == "请遵循格式规则。"
    
    def test_inject_user_command(self, injector, empty_state) -> None:
        """测试注入用户指令"""
        state = injector.inject_user_command(empty_state, "data_analysis")
        
        assert len(state.messages) == 1
        assert isinstance(state.messages[0], HumanMessage)
        assert state.messages[0].content == "请分析数据。"
    
    def test_inject_prompts_all_types(self, injector, empty_state) -> None:
        """测试注入所有类型的提示词"""
        config = PromptConfig(
            system_prompt="assistant",
            rules=["safety", "format"],
            user_command="data_analysis"
        )
        
        state = injector.inject_prompts(empty_state, config)
        
        assert len(state.messages) == 4
        
        # 验证消息顺序：系统提示词在最前面
        assert isinstance(state.messages[0], SystemMessage)
        assert state.messages[0].content == "你是一个通用助手。"
        
        # 验证规则提示词在中间
        assert isinstance(state.messages[1], SystemMessage)
        assert state.messages[1].content == "请遵循安全规则。"
        assert isinstance(state.messages[2], SystemMessage)
        assert state.messages[2].content == "请遵循格式规则。"
        
        # 验证用户指令在最后
        assert isinstance(state.messages[3], HumanMessage)
        assert state.messages[3].content == "请分析数据。"
    
    def test_inject_prompts_partial_config(self, injector, empty_state) -> None:
        """测试部分配置的提示词注入"""
        # 只有系统提示词
        config = PromptConfig(system_prompt="coder")
        state = injector.inject_prompts(empty_state, config)
        
        assert len(state.messages) == 1
        assert isinstance(state.messages[0], SystemMessage)
        assert state.messages[0].content == "你是一个代码生成专家。"
        
        # 清空状态
        state = {
            "messages": [],
            "input": "",
            "output": None,
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False,
            "metadata": {}
        }
        
        # 只有规则提示词
        config = PromptConfig(rules=["safety"])
        state = injector.inject_prompts(state, config)
        
        assert len(state.messages) == 1
        assert isinstance(state.messages[0], SystemMessage)
        assert state.messages[0].content == "请遵循安全规则。"
        
        # 清空状态
        state = {
            "messages": [],
            "input": "",
            "output": None,
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False,
            "metadata": {}
        }
        
        # 只有用户指令
        config = PromptConfig(user_command="code_review")
        state = injector.inject_prompts(state, config)
        
        assert len(state.messages) == 1
        assert isinstance(state.messages[0], HumanMessage)
        assert state.messages[0].content == "请审查代码。"
    
    def test_inject_prompts_empty_config(self, injector, empty_state) -> None:
        """测试空配置的提示词注入"""
        config = PromptConfig()
        state = injector.inject_prompts(empty_state, config)
        
        assert len(state.messages) == 0
    
    def test_inject_system_prompt_error(self, injector, empty_state) -> None:
        """测试注入系统提示词错误"""
        injector.loader.load_prompt.side_effect = Exception("加载失败")
        
        with pytest.raises(ValueError, match="注入系统提示词失败"):
            injector.inject_system_prompt(empty_state, "assistant")
    
    def test_inject_rule_prompts_error(self, injector, empty_state) -> None:
        """测试注入规则提示词错误"""
        injector.loader.load_prompt.side_effect = Exception("加载失败")
        
        with pytest.raises(ValueError, match="注入规则提示词失败"):
            injector.inject_rule_prompts(empty_state, ["safety"])
    
    def test_inject_user_command_error(self, injector, empty_state) -> None:
        """测试注入用户指令错误"""
        injector.loader.load_prompt.side_effect = Exception("加载失败")
        
        with pytest.raises(ValueError, match="注入用户指令失败"):
            injector.inject_user_command(empty_state, "data_analysis")
    
    def test_inject_prompts_with_existing_messages(self, injector) -> None:
        """测试向已有消息的状态注入提示词"""
        # 创建已有消息的状态
        existing_state = {
            "messages": [],
            "input": "",
            "output": None,
            "tool_calls": [],
            "tool_results": [],
            "iteration_count": 0,
            "max_iterations": 10,
            "errors": [],
            "complete": False,
            "metadata": {}
        }
        existing_state["messages"].append(HumanMessage(content="用户问题"))  # type: ignore
        
        config = PromptConfig(
            system_prompt="assistant",
            rules=["safety"]
        )
        
        state = injector.inject_prompts(existing_state, config)
        
        assert len(state.messages) == 3
        
        # 验证系统提示词在最前面
        assert isinstance(state.messages[0], SystemMessage)
        assert state.messages[0].content == "你是一个通用助手。"
        
        # 验证规则提示词在中间
        assert isinstance(state.messages[1], SystemMessage)
        assert state.messages[1].content == "请遵循安全规则。"
        
        # 验证原有消息在最后
        assert isinstance(state.messages[2], HumanMessage)
        assert state.messages[2].content == "用户问题"
