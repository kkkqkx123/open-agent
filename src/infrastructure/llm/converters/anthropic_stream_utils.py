"""Anthropic流式响应处理工具

专门处理Anthropic API的流式响应，包括Server-Sent Events格式解析等。
"""

from typing import Dict, Any, List, Optional, Union, Iterator
import json
from src.services.logger import get_logger


class AnthropicStreamUtils:
    """Anthropic流式响应处理工具类"""
    
    # 流式事件类型
    EVENT_TYPES = {
        "message_start",
        "content_block_start", 
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop"
    }
    
    def __init__(self) -> None:
        """初始化流式工具"""
        self.logger = get_logger(__name__)
    
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析流式事件行
        
        Args:
            event_line: 事件行，格式为 "data: {json}"
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的事件数据
        """
        try:
            if not event_line.startswith("data: "):
                return None
            
            # 移除 "data: " 前缀
            json_str = event_line[6:].strip()
            
            # 检查是否为结束标记
            if json_str == "[DONE]":
                return {"type": "stream_end"}
            
            # 解析JSON
            event_data = json.loads(json_str)
            
            # 验证事件类型
            event_type = event_data.get("type")
            if event_type not in self.EVENT_TYPES:
                self.logger.warning(f"未知的事件类型: {event_type}")
            
            return event_data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}, 原始数据: {event_line}")
            return None
        except Exception as e:
            self.logger.error(f"解析流式事件失败: {e}")
            return None
    
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理流式事件列表，构建完整响应
        
        Args:
            events: 流式事件列表
            
        Returns:
            Dict[str, Any]: 构建的完整响应
        """
        response = {
            "id": "",
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": "",
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0
            }
        }
        
        current_content_block = None
        content_blocks = []
        
        for event in events:
            event_type = event.get("type")
            
            if event_type == "message_start":
                response.update(self._process_message_start(event))
            elif event_type == "content_block_start":
                current_content_block = self._process_content_block_start(event)
            elif event_type == "content_block_delta":
                if current_content_block:
                    current_content_block = self._process_content_block_delta(
                        current_content_block, event
                    )
            elif event_type == "content_block_stop":
                if current_content_block:
                    content_blocks.append(current_content_block)
                    current_content_block = None
            elif event_type == "message_delta":
                response.update(self._process_message_delta(response, event))
            elif event_type == "message_stop":
                # 流式结束，无需特殊处理
                pass
            elif event_type == "stream_end":
                # 处理结束标记
                break
        
        # 设置内容
        response["content"] = content_blocks
        
        return response
    
    def _process_message_start(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """处理message_start事件"""
        message = event.get("message", {})
        return {
            "id": message.get("id", ""),
            "model": message.get("model", ""),
            "usage": message.get("usage", {
                "input_tokens": 0,
                "output_tokens": 0
            })
        }
    
    def _process_content_block_start(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """处理content_block_start事件"""
        content_block = event.get("content_block", {})
        block_type = content_block.get("type", "text")
        
        if block_type == "text":
            return {
                "type": "text",
                "text": ""
            }
        elif block_type == "tool_use":
            return {
                "type": "tool_use",
                "id": content_block.get("id", ""),
                "name": content_block.get("name", ""),
                "input": {}
            }
        else:
            return {
                "type": block_type,
                "data": {}
            }
    
    def _process_content_block_delta(
        self, 
        content_block: Dict[str, Any], 
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理content_block_delta事件"""
        delta = event.get("delta", {})
        delta_type = delta.get("type")
        
        if content_block["type"] == "text" and delta_type == "text_delta":
            text_delta = delta.get("text", "")
            content_block["text"] += text_delta
        elif content_block["type"] == "tool_use" and delta_type == "input_json_delta":
            partial_json = delta.get("partial_json", "")
            # 这里需要更复杂的JSON合并逻辑
            # 简化处理：假设partial_json是完整的JSON片段
            try:
                if partial_json:
                    new_input = json.loads(partial_json)
                    content_block["input"].update(new_input)
            except json.JSONDecodeError:
                self.logger.warning(f"无法解析工具输入JSON片段: {partial_json}")
        
        return content_block
    
    def _process_message_delta(
        self, 
        response: Dict[str, Any], 
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理message_delta事件"""
        delta = event.get("delta", {})
        
        # 更新停止原因
        if "stop_reason" in delta:
            response["stop_reason"] = delta["stop_reason"]
        
        if "stop_sequence" in delta:
            response["stop_sequence"] = delta["stop_sequence"]
        
        # 更新使用统计
        usage = event.get("usage", {})
        if "output_tokens" in usage:
            response["usage"]["output_tokens"] += usage["output_tokens"]
        
        return response
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从流式事件中提取文本内容
        
        Args:
            events: 流式事件列表
            
        Returns:
            str: 提取的文本内容
        """
        text_parts = []
        current_text = ""
        
        for event in events:
            event_type = event.get("type")
            
            if event_type == "content_block_start":
                content_block = event.get("content_block", {})
                if content_block.get("type") == "text":
                    current_text = ""
            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    current_text += delta.get("text", "")
            elif event_type == "content_block_stop":
                if current_text:
                    text_parts.append(current_text)
                    current_text = ""
        
        return "".join(text_parts)
    
    def extract_tool_calls_from_stream_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从流式事件中提取工具调用
        
        Args:
            events: 流式事件列表
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        tool_calls = []
        current_tool_call = None
        
        for event in events:
            event_type = event.get("type")
            
            if event_type == "content_block_start":
                content_block = event.get("content_block", {})
                if content_block.get("type") == "tool_use":
                    current_tool_call = {
                        "id": content_block.get("id", ""),
                        "name": content_block.get("name", ""),
                        "input": {}
                    }
            elif event_type == "content_block_delta" and current_tool_call:
                delta = event.get("delta", {})
                if delta.get("type") == "input_json_delta":
                    partial_json = delta.get("partial_json", "")
                    try:
                        if partial_json:
                            new_input = json.loads(partial_json)
                            current_tool_call["input"].update(new_input)
                    except json.JSONDecodeError:
                        self.logger.warning(f"无法解析工具输入JSON片段: {partial_json}")
            elif event_type == "content_block_stop" and current_tool_call:
                # 转换为标准格式
                tool_call = {
                    "id": current_tool_call["id"],
                    "type": "function",
                    "function": {
                        "name": current_tool_call["name"],
                        "arguments": current_tool_call["input"]
                    }
                }
                tool_calls.append(tool_call)
                current_tool_call = None
        
        return tool_calls
    
    def validate_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """验证流式事件
        
        Args:
            events: 流式事件列表
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not isinstance(events, list):
            errors.append("事件必须是列表格式")
            return errors
        
        has_message_start = False
        has_message_stop = False
        
        for i, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append(f"事件 {i} 必须是字典")
                continue
            
            event_type = event.get("type")
            if not event_type:
                errors.append(f"事件 {i} 缺少type字段")
                continue
            
            if event_type not in self.EVENT_TYPES and event_type != "stream_end":
                errors.append(f"事件 {i} 有未知类型: {event_type}")
            
            if event_type == "message_start":
                if has_message_start:
                    errors.append(f"事件 {i} 重复的message_start")
                has_message_start = True
            elif event_type == "message_stop":
                if has_message_stop:
                    errors.append(f"事件 {i} 重复的message_stop")
                has_message_stop = True
        
        if not has_message_start:
            errors.append("缺少message_start事件")
        
        return errors
    
    def create_stream_response_iterator(
        self, 
        raw_stream: Iterator[str]
    ) -> Iterator[Dict[str, Any]]:
        """创建流式响应迭代器
        
        Args:
            raw_stream: 原始流数据迭代器
            
        Yields:
            Dict[str, Any]: 解析后的事件
        """
        for line in raw_stream:
            line = line.strip()
            if not line:
                continue
            
            event = self.parse_stream_event(line)
            if event:
                yield event