"""TUI集成测试

测试TUI各个组件的集成功能
"""

import pytest
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.presentation.tui.components.session_dialog import SessionManagerDialog
from src.presentation.tui.components.agent_dialog import AgentSelectDialog
from src.presentation.tui.components.workflow_control import WorkflowController
from src.presentation.tui.components.error_feedback import ErrorFeedbackSystem
from src.presentation.tui.components.config_reload import ConfigReloadManager
from src.presentation.tui.components.studio_manager import StudioServerManager
from src.presentation.tui.components.port_manager import PortManager
from src.presentation.tui.components.workflow_visualizer import WorkflowVisualizer
from src.presentation.tui.components.node_debugger import NodeDebugger
from src.presentation.tui.components.history_replay import HistoryReplayManager
from src.presentation.tui.components.performance_analyzer import PerformanceAnalyzer
from src.presentation.tui.components.studio_integration import StudioIntegrationManager


class TestTUIIntegration:
    """TUI集成测试类"""
    
    def test_session_dialog_creation(self):
        """测试会话对话框创建"""
        dialog = SessionManagerDialog()
        assert dialog is not None
        assert dialog.current_mode == "list"
        assert dialog.session_list is not None
        assert dialog.create_dialog is not None
    
    def test_agent_dialog_creation(self):
        """测试Agent对话框创建"""
        dialog = AgentSelectDialog()
        assert dialog is not None
        assert dialog.current_mode == "select"
        assert dialog.agent_list is not None
        assert dialog.agent_detail is not None
    
    def test_workflow_controller(self):
        """测试工作流控制器"""
        controller = WorkflowController()
        assert controller.state.value == "idle"
        
        # 测试启动工作流
        controller.start_workflow(10)
        assert controller.state.value == "running"
        assert controller.total_steps == 10
        
        # 测试暂停
        assert controller.pause_workflow() == True
        assert controller.state.value == "paused"
        
        # 测试恢复
        assert controller.resume_workflow() == True
        assert controller.state.value == "running"
        
        # 测试停止
        assert controller.stop_workflow() == True
        assert controller.state.value == "stopped"
    
    def test_error_feedback_system(self):
        """测试错误反馈系统"""
        feedback = ErrorFeedbackSystem()
        assert len(feedback.notifications) == 0
        
        # 测试添加通知
        feedback.add_info("测试信息")
        feedback.add_success("测试成功")
        feedback.add_warning("测试警告")
        feedback.add_error("测试错误", "错误详情")
        
        assert len(feedback.notifications) == 4
        
        # 测试获取最近通知
        recent = feedback.get_recent_notifications(2)
        assert len(recent) == 2
    
    def test_port_manager(self):
        """测试端口管理器"""
        manager = PortManager()
        
        # 测试端口分配
        port = manager.allocate_port("studio", "test_session")
        assert port is not None
        assert 8123 <= port <= 8223
        
        # 测试端口释放
        assert manager.release_port(port) == True
        
        # 测试会话端口释放
        port2 = manager.allocate_port("studio", "test_session2")
        port3 = manager.allocate_port("api", "test_session2")
        released_ports = manager.release_session_ports("test_session2")
        assert len(released_ports) == 2
    
    def test_workflow_visualizer(self):
        """测试工作流可视化器"""
        visualizer = WorkflowVisualizer()
        assert visualizer.graph is not None
        assert len(visualizer.graph.nodes) > 0
        
        # 测试节点选择
        node_ids = list(visualizer.graph.nodes.keys())
        if node_ids:
            visualizer.select_node(node_ids[0])
            assert visualizer.selected_node == node_ids[0]
    
    def test_node_debugger(self):
        """测试节点调试器"""
        debugger = NodeDebugger()
        assert debugger.mode.value == "off"
        
        # 测试设置调试模式
        from src.presentation.tui.components.node_debugger import DebugMode
        debugger.set_mode(DebugMode.STEP)
        assert debugger.mode.value == "step"
        
        # 测试断点
        bp_id = debugger.add_breakpoint("test_node")
        assert bp_id is not None
        assert len(debugger.breakpoints) == 1
        
        # 测试移除断点
        assert debugger.remove_breakpoint(bp_id) == True
        assert len(debugger.breakpoints) == 0
    
    def test_history_replay_manager(self):
        """测试历史回放管理器"""
        manager = HistoryReplayManager()
        
        # 测试创建历史
        from src.presentation.tui.components.history_replay import SessionHistory
        history = SessionHistory("test_session")
        history.add_event("test_event", {"data": "test"})
        
        # 测试保存历史
        assert manager.save_history(history) == True
        assert "test_session" in manager.histories
        
        # 测试加载历史
        loaded_history = manager.load_history("test_session")
        assert loaded_history is not None
        assert len(loaded_history.events) == 1
    
    def test_performance_analyzer(self):
        """测试性能分析器"""
        analyzer = PerformanceAnalyzer()
        
        # 测试开始会话
        analyzer.start_session("test_session")
        assert analyzer.current_session == "test_session"
        
        # 测试添加指标
        from src.presentation.tui.components.performance_analyzer import MetricType
        analyzer.add_metric("test_metric", 100.0, MetricType.GAUGE)
        analyzer.increment_counter("test_counter")
        analyzer.record_timer("test_timer", 1.5)
        
        # 测试结束会话
        analyzer.end_session()
        assert analyzer.current_session is None
        
        # 测试分析
        analysis = analyzer.analyze_session("test_session")
        assert analysis["session_id"] == "test_session"
        assert analysis["total_metrics"] == 3
    
    def test_studio_integration_manager(self):
        """测试Studio集成管理器"""
        manager = StudioIntegrationManager()
        
        # 测试设置URL和会话
        manager.set_studio_url("http://localhost:8123")
        manager.set_session_id("test_session")
        assert manager.studio_url == "http://localhost:8123"
        assert manager.session_id == "test_session"
        
        # 测试启用同步
        from src.presentation.tui.components.studio_integration import SyncDirection
        manager.enable_sync(SyncDirection.BIDIRECTIONAL)
        assert manager.sync_enabled == True
        assert manager.sync_direction == SyncDirection.BIDIRECTIONAL
        
        # 测试跳转到Studio
        url = manager.jump_to_studio("test_node")
        assert "test_node" in url
        assert "test_session" in url
    
    def test_component_integration(self):
        """测试组件集成"""
        # 创建各个组件
        session_dialog = SessionManagerDialog()
        agent_dialog = AgentSelectDialog()
        workflow_controller = WorkflowController()
        feedback_system = ErrorFeedbackSystem()
        port_manager = PortManager()
        visualizer = WorkflowVisualizer()
        debugger = NodeDebugger()
        replay_manager = HistoryReplayManager()
        analyzer = PerformanceAnalyzer()
        integration_manager = StudioIntegrationManager()
        
        # 测试基本集成
        assert session_dialog is not None
        assert agent_dialog is not None
        assert workflow_controller is not None
        assert feedback_system is not None
        assert port_manager is not None
        assert visualizer is not None
        assert debugger is not None
        assert replay_manager is not None
        assert analyzer is not None
        assert integration_manager is not None
        
        # 测试组件间的数据流
        workflow_controller.start_workflow(5)
        workflow_controller.update_step("test_step")
        workflow_controller.complete_step()
        
        feedback_system.add_info("工作流步骤完成")
        
        analyzer.start_session("integration_test")
        analyzer.record_timer("step_duration", 0.5)
        analyzer.end_session()
        
        integration_manager.set_session_id("integration_test")
        integration_manager.sync_workflow_state({"current_step": "test_step"})


def run_integration_tests():
    """运行集成测试"""
    test_instance = TestTUIIntegration()
    
    tests = [
        test_instance.test_session_dialog_creation,
        test_instance.test_agent_dialog_creation,
        test_instance.test_workflow_controller,
        test_instance.test_error_feedback_system,
        test_instance.test_port_manager,
        test_instance.test_workflow_visualizer,
        test_instance.test_node_debugger,
        test_instance.test_history_replay_manager,
        test_instance.test_performance_analyzer,
        test_instance.test_studio_integration_manager,
        test_instance.test_component_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__} - 通过")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} - 失败: {e}")
            failed += 1
    
    print(f"\n测试结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    print("开始TUI集成测试...")
    success = run_integration_tests()
    if success:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查代码")
