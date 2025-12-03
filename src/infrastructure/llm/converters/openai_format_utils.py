"""OpenAI格式转换工具类

提供OpenAI API的格式转换功能。
"""

from typing import Dict, Any, List, Union, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

from src.infrastructure.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from src.infrastructure.llm.converters.base.base_provider_utils import BaseProviderUtils


class OpenAIFormatUtils(BaseProviderUtils):
    """OpenAI格式转换工具类"""
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "openai"
    
    def convert_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为OpenAI API请求格式"""
        openai_messages = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                openai_messages.append({
                    "role": "user",
                    "content": message.content,
                    **({"name": message.name} if message.name else {})
                })
            elif isinstance(message, AIMessage):
                msg_dict = {
                    "role": "assistant",
                    "content": message.content,
                    **({"name": message.name} if message.name else {})
                }
                
                if message.tool_calls:
                    msg_dict["tool_calls"] = message.tool_calls
                
                openai_messages.append(msg_dict)
            elif isinstance(message, SystemMessage):
                openai_messages.append({
                    "role": "system",
                    "content": message.content,
                    **({"name": message.name} if message.name else {})
                })
            elif isinstance(message, ToolMessage):
                openai_messages.append({
                    "role": "tool",
                    "content": message.content,
                    "tool_call_id": message.tool_call_id,
                    **({"name": message.name} if message.name else {})
                })
        
        request_data = {
            "model": parameters.get("model", "gpt-3.5-turbo"),
            "messages": openai_messages
        }
        
        # 添加可选参数
        optional_params = [
            "temperature", "max_tokens", "top_p", "frequency_penalty",
            "presence_penalty", "stream", "stop", "logit_bias"
        ]
        
        for param in optional_params:
            if param in parameters:
                request_data[param] = parameters[param]
        
        # 处理工具调用
        if "tools" in parameters:
            request_data["tools"] = self._convert_tools_to_openai_format(parameters["tools"])
        
        return request_data
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从OpenAI API响应转换"""
        choice = response["choices"][0]
        message = choice["message"]
        
        if message["role"] == "assistant":
            return AIMessage(
                content=message["content"],
                tool_calls=message.get("tool_calls"),
                additional_kwargs={
                    "finish_reason": choice.get("finish_reason"),
                    "index": choice.get("index")
                }
            )
        else:
            return HumanMessage(content=message["content"])