"""增强的前端交互接口实现"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Union
from langchain_core.messages import BaseMessage

from .exceptions import LLMTimeoutError, LLMInvalidRequestError


class EnhancedFrontendInterface:
    """增强的前端交互接口"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化增强的前端接口
        
        Args:
            config: 前端配置
        """
        self.config = config
        self.interface_type = config.get('interface_type', 'tui')  # tui, web, 或 mock
        
        if self.interface_type not in ['tui', 'web', 'mock']:
            raise ValueError(f"不支持的前端接口类型: {self.interface_type}")
        
        # 初始化特定配置
        self.tui_config = config.get('tui_config', {})
        self.web_config = config.get('web_config', {})
        self.default_timeout = config.get('default_timeout', 300)
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self) -> None:
        """验证配置"""
        # 验证TUI配置
        if self.interface_type == 'tui':
            required_tui_fields = ['prompt_style', 'input_area_height']
            for field in required_tui_fields:
                if field not in self.tui_config:
                    self.tui_config[field] = self._get_default_tui_config(field)
        
        # 验证Web配置
        elif self.interface_type == 'web':
            required_web_fields = ['endpoint']
            for field in required_web_fields:
                if field not in self.web_config:
                    self.web_config[field] = self._get_default_web_config(field)
    
    def _get_default_tui_config(self, field: str) -> Any:
        """获取默认TUI配置"""
        defaults = {
            'prompt_style': 'highlight',
            'input_area_height': 10,
            'show_line_numbers': True,
            'auto_scroll': True,
            'color_scheme': 'default',
            'border_style': 'single',
            'title_style': 'bold'
        }
        return defaults.get(field)
    
    def _get_default_web_config(self, field: str) -> Any:
        """获取默认Web配置"""
        defaults = {
            'endpoint': '/api/human-relay',
            'websocket': True,
            'timeout': 30000,  # 30秒
            'retry_attempts': 3,
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        }
        return defaults.get(field)
    
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
        elif self.interface_type == 'web':
            return await self._web_prompt(prompt, mode, **kwargs)
        else:
            return await self._mock_prompt(prompt, mode, **kwargs)
    
    async def _tui_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """TUI前端交互实现"""
        try:
            from src.presentation.tui.components.human_relay_panel_enhanced import HumanRelayPanelEnhanced
            
            panel = HumanRelayPanelEnhanced(self.tui_config)
            return await panel.show_prompt(prompt, mode, **kwargs)
        except ImportError as e:
            # 如果增强版不可用，回退到基础版
            try:
                from src.presentation.tui.components.human_relay_panel import HumanRelayPanel
                
                panel = HumanRelayPanel(self.tui_config)
                return await panel.show_prompt(prompt, mode, **kwargs)
            except ImportError as e2:
                raise LLMInvalidRequestError(f"TUI组件不可用: {e2}")
    
    async def _web_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """Web前端交互实现"""
        try:
            from src.presentation.web.components.human_relay_client import HumanRelayWebClient
            
            client = HumanRelayWebClient(self.web_config)
            return await client.send_prompt(prompt, mode, **kwargs)
        except ImportError as e:
            raise LLMInvalidRequestError(f"Web组件不可用: {e}")
    
    async def _mock_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """Mock前端交互实现"""
        mock_config = self.config.get('mock_config', {})
        mock_response = mock_config.get('mock_response', "这是一个模拟的Web LLM回复")
        mock_delay = mock_config.get('mock_delay', 0.1)
        
        # 模拟延迟
        if mock_delay > 0:
            await asyncio.sleep(mock_delay)
        
        # 模拟超时检查
        timeout = kwargs.get('timeout', self.default_timeout)
        if timeout < mock_delay:
            raise LLMTimeoutError(f"Mock超时（{timeout}秒）", timeout=timeout)
        
        # 根据模式调整回复
        if mode == 'multi':
            return f"[多轮模式] {mock_response}"
        else:
            return f"[单轮模式] {mock_response}"
    
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
            
            # 添加时间戳（如果有）
            timestamp = ""
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                if 'timestamp' in message.additional_kwargs:
                    timestamp = f" [{message.additional_kwargs['timestamp']}] "
            
            formatted_lines.append(f"{timestamp}{i}. {role}: {content}")
        
        return "\n".join(formatted_lines)
    
    def format_conversation_history_compact(self, history: List[BaseMessage]) -> str:
        """
        格式化对话历史（紧凑模式）
        
        Args:
            history: 对话历史消息列表
            
        Returns:
            str: 格式化后的对话历史
        """
        if not history:
            return ""
        
        # 只显示最近的消息
        recent_history = history[-5:] if len(history) > 5 else history
        
        formatted_parts = []
        for message in recent_history:
            role = "U" if message.type == "human" else "A"
            content = str(message.content)[:50]  # 限制长度
            if len(str(message.content)) > 50:
                content += "..."
            formatted_parts.append(f"{role}:{content}")
        
        return " | ".join(formatted_parts)
    
    def validate_timeout(self, timeout: Optional[int]) -> int:
        """
        验证并返回超时时间
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            int: 验证后的超时时间
        """
        if timeout is None:
            timeout = self.default_timeout
        
        if timeout <= 0:
            raise ValueError("超时时间必须大于0")
        
        # 检查最大超时限制
        max_timeout = self.config.get('max_timeout', 3600)  # 默认1小时
        if timeout > max_timeout:
            timeout = max_timeout
        
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
    
    def get_interface_info(self) -> Dict[str, Any]:
        """
        获取接口信息
        
        Returns:
            Dict[str, Any]: 接口信息
        """
        return {
            "interface_type": self.interface_type,
            "tui_config": self.tui_config,
            "web_config": self.web_config,
            "default_timeout": self.default_timeout,
            "config": self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            new_config: 新的配置
        """
        self.config.update(new_config)
        
        # 更新特定配置
        if 'tui_config' in new_config:
            self.tui_config.update(new_config['tui_config'])
        
        if 'web_config' in new_config:
            self.web_config.update(new_config['web_config'])
        
        if 'default_timeout' in new_config:
            self.default_timeout = new_config['default_timeout']
        
        # 重新验证配置
        self._validate_config()
    
    def is_available(self) -> bool:
        """
        检查接口是否可用
        
        Returns:
            bool: 是否可用
        """
        if self.interface_type == 'tui':
            try:
                from src.presentation.tui.components.human_relay_panel_enhanced import HumanRelayPanelEnhanced
                return True
            except ImportError:
                try:
                    from src.presentation.tui.components.human_relay_panel import HumanRelayPanel
                    return True
                except ImportError:
                    return False
        elif self.interface_type == 'web':
            try:
                from src.presentation.web.components.human_relay_client import HumanRelayWebClient
                return True
            except ImportError:
                return False
        else:
            return True  # Mock总是可用
        
        return True


class HumanRelayPanelEnhanced:
    """增强的HumanRelay TUI面板"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化增强的TUI面板
        
        Args:
            config: TUI配置
        """
        self.config = config
        self.prompt_style = config.get('prompt_style', 'highlight')
        self.input_area_height = config.get('input_area_height', 10)
        self.show_line_numbers = config.get('show_line_numbers', True)
        self.auto_scroll = config.get('auto_scroll', True)
        self.color_scheme = config.get('color_scheme', 'default')
        self.border_style = config.get('border_style', 'single')
        self.title_style = config.get('title_style', 'bold')
    
    async def show_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """
        显示提示并等待用户输入
        
        Args:
            prompt: 提示内容
            mode: 模式
            **kwargs: 其他参数
            
        Returns:
            str: 用户输入
        """
        # 这里实现增强的TUI交互逻辑
        # 包括更好的样式、快捷键支持等
        return await self._show_enhanced_prompt(prompt, mode, **kwargs)
    
    async def _show_enhanced_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """显示增强的提示界面"""
        # 模拟实现，实际应该使用blessed库创建TUI界面
        print(f"\n{'='*60}")
        print(f"HumanRelay - {mode.upper()} 模式")
        print(f"{'='*60}")
        print(f"\n提示词:\n{prompt}")
        print(f"\n请输入Web LLM回复:")
        
        # 模拟用户输入
        import sys
        user_input = sys.stdin.readline().strip()
        
        return user_input


class HumanRelayWebClient:
    """HumanRelay Web客户端"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化Web客户端
        
        Args:
            config: Web配置
        """
        self.config = config
        self.endpoint = config.get('endpoint', '/api/human-relay')
        self.websocket = config.get('websocket', True)
        self.timeout = config.get('timeout', 30000)
        self.headers = config.get('headers', {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.retry_attempts = config.get('retry_attempts', 3)
    
    async def send_prompt(self, prompt: str, mode: str, **kwargs) -> str:
        """
        发送提示到Web端
        
        Args:
            prompt: 提示内容
            mode: 模式
            **kwargs: 其他参数
            
        Returns:
            str: Web LLM回复
        """
        # 这里实现与Web端的通信逻辑
        # 包括WebSocket连接、HTTP请求等
        return await self._send_web_request(prompt, mode, **kwargs)
    
    async def _send_web_request(self, prompt: str, mode: str, **kwargs) -> str:
        """发送Web请求"""
        # 模拟实现
        import asyncio
        await asyncio.sleep(0.1)
        
        payload = {
            "prompt": prompt,
            "mode": mode,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # 模拟响应
        return f"Web LLM回复: {prompt[:50]}..."


def create_enhanced_frontend_interface(config: Dict[str, Any]) -> EnhancedFrontendInterface:
    """
    创建增强的前端接口实例
    
    Args:
        config: 前端配置
        
    Returns:
        EnhancedFrontendInterface: 增强的前端接口实例
    """
    interface_type = config.get('interface_type', 'tui')
    
    if interface_type == 'mock':
        # 创建Mock接口
        mock_config = config.copy()
        mock_config['interface_type'] = 'mock'
        return EnhancedFrontendInterface(mock_config)
    else:
        return EnhancedFrontendInterface(config)