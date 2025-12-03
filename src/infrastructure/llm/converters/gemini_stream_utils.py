"""Gemini流式响应处理工具

专门处理Gemini API的流式响应，包括Server-Sent Events格式解析等。
"""

from typing import Dict, Any, List, Optional, Union, Iterator
import json
from src.services.logger import get_logger


class GeminiStreamUtils:
    """Gemini流式响应处理工具类"""
    
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
        response: Dict[str, Any] = {
            "candidates": []
        }
        
        current_candidate = None
        current_parts = []
        
        for event in events:
            if "candidates" in event:
                candidates = event["candidates"]
                if candidates:
                    candidate = candidates[0]
                    
                    # 如果有新的候选，保存当前的
                    if current_candidate and current_parts:
                        current_candidate["content"]["parts"] = current_parts
                        response["candidates"].append(current_candidate)
                        current_parts = []
                    
                    # 开始新的候选
                    current_candidate = {
                        "content": candidate.get("content", {"parts": []}),
                        "finishReason": candidate.get("finishReason"),
                        "index": candidate.get("index", 0),
                        "safetyRatings": candidate.get("safetyRatings", [])
                    }
                    
                    # 处理内容部分
                    if "content" in candidate and "parts" in candidate["content"]:
                        current_parts = candidate["content"]["parts"]
            
            # 处理使用统计
            if "usageMetadata" in event:
                response["usageMetadata"] = event["usageMetadata"]
        
        # 添加最后一个候选
        if current_candidate and current_parts:
            current_candidate["content"]["parts"] = current_parts
            response["candidates"].append(current_candidate)
        
        return response
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从流式事件中提取文本内容
        
        Args:
            events: 流式事件列表
            
        Returns:
            str: 提取的文本内容
        """
        text_parts = []
        
        for event in events:
            if "candidates" in event:
                candidates = event["candidates"]
                if candidates:
                    candidate = candidates[0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                text_parts.append(part["text"])
        
        return "".join(text_parts)
    
    def extract_tool_calls_from_stream_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从流式事件中提取工具调用
        
        Args:
            events: 流式事件列表
            
        Returns:
            List[Dict[str, Any]]: 工具调用列表
        """
        tool_calls = []
        
        for event in events:
            if "candidates" in event:
                candidates = event["candidates"]
                if candidates:
                    candidate = candidates[0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "functionCall" in part:
                                tool_call = self._extract_single_tool_call(part["functionCall"])
                                if tool_call:
                                    tool_calls.append(tool_call)
        
        return tool_calls
    
    def _extract_single_tool_call(self, function_call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取单个工具调用"""
        try:
            tool_call = {
                "id": f"call_{hash(str(function_call))}",  # Gemini不提供ID，生成一个
                "type": "function",
                "function": {
                    "name": function_call.get("name", ""),
                    "arguments": function_call.get("args", {})
                }
            }
            
            # 验证必需字段
            function_name = tool_call["function"]["name"]
            if not function_name:
                self.logger.warning("工具调用缺少名称")
                return None
            
            return tool_call
        except Exception as e:
            self.logger.error(f"提取工具调用失败: {e}")
            return None
    
    def extract_thoughts_from_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """从流式事件中提取思考过程
        
        Args:
            events: 流式事件列表
            
        Returns:
            List[str]: 思考过程列表
        """
        thoughts = []
        
        for event in events:
            if "candidates" in event:
                candidates = event["candidates"]
                if candidates:
                    candidate = candidates[0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "thought" in part:
                                thoughts.append(part["thought"])
        
        return thoughts
    
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
        
        for i, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append(f"事件 {i} 必须是字典")
                continue
            
            # 验证基本结构
            if "candidates" in event:
                candidates = event["candidates"]
                if not isinstance(candidates, list):
                    errors.append(f"事件 {i} 的candidates字段必须是列表")
                elif len(candidates) > 0:
                    candidate_errors = self._validate_stream_candidate(candidates[0], i)
                    errors.extend(candidate_errors)
            
            # 验证使用统计
            if "usageMetadata" in event:
                usage_errors = self._validate_stream_usage_metadata(event["usageMetadata"], i)
                errors.extend(usage_errors)
        
        return errors
    
    def _validate_stream_candidate(self, candidate: Dict[str, Any], event_index: int) -> List[str]:
        """验证流式候选响应"""
        errors = []
        
        if not isinstance(candidate, dict):
            errors.append(f"事件 {event_index} 的候选必须是字典")
            return errors
        
        # 验证content字段
        if "content" in candidate:
            content = candidate["content"]
            if not isinstance(content, dict):
                errors.append(f"事件 {event_index} 的content必须是字典")
            elif "parts" in content:
                parts = content["parts"]
                if not isinstance(parts, list):
                    errors.append(f"事件 {event_index} 的content.parts必须是列表")
                else:
                    for j, part in enumerate(parts):
                        part_errors = self._validate_stream_part(part, event_index, j)
                        errors.extend(part_errors)
        
        # 验证finishReason字段
        if "finishReason" in candidate:
            finish_reason = candidate["finishReason"]
            valid_reasons = {"STOP", "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER"}
            if finish_reason not in valid_reasons:
                errors.append(f"事件 {event_index} 的finishReason无效: {finish_reason}")
        
        return errors
    
    def _validate_stream_part(self, part: Dict[str, Any], event_index: int, part_index: int) -> List[str]:
        """验证流式内容部分"""
        errors = []
        
        if not isinstance(part, dict):
            errors.append(f"事件 {event_index} 的部分 {part_index} 必须是字典")
            return errors
        
        # 检查至少有一个有效字段
        valid_fields = {"text", "inline_data", "functionCall", "functionResponse", "thought"}
        has_valid_field = any(field in part for field in valid_fields)
        
        if not has_valid_field:
            errors.append(f"事件 {event_index} 的部分 {part_index} 必须包含有效字段之一: {', '.join(valid_fields)}")
        
        return errors
    
    def _validate_stream_usage_metadata(self, usage_metadata: Dict[str, Any], event_index: int) -> List[str]:
        """验证流式使用统计"""
        errors = []
        
        if not isinstance(usage_metadata, dict):
            errors.append(f"事件 {event_index} 的usageMetadata必须是字典")
            return errors
        
        # 验证字段类型
        numeric_fields = ["promptTokenCount", "candidatesTokenCount", "totalTokenCount"]
        for field in numeric_fields:
            if field in usage_metadata:
                if not isinstance(usage_metadata[field], int) or usage_metadata[field] < 0:
                    errors.append(f"事件 {event_index} 的usageMetadata.{field}必须是非负整数")
        
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
    
    def process_openai_compatible_stream(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理OpenAI兼容格式的流式事件
        
        Args:
            events: OpenAI兼容格式的流式事件列表
            
        Returns:
            Dict[str, Any]: 转换为Gemini格式的响应
        """
        response: Dict[str, Any] = {
            "candidates": []
        }
        
        current_candidate: Dict[str, Any] = {
            "content": {"parts": []},
            "finishReason": None,
            "index": 0,
            "safetyRatings": []
        }
        
        for event in events:
            if "choices" in event:
                choices = event["choices"]
                if choices:
                    choice = choices[0]
                    delta = choice.get("delta", {})
                    
                    # 处理文本内容
                    if "content" in delta:
                        current_candidate["content"]["parts"].append({
                            "text": delta["content"]
                        })
                    
                    # 处理工具调用
                    if "tool_calls" in delta:
                        tool_calls = delta["tool_calls"]
                        if isinstance(tool_calls, list):
                            for tool_call_delta in tool_calls:
                                if isinstance(tool_call_delta, dict) and "function" in tool_call_delta:
                                    function_delta = tool_call_delta["function"]
                                    if isinstance(function_delta, dict) and ("name" in function_delta or "arguments" in function_delta):
                                        # 构建函数调用
                                        function_call = {
                                            "name": function_delta.get("name", ""),
                                            "args": json.loads(function_delta.get("arguments", "{}"))
                                        }
                                        current_candidate["content"]["parts"].append({
                                            "functionCall": function_call
                                        })
                    
                    # 处理思考过程
                    if "thoughts" in delta:
                        current_candidate["content"]["parts"].append({
                            "thought": delta["thoughts"]
                        })
                    
                    # 处理结束原因
                    if "finish_reason" in choice:
                        finish_reason_map = {
                            "stop": "STOP",
                            "length": "MAX_TOKENS",
                            "content_filter": "SAFETY",
                            "tool_calls": "STOP"
                        }
                        openai_reason = choice["finish_reason"]
                        current_candidate["finishReason"] = finish_reason_map.get(openai_reason, "OTHER")
            
            # 处理使用统计
            if "usage" in event:
                usage = event["usage"]
                if isinstance(usage, dict):
                    response["usageMetadata"] = {
                        "promptTokenCount": usage.get("prompt_tokens", 0),
                        "candidatesTokenCount": usage.get("completion_tokens", 0),
                        "totalTokenCount": usage.get("total_tokens", 0)
                    }
        
        # 添加候选响应
        if current_candidate["content"]["parts"]:
            response["candidates"].append(current_candidate)
        
        return response
    
    def convert_to_openai_compatible_stream(self, gemini_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """将Gemini流式事件转换为OpenAI兼容格式
        
        Args:
            gemini_event: Gemini流式事件
            
        Returns:
            Optional[Dict[str, Any]]: OpenAI兼容格式的事件
        """
        try:
            if "candidates" not in gemini_event:
                return None
            
            candidates = gemini_event["candidates"]
            if not candidates:
                return None
            
            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            # 构建OpenAI格式
            openai_event: Dict[str, Any] = {
                "choices": [{
                    "index": candidate.get("index", 0),
                    "delta": {},
                    "finish_reason": None
                }]
            }
            
            # 处理内容部分
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict):
                        if "text" in part:
                            openai_event["choices"][0]["delta"]["content"] = part["text"]
                        elif "functionCall" in part:
                            function_call = part["functionCall"]
                            tool_calls_list = [{
                                "id": f"call_{hash(str(function_call))}",
                                "type": "function",
                                "function": {
                                    "name": function_call.get("name", ""),
                                    "arguments": json.dumps(function_call.get("args", {}))
                                }
                            }]
                            openai_event["choices"][0]["delta"]["tool_calls"] = tool_calls_list  # type: ignore
                        elif "thought" in part:
                            openai_event["choices"][0]["delta"]["thoughts"] = part["thought"]
            
            # 处理结束原因
            finish_reason = candidate.get("finishReason")
            if finish_reason:
                reason_map = {
                    "STOP": "stop",
                    "MAX_TOKENS": "length",
                    "SAFETY": "content_filter",
                    "RECITATION": "content_filter",
                    "OTHER": "stop"
                }
                openai_event["choices"][0]["finish_reason"] = reason_map.get(finish_reason, "stop")
            
            # 处理使用统计
            if "usageMetadata" in gemini_event:
                usage = gemini_event["usageMetadata"]
                if isinstance(usage, dict):
                    openai_event["usage"] = {
                        "prompt_tokens": usage.get("promptTokenCount", 0),
                        "completion_tokens": usage.get("candidatesTokenCount", 0),
                        "total_tokens": usage.get("totalTokenCount", 0)
                    }
            
            return openai_event
        except Exception as e:
            self.logger.error(f"转换Gemini流式事件失败: {e}")
            return None