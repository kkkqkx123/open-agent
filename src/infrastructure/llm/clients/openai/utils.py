"""OpenAI 客户端工具函数"""

from typing import Any, Dict, Optional, Sequence

from langchain_core.messages import BaseMessage, AIMessage
from ...models import LLMResponse, TokenUsage


class ResponseConverter:
    """响应转换工具类"""
    
    @staticmethod
    def convert_langchain_response(response: Any) -> LLMResponse:
        """
        转换 LangChain 响应为统一格式
        
        Args:
            response: LangChain 响应
            
        Returns:
            LLMResponse: 统一格式的响应
        """
        # 提取内容
        content = ResponseConverter._extract_content(response)
        
        # 提取 Token 使用情况
        token_usage = ResponseConverter._extract_token_usage(response)
        
        # 提取函数调用信息
        function_call = ResponseConverter._extract_function_call(response)
        
        # 提取完成原因
        finish_reason = ResponseConverter._extract_finish_reason(response)
        
        # 创建响应对象
        return LLMResponse(
            content=content,
            message=response,
            token_usage=token_usage,
            model=getattr(response, "model", "unknown"),
            finish_reason=finish_reason,
            function_call=function_call,
            metadata=getattr(response, "response_metadata", {}),
        )
    
    @staticmethod
    def convert_responses_response(response: Dict[str, Any]) -> LLMResponse:
        """
        转换 Responses API 响应为统一格式
        
        Args:
            response: Responses API 响应
            
        Returns:
            LLMResponse: 统一格式的响应
        """
        # 提取输出内容
        content = ResponseConverter._extract_output_text(response)
        
        # 提取 Token 使用情况
        token_usage = ResponseConverter._extract_responses_token_usage(response)
        
        # 提取函数调用
        function_call = ResponseConverter._extract_responses_function_call(response)
        
        # 提取完成原因
        finish_reason = ResponseConverter._extract_responses_finish_reason(response)
        
        # 创建 LangChain 消息
        message = AIMessage(content=content)
        
        # 确保消息对象兼容 LLMResponse 期望的类型
        return LLMResponse(
            content=content,
            message=message,
            token_usage=token_usage,
            model=response.get("model", "unknown"),
            finish_reason=finish_reason,
            function_call=function_call,
            metadata={
                "response_id": response.get("id"),
                "object": response.get("object"),
                "created_at": response.get("created_at"),
                "output_items": response.get("output", []),
            },
        )
    
    @staticmethod
    def _extract_content(response: Any) -> str:
        """提取响应内容"""
        if hasattr(response, "content"):
            content = response.content
            
            # 如果内容是字符串，直接返回
            if isinstance(content, str):
                return content
            
            # 如果内容是列表，提取文本内容
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                return "".join(text_parts)
            
            # 其他类型转换为字符串
            return str(content)
        
        return str(response)
    
    @staticmethod
    def _extract_token_usage(response: Any) -> TokenUsage:
        """提取 Token 使用情况"""
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            return TokenUsage(
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
        elif hasattr(response, "response_metadata") and response.response_metadata:
            metadata = response.response_metadata
            if "token_usage" in metadata:
                usage = metadata["token_usage"]
                return TokenUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                )
        
        return TokenUsage()
    
    @staticmethod
    def _extract_function_call(response: Any) -> Optional[dict[str, Any]]:
        """提取函数调用信息"""
        if (
            hasattr(response, "additional_kwargs")
            and "function_call" in response.additional_kwargs
        ):
            function_call = response.additional_kwargs["function_call"]
            if isinstance(function_call, dict):
                return function_call
        return None
    
    @staticmethod
    def _extract_finish_reason(response: Any) -> Optional[str]:
        """提取完成原因"""
        if hasattr(response, "response_metadata") and response.response_metadata:
            metadata = response.response_metadata
            finish_reason = metadata.get("finish_reason")
            if isinstance(finish_reason, str):
                return finish_reason
        return None
    
    @staticmethod
    def _extract_output_text(response: Dict[str, Any]) -> str:
        """提取 Responses API 输出文本"""
        output_items = response.get("output", [])
        
        for item in output_items:
            if item.get("type") == "message":
                content = item.get("content", [])
                for content_item in content:
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text", "")
                        return str(text) if text is not None else ""
        
        return ""
    
    @staticmethod
    def _extract_responses_token_usage(response: Dict[str, Any]) -> TokenUsage:
        """提取 Responses API Token 使用情况"""
        usage = response.get("usage", {})
        
        return TokenUsage(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
    
    @staticmethod
    def _extract_responses_function_call(
        response: Dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """提取 Responses API 函数调用信息"""
        output_items = response.get("output", [])
        
        for item in output_items:
            if item.get("type") == "function_call":
                return {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "arguments": item.get("arguments"),
                }
        
        return None
    
    @staticmethod
    def _extract_responses_finish_reason(response: Dict[str, Any]) -> Optional[str]:
        """提取 Responses API 完成原因"""
        return response.get("status") or response.get("finish_reason")


class MessageConverter:
    """消息转换工具类"""
    
    @staticmethod
    def messages_to_input(messages: Sequence[BaseMessage]) -> str:
        """
        将消息列表转换为 input 字符串（用于 Responses API）
        
        Args:
            messages: LangChain 消息列表
            
        Returns:
            str: 转换后的 input 字符串
        """
        input_parts = []
        
        for message in messages:
            if hasattr(message, "content"):
                content = str(message.content)
                if hasattr(message, "type"):
                    if message.type == "system":
                        input_parts.append(f"System: {content}")
                    elif message.type == "human":
                        input_parts.append(f"User: {content}")
                    elif message.type == "ai":
                        input_parts.append(f"Assistant: {content}")
                else:
                    # 根据消息类型判断
                    if hasattr(message, 'type'):
                        if message.type == "system":
                            input_parts.append(f"System: {content}")
                        elif message.type == "human":
                            input_parts.append(f"User: {content}")
                        elif message.type == "ai":
                            input_parts.append(f"Assistant: {content}")
                        else:
                            input_parts.append(content)
                    else:
                        input_parts.append(content)
        
        return "\n".join(input_parts)