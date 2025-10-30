"""等待节点测试

测试等待节点的各种功能，包括超时机制和不同的处理策略。
"""

import time
import pytest
from unittest.mock import Mock, patch

from src.infrastructure.graph.nodes.wait_node import WaitNode, TimeoutStrategy, WaitState
from src.infrastructure.graph.registry import NodeExecutionResult
from src.domain.agent.state import AgentState, AgentMessage


class TestWaitNode:
    """等待节点测试类"""

    def setup_method(self) -> None:
        """测试前设置"""
        self.wait_node = WaitNode()
        self.state = AgentState()
        self.state.agent_id = "test_agent"
        self.state.messages = []

    def test_node_type(self) -> None:
        """测试节点类型"""
        assert self.wait_node.node_type == "wait_node"

    def test_basic_wait_execution(self) -> None:
        """测试基本等待执行"""
        config = {
            "timeout_enabled": False,  # 禁用超时以便测试
            "wait_message": "测试等待消息"
        }
        
        result = self.wait_node.execute(self.state, config)
        
        # 验证返回结果
        assert isinstance(result, NodeExecutionResult)
        assert result.next_node == "__wait__"
        assert result.metadata is not None
        assert result.metadata["is_waiting"] is True
        assert result.metadata["wait_message"] == "测试等待消息"
        
        # 验证状态更新
        assert self.state.is_waiting is True
        assert hasattr(self.state, 'wait_start_time')
        assert len(self.state.messages) == 1
        assert "测试等待消息" in self.state.messages[0].content

    def test_timeout_enabled_continue_waiting(self) -> None:
        """测试启用超时 - 继续等待策略"""
        config = {
            "timeout_enabled": True,
            "timeout_seconds": 1,  # 1秒超时
            "timeout_strategy": "continue_waiting",
            "wait_message": "等待测试"
        }
        
        # 第一次执行 - 开始等待
        result1 = self.wait_node.execute(self.state, config)
        assert result1.next_node == "__wait__"
        assert result1.metadata is not None
        wait_id = result1.metadata["wait_id"]
        
        # 等待超时
        time.sleep(1.5)
        
        # 第二次执行 - 处理超时
        result2 = self.wait_node.execute(self.state, config)
        assert result2.next_node == "__wait__"  # 继续等待
        assert result2.metadata is not None
        assert result2.metadata["timeout_handled"] is True
        assert result2.metadata["strategy"] == "continue_waiting"
        
        # 验证超时消息
        timeout_messages = [msg for msg in self.state.messages if "超时" in msg.content]
        assert len(timeout_messages) > 0

    def test_timeout_enabled_cache_and_exit(self) -> None:
        """测试启用超时 - 缓存并退出策略"""
        config = {
            "timeout_enabled": True,
            "timeout_seconds": 1,
            "timeout_strategy": "cache_and_exit",
            "wait_message": "等待测试"
        }
        
        # 第一次执行
        result1 = self.wait_node.execute(self.state, config)
        assert result1.metadata is not None
        wait_id = result1.metadata["wait_id"]
        
        # 等待超时
        time.sleep(1.5)
        
        # 第二次执行 - 处理超时
        result2 = self.wait_node.execute(self.state, config)
        assert result2.next_node == "__exit__"  # 退出
        assert result2.metadata is not None
        assert result2.metadata["timeout_handled"] is True
        assert result2.metadata["strategy"] == "cache_and_exit"
        assert result2.metadata["cached"] is True
        
        # 验证状态缓存
        cached_state = self.wait_node.get_cached_state(wait_id)
        assert cached_state is not None
        assert cached_state["agent_id"] == "test_agent"

    def test_timeout_enabled_llm_continue(self) -> None:
        """测试启用超时 - LLM继续策略"""
        config = {
            "timeout_enabled": True,
            "timeout_seconds": 1,
            "timeout_strategy": "llm_continue",
            "wait_message": "等待测试",
            "continue_node": "analyze"
        }
        
        # 第一次执行
        result1 = self.wait_node.execute(self.state, config)
        assert result1.metadata is not None
        wait_id = result1.metadata["wait_id"]
        
        # 等待超时
        time.sleep(1.5)
        
        # 第二次执行 - 处理超时
        result2 = self.wait_node.execute(self.state, config)
        assert result2.next_node == "analyze"  # 继续到指定节点
        assert result2.metadata is not None
        assert result2.metadata["timeout_handled"] is True
        assert result2.metadata["strategy"] == "llm_continue"
        assert result2.metadata["auto_continue"] is True
        
        # 验证状态更新
        assert self.state.is_waiting is False
        assert self.state.auto_continue is True
        assert self.state.continue_reason == "timeout"

    def test_external_input_resume(self) -> None:
        """测试外部输入恢复"""
        config = {
            "timeout_enabled": False,
            "auto_resume_key": "human_review_result",
            "routing_rules": {
                "approved": "final_answer",
                "rejected": "analyze"
            },
            "default_next_node": "final_answer"
        }
        
        # 设置外部输入 - 使用custom_fields来存储动态属性
        self.state.custom_fields["human_review_result"] = "approved"
        
        result = self.wait_node.execute(self.state, config)
        
        # 验证恢复执行
        assert result.next_node == "final_answer"
        assert result.metadata is not None
        assert result.metadata["is_waiting"] is False
        assert result.metadata["resumed_by"] == "human_review_result"
        assert result.metadata["resume_value"] == "approved"
        
        # 验证恢复消息
        resume_messages = [msg for msg in self.state.messages if "恢复执行" in msg.content]
        assert len(resume_messages) > 0

    def test_routing_rules(self) -> None:
        """测试路由规则"""
        config = {
            "timeout_enabled": False,
            "auto_resume_key": "human_review_result",
            "routing_rules": {
                "approved": "final_answer",
                "rejected": "analyze",
                "modify": "modify_result"
            }
        }
        
        # 测试不同的路由
        test_cases = [
            ("approved", "final_answer"),
            ("rejected", "analyze"),
            ("modify", "modify_result"),
            ("unknown", "final_answer")  # 默认路由
        ]
        
        for input_value, expected_next in test_cases:
            # 重置状态
            self.state.messages = []
            self.state.custom_fields["human_review_result"] = input_value
            
            result = self.wait_node.execute(self.state, config)
            assert result.next_node == expected_next

    def test_default_routing_logic(self) -> None:
        """测试默认路由逻辑"""
        config = {
            "timeout_enabled": False,
            "auto_resume_key": "human_review_result",
            "default_next_node": "default_node"
        }
        
        # 测试默认的人工审核结果路由
        test_cases = [
            ("approved", "final_answer"),
            ("rejected", "analyze"),
            ("modify", "modify_result"),
            ("other", "default_node")
        ]
        
        for input_value, expected_next in test_cases:
            self.state.messages = []
            self.state.custom_fields["human_review_result"] = input_value
            
            result = self.wait_node.execute(self.state, config)
            assert result.next_node == expected_next

    def test_config_schema(self) -> None:
        """测试配置Schema"""
        schema = self.wait_node.get_config_schema()
        
        # 验证Schema结构
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        
        # 验证必需字段
        properties = schema["properties"]
        assert "timeout_enabled" in properties
        assert "timeout_seconds" in properties
        assert "timeout_strategy" in properties
        assert "wait_message" in properties
        assert "auto_resume_key" in properties
        assert "routing_rules" in properties
        
        # 验证超时策略枚举
        strategy_enum = properties["timeout_strategy"]["enum"]
        assert "continue_waiting" in strategy_enum
        assert "cache_and_exit" in strategy_enum
        assert "llm_continue" in strategy_enum

    def test_validate_config_valid(self) -> None:
        """测试有效配置验证"""
        valid_config = {
            "timeout_enabled": True,
            "timeout_seconds": 300,
            "timeout_strategy": "continue_waiting",
            "wait_message": "测试消息",
            "routing_rules": {"approved": "final"}
        }
        
        errors = self.wait_node.validate_config(valid_config)
        assert len(errors) == 0

    def test_validate_config_invalid_strategy(self) -> None:
        """测试无效策略配置验证"""
        invalid_config = {
            "timeout_strategy": "invalid_strategy"
        }
        
        errors = self.wait_node.validate_config(invalid_config)
        assert len(errors) > 0
        assert any("无效的超时策略" in error for error in errors)

    def test_validate_config_invalid_timeout(self) -> None:
        """测试无效超时时间配置验证"""
        invalid_config = {
            "timeout_seconds": -1
        }
        
        errors = self.wait_node.validate_config(invalid_config)
        assert len(errors) > 0
        assert any("timeout_seconds 必须是正整数" in error for error in errors)

    def test_validate_config_invalid_routing_rules(self) -> None:
        """测试无效路由规则配置验证"""
        invalid_config = {
            "routing_rules": "not_a_dict"
        }
        
        errors = self.wait_node.validate_config(invalid_config)
        assert len(errors) > 0
        assert any("routing_rules 必须是对象类型" in error for error in errors)

    def test_wait_state_management(self) -> None:
        """测试等待状态管理"""
        config = {"timeout_enabled": False}
        
        # 执行等待
        result = self.wait_node.execute(self.state, config)
        assert result.metadata is not None
        wait_id = result.metadata["wait_id"]
        
        # 测试活跃等待列表
        active_waits = self.wait_node.list_active_waits()
        assert wait_id in active_waits
        
        # 测试清除等待状态
        cleared = self.wait_node.clear_wait_state(wait_id)
        assert cleared is True
        
        # 验证已清除
        active_waits_after = self.wait_node.list_active_waits()
        assert wait_id not in active_waits_after

    def test_multiple_wait_sessions(self) -> None:
        """测试多个等待会话"""
        config1 = {"timeout_enabled": False, "wait_message": "等待1"}
        config2 = {"timeout_enabled": False, "wait_message": "等待2"}
        
        # 创建第一个等待会话
        state1 = AgentState()
        state1.agent_id = "agent1"
        result1 = self.wait_node.execute(state1, config1)
        assert result1.metadata is not None
        wait_id1 = result1.metadata["wait_id"]
        
        # 创建第二个等待会话
        state2 = AgentState()
        state2.agent_id = "agent2"
        result2 = self.wait_node.execute(state2, config2)
        assert result2.metadata is not None
        wait_id2 = result2.metadata["wait_id"]
        
        # 验证两个会话都存在
        active_waits = self.wait_node.list_active_waits()
        assert len(active_waits) >= 2
        assert wait_id1 in active_waits
        assert wait_id2 in active_waits
        
        # 验证会话独立性
        assert wait_id1 != wait_id2

    @patch('threading.Thread')
    def test_timeout_handler_setup(self, mock_thread: Mock) -> None:
        """测试超时处理器设置"""
        config = {
            "timeout_enabled": True,
            "timeout_seconds": 60,
            "timeout_strategy": "continue_waiting"
        }
        
        self.wait_node.execute(self.state, config)
        
        # 验证线程被创建
        mock_thread.assert_called_once()
        args, kwargs = mock_thread.call_args
        assert kwargs.get('daemon') is True

    def test_existing_wait_state_handling(self) -> None:
        """测试现有等待状态处理"""
        config = {
            "timeout_enabled": False,
            "auto_resume_key": "test_key"
        }
        
        # 第一次执行 - 创建等待状态
        result1 = self.wait_node.execute(self.state, config)
        assert result1.next_node == "__wait__"
        
        # 第二次执行 - 处理现有等待状态
        result2 = self.wait_node.execute(self.state, config)
        assert result2.next_node == "__wait__"
        assert result2.metadata is not None
        assert "wait_elapsed" in result2.metadata

    def test_wait_state_data_structure(self) -> None:
        """测试等待状态数据结构"""
        wait_state = WaitState(start_time=time.time())
        
        assert wait_state.is_waiting is True
        assert wait_state.timeout_occurred is False
        assert wait_state.wait_message == ""
        assert wait_state.cached_state is None
        
        # 测试状态更新
        wait_state.timeout_occurred = True
        wait_state.wait_message = "测试消息"
        assert wait_state.timeout_occurred is True
        assert wait_state.wait_message == "测试消息"

    def test_timeout_strategy_enum(self) -> None:
        """测试超时策略枚举"""
        assert TimeoutStrategy.CONTINUE_WAITING.value == "continue_waiting"
        assert TimeoutStrategy.CACHE_AND_EXIT.value == "cache_and_exit"
        assert TimeoutStrategy.LLM_CONTINUE.value == "llm_continue"
        
        # 测试枚举创建
        strategy = TimeoutStrategy("continue_waiting")
        assert strategy == TimeoutStrategy.CONTINUE_WAITING