"""流式响应基础工具类

定义所有LLM提供商的流式响应处理通用接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.services.logger.injection import get_logger


class BaseStreamUtils(ABC):
    """流式响应基础工具类
    
    定义流式响应处理的通用接口和基础功能。
    """
    
    def __init__(self) -> None:
        """初始化流式工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析流式事件行
        
        Args:
            event_line: 流式事件行文本
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的事件数据，如果解析失败返回None
        """
        pass
    
    @abstractmethod
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理流式事件列表
        
        Args:
            events: 流式事件列表
            
        Returns:
            Dict[str, Any]: 合并后的响应数据
        """
        pass
    
    @abstractmethod
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从流式事件中提取文本
        
        Args:
            events: 流式事件列表
            
        Returns:
            str: 提取的文本内容
        """
        pass
    
    def validate_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """验证流式事件（通用方法）"""
        errors = []
        
        if not isinstance(events, list):
            errors.append("流式事件必须是列表格式")
            return errors
        
        if not events:
            errors.append("流式事件列表不能为空")
            return errors
        
        for i, event in enumerate(events):
            event_errors = self._validate_single_event(event, i)
            errors.extend(event_errors)
        
        return errors
    
    def _validate_single_event(self, event: Dict[str, Any], index: int) -> List[str]:
        """验证单个流式事件（基础实现，子类可重写）"""
        errors = []
        
        if not isinstance(event, dict):
            errors.append(f"流式事件 {index} 必须是字典")
            return errors
        
        # 基础验证，子类可以添加更多特定验证
        if not event:
            errors.append(f"流式事件 {index} 不能为空")
        
        return errors
    
    def _merge_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并流式事件（通用方法）"""
        merged_response = {}
        
        for event in events:
            if isinstance(event, dict):
                self._merge_single_event(merged_response, event)
        
        return merged_response
    
    def _merge_single_event(self, merged: Dict[str, Any], event: Dict[str, Any]) -> None:
        """合并单个事件到响应中（基础实现，子类可重写）"""
        # 基础实现：简单更新字典
        merged.update(event)
    
    def _extract_text_from_events(self, events: List[Dict[str, Any]]) -> str:
        """从事件列表中提取文本（通用方法）"""
        text_parts = []
        
        for event in events:
            text = self._extract_text_from_single_event(event)
            if text:
                text_parts.append(text)
        
        return "".join(text_parts)
    
    def _extract_text_from_single_event(self, event: Dict[str, Any]) -> Optional[str]:
        """从单个事件中提取文本（基础实现，子类可重写）"""
        # 基础实现：尝试常见的文本字段
        text_fields = ["content", "text", "delta", "message"]
        
        for field in text_fields:
            if field in event:
                value = event[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict):
                    # 尝试从嵌套字典中提取文本
                    nested_text = self._extract_text_from_nested_dict(value)
                    if nested_text:
                        return nested_text
        
        return None
    
    def _extract_text_from_nested_dict(self, nested_dict: Dict[str, Any]) -> Optional[str]:
        """从嵌套字典中提取文本（辅助方法）"""
        for key, value in nested_dict.items():
            if isinstance(value, str) and key in ["content", "text"]:
                return value
            elif isinstance(value, dict):
                result = self._extract_text_from_nested_dict(value)
                if result:
                    return result
        
        return None
    
    def _parse_sse_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析Server-Sent Events格式（通用方法）"""
        import json
        try:
            if not event_line.strip():
                return None
            
            # 移除 "data: " 前缀
            if event_line.startswith("data: "):
                event_line = event_line[6:]
            
            # 检查是否为结束标记
            if event_line.strip() == "[DONE]":
                return {"type": "done"}
            
            # 尝试解析JSON
            return json.loads(event_line)
        except json.JSONDecodeError:
            self.logger.warning(f"无法解析流式事件JSON: {event_line}")
            return None
        except Exception as e:
            self.logger.error(f"解析流式事件失败: {e}")
            return None
    
    def _filter_events_by_type(self, events: List[Dict[str, Any]], event_types: List[str]) -> List[Dict[str, Any]]:
        """按类型过滤事件（辅助方法）"""
        filtered_events = []
        
        for event in events:
            event_type = event.get("type")
            if event_type in event_types:
                filtered_events.append(event)
        
        return filtered_events
    
    def _group_events_by_type(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按类型分组事件（辅助方法）"""
        grouped_events = {}
        
        for event in events:
            event_type = event.get("type", "unknown")
            if event_type not in grouped_events:
                grouped_events[event_type] = []
            grouped_events[event_type].append(event)
        
        return grouped_events
    
    def _extract_tool_calls_from_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从事件中提取工具调用（通用方法）"""
        tool_calls = []
        
        for event in events:
            tool_call = self._extract_tool_call_from_single_event(event)
            if tool_call:
                tool_calls.append(tool_call)
        
        return tool_calls
    
    def _extract_tool_call_from_single_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从单个事件中提取工具调用（基础实现，子类可重写）"""
        # 基础实现：查找常见的工具调用字段
        if "tool_calls" in event:
            return event["tool_calls"]
        elif "function_call" in event:
            return event["function_call"]
        elif "tool_use" in event:
            return event["tool_use"]
        
        return None
    
    def _create_stream_response(
        self, 
        content: str, 
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建流式响应结构（通用方法）"""
        response = {
            "content": content,
            **kwargs
        }
        
        if tool_calls:
            response["tool_calls"] = tool_calls
        
        return response
    
    def _is_complete_event(self, event: Dict[str, Any]) -> bool:
        """检查事件是否为完成事件（基础实现，子类可重写）"""
        finish_reasons = ["stop", "end_turn", "max_tokens", "stop_sequence", "tool_use"]
        finish_reason = event.get("finish_reason") or event.get("stop_reason")
        
        return finish_reason in finish_reasons or event.get("type") == "done"