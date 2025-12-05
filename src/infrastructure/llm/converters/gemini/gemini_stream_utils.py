"""Gemini流式响应处理工具

专门处理Gemini API的流式响应功能。
"""

import json
from typing import Dict, Any, List, Optional
from src.services.logger.injection import get_logger
from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils


class GeminiStreamUtils(BaseStreamUtils):
    """Gemini流式响应处理工具类"""
    
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
            # Gemini流式响应通常是JSON格式
            if not event_line.strip():
                return None
            
            # 尝试直接解析JSON
            return json.loads(event_line)
        except json.JSONDecodeError:
            self.logger.warning(f"无法解析Gemini流式事件JSON: {event_line}")
            return None
        except Exception as e:
            self.logger.error(f"解析Gemini流式事件失败: {e}")
            return None
    
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理流式事件列表
        
        Args:
            events: 流式事件列表
            
        Returns:
            Dict[str, Any]: 合并后的响应数据
        """
        merged_response = {
            "candidates": []
        }
        
        current_candidate = None
        current_parts = []
        
        for event in events:
            try:
                # 处理候选内容
                if "candidates" in event:
                    for candidate in event["candidates"]:
                        if current_candidate is None:
                            current_candidate = candidate.copy()
                            current_candidate["content"] = {"parts": []}
                        else:
                            # 合并候选信息
                            if "finishReason" in candidate:
                                current_candidate["finishReason"] = candidate["finishReason"]
                            if "index" in candidate:
                                current_candidate["index"] = candidate["index"]
                            if "safetyRatings" in candidate:
                                current_candidate["safetyRatings"] = candidate["safetyRatings"]
                        
                        # 处理内容部分
                        if "content" in candidate and "parts" in candidate["content"]:
                            for part in candidate["content"]["parts"]:
                                current_parts.append(part)
                
                # 处理使用元数据
                if "usageMetadata" in event:
                    merged_response["usageMetadata"] = event["usageMetadata"]
                
                # 处理模型信息
                if "model" in event:
                    merged_response["model"] = event["model"]
                
            except Exception as e:
                self.logger.error(f"处理流式事件失败: {e}")
                continue
        
        # 构建最终响应
        if current_candidate:
            current_candidate["content"]["parts"] = current_parts
            merged_response["candidates"].append(current_candidate)
        
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
                if "candidates" in event:
                    for candidate in event["candidates"]:
                        if "content" in candidate and "parts" in candidate["content"]:
                            for part in candidate["content"]["parts"]:
                                if "text" in part:
                                    text_parts.append(part["text"])
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
        
        # Gemini特定验证
        if "candidates" in event:
            candidates = event["candidates"]
            if not isinstance(candidates, list):
                errors.append(f"流式事件 {index} 的candidates字段必须是列表")
            else:
                for j, candidate in enumerate(candidates):
                    if not isinstance(candidate, dict):
                        errors.append(f"流式事件 {index} 的候选 {j} 必须是字典")
                        continue
                    
                    # 验证候选结构
                    if "content" in candidate:
                        content = candidate["content"]
                        if not isinstance(content, dict):
                            errors.append(f"流式事件 {index} 的候选 {j} 的content字段必须是字典")
                        elif "parts" in content:
                            parts = content["parts"]
                            if not isinstance(parts, list):
                                errors.append(f"流式事件 {index} 的候选 {j} 的parts字段必须是列表")
        
        return errors
    
    def _merge_single_event(self, merged: Dict[str, Any], event: Dict[str, Any]) -> None:
        """合并单个事件到响应中"""
        # 合并候选内容
        if "candidates" in event:
            if "candidates" not in merged:
                merged["candidates"] = []
            
            for candidate in event["candidates"]:
                # 查找对应的候选
                existing_candidate = None
                for existing in merged["candidates"]:
                    if existing.get("index") == candidate.get("index", 0):
                        existing_candidate = existing
                        break
                
                if existing_candidate is None:
                    # 创建新候选
                    existing_candidate = {
                        "content": {"parts": []},
                        "index": candidate.get("index", 0)
                    }
                    merged["candidates"].append(existing_candidate)
                
                # 合并内容部分
                if "content" in candidate and "parts" in candidate["content"]:
                    if "content" not in existing_candidate:
                        existing_candidate["content"] = {"parts": []}
                    
                    existing_candidate["content"]["parts"].extend(candidate["content"]["parts"])
                
                # 更新其他字段
                for key in ["finishReason", "safetyRatings"]:
                    if key in candidate:
                        existing_candidate[key] = candidate[key]
        
        # 合并其他字段
        for key in ["usageMetadata", "model"]:
            if key in event:
                merged[key] = event[key]
    
    def _extract_text_from_single_event(self, event: Dict[str, Any]) -> Optional[str]:
        """从单个事件中提取文本"""
        if "candidates" in event:
            for candidate in event["candidates"]:
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            return part["text"]
        return None
    
    def _extract_tool_call_from_single_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从单个事件中提取工具调用"""
        if "candidates" in event:
            for candidate in event["candidates"]:
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "functionCall" in part:
                            return part["functionCall"]
        return None
    
    def _is_complete_event(self, event: Dict[str, Any]) -> bool:
        """检查事件是否为完成事件"""
        if "candidates" in event:
            for candidate in event["candidates"]:
                finish_reason = candidate.get("finishReason")
                if finish_reason in ["STOP", "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER"]:
                    return True
        return False
    
    def extract_tool_calls_from_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从事件中提取工具调用"""
        tool_calls = []
        
        for event in events:
            tool_call = self._extract_tool_call_from_single_event(event)
            if tool_call:
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
    
    def extract_thoughts_from_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """从流式事件中提取思考过程
        
        Args:
            events: 流式事件列表
            
        Returns:
            List[str]: 思考过程列表
        """
        thoughts = []
        
        for event in events:
            try:
                if "candidates" in event:
                    for candidate in event["candidates"]:
                        if "content" in candidate and "parts" in candidate["content"]:
                            for part in candidate["content"]["parts"]:
                                if "thinking" in part:
                                    thoughts.append(part["thinking"])
            except Exception as e:
                self.logger.error(f"提取思考过程失败: {e}")
                continue
        
        return thoughts
    
    def create_stream_response(
        self, 
        content: str, 
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        finish_reason: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """创建流式响应结构"""
        parts: List[Dict[str, Any]] = [{"text": content}]
        
        if tool_calls:
            for tool_call in tool_calls:
                parts.append({"functionCall": tool_call})
        
        response = {
            "candidates": [
                {
                    "content": {"parts": parts},
                    "finishReason": finish_reason or "STOP",
                    "index": 0
                }
            ]
        }
        
        # 添加其他字段
        for key, value in kwargs.items():
            response[key] = value
        
        return response