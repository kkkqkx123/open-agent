"""测试内容变化触发的刷新机制"""

import time
from unittest.mock import Mock, MagicMock
from src.presentation.tui.render_controller import RenderController
from src.presentation.tui.layout import LayoutManager
from src.presentation.tui.config import get_tui_config


def test_content_change_refresh_mechanism():
    """测试内容变化触发的刷新机制"""
    print("🧪 测试内容变化触发的刷新机制")
    print("=" * 50)
    
    # 创建渲染控制器
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
    
    # 创建模拟子界面
    subviews = {
        "analytics": Mock(),
        "visualization": Mock(),
        "system": Mock(),
        "errors": Mock()
    }
    
    render_controller = RenderController(layout_manager, components, subviews, config)
    
    # 创建模拟Live对象
    mock_live = Mock()
    refresh_count = 0
    
    def count_refresh():
        nonlocal refresh_count
        refresh_count += 1
        print(f" 🔄 执行刷新 #{refresh_count}")
    
    mock_live.refresh = Mock(side_effect=count_refresh)
    render_controller.set_live(mock_live)
    
    # 创建模拟状态管理器
    mock_state_manager = Mock()
    mock_state_manager.current_subview = None
    mock_state_manager.show_session_dialog = False
    mock_state_manager.show_agent_dialog = False
    mock_state_manager.session_id = None
    mock_state_manager.message_history = []
    mock_state_manager.current_state = None
    
    print("  模拟无内容变化的多次UI更新...")
    # 模拟多次UI更新，但状态没有变化
    no_change_refreshes = 0
    for i in range(10):
        needs_refresh = render_controller.update_ui(mock_state_manager)
        if needs_refresh:
            no_change_refreshes += 1
        time.sleep(0.01)  # 短暂延迟
    
    print(f"    状态无变化时的刷新次数: {no_change_refreshes}")
    
    # 模拟状态变化
    print("  模拟内容变化...")
    mock_state_manager.session_id = "new_session_123"
    mock_state_manager.message_history = [{"type": "user", "content": "Hello"}]
    
    print(" 模拟有内容变化的UI更新...")
    # 模拟UI更新，此时状态有变化
    change_refreshes = 0
    for i in range(5):
        needs_refresh = render_controller.update_ui(mock_state_manager)
        if needs_refresh:
            change_refreshes += 1
        time.sleep(0.01)  # 短暂延迟
    
    print(f"    状态有变化时的刷新次数: {change_refreshes}")
    
    # 验证结果
    print("\n📊 测试结果:")
    print(f" 无变化时刷新次数: {no_change_refreshes}/10")
    print(f"  有变化时刷新次数: {change_refreshes}/5")
    
    # 无变化时应该很少或没有刷新，有变化时应该有刷新
    if no_change_refreshes == 0 and change_refreshes > 0:
        print("  ✅ 内容变化触发的刷新机制工作正常")
        success = True
    elif no_change_refreshes <= 2 and change_refreshes > 0:  # 容忍少量刷新
        print(" ✅ 内容变化触发的刷新机制基本正常")
        success = True
    else:
        print("  ❌ 内容变化触发的刷新机制存在问题")
        success = False
    
    print(f"\n📈 总体刷新次数: {refresh_count}")
    
    return success


def test_render_stats():
    """测试渲染统计信息"""
    print("\n📊 测试渲染统计信息")
    print("=" * 30)
    
    # 创建渲染控制器
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
    
    # 创建模拟子界面
    subviews = {
        "analytics": Mock(),
        "visualization": Mock(),
        "system": Mock(),
        "errors": Mock()
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
    mock_state_manager.session_id = None
    mock_state_manager.message_history = []
    mock_state_manager.current_state = None
    
    # 获取初始统计信息
    initial_stats = render_controller.get_render_stats()
    print(f"  初始跳过更新数: {initial_stats['skipped_updates']}")
    print(f"  初始总更新数: {initial_stats['total_updates']}")
    
    # 模拟多次无变化的更新
    for i in range(20):
        mock_state_manager.session_id = None # 保持不变
        render_controller.update_ui(mock_state_manager)
    
    # 获取更新后的统计信息
    stats_after_no_change = render_controller.get_render_stats()
    print(f"  无变化后跳过更新数: {stats_after_no_change['skipped_updates']}")
    print(f"  无变化后总更新数: {stats_after_no_change['total_updates']}")
    
    # 模拟状态变化
    mock_state_manager.session_id = "changed_session"
    
    # 模拟几次有变化的更新
    for i in range(5):
        render_controller.update_ui(mock_state_manager)
    
    # 获取变化后的统计信息
    stats_after_change = render_controller.get_render_stats()
    print(f"  有变化后跳过更新数: {stats_after_change['skipped_updates']}")
    print(f"  有变化后总更新数: {stats_after_change['total_updates']}")
    
    # 检查统计信息是否合理
    if (stats_after_no_change['skipped_updates'] >= 15 and  # 大部分无变化的更新被跳过
        stats_after_change['total_updates'] >= 5):         # 有变化的更新被执行
        print("  ✅ 渲染统计信息正常")
        return True
    else:
        print("  ❌ 渲染统计信息异常")
        return False


def main():
    """主函数"""
    print("🚀 开始测试内容变化触发的刷新机制")
    print("=" * 60)
    
    # 运行测试
    test1_success = test_content_change_refresh_mechanism()
    test2_success = test_render_stats()
    
    print("\n" + "=" * 60)
    print("📋 最终测试结果:")
    if test1_success and test2_success:
        print(" 🎉 所有测试通过！内容变化触发的刷新机制工作正常")
        print("  ✅ TUI的刷新机制已成功优化，只在内容变化时刷新")
    else:
        print("  ❌ 部分测试失败，需要进一步调试")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
