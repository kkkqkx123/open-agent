# Anthropic 客户端与基础设施层统一接口重构实施指南

## 总体规划

这份指南结合了两个分析报告的建议：
1. **ANTHROPIC_CLIENT_REFACTOR_ANALYSIS.md** - Core层简化方案
2. **INFRASTRUCTURE_UNIFIED_INTERFACE_ANALYSIS.md** - Infrastructure层统一接口方案

目标：**从 1000+ 行重复代码 → 150 行高效代码**

---

## 执行路线图

```
Week 1
├─ Day 1-2: Infrastructure 层统一接口创建 (ProviderHttpClient)
├─ Day 3: AnthropicHttpClient 迁移
└─ Day 4: OpenAI/Gemini 迁移 + Factory 创建

Week 2
├─ Day 1: Core 层简化
├─ Day 2-3: 测试和集成
├─ Day 4: 文档和向后兼容
└─ Day 5: 代码审查和优化
```

---

## Phase 1: 基础设施层统一接口实施

### 步骤 1.1: 创建 ProviderHttpClient 基类

**文件：** `src/infrastructure/llm/http_client/provider_http_client.py`

```python
"""通用的 LLM Provider HTTP 客户端基类

提供标准化的 chat_completions 实现，子类只需实现核心方法。
"""

from abc import abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, Union, Sequence, List
from httpx import Response

from src.interfaces.llm.http_client import ILLMHttpClient
from src.infrastructure.llm.http_client.base_http_client import BaseHttpClient
from src.infrastructure.llm.models import LLMResponse
from src.services.logger import get_logger

# TYPE_CHECKING 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage


class ProviderHttpClient(BaseHttpClient, ILLMHttpClient):
    """通用的 LLM Provider HTTP 客户端基类
    
    使用模板方法模式，提供标准化的 chat_completions 实现。
    子类只需实现以下关键方法：
    - _get_endpoint_path(model): 获取API端点
    - _stream_response(): 处理流式响应
    - _convert_response(): 转换响应
    - get_provider_name(): 获取提供商名称
    - get_supported_models(): 获取支持的模型列表
    """
    
    # 子类必须定义
    SUPPORTED_MODELS: List[str] = []
    
    @property
    def timeout(self) -> Optional[float]:
        """获取超时时间"""
        return self._timeout if hasattr(self, '_timeout') else self.timeout
    
    @property
    def max_retries(self) -> int:
        """获取最大重试次数"""
        return self.max_retries if hasattr(self, 'max_retries') else 3
    
    async def chat_completions(
        self,
        messages: Sequence["IBaseMessage"],
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """标准化的 chat_completions 实现
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 请求参数
            stream: 是否流式响应
            
        Returns:
            Union[LLMResponse, AsyncGenerator[str, None]]: 响应或流式生成器
            
        Raises:
            Exception: API调用失败
        """
        # 1. 标准化参数准备
        request_params = self._prepare_request_params(parameters, model, stream)
        
        # 2. 验证模型
        self._validate_model(model)
        
        try:
            # 3. 转换请求格式（使用提供商特定的 format_utils）
            request_data = self.format_utils.convert_request(messages, request_params)
            
            # 4. 获取端点路径（提供商特定）
            endpoint = self._get_endpoint_path(model)
            
            # 5. 记录调试信息
            self.logger.debug(
                f"调用 {self.get_provider_name()} API",
                extra={
                    "model": model,
                    "message_count": len(messages),
                    "stream": stream,
                    "parameters": list(request_params.keys())
                }
            )
            
            # 6. 执行请求
            if stream:
                return await self._stream_response(request_data, endpoint)
            else:
                response = await self.post(endpoint, request_data)
                return self._convert_response(response, model)
                
        except Exception as e:
            self.logger.error(f"{self.get_provider_name()} API调用失败: {e}")
            raise
    
    # ========== 子类必须实现 ==========
    
    @abstractmethod
    def _get_endpoint_path(self, model: Optional[str] = None) -> str:
        """获取API端点路径
        
        Args:
            model: 模型名称（某些提供商需要）
            
        Returns:
            str: 相对于 base_url 的端点路径
            
        Examples:
            - Anthropic: "messages"
            - OpenAI: "chat/completions"
            - Gemini: "models/{model}:generateContent"
        """
        pass
    
    @abstractmethod
    async def _stream_response(
        self, request_data: Dict[str, Any], endpoint: str
    ) -> AsyncGenerator[str, None]:
        """处理流式响应
        
        Args:
            request_data: 转换后的请求数据
            endpoint: API端点路径
            
        Yields:
            str: 流式响应的文本片段
        """
        pass
    
    @abstractmethod
    def _convert_response(self, response: Response, model: str) -> LLMResponse:
        """转换HTTP响应为LLMResponse
        
        Args:
            response: httpx.Response 对象
            model: 模型名称
            
        Returns:
            LLMResponse: 标准化的LLM响应对象
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称
        
        Returns:
            str: 提供商名称（如 "anthropic", "openai", "gemini"）
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型名称列表
        """
        pass
    
    # ========== 子类可选覆盖 ==========
    
    def _prepare_request_params(
        self,
        parameters: Optional[Dict[str, Any]],
        model: str,
        stream: bool
    ) -> Dict[str, Any]:
        """准备请求参数
        
        子类可覆盖此方法以添加提供商特定的参数准备逻辑。
        
        Args:
            parameters: 传入的参数
            model: 模型名称
            stream: 是否流式
            
        Returns:
            Dict[str, Any]: 准备好的请求参数
        """
        request_params = parameters or {}
        request_params["model"] = model
        request_params["stream"] = stream
        return request_params
    
    def _validate_model(self, model: str) -> None:
        """验证模型是否支持
        
        Args:
            model: 模型名称
        """
        if model not in self.SUPPORTED_MODELS:
            self.logger.warning(
                f"模型 {model} 不在官方支持列表中，但仍会尝试调用"
            )
```

### 步骤 1.2: 迁移 AnthropicHttpClient

**修改：** `src/infrastructure/llm/http_client/anthropic_http_client.py`

```python
"""Anthropic HTTP客户端实现 - 统一接口版本

已迁移到 ProviderHttpClient 基类。
"""

import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from httpx import Response

from src.infrastructure.llm.http_client.provider_http_client import ProviderHttpClient
from src.infrastructure.llm.converters.anthropic.anthropic_format_utils import AnthropicFormatUtils
from src.infrastructure.llm.models import LLMResponse, TokenUsage


class AnthropicHttpClient(ProviderHttpClient):
    """Anthropic HTTP客户端
    
    实现Anthropic Claude API的HTTP通信。
    """
    
    # 支持的模型列表
    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307",
        "claude-4-opus",
        "claude-4-sonnet",
        "claude-4-haiku"
    ]
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs: Any
    ):
        """初始化Anthropic HTTP客户端"""
        if base_url is None:
            base_url = "https://api.anthropic.com"
        
        default_headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        super().__init__(base_url=base_url, default_headers=default_headers, **kwargs)
        self.format_utils = AnthropicFormatUtils()
        self.api_key = api_key
        
        self.logger.info("初始化Anthropic HTTP客户端")
    
    def _get_endpoint_path(self, model: Optional[str] = None) -> str:
        """Anthropic API端点"""
        return "messages"
    
    async def _stream_response(
        self, request_data: Dict[str, Any], endpoint: str
    ) -> AsyncGenerator[str, None]:
        """处理Anthropic流式响应"""
        try:
            async for chunk in self.stream_post(endpoint, request_data):
                if chunk.startswith("data: "):
                    data_str = chunk[6:]
                    
                    # 跳过事件标记
                    if data_str.startswith("event: "):
                        continue
                    
                    try:
                        data = json.loads(data_str)
                        content = self._extract_stream_content(data)
                        if content:
                            yield content
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"解析流式数据失败: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"处理流式响应失败: {e}")
            raise
    
    def _convert_response(self, response: Response, model: str) -> LLMResponse:
        """转换Anthropic响应"""
        try:
            data = response.json()
            
            # 使用格式转换器转换响应
            message = self.format_utils.convert_response(data)
            
            # 提取token使用情况
            usage = data.get("usage", {})
            token_usage = TokenUsage(
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            )
            
            # 确保内容是字符串类型
            content = message.content if hasattr(message, 'content') else str(message)
            content_str = content if isinstance(content, str) else str(content)
            
            return LLMResponse(
                content=content_str,
                message=message,
                token_usage=token_usage,
                model=model,
                finish_reason=data.get("stop_reason"),
                metadata={
                    "id": data.get("id"),
                    "type": data.get("type"),
                    "usage": usage
                }
            )
            
        except Exception as e:
            self.logger.error(f"转换响应失败: {e}")
            raise
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "anthropic"
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return self.SUPPORTED_MODELS.copy()
    
    # ========== Anthropic 特定方法 ==========
    
    def _extract_stream_content(self, data: Dict[str, Any]) -> Optional[str]:
        """从Anthropic流式响应中提取内容"""
        try:
            if data.get("type") == "content_block_delta":
                delta = data.get("delta", {})
                return delta.get("text")
            
            elif data.get("type") == "message_start":
                message = data.get("message", {})
                content = message.get("content", [])
                if content and isinstance(content, list):
                    return content[0].get("text")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"提取流式内容失败: {e}")
            return None
```

### 步骤 1.3: 迁移其他HTTP客户端

对 `OpenAIHttpClient` 和 `GeminiHttpClient` 应用相同的模式：

**关键点：**
- 继承 `ProviderHttpClient` 而不是 `BaseHttpClient`
- 删除重复的 `chat_completions()` 实现
- 只实现 4 个必需的抽象方法
- 保留提供商特定的私有方法

### 步骤 1.4: 创建统一的 HttpClientFactory

**文件：** `src/infrastructure/llm/http_client/http_client_factory.py`

```python
"""HTTP客户端工厂 - 统一创建所有提供商的客户端"""

from typing import Type, Dict, Optional, Any

from src.interfaces.llm.http_client import ILLMHttpClient
from src.infrastructure.llm.http_client.anthropic_http_client import AnthropicHttpClient
from src.infrastructure.llm.http_client.openai_http_client import OpenAIHttpClient
from src.infrastructure.llm.http_client.gemini_http_client import GeminiHttpClient
from src.services.logger import get_logger


class HttpClientFactory:
    """统一的 HTTP 客户端工厂
    
    负责创建和管理所有提供商的 HTTP 客户端实例。
    """
    
    _registry: Dict[str, Type[ILLMHttpClient]] = {
        "anthropic": AnthropicHttpClient,
        "openai": OpenAIHttpClient,
        "gemini": GeminiHttpClient,
    }
    
    _logger = get_logger(__name__)
    
    @classmethod
    def create_client(
        cls,
        provider: str,
        api_key: str,
        **kwargs: Any
    ) -> ILLMHttpClient:
        """创建 HTTP 客户端
        
        Args:
            provider: 提供商名称 ("anthropic", "openai", "gemini")
            api_key: API密钥
            **kwargs: 其他参数（base_url, timeout, max_retries等）
            
        Returns:
            ILLMHttpClient: HTTP客户端实例
            
        Raises:
            ValueError: 如果提供商不支持
        """
        provider_lower = provider.lower()
        
        if provider_lower not in cls._registry:
            supported = ", ".join(cls._registry.keys())
            raise ValueError(
                f"不支持的提供商: {provider}\n"
                f"支持的提供商: {supported}"
            )
        
        client_class = cls._registry[provider_lower]
        
        cls._logger.info(
            f"创建 {provider} HTTP 客户端",
            extra={"kwargs_keys": list(kwargs.keys())}
        )
        
        return client_class(api_key=api_key, **kwargs)
    
    @classmethod
    def register_client(
        cls,
        provider: str,
        client_class: Type[ILLMHttpClient]
    ) -> None:
        """注册新的客户端
        
        Args:
            provider: 提供商名称
            client_class: 客户端类
        """
        cls._registry[provider.lower()] = client_class
        cls._logger.info(f"已注册 {provider} 客户端: {client_class.__name__}")
    
    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """获取支持的提供商列表"""
        return list(cls._registry.keys())
    
    @classmethod
    def is_provider_supported(cls, provider: str) -> bool:
        """检查提供商是否支持"""
        return provider.lower() in cls._registry
```

### 步骤 1.5: 更新 __init__.py

**文件：** `src/infrastructure/llm/http_client/__init__.py`

```python
"""HTTP客户端模块"""

from src.infrastructure.llm.http_client.provider_http_client import ProviderHttpClient
from src.infrastructure.llm.http_client.anthropic_http_client import AnthropicHttpClient
from src.infrastructure.llm.http_client.openai_http_client import OpenAIHttpClient
from src.infrastructure.llm.http_client.gemini_http_client import GeminiHttpClient
from src.infrastructure.llm.http_client.http_client_factory import HttpClientFactory

__all__ = [
    "ProviderHttpClient",
    "AnthropicHttpClient",
    "OpenAIHttpClient",
    "GeminiHttpClient",
    "HttpClientFactory",
]
```

---

## Phase 2: Core 层简化

### 步骤 2.1: 更新 BaseLLMClient

**修改：** `src/core/llm/clients/base.py`

关键变更：
- 使用 `HttpClientFactory` 创建 HTTP 客户端
- 删除提供商特定的初始化逻辑
- 标准化 `_do_generate_async()` 和 `_do_stream_generate_async()`

```python
# 在 __init__ 中
def __init__(self, config: LLMClientConfig) -> None:
    super().__init__(config)
    
    # 使用工厂创建 HTTP 客户端
    from src.infrastructure.llm.http_client.http_client_factory import HttpClientFactory
    
    self._http_client = HttpClientFactory.create_client(
        provider=config.model_type,
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
        max_retries=config.max_retries
    )
```

### 步骤 2.2: 简化 AnthropicClient

**修改：** `src/core/llm/clients/anthropic.py`

完全重写，只保留配置特定的逻辑：

```python
"""Anthropic客户端实现"""

from typing import Dict, Any, Optional, AsyncGenerator, Sequence

from src.interfaces.messages import IBaseMessage
from src.interfaces.llm import LLMResponse
from .base import BaseLLMClient
from ..config import AnthropicConfig


class AnthropicClient(BaseLLMClient):
    """Anthropic客户端实现
    
    简化版：完全依赖 Infrastructure 层的 AnthropicHttpClient
    """
    
    def __init__(self, config: AnthropicConfig) -> None:
        """初始化Anthropic客户端"""
        super().__init__(config)
        self._config: AnthropicConfig = config
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        return getattr(self._config, 'function_calling_supported', True)
    
    def _prepare_parameters(
        self, parameters: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        """准备HTTP请求参数"""
        params = {
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens or 1024,
        }
        
        # 添加 Anthropic 特定参数
        if hasattr(self._config, 'top_p') and self._config.top_p != 1.0:
            params["top_p"] = self._config.top_p
        
        if hasattr(self._config, 'stop_sequences') and self._config.stop_sequences:
            params["stop_sequences"] = self._config.stop_sequences
        
        if hasattr(self._config, 'thinking_config') and self._config.thinking_config:
            params["thinking_config"] = self._config.thinking_config
        
        if hasattr(self._config, 'response_format') and self._config.response_format:
            params["response_format"] = self._config.response_format
        
        if hasattr(self._config, 'metadata') and self._config.metadata:
            params["metadata"] = self._config.metadata
        
        if hasattr(self._config, 'user') and self._config.user:
            params["user"] = self._config.user
        
        # 工具调用参数
        if hasattr(self._config, 'tools') and self._config.tools:
            params["tools"] = self._config.tools
            if hasattr(self._config, 'tool_choice') and self._config.tool_choice:
                params["tool_choice"] = self._config.tool_choice
        
        # 合并传入参数
        params.update(parameters)
        params.update(kwargs)
        
        return params


# 注意：所有通用的 _do_generate_async 和 _do_stream_generate_async
# 已在 BaseLLMClient 中实现，无需覆盖
```

---

## Phase 3: 测试与验证

### 步骤 3.1: 创建单元测试

**文件：** `tests/infrastructure/llm/http_client/test_provider_http_client.py`

```python
"""测试通用的 ProviderHttpClient 基类"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import Response

from src.infrastructure.llm.http_client.provider_http_client import ProviderHttpClient
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.messages import AIMessage, HumanMessage


class ConcreteProviderClient(ProviderHttpClient):
    """具体的测试实现"""
    
    SUPPORTED_MODELS = ["test-model"]
    
    def __init__(self):
        super().__init__(base_url="https://api.test.com")
        self.format_utils = MagicMock()
    
    def _get_endpoint_path(self, model=None):
        return "test/endpoint"
    
    async def _stream_response(self, request_data, endpoint):
        async def _gen():
            yield "test"
        return _gen()
    
    def _convert_response(self, response, model):
        return LLMResponse(
            content="test",
            token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1),
            model=model
        )
    
    def get_provider_name(self):
        return "test"
    
    def get_supported_models(self):
        return self.SUPPORTED_MODELS


@pytest.mark.asyncio
async def test_chat_completions_non_stream():
    """测试非流式调用"""
    client = ConcreteProviderClient()
    client.format_utils.convert_request = MagicMock(
        return_value={"test": "data"}
    )
    client.post = AsyncMock(
        return_value=MagicMock(json=lambda: {})
    )
    
    messages = [HumanMessage(content="test")]
    result = await client.chat_completions(
        messages=messages,
        model="test-model",
        stream=False
    )
    
    assert isinstance(result, LLMResponse)
    assert result.content == "test"


@pytest.mark.asyncio
async def test_chat_completions_stream():
    """测试流式调用"""
    client = ConcreteProviderClient()
    client.format_utils.convert_request = MagicMock(
        return_value={"test": "data"}
    )
    
    messages = [HumanMessage(content="test")]
    result = await client.chat_completions(
        messages=messages,
        model="test-model",
        stream=True
    )
    
    # 应该返回异步生成器
    assert hasattr(result, '__aiter__')
```

### 步骤 3.2: 创建集成测试

**文件：** `tests/infrastructure/llm/http_client/test_http_client_factory.py`

```python
"""测试 HttpClientFactory"""

import pytest
from src.infrastructure.llm.http_client.http_client_factory import HttpClientFactory
from src.infrastructure.llm.http_client import (
    AnthropicHttpClient,
    OpenAIHttpClient,
    GeminiHttpClient
)


def test_factory_create_anthropic():
    """测试创建 Anthropic 客户端"""
    client = HttpClientFactory.create_client(
        provider="anthropic",
        api_key="test-key"
    )
    
    assert isinstance(client, AnthropicHttpClient)
    assert client.get_provider_name() == "anthropic"


def test_factory_create_openai():
    """测试创建 OpenAI 客户端"""
    client = HttpClientFactory.create_client(
        provider="openai",
        api_key="test-key"
    )
    
    assert isinstance(client, OpenAIHttpClient)
    assert client.get_provider_name() == "openai"


def test_factory_create_gemini():
    """测试创建 Gemini 客户端"""
    client = HttpClientFactory.create_client(
        provider="gemini",
        api_key="test-key"
    )
    
    assert isinstance(client, GeminiHttpClient)
    assert client.get_provider_name() == "gemini"


def test_factory_unsupported_provider():
    """测试不支持的提供商"""
    with pytest.raises(ValueError):
        HttpClientFactory.create_client(
            provider="unsupported",
            api_key="test-key"
        )


def test_factory_get_supported_providers():
    """测试获取支持的提供商列表"""
    providers = HttpClientFactory.get_supported_providers()
    
    assert "anthropic" in providers
    assert "openai" in providers
    assert "gemini" in providers
```

### 步骤 3.3: 运行现有测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 只运行 LLM 相关测试
uv run pytest tests/infrastructure/llm/ tests/core/llm/ -v

# 运行特定测试文件
uv run pytest tests/infrastructure/llm/http_client/ -v
```

### 步骤 3.4: 代码质量检查

```bash
# 类型检查
uv run mypy src/infrastructure/llm/http_client/ --follow-imports=silent

# 代码风格
uv run flake8 src/infrastructure/llm/http_client/

# 复杂度分析
uv run radon cc src/infrastructure/llm/http_client/ -a
```

---

## Phase 4: 验证和优化

### 检查清单

- [ ] 所有测试通过
- [ ] 代码复杂度降低 > 50%
- [ ] 类型检查通过
- [ ] 代码重复率 < 5%
- [ ] 文档更新完成
- [ ] 向后兼容性验证
- [ ] 性能基准测试无退化

### 代码度量目标

| 指标 | 当前 | 目标 |
|-----|-----|-----|
| **HTTP客户端代码行数** | 1000+ | 500 |
| **Core层客户端行数** | 450+ | 100 |
| **重复代码行数** | 700+ | <50 |
| **重复率** | 70% | <5% |
| **平均方法长度** | 30 行 | <20 行 |
| **圈复杂度** | 5-8 | <4 |

---

## 迁移后的架构图

```
┌─────────────────────────────────┐
│       Core Layer Clients         │
│  (AnthropicClient, OpenAI...)   │
│  ≈ 50-100 行 / 个               │
└──────────────┬──────────────────┘
               │
               │ 使用 ILLMHttpClient
               │ (统一接口)
               ▼
┌─────────────────────────────────┐
│    ProviderHttpClient 基类       │
│  (统一的 chat_completions)      │
│  ≈ 100 行                       │
└──────┬──────────────┬──────┬────┘
       │              │      │
       ▼              ▼      ▼
   Anthropic      OpenAI   Gemini
   Client         Client   Client
   ≈ 100 行       ≈ 150    ≈ 150

┌─────────────────────────────────┐
│     HttpClientFactory           │
│  统一创建和管理客户端             │
│  ≈ 80 行                        │
└─────────────────────────────────┘
```

---

## 回滚计划

如果遇到问题，可以按以下步骤回滚：

1. **保留原始文件的备份**
   ```bash
   git stash
   git checkout src/infrastructure/llm/http_client/
   git checkout src/core/llm/clients/
   ```

2. **逐步回滚**
   - 先回滚 Core 层
   - 然后回滚 Infrastructure 层

3. **测试回滚**
   ```bash
   uv run pytest tests/ -v
   ```

---

## 文档更新

需要更新的文档：

1. `docs/ARCHITECTURE.md` - 更新架构图
2. `docs/HTTP_CLIENT_USAGE.md` - 新增或更新使用指南
3. `src/infrastructure/llm/http_client/README.md` - 创建说明文档
4. `AGENTS.md` - 更新开发指南

---

## 预期收益

### 代码质量
- ✓ 代码重复率从 70% 降低到 < 5%
- ✓ 代码行数从 1000+ 降低到 500
- ✓ 方法复杂度降低 50%+
- ✓ 单元测试覆盖率提升 20%+

### 可维护性
- ✓ 添加新提供商只需 100 行代码
- ✓ 修改通用逻辑只需改一个地方
- ✓ 接口一致性 100%
- ✓ 类型安全完全保证

### 性能
- ✓ 无性能退化
- ✓ 内存占用可能降低 (代码重复减少)
- ✓ 初始化时间无变化

