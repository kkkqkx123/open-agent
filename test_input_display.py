#!/usr/bin/env python3
"""测试TUI输入显示问题的脚本"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from presentation.tui.app import TUIApp
from presentation.tui.components.input_panel import InputPanel
from presentation.tui.components.main_content import MainContentComponent
from presentation.tui.state_manager import StateManager

def test_input_panel():
    """测试输入面板组件"""
    print("=== 测试输入面板组件 ===")
    
    # 创建输入面板
    input_panel = InputPanel()
    
    # 模拟输入处理
    print("1. 测试字符输入")
    result = input_panel.handle_key("char:H")
    print(f"   输入 'H' 结果: {result}")
    
    result = input_panel.handle_key("char:e")
    print(f"   输入 'e' 结果: {result}")
    
    result = input_panel.handle_key("char:l")
    print(f"   输入 'l' 结果: {result}")
    
    result = input_panel.handle_key("char:l")
    print(f"   输入 'l' 结果: {result}")
    
    result = input_panel.handle_key("char:o")
    print(f"   输入 'o' 结果: {result}")
    
    print("\n2. 测试回车提交")
    result = input_panel.handle_key("enter")
    print(f"   回车结果: {result}")
    
    print("\n3. 检查输入缓冲区状态")
    print(f"   输入缓冲区文本: '{input_panel.input_buffer.get_text()}'")
    print(f"   输入缓冲区是否为空: {input_panel.input_buffer.is_empty()}")
    
    print("\n4. 渲染输入面板")
    panel = input_panel.render()
    print(f"   渲染结果类型: {type(panel)}")

def test_main_content():
    """测试主内容组件"""
    print("\n=== 测试主内容组件 ===")
    
    # 创建主内容组件
    main_content = MainContentComponent()
    
    # 添加用户消息
    print("1. 添加用户消息")
    main_content.add_user_message("Hello, World!")
    
    # 添加助手消息
    print("2. 添加助手消息")
    main_content.add_assistant_message("你好！我是AI助手。")
    
    # 渲染主内容
    print("3. 渲染主内容")
    panel = main_content.render()
    print(f"   渲染结果类型: {type(panel)}")
    
    # 检查会话历史
    print("4. 检查会话历史")
    history = main_content.conversation_history
    print(f"   消息数量: {len(history.messages)}")
    for i, msg in enumerate(history.messages):
        print(f"   消息 {i+1}: {msg['type']} - {msg['content'][:30]}...")

def test_state_manager():
    """测试状态管理器"""
    print("\n=== 测试状态管理器 ===")
    
    # 创建状态管理器
    state_manager = StateManager()
    
    # 添加用户消息
    print("1. 添加用户消息到状态管理器")
    state_manager.add_user_message("测试消息")
    
    # 检查消息历史
    print("2. 检查消息历史")
    print(f"   消息历史数量: {len(state_manager.message_history)}")
    for i, msg in enumerate(state_manager.message_history):
        print(f"   消息 {i+1}: {msg['type']} - {msg['content']}")

def test_input_flow():
    """测试完整的输入流程"""
    print("\n=== 测试完整输入流程 ===")
    
    # 创建组件
    input_panel = InputPanel()
    main_content = MainContentComponent()
    state_manager = StateManager()
    
    # 设置回调
    def on_submit(text):
        print(f"   提交回调被调用: {text}")
        state_manager.add_user_message(text)
        main_content.add_user_message(text)
        
        # 模拟助手回复
        reply = f"收到您的输入: {text}"
        state_manager.add_assistant_message(reply)
        main_content.add_assistant_message(reply)
    
    input_panel.set_submit_callback(on_submit)
    
    # 模拟输入
    print("1. 模拟用户输入 'test'")
    input_panel.handle_key("char:t")
    input_panel.handle_key("char:e")
    input_panel.handle_key("char:s")
    input_panel.handle_key("char:t")
    
    print("2. 提交输入")
    result = input_panel.handle_key("enter")
    print(f"   提交结果: {result}")
    
    # 检查状态
    print("3. 检查状态")
    print(f"   状态管理器消息数: {len(state_manager.message_history)}")
    print(f"   主内容组件消息数: {len(main_content.conversation_history.messages)}")
    
    # 检查渲染
    print("4. 检查渲染")
    input_panel_render = input_panel.render()
    main_content_render = main_content.render()
    print(f"   输入面板渲染类型: {type(input_panel_render)}")
    print(f"   主内容渲染类型: {type(main_content_render)}")

if __name__ == "__main__":
    print("开始测试TUI输入显示问题...")
    
    try:
        test_input_panel()
        test_main_content()
        test_state_manager()
        test_input_flow()
        
        print("\n=== 测试完成 ===")
        print("如果以上测试都正常，问题可能在于:")
        print("1. 渲染控制器没有正确更新UI")
        print("2. 布局管理器没有正确显示组件")
        print("3. 事件循环中的刷新逻辑有问题")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()