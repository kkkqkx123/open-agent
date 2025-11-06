"""迭代管理器单元测试

测试IterationManager类的功能和正确性。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.infrastructure.graph.iteration_manager import IterationManager, IterationRecord, NodeIterationStats
from src.infrastructure.graph.config import GraphConfig, NodeConfig
from src.infrastructure.graph.states.workflow import create_workflow_state, WorkflowState


class TestIterationManager:
    """IterationManager测试类"""

    def setup_method(self):
        """测试设置方法"""
        # 创建模拟的图配置
        self.mock_config = GraphConfig(
            name="test_graph",
            description="Test graph for iteration management",
            additional_config={
                "max_iterations": 5,
                "cycle_completer_node": "observe_node"
            }
        )
        
        # 添加测试节点
        self.mock_config.nodes = {
            "think_node": NodeConfig(
                name="think_node",
                function_name="think_node",
                config={"max_iterations": 3}
            ),
            "act_node": NodeConfig(
                name="act_node",
                function_name="act_node",
                config={}  # 没有节点特定的限制
            ),
            "observe_node": NodeConfig(
                name="observe_node",
                function_name="observe_node",
                config={"max_iterations": 4}
            )
        }
        
        self.iteration_manager = IterationManager(self.mock_config)

    def test_initialization(self):
        """测试IterationManager初始化"""
        assert self.iteration_manager.workflow_max_iterations == 5
        assert self.iteration_manager.node_specific_limits == {
            "think_node": 3,
            "observe_node": 4
        }
        assert self.iteration_manager.cycle_completer_node == "observe_node"

    def test_record_and_increment_global_count(self):
        """测试记录和增加全局迭代计数"""
        # 创建初始状态
        initial_state = create_workflow_state("test_id", "test_name", "test input")
        
        # 初始状态应该有0次工作流迭代
        assert initial_state.get("workflow_iteration_count", 0) == 0
        
        # 记录循环完成节点的迭代
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        
        updated_state = self.iteration_manager.record_and_increment(
            initial_state,
            "observe_node",  # 循环完成节点
            start_time,
            end_time,
            "SUCCESS",
            None
        )
        
        # 工作流迭代计数应该增加
        assert updated_state["workflow_iteration_count"] == 1

    def test_record_and_increment_node_stats(self):
        """测试记录节点统计信息"""
        # 创建初始状态
        initial_state = create_workflow_state("test_id", "test_name", "test input")
        
        # 初始状态应该没有节点迭代统计
        assert initial_state.get("node_iterations", {}) == {}
        
        # 记录节点迭代
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=2)
        
        updated_state = self.iteration_manager.record_and_increment(
            initial_state,
            "think_node",
            start_time,
            end_time,
            "SUCCESS",
            None
        )
        
        # 检查节点统计信息
        node_stats = updated_state["node_iterations"]["think_node"]
        assert node_stats["count"] == 1
        assert node_stats["total_duration"] == 2.0  # 2秒
        assert node_stats["errors"] == 0
        
        # 检查迭代历史
        assert len(updated_state["iteration_history"]) == 1
        record = updated_state["iteration_history"][0]
        assert record["node_name"] == "think_node"
        assert record["status"] == "SUCCESS"
        assert record["duration"] == 2.0

    def test_record_and_increment_with_error(self):
        """测试记录错误迭代"""
        # 创建初始状态
        initial_state = create_workflow_state("test_id", "test_name", "test input")
        
        # 记录失败的迭代
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=1)
        
        updated_state = self.iteration_manager.record_and_increment(
            initial_state,
            "act_node",
            start_time,
            end_time,
            "FAILURE",
            "Test error occurred"
        )
        
        # 检查错误统计增加
        node_stats = updated_state["node_iterations"]["act_node"]
        assert node_stats["count"] == 1
        assert node_stats["errors"] == 1
        assert node_stats["total_duration"] == 1.0
        
        # 检查错误记录在历史中
        record = updated_state["iteration_history"][0]
        assert record["status"] == "FAILURE"
        assert record["error"] == "Test error occurred"

    def test_check_limits_global_max_reached(self):
        """测试全局最大迭代次数限制"""
        # 创建一个工作流迭代计数已达到最大值的状态
        state = {
            "workflow_iteration_count": 5,  # 达到最大值
            "node_iterations": {}
        }
        
        result = self.iteration_manager.check_limits(state, "think_node")
        assert result is False  # 应该返回False

    def test_check_limits_node_specific_max_reached(self):
        """测试节点特定最大迭代次数限制"""
        # 创建一个think_node已达到节点特定最大值的状态
        state = {
            "workflow_iteration_count": 2,
            "node_iterations": {
                "think_node": {
                    "count": 3,  # 达到节点特定最大值
                    "total_duration": 0.0,
                    "errors": 0
                }
            }
        }
        
        result = self.iteration_manager.check_limits(state, "think_node")
        assert result is False  # 应该返回False

    def test_check_limits_within_limits(self):
        """测试在限制范围内的检查"""
        # 创建一个在限制范围内的状态
        state = {
            "workflow_iteration_count": 2,
            "node_iterations": {
                "think_node": {
                    "count": 1,
                    "total_duration": 0.0,
                    "errors": 0
                }
            }
        }
        
        result = self.iteration_manager.check_limits(state, "think_node")
        assert result is True  # 应该返回True

    def test_check_limits_node_without_specific_limit(self):
        """测试没有节点特定限制的节点"""
        # 创建一个act_node没有特定限制的状态
        state = {
            "workflow_iteration_count": 2,
            "node_iterations": {
                "act_node": {
                    "count": 10,  # 超过默认限制，但没有节点特定限制
                    "total_duration": 0.0,
                    "errors": 0
                }
            }
        }
        
        # 应该只检查全局限制
        result = self.iteration_manager.check_limits(state, "act_node")
        assert result is True  # 应该返回True，因为只有全局限制适用

    def test_has_reached_max_iterations(self):
        """测试has_reached_max_iterations方法"""
        # 创建一个工作流迭代计数未达到最大值的状态
        state1 = {
            "workflow_iteration_count": 2,
            "workflow_max_iterations": 5
        }
        assert self.iteration_manager.has_reached_max_iterations(state1) is False
        
        # 创建一个工作流迭代计数已达到最大值的状态
        state2 = {
            "workflow_iteration_count": 5,
            "workflow_max_iterations": 5
        }
        assert self.iteration_manager.has_reached_max_iterations(state2) is True

    def test_get_iteration_stats(self):
        """测试get_iteration_stats方法"""
        # 创建一个包含迭代数据的状态
        state = {
            "workflow_iteration_count": 3,
            "node_iterations": {
                "think_node": {
                    "count": 2,
                    "total_duration": 5.0,
                    "errors": 1
                }
            },
            "iteration_history": [
                {
                    "node_name": "think_node",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "duration": 2.0,
                    "status": "SUCCESS",
                    "error": None
                }
            ]
        }
        
        stats = self.iteration_manager.get_iteration_stats(state)
        
        assert stats['workflow_iteration_count'] == 3
        assert stats['workflow_max_iterations'] == 5  # 从配置中获取
        assert len(stats['node_iterations']) == 1
        assert len(stats['iteration_history']) == 1


if __name__ == "__main__":
    pytest.main([__file__])