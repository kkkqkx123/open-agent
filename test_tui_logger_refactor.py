"""测试重构后的TUI日志记录器"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.presentation.tui.logger.tui_logger_manager import TUILoggerFactory, TUILoggerManager
from src.presentation.tui.logger.tui_logger_silent import get_tui_silent_logger
from src.presentation.tui.logger.tui_logger import get_tui_debug_logger


def test_logger_factory():
    """测试日志记录器工厂"""
    print("=== 测试日志记录器工厂 ===")
    
    # 测试创建静默日志记录器
    silent_logger = TUILoggerFactory.create_silent_logger("test_silent")
    print(f"创建静默日志记录器: {type(silent_logger).__name__}")
    
    # 测试创建调试日志记录器
    debug_logger = TUILoggerFactory.create_debug_logger("test_debug")
    print(f"创建调试日志记录器: {type(debug_logger).__name__}")
    
    # 测试通过类型创建日志记录器
    silent_logger2 = TUILoggerFactory.create_logger("silent", "test_silent2")
    debug_logger2 = TUILoggerFactory.create_logger("debug", "test_debug2")
    print(f"通过类型创建静默日志记录器: {type(silent_logger2).__name__}")
    print(f"通过类型创建调试日志记录器: {type(debug_logger2).__name__}")
    
    # 测试无效类型
    try:
        invalid_logger = TUILoggerFactory.create_logger("invalid", "test_invalid")
        print("错误：应该抛出异常")
    except ValueError as e:
        print(f"正确捕获异常: {e}")
    
    print()


def test_silent_logger():
    """测试静默日志记录器"""
    print("=== 测试静默日志记录器 ===")
    
    # 设置调试模式
    os.environ["TUI_DEBUG"] = "1"
    
    silent_logger = get_tui_silent_logger("test")
    print(f"获取静默日志记录器: {type(silent_logger).__name__}")
    
    # 测试各种日志方法
    silent_logger.debug_component_event("TestComponent", "click")
    silent_logger.debug_input_handling("keyboard", "a")
    silent_logger.debug_ui_state_change("TestComponent", "old", "new")
    silent_logger.debug_workflow_operation("start")
    silent_logger.debug_session_operation("create", "session123")
    silent_logger.debug_key_event("char:a", True, "test")
    silent_logger.debug_subview_navigation("main", "settings")
    silent_logger.debug_render_operation("TestComponent", "draw")
    silent_logger.debug_error_handling("TypeError", "test error")
    
    # 测试基础日志方法
    silent_logger.info("测试信息日志")
    silent_logger.warning("测试警告日志")
    silent_logger.error("测试错误日志")
    silent_logger.debug("测试调试日志")
    
    print("静默日志记录器测试完成")
    print()


def test_debug_logger():
    """测试调试日志记录器"""
    print("=== 测试调试日志记录器 ===")
    
    debug_logger = get_tui_debug_logger("test")
    print(f"获取调试日志记录器: {type(debug_logger).__name__}")
    
    # 测试各种日志方法
    debug_logger.debug_component_event("TestComponent", "click")
    debug_logger.debug_input_handling("keyboard", "a")
    debug_logger.debug_ui_state_change("TestComponent", "old", "new")
    debug_logger.debug_workflow_operation("start")
    debug_logger.debug_session_operation("create", "session123")
    debug_logger.debug_key_event("char:a", True, "test")
    debug_logger.debug_subview_navigation("main", "settings")
    debug_logger.debug_render_operation("TestComponent", "draw")
    debug_logger.debug_error_handling("TypeError", "test error")
    
    # 测试基础日志方法
    debug_logger.info("测试信息日志")
    debug_logger.warning("测试警告日志")
    debug_logger.error("测试错误日志")
    debug_logger.debug("测试调试日志")
    
    print("调试日志记录器测试完成")
    print()


def test_debug_mode():
    """测试调试模式切换"""
    print("=== 测试调试模式切换 ===")
    
    # 关闭调试模式
    os.environ["TUI_DEBUG"] = "0"
    
    silent_logger = get_tui_silent_logger("test_mode")
    debug_logger = get_tui_debug_logger("test_mode")
    
    print("调试模式关闭:")
    silent_logger.debug("这条静默日志不应该被记录")
    debug_logger.debug("这条调试日志应该被记录")
    
    # 开启调试模式
    os.environ["TUI_DEBUG"] = "1"
    
    # 重新初始化日志记录器
    silent_logger.set_debug_mode(True)
    debug_logger.set_debug_mode(True)
    
    print("调试模式开启:")
    silent_logger.debug("这条静默日志应该被记录")
    debug_logger.debug("这条调试日志应该被记录")
    
    print("调试模式切换测试完成")
    print()


def main():
    """主测试函数"""
    print("开始测试重构后的TUI日志记录器")
    print("=" * 50)
    
    try:
        test_logger_factory()
        test_silent_logger()
        test_debug_logger()
        test_debug_mode()
        
        print("=" * 50)
        print("所有测试完成！重构成功！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()