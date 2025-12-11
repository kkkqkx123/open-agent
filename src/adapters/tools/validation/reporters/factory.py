"""
报告器工厂
"""

from typing import List, Dict, Type
from src.interfaces.tool.reporter import IValidationReporter, IReporterFactory
from src.interfaces.tool.exceptions import ValidationReporterError
from .text_reporter import TextReporter
from .json_reporter import JsonReporter


class ReporterFactory(IReporterFactory):
    """报告器工厂实现"""
    
    def __init__(self):
        """初始化报告器工厂"""
        self._reporters: Dict[str, Type[IValidationReporter]] = {
            "text": TextReporter,
            "json": JsonReporter,
        }
        
        # 注册报告器配置
        self._reporter_configs: Dict[str, Dict] = {
            "json": {
                "indent": 2,
                "ensure_ascii": False
            }
        }
    
    def create_reporter(self, format: str, **kwargs) -> IValidationReporter:
        """创建报告器
        
        Args:
            format: 报告格式
            **kwargs: 报告器配置参数
            
        Returns:
            IValidationReporter: 报告器实例
            
        Raises:
            ValidationReporterError: 不支持的报告格式
        """
        format_lower = format.lower()
        
        if format_lower not in self._reporters:
            supported_formats = ", ".join(self.get_supported_formats())
            raise ValidationReporterError(
                f"不支持的报告格式: {format}",
                reporter_format=format,
                supported_formats=supported_formats
            )
        
        reporter_class = self._reporters[format_lower]
        
        # 获取默认配置
        default_config = self._reporter_configs.get(format_lower, {})
        
        # 合并配置
        config = {**default_config, **kwargs}
        
        try:
            return reporter_class(**config)
        except Exception as e:
            raise ValidationReporterError(
                f"创建报告器失败: {e}",
                reporter_format=format,
                reporter_type=reporter_class.__name__,
                error=str(e)
            )
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的报告格式
        
        Returns:
            List[str]: 支持的格式列表
        """
        return list(self._reporters.keys())
    
    def register_reporter(self, format: str, reporter_class: Type[IValidationReporter], 
                         default_config: Dict | None = None) -> None:
        """注册新的报告器类型
        
        Args:
            format: 报告格式名称
            reporter_class: 报告器类
            default_config: 默认配置
        """
        if not issubclass(reporter_class, IValidationReporter):
            raise ValidationReporterError(
                f"报告器类必须实现 IValidationReporter 接口",
                reporter_type=reporter_class.__name__
            )
        
        format_lower = format.lower()
        self._reporters[format_lower] = reporter_class
        
        if default_config:
            self._reporter_configs[format_lower] = default_config
    
    def unregister_reporter(self, format: str) -> bool:
        """注销报告器类型
        
        Args:
            format: 报告格式名称
            
        Returns:
            bool: 是否成功注销
        """
        format_lower = format.lower()
        
        if format_lower in self._reporters:
            del self._reporters[format_lower]
            if format_lower in self._reporter_configs:
                del self._reporter_configs[format_lower]
            return True
        
        return False
    
    def get_reporter_info(self, format: str) -> Dict:
        """获取报告器信息
        
        Args:
            format: 报告格式名称
            
        Returns:
            Dict: 报告器信息
        """
        format_lower = format.lower()
        
        if format_lower not in self._reporters:
            raise ValidationReporterError(
                f"不支持的报告格式: {format}",
                reporter_format=format
            )
        
        reporter_class = self._reporters[format_lower]
        default_config = self._reporter_configs.get(format_lower, {})
        
        return {
            "format": format_lower,
            "class_name": reporter_class.__name__,
            "module": reporter_class.__module__,
            "default_config": default_config,
            "description": reporter_class.__doc__ or "无描述"
        }
    
    def get_all_reporters_info(self) -> Dict[str, Dict]:
        """获取所有报告器信息
        
        Returns:
            Dict[str, Dict]: 所有报告器信息
        """
        return {
            format: self.get_reporter_info(format)
            for format in self.get_supported_formats()
        }


# 导出报告器工厂
__all__ = [
    "ReporterFactory",
]