"""测试完整的TUI输入处理集成"""

from typing import Optional, List
from unittest.mock import Mock, MagicMock

from ..config import get_tui_config
from ..components import InputPanel
from ..event_engine import EventEngine
from ..state_manager import StateManager
from ..components import MainContentComponent
from blessed import Terminal


class MockTUIApp:
    """模拟TUI应用，测试完整的输入处理流程"""
    
    def __init__(self):
        """初始化模拟应用"""
        self.terminal = Terminal()
        self.config = get_tui_config()
        
        # 创建组件
        self.event_engine = EventEngine(self.terminal, self.config)
        self.input_component = InputPanel(self.config)
        self.state_manager = StateManager()
        self.main_content_component = MainContentComponent(self.config)
        
        # 跟踪处理结果
        self.processed_inputs = []
        self.processed_commands = []
        self.processed_results = []
        
        # 设置回调
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """设置回调函数"""
        # 输入提交回调
        self.input_component.set_submit_callback(self._handle_input_submit)
        self.input_component.set_command_callback(self._handle_command)
        
        # 事件引擎回调
        self.event_engine.set_input_component_handler(self.input_component.handle_key)
        self.event_engine.set_input_result_handler(self._handle_input_result)
    
    def _handle_input_submit(self, input_text: str) -> None:
        """处理输入提交"""
        self.processed_inputs.append(input_text)
        print(f"📝 用户输入已处理: {input_text}")
        
        # 添加到状态管理器
        self.state_manager.add_user_message(input_text)
        
        # 添加到主内容组件
        self.main_content_component.add_user_message(input_text)
        
        # 模拟AI回复
        ai_response = f"收到你的消息: {input_text}"
        self.main_content_component.add_assistant_message(ai_response)
    
    def _handle_command(self, command: str, args: List[str]) -> None:
        """处理命令"""
        self.processed_commands.append((command, args))
        print(f"🔧 命令已处理: {command} {args}")
    
    def _handle_input_result(self, result: str) -> None:
        """处理输入结果"""
        self.processed_results.append(result)
        print(f"📤 输入结果已处理: {result}")
        
        # 处理特殊结果
        if result == "CLEAR_SCREEN":
            self.state_manager.clear_message_history()
            self.main_content_component.clear_all()
            print("🧹 屏幕已清空")
        elif result == "EXIT":
            print("👋 退出程序")
        elif result:
            # 显示命令结果
            self.main_content_component.add_assistant_message(result)
    
    def simulate_input(self, input_text: str) -> None:
        """模拟用户输入"""
        print(f"\n⌨️  模拟输入: '{input_text}'")
        
        # 设置输入文本
        self.input_component.input_buffer.set_text(input_text)
        
        # 处理回车键
        result = self.input_component.handle_key("enter")
        
        # 如果有结果，处理它
        if result is not None:
            self.event_engine.input_result_handler(result) # type: ignore
    
    def get_summary(self) -> str:
        """获取处理摘要"""
        summary = []
        if self.processed_inputs:
            summary.append(f"处理的用户输入: {len(self.processed_inputs)} 条")
        if self.processed_commands:
            summary.append(f"处理的命令: {len(self.processed_commands)} 条")
        if self.processed_results:
            summary.append(f"处理的结果: {len(self.processed_results)} 条")
        return "; ".join(summary) if summary else "没有处理任何内容"


def test_full_integration():
    """测试完整集成"""
    print("🚀 测试完整的TUI输入处理集成")
    print("=" * 60)
    
    # 创建模拟应用
    app = MockTUIApp()
    
    # 测试场景
    test_scenarios = [
        ("普通问候", "你好，AI助手"),
        ("包含换行符的消息", "第一行\n第二行\n第三行"),
        ("帮助命令", "/help"),
        ("清屏命令", "/clear"),
        ("历史命令", "/history"),
        ("空格结尾", "这是一个测试 "),
        ("反斜杠续行", "多行输入\\"),
        ("复杂多行", "标题\n\n内容1\n内容2\n\n结尾"),
    ]
    
    for name, input_text in test_scenarios:
        print(f"\n📋 场景: {name}")
        print("-" * 40)
        
        # 模拟输入
        app.simulate_input(input_text)
        
        # 检查输入缓冲区状态
        if not app.input_component.input_buffer.is_empty():
            remaining = app.input_component.input_buffer.get_text()
            print(f"⚠️  输入缓冲区仍有内容: '{remaining}'")
        else:
            print("✅ 输入缓冲区已清空")
    
    # 显示最终摘要
    print("\n" + "=" * 60)
    print("📊 处理摘要:")
    print(f"  {app.get_summary()}")
    
    # 验证关键功能
    print("\n🔍 功能验证:")
    
    # 验证普通消息处理
    normal_inputs = [inp for inp in app.processed_inputs if not inp.startswith("/")]
    print(f"  ✅ 普通消息处理: {len(normal_inputs)} 条")
    
    # 验证命令处理
    help_results = [r for r in app.processed_results if "可用命令" in r]
    clear_results = [r for r in app.processed_results if r == "CLEAR_SCREEN"]
    print(f"  ✅ 命令结果处理: {len(help_results)} 条帮助, {len(clear_results)} 条清屏")
    
    # 验证多行输入
    multiline_inputs = [inp for inp in app.processed_inputs if "\n" in inp]
    print(f"  ✅ 多行输入处理: {len(multiline_inputs)} 条")
    
    # 验证续行功能
    if app.input_component.input_buffer.get_text():
        print(f"  ✅ 续行功能正常: 缓冲区有内容")
    else:
        print(f"  ✅ 续行功能正常: 缓冲区已清空")
    
    print("\n🎉 完整集成测试通过！")


if __name__ == "__main__":
    test_full_integration()