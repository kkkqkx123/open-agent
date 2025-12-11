"""
Anthropic Token计算器

基于API响应进行token统计，以tiktoken作为回退方案。
"""

from typing import Dict, Any, Optional, Sequence, List
from src.interfaces.dependency_injection import get_logger
from .local_token_calculator import LocalTokenCalculator, TiktokenConfig
from ..models import TokenUsage
from src.interfaces.messages import IBaseMessage

logger = get_logger(__name__)


class AnthropicTokenCalculator(LocalTokenCalculator):
    """Anthropic Token计算器
    
    专门针对Anthropic API的token计算器，优先使用API响应统计。
    """
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229", enable_cache: bool = True):
        """
        初始化Anthropic Token计算器
        
        Args:
            model_name: 模型名称
            enable_cache: 是否启用缓存
        """
        # Anthropic使用cl100k_base作为tiktoken回退编码器
        tiktoken_config = TiktokenConfig(
            encoding_name="cl100k_base",
            enable_fallback=True,
            cache_enabled=enable_cache
        )
        
        super().__init__(
            provider_name="anthropic",
            model_name=model_name,
            tiktoken_config=tiktoken_config,
            enable_cache=enable_cache
        )
        
        logger.info(f"Anthropic Token计算器初始化完成: {model_name}")
    
    def parse_api_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析Anthropic API响应中的token使用信息
        
        Args:
            response: Anthropic API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            # 使用通用解析器，指定提供商为anthropic
            token_usage = self.response_parser.parse_response(response, provider="anthropic")
            
            if token_usage:
                # 添加Anthropic特定的元数据
                if not token_usage.metadata:
                    token_usage.metadata = {}
                
                token_usage.metadata.update({
                    "provider": "anthropic",
                    "model": response.get("model", self.model_name),
                    "id": response.get("id"),
                    "type": response.get("type"),
                    "role": response.get("role"),
                    "stop_reason": response.get("stop_reason"),
                    "stop_sequence": response.get("stop_sequence"),
                    "usage": response.get("usage", {})
                })
                
                # 保存最后一次的使用情况
                self._last_usage = token_usage
                logger.debug(f"成功解析Anthropic响应token信息: {token_usage.total_tokens} tokens")
            else:
                logger.warning("无法从Anthropic API响应中解析token信息")
            
            return token_usage
            
        except Exception as e:
            logger.error(f"解析Anthropic响应失败: {e}")
            return None
    
    def get_supported_models(self) -> List[str]:
        """获取支持的Anthropic模型列表"""
        # 移除硬编码模型列表，从配置文件获取
        logger.warning("模型列表已移除硬编码，请从配置文件获取支持的模型")
        return []
    
    def is_model_supported(self, model_name: str) -> bool:
        """检查是否支持指定的Anthropic模型"""
        supported_models = self.get_supported_models()
        return model_name in supported_models or model_name.startswith("claude-")
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该Anthropic响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        # 检查Anthropic特有的字段
        return (
            "usage" in response and
            isinstance(response.get("usage"), dict) and
            any(key in response.get("usage", {}) for key in ["input_tokens", "output_tokens"])
        ) or (
            # 检查是否有Anthropic特有的响应结构
            response.get("type") == "message"
        )
    
    def _count_messages_tokens_with_encoding(self, messages: Sequence[IBaseMessage]) -> int:
        """
        使用编码器计算Anthropic消息格式的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        if not self._encoding:
            return 0
        
        total_tokens = 0
        
        # Anthropic消息格式开销可能与OpenAI不同，但使用相同的估算方法
        tokens_per_message = 4  # Anthropic可能有不同的消息开销
        tokens_per_name = 2
        
        for message in messages:
            # 计算消息内容的token
            total_tokens += tokens_per_message
            content = self._extract_message_content(message)
            total_tokens += len(self._encoding.encode(content))
            
            # 如果有名称，添加名称的token
            if message.name:
                total_tokens += tokens_per_name + len(self._encoding.encode(message.name))
        
        # Anthropic可能不需要额外的回复token
        # total_tokens += 3
        
        return total_tokens