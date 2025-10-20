"""LLM配置模型"""

from typing import Dict, Any, Optional, List, Tuple
from pydantic import Field, field_validator, model_validator

from .base import BaseConfig


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

    # 参数配置
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模型参数")

    # 缓存配置
    supports_caching: bool = Field(False, description="是否支持缓存")
    cache_config: Dict[str, Any] = Field(default_factory=dict, description="缓存配置")

    # 继承配置
    group: Optional[str] = Field(None, description="所属组名称")
    
    # Token计数器配置
    token_counter: Optional[str] = Field(None, description="Token计数器配置名称")

    # 降级配置
    fallback_enabled: bool = Field(True, description="是否启用降级")
    fallback_models: List[str] = Field(default_factory=list, description="降级模型列表")
    max_fallback_attempts: int = Field(3, description="最大降级尝试次数")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

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

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """获取参数值"""
        return self.parameters.get(key, default)

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
        return self.get_cache_config("ttl_seconds", 3600)

    def get_cache_max_size(self) -> int:
        """获取缓存最大大小"""
        return self.get_cache_config("max_size", 1000)

    def is_fallback_enabled(self) -> bool:
        """检查是否启用降级"""
        return self.fallback_enabled

    def get_fallback_models(self) -> List[str]:
        """获取降级模型列表"""
        return self.fallback_models.copy()

    def get_max_fallback_attempts(self) -> int:
        """获取最大降级尝试次数"""
        return self.max_fallback_attempts

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值"""
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值"""
        self.metadata[key] = value