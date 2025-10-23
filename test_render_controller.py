#!/usr/bin/env python3
"""测试TUI渲染控制器和布局管理器的脚本"""

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
from presentation.tui.render_controller import RenderController
from presentation.tui.layout import LayoutManager
from presentation.tui.config import get_tui_config

def test_render_controller():
    """测试渲染控制器"""
    print("=== 测试渲染控制器 ===")
    
    try:
        # 获取配置
        config = get_tui_config()
        
        # 创建布局管理器
        layout_manager = LayoutManager(config.layout)
        
        # 创建组件
        components = {
            "sidebar": None,
            "langgraph": None,
            "main_content": MainContentComponent(config),
            "input": InputPanel(config),
            "workflow_control": None,
            "error_feedback": None,
            "session_dialog": None,
            "agent_dialog": None
        }
        
        # 创建子界面
        subviews = {}
        
        # 创建渲染控制器
        render_controller = RenderController(layout_manager, components, subviews, config)
        
        # 创建状态管理器
        state_manager = StateManager()
        
        print("1. 初始状态渲染")
        needs_refresh = render_controller.update_ui(state_manager)
        print(f"   需要刷新: {needs_refresh}")
        
        print("\n2. 添加用户输入")
        # 模拟用户输入
        input_panel = components["input"]
        input_panel.handle_key("char:H")
        input_panel.handle_key("char:e")
        input_panel.handle_key("char:l")
        input_panel.handle_key("char:l")
        input_panel.handle_key("char:o")
        
        # 提交输入
        result = input_panel.handle_key("enter")
        print(f"   输入结果: {result}")
        
        # 处理输入结果
        if result and result.startswith("USER_INPUT:"):
            user_text = result.split(":", 1)[1]
            state_manager.add_user_message(user_text)
            components["main_content"].add_user_message(user_text)
            
            # 添加助手回复
            reply = f"收到您的输入: {user_text}"
            state_manager.add_assistant_message(reply)
            components["main_content"].add_assistant_message(reply)
        
        print("\n3. 更新UI后的状态")
        needs_refresh = render_controller.update_ui(state_manager)
        print(f"   需要刷新: {needs_refresh}")
        
        print("\n4. 检查状态管理器")
        print(f"   消息历史数量: {len(state_manager.message_history)}")
        for i, msg in enumerate(state_manager.message_history):
            print(f"   消息 {i+1}: {msg['type']} - {msg['content']}")
        
        print("\n5. 检查主内容组件")
        main_content = components["main_content"]
        print(f"   会话历史数量: {len(main_content.conversation_history.messages)}")
        for i, msg in enumerate(main_content.conversation_history.messages):
            print(f"   消息 {i+1}: {msg['type']} - {msg['content'][:30]}...")
        
        print("\n6. 检查输入面板")
        input_panel = components["input"]
        print(f"   输入缓冲区文本: '{input_panel.input_buffer.get_text()}'")
        print(f"   输入缓冲区是否为空: {input_panel.input_buffer.is_empty()}")
        
        # 渲染各个组件
        print("\n7. 渲染组件")
        main_panel = main_content.render()
        input_panel_render = input_panel.render()
        print(f"   主内容面板类型: {type(main_panel)}")
        print(f"   输入面板类型: {type(input_panel_render)}")
        
        # 检查布局内容
        print("\n8. 检查布局内容")
        layout = layout_manager.create_layout((80, 24))
        print(f"   布局类型: {type(layout)}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def test_layout_manager():
    """测试布局管理器"""
    print("\n=== 测试布局管理器 ===")
    
    try:
        # 获取配置
        config = get_tui_config()
        
        # 创建布局管理器
        layout_manager = LayoutManager(config.layout)
        
        # 创建布局
        layout = layout_manager.create_layout((80, 24))
        print(f"1. 布局类型: {type(layout)}")
        
        # 更新区域内容
        from presentation.tui.layout import LayoutRegion
        from rich.panel import Panel
        from rich.text import Text
        
        print("\n2. 更新区域内容")
        
        # 更新主内容区
        main_content = Panel(Text("这是主内容区"), title="主内容")
        layout_manager.update_region_content(LayoutRegion.MAIN, main_content)
        print("   已更新主内容区")
        
        # 更新输入区
        input_content = Panel(Text("这是输入区"), title="输入")
        layout_manager.update_region_content(LayoutRegion.INPUT, input_content)
        print("   已更新输入区")
        
        # 获取更新后的布局
        updated_layout = layout_manager.layout
        print(f"3. 更新后布局类型: {type(updated_layout)}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试TUI渲染控制器和布局管理器...")
    
    try:
        test_render_controller()
        test_layout_manager()
        
        print("\n=== 测试完成 ===")
        print("如果以上测试都正常，问题可能在于:")
        print("1. Live对象没有正确刷新")
        print("2. 事件循环中的刷新频率过低")
        print("3. 组件内容变化检测逻辑有问题")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()