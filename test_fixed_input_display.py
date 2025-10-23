#!/usr/bin/env python3
"""测试修复后的TUI输入显示功能"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from presentation.tui.app import TUIApp

def test_fixed_input_display():
    """测试修复后的输入显示功能"""
    print("=== 测试修复后的输入显示功能 ===")
    
    try:
        # 创建TUI应用
        app = TUIApp()
        
        # 模拟输入处理
        print("1. 模拟用户输入 'test message'")
        app.input_component.handle_key("char:t")
        app.input_component.handle_key("char:e")
        app.input_component.handle_key("char:s")
        app.input_component.handle_key("char:t")
        app.input_component.handle_key("char: ")
        app.input_component.handle_key("char:m")
        app.input_component.handle_key("char:e")
        app.input_component.handle_key("char:s")
        app.input_component.handle_key("char:s")
        app.input_component.handle_key("char:a")
        app.input_component.handle_key("char:g")
        app.input_component.handle_key("char:e")
        
        # 提交输入
        print("2. 提交输入")
        result = app.input_component.handle_key("enter")
        print(f"   输入结果: {result}")
        
        # 处理输入结果
        if result and result.startswith("USER_INPUT:"):
            user_text = result.split(":", 1)[1]
            print(f"   用户输入: {user_text}")
            
            # 检查状态管理器
            print("3. 检查状态管理器")
            print(f"   消息历史数量: {len(app.state_manager.message_history)}")
            for i, msg in enumerate(app.state_manager.message_history):
                print(f"   消息 {i+1}: {msg['type']} - {msg['content']}")
            
            # 检查主内容组件
            print("4. 检查主内容组件")
            history = app.main_content_component.conversation_history
            print(f"   会话历史数量: {len(history.messages)}")
            for i, msg in enumerate(history.messages):
                print(f"   消息 {i+1}: {msg['type']} - {msg['content'][:30]}...")
            
            # 测试UI更新
            print("5. 测试UI更新")
            needs_refresh = app.update_ui()
            print(f"   需要刷新: {needs_refresh}")
            
            # 渲染组件
            print("6. 渲染组件")
            main_panel = app.main_content_component.render()
            input_panel = app.input_component.render()
            print(f"   主内容面板类型: {type(main_panel)}")
            print(f"   输入面板类型: {type(input_panel)}")
            
            print("\n=== 测试完成 ===")
            print("如果以上测试都正常，说明修复成功！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_input_display()
