"""改进的测试内容变化触发的刷新机制"""

import time
from unittest.mock import Mock, MagicMock, PropertyMock
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
    
    # 为组件添加render方法，返回固定内容
    for name, comp in components.items():
        if name == "main_content":
            comp.render = Mock(return_value="Main Content")
        elif name == "sidebar":
            comp.render = Mock(return_value="Sidebar")
        elif name == "langgraph":
            comp.render = Mock(return_value="LangGraph")
        elif name == "input":
            comp.render = Mock(return_value="Input Panel")
        elif name == "workflow_control":
            comp.render = Mock(return_value="Workflow Control")
        elif name == "error_feedback":
            comp.render = Mock(return_value=None)
        elif name == "session_dialog":
            comp.render = Mock(return_value="Session Dialog")
        elif name == "agent_dialog":
            comp.render = Mock(return_value="Agent Dialog")
    
    # 创建模拟子界面
    subviews = {
        "analytics": Mock(),
        "visualization": Mock(),
        "system": Mock(),
        "errors": Mock()
    }
    
    # 为子界面添加render方法
    for name, view in subviews.items():
        view.render = Mock(return_value=f"{name} View")
    
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
    mock_state_manager.session_id = "session_123"
    mock_state_manager.message_history = []
    mock_state_manager.current_state = None
    
    print("  模拟无内容变化的多次UI更新...")
    # 模拟多次UI更新，但状态没有变化
    no_change_refreshes = 0
    for i in range(5):
        needs_refresh = render_controller.update_ui(mock_state_manager)
        if needs_refresh:
            no_change_refreshes += 1
        time.sleep(0.01)  # 短暂延迟
    
    print(f"    状态无变化时的刷新次数: {no_change_refreshes}")
    
    # 模拟状态变化
    print("  模拟内容变化...")
    mock_state_manager.session_id = "new_session_456"  # 改变状态
    mock_state_manager.message_history = [{"type": "user", "content": "Hello"}]
    
    print("  模拟有内容变化的UI更新...")
    # 模拟UI更新，此时状态有变化
    change_refreshes = 0
    for i in range(3):
        needs_refresh = render_controller.update_ui(mock_state_manager)
        if needs_refresh:
            change_refreshes += 1
        time.sleep(0.01)  # 短暂延迟
    
    print(f"    状态有变化时的刷新次数: {change_refreshes}")
    
    # 验证结果
    print("\n📊 测试结果:")
    print(f" 无变化时刷新次数: {no_change_refreshes}/5")
    print(f"  有变化时刷新次数: {change_refreshes}/3")
    
    # 无变化时应该很少或没有刷新，有变化时应该有刷新
    if no_change_refreshes <= 1 and change_refreshes >= 1:
        print("  ✅ 内容变化触发的刷新机制工作正常")
        success = True
    else:
        print("  ❌ 内容变化触发的刷新机制存在问题")
        success = False
    
    print(f"\n📈 总体刷新次数: {refresh_count}")
    
    return success


def test_render_controller_internal_state():
    """测试渲染控制器内部状态变化检测"""
    print("\n🔍 测试渲染控制器内部状态变化检测")
    print("=" * 45)
    
    # 创建渲染控制器
    config = get_tui_config()
    layout_manager = LayoutManager()
    
    # 创建模拟组件
    components = {
        "sidebar": Mock(render=Mock(return_value="Sidebar")),
        "langgraph": Mock(render=Mock(return_value="LangGraph")),
        "main_content": Mock(render=Mock(return_value="Main Content")),
        "input": Mock(render=Mock(return_value="Input")),
        "workflow_control": Mock(render=Mock(return_value="Workflow")),
        "error_feedback": Mock(render=Mock(return_value=None)),
        "session_dialog": Mock(render=Mock(return_value="Session Dialog")),
        "agent_dialog": Mock(render=Mock(return_value="Agent Dialog"))
    }
    
    # 创建模拟子界面
    subviews = {
        "analytics": Mock(render=Mock(return_value="Analytics")),
        "visualization": Mock(render=Mock(return_value="Visualization")),
        "system": Mock(render=Mock(return_value="System")),
        "errors": Mock(render=Mock(return_value="Errors"))
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
    
    # 第一次调用，应该需要刷新（初始状态）
    needs_refresh_1 = render_controller.update_ui(mock_state_manager)
    print(f"  第一次调用: needs_refresh = {needs_refresh_1}")
    
    # 第二次调用，状态未变，不应该需要刷新
    needs_refresh_2 = render_controller.update_ui(mock_state_manager)
    print(f"  第二次调用(状态未变): needs_refresh = {needs_refresh_2}")
    
    # 改变状态
    mock_state_manager.session_id = "session_2"
    mock_state_manager.message_history = [{"type": "user", "content": "Changed"}]
    
    # 第三次调用，状态已变，应该需要刷新
    needs_refresh_3 = render_controller.update_ui(mock_state_manager)
    print(f"  第三次调用(状态已变): needs_refresh = {needs_refresh_3}")
    
    # 第四次调用，状态未变，不应该需要刷新
    needs_refresh_4 = render_controller.update_ui(mock_state_manager)
    print(f"  第四次调用(状态未变): needs_refresh = {needs_refresh_4}")
    
    # 检查行为是否符合预期
    if not needs_refresh_2 and needs_refresh_3:
        print("  ✅ 状态变化检测机制工作正常")
        return True
    else:
        print("  ❌ 状态变化检测机制存在问题")
        return False


def main():
    """主函数"""
    print("🚀 开始测试改进的内容变化触发的刷新机制")
    print("=" * 60)
    
    # 运行测试
    test1_success = test_content_change_refresh_mechanism()
    test2_success = test_render_controller_internal_state()
    
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
