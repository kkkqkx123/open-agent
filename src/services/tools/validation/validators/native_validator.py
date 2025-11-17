"""
Native工具验证器
验证Native工具的配置和实现
"""

import re
import importlib
from typing import Dict, Any, List
from src.infrastructure.logger.logger import ILogger
from ..interfaces import IToolValidator
from ..models import ValidationResult, ValidationStatus
from ..validators.base_validator import BaseValidator


class NativeToolValidator(BaseValidator):
    """Native工具验证器"""
    
    def __init__(self, logger: ILogger):
        """初始化Native工具验证器
        
        Args:
            logger: 日志记录器
        """
        super().__init__(logger)
    
    def validate_tool_type(self, tool_type: str, config: Dict[str, Any]) -> ValidationResult:
        """验证Native工具类型
        
        Args:
            tool_type: 工具类型
            config: 工具配置数据
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(config.get("name", "unknown"), tool_type, ValidationStatus.SUCCESS)
        
        # 验证函数路径
        function_path = config.get("function_path")
        if not function_path:
            result.add_issue(ValidationStatus.ERROR, "Native工具缺少function_path")
        elif not self._validate_function_path(function_path):
            result.add_issue(ValidationStatus.ERROR, f"无效的函数路径: {function_path}")
        else:
            # 验证函数是否可以加载
            try:
                self._load_function_from_path(function_path)
            except Exception as e:
                result.add_issue(ValidationStatus.ERROR, f"无法加载函数 {function_path}: {e}")
        
        return result
    
    def _validate_function_path(self, path: str) -> bool:
        """验证函数路径格式
        
        Args:
            path: 函数路径，格式为 "module.submodule:function_name"
            
        Returns:
            bool: 路径是否有效
        """
        # 验证路径格式：module.submodule:function_name
        pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$"
        return bool(re.match(pattern, path))
    
    def _load_function_from_path(self, function_path: str) -> Any:
        """从路径加载函数
        
        Args:
            function_path: 函数路径，格式为 "module.submodule:function_name"
            
        Returns:
            Any: 函数对象
            
        Raises:
            ValueError: 加载函数失败
        """
        try:
            module_path, function_name = function_path.split(":")
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)
            
            if not callable(func):
                raise ValueError(f"指定路径不是可调用对象: {function_path}")
            
            return func
            
        except Exception as e:
            raise ValueError(f"加载函数失败 {function_path}: {str(e)}")
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表"""
        return ["native"]