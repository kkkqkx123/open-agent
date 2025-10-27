"""Agent执行节点单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime

from src.infrastructure.graph.nodes.agent_execution_node import (
    AgentExecutionNode,
    agent_execution_node
)
from src.infrastructure.graph.registry import NodeExecutionResult
from src.application.workflow.state import AgentState as WorkflowAgentState
from src.domain.agent.state import AgentState, AgentStatus, AgentMessage
from src.domain.agent import IAgentManager, IAgentEventManager, AgentEvent
from src.infrastructure.container import get_global_container


class TestAgentExecutionNode:
    """Agent执行节点测试"""

    @pytest.fixture
    def mock_agent_manager(self):
        """模拟Agent管理器"""
        return Mock(spec=IAgentManager)

    @pytest.fixture
    def mock_event_manager(self):
        """模拟事件管理器"""
        return Mock(spec=IAgentEventManager)

    @pytest.fixture
    def node(self, mock_agent_manager, mock_event_manager):
        """创建Agent执行节点实例"""
        return AgentExecutionNode(mock_agent_manager, mock_event_manager)

    @pytest.fixture
    def sample_state(self):
        """示例状态"""
        return AgentState(
            agent_id="test_agent",
            messages=[],
            context={},
            task_history=[],
            tool_results=[],
            current_step="",
            max_iterations=10,
            iteration_count=0,
            status=AgentStatus.IDLE,
            errors=[],
            logs=[],
            execution_metrics={},
            custom_fields={}
        )

    @pytest.fixture
    def sample_config(self):
        """示例配置"""
        return {
            "default_agent_id": "test_agent",
            "agent_selection_strategy": "config_based"
        }

    def test_init(self, mock_agent_manager, mock_event_manager):
        """测试初始化"""
        node = AgentExecutionNode(mock_agent_manager, mock_event_manager)
        assert node._agent_manager == mock_agent_manager
        assert node._event_manager == mock_event_manager

    def test_init_without_managers(self):
        """测试不带管理器初始化"""
        node = AgentExecutionNode()
        assert node._agent_manager is None
        assert node._event_manager is None

    def test_node_type_property(self, node):
        """测试节点类型属性"""
        assert node.node_type == "agent_execution_node"

    def test_execute_success(self, node, mock_agent_manager, mock_event_manager, sample_state, sample_config):
        """测试执行成功"""
        # 配置模拟
        updated_state = AgentState(
            agent_id="test_agent",
            messages=[],
            context={},
            task_history=[],
            tool_results=[],
            current_step="",
            max_iterations=10,
            iteration_count=1,
            status=AgentStatus.IDLE,
            errors=[],
            logs=[],
            execution_metrics={},
            custom_fields={}
        )
        mock_agent_manager.execute_agent = AsyncMock(return_value=updated_state)
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.state == updated_state
        assert result.next_node is None
        assert result.metadata is not None
        assert "agent_execution" in result.metadata
        assert result.metadata["agent_execution"] == "success"
        
        # 验证事件发布
        assert mock_event_manager.publish.call_count == 2
        mock_event_manager.publish.assert_any_call(
            AgentEvent.EXECUTION_STARTED,
            {
                "node_type": "agent_execution_node",
                "agent_id": "test_agent",
                "state": sample_state,
                "config": sample_config
            }
        )
        mock_event_manager.publish.assert_any_call(
            AgentEvent.EXECUTION_COMPLETED,
            {
                "node_type": "agent_execution_node",
                "agent_id": "test_agent",
                "input_state": sample_state,
                "output_state": updated_state,
                "next_node": None
            }
        )

    def test_execute_with_next_node(self, node, mock_agent_manager, sample_state, sample_config):
        """测试执行并指定下一个节点"""
        # 配置模拟
        updated_state = AgentState(
            agent_id="test_agent",
            messages=[],
            context={},
            task_history=[],
            tool_results=[],
            current_step="",
            max_iterations=10,
            iteration_count=10,  # 设置为最大迭代次数以触发完成
            status=AgentStatus.IDLE,
            errors=[],
            logs=[],
            execution_metrics={},
            custom_fields={}
        )
        mock_agent_manager.execute_agent = AsyncMock(return_value=updated_state)
        
        # 修改配置以指定下一个节点
        sample_config["on_task_completed"] = "next_node"
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert result.next_node == "next_node"

    def test_execute_agent_failure(self, node, mock_agent_manager, mock_event_manager, sample_state, sample_config):
        """测试Agent执行失败"""
        # 配置模拟
        mock_agent_manager.execute_agent = AsyncMock(side_effect=Exception("执行失败"))
        
        # 执行
        result = node.execute(sample_state, sample_config)
        
        # 验证
        assert isinstance(result, NodeExecutionResult)
        assert result.next_node == "error_handler"
        assert result.metadata is not None
        assert "agent_execution" in result.metadata
        assert result.metadata["agent_execution"] == "failed"
        
        # 验证错误事件发布
        mock_event_manager.publish.assert_any_call(
            AgentEvent.ERROR_OCCURRED,
            {
                "node_type": "agent_execution_node",
                "agent_id": "test_agent",
                "error": "Agent execution failed: 执行失败",
                "state": sample_state
            }
        )

    def test_get_config_schema(self, node):
        """测试获取配置模式"""
        schema = node.get_config_schema()
        
        assert isinstance(schema, dict)
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "default_agent_id" in schema["properties"]
        assert "agent_selection_strategy" in schema["properties"]
        assert "fallback_agent_id" in schema["properties"]
        assert "default_agent_id" in schema["required"]

    def test_get_agent_manager_with_instance(self, mock_agent_manager):
        """测试获取Agent管理器（使用实例）"""
        node = AgentExecutionNode(mock_agent_manager)
        result = node._get_agent_manager({})
        assert result == mock_agent_manager

    def test_get_agent_manager_from_container(self, node):
        """测试从容器获取Agent管理器"""
        # 创建一个没有预设agent_manager的节点
        node_without_manager = AgentExecutionNode()
        
        # 创建模拟容器和管理器
        mock_container = Mock()
        mock_agent_manager = Mock(spec=IAgentManager)
        mock_container.get.return_value = mock_agent_manager
        
        # 配置全局容器
        with patch('src.infrastructure.container.get_global_container', return_value=mock_container):
            result = node_without_manager._get_agent_manager({})
            
            # 验证
            assert result == mock_agent_manager
            mock_container.get.assert_called_once_with(IAgentManager)

    def test_get_agent_manager_from_container_failure(self, node):
        """测试从容器获取Agent管理器失败"""
        # 创建一个没有预设agent_manager的节点
        node_without_manager = AgentExecutionNode()
        
        # 配置全局容器抛出异常
        with patch('tests.unit.infrastructure.graph.nodes.test_agent_execution_node.get_global_container', side_effect=Exception("容器错误")):
            with pytest.raises(ValueError, match="Could not get AgentManager from container"):
                node_without_manager._get_agent_manager({})

    def test_get_event_manager_with_instance(self, mock_event_manager):
        """测试获取事件管理器（使用实例）"""
        node = AgentExecutionNode(event_manager=mock_event_manager)
        result = node._get_event_manager()
        assert result == mock_event_manager

    def test_get_event_manager_from_container(self, node):
        """测试从容器获取事件管理器"""
        # 创建一个没有预设event_manager的节点
        node_without_manager = AgentExecutionNode()
        
        # 创建模拟容器和管理器
        mock_container = Mock()
        mock_event_manager = Mock(spec=IAgentEventManager)
        mock_container.get.return_value = mock_event_manager
        
        # 配置全局容器
        with patch('src.infrastructure.container.get_global_container', return_value=mock_container):
            result = node_without_manager._get_event_manager()
            
            # 验证
            assert result == mock_event_manager
            mock_container.get.assert_called_once_with(IAgentEventManager)

    def test_get_event_manager_from_container_failure(self, node):
        """测试从容器获取事件管理器失败"""
        # 创建一个没有预设event_manager的节点
        node_without_manager = AgentExecutionNode()
        
        # 配置全局容器抛出异常
        with patch('tests.unit.infrastructure.graph.nodes.test_agent_execution_node.get_global_container', side_effect=Exception("容器错误")):
            result = node_without_manager._get_event_manager()
            assert result is None

    def test_determine_next_node_task_completed(self, node, sample_state, sample_config):
        """测试确定下一个节点（任务完成）"""
        # 修改状态以表示任务完成
        sample_state.iteration_count = 10
        sample_state.max_iterations = 10
        
        # 配置配置指定完成时的下一个节点
        sample_config["on_task_completed"] = "completion_node"
        
        result = node._determine_next_node(sample_state, sample_config)
        assert result == "completion_node"

    def test_determine_next_node_needs_agent_switch(self, node, sample_state, sample_config):
        """测试确定下一个节点（需要切换Agent）"""
        # 修改配置以需要切换Agent
        sample_config["agent_selection_strategy"] = "context_based"
        
        # 模拟需要切换Agent
        with patch.object(node, '_needs_agent_switch', return_value=True):
            result = node._determine_next_node(sample_state, sample_config)
            assert result == "agent_selection_node"

    def test_determine_next_node_default(self, node, sample_state, sample_config):
        """测试确定下一个节点（默认）"""
        # 配置默认下一个节点
        sample_config["default_next_node"] = "default_node"
        
        # 确保不会被认为是任务完成或需要切换Agent
        sample_state.iteration_count = 5
        sample_state.max_iterations = 10
        sample_config["agent_selection_strategy"] = "config_based"
        
        with patch.object(node, '_needs_agent_switch', return_value=False):
            result = node._determine_next_node(sample_state, sample_config)
            assert result == "default_node"

    def test_is_task_completed_max_iterations(self, node):
        """测试任务完成检查（达到最大迭代次数）"""
        state = Mock()
        state.iteration_count = 10
        state.max_iterations = 10
        
        result = node._is_task_completed(state)
        assert result is True

    def test_is_task_completed_message_content(self, node):
        """测试任务完成检查（消息内容）"""
        message = AgentMessage(
            content="任务已完成 task_completed",
            role="assistant"
        )
        state = AgentState(
            agent_id="test_agent",
            messages=[message],
            context={},
            task_history=[],
            tool_results=[],
            current_step="",
            max_iterations=10,
            iteration_count=5,
            status=AgentStatus.IDLE,
            errors=[],
            logs=[],
            execution_metrics={},
            custom_fields={}
        )
        
        result = node._is_task_completed(state)
        assert result is True

    def test_is_task_completed_not_completed(self, node):
        """测试任务完成检查（未完成）"""
        message = AgentMessage(
            content="进行中",
            role="assistant"
        )
        state = AgentState(
            agent_id="test_agent",
            messages=[message],
            context={},
            task_history=[],
            tool_results=[],
            current_step="",
            max_iterations=10,
            iteration_count=5,
            status=AgentStatus.IDLE,
            errors=[],
            logs=[],
            execution_metrics={},
            custom_fields={}
        )
        
        result = node._is_task_completed(state)
        assert result is False

    def test_needs_agent_switch_context_based(self, node, sample_state, sample_config):
        """测试是否需要切换Agent（基于上下文）"""
        sample_config["agent_selection_strategy"] = "context_based"
        
        result = node._needs_agent_switch(sample_state, sample_config)
        assert result is False  # 默认实现返回False

    def test_needs_agent_switch_rule_based(self, node, sample_state, sample_config):
        """测试是否需要切换Agent（基于规则）"""
        sample_config["agent_selection_strategy"] = "rule_based"
        
        result = node._needs_agent_switch(sample_state, sample_config)
        assert result is False  # 默认实现返回False

    def test_needs_agent_switch_config_based(self, node, sample_state, sample_config):
        """测试是否需要切换Agent（基于配置）"""
        sample_config["agent_selection_strategy"] = "config_based"
        
        result = node._needs_agent_switch(sample_state, sample_config)
        assert result is False  # 默认实现返回False


class TestAgentExecutionNodeFunction:
    """Agent执行节点函数测试"""

    def test_agent_execution_node_function(self):
        """测试Agent执行节点函数"""
        # 创建模拟状态
        state = AgentState(
            agent_id="test_agent",
            messages=[],
            context={},
            task_history=[],
            tool_results=[],
            current_step="",
            max_iterations=10,
            iteration_count=0,
            status=AgentStatus.IDLE,
            errors=[],
            logs=[],
            execution_metrics={},
            custom_fields={}
        )

        # 创建一个带有模拟AgentManager的节点
        mock_agent_manager = Mock(spec=IAgentManager)
        # 使用普通的Mock而不是AsyncMock，因为execute方法内部会处理异步调用
        mock_agent_manager.execute_agent = Mock(return_value=state)
        
        # 创建节点实例并直接传入模拟的AgentManager
        from src.infrastructure.graph.nodes.agent_execution_node import AgentExecutionNode
        node = AgentExecutionNode(agent_manager=mock_agent_manager)
        
        # 直接调用execute方法而不是使用函数包装器
        result = node.execute(state, {})

        # 验证结果
        assert isinstance(result, NodeExecutionResult)
        assert isinstance(result.state, AgentState)