"""状态机工作流测试

测试基于状态机的工作流基类的功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../src'))

from application.workflow.state_machine.state_machine_workflow import (
    StateMachineWorkflow, StateMachineConfig, StateDefinition, Transition, StateType, TransitionRecord
)
from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.states import WorkflowState


class TestStateType:
    """测试状态类型枚举"""

    def test_state_type_values(self):
        """测试状态类型枚举值"""
        assert StateType.START.value == "start"
        assert StateType.END.value == "end"
        assert StateType.PROCESS.value == "process"
        assert StateType.DECISION.value == "decision"
        assert StateType.PARALLEL.value == "parallel"
        assert StateType.CONDITIONAL.value == "conditional"


class TestTransition:
    """测试状态转移定义"""

    def test_transition_init(self):
        """测试转移初始化"""
        transition = Transition("target_state")
        assert transition.target_state == "target_state"
        assert transition.condition is None
        assert transition.description == ""

    def test_transition_with_condition(self):
        """测试带条件的转移"""
        transition = Transition("target_state", "has_data", "条件转移")
        assert transition.target_state == "target_state"
        assert transition.condition == "has_data"
        assert transition.description == "条件转移"


class TestTransitionRecord:
    """测试状态转移记录"""

    def test_transition_record_init(self):
        """测试转移记录初始化"""
        record = TransitionRecord("state_a", "state_b", "2023-01-01T00:00:00")
        assert record.from_state == "state_a"
        assert record.to_state == "state_b"
        assert record.timestamp == "2023-01-01T00:00:00"
        assert record.condition is None

    def test_transition_record_with_condition(self):
        """测试带条件的转移记录"""
        record = TransitionRecord("state_a", "state_b", "2023-01-01T00:00:00", "has_data")
        assert record.condition == "has_data"


class TestStateDefinition:
    """测试状态定义"""

    def test_state_definition_init(self):
        """测试状态定义初始化"""
        state_def = StateDefinition("test_state", StateType.PROCESS, "handle_test", "测试状态", {"param": "value"})
        assert state_def.name == "test_state"
        assert state_def.state_type == StateType.PROCESS
        assert state_def.handler == "handle_test"
        assert state_def.description == "测试状态"
        assert state_def.config == {"param": "value"}
        assert state_def.transitions == []

    def test_add_transition(self):
        """测试添加转移"""
        state_def = StateDefinition("test_state", StateType.PROCESS)
        transition = Transition("next_state")
        state_def.add_transition(transition)
        assert len(state_def.transitions) == 1
        assert state_def.transitions[0] == transition


class TestStateMachineConfig:
    """测试状态机配置"""

    def test_config_init(self):
        """测试配置初始化"""
        config = StateMachineConfig("test_workflow", "测试工作流", "1.0.0", "start")
        assert config.name == "test_workflow"
        assert config.description == "测试工作流"
        assert config.version == "1.0.0"
        assert config.initial_state == "start"
        assert config.states == {}

    def test_add_state(self):
        """测试添加状态"""
        config = StateMachineConfig("test_workflow")
        state = StateDefinition("test_state", StateType.PROCESS)
        config.add_state(state)
        assert len(config.states) == 1
        assert config.states["test_state"] == state

    def test_get_state(self):
        """测试获取状态"""
        config = StateMachineConfig("test_workflow")
        state = StateDefinition("test_state", StateType.PROCESS)
        config.add_state(state)
        retrieved_state = config.get_state("test_state")
        assert retrieved_state == state
        assert config.get_state("nonexistent") is None

    def test_validate_success(self):
        """测试配置验证成功"""
        config = StateMachineConfig("test_workflow", initial_state="start")
        
        # 添加状态
        start_state = StateDefinition("start", StateType.START)
        process_state = StateDefinition("process", StateType.PROCESS)
        end_state = StateDefinition("end", StateType.END)
        
        config.add_state(start_state)
        config.add_state(process_state)
        config.add_state(end_state)
        
        # 添加转移
        start_state.add_transition(Transition("process"))
        process_state.add_transition(Transition("end"))
        
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_missing_initial_state(self):
        """测试缺少初始状态的验证"""
        config = StateMachineConfig("test_workflow", initial_state="missing")
        state = StateDefinition("start", StateType.START)
        config.add_state(state)
        
        errors = config.validate()
        # 应该有两个错误：初始状态不存在和存在不可达状态
        assert len(errors) == 2
        assert "初始状态 'missing' 不存在" in errors[0]
        assert "存在不可达状态: start" in errors[1]

    def test_validate_multiple_start_states(self):
        """测试多个开始状态的验证"""
        config = StateMachineConfig("test_workflow", initial_state="start")
        
        start_state1 = StateDefinition("start", StateType.START)
        start_state2 = StateDefinition("start2", StateType.START)
        config.add_state(start_state1)
        config.add_state(start_state2)
        
        errors = config.validate()
        # 应该有两个错误：多个开始状态和存在不可达状态
        assert len(errors) == 2
        assert "状态机必须包含且仅包含一个开始状态" in errors[0]
        assert "存在不可达状态: start2" in errors[1]

    def test_validate_invalid_transition_target(self):
        """测试无效转移目标的验证"""
        config = StateMachineConfig("test_workflow", initial_state="start")
        
        start_state = StateDefinition("start", StateType.START)
        config.add_state(start_state)
        start_state.add_transition(Transition("invalid_target"))
        
        errors = config.validate()
        assert len(errors) == 1
        assert "状态 'start' 的转移目标 'invalid_target' 不存在" in errors[0]

    def test_validate_unreachable_states(self):
        """测试不可达状态的验证"""
        config = StateMachineConfig("test_workflow", initial_state="start")
        
        start_state = StateDefinition("start", StateType.START)
        unreachable_state = StateDefinition("unreachable", StateType.PROCESS)
        
        config.add_state(start_state)
        config.add_state(unreachable_state)
        start_state.add_transition(Transition("start"))  # 自循环，不连接到unreachable
        
        errors = config.validate()
        assert len(errors) == 1
        assert "存在不可达状态: unreachable" in errors[0]


class TestStateMachineWorkflow:
    """测试状态机工作流"""

    @pytest.fixture
    def basic_config(self):
        """基本工作流配置fixture"""
        return WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            nodes={},
            edges=[],
            entry_point="start"
        )

    @pytest.fixture
    def basic_state_machine_config(self):
        """基本状态机配置fixture"""
        config = StateMachineConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            initial_state="start"
        )
        
        # 添加状态
        start_state = StateDefinition("start", StateType.START)
        process_state = StateDefinition("process", StateType.PROCESS)
        end_state = StateDefinition("end", StateType.END)
        
        config.add_state(start_state)
        config.add_state(process_state)
        config.add_state(end_state)
        
        # 添加转移
        start_state.add_transition(Transition("process"))
        process_state.add_transition(Transition("end"))
        
        return config

    def test_workflow_init(self, basic_config, basic_state_machine_config):
        """测试工作流初始化"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        assert workflow.config == basic_config
        assert workflow.state_machine_config == basic_state_machine_config
        assert workflow.current_state == "start"
        assert workflow.state_history == []
        assert workflow.transition_history == []

    def test_default_state_handler(self, basic_config, basic_state_machine_config):
        """测试默认状态处理器"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        state_def = StateDefinition("test_state", StateType.PROCESS)
        
        initial_state = {}
        result_state = workflow._default_state_handler(initial_state, state_def)
        
        assert result_state["current_state"] == "test_state"
        assert "execution_info" in result_state
        assert "test_state" in result_state["execution_info"]

    def test_evaluate_transition_condition_always(self):
        """测试总是为真的转移条件"""
        # 创建实际的工作流实例来测试静态方法
        config = StateMachineConfig("test_workflow")
        workflow_config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            nodes={},
            edges=[],
            entry_point="start"
        )
        workflow = StateMachineWorkflow(workflow_config, config)
        
        transition = Transition("target", "always")
        state = {}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is True

    def test_evaluate_transition_condition_never(self):
        """测试总是为假的转移条件"""
        # 创建实际的工作流实例来测试静态方法
        config = StateMachineConfig("test_workflow")
        workflow_config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            nodes={},
            edges=[],
            entry_point="start"
        )
        workflow = StateMachineWorkflow(workflow_config, config)
        
        transition = Transition("target", "never")
        state = {}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is False

    def test_evaluate_transition_condition_has_field(self):
        """测试存在字段的转移条件"""
        # 创建实际的工作流实例来测试静态方法
        config = StateMachineConfig("test_workflow")
        workflow_config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            nodes={},
            edges=[],
            entry_point="start"
        )
        workflow = StateMachineWorkflow(workflow_config, config)
        
        transition = Transition("target", "has_data")
        state = {"data": "value"}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is True
        
        state = {}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is False

    def test_evaluate_transition_condition_not_has_field(self):
        """测试不存在字段的转移条件"""
        # 创建实际的工作流实例来测试静态方法
        config = StateMachineConfig("test_workflow")
        workflow_config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0.0",
            nodes={},
            edges=[],
            entry_point="start"
        )
        workflow = StateMachineWorkflow(workflow_config, config)
        
        transition = Transition("target", "not_has_data")
        state = {}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is True
        
        state = {"data": "value"}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is False
        
        # 测试字段存在但为空的情况
        state = {"data": ""}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is True
        
        # 测试字段存在但为None的情况
        state = {"data": None}
        result = workflow._evaluate_transition_condition(transition, state)
        assert result is True

    def test_determine_next_state_single_unconditional(self, basic_config, basic_state_machine_config):
        """测试确定下一个状态 - 单一无条件转移"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        state_def = StateDefinition("test_state", StateType.PROCESS)
        state_def.add_transition(Transition("next_state"))
        
        state = {}
        next_state = workflow._determine_next_state(state_def, state)
        assert next_state == "next_state"

    def test_determine_next_state_conditional_true(self, basic_config, basic_state_machine_config):
        """测试确定下一个状态 - 条件为真"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        state_def = StateDefinition("test_state", StateType.PROCESS)
        state_def.add_transition(Transition("conditional_state", "has_data"))
        state_def.add_transition(Transition("fallback_state"))
        
        state = {"data": "value"}
        next_state = workflow._determine_next_state(state_def, state)
        assert next_state == "conditional_state"

    def test_determine_next_state_conditional_false(self, basic_config, basic_state_machine_config):
        """测试确定下一个状态 - 条件为假"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        state_def = StateDefinition("test_state", StateType.PROCESS)
        state_def.add_transition(Transition("conditional_state", "has_data"))
        state_def.add_transition(Transition("fallback_state"))
        
        state = {}
        next_state = workflow._determine_next_state(state_def, state)
        assert next_state == "fallback_state"

    def test_validate_config(self, basic_config, basic_state_machine_config):
        """测试配置验证"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        errors = workflow.validate_config()
        assert len(errors) == 0

    def test_reset(self, basic_config, basic_state_machine_config):
        """测试重置功能"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        workflow.current_state = "end"
        workflow.reset()
        assert workflow.current_state == "start"

    def test_get_current_state_info(self, basic_config, basic_state_machine_config):
        """测试获取当前状态信息"""
        workflow = StateMachineWorkflow(basic_config, basic_state_machine_config)
        state_info = workflow.get_current_state_info()
        
        assert state_info is not None
        assert state_info["name"] == "start"
        assert state_info["type"] == "start"
        assert len(state_info["transitions"]) == 1
        assert state_info["transitions"][0]["target"] == "process"