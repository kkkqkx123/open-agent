"""LLM模块配置定义"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path

from config.models.llm_config import LLMConfig


@dataclass
class LLMClientConfig:
    """LLM客户端配置"""
    # 基础配置
    model_type: str
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    # 请求配置
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    max_retries: int = 3
    
    # 内部状态
    _resolved_headers: Optional[Dict[str, str]] = field(default=None, init=False)
    _sanitized_headers: Optional[Dict[str, str]] = field(default=None, init=False)
    
    # 参数配置
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # 高级配置
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None
    
    # 降级配置
    fallback_enabled: bool = True
    fallback_models: List[str] = field(default_factory=list)
    max_fallback_attempts: int = 3
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_llm_config(cls, config: LLMConfig) -> 'LLMClientConfig':
        """从LLMConfig创建LLMClientConfig"""
        # 提取参数
        parameters = config.parameters or {}
        
        return cls(
            model_type=config.model_type,
            model_name=config.model_name,
            base_url=config.base_url,
            api_key=config.api_key,
            headers=config.headers,
            timeout=parameters.get('timeout', 30),
            max_retries=parameters.get('max_retries', 3),
            temperature=parameters.get('temperature', 0.7),
            max_tokens=parameters.get('max_tokens'),
            top_p=parameters.get('top_p', 1.0),
            frequency_penalty=parameters.get('frequency_penalty', 0.0),
            presence_penalty=parameters.get('presence_penalty', 0.0),
            stream=parameters.get('stream', False),
            functions=parameters.get('functions'),
            function_call=parameters.get('function_call'),
            fallback_enabled=parameters.get('fallback_enabled', True),
            fallback_models=parameters.get('fallback_models', []),
            max_fallback_attempts=parameters.get('max_fallback_attempts', 3),
            metadata=parameters.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": self.stream,
            "fallback_enabled": self.fallback_enabled,
            "max_fallback_attempts": self.max_fallback_attempts
        }
        
        if self.base_url:
            result["base_url"] = self.base_url
            
        if self.api_key:
            result["api_key"] = "***"  # 隐藏API密钥
            
        if self.headers:
            # 使用脱敏后的标头
            result["headers"] = self.get_sanitized_headers()
            
        if self.max_tokens:
            result["max_tokens"] = self.max_tokens
            
        if self.functions:
            result["functions"] = self.functions
            
        if self.function_call:
            result["function_call"] = self.function_call
            
        if self.fallback_models:
            result["fallback_models"] = self.fallback_models
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    def get_resolved_headers(self) -> Dict[str, str]:
        """获取解析后的请求头（已解析环境变量）"""
        if self._resolved_headers is not None:
            return self._resolved_headers.copy()
        
        # 解析标头
        from .header_validator import HeaderProcessor
        processor = HeaderProcessor()
        resolved_headers, _, is_valid, errors = processor.process_headers(self.headers)
        
        if not is_valid:
            raise ValueError(f"HTTP标头验证失败: {'; '.join(errors)}")
        
        # 处理API密钥
        headers = resolved_headers.copy()
        if self.api_key:
            from .header_validator import HeaderValidator
            validator = HeaderValidator()
            
            if validator._is_env_var_reference(self.api_key):
                # 解析环境变量
                resolved_key = validator._resolve_env_var(self.api_key)
                if resolved_key:
                    # 根据模型类型设置不同的认证头
                    if self.model_type == 'openai':
                        headers['Authorization'] = f'Bearer {resolved_key}'
                    elif self.model_type == 'gemini':
                        headers['x-goog-api-key'] = resolved_key
                    elif self.model_type == 'anthropic':
                        headers['x-api-key'] = resolved_key
            else:
                # 直接使用API密钥
                if self.model_type == 'openai':
                    headers['Authorization'] = f'Bearer {self.api_key}'
                elif self.model_type == 'gemini':
                    headers['x-goog-api-key'] = self.api_key
                elif self.model_type == 'anthropic':
                    headers['x-api-key'] = self.api_key
        
        # 缓存结果
        self._resolved_headers = headers
        
        return headers
    
    def get_sanitized_headers(self) -> Dict[str, str]:
        """获取脱敏后的请求头（用于日志记录）"""
        if self._sanitized_headers is not None:
            return self._sanitized_headers.copy()
        
        # 获取原始标头
        headers = self.headers.copy()
        
        # 处理API密钥
        if self.api_key:
            # 根据模型类型设置不同的认证头
            if self.model_type == 'openai':
                headers['Authorization'] = self.api_key
            elif self.model_type == 'gemini':
                headers['x-goog-api-key'] = self.api_key
            elif self.model_type == 'anthropic':
                headers['x-api-key'] = self.api_key
        
        # 脱敏处理
        from .header_validator import HeaderValidator
        validator = HeaderValidator()
        sanitized_headers = validator.sanitize_headers_for_logging(headers)
        
        # 缓存结果
        self._sanitized_headers = sanitized_headers
        
        return sanitized_headers
    
    def validate_headers(self) -> Tuple[bool, List[str]]:
        """验证HTTP标头"""
        from .header_validator import HeaderValidator
        validator = HeaderValidator()
        return validator.validate_headers(self.headers)
    
    def merge_parameters(self, parameters: Dict[str, Any]) -> 'LLMClientConfig':
        """合并参数创建新配置"""
        # 创建新配置实例
        new_config = LLMClientConfig(
            model_type=self.model_type,
            model_name=self.model_name,
            base_url=self.base_url,
            api_key=self.api_key,
            headers=self.headers.copy(),
            timeout=self.timeout,
            max_retries=self.max_retries,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stream=self.stream,
            functions=self.functions.copy() if self.functions else None,
            function_call=self.function_call,
            fallback_enabled=self.fallback_enabled,
            fallback_models=self.fallback_models.copy(),
            max_fallback_attempts=self.max_fallback_attempts,
            metadata=self.metadata.copy()
        )
        
        # 更新参数
        for key, value in parameters.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
            else:
                new_config.metadata[key] = value
                
        return new_config
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LLMClientConfig':
        """从字典创建配置"""
        # 提取基础配置
        model_type = config_dict.get('model_type', 'openai')
        model_name = config_dict.get('model_name', 'gpt-3.5-turbo')
        
        # 根据模型类型创建特定配置
        if model_type == 'openai':
            from . import OpenAIConfig
            return OpenAIConfig(
                model_type=model_type,
                model_name=model_name,
                base_url=config_dict.get('base_url'),
                api_key=config_dict.get('api_key'),
                headers=config_dict.get('headers', {}),
                timeout=config_dict.get('timeout', 30),
                max_retries=config_dict.get('max_retries', 3),
                temperature=config_dict.get('temperature', 0.7),
                max_tokens=config_dict.get('max_tokens'),
                top_p=config_dict.get('top_p', 1.0),
                frequency_penalty=config_dict.get('frequency_penalty', 0.0),
                presence_penalty=config_dict.get('presence_penalty', 0.0),
                stream=config_dict.get('stream', False),
                functions=config_dict.get('functions'),
                function_call=config_dict.get('function_call'),
                fallback_enabled=config_dict.get('fallback_enabled', True),
                fallback_models=config_dict.get('fallback_models', []),
                max_fallback_attempts=config_dict.get('max_fallback_attempts', 3),
                metadata=config_dict.get('metadata', {})
            )
        elif model_type == 'gemini':
            from . import GeminiConfig
            return GeminiConfig(
                model_type=model_type,
                model_name=model_name,
                base_url=config_dict.get('base_url'),
                api_key=config_dict.get('api_key'),
                headers=config_dict.get('headers', {}),
                timeout=config_dict.get('timeout', 30),
                max_retries=config_dict.get('max_retries', 3),
                temperature=config_dict.get('temperature', 0.7),
                max_tokens=config_dict.get('max_tokens'),
                top_p=config_dict.get('top_p', 1.0),
                frequency_penalty=config_dict.get('frequency_penalty', 0.0),
                presence_penalty=config_dict.get('presence_penalty', 0.0),
                stream=config_dict.get('stream', False),
                functions=config_dict.get('functions'),
                function_call=config_dict.get('function_call'),
                fallback_enabled=config_dict.get('fallback_enabled', True),
                fallback_models=config_dict.get('fallback_models', []),
                max_fallback_attempts=config_dict.get('max_fallback_attempts', 3),
                metadata=config_dict.get('metadata', {})
            )
        elif model_type in ['anthropic', 'claude']:
            from . import AnthropicConfig
            return AnthropicConfig(
                model_type=model_type,
                model_name=model_name,
                base_url=config_dict.get('base_url'),
                api_key=config_dict.get('api_key'),
                headers=config_dict.get('headers', {}),
                timeout=config_dict.get('timeout', 30),
                max_retries=config_dict.get('max_retries', 3),
                temperature=config_dict.get('temperature', 0.7),
                max_tokens=config_dict.get('max_tokens'),
                top_p=config_dict.get('top_p', 1.0),
                frequency_penalty=config_dict.get('frequency_penalty', 0.0),
                presence_penalty=config_dict.get('presence_penalty', 0.0),
                stream=config_dict.get('stream', False),
                functions=config_dict.get('functions'),
                function_call=config_dict.get('function_call'),
                fallback_enabled=config_dict.get('fallback_enabled', True),
                fallback_models=config_dict.get('fallback_models', []),
                max_fallback_attempts=config_dict.get('max_fallback_attempts', 3),
                metadata=config_dict.get('metadata', {})
            )
        elif model_type == 'mock':
            from . import MockConfig
            return MockConfig(
                model_type=model_type,
                model_name=model_name,
                base_url=config_dict.get('base_url'),
                api_key=config_dict.get('api_key'),
                headers=config_dict.get('headers', {}),
                timeout=config_dict.get('timeout', 30),
                max_retries=config_dict.get('max_retries', 3),
                temperature=config_dict.get('temperature', 0.7),
                max_tokens=config_dict.get('max_tokens'),
                top_p=config_dict.get('top_p', 1.0),
                frequency_penalty=config_dict.get('frequency_penalty', 0.0),
                presence_penalty=config_dict.get('presence_penalty', 0.0),
                stream=config_dict.get('stream', False),
                functions=config_dict.get('functions'),
                function_call=config_dict.get('function_call'),
                fallback_enabled=config_dict.get('fallback_enabled', True),
                fallback_models=config_dict.get('fallback_models', []),
                max_fallback_attempts=config_dict.get('max_fallback_attempts', 3),
                metadata=config_dict.get('metadata', {}),
                response_delay=config_dict.get('response_delay', 0.1),
                error_rate=config_dict.get('error_rate', 0.0),
                error_types=config_dict.get('error_types', ['timeout', 'rate_limit'])
            )
        else:
            # 默认创建基础配置
            return cls(
                model_type=model_type,
                model_name=model_name,
                base_url=config_dict.get('base_url'),
                api_key=config_dict.get('api_key'),
                headers=config_dict.get('headers', {}),
                timeout=config_dict.get('timeout', 30),
                max_retries=config_dict.get('max_retries', 3),
                temperature=config_dict.get('temperature', 0.7),
                max_tokens=config_dict.get('max_tokens'),
                top_p=config_dict.get('top_p', 1.0),
                frequency_penalty=config_dict.get('frequency_penalty', 0.0),
                presence_penalty=config_dict.get('presence_penalty', 0.0),
                stream=config_dict.get('stream', False),
                functions=config_dict.get('functions'),
                function_call=config_dict.get('function_call'),
                fallback_enabled=config_dict.get('fallback_enabled', True),
                fallback_models=config_dict.get('fallback_models', []),
                max_fallback_attempts=config_dict.get('max_fallback_attempts', 3),
                metadata=config_dict.get('metadata', {})
            )


@dataclass
class LLMModuleConfig:
    """LLM模块配置"""
    # 默认配置
    default_model: str = "openai-gpt4"
    default_timeout: int = 30
    default_max_retries: int = 3
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存生存时间（秒）
    cache_max_size: int = 100
    
    # 钩子配置
    hooks_enabled: bool = True
    log_requests: bool = True
    log_responses: bool = True
    log_errors: bool = True
    
    # 降级配置
    fallback_enabled: bool = True
    global_fallback_models: List[str] = field(default_factory=list)
    
    # 性能配置
    max_concurrent_requests: int = 10
    request_queue_size: int = 100
    
    # 监控配置
    metrics_enabled: bool = True
    performance_tracking: bool = True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LLMModuleConfig':
        """从字典创建配置"""
        return cls(
            default_model=config_dict.get('default_model', 'openai-gpt4'),
            default_timeout=config_dict.get('default_timeout', 30),
            default_max_retries=config_dict.get('default_max_retries', 3),
            cache_enabled=config_dict.get('cache_enabled', True),
            cache_ttl=config_dict.get('cache_ttl', 3600),
            cache_max_size=config_dict.get('cache_max_size', 100),
            hooks_enabled=config_dict.get('hooks_enabled', True),
            log_requests=config_dict.get('log_requests', True),
            log_responses=config_dict.get('log_responses', True),
            log_errors=config_dict.get('log_errors', True),
            fallback_enabled=config_dict.get('fallback_enabled', True),
            global_fallback_models=config_dict.get('global_fallback_models', []),
            max_concurrent_requests=config_dict.get('max_concurrent_requests', 10),
            request_queue_size=config_dict.get('request_queue_size', 100),
            metrics_enabled=config_dict.get('metrics_enabled', True),
            performance_tracking=config_dict.get('performance_tracking', True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "default_model": self.default_model,
            "default_timeout": self.default_timeout,
            "default_max_retries": self.default_max_retries,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_max_size": self.cache_max_size,
            "hooks_enabled": self.hooks_enabled,
            "log_requests": self.log_requests,
            "log_responses": self.log_responses,
            "log_errors": self.log_errors,
            "fallback_enabled": self.fallback_enabled,
            "global_fallback_models": self.global_fallback_models,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_queue_size": self.request_queue_size,
            "metrics_enabled": self.metrics_enabled,
            "performance_tracking": self.performance_tracking
        }


@dataclass
class OpenAIConfig(LLMClientConfig):
    """OpenAI特定配置"""
    organization: Optional[str] = None
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.model_type != "openai":
            raise ValueError("OpenAIConfig的model_type必须为'openai'")


@dataclass
class GeminiConfig(LLMClientConfig):
    """Gemini特定配置"""
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.model_type != "gemini":
            raise ValueError("GeminiConfig的model_type必须为'gemini'")


@dataclass
class AnthropicConfig(LLMClientConfig):
    """Anthropic特定配置"""
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.model_type not in ["anthropic", "claude"]:
            raise ValueError("AnthropicConfig的model_type必须为'anthropic'或'claude'")


@dataclass
class MockConfig(LLMClientConfig):
    """Mock客户端配置"""
    response_delay: float = 0.1  # 响应延迟（秒）
    error_rate: float = 0.0  # 错误率（0-1）
    error_types: List[str] = field(default_factory=lambda: ["timeout", "rate_limit"])
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if self.model_type != "mock":
            raise ValueError("MockConfig的model_type必须为'mock'")