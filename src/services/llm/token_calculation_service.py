"""统一的Token计算服务 - 重构版本

使用 infrastructure 层的 TokenCalculatorFactory 实现。
"""

from typing import Dict, Any, Optional, Sequence, TYPE_CHECKING
from dataclasses import asdict
from src.infrastructure.messages.base import BaseMessage

# 使用 infrastructure 层的实现
from src.infrastructure.llm.token_calculators import get_token_calculator_factory
from src.infrastructure.llm.models import TokenUsage

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage


class TokenCalculationService:
    """统一的Token计算服务 - 重构版本
    
    现在使用 infrastructure 层的 TokenCalculatorFactory 来提供统一的 Token 计算功能。
    """
    
    def __init__(self, default_provider: str = "openai"):
        """
        初始化Token计算服务
        
        Args:
            default_provider: 默认提供商名称
        """
        self._default_provider = default_provider
        # 使用 infrastructure 层的工厂
        self._factory = get_token_calculator_factory()
        
    def calculate_tokens(self, text: str, model_type: str, model_name: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            int: token数量
        """
        calculator = self._factory.get_calculator(model_type, model_name)
        result = calculator.count_tokens(text)
        return result if result is not None else 0
    
    def calculate_messages_tokens(self, messages: Sequence["IBaseMessage"], model_type: str, model_name: str) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            int: token数量
        """
        calculator = self._factory.get_calculator(model_type, model_name)
        result = calculator.count_messages_tokens(messages)
        return result if result is not None else 0
    
    def parse_token_usage_from_response(self, response: Dict[str, Any], model_type: str) -> Optional[TokenUsage]:
        """
        从API响应中解析token使用情况
        
        Args:
            response: API响应
            model_type: 模型类型
            
        Returns:
            Optional[TokenUsage]: token使用情况
        """
        calculator = self._factory.get_calculator(model_type, "default")
        if hasattr(calculator, 'parse_api_response'):
            return calculator.parse_api_response(response)
        return None
    
    def get_processor_stats(self, model_type: str, model_name: str) -> Dict[str, Any]:
        """
        获取处理器统计信息
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        calculator = self._factory.get_calculator(model_type, model_name)
        if hasattr(calculator, 'get_stats'):
            stats = calculator.get_stats()
            return asdict(stats)
        return {}