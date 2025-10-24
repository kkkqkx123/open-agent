"""测试TUI主循环中的条件刷新机制"""

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
    refresh_count_before = app.render_controller._render_stats['total_updates']
    skipped_count_before = app.render_controller._render_stats['skipped_updates']
    
    for i in range(10):
        # 直接调用update_ui，模拟主循环行为
        app.update_ui()
        time.sleep(0.01)  # 模拟间隔
    
    refresh_count_after = app.render_controller._render_stats['total_updates']
    skipped_count_after = app.render_controller._render_stats['skipped_updates']
    
    updates_made = refresh_count_after - refresh_count_before
    updates_skipped = skipped_count_after - skipped_count_before
    
    print(f"    实际执行的更新数: {updates_made}")
    print(f"    跳过的更新数: {updates_skipped}")
    
    # 改变状态
    print("  模拟状态变化...")
    mock_state_manager.session_id = "new_session"
    mock_state_manager.message_history = [{"type": "user", "content": "New message"}]
    
    print("  模拟5次有内容变化的UI更新...")
    refresh_count_before = app.render_controller._render_stats['total_updates']
    skipped_count_before = app.render_controller._render_stats['skipped_updates']
    
    for i in range(5):
        # 直接调用update_ui，模拟主循环行为
        app.update_ui()
        time.sleep(0.01)  # 模拟间隔
    
    refresh_count_after = app.render_controller._render_stats['total_updates']
    skipped_count_after = app.render_controller._render_stats['skipped_updates']
    
    updates_made_after_change = refresh_count_after - refresh_count_before
    updates_skipped_after_change = skipped_count_after - skipped_count_before
    
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
        print("  ❌ 刷新优化机制存在问题")
        success = False
    
    end_time = time.time()
    print(f"\n⏱️  测试耗时: {end_time - start_time:.2f}秒")
    
    return success


def test_render_controller_directly():
    """直接测试渲染控制器"""
    print("\n🔧 直接测试渲染控制器")
    print("=" * 30)
    
    from src.presentation.tui.render_controller import RenderController
    from src.presentation.tui.layout import LayoutManager
    
    config = get_tui_config()
    layout_manager = LayoutManager()
    
    # 创建模拟组件
    components = {
        "sidebar": Mock(),
        "langgraph": Mock(),
        "main_content": Mock(),
        "input": Mock(),
        "workflow_control": Mock(),
        "error_feedback": Mock(),
        "session_dialog": Mock(),
        "agent_dialog": Mock()
    }
    
    # 为组件添加render方法
    for name, comp in components.items():
        if hasattr(comp, 'render'):
            continue
        comp.render = Mock(return_value=f"{name}_content")
    
    # 创建模拟子界面
    subviews = {
        "analytics": Mock(),
        "visualization": Mock(),
        "system": Mock(),
        "errors": Mock()
    }
    
    # 为子界面添加render方法
    for name, view in subviews.items():
        if hasattr(view, 'render'):
            continue
        view.render = Mock(return_value=f"{name}_view")
    
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
    mock_state_manager.session_id = "session_2"
    mock_state_manager.message_history = [{"type": "user", "content": "Changed"}]
    
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
    if not needs_refresh_2 and needs_refresh_3:
        print("  ✅ 状态变化检测正常工作")
        return True
    else:
        print("  ❌ 状态变化检测存在问题")
        return False


def main():
    """主函数"""
    print("🚀 开始测试TUI主循环的刷新优化机制")
    print("=" * 55)
    
    # 运行测试
    test1_success = test_main_loop_refresh_optimization()
    test2_success = test_render_controller_directly()
    
    print("\n" + "=" * 55)
    print("📋 最终测试结果:")
    if test1_success and test2_success:
        print(" 🎉 所有测试通过！TUI刷新优化机制工作正常")
        print("  ✅ 只有在内容真正变化时才会刷新，减少不必要的渲染")
    else:
        print("  ❌ 部分测试失败，需要进一步调试")
    
    print("=" * 55)


if __name__ == "__main__":
    main()
