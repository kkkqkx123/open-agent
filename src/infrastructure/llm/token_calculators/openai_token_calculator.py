"""
OpenAI Token计算器

基于tiktoken库实现OpenAI模型的精确Token计算。
"""

import time
from typing import Dict, Any, Optional, Sequence, List, Tuple
from dataclasses import dataclass

from src.services.logger import get_logger
from .base_token_calculator import BaseTokenCalculator, TokenCalculationStats
from .token_cache import TokenCache
from ..models import TokenUsage
from src.interfaces.messages import IBaseMessage

logger = get_logger(__name__)


@dataclass
class OpenAIModelInfo:
    """OpenAI模型信息"""
    
    name: str
    encoding_name: str
    max_tokens: int
    input_cost: float  # 每1K tokens的成本
    output_cost: float  # 每1K tokens的成本
    supports_function_calling: bool = True
    supports_vision: bool = False


class OpenAITokenCalculator(BaseTokenCalculator):
    """OpenAI Token计算器
    
    使用tiktoken库提供精确的Token计算功能。
    """
    
    # OpenAI模型配置
    MODELS = {
        "gpt-3.5-turbo": OpenAIModelInfo(
            name="gpt-3.5-turbo",
            encoding_name="cl100k_base",
            max_tokens=4096,
            input_cost=0.0005,
            output_cost=0.0015
        ),
        "gpt-3.5-turbo-16k": OpenAIModelInfo(
            name="gpt-3.5-turbo-16k",
            encoding_name="cl100k_base",
            max_tokens=16384,
            input_cost=0.003,
            output_cost=0.004
        ),
        "gpt-4": OpenAIModelInfo(
            name="gpt-4",
            encoding_name="cl100k_base",
            max_tokens=8192,
            input_cost=0.03,
            output_cost=0.06
        ),
        "gpt-4-32k": OpenAIModelInfo(
            name="gpt-4-32k",
            encoding_name="cl100k_base",
            max_tokens=32768,
            input_cost=0.06,
            output_cost=0.12
        ),
        "gpt-4-turbo": OpenAIModelInfo(
            name="gpt-4-turbo",
            encoding_name="cl100k_base",
            max_tokens=128000,
            input_cost=0.01,
            output_cost=0.03
        ),
        "gpt-4-turbo-preview": OpenAIModelInfo(
            name="gpt-4-turbo-preview",
            encoding_name="cl100k_base",
            max_tokens=128000,
            input_cost=0.01,
            output_cost=0.03
        ),
        "gpt-4o": OpenAIModelInfo(
            name="gpt-4o",
            encoding_name="o200k_base",
            max_tokens=128000,
            input_cost=0.005,
            output_cost=0.015
        ),
        "gpt-4o-mini": OpenAIModelInfo(
            name="gpt-4o-mini",
            encoding_name="o200k_base",
            max_tokens=128000,
            input_cost=0.00015,
            output_cost=0.0006
        ),
        "text-davinci-003": OpenAIModelInfo(
            name="text-davinci-003",
            encoding_name="p50k_base",
            max_tokens=4097,
            input_cost=0.02,
            output_cost=0.02
        ),
        "text-curie-001": OpenAIModelInfo(
            name="text-curie-001",
            encoding_name="p50k_base",
            max_tokens=2049,
            input_cost=0.002,
            output_cost=0.002
        ),
    }
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", enable_cache: bool = True):
        """
        初始化OpenAI Token计算器
        
        Args:
            model_name: 模型名称
            enable_cache: 是否启用缓存
        """
        super().__init__("openai", model_name)
        
        self.enable_cache = enable_cache
        self.cache = TokenCache() if enable_cache else None
        
        # 验证模型支持
        if model_name not in self.MODELS:
            logger.warning(f"未知模型: {model_name}，使用默认配置")
            # 创建默认模型配置
            self.model_info = OpenAIModelInfo(
                name=model_name,
                encoding_name="cl100k_base",
                max_tokens=4096,
                input_cost=0.001,
                output_cost=0.002
            )
        else:
            self.model_info = self.MODELS[model_name]
        
        logger.info(f"OpenAI Token计算器初始化完成: {model_name}")
    
    def _load_encoding(self) -> None:
        """加载tiktoken编码器"""
        try:
            import tiktoken
            
            # 尝试获取模型特定的编码器
            try:
                self._encoding = tiktoken.encoding_for_model(self.model_name)
            except KeyError:
                # 如果模型没有特定编码器，使用配置中的编码器
                self._encoding = tiktoken.get_encoding(self.model_info.encoding_name)
                
            logger.debug(f"OpenAI计算器使用编码器: {self._encoding.name}")
                
        except ImportError:
            raise ImportError(
                "tiktoken is required for OpenAI token processing. "
                "Please install it with: pip install tiktoken"
            )
        except Exception as e:
            logger.error(f"加载tiktoken编码器失败: {e}")
            raise
    
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
        
        try:
            if not self._encoding:
                logger.error("编码器不可用")
                self._update_stats_on_failure()
                return None
            
            token_count = len(self._encoding.encode(text))
            
            # 存储到缓存
            if self.cache:
                self.cache.put(text, self.model_name, token_count)
            
            # 更新统计
            calculation_time = time.time() - start_time
            self._update_stats_on_success(token_count, calculation_time)
            
            return token_count
            
        except Exception as e:
            logger.error(f"计算OpenAI token失败: {e}")
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
            if not self._encoding:
                logger.error("编码器不可用")
                self._update_stats_on_failure()
                return None
            
            # 使用OpenAI的消息格式计算
            token_count = self._count_openai_messages_tokens(messages)
            
            # 更新统计
            calculation_time = time.time() - start_time
            self._update_stats_on_success(token_count, calculation_time)
            
            return token_count
            
        except Exception as e:
            logger.error(f"计算OpenAI消息token失败: {e}")
            self._update_stats_on_failure()
            return None
    
    def _count_openai_messages_tokens(self, messages: Sequence[IBaseMessage]) -> int:
        """
        使用OpenAI格式计算消息token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        total_tokens = 0
        
        # 每条消息的开销
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
        解析OpenAI API响应中的token使用信息
        
        Args:
            response: OpenAI API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            usage = response.get("usage", {})
            if not usage:
                logger.warning("OpenAI响应中未找到usage信息")
                return None
            
            # 解析缓存token信息
            prompt_details = usage.get("prompt_tokens_details", {})
            completion_details = usage.get("completion_tokens_details", {})
            
            cached_tokens = prompt_details.get("cached_tokens", 0)
            
            # 解析扩展token信息
            extended_tokens = {}
            
            # 音频token
            audio_tokens = prompt_details.get("audio_tokens", 0)
            if audio_tokens > 0:
                extended_tokens["prompt_audio_tokens"] = audio_tokens
            
            completion_audio_tokens = completion_details.get("audio_tokens", 0)
            if completion_audio_tokens > 0:
                extended_tokens["completion_audio_tokens"] = completion_audio_tokens
            
            # 推理token
            reasoning_tokens = completion_details.get("reasoning_tokens", 0)
            if reasoning_tokens > 0:
                extended_tokens["reasoning_tokens"] = reasoning_tokens
            
            # 预测token
            accepted_prediction_tokens = completion_details.get("accepted_prediction_tokens", 0)
            rejected_prediction_tokens = completion_details.get("rejected_prediction_tokens", 0)
            if accepted_prediction_tokens > 0:
                extended_tokens["accepted_prediction_tokens"] = accepted_prediction_tokens
            if rejected_prediction_tokens > 0:
                extended_tokens["rejected_prediction_tokens"] = rejected_prediction_tokens
            
            # 思考token（Gemini风格，但OpenAI也可能有）
            thoughts_tokens = completion_details.get("thoughts_tokens", 0)
            if thoughts_tokens > 0:
                extended_tokens["thoughts_tokens"] = thoughts_tokens
            
            # 工具调用token
            tool_call_tokens = completion_details.get("tool_call_tokens", 0)
            if tool_call_tokens > 0:
                extended_tokens["tool_call_tokens"] = tool_call_tokens
            
            token_usage = TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                # 缓存token统计
                cached_tokens=cached_tokens,
                cached_prompt_tokens=cached_tokens,
                cached_completion_tokens=0,  # OpenAI通常不缓存completion_tokens
                # 音频token统计
                prompt_audio_tokens=audio_tokens,
                completion_audio_tokens=completion_audio_tokens,
                # 推理token统计
                reasoning_tokens=reasoning_tokens,
                # 预测token统计
                accepted_prediction_tokens=accepted_prediction_tokens,
                rejected_prediction_tokens=rejected_prediction_tokens,
                # 思考token统计
                thoughts_tokens=thoughts_tokens,
                # 工具调用token统计
                tool_call_tokens=tool_call_tokens,
                # 元数据
                metadata={
                    "model": response.get("model"),
                    "response_id": response.get("id"),
                    "object": response.get("object"),
                    "created": response.get("created"),
                    "system_fingerprint": response.get("system_fingerprint"),
                    "provider": "openai"
                }
            )
            
            # 保存最后一次的使用情况
            self._last_usage = token_usage
            
            return token_usage
            
        except Exception as e:
            logger.error(f"解析OpenAI响应失败: {e}")
            return None
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        return list(self.MODELS.keys())
    
    def get_model_pricing(self, model_name: str) -> Optional[Dict[str, float]]:
        """
        获取模型定价信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Dict[str, float]]: 定价信息
        """
        model_info = self.MODELS.get(model_name)
        if not model_info:
            return None
        
        return {
            "prompt": model_info.input_cost / 1000,  # 转换为每个token的成本
            "completion": model_info.output_cost / 1000
        }
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        return (
            "usage" in response and
            isinstance(response.get("usage"), dict) and
            any(key in response.get("usage", {}) for key in ["prompt_tokens", "completion_tokens", "total_tokens"])
        )
    
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
                logger.error(f"批量计算OpenAI token失败: {e}")
                # 设置失败的结果为None
                for original_index in uncached_indices:
                    results[original_index] = None
        
        return results
    
    def get_model_info(self, model_name: str) -> Optional[OpenAIModelInfo]:
        """
        获取模型详细信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[OpenAIModelInfo]: 模型信息
        """
        return self.MODELS.get(model_name)
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.cache:
            self.cache.clear()
    
    def _update_cache_stats(self, hit: bool) -> None:
        """更新缓存统计"""
        if hit:
            self._stats.cache_hits += 1
        else:
            self._stats.cache_misses += 1
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """获取缓存统计信息"""
        if not self.cache:
            return None
        return self.cache.get_cache_info()