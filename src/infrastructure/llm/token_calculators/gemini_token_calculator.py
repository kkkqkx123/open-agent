"""
Gemini Token计算器

基于API响应进行token统计，以tiktoken作为回退方案。
"""

from typing import Dict, Any, Optional, Sequence, List
from src.interfaces.dependency_injection import get_logger
from .local_token_calculator import LocalTokenCalculator, TiktokenConfig
from ..models import TokenUsage
from src.interfaces.messages import IBaseMessage

logger = get_logger(__name__)


class GeminiTokenCalculator(LocalTokenCalculator):
    """Gemini Token计算器
    
    专门针对Gemini API的token计算器，优先使用API响应统计。
    """
    
    def __init__(self, model_name: str = "gemini-pro", enable_cache: bool = True):
        """
        初始化Gemini Token计算器
        
        Args:
            model_name: 模型名称
            enable_cache: 是否启用缓存
        """
        # Gemini使用cl100k_base作为tiktoken回退编码器
        tiktoken_config = TiktokenConfig(
            encoding_name="cl100k_base",
            enable_fallback=True,
            cache_enabled=enable_cache
        )
        
        super().__init__(
            provider_name="gemini",
            model_name=model_name,
            tiktoken_config=tiktoken_config,
            enable_cache=enable_cache
        )
        
        logger.info(f"Gemini Token计算器初始化完成: {model_name}")
    
    def parse_api_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析Gemini API响应中的token使用信息
        
        Args:
            response: Gemini API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            # 使用通用解析器，指定提供商为gemini
            token_usage = self.response_parser.parse_response(response, provider="gemini")
            
            if token_usage:
                # 添加Gemini特定的元数据
                if not token_usage.metadata:
                    token_usage.metadata = {}
                
                token_usage.metadata.update({
                    "provider": "gemini",
                    "model": response.get("model", self.model_name),
                    "candidates": response.get("candidates", []),
                    "prompt_feedback": response.get("promptFeedback"),
                    "usage_metadata": response.get("usageMetadata", {})
                })
                
                # 保存最后一次的使用情况
                self._last_usage = token_usage
                logger.debug(f"成功解析Gemini响应token信息: {token_usage.total_tokens} tokens")
            else:
                logger.warning("无法从Gemini API响应中解析token信息")
            
            return token_usage
            
        except Exception as e:
            logger.error(f"解析Gemini响应失败: {e}")
            return None
    
    def get_supported_models(self) -> List[str]:
        """获取支持的Gemini模型列表"""
        # 移除硬编码模型列表，从配置文件获取
        logger.warning("模型列表已移除硬编码，请从配置文件获取支持的模型")
        return []
    
    def is_model_supported(self, model_name: str) -> bool:
        """检查是否支持指定的Gemini模型"""
        supported_models = self.get_supported_models()
        return model_name in supported_models or model_name.startswith("gemini-")
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该Gemini响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        # 检查Gemini特有的字段
        return (
            "usageMetadata" in response and
            isinstance(response.get("usageMetadata"), dict) and
            any(key in response.get("usageMetadata", {}) for key in [
                "promptTokenCount", "candidatesTokenCount", "totalTokenCount"
            ])
        ) or (
            # 检查是否有Gemini特有的响应结构
            "candidates" in response
        )
    
    def _count_messages_tokens_with_encoding(self, messages: Sequence[IBaseMessage]) -> int:
        """
        使用编码器计算Gemini消息格式的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        if not self._encoding:
            return 0
        
        total_tokens = 0
        
        # Gemini消息格式开销可能与OpenAI不同，但使用相同的估算方法
        tokens_per_message = 4  # Gemini可能有不同的消息开销
        tokens_per_name = 2
        
        for message in messages:
            # 计算消息内容的token
            total_tokens += tokens_per_message
            content = self._extract_message_content(message)
            total_tokens += len(self._encoding.encode(content))
            
            # 如果有名称，添加名称的token
            if message.name:
                total_tokens += tokens_per_name + len(self._encoding.encode(message.name))
        
        # Gemini可能不需要额外的回复token
        # total_tokens += 3
        
        return total_tokens