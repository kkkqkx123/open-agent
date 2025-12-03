"""Anthropic流式响应处理工具

专门处理Anthropic API的流式响应功能。
"""

import json
from typing import Dict, Any, List, Optional
from src.services.logger import get_logger
from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils


class AnthropicStreamUtils(BaseStreamUtils):
    """Anthropic流式响应处理工具类"""
    
    def __init__(self) -> None:
        """初始化流式工具"""
        super().__init__()
    
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析流式事件行
        
        Args:
            event_line: 流式事件行文本
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的事件数据，如果解析失败返回None
        """
        try:
            # Anthropic流式响应使用Server-Sent Events格式
            if not event_line.strip():
                return None
            
            # 处理事件类型
            if event_line.startswith("event: "):
                event_type = event_line[7:].strip()
                return {"event_type": event_type}
            elif event_line.startswith("data: "):
                data_str = event_line[6:].strip()
                if data_str == "[DONE]":
                    return {"type": "done"}
                return json.loads(data_str)
            else:
                # 尝试直接解析JSON
                return json.loads(event_line)
        except json.JSONDecodeError:
            self.logger.warning(f"无法解析Anthropic流式事件JSON: {event_line}")
            return None
        except Exception as e:
            self.logger.error(f"解析Anthropic流式事件失败: {e}")
            return None
    
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理流式事件列表
        
        Args:
            events: 流式事件列表
            
        Returns:
            Dict[str, Any]: 合并后的响应数据
        """
        merged_response = {
            "content": [],
            "id": "",
            "type": "message",
            "role": "assistant",
            "model": "",
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {}
        }
        
        current_content_block = None
        accumulated_text = ""
        
        for event in events:
            try:
                event_type = event.get("type")
                
                if event_type == "message_start":
                    # 消息开始
                    message = event.get("message", {})
                    merged_response["id"] = message.get("id", "")
                    merged_response["model"] = message.get("model", "")
                    merged_response["usage"] = message.get("usage", {})
                
                elif event_type == "content_block_start":
                    # 内容块开始
                    content_block = event.get("content_block", {})
                    current_content_block = {
                        "type": content_block.get("type"),
                        "index": content_block.get("index")
                    }
                    
                    if content_block.get("type") == "text":
                        current_content_block["text"] = ""
                    elif content_block.get("type") == "tool_use":
                        current_content_block.update({
                            "id": content_block.get("id"),
                            "name": content_block.get("name"),
                            "input": {}
                        })
                
                elif event_type == "content_block_delta":
                    # 内容块增量
                    delta = event.get("delta", {})
                    delta_type = delta.get("type")
                    
                    if current_content_block and delta_type == "text_delta":
                        text = delta.get("text", "")
                        accumulated_text += text
                        current_content_block["text"] = accumulated_text
                    elif current_content_block and delta_type == "input_json_delta":
                        partial_json = delta.get("partial_json", "")
                        if "input" not in current_content_block:
                            current_content_block["input"] = ""
                        current_content_block["input"] += partial_json
                
                elif event_type == "content_block_stop":
                    # 内容块结束
                    if current_content_block:
                        if current_content_block.get("type") == "tool_use":
                            # 解析工具输入JSON
                            try:
                                input_str = current_content_block.get("input", "{}")
                                if isinstance(input_str, str):
                                    current_content_block["input"] = json.loads(input_str)
                            except json.JSONDecodeError:
                                self.logger.warning("无法解析工具输入JSON")
                        
                        merged_response["content"].append(current_content_block.copy())
                        current_content_block = None
                        accumulated_text = ""
                
                elif event_type == "message_delta":
                    # 消息增量
                    delta = event.get("delta", {})
                    stop_reason = delta.get("stop_reason")
                    if stop_reason:
                        merged_response["stop_reason"] = stop_reason
                
                elif event_type == "message_stop":
                    # 消息结束
                    break
                
            except Exception as e:
                self.logger.error(f"处理流式事件失败: {e}")
                continue
        
        return merged_response
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从流式事件中提取文本
        
        Args:
            events: 流式事件列表
            
        Returns:
            str: 提取的文本内容
        """
        text_parts = []
        
        for event in events:
            try:
                event_type = event.get("type")
                
                if event_type == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text_parts.append(delta.get("text", ""))
            except Exception as e:
                self.logger.error(f"提取文本失败: {e}")
                continue
        
        return "".join(text_parts)
    
    def validate_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """验证流式事件"""
        errors = []
        
        if not isinstance(events, list):
            errors.append("流式事件必须是列表格式")
            return errors
        
        if not events:
            errors.append("流式事件列表不能为空")
            return errors
        
        # 检查是否有message_start事件
        has_start = any(event.get("type") == "message_start" for event in events)
        if not has_start:
            errors.append("流式事件缺少message_start事件")
        
        # 检查是否有message_stop事件
        has_stop = any(event.get("type") == "message_stop" for event in events)
        if not has_stop:
            errors.append("流式事件缺少message_stop事件")
        
        for i, event in enumerate(events):
            event_errors = self._validate_single_event(event, i)
            errors.extend(event_errors)
        
        return errors
    
    def _validate_single_event(self, event: Dict[str, Any], index: int) -> List[str]:
        """验证单个流式事件"""
        errors = []
        
        if not isinstance(event, dict):
            errors.append(f"流式事件 {index} 必须是字典")
            return errors
        
        event_type = event.get("type")
        if not event_type:
            errors.append(f"流式事件 {index} 缺少type字段")
            return errors
        
        # Anthropic特定验证
        valid_types = {
            "message_start", "content_block_start", "content_block_delta",
            "content_block_stop", "message_delta", "message_stop", "error"
        }
        
        if event_type not in valid_types:
            errors.append(f"流式事件 {index} 有无效的type: {event_type}")
        
        return errors
    
    def _merge_single_event(self, merged: Dict[str, Any], event: Dict[str, Any]) -> None:
        """合并单个事件到响应中"""
        event_type = event.get("type")
        
        if event_type == "message_start":
            message = event.get("message", {})
            merged.update({
                "id": message.get("id", merged.get("id", "")),
                "model": message.get("model", merged.get("model", "")),
                "usage": message.get("usage", merged.get("usage", {}))
            })
        
        elif event_type == "message_delta":
            delta = event.get("delta", {})
            if "stop_reason" in delta:
                merged["stop_reason"] = delta["stop_reason"]
            if "stop_sequence" in delta:
                merged["stop_sequence"] = delta["stop_sequence"]
        
        elif event_type == "content_block_stop":
            # 内容块在process_stream_events中处理
            pass
    
    def _extract_text_from_single_event(self, event: Dict[str, Any]) -> Optional[str]:
        """从单个事件中提取文本"""
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return delta.get("text", "")
        return None
    
    def _extract_tool_call_from_single_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从单个事件中提取工具调用"""
        if event.get("type") == "content_block_stop":
            # 工具调用在process_stream_events中处理
            pass
        return None
    
    def _is_complete_event(self, event: Dict[str, Any]) -> bool:
        """检查事件是否为完成事件"""
        return event.get("type") == "message_stop"
    
    def extract_tool_calls_from_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从事件中提取工具调用"""
        tool_calls = []
        
        # 处理完整的事件序列
        response = self.process_stream_events(events)
        
        for item in response.get("content", []):
            if item.get("type") == "tool_use":
                tool_call = {
                    "id": item.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": item.get("input", {})
                    }
                }
                tool_calls.append(tool_call)
        
        return tool_calls
    
    def extract_tool_calls_from_stream_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从流式事件中提取工具调用（别名方法）
        
        Args:
            events: 流式事件列表
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        return self.extract_tool_calls_from_events(events)
    
    def create_stream_response(
        self, 
        content: str, 
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        stop_reason: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建流式响应结构"""
        content_blocks = [{"type": "text", "text": content}]
        
        if tool_calls:
            for tool_call in tool_calls:
                content_blocks.append({
                    "type": "tool_use",
                    "id": tool_call.get("id", ""),
                    "name": tool_call.get("function", {}).get("name", ""),
                    "input": tool_call.get("function", {}).get("arguments", {})
                })
        
        response = {
            "content": content_blocks,
            "type": "message",
            "role": "assistant"
        }
        
        if stop_reason:
            response["stop_reason"] = stop_reason
        
        # 添加其他字段
        for key, value in kwargs.items():
            response[key] = value
        
        return response