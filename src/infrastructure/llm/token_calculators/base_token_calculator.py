"""
基础Token计算器接口和抽象类

定义统一的Token计算接口，提供通用功能的默认实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Sequence, List, Union
from datetime import datetime
from dataclasses import dataclass, field

from src.interfaces.dependency_injection import get_logger
from ..models import TokenUsage
from src.interfaces.messages import IBaseMessage

logger = get_logger(__name__)


@dataclass
class TokenCalculationStats:
    """Token计算统计信息"""
    
    total_calculations: int = 0
    successful_calculations: int = 0
    failed_calculations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens_calculated: int = 0
    total_calculation_time: float = 0.0
    last_calculation_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_calculations == 0:
            return 0.0
        return (self.successful_calculations / self.total_calculations) * 100
    
    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100
    
    @property
    def average_calculation_time(self) -> float:
        """平均计算时间"""
        if self.successful_calculations == 0:
            return 0.0
        return self.total_calculation_time / self.successful_calculations


class ITokenCalculator(ABC):
    """统一的Token计算器接口"""
    
    @abstractmethod
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量，如果无法计算则返回None
        """
        pass
    
    @abstractmethod
    def count_messages_tokens(self, messages: Sequence[IBaseMessage]) -> Optional[int]:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            Optional[int]: token数量，如果无法计算则返回None
        """
        pass
    
    @abstractmethod
    def parse_api_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析API响应中的token使用信息
        
        Args:
            response: API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型列表
        """
        pass
    
    @abstractmethod
    def is_model_supported(self, model_name: str) -> bool:
        """
        检查是否支持指定模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 是否支持该模型
        """
        pass
    
    # 可选功能接口
    def supports_batch_calculation(self) -> bool:
        """
        检查是否支持批量计算
        
        Returns:
            bool: 是否支持批量计算
        """
        return False
    
    def count_tokens_batch(self, texts: List[str]) -> List[Optional[int]]:
        """
        批量计算token数量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[Optional[int]]: token数量列表
        """
        if not self.supports_batch_calculation():
            # 如果不支持批量计算，逐个计算
            return [self.count_tokens(text) for text in texts]
        
        # 子类实现具体的批量计算逻辑
        raise NotImplementedError("批量计算功能未实现")
    
    def get_model_pricing(self, model_name: str) -> Optional[Dict[str, float]]:
        """
        获取模型定价信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            Optional[Dict[str, float]]: 定价信息，格式为 {"prompt": 0.001, "completion": 0.002}
        """
        return None
    
    def calculate_cost(self, token_usage: TokenUsage, model_name: str) -> Optional[float]:
        """
        计算Token使用成本
        
        Args:
            token_usage: Token使用情况
            model_name: 模型名称
            
        Returns:
            Optional[float]: 成本，如果无法计算则返回None
        """
        pricing = self.get_model_pricing(model_name)
        if not pricing:
            return None
        
        try:
            prompt_cost = token_usage.prompt_tokens * pricing.get("prompt", 0)
            completion_cost = token_usage.completion_tokens * pricing.get("completion", 0)
            return prompt_cost + completion_cost
        except Exception as e:
            logger.error(f"计算成本失败: {e}")
            return None
    
    def get_stats(self) -> TokenCalculationStats:
        """
        获取计算统计信息
        
        Returns:
            TokenCalculationStats: 统计信息
        """
        return TokenCalculationStats()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        pass
    
    def clear_cache(self) -> None:
        """清空缓存"""
        pass


class BaseTokenCalculator(ITokenCalculator):
    """Token计算器基础实现类"""
    
    def __init__(self, provider_name: str, model_name: str):
        """
        初始化基础Token计算器
        
        Args:
            provider_name: 提供商名称
            model_name: 模型名称
        """
        self.provider_name = provider_name
        self.model_name = model_name
        self._stats = TokenCalculationStats()
        self._last_usage: Optional[TokenUsage] = None
        
        # 初始化编码器（子类实现）
        self._encoding = None
        self._load_encoding()
    
    def _load_encoding(self) -> None:
        """加载编码器（子类实现）"""
        pass
    
    def _update_stats_on_success(self, token_count: int, calculation_time: float) -> None:
        """更新成功统计"""
        self._stats.total_calculations += 1
        self._stats.successful_calculations += 1
        self._stats.total_tokens_calculated += token_count
        self._stats.total_calculation_time += calculation_time
        self._stats.last_calculation_time = datetime.now()
    
    def _update_stats_on_failure(self) -> None:
        """更新失败统计"""
        self._stats.total_calculations += 1
        self._stats.failed_calculations += 1
    
    def _update_cache_stats(self, hit: bool) -> None:
        """更新缓存统计"""
        if hit:
            self._stats.cache_hits += 1
        else:
            self._stats.cache_misses += 1
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return self.provider_name
    
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表（子类可重写）"""
        return [self.model_name]
    
    def is_model_supported(self, model_name: str) -> bool:
        """检查是否支持指定模型"""
        return model_name in self.get_supported_models()
    
    def get_stats(self) -> TokenCalculationStats:
        """获取计算统计信息"""
        return self._stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = TokenCalculationStats()
        self._last_usage = None
    
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """获取最近的API使用情况"""
        return self._last_usage
    
    def is_api_usage_available(self) -> bool:
        """检查是否有可用的API使用数据"""
        return self._last_usage is not None
    
    def format_usage_summary(self, usage: TokenUsage) -> str:
        """
        格式化Token使用情况摘要
        
        Args:
            usage: Token使用情况
            
        Returns:
            str: 格式化的摘要字符串
        """
        return (
            f"Token使用情况 - "
            f"提示: {usage.prompt_tokens}, "
            f"完成: {usage.completion_tokens}, "
            f"总计: {usage.total_tokens}"
        )
    
    def _extract_message_content(self, message: IBaseMessage) -> str:
        """
        提取消息内容
        
        Args:
            message: 基础消息
            
        Returns:
            str: 提取的文本内容
        """
        content = message.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # 处理内容列表，提取文本部分
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
            return " ".join(text_parts)
        else:
            return str(content)
    
    def _count_messages_tokens_with_format(self, messages: Sequence[IBaseMessage]) -> int:
        """
        使用编码器计算消息格式的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        if not self._encoding:
            return 0
        
        total_tokens = 0
        
        # 每条消息的开销（OpenAI格式）
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
    
    # 默认实现（子类可重写）
    def count_tokens(self, text: str) -> Optional[int]:
        """默认的token计算实现"""
        if not self._encoding:
            logger.warning("编码器不可用，无法计算token")
            return None
        
        try:
            return len(self._encoding.encode(text))
        except Exception as e:
            logger.error(f"计算token失败: {e}")
            self._update_stats_on_failure()
            return None
    
    def count_messages_tokens(self, messages: Sequence[IBaseMessage]) -> Optional[int]:
        """默认的消息token计算实现"""
        if not self._encoding:
            logger.warning("编码器不可用，无法计算消息token")
            return None
        
        try:
            return self._count_messages_tokens_with_format(messages)
        except Exception as e:
            logger.error(f"计算消息token失败: {e}")
            self._update_stats_on_failure()
            return None
    
    def parse_api_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """默认的API响应解析实现"""
        logger.warning("当前计算器不支持API响应解析")
        return None
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """检查是否支持解析该响应"""
        return False