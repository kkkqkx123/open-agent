"""OpenAI Responses API流式处理工具类

提供OpenAI Responses API的流式响应处理功能。
"""

from typing import Dict, Any, List, Optional, Union
import json
from src.services.logger.injection import get_logger
from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils


class OpenAIResponsesStreamUtils(BaseStreamUtils):
    """OpenAI Responses API流式处理工具类
    
    提供OpenAI Responses API特定的流式响应处理功能。
    Responses API的流式事件格式与Chat Completions API有所不同。
    """
    
    def __init__(self) -> None:
        """初始化OpenAI Responses流式工具"""
        super().__init__()
        self.logger = get_logger(__name__)
    
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析OpenAI Responses API流式事件行"""
        return self._parse_responses_sse_event(event_line)
    
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理OpenAI Responses API流式事件列表"""
        if not events:
            return {}
        
        # 合并所有事件
        merged_response = self._merge_responses_stream_events(events)
        
        # 提取完整内容
        content = self.extract_text_from_stream_events(events)
        if content:
            merged_response["output_text"] = content
        
        # 提取工具调用
        tool_calls = self._extract_tool_calls_from_stream_events(events)
        if tool_calls:
            merged_response["tool_calls"] = tool_calls
        
        # 提取使用信息
        usage = self._extract_usage_from_stream_events(events)
        if usage:
            merged_response["usage"] = usage
        
        # 提取推理信息
        reasoning = self._extract_reasoning_from_stream_events(events)
        if reasoning:
            merged_response["reasoning"] = reasoning
        
        return merged_response
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从OpenAI Responses API流式事件中提取文本"""
        text_parts: List[str] = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            # 检查事件类型
            event_type = event.get("type")
            
            if event_type == "response.output_text.delta":
                delta = event.get("delta", "")
                if delta and isinstance(delta, str):
                    text_parts.append(delta)
            elif event_type == "response.output_text.done":
                # 文本完成事件，可能包含完整文本
                text = event.get("text", "")
                if text and isinstance(text, str):
                    # 如果之前没有累积文本，使用完整文本
                    if not text_parts:
                        return str(text)
        
        return "".join(text_parts)
    
    def validate_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """验证OpenAI Responses API流式事件"""
        errors = []
        
        if not isinstance(events, list):
            errors.append("流式事件必须是列表格式")
            return errors
        
        if not events:
            errors.append("流式事件列表不能为空")
            return errors
        
        for i, event in enumerate(events):
            event_errors = self._validate_responses_stream_event(event, i)
            errors.extend(event_errors)
        
        return errors
    
    def _parse_responses_sse_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析Responses API的Server-Sent Events格式"""
        if not event_line.strip():
            return None
        
        try:
            # 移除 "data: " 前缀
            if event_line.startswith("data: "):
                json_str = event_line[6:]  # 去掉 "data: "
            elif event_line.startswith("data:"):
                json_str = event_line[5:]   # 去掉 "data:"
            else:
                return None
            
            # 解析JSON
            result = json.loads(json_str)
            return result if isinstance(result, dict) else None
        except json.JSONDecodeError as e:
            self.logger.warning(f"解析流式事件JSON失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析流式事件失败: {e}")
            return None
    
    def _merge_responses_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并Responses API流式事件"""
        merged_response = {}
        
        # 从第一个事件获取基本信息
        if events and isinstance(events[0], dict):
            first_event = events[0]
            
            # 复制基本字段
            for field in ["id", "object", "created", "model"]:
                if field in first_event:
                    merged_response[field] = first_event[field]
        
        # 初始化累积字段
        accumulated_text = ""
        tool_calls: List[Dict[str, Any]] = []
        reasoning_steps: List[str] = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            event_type = event.get("type")
            
            # 处理文本增量
            if event_type == "response.output_text.delta":
                delta = event.get("delta", "")
                if delta and isinstance(delta, str):
                    accumulated_text += delta
            
            # 处理文本完成
            elif event_type == "response.output_text.done":
                text = event.get("text", "")
                if text and isinstance(text, str):
                    # 如果没有累积文本，使用完整文本
                    if not accumulated_text:
                        accumulated_text = text
            
            # 处理工具调用增量
            elif event_type == "response.tool_call.delta":
                self._process_tool_call_delta(tool_calls, event)
            
            # 处理工具调用完成
            elif event_type == "response.tool_call.done":
                self._process_tool_call_done(tool_calls, event)
            
            # 处理推理增量
            elif event_type == "response.reasoning.delta":
                delta = event.get("delta", "")
                if delta and isinstance(delta, str):
                    reasoning_steps.append(delta)
            
            # 处理推理完成
            elif event_type == "response.reasoning.done":
                reasoning = event.get("reasoning", {})
                if reasoning and isinstance(reasoning, dict):
                    merged_response["reasoning"] = reasoning
            
            # 处理响应完成
            elif event_type == "response.done":
                # 最终完成事件，可能包含完整响应
                final_response = event.get("response", {})
                if final_response and isinstance(final_response, dict):
                    merged_response.update(final_response)
        
        # 设置累积的内容
        if accumulated_text:
            merged_response["output_text"] = accumulated_text
        
        if tool_calls:
            merged_response["tool_calls"] = tool_calls
        
        if reasoning_steps and "reasoning" not in merged_response:
            merged_response["reasoning"] = {
                "chain_of_thought": "".join(reasoning_steps)
            }
        
        return merged_response
    
    def _process_tool_call_delta(self, tool_calls: List[Dict[str, Any]], event: Dict[str, Any]) -> None:
        """处理工具调用增量事件"""
        call_index = event.get("index", 0)
        
        # 确保有足够的工具调用槽位
        while len(tool_calls) <= call_index:
            tool_calls.append({
                "id": None,
                "type": "function",
                "function": {}
            })
        
        current_call = tool_calls[call_index]
        
        # 更新工具调用信息
        if "id" in event:
            current_call["id"] = event["id"]
        
        if "name" in event:
            if "function" not in current_call:
                current_call["function"] = {}
            current_call["function"]["name"] = event["name"]
        
        if "arguments" in event:
            if "function" not in current_call:
                current_call["function"] = {}
            existing_args = current_call["function"].get("arguments", "")
            current_call["function"]["arguments"] = existing_args + event["arguments"]
    
    def _process_tool_call_done(self, tool_calls: List[Dict[str, Any]], event: Dict[str, Any]) -> None:
        """处理工具调用完成事件"""
        call_index = event.get("index", 0)
        
        if call_index < len(tool_calls):
            current_call = tool_calls[call_index]
            
            # 更新最终的工具调用信息
            if "tool_call" in event:
                tool_call_info = event["tool_call"]
                if isinstance(tool_call_info, dict):
                    if "id" in tool_call_info:
                        current_call["id"] = tool_call_info["id"]
                    if "function" in tool_call_info:
                        function_info = tool_call_info["function"]
                        if isinstance(function_info, dict):
                            if "function" not in current_call:
                                current_call["function"] = {}
                            current_call["function"].update(function_info)
    
    def _extract_tool_calls_from_stream_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从流式事件中提取工具调用"""
        tool_calls: List[Dict[str, Any]] = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            event_type = event.get("type")
            
            if event_type == "response.tool_call.delta":
                self._process_tool_call_delta(tool_calls, event)
            elif event_type == "response.tool_call.done":
                self._process_tool_call_done(tool_calls, event)
        
        # 过滤掉不完整的工具调用
        complete_calls = []
        for call in tool_calls:
            if (call.get("id") and 
                call.get("function", {}).get("name") and 
                call.get("function", {}).get("arguments")):
                complete_calls.append(call)
        
        return complete_calls
    
    def _extract_usage_from_stream_events(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """从流式事件中提取使用信息"""
        for event in events:
            if not isinstance(event, dict):
                continue
            
            event_type = event.get("type")
            
            if event_type == "response.done":
                usage = event.get("usage")
                if usage and isinstance(usage, dict):
                    return usage  # type: ignore
        
        return None
    
    def _extract_reasoning_from_stream_events(self, events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """从流式事件中提取推理信息"""
        reasoning_steps = []
        reasoning_info = {}
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            event_type = event.get("type")
            
            if event_type == "response.reasoning.delta":
                delta = event.get("delta", "")
                if delta and isinstance(delta, str):
                    reasoning_steps.append(delta)
            elif event_type == "response.reasoning.done":
                reasoning = event.get("reasoning", {})
                if reasoning and isinstance(reasoning, dict):
                    reasoning_info.update(reasoning)
        
        if reasoning_steps:
            reasoning_info["chain_of_thought"] = "".join(reasoning_steps)
        
        return reasoning_info if reasoning_info else None
    
    def _validate_responses_stream_event(self, event: Dict[str, Any], index: int) -> List[str]:
        """验证单个Responses API流式事件"""
        errors = []
        
        if not isinstance(event, dict):
            errors.append(f"流式事件 {index} 必须是字典")
            return errors
        
        # 检查type字段
        event_type = event.get("type")
        if not event_type:
            errors.append(f"流式事件 {index} 缺少type字段")
            return errors
        
        # 验证已知的事件类型
        valid_types = [
            "response.created",
            "response.output_text.delta", 
            "response.output_text.done",
            "response.tool_call.delta",
            "response.tool_call.done", 
            "response.reasoning.delta",
            "response.reasoning.done",
            "response.done",
            "error"
        ]
        
        if event_type not in valid_types:
            errors.append(f"流式事件 {index} 的type字段值无效: {event_type}")
        
        # 根据事件类型进行特定验证
        if event_type == "response.output_text.delta":
            self._validate_text_delta_event(event, index, errors)
        elif event_type == "response.output_text.done":
            self._validate_text_done_event(event, index, errors)
        elif event_type == "response.tool_call.delta":
            self._validate_tool_call_delta_event(event, index, errors)
        elif event_type == "response.tool_call.done":
            self._validate_tool_call_done_event(event, index, errors)
        elif event_type == "response.reasoning.delta":
            self._validate_reasoning_delta_event(event, index, errors)
        elif event_type == "response.reasoning.done":
            self._validate_reasoning_done_event(event, index, errors)
        elif event_type == "response.done":
            self._validate_response_done_event(event, index, errors)
        
        return errors
    
    def _validate_text_delta_event(self, event: Dict[str, Any], index: int, errors: List[str]) -> None:
        """验证文本增量事件"""
        delta = event.get("delta")
        if delta is not None and not isinstance(delta, str):
            errors.append(f"流式事件 {index} 的delta字段必须是字符串")
    
    def _validate_text_done_event(self, event: Dict[str, Any], index: int, errors: List[str]) -> None:
        """验证文本完成事件"""
        text = event.get("text")
        if text is not None and not isinstance(text, str):
            errors.append(f"流式事件 {index} 的text字段必须是字符串")
    
    def _validate_tool_call_delta_event(self, event: Dict[str, Any], index: int, errors: List[str]) -> None:
        """验证工具调用增量事件"""
        # 验证index字段
        call_index = event.get("index")
        if call_index is not None and not isinstance(call_index, int):
            errors.append(f"流式事件 {index} 的index字段必须是整数")
        
        # 验证id字段
        call_id = event.get("id")
        if call_id is not None and not isinstance(call_id, str):
            errors.append(f"流式事件 {index} 的id字段必须是字符串")
        
        # 验证name字段
        name = event.get("name")
        if name is not None and not isinstance(name, str):
            errors.append(f"流式事件 {index} 的name字段必须是字符串")
        
        # 验证arguments字段
        arguments = event.get("arguments")
        if arguments is not None and not isinstance(arguments, str):
            errors.append(f"流式事件 {index} 的arguments字段必须是字符串")
    
    def _validate_tool_call_done_event(self, event: Dict[str, Any], index: int, errors: List[str]) -> None:
        """验证工具调用完成事件"""
        # 验证index字段
        call_index = event.get("index")
        if call_index is not None and not isinstance(call_index, int):
            errors.append(f"流式事件 {index} 的index字段必须是整数")
        
        # 验证tool_call字段
        tool_call = event.get("tool_call")
        if tool_call is not None and not isinstance(tool_call, dict):
            errors.append(f"流式事件 {index} 的tool_call字段必须是字典")
    
    def _validate_reasoning_delta_event(self, event: Dict[str, Any], index: int, errors: List[str]) -> None:
        """验证推理增量事件"""
        delta = event.get("delta")
        if delta is not None and not isinstance(delta, str):
            errors.append(f"流式事件 {index} 的delta字段必须是字符串")
    
    def _validate_reasoning_done_event(self, event: Dict[str, Any], index: int, errors: List[str]) -> None:
        """验证推理完成事件"""
        reasoning = event.get("reasoning")
        if reasoning is not None and not isinstance(reasoning, dict):
            errors.append(f"流式事件 {index} 的reasoning字段必须是字典")
    
    def _validate_response_done_event(self, event: Dict[str, Any], index: int, errors: List[str]) -> None:
        """验证响应完成事件"""
        # 验证response字段
        response = event.get("response")
        if response is not None and not isinstance(response, dict):
            errors.append(f"流式事件 {index} 的response字段必须是字典")
        
        # 验证usage字段
        usage = event.get("usage")
        if usage is not None and not isinstance(usage, dict):
            errors.append(f"流式事件 {index} 的usage字段必须是字典")
    
    def _is_complete_event(self, event: Dict[str, Any]) -> bool:
        """检查事件是否为完成事件"""
        event_type = event.get("type")
        return event_type in ["response.done", "error"]
    
    def create_stream_chunk(
        self, 
        event_type: str,
        content: Optional[str] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建Responses API流式响应块"""
        chunk = {
            "type": event_type,
            **kwargs
        }
        
        # 根据事件类型添加特定字段
        if event_type == "response.output_text.delta" and content:
            chunk["delta"] = content
        elif event_type == "response.output_text.done" and content:
            chunk["text"] = content
        elif event_type == "response.tool_call.delta" and tool_call:
            chunk.update(tool_call)
        elif event_type == "response.tool_call.done" and tool_call:
            chunk["tool_call"] = tool_call
        elif event_type == "response.reasoning.delta" and reasoning:
            chunk["delta"] = reasoning.get("delta", "")
        elif event_type == "response.reasoning.done" and reasoning:
            chunk["reasoning"] = reasoning
        elif event_type == "response.done":
            if content:
                chunk["response"] = {"output_text": content}
            if reasoning:
                if "response" not in chunk:
                    chunk["response"] = {}
                chunk["response"]["reasoning"] = reasoning.get("chain_of_thought", "") if isinstance(reasoning, dict) else reasoning
        
        return chunk
    
    def format_stream_event_for_sse(self, chunk: Dict[str, Any]) -> str:
        """格式化流式事件为Server-Sent Events格式"""
        try:
            json_str = json.dumps(chunk, ensure_ascii=False)
            return f"data: {json_str}\n\n"
        except Exception as e:
            self.logger.error(f"格式化流式事件失败: {e}")
            return "data: {}\n\n"
    
    def convert_from_openai_stream_events(self, openai_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从OpenAI Chat Completions流式事件转换为Responses API格式
        
        Args:
            openai_events: OpenAI格式的流式事件列表
            
        Returns:
            List[Dict[str, Any]]: Responses API格式的流式事件列表
        """
        responses_events = []
        accumulated_text = ""
        
        for openai_event in openai_events:
            if not isinstance(openai_event, dict):
                continue
            
            # 提取choices中的delta内容
            choices = openai_event.get("choices", [])
            if not choices:
                continue
            
            choice = choices[0]
            delta = choice.get("delta", {})
            
            # 处理文本增量
            content = delta.get("content")
            if content and isinstance(content, str):
                accumulated_text += content
                responses_events.append({
                    "type": "response.output_text.delta",
                    "delta": content
                })
            
            # 处理工具调用增量
            tool_calls_delta = delta.get("tool_calls", [])
            for tool_call_delta in tool_calls_delta:
                if isinstance(tool_call_delta, dict):
                    responses_events.append({
                        "type": "response.tool_call.delta",
                        "index": tool_call_delta.get("index", 0),
                        **tool_call_delta
                    })
            
            # 检查是否为完成事件
            finish_reason = choice.get("finish_reason")
            if finish_reason:
                # 创建文本完成事件
                if accumulated_text:
                    responses_events.append({
                        "type": "response.output_text.done",
                        "text": accumulated_text
                    })
                
                # 创建响应完成事件
                responses_events.append({
                    "type": "response.done",
                    "response": {
                        "output_text": accumulated_text,
                        "finish_reason": finish_reason
                    }
                })
                
                # 添加使用信息（如果有）
                usage = openai_event.get("usage")
                if usage:
                    responses_events[-1]["usage"] = usage
        
        return responses_events
    
    def convert_to_openai_stream_events(self, responses_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从Responses API流式事件转换为OpenAI Chat Completions格式
        
        Args:
            responses_events: Responses API格式的流式事件列表
            
        Returns:
            List[Dict[str, Any]]: OpenAI格式的流式事件列表
        """
        openai_events = []
        accumulated_text = ""
        
        for responses_event in responses_events:
            if not isinstance(responses_event, dict):
                continue
            
            event_type = responses_event.get("type")
            
            # 处理文本增量
            if event_type == "response.output_text.delta":
                delta = responses_event.get("delta", "")
                if delta and isinstance(delta, str):
                    accumulated_text += delta
                    openai_events.append({
                        "object": "chat.completion.chunk",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": delta}
                        }]
                    })
            
            # 处理工具调用增量
            elif event_type == "response.tool_call.delta":
                tool_call_delta = {
                    "index": responses_event.get("index", 0)
                }
                if "id" in responses_event:
                    tool_call_delta["id"] = responses_event["id"]
                if "name" in responses_event:
                    tool_call_delta["function"] = {"name": responses_event["name"]}
                if "arguments" in responses_event:
                    if "function" not in tool_call_delta:
                        tool_call_delta["function"] = {}
                    tool_call_delta["function"]["arguments"] = responses_event["arguments"]
                
                openai_events.append({
                    "object": "chat.completion.chunk",
                    "choices": [{
                        "index": 0,
                        "delta": {"tool_calls": [tool_call_delta]}
                    }]
                })
            
            # 处理完成事件
            elif event_type == "response.done":
                finish_reason = responses_event.get("response", {}).get("finish_reason", "stop")
                openai_events.append({
                    "object": "chat.completion.chunk",
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": finish_reason
                    }]
                })
                
                # 添加使用信息（如果有）
                usage = responses_event.get("usage")
                if usage:
                    openai_events[-1]["usage"] = usage
        
        return openai_events