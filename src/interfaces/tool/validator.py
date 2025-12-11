"""
工具验证器接口定义
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class ValidationType(Enum):
    """验证类型枚举"""
    CONFIG = "config"
    LOADING = "loading"
    TYPE_SPECIFIC = "type_specific"
    SCHEMA = "schema"


class IToolValidator(ABC):
    """工具验证器接口"""
    
    @abstractmethod
    def validate(self, target: Any, validation_type: ValidationType) -> 'ValidationResult':
        """通用验证方法
        
        Args:
            target: 验证目标
            validation_type: 验证类型
            
        Returns:
            ValidationResult: 验证结果
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[ValidationType]:
        """获取支持的验证类型
        
        Returns:
            List[ValidationType]: 支持的验证类型列表
        """
        pass


class IValidationEngine(ABC):
    """验证引擎接口"""
    
    @abstractmethod
    def register_validator(self, validator: IToolValidator) -> None:
        """注册验证器
        
        Args:
            validator: 验证器实例
        """
        pass
    
    @abstractmethod
    def validate_tool(self, tool_config: Any) -> 'ValidationResult':
        """验证工具配置
        
        Args:
            tool_config: 工具配置
            
        Returns:
            ValidationResult: 验证结果
        """
        pass
    
    @abstractmethod
    def validate_all_tools(self, config_dir: str) -> Dict[str, 'ValidationResult']:
        """验证所有工具
        
        Args:
            config_dir: 配置目录
            
        Returns:
            Dict[str, ValidationResult]: 所有工具的验证结果
        """
        pass


# 前向声明，避免循环导入
class ValidationResult:
    """验证结果前向声明"""
    pass


# 导出所有接口
__all__ = [
    "ValidationType",
    "IToolValidator",
    "IValidationEngine",
]