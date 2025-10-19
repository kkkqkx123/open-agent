# OpenAI API格式支持 - 技术实现细节

## 1. 核心接口定义

### 1.1 API格式适配器接口

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, AsyncGenerator, Optional
from langchain_core.messages import BaseMessage
from ...models import LLMResponse, TokenUsage

class APIFormatAdapter(ABC):
    """API格式适配器基类"""
    
    def __init__(self, config: 'OpenAIConfig'):
        self.config = config
        self._client = None
    
    @abstractmethod
    def initialize_client(self) -> None:
        """初始化底层客户端"""
        pass
    
    @abstractmethod
    def generate(self, messages: List[BaseMessage], **kwargs) -> LLMResponse:
        """同步生成响应"""
        pass
    
    @abstractmethod
    async def generate_async(self, messages: List[BaseMessage], **kwargs) -> LLMResponse:
        """异步生成响应"""
        pass
    
    @abstractmethod
    def stream_generate(self, messages: List[BaseMessage], **kwargs) -> Generator[str, None, None]:
        """同步流式生成"""
        pass
    
    @abstractmethod
    async def stream_generate_async(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成"""
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """计算文本token数量"""
        pass
    
    @abstractmethod
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表token数量"""
        pass
    
    @abstractmethod
    def supports_function_calling(self) -> bool:
        """是否支持函数调用"""
        pass
```

### 1.2 消息转换器接口

```python
class MessageConverter(ABC):
    """消息格式转换器"""
    
    @abstractmethod
    def to_api_format(self, messages: List[BaseMessage]) -> Any:
        """转换为API特定格式"""
        pass
    
    @abstractmethod
    def from_api_format(self, api_response: Any) -> LLMResponse:
        """从API响应转换为统一格式"""
        pass
```

## 2. Chat Completion适配器实现

### 2.1 适配器实现

```python
from langchain_openai import ChatOpenAI
from .base import APIFormatAdapter
from ..converters.chat_completion_converter import ChatCompletionConverter

class ChatCompletionAdapter(APIFormatAdapter):
    """Chat Completion API适配器"""
    
    def __init__(self, config: 'OpenAIConfig'):
        super().__init__(config)
        self.converter = ChatCompletionConverter()
    
    def initialize_client(self) -> None:
        """初始化LangChain ChatOpenAI客户端"""
        if self._client is None:
            # 获取解析后的HTTP标头
            resolved_headers = self.config.get_resolved_headers()
            
            # 准备模型参数
            model_kwargs = {}
            if self.config.max_tokens:
                model_kwargs["max_tokens"] = self.config.max_tokens
            if self.config.functions:
                model_kwargs["functions"] = self.config.functions
                if self.config.function_call:
                    model_kwargs["function_call"] = self.config.function_call
            
            # 转换 api_key 为 SecretStr 类型
            from pydantic import SecretStr
            api_key = SecretStr(self.config.api_key) if self.config.api_key else None
            
            self._client = ChatOpenAI(
                model=self.config.model_name,
                api_key=api_key,
                base_url=self.config.base_url,
                organization=getattr(self.config, 'organization', None),
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                default_headers=resolved_headers,
                model_kwargs=model_kwargs
            )
    
    def generate(self, messages: List[BaseMessage], **kwargs) -> LLMResponse:
        """生成响应"""
        self.initialize_client()
        
        try:
            # 调用ChatOpenAI
            response = self._client.invoke(messages, **kwargs)
            
            # 转换响应格式
            return self.converter.from_api_format(response)
            
        except Exception as e:
            # 错误处理
            raise self._handle_error(e)
    
    # ... 其他方法实现
```

### 2.2 消息转换器实现

```python
from langchain_core.messages import BaseMessage
from ...models import LLMResponse, TokenUsage

class ChatCompletionConverter(MessageConverter):
    """Chat Completion格式转换器"""
    
    def to_api_format(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Chat Completion API直接使用LangChain消息格式"""
        return messages
    
    def from_api_format(self, api_response: Any) -> LLMResponse:
        """从Chat Completion响应转换为统一格式"""
        # 提取Token使用情况
        token_usage = self._extract_token_usage(api_response)
        
        # 提取函数调用信息
        function_call = self._extract_function_call(api_response)
        
        # 提取完成原因
        finish_reason = self._extract_finish_reason(api_response)
        
        # 提取内容
        content = self._extract_content(api_response)
        
        return LLMResponse(
            content=content,
            message=api_response,
            token_usage=token_usage,
            model=getattr(api_response, 'model', 'unknown'),
            finish_reason=finish_reason,
            function_call=function_call,
            metadata=getattr(api_response, 'response_metadata', {})
        )
    
    def _extract_token_usage(self, response: Any) -> TokenUsage:
        """提取Token使用情况"""
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = response.usage_metadata
            return TokenUsage(
                prompt_tokens=usage.get('input_tokens', 0),
                completion_tokens=usage.get('output_tokens', 0),
                total_tokens=usage.get('total_tokens', 0)
            )
        elif hasattr(response, 'response_metadata') and response.response_metadata:
            metadata = response.response_metadata
            if 'token_usage' in metadata:
                usage = metadata['token_usage']
                return TokenUsage(
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0)
                )
        
        return TokenUsage()
    
    # ... 其他提取方法
```

## 3. Responses API适配器实现

### 3.1 原生客户端实现

```python
import httpx
import json
from typing import Dict, Any, List, Optional
from ...config import OpenAIConfig

class OpenAIResponsesClient:
    """OpenAI Responses API原生客户端"""
    
    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.api_key = config.api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 添加自定义标头
        resolved_headers = config.get_resolved_headers()
        self.headers.update(resolved_headers)
    
    async def create_response(
        self,
        input_text: str,
        previous_response_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """创建Responses API请求"""
        url = f"{self.base_url}/responses"
        
        payload = {
            "model": self.config.model_name,
            "input": input_text,
            **kwargs
        }
        
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    def create_response_sync(
        self,
        input_text: str,
        previous_response_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """同步创建Responses API请求"""
        url = f"{self.base_url}/responses"
        
        payload = {
            "model": self.config.model_name,
            "input": input_text,
            **kwargs
        }
        
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        
        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.post(
                url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
```

### 3.2 Responses API适配器

```python
from .base import APIFormatAdapter
from .native_client import OpenAIResponsesClient
from ..converters.responses_converter import ResponsesConverter
from ...token_counter import TokenCounterFactory

class ResponsesAPIAdapter(APIFormatAdapter):
    """Responses API适配器"""
    
    def __init__(self, config: 'OpenAIConfig'):
        super().__init__(config)
        self.converter = ResponsesConverter()
        self._conversation_history = []
    
    def initialize_client(self) -> None:
        """初始化Responses API客户端"""
        if self._client is None:
            self._client = OpenAIResponsesClient(self.config)
    
    def generate(self, messages: List[BaseMessage], **kwargs) -> LLMResponse:
        """生成响应"""
        self.initialize_client()
        
        # 转换消息为input格式
        input_text = self.converter.messages_to_input(messages)
        
        # 获取之前的响应ID（如果有）
        previous_response_id = self._get_previous_response_id()
        
        try:
            # 调用Responses API
            api_response = self._client.create_response_sync(
                input_text=input_text,
                previous_response_id=previous_response_id,
                **kwargs
            )
            
            # 转换响应格式
            llm_response = self.converter.from_api_format(api_response)
            
            # 更新对话历史
            self._update_conversation_history(api_response)
            
            return llm_response
            
        except Exception as e:
            raise self._handle_error(e)
    
    def _get_previous_response_id(self) -> Optional[str]:
        """获取之前的响应ID"""
        if self._conversation_history:
            return self._conversation_history[-1].get('id')
        return None
    
    def _update_conversation_history(self, response: Dict[str, Any]) -> None:
        """更新对话历史"""
        self._conversation_history.append(response)
        
        # 限制历史记录长度
        max_history = 10
        if len(self._conversation_history) > max_history:
            self._conversation_history = self._conversation_history[-max_history:]
    
    def get_token_count(self, text: str) -> int:
        """计算文本token数量"""
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        return counter.count_tokens(text)
    
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表token数量"""
        counter = TokenCounterFactory.create_counter("openai", self.config.model_name)
        return counter.count_messages_tokens(messages)
    
    def supports_function_calling(self) -> bool:
        """Responses API支持函数调用"""
        return True
```

### 3.3 Responses格式转换器

```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from ...models import LLMResponse, TokenUsage

class ResponsesConverter(MessageConverter):
    """Responses API格式转换器"""
    
    def messages_to_input(self, messages: List[BaseMessage]) -> str:
        """将消息列表转换为input字符串"""
        # 简单实现：连接所有消息内容
        # 实际实现可能需要更复杂的逻辑
        input_parts = []
        
        for message in messages:
            if hasattr(message, 'content'):
                content = str(message.content)
                if hasattr(message, 'type'):
                    if message.type == 'system':
                        input_parts.append(f"System: {content}")
                    elif message.type == 'human':
                        input_parts.append(f"User: {content}")
                    elif message.type == 'ai':
                        input_parts.append(f"Assistant: {content}")
                else:
                    input_parts.append(content)
        
        return "\n".join(input_parts)
    
    def from_api_format(self, api_response: Dict[str, Any]) -> LLMResponse:
        """从Responses API响应转换为统一格式"""
        # 提取输出内容
        content = self._extract_output_text(api_response)
        
        # 提取Token使用情况
        token_usage = self._extract_token_usage(api_response)
        
        # 提取函数调用
        function_call = self._extract_function_call(api_response)
        
        # 创建LangChain消息
        message = AIMessage(content=content)
        
        return LLMResponse(
            content=content,
            message=message,
            token_usage=token_usage,
            model=api_response.get('model', 'unknown'),
            function_call=function_call,
            metadata={
                'response_id': api_response.get('id'),
                'object': api_response.get('object'),
                'created_at': api_response.get('created_at'),
                'output_items': api_response.get('output', [])
            }
        )
    
    def _extract_output_text(self, response: Dict[str, Any]) -> str:
        """提取输出文本"""
        output_items = response.get('output', [])
        
        for item in output_items:
            if item.get('type') == 'message':
                content = item.get('content', [])
                for content_item in content:
                    if content_item.get('type') == 'output_text':
                        return content_item.get('text', '')
        
        return ''
    
    def _extract_token_usage(self, response: Dict[str, Any]) -> TokenUsage:
        """提取Token使用情况"""
        # Responses API的Token使用情况可能在不同的字段中
        usage = response.get('usage', {})
        
        return TokenUsage(
            prompt_tokens=usage.get('prompt_tokens', 0),
            completion_tokens=usage.get('completion_tokens', 0),
            total_tokens=usage.get('total_tokens', 0)
        )
    
    def _extract_function_call(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取函数调用信息"""
        output_items = response.get('output', [])
        
        for item in output_items:
            if item.get('type') == 'function_call':
                return {
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'arguments': item.get('arguments')
                }
        
        return None
```

## 4. 统一客户端实现

### 4.1 统一客户端

```python
from typing import Dict, Any, List, Generator, AsyncGenerator
from langchain_core.messages import BaseMessage
from ..base import BaseLLMClient
from ..models import LLMResponse
from .adapters.chat_completion import ChatCompletionAdapter
from .adapters.responses_api import ResponsesAPIAdapter
from ...config import OpenAIConfig

class OpenAIUnifiedClient(BaseLLMClient):
    """OpenAI统一客户端，支持多种API格式"""
    
    def __init__(self, config: OpenAIConfig) -> None:
        super().__init__(config)
        self._adapter = None
        self._initialize_adapter()
    
    def _initialize_adapter(self) -> None:
        """根据配置初始化适配器"""
        api_format = getattr(self.config, 'api_format', 'chat_completion')
        
        if api_format == 'chat_completion':
            self._adapter = ChatCompletionAdapter(self.config)
        elif api_format == 'responses':
            self._adapter = ResponsesAPIAdapter(self.config)
        else:
            raise ValueError(f"不支持的API格式: {api_format}")
    
    def _do_generate(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> LLMResponse:
        """执行生成操作"""
        return self._adapter.generate(messages, **parameters, **kwargs)
    
    async def _do_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        return await self._adapter.generate_async(messages, **parameters, **kwargs)
    
    def _do_stream_generate(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> Generator[str, None, None]:
        """执行流式生成操作"""
        return self._adapter.stream_generate(messages, **parameters, **kwargs)
    
    async def _do_stream_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        async for chunk in self._adapter.stream_generate_async(messages, **parameters, **kwargs):
            yield chunk
    
    def get_token_count(self, text: str) -> int:
        """计算文本token数量"""
        return self._adapter.get_token_count(text)
    
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表token数量"""
        return self._adapter.get_messages_token_count(messages)
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        return self._adapter.supports_function_calling()
    
    def switch_api_format(self, api_format: str) -> None:
        """切换API格式"""
        if hasattr(self.config, 'api_format'):
            self.config.api_format = api_format
            self._initialize_adapter()
        else:
            raise AttributeError("配置不支持API格式切换")
```

## 5. 配置系统扩展

### 5.1 扩展配置类

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .llm_client_config import LLMClientConfig

@dataclass
class OpenAIConfig(LLMClientConfig):
    """OpenAI扩展配置"""
    organization: Optional[str] = None
    api_format: str = "chat_completion"  # chat_completion | responses
    api_format_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.model_type != "openai":
            raise ValueError("OpenAIConfig的model_type必须为'openai'")
        
        # 设置默认的API格式配置
        if not self.api_format_configs:
            self.api_format_configs = {
                "chat_completion": {
                    "endpoint": "/chat/completions",
                    "supports_multiple_choices": True,
                    "legacy_structured_output": True
                },
                "responses": {
                    "endpoint": "/responses",
                    "supports_reasoning": True,
                    "native_storage": True,
                    "structured_output_format": "text.format"
                }
            }
    
    def get_api_format_config(self, format_name: str) -> Dict[str, Any]:
        """获取特定API格式的配置"""
        return self.api_format_configs.get(format_name, {})
    
    def is_api_format_supported(self, format_name: str) -> bool:
        """检查是否支持指定的API格式"""
        return format_name in self.api_format_configs
```

### 5.2 工厂模式更新

```python
from ..factory import LLMClientFactory
from .unified_client import OpenAIUnifiedClient

class ExtendedLLMClientFactory(LLMClientFactory):
    """扩展的LLM客户端工厂"""
    
    def create_openai_client(self, config: OpenAIConfig) -> OpenAIUnifiedClient:
        """创建OpenAI统一客户端"""
        return OpenAIUnifiedClient(config)
    
    def register_openai_client(self) -> None:
        """注册OpenAI客户端"""
        self._client_types["openai"] = OpenAIUnifiedClient
```

## 6. 错误处理和降级

### 6.1 错误处理策略

```python
from ...exceptions import LLMCallError, LLMServiceUnavailableError

class APIFormatSwitcher:
    """API格式切换器，用于错误处理和降级"""
    
    def __init__(self, primary_client: OpenAIUnifiedClient):
        self.primary_client = primary_client
        self.fallback_client = None
        self._initialize_fallback()
    
    def _initialize_fallback(self) -> None:
        """初始化降级客户端"""
        config = self.primary_client.config
        
        # 如果主客户端使用responses，降级到chat_completion
        if getattr(config, 'api_format', 'chat_completion') == 'responses':
            fallback_config = self._create_fallback_config(config, 'chat_completion')
            self.fallback_client = OpenAIUnifiedClient(fallback_config)
    
    def _create_fallback_config(self, original_config: OpenAIConfig, api_format: str) -> OpenAIConfig:
        """创建降级配置"""
        import copy
        
        fallback_config = copy.deepcopy(original_config)
        fallback_config.api_format = api_format
        
        return fallback_config
    
    def generate_with_fallback(self, messages: List[BaseMessage], **kwargs) -> LLMResponse:
        """带降级的生成"""
        try:
            return self.primary_client.generate(messages, **kwargs)
        except (LLMServiceUnavailableError, LLMCallError) as e:
            if self.fallback_client and self._should_fallback(e):
                return self.fallback_client.generate(messages, **kwargs)
            else:
                raise
    
    def _should_fallback(self, error: Exception) -> bool:
        """判断是否应该降级"""
        # 根据错误类型和配置决定是否降级
        return isinstance(error, (LLMServiceUnavailableError, LLMCallError))
```

## 7. 测试策略

### 7.1 单元测试结构

```python
import pytest
from unittest.mock import Mock, patch
from src.llm.clients.openai.unified_client import OpenAIUnifiedClient
from src.llm.clients.openai.adapters.chat_completion import ChatCompletionAdapter
from src.llm.clients.openai.adapters.responses_api import ResponsesAPIAdapter

class TestOpenAIUnifiedClient:
    """统一客户端测试"""
    
    @pytest.fixture
    def chat_completion_config(self):
        """Chat Completion配置"""
        from src.llm.config import OpenAIConfig
        
        return OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="chat_completion"
        )
    
    @pytest.fixture
    def responses_config(self):
        """Responses API配置"""
        from src.llm.config import OpenAIConfig
        
        return OpenAIConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key",
            api_format="responses"
        )
    
    def test_chat_completion_adapter_selection(self, chat_completion_config):
        """测试Chat Completion适配器选择"""
        client = OpenAIUnifiedClient(chat_completion_config)
        assert isinstance(client._adapter, ChatCompletionAdapter)
    
    def test_responses_adapter_selection(self, responses_config):
        """测试Responses API适配器选择"""
        client = OpenAIUnifiedClient(responses_config)
        assert isinstance(client._adapter, ResponsesAPIAdapter)
    
    def test_api_format_switching(self, chat_completion_config):
        """测试API格式切换"""
        client = OpenAIUnifiedClient(chat_completion_config)
        
        # 初始应该是Chat Completion适配器
        assert isinstance(client._adapter, ChatCompletionAdapter)
        
        # 切换到Responses API
        client.switch_api_format("responses")
        assert isinstance(client._adapter, ResponsesAPIAdapter)
```

## 8. 性能优化

### 8.1 缓存策略

```python
from functools import lru_cache
from typing import Tuple

class CachedTokenCounter:
    """缓存的Token计数器"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._counter = TokenCounterFactory.create_counter("openai", model_name)
    
    @lru_cache(maxsize=1000)
    def count_tokens(self, text: str) -> int:
        """缓存的Token计数"""
        return self._counter.count_tokens(text)
    
    @lru_cache(maxsize=500)
    def count_messages_tokens(self, messages_hash: Tuple) -> int:
        """缓存的消息Token计数"""
        # 需要将消息列表转换为可哈希的格式
        messages = eval(messages_hash)  # 实际实现中应该用更安全的方法
        return self._counter.count_messages_tokens(messages)
```

### 8.2 连接池优化

```python
import httpx
from typing import Optional

class OptimizedHTTPClient:
    """优化的HTTP客户端"""
    
    def __init__(self, base_url: str, api_key: str, pool_size: int = 10):
        self.base_url = base_url
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=pool_size),
            timeout=30.0
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
```

---

**文档版本**：1.0  
**创建日期**：2025-10-19  
**作者**：架构团队  
**状态**：详细设计完成