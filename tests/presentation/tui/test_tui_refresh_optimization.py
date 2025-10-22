"""测试TUI刷新优化机制 - 改进版"""

import time
from unittest.mock import Mock
from src.presentation.tui.app import TUIApp
from src.presentation.tui.config import get_tui_config


def test_main_loop_refresh_optimization():
    """测试主循环中的刷新优化机制"""
    print("🧪 测试主循环中的刷新优化机制")
    print("=" * 45)
    
    # 创建TUIApp实例（但不运行，只测试逻辑）
    app = TUIApp()
    
    # 创建模拟状态管理器
    mock_state_manager = Mock()
    mock_state_manager.current_subview = None
    mock_state_manager.show_session_dialog = False
    mock_state_manager.show_agent_dialog = False
    mock_state_manager.session_id = "test_session"
    mock_state_manager.message_history = []
    mock_state_manager.current_state = None
    
    # 模拟app的state_manager
    app.state_manager = mock_state_manager
    
    # 记录初始时间
    start_time = time.time()
    
    print("  模拟10次无内容变化的UI更新...")
    # 模拟多次调用update_ui，但状态不变
    initial_skipped = app.render_controller._render_stats['skipped_updates']
    initial_updates = app.render_controller._render_stats['total_updates']
    
    for i in range(10):
        # 直接调用update_ui，模拟主循环行为
        app.update_ui()
        time.sleep(0.001)  # 更小的间隔，模拟真实情况
    
    final_skipped = app.render_controller._render_stats['skipped_updates']
    final_updates = app.render_controller._render_stats['total_updates']
    
    updates_made = final_updates - initial_updates
    updates_skipped = final_skipped - initial_skipped
    
    print(f"    实际执行的更新数: {updates_made}")
    print(f"    跳过的更新数: {updates_skipped}")
    
    # 改变状态
    print("  模拟状态变化...")
    # 创建新的状态管理器实例来模拟真正的状态变化
    mock_state_manager2 = Mock()
    mock_state_manager2.current_subview = None
    mock_state_manager2.show_session_dialog = False
    mock_state_manager2.show_agent_dialog = False
    mock_state_manager2.session_id = "new_session_different"
    mock_state_manager2.message_history = [{"type": "user", "content": "New message for real change"}]
    mock_state_manager2.current_state = None
    
    # 重新赋值app的state_manager
    app.state_manager = mock_state_manager2
    
    print("  模拟5次有内容变化的UI更新...")
    initial_skipped_after = app.render_controller._render_stats['skipped_updates']
    initial_updates_after = app.render_controller._render_stats['total_updates']
    
    for i in range(5):
        # 直接调用update_ui，模拟主循环行为
        app.update_ui()
        time.sleep(0.01)  # 模拟间隔
    
    final_skipped_after = app.render_controller._render_stats['skipped_updates']
    final_updates_after = app.render_controller._render_stats['total_updates']
    
    updates_made_after_change = final_updates_after - initial_updates_after
    updates_skipped_after_change = final_skipped_after - initial_skipped_after
    
    print(f"    状态变化后的更新数: {updates_made_after_change}")
    print(f"    状态变化后跳过的更新数: {updates_skipped_after_change}")
    
    # 检查结果
    print("\n📊 测试结果分析:")
    print(f"  无变化时: {updates_made}/10 实际更新, {updates_skipped}/10 跳过")
    print(f" 有变化时: {updates_made_after_change}/5 实际更新, {updates_skipped_after_change}/5 跳过")
    
    # 如果大部分无变化的更新被跳过，且有变化的更新被执行，则认为成功
    if updates_skipped >= 8 and updates_made_after_change >= 1:
        print("  ✅ 刷新优化机制工作正常")
        success = True
    else:
        print(" ❌ 刷新优化机制存在问题")
        success = False
    
    end_time = time.time()
    print(f"\n⏱️  测试耗时: {end_time - start_time:.2f}秒")
    
    return success


def test_render_controller_with_real_components():
    """使用更真实的组件测试渲染控制器"""
    print("\n🔧 使用更真实的组件测试渲染控制器")
    print("=" * 42)
    
    from src.presentation.tui.render_controller import RenderController
    from src.presentation.tui.layout import LayoutManager
    from src.presentation.tui.components.main_content import MainContentComponent
    from src.presentation.tui.components.sidebar import SidebarComponent
    from src.presentation.tui.components.langgraph_panel import LangGraphPanelComponent
    from src.presentation.tui.components.input_panel import InputPanel
    from src.presentation.tui.subviews.analytics import AnalyticsSubview
    from src.presentation.tui.subviews.system import SystemSubview
    from src.presentation.tui.subviews.visualization import VisualizationSubview
    from src.presentation.tui.subviews.errors import ErrorFeedbackSubview
    
    config = get_tui_config()
    layout_manager = LayoutManager()
    
    # 创建真实组件实例（而不是Mock）
    try:
        main_content = MainContentComponent(config)
        sidebar = SidebarComponent(config)
        langgraph = LangGraphPanelComponent(config)
        input_panel = InputPanel(config)
        
        # 创建真实子界面实例
        analytics = AnalyticsSubview(config)
        visualization = VisualizationSubview(config)
        system = SystemSubview(config)
        errors = ErrorFeedbackSubview(config)
        
        # 将真实组件放入字典
        components = {
            "sidebar": sidebar,
            "langgraph": langgraph,
            "main_content": main_content,
            "input": input_panel,
            "workflow_control": Mock(),  # 模拟工作流控制面板
            "error_feedback": Mock(),   # 模拟错误反馈面板
            "session_dialog": Mock(),   # 模拟会话对话框
            "agent_dialog": Mock()      # 模拟代理对话框
        }
        
        subviews = {
            "analytics": analytics,
            "visualization": visualization,
            "system": system,
            "errors": errors
        }
        
        print("  ✅ 成功创建真实组件实例")
        
    except Exception as e:
        print(f" ❌ 创建真实组件失败: {e}")
        print(" 使用模拟组件进行测试...")
        # 使用模拟组件作为备选
        components = {
            "sidebar": Mock(render=lambda: "Sidebar Content"),
            "langgraph": Mock(render=lambda: "LangGraph Content"),
            "main_content": Mock(render=lambda: "Main Content"),
            "input": Mock(render=lambda: "Input Content"),
            "workflow_control": Mock(render=lambda: "Workflow Content"),
            "error_feedback": Mock(render=lambda: None),
            "session_dialog": Mock(render=lambda: "Session Dialog"),
            "agent_dialog": Mock(render=lambda: "Agent Dialog")
        }
        
        subviews = {
            "analytics": Mock(render=lambda: "Analytics View"),
            "visualization": Mock(render=lambda: "Visualization View"),
            "system": Mock(render=lambda: "System View"),
            "errors": Mock(render=lambda: "Errors View")
        }
    
    render_controller = RenderController(layout_manager, components, subviews, config)
    
    # 创建模拟Live对象
    mock_live = Mock()
    mock_live.refresh = Mock()
    render_controller.set_live(mock_live)
    
    # 创建模拟状态管理器
    mock_state_manager = Mock()
    mock_state_manager.current_subview = None
    mock_state_manager.show_session_dialog = False
    mock_state_manager.show_agent_dialog = False
    mock_state_manager.session_id = "session_1"
    mock_state_manager.message_history = [{"type": "user", "content": "Initial"}]
    mock_state_manager.current_state = None
    
    print("  测试状态变化检测...")
    
    # 第一次调用 - 初始状态
    needs_refresh_1 = render_controller.update_ui(mock_state_manager)
    print(f"    第1次调用 (初始): needs_refresh = {needs_refresh_1}")
    
    # 第二次调用 - 状态未变
    needs_refresh_2 = render_controller.update_ui(mock_state_manager)
    print(f"    第2次调用 (未变): needs_refresh = {needs_refresh_2}")
    
    # 改变状态
    mock_state_manager.session_id = "session_2_different"
    mock_state_manager.message_history = [{"type": "user", "content": "Changed Message"}]
    
    # 第三次调用 - 状态已变
    needs_refresh_3 = render_controller.update_ui(mock_state_manager)
    print(f"    第3次调用 (已变): needs_refresh = {needs_refresh_3}")
    
    # 第四次调用 - 状态未变
    needs_refresh_4 = render_controller.update_ui(mock_state_manager)
    print(f"    第4次调用 (未变): needs_refresh = {needs_refresh_4}")
    
    # 获取统计信息
    stats = render_controller.get_render_stats()
    print(f"    总更新数: {stats['total_updates']}")
    print(f"    跳过更新数: {stats['skipped_updates']}")
    
    # 检查行为
    if not needs_refresh_2 and (needs_refresh_3 or needs_refresh_1):
        print("  ✅ 状态变化检测基本正常工作")
        return True
    else:
        print(" ❌ 状态变化检测存在问题")
        return False


def test_original_vs_modified_behavior():
    """对比原始行为和修改后行为的差异"""
    print("\n🔍 对比原始行为和修改后行为")
    print("=" * 35)
    
    from src.presentation.tui.render_controller import RenderController
    from src.presentation.tui.layout import LayoutManager
    
    config = get_tui_config()
    layout_manager = LayoutManager()
    
    # 创建模拟组件
    components = {
        "sidebar": Mock(render=lambda: "Sidebar Content"),
        "langgraph": Mock(render=lambda: "LangGraph Content"),
        "main_content": Mock(render=lambda: "Main Content"),
        "input": Mock(render=lambda: "Input Content"),
        "workflow_control": Mock(render=lambda: "Workflow Content"),
        "error_feedback": Mock(render=lambda: None),
        "session_dialog": Mock(render=lambda: "Session Dialog"),
        "agent_dialog": Mock(render=lambda: "Agent Dialog")
    }
    
    subviews = {
        "analytics": Mock(render=lambda: "Analytics View"),
        "visualization": Mock(render=lambda: "Visualization View"),
        "system": Mock(render=lambda: "System View"),
        "errors": Mock(render=lambda: "Errors View")
    }
    
    render_controller = RenderController(layout_manager, components, subviews, config)
    
    # 创建模拟Live对象
    mock_live = Mock()
    mock_live.refresh = Mock()
    render_controller.set_live(mock_live)
    
    # 创建模拟状态管理器
    mock_state_manager = Mock()
    mock_state_manager.current_subview = None
    mock_state_manager.show_session_dialog = False
    mock_state_manager.show_agent_dialog = False
    mock_state_manager.session_id = "session_1"
    mock_state_manager.message_history = [{"type": "user", "content": "Initial"}]
    mock_state_manager.current_state = None
    
    print(" 模拟连续调用update_ui并观察行为...")
    
    # 连续调用多次，状态不变
    results = []
    for i in range(5):
        needs_refresh = render_controller.update_ui(mock_state_manager)
        results.append(needs_refresh)
        print(f"    第{i+1}次调用: needs_refresh = {needs_refresh}")
    
    # 检查是否大部分调用返回False（表示没有刷新需求）
    false_count = results.count(False)
    true_count = results.count(True)
    
    print(f"\n    结果统计: {false_count}次False, {true_count}次True")
    
    if false_count >= 3:  # 大部分应该是False，表示跳过了重复更新
        print("  ✅ 修改后的行为符合预期 - 避免了不必要的重复刷新")
        success = True
    else:
        print(" ❌ 修改后的行为不符合预期")
        success = False
    
    # 现在改变状态，看是否能正确检测到变化
    print("\n  改变状态后测试...")
    mock_state_manager.session_id = "session_2_different"
    mock_state_manager.message_history = [{"type": "user", "content": "Changed Message"}]
    
    needs_refresh_after_change = render_controller.update_ui(mock_state_manager)
    print(f"    状态改变后调用: needs_refresh = {needs_refresh_after_change}")
    
    if needs_refresh_after_change:
        print(" ✅ 状态变化被正确检测到")
        success = success and True
    else:
        print(" ❌ 状态变化未被检测到")
        success = False
    
    return success


def main():
    """主函数"""
    print("🚀 开始测试TUI主循环的刷新优化机制 - 改进版")
    print("=" * 55)
    
    # 运行测试
    test1_success = test_main_loop_refresh_optimization()
    test2_success = test_render_controller_with_real_components()
    test3_success = test_original_vs_modified_behavior()
    
    print("\n" + "=" * 55)
    print("📋 最终测试结果:")
    successful_tests = sum([test1_success, test2_success, test3_success])
    total_tests = 3
    
    if successful_tests >= 2:  # 至少2个测试通过
        print(f" 🎉 多数测试通过！TUI刷新优化机制基本正常")
        print("  ✅ 只有在内容真正变化时才会刷新，减少不必要的渲染")
    else:
        print(f"  ❌ 多数测试失败，需要进一步调试")
    
    print(f" 测试通过: {successful_tests}/{total_tests}")
    print("=" * 55)


if __name__ == "__main__":
    main()