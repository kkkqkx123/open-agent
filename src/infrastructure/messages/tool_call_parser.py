"""
工具调用解析器

提供统一的工具调用解析功能，将不同格式的工具调用转换为标准格式。
"""

import json
from typing import Dict, Any, List, Optional, Union
from src.interfaces.tool.base import ToolCall


class ToolCallParser:
    """工具调用解析器
    
    负责将不同格式的工具调用数据解析为标准的ToolCall对象。
    """
    
    @staticmethod
    def parse_tool_call(tool_call_data: Dict[str, Any]) -> Optional[ToolCall]:
        """解析单个工具调用
        
        Args:
            tool_call_data: 工具调用数据
            
        Returns:
            Optional[ToolCall]: 解析后的工具调用对象，解析失败返回None
        """
        try:
            # 处理标准格式（OpenAI格式）
            if "function" in tool_call_data:
                function = tool_call_data["function"]
                if "name" in function and "arguments" in function:
                    # 解析参数
                    if isinstance(function["arguments"], str):
                        arguments = json.loads(function["arguments"])
                    else:
                        arguments = function["arguments"]
                    
                    return ToolCall(
                        name=function["name"],
                        arguments=arguments,
                        call_id=tool_call_data.get("id")
                    )
            
            return None
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # 解析失败，返回None
            return None
    
    @staticmethod
    def parse_tool_calls(tool_calls_data: List[Dict[str, Any]]) -> List[ToolCall]:
        """解析多个工具调用
        
        Args:
            tool_calls_data: 工具调用数据列表
            
        Returns:
            List[ToolCall]: 解析后的工具调用对象列表
        """
        tool_calls = []
        
        for tool_call_data in tool_calls_data:
            tool_call = ToolCallParser.parse_tool_call(tool_call_data)
            if tool_call:
                tool_calls.append(tool_call)
        
        return tool_calls
    
    @staticmethod
    def extract_and_parse_tool_calls(message_data: Dict[str, Any]) -> List[ToolCall]:
        """从消息数据中提取并解析工具调用
        
        Args:
            message_data: 消息数据
            
        Returns:
            List[ToolCall]: 解析后的工具调用对象列表
        """
        tool_calls_data = []
        
        # 从tool_calls字段提取
        if "tool_calls" in message_data:
            tool_calls_data.extend(message_data["tool_calls"])
        
        # 从additional_kwargs中的function_call提取
        if "additional_kwargs" in message_data:
            additional_kwargs = message_data["additional_kwargs"]
            if isinstance(additional_kwargs, dict) and "function_call" in additional_kwargs:
                tool_calls_data.append(additional_kwargs["function_call"])
        
        # 从response_metadata提取
        if "response_metadata" in message_data:
            metadata = message_data["response_metadata"]
            if isinstance(metadata, dict):
                if "function_call" in metadata:
                    tool_calls_data.append(metadata["function_call"])
                elif "tool_calls" in metadata:
                    tool_calls_data.extend(metadata["tool_calls"])
        
        return ToolCallParser.parse_tool_calls(tool_calls_data)
    
    @staticmethod
    def validate_tool_call(tool_call_data: Dict[str, Any]) -> List[str]:
        """验证工具调用数据
        
        Args:
            tool_call_data: 工具调用数据
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not isinstance(tool_call_data, dict):
            errors.append("工具调用数据必须是字典")
            return errors
        
        # 检查标准格式
        if "function" in tool_call_data:
            function = tool_call_data["function"]
            if not isinstance(function, dict):
                errors.append("function字段必须是字典")
            else:
                if "name" not in function:
                    errors.append("缺少function.name字段")
                if "arguments" not in function:
                    errors.append("缺少function.arguments字段")
        
        else:
            errors.append("无法识别的工具调用格式，必须包含function字段")
        
        return errors
    
    @staticmethod
    def normalize_tool_call_data(tool_call_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化工具调用数据格式
        
        Args:
            tool_call_data: 原始工具调用数据
            
        Returns:
            Dict[str, Any]: 标准化后的工具调用数据
        """
        # 如果已经是标准格式，直接返回
        if "function" in tool_call_data:
            return tool_call_data
        
        # 无法识别的格式，返回原数据
        return tool_call_data