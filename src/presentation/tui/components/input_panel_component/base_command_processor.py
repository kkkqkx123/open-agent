"""基础命令处理器

定义命令处理器的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any

from ...logger import get_tui_silent_logger


class BaseCommandProcessor(ABC):
    """基础命令处理器抽象类"""
    
    def __init__(self, trigger_char: str):
        """初始化命令处理器
        
        Args:
            trigger_char: 触发字符 (如 '@', '#', '/')
        """
        self.trigger_char = trigger_char
        
        # 初始化TUI调试日志记录器
        self.tui_logger = get_tui_silent_logger("base_command_processor")
    
    @abstractmethod
    def is_command(self, input_text: str) -> bool:
        """检查输入是否是该类型的命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            bool: 是否是命令
        """
        pass
    
    @abstractmethod
    def parse_command(self, input_text: str) -> Tuple[str, List[str]]:
        """解析命令和参数
        
        Args:
            input_text: 输入文本
            
        Returns:
            Tuple[str, List[str]]: 命令名称和参数列表
        """
        pass
    
    @abstractmethod
    def execute_command(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """执行命令
        
        Args:
            input_text: 输入文本
            context: 执行上下文
            
        Returns:
            Optional[str]: 执行结果或错误信息
        """
        pass
    
    @abstractmethod
    def get_suggestions(self, partial_input: str) -> List[str]:
        """获取命令补全建议
        
        Args:
            partial_input: 部分输入
            
        Returns:
            List[str]: 补全建议列表
        """
        pass
    
    def get_command_help(self, command_name: Optional[str] = None) -> str:
        """获取命令帮助
        
        Args:
            command_name: 命令名称，None表示显示所有命令
            
        Returns:
            str: 帮助文本
        """
        if command_name:
            return f"未知命令: {command_name}"
        
        return f"使用 {self.trigger_char} 触发 {self.__class__.__name__} 命令"
    
    def _remove_trigger_char(self, input_text: str) -> str:
        """移除触发字符
        
        Args:
            input_text: 输入文本
            
        Returns:
            str: 移除触发字符后的文本
        """
        if input_text.startswith(self.trigger_char):
            return input_text[1:].strip()
        return input_text
    
    def _split_command_and_args(self, command_text: str) -> Tuple[str, List[str]]:
        """分割命令和参数
        
        Args:
            command_text: 命令文本
            
        Returns:
            Tuple[str, List[str]]: 命令名称和参数列表
        """
        parts = command_text.split()
        if not parts:
            return "", []
        
        command_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        return command_name, args