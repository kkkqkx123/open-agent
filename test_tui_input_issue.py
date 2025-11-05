#!/usr/bin/env python3
"""
TUI输入功能测试脚本

用于诊断和验证TUI输入功能异常问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.presentation.tui.components.input_panel_component.input_buffer import InputBuffer
from src.presentation.tui.components.input_panel import InputPanel
from src.presentation.tui.key import Key, KeyType, KEY_ENTER
from src.presentation.tui.logger import get_tui_silent_logger

def test_input_buffer():
    """测试输入缓冲区的基本功能"""
    print("=== 测试输入缓冲区 ===")
    
    buffer = InputBuffer()
    logger = get_tui_silent_logger("test_input_buffer")
    
    # 测试1: 基本文本插入
    print("测试1: 基本文本插入")
    buffer.insert_text("hello")
    text = buffer.get_text()
    print(f"插入 'hello' 后，缓冲区内容: '{text}'")
    print(f"预期: 'hello', 实际: '{text}', 结果: {'✓' if text == 'hello' else '✗'}")
    
    # 测试2: 多字符输入
    print("\n测试2: 多字符输入")
    buffer.clear()
    buffer.insert_text("123")
    text = buffer.get_text()
    print(f"插入 '123' 后，缓冲区内容: '{text}'")
    print(f"预期: '123', 实际: '{text}', 结果: {'✓' if text == '123' else '✗'}")
    
    # 测试3: 检查光标位置
    print("\n测试3: 光标位置")
    buffer.clear()
    buffer.insert_text("test")
    print(f"插入 'test' 后，光标位置: {buffer.cursor_position}")
    print(f"预期: 4, 实际: {buffer.cursor_position}, 结果: {'✓' if buffer.cursor_position == 4 else '✗'}")
    
    return buffer

def test_input_panel():
    """测试输入面板的完整流程"""
    print("\n=== 测试输入面板 ===")
    
    panel = InputPanel()
    logger = get_tui_silent_logger("test_input_panel")
    
    # 测试1: 字符输入
    print("测试1: 字符输入处理")
    result1 = panel.handle_key(Key("1", KeyType.CHARACTER))
    print(f"输入 '1' 后的结果: {result1}")
    buffer_text = panel.input_buffer.get_text()
    print(f"缓冲区内容: '{buffer_text}'")
    print(f"结果: {'✓' if buffer_text == '1' else '✗'}")
    
    # 测试2: 多个字符输入
    print("\n测试2: 多个字符输入")
    result2 = panel.handle_key(Key("2", KeyType.CHARACTER))
    result3 = panel.handle_key(Key("3", KeyType.CHARACTER))
    buffer_text = panel.input_buffer.get_text()
    print(f"输入 '123' 后，缓冲区内容: '{buffer_text}'")
    print(f"结果: {'✓' if buffer_text == '123' else '✗'}")
    
    # 测试3: 回车键处理（这是问题的关键）
    print("\n测试3: 回车键处理")
    print("当前缓冲区内容:", buffer_text)
    
    # 模拟回车键处理
    enter_result = panel.handle_key(KEY_ENTER)
    print(f"回车处理结果: {enter_result}")
    print(f"回车后缓冲区内容: '{panel.input_buffer.get_text()}'")
    
    return panel

def test_edge_cases():
    """测试边界情况"""
    print("\n=== 测试边界情况 ===")
    
    panel = InputPanel()
    
    # 测试1: 空输入回车
    print("测试1: 空输入回车")
    panel.input_buffer.clear()
    result = panel.handle_key(KEY_ENTER)
    print(f"空输入回车结果: {result}")
    print(f"预期: None, 实际: {result}, 结果: {'✓' if result is None else '✗'}")
    
    # 测试2: 只有空格输入
    print("\n测试2: 只有空格输入")
    panel.input_buffer.clear()
    panel.input_buffer.insert_text("   ")
    result = panel.handle_key(KEY_ENTER)
    print(f"空格输入回车结果: {result}")
    print(f"预期: None, 实际: {result}, 结果: {'✓' if result is None else '✗'}")
    
    # 测试3: 输入后删除所有内容再回车
    print("\n测试3: 输入后删除所有内容")
    panel.input_buffer.clear()
    panel.input_buffer.insert_text("test")
    panel.input_buffer.delete_char(backward=True)  # 删除 't'
    panel.input_buffer.delete_char(backward=True)  # 删除 's'
    panel.input_buffer.delete_char(backward=True)  # 删除 'e'
    panel.input_buffer.delete_char(backward=True)  # 删除 't'
    result = panel.handle_key(KEY_ENTER)
    print(f"删除所有内容后回车结果: {result}")
    print(f"缓冲区最终内容: '{panel.input_buffer.get_text()}'")
    print(f"结果: {'✓' if result is None else '✗'}")

def main():
    """主测试函数"""
    print("TUI输入功能诊断测试")
    print("=" * 50)
    
    try:
        # 测试输入缓冲区
        buffer = test_input_buffer()
        
        # 测试输入面板
        panel = test_input_panel()
        
        # 测试边界情况
        test_edge_cases()
        
        print("\n=== 测试总结 ===")
        print("测试完成。请检查上面的输出以确定问题所在。")
        print("关键问题：回车时缓冲区内容是否被异常清空？")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()