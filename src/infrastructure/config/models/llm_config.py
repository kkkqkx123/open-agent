"""LLM配置模型"""

from typing import Dict, Any, Optional, List, Tuple
from pydantic import Field, field_validator, model_validator

from ..base import BaseConfig
from .retry_timeout_config import RetryTimeoutConfig, TimeoutConfig
from .connection_pool_config import ConnectionPoolConfig


class LLMConfig(BaseConfig):
    """LLM配置模型"""

    # 基础配置
    model_type: str = Field(..., description="模型类型：openai, gemini, anthropic等")
    model_name: str = Field(..., description="模型名称：gpt-4, gemini-pro等")
    provider: Optional[str] = Field(None, description="提供商名称")

    # API配置
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    api_format: Optional[str] = Field(None, description="API格式")

    # 参数配置
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模型参数")
    api_formats: Dict[str, Any] = Field(default_factory=dict, description="API格式配置")

    # 重试和超时配置
    retry_config: RetryTimeoutConfig = Field(
    default_factory=lambda: RetryTimeoutConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    jitter=True,
    exponential_base=2.0
    ), description="重试配置"
    )
    timeout_config: TimeoutConfig = Field(
        default_factory=lambda: TimeoutConfig(
            request_timeout=30,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30
        ), description="超时配置"
    )

    # 缓存配置
    supports_caching: bool = Field(False, description="是否支持缓存")
    cache_config: Dict[str, Any] = Field(default_factory=dict, description="缓存配置")

    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")
    
    # Token计数器配置
    # 任务组配置
    task_group: Optional[str] = Field(None, description="任务组引用，如 'fast_group.echelon1'")
    fallback_groups: List[str] = Field(default_factory=list, description="降级组引用列表")
    polling_pool: Optional[str] = Field(None, description="轮询池名称")
    
    # 并发和速率限制配置
    concurrency_limit: Optional[int] = Field(None, description="并发限制")
    rpm_limit: Optional[int] = Field(None, description="每分钟请求限制")
    
    token_counter: Optional[str] = Field(None, description="Token计数器配置名称")

    # 降级配置
    fallback_enabled: bool = Field(True, description="是否启用降级")
    fallback_models: List[str] = Field(default_factory=list, description="降级模型列表")
    max_fallback_attempts: int = Field(3, description="最大降级尝试次数")
    fallback_formats: List[str] = Field(default_factory=list, description="降级格式列表")

    # 工具调用配置
    function_calling_supported: bool = Field(True, description="是否支持函数调用")
    function_calling_mode: str = Field("auto", description="函数调用模式: auto, none, required")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    # 连接池配置
    connection_pool_config: ConnectionPoolConfig = Field(
        default_factory=lambda: ConnectionPoolConfig(
            max_connections=10,
            max_keepalive=10,
            timeout=30.0,
            keepalive_expiry=300.0,
            enabled=True
        ), description="连接池配置"
    )
    
    # 内部状态
    _resolved_headers: Optional[Dict[str, str]] = None
    _sanitized_headers: Optional[Dict[str, str]] = None

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """验证模型类型"""
        allowed_types = ["openai", "gemini", "anthropic", "claude", "local"]
        if v.lower() not in allowed_types:
            raise ValueError(f"模型类型必须是以下之一: {allowed_types}")
        return v.lower()

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """验证基础URL"""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("基础URL必须以http://或https://开头")
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """验证API密钥格式"""
        if v is None:
            return v

        # 检查是否为环境变量引用
        if v.startswith("${") and v.endswith("}"):
            return v

        # 根据不同的模型类型验证API密钥格式
        # 这里只做基本检查，具体验证在客户端中进行
        if len(v) < 6:
            raise ValueError("API密钥长度不能少于6个字符")

        return v

    @model_validator(mode="after")
    def validate_headers_and_resolve(self) -> "LLMConfig":
        """验证HTTP标头并解析环境变量"""
        # 延迟导入避免循环依赖
        from ...llm.header_validator import HeaderProcessor

        processor = HeaderProcessor()
        
        # 分离认证头和普通头，因为认证头可能包含直接的API密钥
        original_headers = self.headers.copy()
        auth_headers = {}
        
        if self.api_key:
            # 检查API密钥是否是环境变量引用格式
            from ...llm.header_validator import HeaderValidator
            validator = HeaderValidator()
            
            if validator._is_env_var_reference(self.api_key):
                # 如果是环境变量引用，解析后再使用
                resolved_key = validator._resolve_env_var(self.api_key)
                if resolved_key:
                    if self.model_type == "openai":
                        auth_headers["Authorization"] = f"Bearer {resolved_key}"
                    elif self.model_type == "gemini":
                        auth_headers["x-goog-api-key"] = resolved_key
                    elif self.model_type in ["anthropic", "claude"]:
                        auth_headers["x-api-key"] = resolved_key
            else:
                # 如果是直接的API密钥，直接使用
                if self.model_type == "openai":
                    auth_headers["Authorization"] = f"Bearer {self.api_key}"
                elif self.model_type == "gemini":
                    auth_headers["x-goog-api-key"] = self.api_key
                elif self.model_type in ["anthropic", "claude"]:
                    auth_headers["x-api-key"] = self.api_key

        # 只验证非认证头
        resolved_headers, sanitized_headers, is_valid, errors = (
            processor.process_headers(original_headers)
        )

        if not is_valid:
            raise ValueError(f"HTTP标头验证失败: {'; '.join(errors)}")

        # 将认证头添加到已验证的标头中
        resolved_headers.update(auth_headers)
        sanitized_headers.update({k: "***" for k in auth_headers.keys()})  # 对认证头进行脱敏

        # 缓存解析后的标头
        self._resolved_headers = resolved_headers
        self._sanitized_headers = sanitized_headers

        return self

    @model_validator(mode="after")
    def validate_legacy_timeout_retry_params(self) -> "LLMConfig":
        """验证并迁移旧的超时和重试参数"""
        # 检查是否存在旧的timeout和max_retries参数
        if self.parameters:
            # 迁移timeout参数
            if "timeout" in self.parameters:
                timeout_value = self.parameters["timeout"]
                if isinstance(timeout_value, (int, float)) and timeout_value > 0:
                    # 更新timeout_config
                    self.timeout_config.request_timeout = int(timeout_value)
                    # 从parameters中移除，避免重复
                    del self.parameters["timeout"]
            
            # 迁移max_retries参数
            if "max_retries" in self.parameters:
                max_retries_value = self.parameters["max_retries"]
                if isinstance(max_retries_value, int) and max_retries_value >= 0:
                    # 更新retry_config
                    self.retry_config.max_retries = max_retries_value
                    # 从parameters中移除，避免重复
                    del self.parameters["max_retries"]
        
        return self

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        # 首先从parameters中获取
        if key in self.parameters:
            return self.parameters[key]
        
        # 如果是timeout参数，从timeout_config中获取
        if key == "timeout" and hasattr(self.timeout_config, 'request_timeout'):
            return self.timeout_config.request_timeout
        
        # 如果是max_retries参数，从retry_config中获取
        if key == "max_retries" and hasattr(self.retry_config, 'max_retries'):
            return self.retry_config.max_retries
            
        return default

    def set_parameter(self, key: str, value: Any) -> None:
        """设置参数值"""
        self.parameters[key] = value

    def get_cache_config(self, key: str, default: Any = None) -> Any:
        """获取缓存配置值"""
        return self.cache_config.get(key, default)

    def set_cache_config(self, key: str, value: Any) -> None:
        """设置缓存配置值"""
        self.cache_config[key] = value

    def get_headers(self) -> Dict[str, str]:
        """获取请求头（已解析环境变量）"""
        # 如果已经解析过，直接返回
        if self._resolved_headers is not None:
            return self._resolved_headers.copy()

        # 否则解析并返回
        headers = self.headers.copy()

        # 处理API密钥
        if self.api_key:
            if self.model_type == "openai":
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.model_type == "gemini":
                headers["x-goog-api-key"] = self.api_key
            elif self.model_type in ["anthropic", "claude"]:
                headers["x-api-key"] = self.api_key

        # 解析其他标头中的环境变量
        from ...llm.header_validator import HeaderValidator

        validator = HeaderValidator()
        resolved_headers = validator.resolve_headers(headers)

        # 缓存结果
        self._resolved_headers = resolved_headers

        return resolved_headers

    def get_sanitized_headers(self) -> Dict[str, str]:
        """获取脱敏后的请求头（用于日志记录）"""
        if self._sanitized_headers is not None:
            return self._sanitized_headers.copy()

        # 获取原始标头
        headers = self.headers.copy()

        # 处理API密钥
        if self.api_key:
            # 根据模型类型设置不同的认证头
            if self.model_type == "openai":
                headers["Authorization"] = self.api_key
            elif self.model_type == "gemini":
                headers["x-goog-api-key"] = self.api_key
            elif self.model_type == "anthropic":
                headers["x-api-key"] = self.api_key

        # 脱敏处理
        from ...llm.header_validator import HeaderValidator

        validator = HeaderValidator()
        sanitized_headers = validator.sanitize_headers_for_logging(headers)

        # 缓存结果
        self._sanitized_headers = sanitized_headers

        return sanitized_headers

    def merge_parameters(self, other_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """合并参数"""
        result = self.parameters.copy()
        result.update(other_parameters)
        return result

    def is_openai_compatible(self) -> bool:
        """检查是否为OpenAI兼容模型"""
        return self.model_type in ["openai", "local"]

    def is_gemini(self) -> bool:
        """检查是否为Gemini模型"""
        return self.model_type == "gemini"

    def is_anthropic(self) -> bool:
        """检查是否为Anthropic模型"""
        return self.model_type in ["anthropic", "claude"]

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return self.provider or self.model_type

    def supports_api_caching(self) -> bool:
        """检查是否支持API级缓存"""
        return self.supports_caching

    def get_cache_ttl(self) -> int:
        """获取缓存TTL（秒）"""
        result = self.get_cache_config("ttl_seconds", 3600)
        return int(result) if result is not None else 3600

    def get_cache_max_size(self) -> int:
        """获取缓存最大大小"""
        result = self.get_cache_config("max_size", 1000)
        return int(result) if result is not None else 1000

    def is_fallback_enabled(self) -> bool:
        """检查是否启用降级"""
        return self.fallback_enabled

    def get_fallback_models(self) -> List[str]:
        """获取降级模型列表"""
        return self.fallback_models.copy()

    def get_max_fallback_attempts(self) -> int:
        """获取最大降级尝试次数"""
        return self.max_fallback_attempts

    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        return self.function_calling_supported

    def get_function_calling_mode(self) -> str:
        """获取函数调用模式"""
        return self.function_calling_mode

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值"""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值"""
        self.metadata[key] = value

    def get_max_retries(self) -> int:
        """获取最大重试次数（向后兼容）"""
        return self.retry_config.max_retries
    
    # 任务组相关方法
    def has_task_group(self) -> bool:
        """检查是否配置了任务组"""
        return self.task_group is not None
    
    def get_task_group(self) -> Optional[str]:
        """获取任务组引用"""
        return self.task_group
    
    def set_task_group(self, task_group: str) -> None:
        """设置任务组引用"""
        self.task_group = task_group
    
    def get_fallback_groups(self) -> List[str]:
        """获取降级组列表"""
        return self.fallback_groups.copy()
    
    def add_fallback_group(self, fallback_group: str) -> None:
        """添加降级组"""
        if fallback_group not in self.fallback_groups:
            self.fallback_groups.append(fallback_group)
    
    def get_polling_pool(self) -> Optional[str]:
        """获取轮询池名称"""
        return self.polling_pool
    
    def set_polling_pool(self, polling_pool: str) -> None:
        """设置轮询池名称"""
        self.polling_pool = polling_pool
    
    def get_concurrency_limit(self) -> Optional[int]:
        """获取并发限制"""
        return self.concurrency_limit
    
    def set_concurrency_limit(self, limit: int) -> None:
        """设置并发限制"""
        self.concurrency_limit = limit
    
    def get_rpm_limit(self) -> Optional[int]:
        """获取每分钟请求限制"""
        return self.rpm_limit
    
    def set_rpm_limit(self, rpm: int) -> None:
        """设置每分钟请求限制"""
        self.rpm_limit = rpm
    
    def is_task_group_config(self) -> bool:
        """检查是否为任务组配置"""
        return self.task_group is not None
    
    def get_effective_config(self, task_group_manager=None) -> "LLMConfig":
        """
        获取有效配置（合并任务组配置）
        
        Args:
            task_group_manager: 任务组管理器
            
        Returns:
            合并后的配置
        """
        if not self.has_task_group() or task_group_manager is None:
            return self
        
        # 解析任务组引用
        group_name, echelon_or_task = task_group_manager.parse_group_reference(self.task_group)
        
        if not group_name:
            return self
        
        # 获取任务组配置
        task_group = task_group_manager.get_task_group(group_name)
        if not task_group:
            return self
        
        # 获取层级配置
        echelon_config = None
        if echelon_or_task:
            echelon_config = task_group.echelons.get(echelon_or_task)
        
        if not echelon_config:
            return self
        
        # 创建新的配置副本
        effective_config = LLMConfig(**self.model_dump())
        
        # 合并层级配置
        effective_config.timeout_config.request_timeout = echelon_config.timeout
        effective_config.retry_config.max_retries = echelon_config.max_retries
        effective_config.concurrency_limit = echelon_config.concurrency_limit
        effective_config.rpm_limit = echelon_config.rpm_limit
        
        # 更新参数
        effective_config.parameters["temperature"] = echelon_config.temperature
        effective_config.parameters["max_tokens"] = echelon_config.max_tokens
        
        if echelon_config.function_calling:
            effective_config.function_calling_mode = echelon_config.function_calling
        
        if echelon_config.response_format:
            effective_config.parameters["response_format"] = echelon_config.response_format
        
        if echelon_config.thinking_config:
            effective_config.parameters["thinking_config"] = echelon_config.thinking_config.__dict__
        
        return effective_config
