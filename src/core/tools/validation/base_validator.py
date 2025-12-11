"""
基础验证器
"""

from typing import Dict, Any, List, Optional
from src.interfaces.tool.validator import IToolValidator, ValidationType
from src.interfaces.logger import ILogger
from .models import ValidationResult, ValidationStatus


class BaseValidator(IToolValidator):
    """基础验证器"""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """初始化基础验证器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
    
    def get_supported_types(self) -> List[ValidationType]:
        """获取支持的验证类型"""
        return []
    
    def validate(self, target: Any, validation_type: ValidationType) -> ValidationResult:
        """通用验证方法"""
        if validation_type not in self.get_supported_types():
            tool_name = getattr(target, 'name', 'unknown')
            tool_type = getattr(target, 'tool_type', 'unknown')
            
            result = ValidationResult(tool_name, tool_type, ValidationStatus.WARNING)
            result.add_issue(
                ValidationStatus.WARNING,
                f"验证器不支持 {validation_type.value} 类型验证",
                validator=self.__class__.__name__,
                validation_type=validation_type.value,
                suggestion=f"使用支持 {validation_type.value} 的验证器"
            )
            
            if self.logger:
                self.logger.warning(f"验证器 {self.__class__.__name__} 不支持 {validation_type.value} 类型验证")
            
            return result
        
        return self._do_validate(target, validation_type)
    
    def _do_validate(self, target: Any, validation_type: ValidationType) -> ValidationResult:
        """执行具体验证逻辑，由子类实现"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _create_result(self, target: Any, status: ValidationStatus = ValidationStatus.SUCCESS) -> ValidationResult:
        """创建验证结果"""
        tool_name = getattr(target, 'name', 'unknown')
        tool_type = getattr(target, 'tool_type', 'unknown')
        return ValidationResult(tool_name, tool_type, status)
    
    def _log_validation_start(self, target: Any, validation_type: ValidationType) -> None:
        """记录验证开始"""
        if self.logger:
            tool_name = getattr(target, 'name', 'unknown')
            self.logger.debug(f"开始验证工具 {tool_name}，类型: {validation_type.value}")
    
    def _log_validation_end(self, target: Any, validation_type: ValidationType, result: ValidationResult) -> None:
        """记录验证结束"""
        if self.logger:
            tool_name = getattr(target, 'name', 'unknown')
            status_str = "通过" if result.is_successful() else "失败"
            self.logger.debug(f"工具 {tool_name} {validation_type.value} 验证{status_str}")


# 导出基础验证器
__all__ = [
    "BaseValidator",
]