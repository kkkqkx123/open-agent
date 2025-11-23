"""测试完整的输入回调链路"""

from typing import Optional, List
from unittest.mock import Mock

from ..config import get_tui_config
from ..components import InputPanel
from ..event_engine import EventEngine
from blessed import Terminal


def test_complete_callback_chain():
    """测试完整的回调链路"""
    print("🔍 测试完整的输入回调链路")
    
    # 创建组件
    terminal = Terminal()
    config = get_tui_config()
    event_engine = EventEngine(terminal, config)
    input_panel = InputPanel(config)
    
    # 跟踪回调调用
    submit_calls = []
    command_calls = []
    result_calls = []
    
    def submit_callback(text: str) -> None:
        """提交回调"""
        submit_calls.append(text)
        print(f"✅ 提交回调被调用: {text}")
    
    def command_callback(cmd: str, args: List[str]) -> None:
        """命令回调"""
        command_calls.append((cmd, args))
        print(f"🔧 命令回调被调用: {cmd} {args}")
    
    def result_callback(result: str) -> None:
        """结果回调"""
        result_calls.append(result)
        print(f"📤 结果回调被调用: {result}")
    
    # 设置回调
    input_panel.set_submit_callback(submit_callback)
    input_panel.set_command_callback(command_callback)
    
    # 设置事件引擎处理器
    event_engine.set_input_component_handler(input_panel.handle_key)
    event_engine.set_input_result_handler(result_callback)
    
    # 测试场景
    test_cases = [
        ("普通消息", "hello world"),
        ("命令", "/help"),
        ("多行消息", "line1\nline2"),
        ("空格结尾", "hello "),
        ("反斜杠续行", "line1\\"),
    ]
    
    for name, input_text in test_cases:
        print(f"\n📝 测试 {name}: '{input_text}'")
        
        # 重置跟踪
        submit_calls.clear()
        command_calls.clear()
        result_calls.clear()
        
        # 设置输入
        input_panel.input_buffer.set_text(input_text)
        
        # 模拟事件引擎处理
        result = input_panel.handle_key("enter")
        
        # 如果有结果，调用结果处理器
        if result is not None:
            event_engine.input_result_handler(result) # type: ignore
        
        # 验证回调调用
        print(f"  提交回调: {len(submit_calls)} 次")
        print(f"  命令回调: {len(command_calls)} 次") 
        print(f"  结果回调: {len(result_calls)} 次")
        
        # 分析结果
        if input_text.startswith("/"):
            # 命令应该通过结果回调处理
            assert len(result_calls) > 0, f"命令 {input_text} 应该触发结果回调"
            assert len(submit_calls) == 0, f"命令 {input_text} 不应该触发提交回调"
        elif input_text.endswith("\\"):
            # 反斜杠续行不应该触发任何回调
            assert len(submit_calls) == 0, f"续行输入 {input_text} 不应该触发提交回调"
            assert len(result_calls) == 0, f"续行输入 {input_text} 不应该触发结果回调"
        else:
            # 普通消息应该通过提交回调处理
            assert len(submit_calls) > 0, f"普通消息 {input_text} 应该触发提交回调"
            assert len(result_calls) == 0, f"普通消息 {input_text} 不应该触发结果回调"
    
    print("\n✅ 所有回调链路测试通过！")


if __name__ == "__main__":
    test_complete_callback_chain()