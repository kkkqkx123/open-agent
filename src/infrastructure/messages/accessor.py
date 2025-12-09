"""消息工具访问器

提供统一的工具调用信息访问方式，确保类型安全和一致性。
"""

from typing import Dict, Any, List, Optional, Union
from src.interfaces.messages import IBaseMessage
from .types import AIMessage


class MessageToolAccessor:
    """消息工具访问器
    
    提供统一的工具调用信息访问方式，避免上层应用直接访问消息的具体属性。
    """
    
    @staticmethod
    def has_tool_calls(message: IBaseMessage) -> bool:
        """统一检查工具调用
        
        Args:
            message: 消息对象
            
        Returns:
            bool: 是否包含工具调用
        """
        if not isinstance(message, IBaseMessage):
            return False
        
        return message.has_tool_calls()
    
    @staticmethod
    def extract_tool_calls(message: IBaseMessage) -> List[Dict[str, Any]]:
        """统一提取工具调用
        
        Args:
            message: 消息对象
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        if not isinstance(message, IBaseMessage):
            return []
        
        return message.get_tool_calls()
    
    @staticmethod
    def extract_valid_tool_calls(message: IBaseMessage) -> List[Dict[str, Any]]:
        """提取有效的工具调用
        
        Args:
            message: 消息对象
            
        Returns:
            List[Dict[str, Any]]: 有效的工具调用列表
        """
        if not isinstance(message, IBaseMessage):
            return []
        
        return message.get_valid_tool_calls()
    
    @staticmethod
    def extract_invalid_tool_calls(message: IBaseMessage) -> List[Dict[str, Any]]:
        """提取无效的工具调用
        
        Args:
            message: 消息对象
            
        Returns:
            List[Dict[str, Any]]: 无效的工具调用列表
        """
        if not isinstance(message, IBaseMessage):
            return []
        
        return message.get_invalid_tool_calls()
    
    @staticmethod
    def is_ai_message_with_tool_calls(message: IBaseMessage) -> bool:
        """检查是否为AI消息且包含工具调用
        
        Args:
            message: 消息对象
            
        Returns:
            bool: 是否为AI消息且包含工具调用
        """
        return isinstance(message, AIMessage) and message.has_tool_calls()
    
    @staticmethod
    def get_tool_call_count(message: IBaseMessage) -> int:
        """获取工具调用数量
        
        Args:
            message: 消息对象
            
        Returns:
            int: 工具调用数量
        """
        if not isinstance(message, IBaseMessage):
            return 0
        
        return len(message.get_tool_calls())
    
    @staticmethod
    def get_valid_tool_call_count(message: IBaseMessage) -> int:
        """获取有效工具调用数量
        
        Args:
            message: 消息对象
            
        Returns:
            int: 有效工具调用数量
        """
        if not isinstance(message, IBaseMessage):
            return 0
        
        return len(message.get_valid_tool_calls())
    
    @staticmethod
    def get_invalid_tool_call_count(message: IBaseMessage) -> int:
        """获取无效工具调用数量
        
        Args:
            message: 消息对象
            
        Returns:
            int: 无效工具调用数量
        """
        if not isinstance(message, IBaseMessage):
            return 0
        
        return len(message.get_invalid_tool_calls())
    
    @staticmethod
    def add_tool_call_to_message(message: IBaseMessage, tool_call: Dict[str, Any]) -> None:
        """向消息添加工具调用
        
        Args:
            message: 消息对象
            tool_call: 工具调用信息
        """
        if isinstance(message, IBaseMessage):
            message.add_tool_call(tool_call)
    
    @staticmethod
    def extract_tool_names(message: IBaseMessage) -> List[str]:
        """提取工具调用名称列表
        
        Args:
            message: 消息对象
            
        Returns:
            List[str]: 工具名称列表
        """
        tool_calls = MessageToolAccessor.extract_tool_calls(message)
        tool_names = []
        
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                # 处理标准格式
                if "name" in tool_call:
                    tool_names.append(tool_call["name"])
                elif "function" in tool_call and "name" in tool_call["function"]:
                    tool_names.append(tool_call["function"]["name"])
        
        return tool_names
    
    @staticmethod
    def has_tool_call_with_name(message: IBaseMessage, tool_name: str) -> bool:
        """检查是否包含指定名称的工具调用
        
        Args:
            message: 消息对象
            tool_name: 工具名称
            
        Returns:
            bool: 是否包含指定名称的工具调用
        """
        tool_names = MessageToolAccessor.extract_tool_names(message)
        return tool_name in tool_names
    
    @staticmethod
    def get_tool_calls_with_name(message: IBaseMessage, tool_name: str) -> List[Dict[str, Any]]:
        """获取指定名称的工具调用
        
        Args:
            message: 消息对象
            tool_name: 工具名称
            
        Returns:
            List[Dict[str, Any]]: 指定名称的工具调用列表
        """
        tool_calls = MessageToolAccessor.extract_tool_calls(message)
        matching_calls = []
        
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                # 处理标准格式
                call_name = None
                if "name" in tool_call:
                    call_name = tool_call["name"]
                elif "function" in tool_call and "name" in tool_call["function"]:
                    call_name = tool_call["function"]["name"]
                
                if call_name == tool_name:
                    matching_calls.append(tool_call)
        
        return matching_calls