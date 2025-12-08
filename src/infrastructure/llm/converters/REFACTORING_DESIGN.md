# LLM Converters 重构设计方案

## 1. 重构后的目录结构

```
src/infrastructure/llm/converters/
├── core/                           # 核心抽象和接口
│   ├── __init__.py
│   ├── interfaces.py               # 核心接口定义
│   ├── base_converter.py           # 统一的基础转换器
│   ├── conversion_context.py       # 转换上下文
│   └── conversion_pipeline.py      # 转换管道
├── common/                         # 通用工具和处理器
│   ├── __init__.py
│   ├── content_processors.py       # 内容处理器（重构后）
│   ├── error_handlers.py           # 错误处理器
│   ├── validators.py               # 验证器
│   ├── utils.py                    # 通用工具
│   └── patterns.py                 # 设计模式实现
├── providers/                      # 提供商实现
│   ├── __init__.py
│   ├── base/                       # 提供商基础类
│   │   ├── __init__.py
│   │   ├── provider_base.py        # 提供商基础实现
│   │   └── provider_factory.py     # 提供商工厂
│   ├── openai/                     # OpenAI 实现
│   │   ├── __init__.py
│   │   ├── openai_provider.py      # OpenAI 提供商实现
│   │   ├── openai_config.py        # OpenAI 配置
│   │   └── adapters/               # 适配器
│   │       ├── __init__.py
│   │       ├── multimodal_adapter.py
│   │       ├── stream_adapter.py
│   │       ├── tools_adapter.py
│   │       └── validation_adapter.py
│   ├── anthropic/                  # Anthropic 实现
│   │   ├── __init__.py
│   │   ├── anthropic_provider.py   # Anthropic 提供商实现
│   │   ├── anthropic_config.py     # Anthropic 配置
│   │   └── adapters/               # 适配器
│   │       ├── __init__.py
│   │       ├── multimodal_adapter.py
│   │       ├── stream_adapter.py
│   │       ├── tools_adapter.py
│   │       └── validation_adapter.py
│   ├── gemini/                     # Gemini 实现
│   │   ├── __init__.py
│   │   ├── gemini_provider.py      # Gemini 提供商实现
│   │   ├── gemini_config.py        # Gemini 配置
│   │   └── adapters/               # 适配器
│   │       ├── __init__.py
│   │       ├── multimodal_adapter.py
│   │       ├── stream_adapter.py
│   │       ├── tools_adapter.py
│   │       └── validation_adapter.py
│   └── openai_responses/           # OpenAI Responses 实现
│       ├── __init__.py
│       ├── openai_responses_provider.py
│       ├── openai_responses_config.py
│       └── adapters/
│           ├── __init__.py
│           ├── multimodal_adapter.py
│           ├── stream_adapter.py
│           ├── tools_adapter.py
│           └── validation_adapter.py
├── converters/                     # 转换器实现
│   ├── __init__.py
│   ├── message_converter.py        # 消息转换器（重构后）
│   ├── request_converter.py        # 请求转换器
│   ├── response_converter.py       # 响应转换器
│   ├── format_converter.py         # 格式转换器
│   └── factory.py                  # 转换器工厂
├── registry/                       # 注册中心
│   ├── __init__.py
│   ├── provider_registry.py        # 提供商注册中心
│   └── converter_registry.py       # 转换器注册中心
└── __init__.py                     # 主入口
```

## 2. 核心设计模式

### 2.1 策略模式 (Strategy Pattern)
用于处理不同提供商的转换策略：
```python
class ConversionStrategy(ABC):
    @abstractmethod
    def convert(self, context: ConversionContext) -> Any:
        pass

class OpenAIStrategy(ConversionStrategy):
    def convert(self, context: ConversionContext) -> Any:
        # OpenAI 特定的转换逻辑
        pass
```

### 2.2 工厂模式 (Factory Pattern)
用于创建不同提供商的转换器：
```python
class ProviderFactory:
    @staticmethod
    def create_provider(provider_name: str) -> IProvider:
        # 根据名称创建对应的提供商实例
        pass
```

### 2.3 适配器模式 (Adapter Pattern)
用于统一不同提供商的接口：
```python
class MultimodalAdapter(ABC):
    @abstractmethod
    def process_content(self, content: Any) -> Any:
        pass

class OpenAIMultimodalAdapter(MultimodalAdapter):
    def process_content(self, content: Any) -> Any:
        # OpenAI 特定的多模态处理
        pass
```

### 2.4 模板方法模式 (Template Method Pattern)
用于定义通用的转换流程：
```python
class BaseConverter:
    def convert(self, context: ConversionContext) -> Any:
        self.validate(context)
        self.prepare(context)
        result = self.do_convert(context)
        self.post_process(context, result)
        return result
    
    @abstractmethod
    def do_convert(self, context: ConversionContext) -> Any:
        pass
```

## 3. 核心接口设计

### 3.1 提供商接口
```python
class IProvider(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def convert_request(self, messages: List[IBaseMessage], params: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def convert_response(self, response: Dict[str, Any]) -> IBaseMessage:
        pass
    
    @abstractmethod
    def convert_stream_response(self, events: List[Dict[str, Any]]) -> IBaseMessage:
        pass
```

### 3.2 转换器接口
```python
class IConverter(ABC):
    @abstractmethod
    def can_convert(self, source_type: type, target_type: type) -> bool:
        pass
    
    @abstractmethod
    def convert(self, source: Any, context: ConversionContext) -> Any:
        pass
```

### 3.3 适配器接口
```python
class IMultimodalAdapter(ABC):
    @abstractmethod
    def process_content_to_provider_format(self, content: Any) -> Any:
        pass
    
    @abstractmethod
    def extract_text_from_provider_content(self, content: Any) -> str:
        pass
    
    @abstractmethod
    def validate_provider_content(self, content: Any) -> List[str]:
        pass
```

## 4. 具体重构实现

### 4.1 统一的基础转换器
```python
class BaseConverter(IConverter):
    def __init__(self, provider: IProvider):
        self.provider = provider
        self.logger = get_logger(__name__)
    
    def convert(self, source: Any, context: ConversionContext) -> Any:
        try:
            self.validate_input(source, context)
            self.prepare_context(context)
            result = self.do_convert(source, context)
            return self.post_process(result, context)
        except Exception as e:
            self.handle_error(e, context)
            raise
    
    @abstractmethod
    def do_convert(self, source: Any, context: ConversionContext) -> Any:
        pass
    
    def validate_input(self, source: Any, context: ConversionContext) -> None:
        # 通用验证逻辑
        pass
    
    def prepare_context(self, context: ConversionContext) -> None:
        # 上下文准备逻辑
        pass
    
    def post_process(self, result: Any, context: ConversionContext) -> Any:
        # 后处理逻辑
        return result
    
    def handle_error(self, error: Exception, context: ConversionContext) -> None:
        # 错误处理逻辑
        self.logger.error(f"转换失败: {error}")
```

### 4.2 提供商基础实现
```python
class BaseProvider(IProvider):
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.multimodal_adapter = self.create_multimodal_adapter()
        self.stream_adapter = self.create_stream_adapter()
        self.tools_adapter = self.create_tools_adapter()
        self.validation_adapter = self.create_validation_adapter()
    
    @abstractmethod
    def create_multimodal_adapter(self) -> IMultimodalAdapter:
        pass
    
    @abstractmethod
    def create_stream_adapter(self) -> IStreamAdapter:
        pass
    
    @abstractmethod
    def create_tools_adapter(self) -> IToolsAdapter:
        pass
    
    @abstractmethod
    def create_validation_adapter(self) -> IValidationAdapter:
        pass
    
    def convert_request(self, messages: List[IBaseMessage], params: Dict[str, Any]) -> Dict[str, Any]:
        # 模板方法实现
        self.validate_request_params(params)
        processed_messages = self.process_messages(messages)
        request_data = self.build_request(processed_messages, params)
        return request_data
    
    def validate_request_params(self, params: Dict[str, Any]) -> None:
        errors = self.validation_adapter.validate_request_params(params)
        if errors:
            raise ValidationError(f"请求参数验证失败: {errors}")
    
    @abstractmethod
    def process_messages(self, messages: List[IBaseMessage]) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def build_request(self, messages: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        pass
```

### 4.3 OpenAI 提供商实现
```python
class OpenAIProvider(BaseProvider):
    def __init__(self, config: OpenAIConfig):
        super().__init__(config)
    
    def get_name(self) -> str:
        return "openai"
    
    def create_multimodal_adapter(self) -> IMultimodalAdapter:
        return OpenAIMultimodalAdapter(self.config)
    
    def create_stream_adapter(self) -> IStreamAdapter:
        return OpenAIStreamAdapter(self.config)
    
    def create_tools_adapter(self) -> IToolsAdapter:
        return OpenAIToolsAdapter(self.config)
    
    def create_validation_adapter(self) -> IValidationAdapter:
        return OpenAIValidationAdapter(self.config)
    
    def process_messages(self, messages: List[IBaseMessage]) -> List[Dict[str, Any]]:
        processed_messages = []
        for message in messages:
            processed_message = self._process_single_message(message)
            if processed_message:
                processed_messages.append(processed_message)
        return processed_messages
    
    def _process_single_message(self, message: IBaseMessage) -> Optional[Dict[str, Any]]:
        if isinstance(message, SystemMessage):
            return self._process_system_message(message)
        elif isinstance(message, HumanMessage):
            return self._process_human_message(message)
        elif isinstance(message, AIMessage):
            return self._process_ai_message(message)
        elif isinstance(message, ToolMessage):
            return self._process_tool_message(message)
        else:
            self.logger.warning(f"不支持的消息类型: {type(message)}")
            return None
    
    def _process_system_message(self, message: SystemMessage) -> Dict[str, Any]:
        content = self.multimodal_adapter.process_content_to_provider_format(message.content)
        return {
            "role": "system",
            "content": content,
            "name": message.name
        }
    
    # 其他消息处理方法...
    
    def build_request(self, messages: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        request_data = {
            "model": params.get("model", "gpt-3.5-turbo"),
            "messages": messages
        }
        
        # 添加可选参数
        optional_params = [
            "temperature", "top_p", "n", "stream", "stop", 
            "max_tokens", "presence_penalty", "frequency_penalty"
        ]
        
        for param in optional_params:
            if param in params:
                request_data[param] = params[param]
        
        # 处理工具配置
        if "tools" in params:
            tools = params["tools"]
            request_data["tools"] = self.tools_adapter.convert_tools_to_provider_format(tools)
            
            if "tool_choice" in params:
                request_data["tool_choice"] = self.tools_adapter.process_tool_choice(
                    params["tool_choice"]
                )
        
        return request_data
```

### 4.4 转换器工厂
```python
class ConverterFactory:
    def __init__(self, provider_registry: ProviderRegistry):
        self.provider_registry = provider_registry
        self.logger = get_logger(__name__)
    
    def create_converter(self, converter_type: str, provider_name: str) -> IConverter:
        provider = self.provider_registry.get_provider(provider_name)
        
        if converter_type == "message":
            return MessageConverter(provider)
        elif converter_type == "request":
            return RequestConverter(provider)
        elif converter_type == "response":
            return ResponseConverter(provider)
        elif converter_type == "format":
            return FormatConverter(provider)
        else:
            raise ValueError(f"不支持的转换器类型: {converter_type}")
    
    def create_message_converter(self, provider_name: str) -> MessageConverter:
        return self.create_converter("message", provider_name)
    
    def create_request_converter(self, provider_name: str) -> RequestConverter:
        return self.create_converter("request", provider_name)
    
    def create_response_converter(self, provider_name: str) -> ResponseConverter:
        return self.create_converter("response", provider_name)
```

### 4.5 提供商注册中心
```python
class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, IProvider] = {}
        self._configs: Dict[str, ProviderConfig] = {}
        self.logger = get_logger(__name__)
    
    def register_provider(self, name: str, provider: IProvider, config: ProviderConfig) -> None:
        self._providers[name] = provider
        self._configs[name] = config
        self.logger.info(f"已注册提供商: {name}")
    
    def get_provider(self, name: str) -> IProvider:
        if name not in self._providers:
            raise ValueError(f"未找到提供商: {name}")
        return self._providers[name]
    
    def get_config(self, name: str) -> ProviderConfig:
        if name not in self._configs:
            raise ValueError(f"未找到提供商配置: {name}")
        return self._configs[name]
    
    def list_providers(self) -> List[str]:
        return list(self._providers.keys())
    
    def unregister_provider(self, name: str) -> None:
        if name in self._providers:
            del self._providers[name]
            del self._configs[name]
            self.logger.info(f"已注销提供商: {name}")
```

## 5. 重构收益

### 5.1 代码减少
- 预计减少重复代码 40-50%
- 文件数量从 24 个减少到约 35 个（结构更清晰）
- 单个文件的平均代码行数减少 30%

### 5.2 可维护性提升
- 清晰的职责分离
- 统一的设计模式
- 更好的抽象层次

### 5.3 可扩展性提升
- 新增提供商只需实现 4 个适配器类
- 支持动态注册新提供商
- 插件化的架构设计

### 5.4 性能优化
- 减少重复的对象创建
- 更好的缓存机制
- 优化的转换流程

## 6. 迁移策略

### 6.1 渐进式迁移
1. 保持现有 API 兼容性
2. 逐步替换内部实现
3. 提供适配器确保平滑过渡

### 6.2 向后兼容
```python
# 保持现有 API 的兼容性
class MessageConverter:
    def __init__(self):
        # 内部使用新的实现
        self._factory = ConverterFactory(provider_registry)
    
    def to_base_message(self, message: Any) -> IBaseMessage:
        # 委托给新的实现
        converter = self._factory.create_message_converter("auto")
        return converter.convert_to_base(message)
```

### 6.3 测试策略
1. 为每个重构的组件编写单元测试
2. 保持现有集成测试的通过
3. 添加性能测试确保无回归

这个重构设计方案通过引入清晰的设计模式和抽象层次，显著减少了代码重复，提高了系统的可维护性和可扩展性。