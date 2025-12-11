"""
验证报告器接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class IValidationReporter(ABC):
    """验证报告器接口"""
    
    @abstractmethod
    def generate(self, results: Dict[str, Any]) -> str:
        """生成验证报告
        
        Args:
            results: 验证结果
            
        Returns:
            str: 生成的报告
        """
        pass
    
    @abstractmethod
    def get_format(self) -> str:
        """获取报告格式
        
        Returns:
            str: 报告格式名称
        """
        pass


class IReporterFactory(ABC):
    """报告器工厂接口"""
    
    @abstractmethod
    def create_reporter(self, format: str) -> IValidationReporter:
        """创建报告器
        
        Args:
            format: 报告格式
            
        Returns:
            IValidationReporter: 报告器实例
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的报告格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        pass


# 导出所有接口
__all__ = [
    "IValidationReporter",
    "IReporterFactory",
]