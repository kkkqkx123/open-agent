"""HumanRelay专用TUI面板"""

import asyncio
from typing import Dict, Any, Optional, List
from blessed import Terminal

from ..logger import get_tui_logger


class HumanRelayPanel:
    """HumanRelay专用TUI面板"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化HumanRelay面板
        
        Args:
            config: TUI配置
        """
        self.config = config
        self.term = Terminal()
        self.logger = get_tui_logger("human_relay")
        self.prompt_style = config.get('prompt_style', 'highlight')
        self.input_area_height = config.get('input_area_height', 10)
        self.show_timer = config.get('show_timer', True)
        
    async def show_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """
        显示提示词并等待用户输入
        
        Args:
            prompt: 提示词内容
            mode: 模式（single 或 multi）
            **kwargs: 其他参数
            
        Returns:
            str: 用户输入的Web LLM回复
        """
        # 清屏并显示标题
        print(self.term.clear())
        self._print_header(mode)
        
        # 显示提示词
        self._print_prompt(prompt, mode)
        
        # 显示对话历史（多轮模式）
        if mode == "multi" and "conversation_history" in kwargs:
            self._print_conversation_history(kwargs["conversation_history"])
        
        # 显示输入区域
        user_input = await self._get_user_input(**kwargs)
        
        return user_input
    
    def _print_header(self, mode: str) -> None:
        """打印标题"""
        mode_text = "单轮对话" if mode == "single" else "多轮对话"
        title = f"HumanRelay {mode_text} 模式"
        
        # 居中显示标题
        width = self.term.width
        padding = (width - len(title)) // 2
        
        print(self.term.bold(self.term.cyan(title.center(width))))
        print(self.term.bold("─" * width))
        print()
    
    def _print_prompt(self, prompt: str, mode: str) -> None:
        """打印提示词"""
        if self.prompt_style == "highlight":
            print(self.term.bold("🎯 提示词内容："))
            print(self.term.yellow("─" * 50))
            print(self.term.white(prompt))
            print(self.term.yellow("─" * 50))
        else:
            print("提示词内容：")
            print("-" * 30)
            print(prompt)
            print("-" * 30)
        
        print()
    
    def _print_conversation_history(self, history: Any) -> None:
        """打印对话历史"""
        print(self.term.bold("📋 对话历史："))
        print(self.term.blue("─" * 30))
        
        if hasattr(history, '__iter__') and not isinstance(history, str):
            for i, message in enumerate(history, 1):
                if hasattr(message, 'type') and hasattr(message, 'content'):
                    role = "用户" if message.type == "human" else "AI"
                    content = str(message.content)
                    print(f"{i}. {self.term.green(role)}: {content}")
                else:
                    print(f"{i}. {message}")
        else:
            print(str(history))
        
        print(self.term.blue("─" * 30))
        print()
    
    async def _get_user_input(self, **kwargs) -> str:
        """获取用户输入"""
        timeout = kwargs.get('timeout', 300)
        
        print(self.term.bold("📝 请将Web LLM的回复粘贴到下方："))
        print(self.term.cyan("─" * 50))
        
        # 创建输入区域
        input_lines = []
        current_line = ""
        
        # 显示输入提示
        print(self.term.green("> "), end="", flush=True)
        
        # 异步读取输入
        try:
            while True:
                # 非阻塞读取键盘输入
                with self.term.cbreak():
                    key = self.term.inkey(timeout=0.1)
                
                if key:
                    if key.name == "ENTER":
                        if current_line.strip():
                            input_lines.append(current_line)
                            current_line = ""
                        else:
                            # 空行表示输入结束
                            break
                    elif key.name == "BACKSPACE":
                        if current_line:
                            current_line = current_line[:-1]
                            # 退格并清除字符
                            print("\b \b", end="", flush=True)
                    elif key.name == "CTRL_C":
                        print("\n操作已取消")
                        return ""
                    else:
                        current_line += key
                        print(key, end="", flush=True)
                
                # 检查超时
                if self.show_timer and timeout > 0:
                    # 这里可以添加倒计时显示
                    pass
                
                await asyncio.sleep(0.01)  # 避免CPU占用过高
        
        except KeyboardInterrupt:
            print("\n操作已取消")
            return ""
        
        # 组合输入内容
        user_input = "\n".join(input_lines)
        
        print(self.term.cyan("─" * 50))
        print()
        
        # 确认输入
        if user_input.strip():
            print(self.term.green("✓ 已收到回复"))
            return user_input
        else:
            print(self.term.red("✗ 输入为空，请重试"))
            return await self._get_user_input(**kwargs)
    
    def show_error(self, error_message: str) -> None:
        """显示错误信息"""
        print(self.term.red(f"❌ 错误: {error_message}"))
    
    def show_success(self, message: str) -> None:
        """显示成功信息"""
        print(self.term.green(f"✅ {message}"))
    
    def show_info(self, message: str) -> None:
        """显示信息"""
        print(self.term.blue(f"ℹ️  {message}"))


class MockHumanRelayPanel(HumanRelayPanel):
    """Mock HumanRelay面板，用于测试"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.mock_response = config.get('mock_response', "Mock Web LLM回复")
        self.mock_delay = config.get('mock_delay', 0.1)
    
    async def show_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """Mock显示提示词"""
        print(f"[Mock] HumanRelay {mode} 模式")
        print(f"[Mock] 提示词: {prompt[:50]}...")
        
        # 模拟延迟
        if self.mock_delay > 0:
            await asyncio.sleep(self.mock_delay)
        
        print(f"[Mock] 返回回复: {self.mock_response}")
        return self.mock_response


def create_human_relay_panel(config: Dict[str, Any]) -> HumanRelayPanel:
    """
    创建HumanRelay面板实例
    
    Args:
        config: 面板配置
        
    Returns:
        HumanRelayPanel: 面板实例
    """
    if config.get('mock_mode', False):
        return MockHumanRelayPanel(config)
    else:
        return HumanRelayPanel(config)