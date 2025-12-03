# Provider重构实施计划

## 概述

本文档提供了将现有OpenAI和Gemini格式转换器重构为模块化架构的具体实施步骤和代码示例。

## 实施步骤

### 阶段1：创建基础架构

#### 1.1 创建基础目录结构

```bash
mkdir -p src/infrastructure/llm/converters/base
mkdir -p src/infrastructure/llm/converters/common
mkdir -p src/infrastructure/llm/converters/openai
mkdir -p src/infrastructure/llm/converters/gemini
```

#### 1.2 创建基础抽象类

**base/base_provider_utils.py**
```python
"""提供商基础工具类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from src.services.logger import get_logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

class BaseProviderUtils(ABC):
    """提供商基础工具类"""
    
    def __init__(self) -> None:
        """初始化基础工具类"""
        self.logger = get_logger(__name__)
        self.multimodal_utils = None
        self.tools_utils = None
        self.stream_utils = None
        self.validation_utils = None
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass
    
    @abstractmethod
    def convert_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为提供商API请求格式"""
        pass
    
    @abstractmethod
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从提供商API响应转换"""
        pass
    
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """从提供商流式响应转换（默认实现）"""
        if self.stream_utils:
            response = self.stream_utils.process_stream_events(events)
            return self.convert_response(response)
        else:
            raise NotImplementedError(f"{self.get_provider_name()} 不支持流式响应")
    
    def validate_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数（默认实现）"""
        if self.validation_utils:
            return self.validation_utils.validate_request_parameters(parameters)
        else:
            return []
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误（默认实现）"""
        if self.validation_utils:
            return self.validation_utils.handle_api_error(error_response)
        else:
            return f"API错误: {error_response}"
```

**base/base_multimodal_utils.py**
```python
"""多模态基础工具类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union
from src.services.logger import get_logger

class BaseMultimodalUtils(ABC):
    """多模态基础工具类"""
    
    def __init__(self) -> None:
        """初始化多模态工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def process_content_to_provider_format(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """将内容转换为提供商格式"""
        pass
    
    @abstractmethod
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从提供商格式内容中提取文本"""
        pass
    
    @abstractmethod
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证提供商格式内容"""
        pass
    
    def _extract_text_from_mixed_content(self, content: List[Union[str, Dict[str, Any]]]) -> str:
        """从混合内容中提取文本（通用方法）"""
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                else:
                    text_parts.append(f"[{item.get('type', 'unknown')} content]")
        return " ".join(text_parts)
```

**base/base_tools_utils.py**
```python
"""工具使用基础工具类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional
from src.services.logger import get_logger

class BaseToolsUtils(ABC):
    """工具使用基础工具类"""
    
    def __init__(self) -> None:
        """初始化工具工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为提供商格式"""
        pass
    
    @abstractmethod
    def process_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> Any:
        """处理工具选择策略"""
        pass
    
    @abstractmethod
    def extract_tool_calls_from_response(self, response_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从响应中提取工具调用"""
        pass
    
    def validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
        """验证工具定义（通用方法）"""
        errors = []
        
        if not isinstance(tools, list):
            errors.append("工具必须是列表格式")
            return errors
        
        if len(tools) > 100:
            errors.append("工具数量不能超过100个")
        
        tool_names = set()
        for i, tool in enumerate(tools):
            tool_errors = self._validate_single_tool(tool, i, tool_names)
            errors.extend(tool_errors)
        
        return errors
    
    def _validate_single_tool(self, tool: Dict[str, Any], index: int, existing_names: set) -> List[str]:
        """验证单个工具（通用方法）"""
        errors = []
        
        if not isinstance(tool, dict):
            errors.append(f"工具 {index} 必须是字典")
            return errors
        
        name = tool.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"工具 {index} 缺少有效的名称")
        elif name in existing_names:
            errors.append(f"工具 {index} 的名称 '{name}' 已存在")
        else:
            existing_names.add(name)
        
        return errors
```

**base/base_stream_utils.py**
```python
"""流式响应基础工具类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Iterator
from src.services.logger import get_logger

class BaseStreamUtils(ABC):
    """流式响应基础工具类"""
    
    def __init__(self) -> None:
        """初始化流式工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析流式事件行"""
        pass
    
    @abstractmethod
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理流式事件列表"""
        pass
    
    @abstractmethod
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从流式事件中提取文本内容"""
        pass
    
    def validate_stream_events(self, events: List[Dict[str, Any]]) -> List[str]:
        """验证流式事件（通用方法）"""
        errors = []
        
        if not isinstance(events, list):
            errors.append("事件必须是列表格式")
            return errors
        
        if not events:
            errors.append("事件列表不能为空")
        
        return errors
```

**base/base_validation_utils.py**
```python
"""验证基础工具类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.services.logger import get_logger

class BaseValidationUtils(ABC):
    """验证基础工具类"""
    
    def __init__(self) -> None:
        """初始化验证工具"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数"""
        pass
    
    @abstractmethod
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证响应格式"""
        pass
    
    @abstractmethod
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理API错误"""
        pass
    
    def _validate_basic_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证基本参数（通用方法）"""
        errors = []
        
        # 验证模型
        if "model" not in parameters:
            errors.append("缺少model参数")
        
        # 验证max_tokens
        max_tokens = parameters.get("max_tokens")
        if max_tokens is not None:
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                errors.append("max_tokens必须是正整数")
        
        # 验证temperature
        temperature = parameters.get("temperature")
        if temperature is not None:
            if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
                errors.append("temperature必须在0.0-2.0范围内")
        
        return errors
```

#### 1.3 创建通用组件

**common/content_processors.py**
```python
"""通用内容处理器"""

from typing import Dict, Any, List, Union
import base64
import mimetypes

class TextProcessor:
    """文本内容处理器"""
    
    @staticmethod
    def extract_text(content: Union[str, List[Union[str, Dict[str, Any]]]]) -> str:
        """提取文本内容"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return " ".join(text_parts)
        else:
            return str(content)
    
    @staticmethod
    def validate_text(text: str) -> List[str]:
        """验证文本内容"""
        errors = []
        if not isinstance(text, str):
            errors.append("文本内容必须是字符串")
        return errors

class ImageProcessor:
    """图像内容处理器"""
    
    SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    
    @classmethod
    def process_image(cls, image_data: bytes, media_type: str) -> Dict[str, Any]:
        """处理图像数据"""
        encoded_data = base64.b64encode(image_data).decode('utf-8')
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": encoded_data
            }
        }
    
    @classmethod
    def validate_image(cls, image_dict: Dict[str, Any]) -> List[str]:
        """验证图像数据"""
        errors = []
        
        source = image_dict.get("source", {})
        media_type = source.get("media_type", "")
        
        if media_type not in cls.SUPPORTED_FORMATS:
            errors.append(f"不支持的图像格式: {media_type}")
        
        data = source.get("data", "")
        if isinstance(data, str):
            try:
                decoded_data = base64.b64decode(data)
                if len(decoded_data) > cls.MAX_SIZE:
                    errors.append("图像大小超过5MB限制")
            except Exception:
                errors.append("图像数据不是有效的base64编码")
        
        return errors

class MixedContentProcessor:
    """混合内容处理器"""
    
    @staticmethod
    def process_mixed_content(content: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """处理混合内容"""
        processed = []
        for item in content:
            if isinstance(item, str):
                processed.append({"type": "text", "text": item})
            elif isinstance(item, dict):
                processed.append(item)
            else:
                processed.append({"type": "text", "text": str(item)})
        return processed
    
    @staticmethod
    def validate_mixed_content(content: List[Union[str, Dict[str, Any]]]) -> List[str]:
        """验证混合内容"""
        errors = []
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        image_count = 0
        for i, item in enumerate(content):
            if isinstance(item, dict) and item.get("type") == "image":
                image_count += 1
                image_errors = ImageProcessor.validate_image(item)
                for error in image_errors:
                    errors.append(f"内容项 {i}: {error}")
        
        if image_count > 5:
            errors.append("每条消息最多支持5张图像")
        
        return errors
```

**common/error_handlers.py**
```python
"""通用错误处理器"""

from typing import Dict, Any, List

class ErrorHandler:
    """通用错误处理器"""
    
    @staticmethod
    def handle_validation_error(errors: List[str]) -> str:
        """处理验证错误"""
        if not errors:
            return "未知验证错误"
        return f"验证失败: {'; '.join(errors)}"
    
    @staticmethod
    def handle_format_error(error: Exception) -> str:
        """处理格式错误"""
        return f"格式错误: {str(error)}"
    
    @staticmethod
    def handle_api_error(error_response: Dict[str, Any], provider: str) -> str:
        """处理API错误"""
        error_type = error_response.get("error", {}).get("type", "unknown")
        error_message = error_response.get("error", {}).get("message", "未知错误")
        
        # 根据provider提供特定的错误映射
        error_mappings = {
            "openai": {
                "invalid_request_error": "请求参数无效",
                "authentication_error": "认证失败，请检查API密钥",
                "permission_error": "权限不足",
                "not_found_error": "请求的资源不存在",
                "rate_limit_error": "请求频率过高，请稍后重试",
                "api_error": "API内部错误"
            },
            "anthropic": {
                "invalid_request_error": "请求参数无效",
                "authentication_error": "认证失败，请检查API密钥",
                "permission_error": "权限不足",
                "not_found_error": "请求的资源不存在",
                "rate_limit_error": "请求频率过高，请稍后重试",
                "api_error": "API内部错误",
                "overloaded_error": "服务过载，请稍后重试"
            },
            "gemini": {
                "INVALID_ARGUMENT": "请求参数无效",
                "PERMISSION_DENIED": "权限不足",
                "NOT_FOUND": "请求的资源不存在",
                "RESOURCE_EXHAUSTED": "请求频率过高，请稍后重试",
                "INTERNAL": "API内部错误"
            }
        }
        
        provider_mappings = error_mappings.get(provider, {})
        friendly_message = provider_mappings.get(error_type, f"未知错误类型: {error_type}")
        
        return f"{friendly_message}: {error_message}"
```

### 阶段2：重构OpenAI模块

#### 2.1 创建OpenAI多模态工具

**openai/openai_multimodal_utils.py**
```python
"""OpenAI多模态内容处理工具"""

from typing import Dict, Any, List, Union
from src.infrastructure.llm.converters.base.base_multimodal_utils import BaseMultimodalUtils
from src.infrastructure.llm.converters.common.content_processors import TextProcessor, ImageProcessor

class OpenAIMultimodalUtils(BaseMultimodalUtils):
    """OpenAI多模态内容处理工具类"""
    
    def process_content_to_provider_format(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> List[Dict[str, Any]]:
        """将内容转换为OpenAI格式"""
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        elif isinstance(content, list):
            processed_content = []
            for item in content:
                if isinstance(item, str):
                    processed_content.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    if item.get("type") == "text":
                        processed_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    elif item.get("type") == "image":
                        # OpenAI图像URL格式
                        image_url = self._process_image_for_openai(item)
                        if image_url:
                            processed_content.append({
                                "type": "image_url",
                                "image_url": image_url
                            })
                    else:
                        processed_content.append({"type": "text", "text": str(item)})
            return processed_content
        else:
            return [{"type": "text", "text": str(content)}]
    
    def extract_text_from_provider_content(self, content: List[Dict[str, Any]]) -> str:
        """从OpenAI格式内容中提取文本"""
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "image_url":
                    text_parts.append("[图像内容]")
        return " ".join(text_parts)
    
    def validate_provider_content(self, content: List[Dict[str, Any]]) -> List[str]:
        """验证OpenAI格式内容"""
        errors = []
        
        if not isinstance(content, list):
            errors.append("内容必须是列表格式")
            return errors
        
        image_count = 0
        for i, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"内容项 {i} 必须是字典")
                continue
            
            content_type = item.get("type")
            if not content_type:
                errors.append(f"内容项 {i} 缺少type字段")
                continue
            
            if content_type == "text":
                text = item.get("text")
                if not isinstance(text, str):
                    errors.append(f"文本内容项 {i} 的text字段必须是字符串")
            elif content_type == "image_url":
                image_count += 1
                image_url = item.get("image_url", {})
                if not isinstance(image_url, dict):
                    errors.append(f"图像内容项 {i} 的image_url字段必须是字典")
                else:
                    url = image_url.get("url")
                    if not isinstance(url, str):
                        errors.append(f"图像内容项 {i} 的url字段必须是字符串")
            else:
                errors.append(f"内容项 {i} 有不支持的类型: {content_type}")
        
        # OpenAI限制
        if image_count > 10:  # OpenAI的具体限制可能不同
            errors.append("每条消息最多支持10张图像")
        
        return errors
    
    def _process_image_for_openai(self, image_item: Dict[str, Any]) -> Dict[str, Any]:
        """为OpenAI处理图像项"""
        source = image_item.get("source", {})
        if source.get("type") == "base64":
            media_type = source.get("media_type", "")
            data = source.get("data", "")
            
            # OpenAI需要特定的URL格式
            return {
                "url": f"data:{media_type};base64,{data}"
            }
        
        return None
```

#### 2.2 创建OpenAI工具工具

**openai/openai_tools_utils.py**
```python
"""OpenAI工具使用处理工具"""

from typing import Dict, Any, List, Union
from src.infrastructure.llm.converters.base.base_tools_utils import BaseToolsUtils

class OpenAIToolsUtils(BaseToolsUtils):
    """OpenAI工具使用处理工具类"""
    
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为OpenAI格式"""
        openai_tools = []
        
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", "")
                }
            }
            
            if "parameters" in tool:
                openai_tool["function"]["parameters"] = tool["parameters"]
            
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    def process_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> Any:
        """处理工具选择策略"""
        if tool_choice == "auto" or tool_choice is None:
            return "auto"
        elif tool_choice == "none":
            return "none"
        elif isinstance(tool_choice, dict):
            if tool_choice.get("type") == "function":
                return {
                    "type": "function",
                    "function": {"name": tool_choice.get("function", {}).get("name", "")}
                }
        
        return "auto"  # 默认值
    
    def extract_tool_calls_from_response(self, response_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从响应中提取工具调用"""
        # OpenAI的工具调用通常在message的tool_calls字段中
        # 这里需要根据实际的响应结构来提取
        tool_calls = []
        
        # 这个方法需要根据OpenAI的实际响应格式来实现
        # 可能需要从response的其他部分提取tool_calls
        
        return tool_calls
    
    def extract_tool_calls_from_message(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从消息中提取工具调用（OpenAI特定）"""
        return message.get("tool_calls", [])
```

#### 2.3 创建OpenAI流式工具

**openai/openai_stream_utils.py**
```python
"""OpenAI流式响应处理工具"""

import json
from typing import Dict, Any, List, Optional
from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils

class OpenAIStreamUtils(BaseStreamUtils):
    """OpenAI流式响应处理工具类"""
    
    def parse_stream_event(self, event_line: str) -> Optional[Dict[str, Any]]:
        """解析OpenAI流式事件行"""
        try:
            if not event_line.startswith("data: "):
                return None
            
            json_str = event_line[6:].strip()
            
            if json_str == "[DONE]":
                return {"type": "stream_end"}
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            self.logger.error(f"JSON解析失败: {event_line}")
            return None
    
    def process_stream_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理OpenAI流式事件列表"""
        # 构建完整的响应结构
        response = {
            "choices": [{}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0}
        }
        
        current_choice = response["choices"][0]
        content_parts = []
        tool_calls = []
        
        for event in events:
            if event.get("type") == "stream_end":
                break
            
            choices = event.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                
                # 处理文本内容
                if "content" in delta:
                    content_parts.append(delta["content"])
                
                # 处理工具调用
                if "tool_calls" in delta:
                    for tool_call_delta in delta["tool_calls"]:
                        self._process_tool_call_delta(tool_call_delta, tool_calls)
                
                # 更新finish_reason
                if "finish_reason" in choices[0]:
                    current_choice["finish_reason"] = choices[0]["finish_reason"]
            
            # 更新使用统计
            if "usage" in event:
                usage = event["usage"]
                response["usage"]["completion_tokens"] += usage.get("completion_tokens", 0)
        
        # 设置内容
        if content_parts:
            current_choice["message"] = {
                "role": "assistant",
                "content": "".join(content_parts)
            }
        
        if tool_calls:
            if "message" not in current_choice:
                current_choice["message"] = {"role": "assistant"}
            current_choice["message"]["tool_calls"] = tool_calls
        
        return response
    
    def extract_text_from_stream_events(self, events: List[Dict[str, Any]]) -> str:
        """从OpenAI流式事件中提取文本内容"""
        text_parts = []
        
        for event in events:
            choices = event.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                if "content" in delta:
                    text_parts.append(delta["content"])
        
        return "".join(text_parts)
    
    def _process_tool_call_delta(self, tool_call_delta: Dict[str, Any], tool_calls: List[Dict[str, Any]]) -> None:
        """处理工具调用增量"""
        index = tool_call_delta.get("index")
        if index is None:
            return
        
        # 确保tool_calls列表足够长
        while len(tool_calls) <= index:
            tool_calls.append({
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""}
            })
        
        tool_call = tool_calls[index]
        
        # 更新ID
        if "id" in tool_call_delta:
            tool_call["id"] = tool_call_delta["id"]
        
        # 更新函数信息
        if "function" in tool_call_delta:
            function_delta = tool_call_delta["function"]
            if "name" in function_delta:
                tool_call["function"]["name"] = function_delta["name"]
            if "arguments" in function_delta:
                tool_call["function"]["arguments"] += function_delta["arguments"]
```

#### 2.4 创建OpenAI验证工具

**openai/openai_validation_utils.py**
```python
"""OpenAI验证和错误处理工具"""

from typing import Dict, Any, List
from src.infrastructure.llm.converters.base.base_validation_utils import BaseValidationUtils
from src.infrastructure.llm.converters.common.error_handlers import ErrorHandler

class OpenAIValidationUtils(BaseValidationUtils):
    """OpenAI验证工具类"""
    
    # 支持的模型列表
    SUPPORTED_MODELS = {
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
        "gpt-4", "gpt-4-32k", "gpt-4-turbo-preview",
        "gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"
    }
    
    def validate_request_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """验证OpenAI请求参数"""
        errors = self._validate_basic_parameters(parameters)
        
        # OpenAI特定验证
        model = parameters.get("model", "")
        if model and model not in self.SUPPORTED_MODELS:
            errors.append(f"不支持的OpenAI模型: {model}")
        
        # 验证temperature范围（OpenAI支持0-2）
        temperature = parameters.get("temperature")
        if temperature is not None and (temperature < 0 or temperature > 2):
            errors.append("OpenAI的temperature必须在0.0-2.0范围内")
        
        # 验证top_p
        top_p = parameters.get("top_p")
        if top_p is not None and (top_p <= 0 or top_p > 1):
            errors.append("top_p必须在0.0-1.0范围内")
        
        # 验证frequency_penalty
        frequency_penalty = parameters.get("frequency_penalty")
        if frequency_penalty is not None and (frequency_penalty < -2 or frequency_penalty > 2):
            errors.append("frequency_penalty必须在-2.0到2.0范围内")
        
        # 验证presence_penalty
        presence_penalty = parameters.get("presence_penalty")
        if presence_penalty is not None and (presence_penalty < -2 or presence_penalty > 2):
            errors.append("presence_penalty必须在-2.0到2.0范围内")
        
        return errors
    
    def validate_response(self, response: Dict[str, Any]) -> List[str]:
        """验证OpenAI响应格式"""
        errors = []
        
        # 验证基本结构
        if "choices" not in response:
            errors.append("响应缺少choices字段")
            return errors
        
        choices = response["choices"]
        if not isinstance(choices, list) or len(choices) == 0:
            errors.append("choices必须是非空列表")
            return errors
        
        choice = choices[0]
        if "message" not in choice:
            errors.append("choice缺少message字段")
            return errors
        
        message = choice["message"]
        if "role" not in message or message["role"] != "assistant":
            errors.append("message的role必须是assistant")
        
        return errors
    
    def handle_api_error(self, error_response: Dict[str, Any]) -> str:
        """处理OpenAI API错误"""
        return ErrorHandler.handle_api_error(error_response, "openai")
```

#### 2.5 重构OpenAI主格式工具

**openai/openai_format_utils.py**
```python
"""OpenAI格式转换工具类"""

from typing import Dict, Any, List
from src.infrastructure.llm.converters.base.base_provider_utils import BaseProviderUtils
from src.infrastructure.llm.converters.openai.openai_multimodal_utils import OpenAIMultimodalUtils
from src.infrastructure.llm.converters.openai.openai_tools_utils import OpenAIToolsUtils
from src.infrastructure.llm.converters.openai.openai_stream_utils import OpenAIStreamUtils
from src.infrastructure.llm.converters.openai.openai_validation_utils import OpenAIValidationUtils
from src.infrastructure.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

class OpenAIFormatUtils(BaseProviderUtils):
    """OpenAI格式转换工具类"""
    
    def __init__(self) -> None:
        """初始化OpenAI格式工具"""
        super().__init__()
        self.multimodal_utils = OpenAIMultimodalUtils()
        self.tools_utils = OpenAIToolsUtils()
        self.stream_utils = OpenAIStreamUtils()
        self.validation_utils = OpenAIValidationUtils()
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "openai"
    
    def convert_request(self, messages: List["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换为OpenAI API请求格式"""
        openai_messages = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                openai_messages.append({
                    "role": "user",
                    "content": self.multimodal_utils.process_content_to_provider_format(message.content),
                    **({"name": message.name} if message.name else {})
                })
            elif isinstance(message, AIMessage):
                msg_dict = {
                    "role": "assistant",
                    "content": self.multimodal_utils.process_content_to_provider_format(message.content),
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
            request_data["tools"] = self.tools_utils.convert_tools_to_provider_format(parameters["tools"])
            
            # 处理工具选择
            if "tool_choice" in parameters:
                request_data["tool_choice"] = self.tools_utils.process_tool_choice(parameters["tool_choice"])
        
        return request_data
    
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """从OpenAI API响应转换"""
        choice = response["choices"][0]
        message = choice["message"]
        
        if message["role"] == "assistant":
            # 提取工具调用
            tool_calls = self.tools_utils.extract_tool_calls_from_message(message)
            
            return AIMessage(
                content=message.get("content", ""),
                tool_calls=tool_calls if tool_calls else None,
                additional_kwargs={
                    "finish_reason": choice.get("finish_reason"),
                    "index": choice.get("index")
                }
            )
        else:
            return HumanMessage(content=message.get("content", ""))
```

### 阶段3：更新工厂类和导入

#### 3.1 更新provider_format_utils.py

```python
# 在provider_format_utils.py中更新导入路径

class ProviderFormatUtilsFactory:
    def get_format_utils(self, provider: str) -> BaseProviderUtils:
        if provider == "openai":
            from .openai.openai_format_utils import OpenAIFormatUtils
            return OpenAIFormatUtils()
        elif provider == "gemini":
            from .gemini.gemini_format_utils import GeminiFormatUtils
            return GeminiFormatUtils()
        elif provider == "anthropic":
            from .anthropic.anthropic_format_utils import AnthropicFormatUtils
            return AnthropicFormatUtils()
        else:
            raise ValueError(f"不支持的提供商: {provider}")
```

#### 3.2 创建各模块的__init__.py

**openai/__init__.py**
```python
"""OpenAI格式转换模块"""

from .openai_format_utils import OpenAIFormatUtils
from .openai_multimodal_utils import OpenAIMultimodalUtils
from .openai_tools_utils import OpenAIToolsUtils
from .openai_stream_utils import OpenAIStreamUtils
from .openai_validation_utils import OpenAIValidationUtils

__all__ = [
    "OpenAIFormatUtils",
    "OpenAIMultimodalUtils", 
    "OpenAIToolsUtils",
    "OpenAIStreamUtils",
    "OpenAIValidationUtils"
]
```

## 测试策略

### 1. 单元测试
为每个新创建的工具类创建独立的单元测试

### 2. 集成测试
测试整个OpenAI模块的端到端功能

### 3. 兼容性测试
确保重构后的代码与现有代码兼容

### 4. 性能测试
验证重构后的性能没有显著下降

## 迁移检查清单

- [ ] 创建基础架构
- [ ] 重构OpenAI模块
- [ ] 创建OpenAI测试
- [ ] 更新工厂类
- [ ] 运行现有测试
- [ ] 性能验证
- [ ] 文档更新

这个实施计划提供了详细的步骤和代码示例，确保重构过程的顺利进行。