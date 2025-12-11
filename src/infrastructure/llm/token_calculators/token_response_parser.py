"""
Token响应解析器

提供统一的API响应token解析功能，支持多个LLM提供商。
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from src.interfaces.dependency_injection import get_logger
from ..models import TokenUsage

logger = get_logger(__name__)


@dataclass
class ProviderTokenMapping:
    """提供商Token字段映射"""
    
    provider_name: str
    prompt_tokens_field: str
    completion_tokens_field: str
    total_tokens_field: Optional[str]
    usage_container: str  # usage字段的位置
    additional_mappings: Dict[str, str]  # 额外字段映射


class TokenResponseParser:
    """Token响应解析器
    
    提供统一的API响应token解析功能，支持多个LLM提供商。
    """
    
    # 提供商Token字段映射
    PROVIDER_MAPPINGS = {
        "openai": ProviderTokenMapping(
            provider_name="openai",
            prompt_tokens_field="prompt_tokens",
            completion_tokens_field="completion_tokens", 
            total_tokens_field="total_tokens",
            usage_container="usage",
            additional_mappings={
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "prompt_audio_tokens": "usage.prompt_tokens_details.audio_tokens",
                "completion_audio_tokens": "usage.completion_tokens_details.audio_tokens",
                "reasoning_tokens": "usage.completion_tokens_details.reasoning_tokens",
                "accepted_prediction_tokens": "usage.completion_tokens_details.accepted_prediction_tokens",
                "rejected_prediction_tokens": "usage.completion_tokens_details.rejected_prediction_tokens",
            }
        ),
        "gemini": ProviderTokenMapping(
            provider_name="gemini",
            prompt_tokens_field="promptTokenCount",
            completion_tokens_field="candidatesTokenCount",
            total_tokens_field="totalTokenCount", 
            usage_container="usageMetadata",
            additional_mappings={
                "cached_tokens": "cachedContentTokenCount",
                "thoughts_tokens": "thoughtsTokenCount",
                "tool_use_prompt_tokens": "toolUsePromptTokenCount",
            }
        ),
        "anthropic": ProviderTokenMapping(
            provider_name="anthropic",
            prompt_tokens_field="input_tokens",
            completion_tokens_field="output_tokens",
            total_tokens_field=None,  # Anthropic没有直接提供total_tokens
            usage_container="usage",
            additional_mappings={
                "cached_tokens": "cache_creation_input_tokens",  # 需要合并cache_read_input_tokens
                "cache_creation_input_tokens": "cache_creation_input_tokens",
                "cache_read_input_tokens": "cache_read_input_tokens",
            }
        ),
    }
    
    def __init__(self):
        """初始化Token响应解析器"""
        self.logger = get_logger(__name__)
    
    def parse_response(self, response: Dict[str, Any], provider: Optional[str] = None) -> Optional[TokenUsage]:
        """
        解析API响应中的token使用信息
        
        Args:
            response: API响应数据
            provider: 提供商名称，如果为None则自动检测
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            # 自动检测提供商
            if provider is None:
                provider = self._detect_provider(response)
                if not provider:
                    self.logger.warning("无法检测提供商，无法解析token信息")
                    return None
            
            # 获取提供商映射
            mapping = self.PROVIDER_MAPPINGS.get(provider.lower())
            if not mapping:
                self.logger.warning(f"不支持的提供商: {provider}")
                return None
            
            # 提取基础token信息
            usage_data = self._extract_usage_data(response, mapping)
            if not usage_data:
                self.logger.warning(f"无法从{provider}响应中提取usage数据")
                return None
            
            # 解析基础token数量
            prompt_tokens = self._get_nested_field(usage_data, mapping.prompt_tokens_field, 0)
            completion_tokens = self._get_nested_field(usage_data, mapping.completion_tokens_field, 0)
            
            # 计算total_tokens
            if mapping.total_tokens_field:
                total_tokens = self._get_nested_field(usage_data, mapping.total_tokens_field, 0)
            else:
                total_tokens = prompt_tokens + completion_tokens
            
            # 解析扩展token信息
            extended_tokens = self._parse_extended_tokens(response, mapping)
            
            # 解析缓存token信息
            cache_info = self._parse_cache_tokens(response, mapping)
            
            # 创建TokenUsage对象
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                # 缓存token统计
                cached_tokens=cache_info.get("cached_tokens", 0),
                cached_prompt_tokens=cache_info.get("cached_prompt_tokens", 0),
                cached_completion_tokens=cache_info.get("cached_completion_tokens", 0),
                # 音频token统计
                prompt_audio_tokens=extended_tokens.get("prompt_audio_tokens", 0),
                completion_audio_tokens=extended_tokens.get("completion_audio_tokens", 0),
                # 推理token统计
                reasoning_tokens=extended_tokens.get("reasoning_tokens", 0),
                # 预测token统计
                accepted_prediction_tokens=extended_tokens.get("accepted_prediction_tokens", 0),
                rejected_prediction_tokens=extended_tokens.get("rejected_prediction_tokens", 0),
                # 思考token统计
                thoughts_tokens=extended_tokens.get("thoughts_tokens", 0),
                # 工具调用token统计
                tool_call_tokens=extended_tokens.get("tool_use_prompt_tokens", 0),
                # 元数据
                metadata={
                    "provider": provider,
                    "model": response.get("model"),
                    "response_id": response.get("id"),
                    "object": response.get("object"),
                    "created": response.get("created"),
                    "system_fingerprint": response.get("system_fingerprint"),
                    "source": "api"
                }
            )
            
            self.logger.debug(f"成功解析{provider}响应token信息: {token_usage.total_tokens} tokens")
            return token_usage
            
        except Exception as e:
            self.logger.error(f"解析{provider or '未知'}响应失败: {e}")
            return None
    
    def _detect_provider(self, response: Dict[str, Any]) -> Optional[str]:
        """
        自动检测提供商类型
        
        Args:
            response: API响应数据
            
        Returns:
            Optional[str]: 提供商名称
        """
        # OpenAI特征检测
        if "usage" in response and isinstance(response.get("usage"), dict):
            usage = response["usage"]
            if any(key in usage for key in ["prompt_tokens", "completion_tokens", "total_tokens"]):
                return "openai"
        
        # Gemini特征检测
        if "usageMetadata" in response and isinstance(response.get("usageMetadata"), dict):
            metadata = response["usageMetadata"]
            if any(key in metadata for key in ["promptTokenCount", "candidatesTokenCount", "totalTokenCount"]):
                return "gemini"
        
        # Anthropic特征检测
        if "usage" in response and isinstance(response.get("usage"), dict):
            usage = response["usage"]
            if any(key in usage for key in ["input_tokens", "output_tokens"]):
                return "anthropic"
        
        # 检查响应结构特征
        if "choices" in response:  # OpenAI特征
            return "openai"
        elif "candidates" in response:  # Gemini特征
            return "gemini"
        elif response.get("type") == "message":  # Anthropic特征
            return "anthropic"
        
        return None
    
    def _extract_usage_data(self, response: Dict[str, Any], mapping: ProviderTokenMapping) -> Optional[Dict[str, Any]]:
        """
        提取usage数据
        
        Args:
            response: API响应数据
            mapping: 提供商映射
            
        Returns:
            Optional[Dict[str, Any]]: usage数据
        """
        if mapping.usage_container == "usage":
            return response.get("usage")
        elif mapping.usage_container == "usageMetadata":
            return response.get("usageMetadata")
        else:
            return response.get(mapping.usage_container)
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str, default: Any = None) -> Any:
        """
        获取嵌套字段值
        
        Args:
            data: 数据字典
            field_path: 字段路径，如 "usage.prompt_tokens"
            default: 默认值
            
        Returns:
            Any: 字段值
        """
        if not field_path:
            return default
        
        keys = field_path.split(".")
        current = data
        
        try:
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current
        except (KeyError, TypeError):
            return default
    
    def _parse_extended_tokens(self, response: Dict[str, Any], mapping: ProviderTokenMapping) -> Dict[str, int]:
        """
        解析扩展token信息
        
        Args:
            response: API响应数据
            mapping: 提供商映射
            
        Returns:
            Dict[str, int]: 扩展token信息
        """
        extended_tokens = {}
        
        for token_type, field_path in mapping.additional_mappings.items():
            if token_type.startswith("cached_"):
                continue  # 缓存token单独处理
            
            value = self._get_nested_field(response, field_path, 0)
            if isinstance(value, (int, float)) and value > 0:
                extended_tokens[token_type] = int(value)
        
        return extended_tokens
    
    def _parse_cache_tokens(self, response: Dict[str, Any], mapping: ProviderTokenMapping) -> Dict[str, int]:
        """
        解析缓存token信息
        
        Args:
            response: API响应数据
            mapping: 提供商映射
            
        Returns:
            Dict[str, int]: 缓存token信息
        """
        cache_info = {
            "cached_tokens": 0,
            "cached_prompt_tokens": 0,
            "cached_completion_tokens": 0
        }
        
        if mapping.provider_name == "openai":
            # OpenAI缓存token处理
            cached_tokens = self._get_nested_field(response, "usage.prompt_tokens_details.cached_tokens", 0)
            cache_info["cached_tokens"] = int(cached_tokens)
            cache_info["cached_prompt_tokens"] = int(cached_tokens)
            
        elif mapping.provider_name == "gemini":
            # Gemini缓存token处理
            cached_tokens = self._get_nested_field(response, "usageMetadata.cachedContentTokenCount", 0)
            cache_info["cached_tokens"] = int(cached_tokens)
            cache_info["cached_prompt_tokens"] = int(cached_tokens)
            
        elif mapping.provider_name == "anthropic":
            # Anthropic缓存token处理（需要合并创建和读取）
            cache_creation = self._get_nested_field(response, "usage.cache_creation_input_tokens", 0)
            cache_read = self._get_nested_field(response, "usage.cache_read_input_tokens", 0)
            total_cached = int(cache_creation) + int(cache_read)
            
            cache_info["cached_tokens"] = total_cached
            cache_info["cached_prompt_tokens"] = total_cached
        
        return cache_info
    
    def is_supported_response(self, response: Dict[str, Any], provider: Optional[str] = None) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            provider: 提供商名称
            
        Returns:
            bool: 是否支持解析
        """
        if provider:
            return provider.lower() in self.PROVIDER_MAPPINGS
        
        # 自动检测并验证
        detected_provider = self._detect_provider(response)
        return detected_provider is not None
    
    def get_supported_providers(self) -> List[str]:
        """
        获取支持的提供商列表
        
        Returns:
            List[str]: 支持的提供商名称列表
        """
        return list(self.PROVIDER_MAPPINGS.keys())
    
    def register_provider_mapping(self, mapping: ProviderTokenMapping) -> None:
        """
        注册新的提供商映射
        
        Args:
            mapping: 提供商映射
        """
        self.PROVIDER_MAPPINGS[mapping.provider_name.lower()] = mapping
        self.logger.info(f"注册提供商映射: {mapping.provider_name}")
    
    def unregister_provider(self, provider: str) -> bool:
        """
        注销提供商映射
        
        Args:
            provider: 提供商名称
            
        Returns:
            bool: 是否成功注销
        """
        provider_lower = provider.lower()
        if provider_lower in self.PROVIDER_MAPPINGS:
            del self.PROVIDER_MAPPINGS[provider_lower]
            self.logger.info(f"注销提供商映射: {provider}")
            return True
        return False


# 全局解析器实例
_global_parser: Optional[TokenResponseParser] = None


def get_token_response_parser() -> TokenResponseParser:
    """
    获取全局Token响应解析器实例
    
    Returns:
        TokenResponseParser: 解析器实例
    """
    global _global_parser
    if _global_parser is None:
        _global_parser = TokenResponseParser()
    return _global_parser