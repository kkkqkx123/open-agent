#!/usr/bin/env python3
"""测试TUI修复后的重复渲染问题"""

import asyncio
import time
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.presentation.tui.app import TUIApp


def test_tui_performance():
    """测试TUI性能"""
    print("正在启动TUI应用测试...")
    print("请在3秒内观察界面渲染情况...")
    
    start_time = time.time()
    
    try:
        # 创建TUI应用实例
        app = TUIApp()
        
        # 在后台运行应用3秒然后退出
        import threading
        def run_app():
            app.run()
        
        def stop_after_timeout():
            time.sleep(3)
            app.running = False
            print("\n[INFO] 3秒超时，停止应用")
            
            # 获取渲染统计信息
            try:
                render_stats = app.render_controller.get_render_stats()
                print(f"[STATS] 总更新次数: {render_stats['total_updates']}")
                print(f"[STATS] 跳过更新次数: {render_stats['skipped_updates']}")
                print(f"[STATS] 平均更新间隔: {render_stats['avg_update_interval']:.3f}秒")
                
                total_operations = render_stats['total_updates'] + render_stats['skipped_updates']
                if total_operations > 0:
                    efficiency = render_stats['skipped_updates'] / total_operations * 100
                    print(f"[STATS] 渲染效率: 跳过{efficiency:.1f}%的无用更新")
            except Exception as stats_error:
                print(f"[ERROR] 获取统计信息失败: {stats_error}")
        
        app_thread = threading.Thread(target=run_app, daemon=True)
        timeout_thread = threading.Thread(target=stop_after_timeout, daemon=True)
        
        app_thread.start()
        timeout_thread.start()
        
        # 等待应用线程结束
        app_thread.join(timeout=5)  # 等待最多5秒
        
        end_time = time.time()
        print(f"[INFO] 应用运行时间: {end_time - start_time:.2f}秒")
        
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置环境变量以启用TUI调试
    os.environ["TUI_DEBUG"] = "1"
    
    test_tui_performance()