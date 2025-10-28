"""前端交互接口实现"""

import asyncio
from typing import Dict, Any, Optional, List
from langchain_core.messages import BaseMessage

from .exceptions import LLMTimeoutError, LLMInvalidRequestError


class FrontendInterface:
    """前端交互抽象接口"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化前端接口
        
        Args:
            config: 前端配置
        """
        self.config = config
        self.interface_type = config.get('interface_type', 'tui')  # tui 或 web
        
        if self.interface_type not in ['tui', 'web', 'mock']:
            raise ValueError(f"不支持的前端接口类型: {self.interface_type}")
    
    async def prompt_user(self, prompt: str, mode: str, **kwargs) -> str:
        """
        显示提示词并等待用户输入
        
        Args:
            prompt: 提示词内容
            mode: 模式（single 或 multi）
            **kwargs: 其他参数
            
        Returns:
            str: 用户输入的Web LLM回复
        """
        if self.interface_type == 'tui':
            return await self._tui_prompt(prompt, mode, **kwargs)
        else:
            return await self._web_prompt(prompt, mode, **kwargs)
    
    async def _tui_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """TUI前端交互实现"""
        try:
            from src.presentation.tui.components.human_relay_panel import HumanRelayPanel
            
            panel = HumanRelayPanel(self.config.get('tui_config', {}))
            return await panel.show_prompt(prompt, mode, **kwargs)
        except ImportError as e:
            raise LLMInvalidRequestError(f"TUI组件不可用: {e}")
    
    async def _web_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """Web前端交互实现"""
        # 通过WebSocket或HTTP与前端通信
        # 这里需要与前端框架集成
        raise NotImplementedError("Web前端交互暂未实现")
    
    def format_conversation_history(self, history: List[BaseMessage]) -> str:
        """
        格式化对话历史
        
        Args:
            history: 对话历史消息列表
            
        Returns:
            str: 格式化后的对话历史
        """
        if not history:
            return "（无对话历史）"
        
        formatted_lines = []
        for i, message in enumerate(history, 1):
            role = "用户" if message.type == "human" else "AI"
            content = str(message.content)
            formatted_lines.append(f"{i}. {role}: {content}")
        
        return "\n".join(formatted_lines)
    
    def validate_timeout(self, timeout: Optional[int]) -> int:
        """
        验证并返回超时时间
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            int: 验证后的超时时间
        """
        if timeout is None:
            return self.config.get('default_timeout', 300)
        
        if timeout <= 0:
            raise ValueError("超时时间必须大于0")
        
        return timeout
    
    async def wait_with_timeout(self, coro, timeout: int) -> Any:
        """
        等待协程完成，支持超时
        
        Args:
            coro: 要等待的协程
            timeout: 超时时间（秒）
            
        Returns:
            Any: 协程结果
            
        Raises:
            LLMTimeoutError: 超时异常
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"前端交互超时（{timeout}秒）", timeout=timeout)


class MockFrontendInterface(FrontendInterface):
    """Mock前端接口，用于测试"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.mock_response = config.get('mock_response', "Mock Web LLM回复")
        self.mock_delay = config.get('mock_delay', 0.1)
    
    async def _tui_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """Mock TUI交互"""
        # 模拟延迟
        if self.mock_delay > 0:
            await asyncio.sleep(self.mock_delay)
        
        # 模拟超时
        timeout = kwargs.get('timeout', 300)
        if timeout < self.mock_delay:
            raise LLMTimeoutError(f"Mock超时（{timeout}秒）", timeout=timeout)
        
        return self.mock_response
    
    async def _web_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """Mock Web交互"""
        return await self._tui_prompt(prompt, mode, **kwargs)


def create_frontend_interface(config: Dict[str, Any]) -> FrontendInterface:
    """
    创建前端接口实例
    
    Args:
        config: 前端配置
        
    Returns:
        FrontendInterface: 前端接口实例
    """
    interface_type = config.get('interface_type', 'tui')
    
    if interface_type == 'mock':
        return MockFrontendInterface(config)
    else:
        return FrontendInterface(config)