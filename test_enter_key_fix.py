#!/usr/bin/env python3
"""测试Enter键提交消息的修复"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.presentation.tui.components.input_panel import InputPanel
from src.presentation.tui.config import get_tui_config


def test_enter_key_submission():
    """测试Enter键提交消息功能"""
    print("测试Enter键提交消息功能...")
    
    # 创建输入面板
    config = get_tui_config()
    input_panel = InputPanel(config)
    
    # 设置回调函数来捕获提交
    submitted_messages = []
    
    def on_submit(text):
        submitted_messages.append(text)
        print(f"消息已提交: {text}")
    
    input_panel.set_submit_callback(on_submit)
    
    # 测试1: 普通消息提交
    print("\n测试1: 普通消息提交")
    input_panel.input_buffer.set_text("Hello, world!")
    result = input_panel.handle_key("enter")
    
    # 检查结果
    assert result == "USER_INPUT:Hello, world!", f"期望返回'USER_INPUT:Hello, world!'，实际返回'{result}'"
    assert len(submitted_messages) == 1, f"期望提交1条消息，实际提交{len(submitted_messages)}条"
    assert submitted_messages[0] == "Hello, world!", f"期望提交'Hello, world!'，实际提交'{submitted_messages[0]}'"
    print("✓ 普通消息提交测试通过")
    
    # 测试2: 以反斜杠结尾的多行输入
    print("\n测试2: 以反斜杠结尾的多行输入")
    input_panel.input_buffer.set_text("Hello\\")
    result = input_panel.handle_key("enter")
    
    # 检查结果
    assert result is None, f"期望返回None，实际返回'{result}'"
    assert len(submitted_messages) == 1, f"期望仍为1条消息，实际为{len(submitted_messages)}条"
    assert input_panel.input_buffer.get_text() == "Hello\n", f"期望缓冲区内容为'Hello\\n'，实际为'{input_panel.input_buffer.get_text()}'"
    print("✓ 多行输入测试通过")
    
    # 测试3: 命令处理
    print("\n测试3: 命令处理")
    command_results = []
    
    def on_command(command, args):
        command_results.append((command, args))
        print(f"命令已处理: {command} {args}")
    
    input_panel.set_command_callback(on_command)
    input_panel.input_buffer.set_text("/help")
    result = input_panel.handle_key("enter")
    
    # 检查结果
    assert result is not None, "期望命令处理返回非None结果"
    print("✓ 命令处理测试通过")
    
    # 测试4: 空输入不提交
    print("\n测试4: 空输入不提交")
    input_panel.input_buffer.set_text("")
    result = input_panel.handle_key("enter")
    
    # 检查结果
    assert result is None, f"期望空输入返回None，实际返回'{result}'"
    assert len(submitted_messages) == 1, f"期望仍为1条消息，实际为{len(submitted_messages)}条"
    print("✓ 空输入测试通过")
    
    print("\n所有测试通过！Enter键提交消息功能已修复。")


if __name__ == "__main__":
    test_enter_key_submission()