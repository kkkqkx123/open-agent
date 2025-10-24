"""TUI子界面测试"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.presentation.tui.subviews.base import BaseSubview
from src.presentation.tui.subviews.analytics import AnalyticsSubview
from src.presentation.tui.subviews.visualization import VisualizationSubview
from src.presentation.tui.subviews.system import SystemSubview
from src.presentation.tui.subviews.errors import ErrorsSubview
from src.presentation.tui.config import TUIConfig, SubviewConfig, ShortcutConfig


class TestBaseSubview:
    """基础子界面测试"""
    
    def test_subview_initialization(self):
        """测试子界面初始化"""
        config = Mock(spec=TUIConfig)
        subview = BaseSubview(config)
        
        assert subview.config == config
        assert subview.data == {}
        assert subview.callbacks == {}
    
    def test_subview_data_management(self):
        """测试子界面数据管理"""
        config = Mock(spec=TUIConfig)
        subview = BaseSubview(config)
        
        # 测试数据更新
        test_data = {"key": "value"}
        subview.update_data(test_data)
        assert subview.data == test_data
        
        # 测试数据追加
        additional_data = {"another_key": "another_value"}
        subview.update_data(additional_data)
        assert subview.data == {**test_data, **additional_data}
    
    def test_subview_callback_management(self):
        """测试子界面回调管理"""
        config = Mock(spec=TUIConfig)
        subview = BaseSubview(config)
        
        # 测试回调设置
        callback = Mock()
        subview.set_callback("test_event", callback)
        assert subview.callbacks["test_event"] == callback
        
        # 测试回调触发
        subview.trigger_callback("test_event", "arg1", kwarg1="value1")
        callback.assert_called_once_with("arg1", kwarg1="value1")
        
        # 测试不存在的回调
        result = subview.trigger_callback("nonexistent_event")
        assert result is None
    
    def test_subview_escape_key_handling(self):
        """测试ESC键处理"""
        config = Mock(spec=TUIConfig)
        subview = BaseSubview(config)
        
        # ESC键应该被处理
        assert subview.handle_key("escape") is True
        
        # 其他键应该传递到上层
        assert subview.handle_key("other_key") is False


class TestAnalyticsSubview:
    """分析监控子界面测试"""
    
    def test_analytics_subview_initialization(self):
        """测试分析监控子界面初始化"""
        config = Mock(spec=TUIConfig)
        subview = AnalyticsSubview(config)
        
        assert subview.get_title() == "📊 分析监控"
        assert subview.performance_data["total_requests"] == 0
        assert subview.system_metrics["cpu_usage"] == 0.0
        assert len(subview.execution_history) == 0
    
    def test_performance_data_update(self):
        """测试性能数据更新"""
        config = Mock(spec=TUIConfig)
        subview = AnalyticsSubview(config)
        
        test_data = {
            "total_requests": 100,
            "avg_response_time": 250.5,
            "success_rate": 95.0
        }
        
        subview.update_performance_data(test_data)
        assert subview.performance_data["total_requests"] == 100
        assert subview.performance_data["avg_response_time"] == 250.5
        assert subview.performance_data["success_rate"] == 95.0
    
    def test_system_metrics_update(self):
        """测试系统指标更新"""
        config = Mock(spec=TUIConfig)
        subview = AnalyticsSubview(config)
        
        test_metrics = {
            "cpu_usage": 75.5,
            "memory_usage": 60.2,
            "disk_usage": 45.0
        }
        
        subview.update_system_metrics(test_metrics)
        assert subview.system_metrics["cpu_usage"] == 75.5
        assert subview.system_metrics["memory_usage"] == 60.2
        assert subview.system_metrics["disk_usage"] == 45.0
    
    def test_execution_record_addition(self):
        """测试执行记录添加"""
        config = Mock(spec=TUIConfig)
        subview = AnalyticsSubview(config)
        
        test_record = {
            "action": "test_action",
            "status": "completed",
            "duration": 1.5
        }
        
        subview.add_execution_record(test_record)
        assert len(subview.execution_history) == 1
        assert subview.execution_history[0]["action"] == "test_action"
        assert "timestamp" in subview.execution_history[0]
    
    def test_execution_history_limit(self):
        """测试执行历史限制"""
        config = Mock(spec=TUIConfig)
        subview = AnalyticsSubview(config)
        
        # 添加超过限制的记录
        for i in range(150):
            subview.add_execution_record({"action": f"action_{i}"})
        
        # 应该只保留最近的100条记录
        assert len(subview.execution_history) == 100
        assert subview.execution_history[-1]["action"] == "action_149"


class TestVisualizationSubview:
    """可视化调试子界面测试"""
    
    def test_visualization_subview_initialization(self):
        """测试可视化调试子界面初始化"""
        config = Mock(spec=TUIConfig)
        subview = VisualizationSubview(config)
        
        assert subview.get_title() == "🎨 可视化调试"
        assert subview.workflow_data["nodes"] == []
        assert subview.workflow_data["current_node"] is None
        assert subview.node_debug_data["selected_node"] is None
    
    def test_workflow_data_update(self):
        """测试工作流数据更新"""
        config = Mock(spec=TUIConfig)
        subview = VisualizationSubview(config)
        
        test_data = {
            "nodes": [
                {"id": "node1", "type": "process", "description": "Test node"},
                {"id": "node2", "type": "decision", "description": "Another node"}
            ],
            "current_node": "node1"
        }
        
        subview.update_workflow_data(test_data)
        assert len(subview.workflow_data["nodes"]) == 2
        assert subview.workflow_data["current_node"] == "node1"
    
    def test_node_selection(self):
        """测试节点选择"""
        config = Mock(spec=TUIConfig)
        subview = VisualizationSubview(config)
        
        # 设置工作流数据
        subview.workflow_data["nodes"] = [
            {"id": "node1", "type": "process", "description": "Test node"}
        ]
        
        # 选择节点
        subview.select_node("node1")
        assert subview.node_debug_data["selected_node"] == "node1"
        assert "type" in subview.node_debug_data["node_metadata"]
    
    def test_visualization_settings(self):
        """测试可视化设置"""
        config = Mock(spec=TUIConfig)
        subview = VisualizationSubview(config)
        
        # 默认设置
        assert subview.visualization_settings["show_details"] is True
        assert subview.visualization_settings["auto_refresh"] is True
        
        # 测试按键处理
        assert subview.handle_key("d") is True  # 切换详细信息
        assert subview.visualization_settings["show_details"] is False


class TestSystemSubview:
    """系统管理子界面测试"""
    
    def test_system_subview_initialization(self):
        """测试系统管理子界面初始化"""
        config = Mock(spec=TUIConfig)
        subview = SystemSubview(config)
        
        assert subview.get_title() == "⚙️ 系统管理"
        assert subview.studio_status["running"] is False
        assert subview.studio_status["port"] == 8079
        assert subview.port_config["studio_port"] == 8079
    
    def test_studio_status_update(self):
        """测试Studio状态更新"""
        config = Mock(spec=TUIConfig)
        subview = SystemSubview(config)
        
        test_status = {
            "running": True,
            "port": 8080,
            "url": "http://localhost:8080",
            "connected_clients": 3
        }
        
        subview.update_studio_status(test_status)
        assert subview.studio_status["running"] is True
        assert subview.studio_status["port"] == 8080
        assert subview.studio_status["url"] == "http://localhost:8080"
        assert subview.studio_status["connected_clients"] == 3
    
    def test_studio_control(self):
        """测试Studio控制"""
        config = Mock(spec=TUIConfig)
        subview = SystemSubview(config)
        
        # 测试启动Studio
        result = subview.start_studio()
        assert result is True
        assert subview.studio_status["running"] is True
        assert subview.studio_status["url"] == "http://localhost:8079"
        
        # 测试停止Studio
        result = subview.stop_studio()
        assert result is True
        assert subview.studio_status["running"] is False
        assert subview.studio_status["url"] == ""
    
    def test_config_reload(self):
        """测试配置重载"""
        config = Mock(spec=TUIConfig)
        subview = SystemSubview(config)
        
        result = subview.reload_config()
        assert result is True
        assert subview.config_management["last_reload"] is not None
    
    def test_auto_reload_toggle(self):
        """测试自动重载切换"""
        config = Mock(spec=TUIConfig)
        subview = SystemSubview(config)
        
        # 默认状态
        assert subview.config_management["auto_reload"] is False
        
        # 切换状态
        subview.toggle_auto_reload()
        assert subview.config_management["auto_reload"] is True
        
        # 再次切换
        subview.toggle_auto_reload()
        assert subview.config_management["auto_reload"] is False


class TestErrorsSubview:
    """错误反馈子界面测试"""
    
    def test_errors_subview_initialization(self):
        """测试错误反馈子界面初始化"""
        config = Mock(spec=TUIConfig)
        subview = ErrorsSubview(config)
        
        assert subview.get_title() == "🚨 错误反馈"
        assert len(subview.error_list) == 0
        assert subview.error_stats["total_errors"] == 0
    
    def test_error_addition(self):
        """测试错误添加"""
        config = Mock(spec=TUIConfig)
        subview = ErrorsSubview(config)
        
        test_error = {
            "message": "Test error",
            "level": "error",
            "category": "system"
        }
        
        subview.add_error(test_error)
        assert len(subview.error_list) == 1
        assert subview.error_list[0]["message"] == "Test error"
        assert "id" in subview.error_list[0]
        assert "timestamp" in subview.error_list[0]
    
    def test_error_selection(self):
        """测试错误选择"""
        config = Mock(spec=TUIConfig)
        subview = ErrorsSubview(config)
        
        # 添加错误
        test_error = {"message": "Test error"}
        subview.add_error(test_error)
        
        # 选择错误
        error_id = subview.error_list[0]["id"]
        result = subview.select_error(error_id)
        assert result is True
        assert subview.selected_error["message"] == "Test error"
    
    def test_error_resolution(self):
        """测试错误解决"""
        config = Mock(spec=TUIConfig)
        subview = ErrorsSubview(config)
        
        # 添加错误
        test_error = {"message": "Test error"}
        subview.add_error(test_error)
        
        # 解决错误
        error_id = subview.error_list[0]["id"]
        result = subview.resolve_error(error_id)
        assert result is True
        assert subview.error_list[0]["resolved"] is True
    
    def test_error_statistics(self):
        """测试错误统计"""
        config = Mock(spec=TUIConfig)
        subview = ErrorsSubview(config)
        
        # 添加不同级别的错误
        subview.add_error({"level": "critical", "message": "Critical error"})
        subview.add_error({"level": "warning", "message": "Warning error"})
        subview.add_error({"level": "error", "message": "Normal error"})
        
        stats = subview.error_stats
        assert stats["total_errors"] == 3
        assert stats["critical_errors"] == 1
        assert stats["warning_errors"] == 1
    
    def test_feedback_settings(self):
        """测试反馈设置"""
        config = Mock(spec=TUIConfig)
        subview = ErrorsSubview(config)
        
        # 默认设置
        assert subview.feedback_settings["auto_report"] is False
        assert subview.feedback_settings["include_stacktrace"] is True
        
        # 切换设置
        subview.toggle_auto_report()
        assert subview.feedback_settings["auto_report"] is True
        
        subview.toggle_include_stacktrace()
        assert subview.feedback_settings["include_stacktrace"] is False


class TestSubviewIntegration:
    """子界面集成测试"""
    
    def test_all_subviews_render(self):
        """测试所有子界面渲染"""
        config = Mock(spec=TUIConfig)
        
        subviews = [
            AnalyticsSubview(config),
            VisualizationSubview(config),
            SystemSubview(config),
            ErrorsSubview(config)
        ]
        
        for subview in subviews:
            # 所有子界面都应该能够渲染
            panel = subview.render()
            assert panel is not None
            assert subview.get_title() in str(panel)
    
    def test_subview_key_handling(self):
        """测试子界面按键处理"""
        config = Mock(spec=TUIConfig)
        
        subviews = [
            AnalyticsSubview(config),
            VisualizationSubview(config),
            SystemSubview(config),
            ErrorsSubview(config)
        ]
        
        for subview in subviews:
            # ESC键应该被所有子界面处理
            assert subview.handle_key("escape") is True
            
            # 其他键的处理可能因子界面而异
            # 但至少不应该抛出异常
            try:
                subview.handle_key("unknown_key")
            except Exception:
                pytest.fail(f"Subview {subview.__class__.__name__} raised exception on unknown key")


if __name__ == "__main__":
    pytest.main([__file__])
