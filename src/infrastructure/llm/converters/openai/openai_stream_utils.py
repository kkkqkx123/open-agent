"""OpenAI流式处理工具类

提供OpenAI API的流式响应处理功能。
"""

from typing import Dict, Any, List, Optional
import json
from src.services.logger.injection import get_logger
from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils


class OpenAIStreamUtils(BaseStreamUtils):
    """OpenAI流式处理工具类
    
    提供OpenAI API特定的流式响应处理功能。
    """
    
    def __init__(self) -> None:
        """初始化OpenAI流式工具"""
        super().__init__()
    
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析OpenAI流式事件行"""
        return self._parse_sse_event(event_line)
    
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理OpenAI流式事件列表"""
        if not events:
            return {}
        
        # 合并所有事件
        merged_response = self._merge_openai_stream_events(events)
        
        # 提取完整内容
        content = self.extract_text_from_stream_events(events)
        if content:
            merged_response["content"] = content
        
        # 提取工具调用
        tool_calls = self._extract_tool_calls_from_stream_events(events)
        if tool_calls:
            merged_response["tool_calls"] = tool_calls
        
        # 提取使用信息
        usage = self._extract_usage_from_stream_events(events)
        if usage:
            merged_response["usage"] = usage
        
        return merged_response
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从OpenAI流式事件中提取文本"""
        text_parts = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            # 检查是否为完成事件
            if event.get("type") == "done":
                break
            
            # 提取choices中的delta内容
            choices = event.get("choices", [])
            if not choices:
                continue
            
            choice = choices[0]  # OpenAI通常只有一个choice
            delta = choice.get("delta", {})
            
            # 提取文本内容
            content = delta.get("content")
            if content and isinstance(content, str):
                text_parts.append(content)
        
        return "".join(text_parts)
    
    def validate_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """验证OpenAI流式事件"""
        errors = []
        
        if not isinstance(events, list):
            errors.append("流式事件必须是列表格式")
            return errors
        
        if not events:
            errors.append("流式事件列表不能为空")
            return errors
        
        for i, event in enumerate(events):
            event_errors = self._validate_openai_stream_event(event, i)
            errors.extend(event_errors)
        
        return errors
    
    def _merge_openai_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并OpenAI流式事件"""
        merged_response = {}
        
        # 从第一个事件获取基本信息
        if events and isinstance(events[0], dict):
            first_event = events[0]
            
            # 复制基本字段
            for field in ["id", "object", "created", "model"]:
                if field in first_event:
                    merged_response[field] = first_event[field]
        
        # 合并choices
        merged_choices = []
        current_choice = None
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            choices = event.get("choices", [])
            if not choices:
                continue
            
            choice = choices[0]
            choice_index = choice.get("index", 0)
            
            # 确保有足够的choice槽位
            while len(merged_choices) <= choice_index:
                merged_choices.append({
                    "index": choice_index,
                    "message": {},
                    "finish_reason": None
                })
            
            # 合并delta到message
            delta = choice.get("delta", {})
            if delta:
                if not merged_choices[choice_index]["message"]:
                    merged_choices[choice_index]["message"] = {}
                
                # 合并delta内容
                for key, value in delta.items():
                    if key == "content":
                        # 内容需要累加
                        existing = merged_choices[choice_index]["message"].get("content", "")
                        merged_choices[choice_index]["message"]["content"] = existing + (value or "")
                    elif key == "tool_calls":
                        # 工具调用需要特殊处理
                        self._merge_tool_calls_delta(merged_choices[choice_index]["message"], value)
                    else:
                        # 其他字段直接设置
                        merged_choices[choice_index]["message"][key] = value
            
            # 设置finish_reason
            finish_reason = choice.get("finish_reason")
            if finish_reason:
                merged_choices[choice_index]["finish_reason"] = finish_reason
        
        merged_response["choices"] = merged_choices
        return merged_response
    
    def _merge_tool_calls_delta(self, message: Dict[str, Any], tool_calls_delta: List[Dict[str, Any]]) -> None:
        """合并工具调用delta"""
        if not isinstance(tool_calls_delta, list):
            return
        
        # 确保message中有tool_calls字段
        if "tool_calls" not in message:
            message["tool_calls"] = []
        
        for delta_call in tool_calls_delta:
            if not isinstance(delta_call, dict):
                continue
            
            call_index = delta_call.get("index", 0)
            
            # 确保有足够的tool_calls槽位
            while len(message["tool_calls"]) <= call_index:
                message["tool_calls"].append({
                    "id": None,
                    "type": "function",
                    "function": {}
                })
            
            current_call = message["tool_calls"][call_index]
            
            # 合并delta
            if "id" in delta_call:
                current_call["id"] = delta_call["id"]
            
            if "type" in delta_call:
                current_call["type"] = delta_call["type"]
            
            # 处理function delta
            function_delta = delta_call.get("function", {})
            if function_delta:
                if "function" not in current_call:
                    current_call["function"] = {}
                
                for key, value in function_delta.items():
                    if key == "arguments":
                        # 参数需要累加
                        existing = current_call["function"].get("arguments", "")
                        current_call["function"]["arguments"] = existing + (value or "")
                    else:
                        current_call["function"][key] = value
    
    def _extract_tool_calls_from_stream_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从流式事件中提取工具调用"""
        tool_calls = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
            
            choices = event.get("choices", [])
            if not choices:
                continue
            
            choice = choices[0]
            delta = choice.get("delta", {})
            
            # 提取工具调用delta
            tool_calls_delta = delta.get("tool_calls", [])
            if not isinstance(tool_calls_delta, list):
                continue
            
            for delta_call in tool_calls_delta:
                if not isinstance(delta_call, dict):
                    continue
                
                call_index = delta_call.get("index", 0)
                
                # 确保有足够的槽位
                while len(tool_calls) <= call_index:
                    tool_calls.append({
                        "id": None,
                        "type": "function",
                        "function": {}
                    })
                
                current_call = tool_calls[call_index]
                
                # 合并delta
                if "id" in delta_call:
                    current_call["id"] = delta_call["id"]
                
                if "type" in delta_call:
                    current_call["type"] = delta_call["type"]
                
                function_delta = delta_call.get("function", {})
                if function_delta:
                    if "function" not in current_call:
                        current_call["function"] = {}
                    
                    for key, value in function_delta.items():
                        if key == "arguments":
                            existing = current_call["function"].get("arguments", "")
                            current_call["function"]["arguments"] = existing + (value or "")
                        else:
                            current_call["function"][key] = value
        
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
            
            usage = event.get("usage")
            if usage and isinstance(usage, dict):
                return usage
        
        return None
    
    def _validate_openai_stream_event(self, event: Dict[str, Any], index: int) -> List[str]:
        """验证单个OpenAI流式事件"""
        errors = []
        
        if not isinstance(event, dict):
            errors.append(f"流式事件 {index} 必须是字典")
            return errors
        
        # 检查基本字段
        if "object" in event:
            object_type = event["object"]
            if object_type not in ["chat.completion.chunk"]:
                errors.append(f"流式事件 {index} 的object字段值无效: {object_type}")
        
        # 验证choices字段
        if "choices" in event:
            choices = event["choices"]
            if not isinstance(choices, list):
                errors.append(f"流式事件 {index} 的choices字段必须是列表")
            else:
                for i, choice in enumerate(choices):
                    choice_errors = self._validate_stream_choice(choice, index, i)
                    errors.extend(choice_errors)
        
        return errors
    
    def _validate_stream_choice(self, choice: Dict[str, Any], event_index: int, choice_index: int) -> List[str]:
        """验证流式事件中的choice"""
        errors = []
        
        if not isinstance(choice, dict):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 必须是字典")
            return errors
        
        # 验证index字段
        if "index" in choice and not isinstance(choice["index"], int):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的index字段必须是整数")
        
        # 验证delta字段
        delta = choice.get("delta")
        if delta is not None:
            if not isinstance(delta, dict):
                errors.append(f"流式事件 {event_index} 的choice {choice_index} 的delta字段必须是字典")
            else:
                delta_errors = self._validate_stream_delta(delta, event_index, choice_index)
                errors.extend(delta_errors)
        
        # 验证finish_reason字段
        finish_reason = choice.get("finish_reason")
        if finish_reason is not None:
            valid_reasons = ["stop", "length", "tool_calls", "content_filter", "function_call", None]
            if finish_reason not in valid_reasons:
                errors.append(f"流式事件 {event_index} 的choice {choice_index} 的finish_reason值无效: {finish_reason}")
        
        return errors
    
    def _validate_stream_delta(self, delta: Dict[str, Any], event_index: int, choice_index: int) -> List[str]:
        """验证流式事件中的delta"""
        errors = []
        
        # 验证content字段
        content = delta.get("content")
        if content is not None and not isinstance(content, str):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的delta.content字段必须是字符串")
        
        # 验证role字段
        role = delta.get("role")
        if role is not None and role != "assistant":
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的delta.role字段必须是'assistant'")
        
        # 验证tool_calls字段
        tool_calls = delta.get("tool_calls")
        if tool_calls is not None:
            if not isinstance(tool_calls, list):
                errors.append(f"流式事件 {event_index} 的choice {choice_index} 的delta.tool_calls字段必须是列表")
            else:
                for i, tool_call in enumerate(tool_calls):
                    tool_call_errors = self._validate_stream_tool_call(tool_call, event_index, choice_index, i)
                    errors.extend(tool_call_errors)
        
        return errors
    
    def _validate_stream_tool_call(
        self, 
        tool_call: Dict[str, Any], 
        event_index: int, 
        choice_index: int, 
        call_index: int
    ) -> List[str]:
        """验证流式事件中的工具调用"""
        errors = []
        
        if not isinstance(tool_call, dict):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的tool_call {call_index} 必须是字典")
            return errors
        
        # 验证index字段
        if "index" in tool_call and not isinstance(tool_call["index"], int):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的tool_call {call_index} 的index字段必须是整数")
        
        # 验证id字段
        call_id = tool_call.get("id")
        if call_id is not None and not isinstance(call_id, str):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的tool_call {call_index} 的id字段必须是字符串")
        
        # 验证type字段
        call_type = tool_call.get("type")
        if call_type is not None and call_type != "function":
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的tool_call {call_index} 的type字段必须是'function'")
        
        # 验证function字段
        function = tool_call.get("function")
        if function is not None:
            if not isinstance(function, dict):
                errors.append(f"流式事件 {event_index} 的choice {choice_index} 的tool_call {call_index} 的function字段必须是字典")
            else:
                function_errors = self._validate_stream_function(function, event_index, choice_index, call_index)
                errors.extend(function_errors)
        
        return errors
    
    def _validate_stream_function(
        self, 
        function: Dict[str, Any], 
        event_index: int, 
        choice_index: int, 
        call_index: int
    ) -> List[str]:
        """验证流式事件中的function"""
        errors = []
        
        # 验证name字段
        name = function.get("name")
        if name is not None and not isinstance(name, str):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的tool_call {call_index} 的function.name字段必须是字符串")
        
        # 验证arguments字段
        arguments = function.get("arguments")
        if arguments is not None and not isinstance(arguments, str):
            errors.append(f"流式事件 {event_index} 的choice {choice_index} 的tool_call {call_index} 的function.arguments字段必须是字符串")
        
        return errors
    
    def _is_complete_event(self, event: Dict[str, Any]) -> bool:
        """检查事件是否为完成事件"""
        if event.get("type") == "done":
            return True
        
        choices = event.get("choices", [])
        if choices:
            choice = choices[0]
            finish_reason = choice.get("finish_reason")
            return finish_reason is not None and finish_reason != "null"
        
        return False
    
    def create_stream_chunk(
        self, 
        content: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        finish_reason: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建流式响应块"""
        chunk = {
            "object": "chat.completion.chunk",
            **kwargs
        }
        
        # 构建choice
        choice = {"index": 0, "delta": {}}
        
        if content:
            choice["delta"]["content"] = content
        
        if tool_calls:
            choice["delta"]["tool_calls"] = tool_calls
        
        if finish_reason:
            choice["finish_reason"] = finish_reason
        
        chunk["choices"] = [choice]
        
        return chunk
    
    def format_stream_event_for_sse(self, chunk: Dict[str, Any]) -> str:
        """格式化流式事件为Server-Sent Events格式"""
        try:
            json_str = json.dumps(chunk, ensure_ascii=False)
            return f"data: {json_str}\n\n"
        except Exception as e:
            self.logger.error(f"格式化流式事件失败: {e}")
            return "data: {}\n\n"