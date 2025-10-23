#!/usr/bin/env python3
"""测试修复后的实时输入显示功能"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from presentation.tui.app import TUIApp

def test_realtime_input_display():
    """测试实时输入显示功能"""
    print("=== 测试实时输入显示功能 ===")
    
    try:
        # 创建TUI应用
        app = TUIApp()
        
        # 测试输入过程中的状态变化检测
        print("1. 测试输入过程中的状态变化检测")
        
        # 模拟输入字符
        print("   输入字符 'H'")
        result = app.input_component.handle_key("char:H")
        print(f"   处理结果: {result}")
        
        # 检查状态哈希是否变化
        old_hash = app.render_controller._get_state_hash(app.state_manager)
        print(f"   当前状态哈希: {old_hash[:8]}")
        
        print("   输入字符 'e'")
        result = app.input_component.handle_key("char:e")
        print(f"   处理结果: {result}")
        
        new_hash = app.render_controller._get_state_hash(app.state_manager)
        print(f"   新状态哈希: {new_hash[:8]}")
        
        if old_hash != new_hash:
            print("   ✓ 状态哈希已变化，UI会刷新")
        else:
            print("   ✗ 状态哈希未变化，UI不会刷新")
        
        # 测试UI更新
        print("\n2. 测试UI更新")
        needs_refresh = app.update_ui()
        print(f"   需要刷新: {needs_refresh}")
        
        # 测试输入缓冲区内容
        print("\n3. 测试输入缓冲区内容")
        input_text = app.input_component.input_buffer.get_text()
        print(f"   输入缓冲区内容: '{input_text}'")
        
        # 渲染输入面板
        print("\n4. 渲染输入面板")
        input_panel = app.input_component.render()
        print(f"   输入面板类型: {type(input_panel)}")
        
        print("\n=== 测试完成 ===")
        print("如果状态哈希变化且UI需要刷新，说明修复成功！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_realtime_input_display()
