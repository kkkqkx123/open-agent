"""测试TUI实际刷新行为"""

import time
import threading
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.presentation.tui.app import TUIApp


def test_actual_refresh_behavior():
    """测试实际刷新行为"""
    print("🔍 测试TUI实际刷新行为...")
    
    # 创建TUIApp实例
    app = TUIApp()
    
    # 模拟多次调用update_ui
    print("  - 模拟内容无变化时的多次update_ui调用...")
    
    refresh_count = 0
    total_calls = 0
    
    # 记录开始时间
    start_time = time.time()
    
    # 连续调用update_ui 50次
    for i in range(50):
        needs_refresh = app.update_ui()
        total_calls += 1
        if needs_refresh:
            refresh_count += 1
        time.sleep(0.001)  # 模拟实际循环时间
    
    end_time = time.time()
    
    print(f"  - 在{end_time - start_time:.3f}秒内，共调用update_ui {total_calls}次")
    print(f"  - 其中 {refresh_count} 次需要实际刷新")
    print(f"  - {total_calls - refresh_count} 次无需刷新")
    
    if refresh_count == 0:
        print(" ✅ 优化成功：内容无变化时无实际刷新")
        success1 = True
    else:
        print("  ❌ 仍有不必要的刷新")
        success1 = False
    
    # 现在模拟内容变化
    print("\n  - 模拟内容变化后的行为...")
    
    # 添加一条系统消息以触发内容变化
    app.state_manager.add_system_message("Test message to trigger change")
    
    # 短暂等待变化生效
    time.sleep(0.01)
    
    # 再次调用update_ui
    needs_refresh_after_change = app.update_ui()
    
    if needs_refresh_after_change:
        print("  ✅ 内容变化后能正确检测并标记需要刷新")
        success2 = True
    else:
        print("  ❌ 内容变化后未能检测到需要刷新")
        success2 = False
    
    return success1 and success2


def test_refresh_rate_comparison():
    """测试刷新率对比"""
    print("\n📊 测试刷新率对比...")
    
    app = TUIApp()
    
    print("  - 修复前行为：固定刷新率（每秒10次，即使内容无变化）")
    print("  - 修复后行为：仅在内容变化时刷新")
    
    # 测试10秒内的行为
    start_time = time.time()
    
    # 模拟10秒内每秒调用10次（模拟之前的固定刷新率）
    call_count = 0
    refresh_count = 0
    
    for second in range(10):
        for i in range(10):  # 每秒10次
            needs_refresh = app.update_ui()
            call_count += 1
            if needs_refresh:
                refresh_count += 1
            time.sleep(0.001)  # 小休眠以避免过度占用CPU
        print(f"    第{second+1}秒: {10}次调用，{sum(1 for _ in range(10) if app.update_ui())}次刷新")  # 简单显示
    
    end_time = time.time()
    
    print(f"  - 10秒内总共调用 {call_count} 次update_ui")
    print(f"  - 实际需要刷新 {refresh_count} 次")
    
    if refresh_count < call_count * 0.1:  # 如果实际刷新次数少于总调用的10%
        print("  ✅ 显著减少不必要的刷新")
        success = True
    else:
        print("  ❌ 仍有过多不必要的刷新")
        success = False
    
    return success


def main():
    """主函数"""
    print("🚀 测试TUI实际刷新行为")
    print("=" * 45)
    
    test1_success = test_actual_refresh_behavior()
    test2_success = test_refresh_rate_comparison()
    
    print("\n" + "=" * 45)
    print("📋 测试结果:")
    
    if test1_success and test2_success:
        print(" 🎉 所有测试通过！")
        print("  ✅ 内容无变化时无实际刷新")
        print("  ✅ 内容变化时能正确检测")
        print(" ✅ 显著减少不必要的刷新")
        print("\n🎯 修复效果总结:")
        print("  • TUI现在只在内容真正变化时才执行实际的UI刷新")
        print("  • 减少了CPU使用率和渲染开销")
        print("  • 保持了对内容变化的敏感性")
    else:
        print("  ❌ 部分测试失败")
        print(f"  • 内容无变化刷新测试: {'✅' if test1_success else '❌'}")
        print(f"  • 刷新率对比测试: {'✅' if test2_success else '❌'}")
    
    print("=" * 45)


if __name__ == "__main__":
    main()