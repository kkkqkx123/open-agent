"""
基础报告生成器
定义报告生成器的接口
"""

from abc import ABC, abstractmethod
from typing import Dict
from ..models import ValidationResult


class BaseReporter(ABC):
    """基础报告生成器"""
    
    @abstractmethod
    def generate(self, all_results: Dict[str, Dict[str, ValidationResult]]) -> str:
        """生成报告
        
        Args:
            all_results: 验证结果
            
        Returns:
            str: 生成的报告
        """
        pass