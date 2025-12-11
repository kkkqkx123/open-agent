"""
验证引擎实现
"""

from typing import Dict, List, Any, Optional
from src.interfaces.tool.validator import IToolValidator, IValidationEngine, ValidationType
from src.interfaces.tool.exceptions import ToolValidationError
from src.interfaces.logger import ILogger
from .models import ValidationResult, ValidationStatus


class ValidationEngine(IValidationEngine):
    """验证引擎实现"""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """初始化验证引擎
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self._validators: Dict[ValidationType, List[IToolValidator]] = {}
    
    def register_validator(self, validator: IToolValidator) -> None:
        """注册验证器
        
        Args:
            validator: 验证器实例
        """
        supported_types = validator.get_supported_types()
        
        if not supported_types:
            if self.logger:
                self.logger.warning(f"验证器 {validator.__class__.__name__} 没有支持任何验证类型")
            return
        
        for validation_type in supported_types:
            if validation_type not in self._validators:
                self._validators[validation_type] = []
            
            self._validators[validation_type].append(validator)
            
            if self.logger:
                self.logger.debug(f"注册验证器 {validator.__class__.__name__} 支持 {validation_type.value} 类型")
    
    def validate_tool(self, tool_config: Any) -> ValidationResult:
        """验证工具配置
        
        Args:
            tool_config: 工具配置
            
        Returns:
            ValidationResult: 验证结果
        """
        # 创建基础结果
        tool_name = getattr(tool_config, 'name', 'unknown')
        tool_type = getattr(tool_config, 'tool_type', 'unknown')
        result = ValidationResult(tool_name, tool_type, ValidationStatus.SUCCESS)
        
        if self.logger:
            self.logger.info(f"开始验证工具: {tool_name} (类型: {tool_type})")
        
        # 按顺序执行各种验证
        validation_performed = False
        for validation_type in ValidationType:
            validators = self._validators.get(validation_type, [])
            
            if validators:
                validation_performed = True
                for validator in validators:
                    try:
                        if self.logger:
                            self.logger.debug(f"使用验证器 {validator.__class__.__name__} 执行 {validation_type.value} 验证")
                        
                        partial_result = validator.validate(tool_config, validation_type)
                        result.merge(partial_result)
                        
                        if self.logger:
                            status_str = "通过" if partial_result.is_successful() else "失败"
                            self.logger.debug(f"验证器 {validator.__class__.__name__} {validation_type.value} 验证{status_str}")
                    
                    except Exception as e:
                        error_msg = f"验证器 {validator.__class__.__name__} 执行失败: {e}"
                        result.add_issue(
                            ValidationStatus.ERROR,
                            error_msg,
                            validator=validator.__class__.__name__,
                            validation_type=validation_type.value,
                            error=str(e)
                        )
                        
                        if self.logger:
                            self.logger.error(error_msg)
        
        if not validation_performed:
            result.add_issue(
                ValidationStatus.WARNING,
                "没有找到任何验证器",
                suggestion="请确保已注册相应的验证器"
            )
            
            if self.logger:
                self.logger.warning(f"工具 {tool_name} 没有找到任何验证器")
        
        if self.logger:
            status_str = "通过" if result.is_successful() else "失败"
            error_count = result.get_error_count()
            warning_count = result.get_warning_count()
            self.logger.info(f"工具 {tool_name} 验证{status_str}，错误: {error_count}，警告: {warning_count}")
        
        return result
    
    def validate_all_tools(self, config_dir: str) -> Dict[str, ValidationResult]:
        """验证所有工具
        
        Args:
            config_dir: 配置目录
            
        Returns:
            Dict[str, ValidationResult]: 所有工具的验证结果
            
        Raises:
            NotImplementedError: 此方法需要在服务层实现具体逻辑
        """
        # 这里需要依赖配置加载器，实际实现中会通过依赖注入获取
        raise NotImplementedError("需要在服务层实现具体逻辑")
    
    def get_validators_for_type(self, validation_type: ValidationType) -> List[IToolValidator]:
        """获取指定类型的验证器列表
        
        Args:
            validation_type: 验证类型
            
        Returns:
            List[IToolValidator]: 验证器列表
        """
        return self._validators.get(validation_type, []).copy()
    
    def get_supported_types(self) -> List[ValidationType]:
        """获取所有支持的验证类型
        
        Returns:
            List[ValidationType]: 支持的验证类型列表
        """
        return list(self._validators.keys())
    
    def clear_validators(self) -> None:
        """清除所有验证器"""
        self._validators.clear()
        
        if self.logger:
            self.logger.info("已清除所有验证器")
    
    def remove_validator(self, validator: IToolValidator) -> bool:
        """移除指定的验证器
        
        Args:
            validator: 要移除的验证器
            
        Returns:
            bool: 是否成功移除
        """
        removed = False
        
        for validation_type, validators in self._validators.items():
            if validator in validators:
                validators.remove(validator)
                removed = True
                
                if self.logger:
                    self.logger.debug(f"移除验证器 {validator.__class__.__name__} 对 {validation_type.value} 的支持")
        
        return removed


# 导出验证引擎
__all__ = [
    "ValidationEngine",
]