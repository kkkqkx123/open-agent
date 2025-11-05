#!/usr/bin/env python3
"""
TUI输入功能综合测试脚本

用于全面验证TUI输入功能的修复效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.presentation.tui.components.input_panel import InputPanel
from src.presentation.tui.key import Key, KeyType, KEY_ENTER, KEY_BACKSPACE, KEY_LEFT, KEY_RIGHT
from src.presentation.tui.logger import get_tui_silent_logger

def test_comprehensive_input_scenarios():
    """测试综合输入场景"""
    print("=== 综合输入场景测试 ===")
    
    panel = InputPanel()
    
    # 场景1: 基本输入和提交
    print("场景1: 基本输入和提交")
    panel.input_buffer.clear()
    
    # 输入 "hello"
    for char in "hello":
        result = panel.handle_key(Key(char, KeyType.CHARACTER))
        print(f"输入 '{char}' 结果: {result}")
    
    buffer_text = panel.input_buffer.get_text()
    print(f"缓冲区内容: '{buffer_text}'")
    assert buffer_text == "hello", f"预期 'hello', 实际 '{buffer_text}'"
    
    # 提交
    submit_result = panel.handle_key(KEY_ENTER)
    print(f"提交结果: {submit_result}")
    assert submit_result == "USER_INPUT:hello", f"预期 'USER_INPUT:hello', 实际 '{submit_result}'"
    assert panel.input_buffer.get_text() == "", "提交后缓冲区应该为空"
    print("✓ 场景1 通过\n")
    
    # 场景2: 输入后退格和编辑
    print("场景2: 输入后退格和编辑")
    panel.input_buffer.clear()
    
    # 输入 "test"
    for char in "test":
        panel.handle_key(Key(char, KeyType.CHARACTER))
    
    # 退格两次（删除 "st"）
    panel.handle_key(KEY_BACKSPACE)
    panel.handle_key(KEY_BACKSPACE)
    
    buffer_text = panel.input_buffer.get_text()
    print(f"退格后缓冲区内容: '{buffer_text}'")
    assert buffer_text == "te", f"预期 'te', 实际 '{buffer_text}'"
    
    # 添加新字符
    panel.handle_key(Key("x", KeyType.CHARACTER))
    panel.handle_key(Key("y", KeyType.CHARACTER))
    
    buffer_text = panel.input_buffer.get_text()
    print(f"添加新字符后缓冲区内容: '{buffer_text}'")
    assert buffer_text == "texy", f"预期 'texy', 实际 '{buffer_text}'"
    print("✓ 场景2 通过\n")
    
    # 场景3: 光标移动和插入
    print("场景3: 光标移动和插入")
    panel.input_buffer.clear()
    
    # 输入 "abc"
    for char in "abc":
        panel.handle_key(Key(char, KeyType.CHARACTER))
    
    # 向左移动光标两次（到 'a' 后面）
    panel.handle_key(KEY_LEFT)
    panel.handle_key(KEY_LEFT)
    
    # 插入字符 'X'
    panel.handle_key(Key("X", KeyType.CHARACTER))
    
    buffer_text = panel.input_buffer.get_text()
    print(f"插入后缓冲区内容: '{buffer_text}'")
    assert buffer_text == "aXbc", f"预期 'aXbc', 实际 '{buffer_text}'"
    print("✓ 场景3 通过\n")
    
    # 场景4: 命令输入
    print("场景4: 命令输入")
    panel.input_buffer.clear()
    
    # 输入命令 "/help"
    for char in "/help":
        panel.handle_key(Key(char, KeyType.CHARACTER))
    
    buffer_text = panel.input_buffer.get_text()
    print(f"命令缓冲区内容: '{buffer_text}'")
    assert buffer_text == "/help", f"预期 '/help', 实际 '{buffer_text}'"
    
    # 提交命令
    submit_result = panel.handle_key(KEY_ENTER)
    print(f"命令提交结果: {submit_result}")
    # 命令应该返回None，因为SlashCommandProcessor需要实际配置
    print("✓ 场景4 通过\n")
    
    print("=== 所有综合场景测试通过！ ===")

def test_edge_cases():
    """测试边界情况"""
    print("=== 边界情况测试 ===")
    
    panel = InputPanel()
    
    # 情况1: 特殊字符
    print("情况1: 特殊字符")
    special_chars = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "-", "_", "=", "+", "[", "]", "{", "}", ";", ":", "'", "\"", ",", ".", "/", "?", "<", ">"]
    
    for char in special_chars:
        panel.input_buffer.clear()
        panel.handle_key(Key(char, KeyType.CHARACTER))
        buffer_text = panel.input_buffer.get_text()
        assert buffer_text == char, f"特殊字符 '{char}' 处理失败，缓冲区内容: '{buffer_text}'"
    
    print("✓ 所有特殊字符处理正确\n")
    
    # 情况2: 数字和字母混合
    print("情况2: 数字和字母混合")
    panel.input_buffer.clear()
    
    mixed_input = "a1b2c3D4E5"
    for char in mixed_input:
        panel.handle_key(Key(char, KeyType.CHARACTER))
    
    buffer_text = panel.input_buffer.get_text()
    print(f"混合输入缓冲区内容: '{buffer_text}'")
    assert buffer_text == mixed_input, f"预期 '{mixed_input}', 实际 '{buffer_text}'"
    print("✓ 数字和字母混合输入正确\n")
    
    # 情况3: 空格输入
    print("情况3: 空格输入")
    panel.input_buffer.clear()
    
    # 输入包含空格的文本
    text_with_spaces = "hello world"
    for char in text_with_spaces:
        panel.handle_key(Key(char, KeyType.CHARACTER))
    
    buffer_text = panel.input_buffer.get_text()
    print(f"含空格缓冲区内容: '{buffer_text}'")
    assert buffer_text == text_with_spaces, f"预期 '{text_with_spaces}', 实际 '{buffer_text}'"
    print("✓ 空格输入处理正确\n")
    
    print("=== 所有边界情况测试通过！ ===")

def test_performance():
    """测试性能 - 快速连续输入"""
    print("=== 性能测试 ===")
    
    panel = InputPanel()
    
    # 快速输入100个字符
    import time
    start_time = time.time()
    
    test_text = "a" * 100
    for char in test_text:
        panel.handle_key(Key(char, KeyType.CHARACTER))
    
    end_time = time.time()
    duration = end_time - start_time
    
    buffer_text = panel.input_buffer.get_text()
    print(f"快速输入100个字符耗时: {duration:.4f}秒")
    print(f"缓冲区内容长度: {len(buffer_text)}")
    assert len(buffer_text) == 100, f"预期长度100，实际长度{len(buffer_text)}"
    assert buffer_text == test_text, "缓冲区内容应该与输入一致"
    
    print(f"✓ 性能测试通过 - 每秒处理 {100/duration:.1f} 个字符")

def main():
    """主测试函数"""
    print("TUI输入功能综合测试")
    print("=" * 60)
    
    try:
        # 运行综合场景测试
        test_comprehensive_input_scenarios()
        
        # 运行边界情况测试
        test_edge_cases()
        
        # 运行性能测试
        test_performance()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！TUI输入功能修复成功！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)