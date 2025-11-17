"""
工具检验模块接口定义
定义了工具检验器的核心接口
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from src.core.tools.interfaces import ITool
from .models import ValidationResult


class IToolValidator(ABC):
    """工具检验器接口"""

    @abstractmethod
    def validate_config(self, config_path: str) -> ValidationResult:
        """验证工具配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            ValidationResult: 验证结果
        """
        pass

    @abstractmethod
    def validate_loading(self, tool_name: str) -> ValidationResult:
        """验证工具加载过程
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ValidationResult: 验证结果
        """
        pass

    @abstractmethod
    def validate_tool_type(self, tool_type: str, config: Dict[str, Any]) -> ValidationResult:
        """验证特定工具类型
        
        Args:
            tool_type: 工具类型
            config: 工具配置数据
            
        Returns:
            ValidationResult: 验证结果
        """
        pass

    @abstractmethod
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表
        
        Returns:
            List[str]: 支持的工具类型列表
        """
        pass