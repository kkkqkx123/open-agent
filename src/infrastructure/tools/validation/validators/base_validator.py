"""
基础验证器
提供通用的验证功能
"""

from typing import Dict, Any, List
from src.infrastructure.logger.logger import ILogger
from ..interfaces import IToolValidator
from ..models import ValidationResult, ValidationStatus


class BaseValidator(IToolValidator):
    """基础验证器"""
    
    def __init__(self, logger: ILogger):
        """初始化基础验证器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
    
    def validate_config(self, config_path: str) -> ValidationResult:
        """验证工具配置文件 - 基础验证器不实现此方法"""
        result = ValidationResult("unknown", "unknown", ValidationStatus.WARNING)
        result.add_issue(
            ValidationStatus.WARNING,
            "基础验证器不支持配置验证",
            suggestion="使用配置验证器进行配置验证"
        )
        return result
    
    def validate_loading(self, tool_name: str) -> ValidationResult:
        """验证工具加载过程 - 基础验证器不实现此方法"""
        result = ValidationResult(tool_name, "unknown", ValidationStatus.WARNING)
        result.add_issue(
            ValidationStatus.WARNING,
            "基础验证器不支持加载验证",
            suggestion="使用加载验证器进行加载验证"
        )
        return result
    
    def validate_tool_type(self, tool_type: str, config: Dict[str, Any]) -> ValidationResult:
        """验证特定工具类型 - 基础验证器不实现此方法"""
        result = ValidationResult(config.get("name", "unknown"), tool_type, ValidationStatus.WARNING)
        result.add_issue(
            ValidationStatus.WARNING,
            "基础验证器不支持类型特定验证",
            suggestion="使用类型特定验证器进行验证"
        )
        return result
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表"""
        return []