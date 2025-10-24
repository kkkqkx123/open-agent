"""LangGraph集成模块单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

from src.domain.prompts.langgraph_integration import (
    get_agent_config,
    create_agent_workflow,
    create_simple_workflow,
    LANGGRAPH_AVAILABLE
)
from src.domain.prompts.interfaces import IPromptInjector
from src.domain.prompts.models import PromptConfig
from src.domain.prompts.agent_state import AgentState, HumanMessage


class TestGetAgentConfig:
    """测试get_agent_config函数"""
    
    def test_get_agent_config_returns_valid_config(self):
        """测试get_agent_config返回有效的配置"""
        config = get_agent_config()
        
        assert isinstance(config, PromptConfig)
        assert config.system_prompt == "assistant"
        assert config.rules == ["safety", "format"]
        assert config.user_command == "data_analysis"
        assert config.cache_enabled is True


class TestCreateAgentWorkflow:
    """测试create_agent_workflow函数"""
    
    def test_create_agent_workflow_without_langgraph(self):
        """测试在没有LangGraph时创建工作流抛出异常"""
        mock_injector = Mock(spec=IPromptInjector)
        
        with patch('src.prompts.langgraph_integration.LANGGRAPH_AVAILABLE', False):
            with pytest.raises(ImportError, match="LangGraph未安装，无法创建工作流"):
                create_agent_workflow(mock_injector)
    
    @patch('src.prompts.langgraph_integration.LANGGRAPH_AVAILABLE', True)
    @patch('src.prompts.langgraph_integration.StateGraph')
    def test_create_agent_workflow_with_langgraph(self, mock_state_graph):
        """测试在有LangGraph时创建工作流"""
        # 设置模拟对象
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = AgentState()
        
        mock_workflow = Mock()
        mock_state_graph.return_value = mock_workflow
        mock_workflow.compile.return_value = "compiled_workflow"
        
        # 调用函数
        result = create_agent_workflow(mock_injector)
        
        # 验证结果
        assert result == "compiled_workflow"
        
        # 验证调用
        mock_state_graph.assert_called_once_with(AgentState)
        
        # 验证add_node被调用了两次，分别用于inject_prompts和call_llm
        assert mock_workflow.add_node.call_count == 2
        node_names = [call[0][0] for call in mock_workflow.add_node.call_args_list]
        assert "inject_prompts" in node_names
        assert "call_llm" in node_names
        
        mock_workflow.set_entry_point.assert_called_once_with("inject_prompts")
        mock_workflow.add_edge.assert_called_once_with("inject_prompts", "call_llm")
        mock_workflow.compile.assert_called_once()
    
    @patch('src.prompts.langgraph_integration.LANGGRAPH_AVAILABLE', True)
    @patch('src.prompts.langgraph_integration.StateGraph', None)
    def test_create_agent_workflow_with_stategraph_none(self):
        """测试StateGraph为None时抛出异常"""
        mock_injector = Mock(spec=IPromptInjector)
        
        with pytest.raises(ImportError, match="LangGraph的StateGraph不可用"):
            create_agent_workflow(mock_injector)
    
    @patch('src.prompts.langgraph_integration.LANGGRAPH_AVAILABLE', True)
    @patch('src.prompts.langgraph_integration.StateGraph')
    def test_inject_prompts_node_function(self, mock_state_graph):
        """测试inject_prompts节点函数"""
        # 设置模拟对象
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = AgentState()
        
        mock_workflow = Mock()
        mock_state_graph.return_value = mock_workflow
        mock_workflow.compile.return_value = "compiled_workflow"
        
        # 调用函数
        create_agent_workflow(mock_injector)
        
        # 获取inject_prompts节点函数
        call_args = mock_workflow.add_node.call_args_list
        inject_prompts_call = None
        for call in call_args:
            if call[0][0] == "inject_prompts":
                inject_prompts_call = call
                break
        
        assert inject_prompts_call is not None
        inject_prompts_func = inject_prompts_call[0][1]
        
        # 测试节点函数
        test_state = AgentState()
        result_state = inject_prompts_func(test_state)
        
        # 验证调用
        mock_injector.inject_prompts.assert_called_with(test_state, get_agent_config())
    
    @patch('src.prompts.langgraph_integration.LANGGRAPH_AVAILABLE', True)
    @patch('src.prompts.langgraph_integration.StateGraph')
    def test_call_llm_node_without_llm_client(self, mock_state_graph):
        """测试没有LLM客户端时的call_llm节点函数"""
        # 设置模拟对象
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = AgentState()
        
        mock_workflow = Mock()
        mock_state_graph.return_value = mock_workflow
        mock_workflow.compile.return_value = "compiled_workflow"
        
        # 调用函数
        create_agent_workflow(mock_injector)
        
        # 获取call_llm节点函数
        call_args = mock_workflow.add_node.call_args_list
        call_llm_call = None
        for call in call_args:
            if call[0][0] == "call_llm":
                call_llm_call = call
                break
        
        assert call_llm_call is not None
        call_llm_func = call_llm_call[0][1]
        
        # 测试节点函数
        test_state = AgentState()
        result_state = call_llm_func(test_state)
        
        # 验证结果
        assert len(result_state.messages) == 1
        assert isinstance(result_state.messages[0], HumanMessage)
        assert result_state.messages[0].content == "这是一个模拟的LLM响应"
    
    @patch('src.prompts.langgraph_integration.LANGGRAPH_AVAILABLE', True)
    @patch('src.prompts.langgraph_integration.StateGraph')
    def test_call_llm_node_with_llm_client(self, mock_state_graph):
        """测试有LLM客户端时的call_llm节点函数"""
        # 设置模拟对象
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = AgentState()
        
        mock_llm_client = Mock()
        mock_response = Mock()
        mock_llm_client.generate.return_value = mock_response
        
        mock_workflow = Mock()
        mock_state_graph.return_value = mock_workflow
        mock_workflow.compile.return_value = "compiled_workflow"
        
        # 调用函数
        create_agent_workflow(mock_injector, mock_llm_client)
        
        # 获取call_llm节点函数
        call_args = mock_workflow.add_node.call_args_list
        call_llm_call = None
        for call in call_args:
            if call[0][0] == "call_llm":
                call_llm_call = call
                break
        
        assert call_llm_call is not None
        call_llm_func = call_llm_call[0][1]
        
        # 测试节点函数
        test_state = AgentState()
        test_state.messages = [HumanMessage(content="existing_message")]
        result_state = call_llm_func(test_state)
        
        # 验证调用
        mock_llm_client.generate.assert_called_once()
        
        # 验证结果
        assert len(result_state.messages) == 2
        assert result_state.messages[1] == mock_response


class TestCreateSimpleWorkflow:
    """测试create_simple_workflow函数"""
    
    def test_create_simple_workflow_returns_dict(self):
        """测试create_simple_workflow返回字典"""
        mock_injector = Mock(spec=IPromptInjector)
        
        result = create_simple_workflow(mock_injector)
        
        assert isinstance(result, dict)
        assert "run" in result
        assert "description" in result
        assert result["description"] == "简单提示词注入工作流"
        assert callable(result["run"])
    
    def test_simple_workflow_run_with_none_state(self):
        """测试简单工作流运行函数，初始状态为None"""
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = AgentState()
        
        workflow = create_simple_workflow(mock_injector)
        result = workflow["run"]()
        
        # 验证调用
        mock_injector.inject_prompts.assert_called_once()
        
        # 验证传入的状态是新的AgentState实例
        call_args = mock_injector.inject_prompts.call_args[0]
        assert isinstance(call_args[0], AgentState)
        assert isinstance(call_args[1], PromptConfig)
        
        # 验证返回值
        assert result == mock_injector.inject_prompts.return_value
    
    def test_simple_workflow_run_with_initial_state(self):
        """测试简单工作流运行函数，提供初始状态"""
        mock_injector = Mock(spec=IPromptInjector)
        mock_injector.inject_prompts.return_value = AgentState()
        
        initial_state = AgentState()
        initial_state.current_step = "test_step"
        
        workflow = create_simple_workflow(mock_injector)
        result = workflow["run"](initial_state)
        
        # 验证调用
        mock_injector.inject_prompts.assert_called_once_with(initial_state, get_agent_config())
        
        # 验证返回值
        assert result == mock_injector.inject_prompts.return_value


class TestLangGraphAvailability:
    """测试LangGraph可用性检查"""
    
    def test_langgraph_available_constant_exists(self):
        """测试LANGGRAPH_AVAILABLE常量存在"""
        assert isinstance(LANGGRAPH_AVAILABLE, bool)
