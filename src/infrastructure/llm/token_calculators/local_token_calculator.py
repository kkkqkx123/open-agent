"""
通用Token计算器

基于API响应进行token统计，以tiktoken作为回退方案。
"""

import time
from typing import Dict, Any, Optional, Sequence, List, Tuple
from dataclasses import dataclass

from src.interfaces.dependency_injection import get_logger
from .base_token_calculator import BaseTokenCalculator, TokenCalculationStats
from .token_cache import TokenCache
from .token_response_parser import TokenResponseParser, get_token_response_parser
from ..models import TokenUsage
from src.interfaces.messages import IBaseMessage

logger = get_logger(__name__)


@dataclass
class TiktokenConfig:
    """Tiktoken配置"""
    
    encoding_name: str = "cl100k_base"  # 默认使用cl100k_base编码器
    enable_fallback: bool = True
    cache_enabled: bool = True
    cache_max_size: int = 1000
    cache_ttl: Optional[float] = 3600  # 1小时


class LocalTokenCalculator(BaseTokenCalculator):
    """通用Token计算器
    
    基于API响应进行token统计，以tiktoken作为回退方案。
    """
    
    def __init__(
        self,
        provider_name: str = "universal",
        model_name: str = "default",
        tiktoken_config: Optional[TiktokenConfig] = None,
        enable_cache: bool = True
    ):
        """
        初始化通用Token计算器
        
        Args:
            provider_name: 提供商名称
            model_name: 模型名称
            tiktoken_config: Tiktoken配置
            enable_cache: 是否启用缓存
        """
        super().__init__(provider_name, model_name)
        
        self.tiktoken_config = tiktoken_config or TiktokenConfig()
        self.enable_cache = enable_cache
        self.cache = TokenCache() if enable_cache else None
        self.response_parser = get_token_response_parser()
        
        # 初始化tiktoken编码器
        self._encoding = None
        self._load_tiktoken_encoding()
        
        logger.info(f"通用Token计算器初始化完成: {provider_name}:{model_name}")
    
    def _load_tiktoken_encoding(self) -> None:
        """加载tiktoken编码器"""
        if not self.tiktoken_config.enable_fallback:
            logger.info("Tiktoken回退方案已禁用")
            return
        
        try:
            import tiktoken
            
            # 使用配置的编码器
            self._encoding = tiktoken.get_encoding(self.tiktoken_config.encoding_name)
            logger.info(f"加载tiktoken编码器成功: {self._encoding.name}")
                
        except ImportError:
            logger.warning("tiktoken未安装，本地token计算功能不可用")
        except Exception as e:
            logger.error(f"加载tiktoken编码器失败: {e}")
    
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量
        """
        if not text:
            return 0
        
        start_time = time.time()
        
        # 检查缓存
        if self.cache:
            cached_result = self.cache.get(text, self.model_name)
            if cached_result is not None:
                self._update_cache_stats(True)
                return cached_result
            self._update_cache_stats(False)
        
        # 使用tiktoken计算
        if self._encoding:
            try:
                token_count = len(self._encoding.encode(text))
                
                # 存储到缓存
                if self.cache:
                    self.cache.put(text, self.model_name, token_count)
                
                # 更新统计
                calculation_time = time.time() - start_time
                self._update_stats_on_success(token_count, calculation_time)
                
                return token_count
                
            except Exception as e:
                logger.error(f"tiktoken计算失败: {e}")
                self._update_stats_on_failure()
                return None
        else:
            logger.warning("tiktoken编码器不可用，无法计算token")
            self._update_stats_on_failure()
            return None
    
    def count_messages_tokens(self, messages: Sequence[IBaseMessage]) -> Optional[int]:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            Optional[int]: token数量
        """
        if not messages:
            return 0
        
        start_time = time.time()
        
        try:
            if self._encoding:
                # 使用tiktoken计算消息token
                token_count = self._count_messages_tokens_with_encoding(messages)
                
                # 更新统计
                calculation_time = time.time() - start_time
                self._update_stats_on_success(token_count, calculation_time)
                
                return token_count
            else:
                logger.warning("tiktoken编码器不可用，无法计算消息token")
                self._update_stats_on_failure()
                return None
                
        except Exception as e:
            logger.error(f"计算消息token失败: {e}")
            self._update_stats_on_failure()
            return None
    
    def _count_messages_tokens_with_encoding(self, messages: Sequence[IBaseMessage]) -> int:
        """
        使用编码器计算消息格式的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        total_tokens = 0
        
        # 检查编码器是否可用
        if not self._encoding:
            return 0
        
        # 每条消息的开销（OpenAI格式作为通用标准）
        tokens_per_message = 3
        tokens_per_name = 1
        
        for message in messages:
            # 计算消息内容的token
            total_tokens += tokens_per_message
            content = self._extract_message_content(message)
            total_tokens += len(self._encoding.encode(content))
            
            # 如果有名称，添加名称的token
            if message.name:
                total_tokens += tokens_per_name + len(self._encoding.encode(message.name))
        
        # 添加回复的token
        total_tokens += 3
        
        return total_tokens
    
    def parse_api_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析API响应中的token使用信息
        
        Args:
            response: API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            # 使用响应解析器解析token信息
            token_usage = self.response_parser.parse_response(response)
            
            if token_usage:
                # 保存最后一次的使用情况
                self._last_usage = token_usage
                logger.debug(f"成功解析API响应token信息: {token_usage.total_tokens} tokens")
            else:
                logger.warning("无法从API响应中解析token信息")
            
            return token_usage
            
        except Exception as e:
            logger.error(f"解析API响应失败: {e}")
            return None
    
    def count_messages_tokens_with_response(
        self,
        messages: Sequence[IBaseMessage],
        api_response: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        结合API响应计算消息token数量
        
        Args:
            messages: 消息列表
            api_response: API响应（可选）
            
        Returns:
            Optional[int]: token数量
        """
        # 如果有API响应，优先使用API响应中的token数量
        if api_response:
            token_usage = self.parse_api_response(api_response)
            if token_usage and token_usage.total_tokens > 0:
                return token_usage.total_tokens
        
        # 否则使用本地计算
        return self.count_messages_tokens(messages)
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        # 通用计算器支持所有模型
        return ["*"]
    
    def is_model_supported(self, model_name: str) -> bool:
        """检查是否支持指定模型"""
        # 通用计算器支持所有模型
        return True
    
    def supports_batch_calculation(self) -> bool:
        """检查是否支持批量计算"""
        return True
    
    def count_tokens_batch(self, texts: List[str]) -> List[Optional[int]]:
        """
        批量计算token数量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[Optional[int]]: token数量列表
        """
        if not self.cache:
            # 如果没有缓存，逐个计算
            return [self.count_tokens(text) for text in texts]
        
        # 批量检查缓存
        cache_items: List[Tuple[str, str, Optional[Dict[str, Any]]]] = [(text, self.model_name, None) for text in texts]
        cached_results = self.cache.get_batch(cache_items)
        
        # 计算未缓存的文本
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, (text, cached_result) in enumerate(zip(texts, cached_results)):
            if cached_result is not None:
                results.append(cached_result)
            else:
                results.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 批量计算未缓存的文本
        if uncached_texts and self._encoding:
            try:
                # 使用tiktoken的批量编码
                uncached_tokens = [len(self._encoding.encode(text)) for text in uncached_texts]
                
                # 更新结果和缓存
                cache_put_items = []
                for text, token_count, original_index in zip(uncached_texts, uncached_tokens, uncached_indices):
                    results[original_index] = token_count
                    cache_put_items.append((text, self.model_name, token_count, None, None))
                
                # 批量存储到缓存
                self.cache.put_batch(cache_put_items)
                
            except Exception as e:
                logger.error(f"批量计算token失败: {e}")
                # 设置失败的结果为None
                for original_index in uncached_indices:
                    results[original_index] = None
        
        return results
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        return self.response_parser.is_supported_response(response)
    
    def get_supported_providers(self) -> List[str]:
        """
        获取支持的提供商列表
        
        Returns:
            List[str]: 支持的提供商名称列表
        """
        return self.response_parser.get_supported_providers()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.cache:
            self.cache.clear()
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """获取缓存统计信息"""
        if not self.cache:
            return None
        return self.cache.get_cache_info()
    
    def _update_cache_stats(self, hit: bool) -> None:
        """更新缓存统计"""
        if hit:
            self._stats.cache_hits += 1
        else:
            self._stats.cache_misses += 1
    
    def get_calculator_info(self) -> Dict[str, Any]:
        """
        获取计算器信息
        
        Returns:
            Dict[str, Any]: 计算器信息
        """
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "calculator_type": "universal",
            "tiktoken_enabled": self._encoding is not None,
            "tiktoken_encoding": self._encoding.name if self._encoding else None,
            "cache_enabled": self.enable_cache,
            "supported_providers": self.get_supported_providers(),
            "stats": self.get_stats().__dict__,
            "cache_stats": self.get_cache_stats()
        }
    
    def update_tiktoken_config(self, config: TiktokenConfig) -> None:
        """
        更新tiktoken配置
        
        Args:
            config: 新的配置
        """
        self.tiktoken_config = config
        self._load_tiktoken_encoding()
        logger.info("tiktoken配置已更新")
    
    def enable_tiktoken_fallback(self, enabled: bool) -> None:
        """
        启用/禁用tiktoken回退方案
        
        Args:
            enabled: 是否启用
        """
        if enabled and not self._encoding:
            self._load_tiktoken_encoding()
        elif not enabled:
            self._encoding = None
        
        logger.info(f"tiktoken回退方案: {'启用' if enabled else '禁用'}")