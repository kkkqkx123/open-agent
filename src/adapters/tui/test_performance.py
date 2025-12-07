"""TUI性能测试脚本"""

import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from .app import TUIApp
from .config import get_tui_config


def test_render_performance():
    """测试渲染性能"""
    print("开始渲染性能测试...")
    
    # 创建TUI应用实例
    config = get_tui_config()
    app = TUIApp()
    
    # 测试渲染控制器的性能
    start_time = time.time()
    
    # 模拟多次UI更新
    for i in range(100):
        # 更新状态管理器
        app.state_manager.message_history.append({
            "type": "user",
            "content": f"测试消息 {i}"
        })
        
        # 更新UI
        app.update_ui()
        
        # 每10次更新打印一次进度
        if (i + 1) % 10 == 0:
            print(f"已完成 {i + 1}/100 次更新")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"渲染性能测试完成:")
    print(f"  总时间: {total_time:.2f} 秒")
    print(f"  平均每次更新: {total_time/100*1000:.2f} 毫秒")
    print(f"  更新频率: {100/total_time:.2f} 次/秒")


def test_memory_usage():
    """测试内存使用"""
    print("\n开始内存使用测试...")
    
    import psutil
    import os
    
    # 获取当前进程
    process = psutil.Process(os.getpid())
    
    # 初始内存使用
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"初始内存使用: {initial_memory:.2f} MB")
    
    # 创建TUI应用实例
    app = TUIApp()
    
    # 加载多个子界面
    subviews = ["analytics", "visualization", "system", "errors", "status_overview", "workflow"]
    
    for subview in subviews:
        app._switch_to_subview(subview)
        app.update_ui()
    
    # 最终内存使用
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"加载子界面后内存使用: {final_memory:.2f} MB")
    print(f"内存增长: {final_memory - initial_memory:.2f} MB")


def test_response_time():
    """测试响应时间"""
    print("\n开始响应时间测试...")
    
    # 创建TUI应用实例
    app = TUIApp()
    
    # 测试子界面切换响应时间
    subviews = ["analytics", "visualization", "system", "errors", "status_overview", "workflow"]
    
    total_switch_time = 0
    total_update_time = 0
    
    for subview in subviews:
        # 测试切换时间
        start_time = time.time()
        app._switch_to_subview(subview)
        switch_time = time.time() - start_time
        total_switch_time += switch_time
        
        # 测试更新时间
        start_time = time.time()
        app.update_ui()
        update_time = time.time() - start_time
        total_update_time += update_time
        
        print(f"  {subview}: 切换 {switch_time*1000:.2f}ms, 更新 {update_time*1000:.2f}ms")
    
    avg_switch_time = total_switch_time / len(subviews) * 1000  # 转换为毫秒
    avg_update_time = total_update_time / len(subviews) * 1000  # 转换为毫秒
    
    print(f"平均切换时间: {avg_switch_time:.2f} 毫秒")
    print(f"平均更新时间: {avg_update_time:.2f} 毫秒")


if __name__ == "__main__":
    print("TUI性能测试")
    print("=" * 50)
    
    try:
        test_render_performance()
        test_memory_usage()
        test_response_time()
        
        print("\n所有性能测试完成!")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()