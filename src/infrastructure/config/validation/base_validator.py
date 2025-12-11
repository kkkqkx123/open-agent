"""基础验证器模块

提供配置验证的基础实现，只依赖接口层。
"""

import re
import logging
from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod

from src.interfaces.common_domain import IValidationResult
from src.interfaces.config import IConfigValidator
from src.infrastructure.validation.result import ValidationResult


class IValidationContext(Protocol):
    """验证上下文接口"""
    
    @property
    def config_type(self) -> str:
        """配置类型"""
        ...
    
    @property
    def strict_mode(self) -> bool:
        """严格模式"""
        ...
    
    @property
    def environment(self) -> str:
        """环境"""
        ...
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        ...


class BaseConfigValidator(IConfigValidator, ABC):
    """配置验证器基类
    
    提供基础验证逻辑和扩展点，不依赖核心层。
    """
    
    def __init__(self, name: str = "BaseValidator", logger: Optional[logging.Logger] = None):
        """初始化验证器
        
        Args:
            name: 验证器名称
            logger: 日志记录器
        """
        self.name = name
        self.logger = logger or logging.getLogger(f"{__name__}.{name}")
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        return True
    
    def validate(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # 基础验证
        self._validate_basic_structure(config, result)
        
        # 自定义验证
        self._validate_custom(config, result)
        
        # 记录验证结果
        self._log_validation_result(result)
        
        return result
    
    def validate_with_context(self, config: Dict[str, Any],
                            context: Optional[IValidationContext] = None) -> IValidationResult:
        """带上下文的验证
        
        Args:
            config: 配置字典
            context: 验证上下文
            
        Returns:
            ValidationResult: 验证结果
        """
        result = self.validate(config)
        
        # 根据上下文调整验证结果
        if context:
            self._apply_context_rules(config, context, result)
        
        return result
    
    def _validate_basic_structure(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """验证基础结构
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        if not isinstance(config, dict):
            result.add_error("配置必须是字典类型")
            return
        
        if not config:
            result.add_error("配置不能为空")
    
    @abstractmethod
    def _validate_custom(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """自定义验证逻辑，子类必须实现此方法
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        pass
    
    def _apply_context_rules(self, config: Dict[str, Any],
                           context: IValidationContext,
                           result: IValidationResult) -> None:
        """应用上下文规则
        
        Args:
            config: 配置字典
            context: 验证上下文
            result: 验证结果
        """
        # 根据环境调整验证严格性
        if context.environment == "production":
            # 生产环境更严格的验证
            self._apply_production_rules(config, result)
        elif context.environment == "development":
            # 开发环境更宽松的验证
            self._apply_development_rules(config, result)
    
    def _apply_production_rules(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """应用生产环境规则
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 子类可以重写此方法实现生产环境特定规则
        pass
    
    def _apply_development_rules(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """应用开发环境规则
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 子类可以重写此方法实现开发环境特定规则
        pass
    
    def _validate_required_fields(self, config: Dict[str, Any], required_fields: List[str], result: IValidationResult) -> None:
        """验证必需字段
        
        Args:
            config: 配置字典
            required_fields: 必需字段列表
            result: 验证结果
        """
        for field in required_fields:
            if field not in config:
                result.add_error(f"缺少必需字段: {field}")
            elif config[field] is None:
                result.add_error(f"必需字段不能为空: {field}")
    
    def _validate_field_types(self, config: Dict[str, Any], type_rules: Dict[str, type], result: IValidationResult) -> None:
        """验证字段类型
        
        Args:
            config: 配置字典
            type_rules: 类型规则字典 {字段名: 期望类型}
            result: 验证结果
        """
        for field, expected_type in type_rules.items():
            if field in config and config[field] is not None:
                if not isinstance(config[field], expected_type):
                    result.add_error(f"字段 '{field}' 类型错误，期望 {expected_type.__name__}，实际 {type(config[field]).__name__}")
    
    def _validate_field_values(self, config: Dict[str, Any], value_rules: Dict[str, Dict[str, Any]], result: IValidationResult) -> None:
        """验证字段值
        
        Args:
            config: 配置字典
            value_rules: 值规则字典 {字段名: 规则字典}
            result: 验证结果
        """
        for field, rules in value_rules.items():
            if field not in config or config[field] is None:
                continue
            
            value = config[field]
            
            # 验证枚举值
            if "enum" in rules and value not in rules["enum"]:
                result.add_error(f"字段 '{field}' 值无效，必须是 {rules['enum']} 中的一个")
            
            # 验证范围
            if "range" in rules:
                min_val, max_val = rules["range"]
                if not (min_val <= value <= max_val):
                    result.add_error(f"字段 '{field}' 值超出范围，必须在 {min_val} 到 {max_val} 之间")
            
            # 验证正则表达式
            if "pattern" in rules:
                pattern = rules["pattern"]
                if not re.match(pattern, str(value)):
                    result.add_error(f"字段 '{field}' 值格式不正确，必须匹配模式: {pattern}")
            
            # 验证最小长度
            if "min_length" in rules:
                min_len = rules["min_length"]
                if len(str(value)) < min_len:
                    result.add_error(f"字段 '{field}' 长度不足，最小长度为 {min_len}")
            
            # 验证最大长度
            if "max_length" in rules:
                max_len = rules["max_length"]
                if len(str(value)) > max_len:
                    result.add_error(f"字段 '{field}' 长度超限，最大长度为 {max_len}")
    
    def _validate_class_path(self, class_path: str, result: IValidationResult) -> None:
        """验证类路径格式
        
        Args:
            class_path: 类路径字符串
            result: 验证结果
        """
        if not isinstance(class_path, str):
            result.add_error("类路径必须是字符串类型")
            return
        
        if not class_path.strip():
            result.add_error("类路径不能为空")
            return
        
        # 检查格式：module.submodule:ClassName
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$'
        if not re.match(pattern, class_path):
            result.add_error(f"类路径格式不正确: {class_path}，应为 'module.submodule:ClassName'")
    
    def _validate_file_path(self, file_path: str, result: IValidationResult) -> None:
        """验证文件路径格式
        
        Args:
            file_path: 文件路径字符串
            result: 验证结果
        """
        if not isinstance(file_path, str):
            result.add_error("文件路径必须是字符串类型")
            return
        
        if not file_path.strip():
            result.add_error("文件路径不能为空")
            return
        
        # 检查是否包含非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in illegal_chars:
            if char in file_path:
                result.add_error(f"文件路径包含非法字符 '{char}': {file_path}")
    
    def _log_validation_result(self, result: IValidationResult) -> None:
        """记录验证结果
        
        Args:
            result: 验证结果
        """
        if result.is_valid:
            self.logger.debug(f"配置验证通过: {self.name}")
        else:
            self.logger.error(f"配置验证失败: {self.name}")
            for error in result.errors:
                self.logger.error(f"  错误: {error}")
        
        for warning in result.warnings:
            self.logger.warning(f"  警告: {warning}")
        
        for info in result.info:
            self.logger.info(f"  信息: {info}")


class GenericConfigValidator(BaseConfigValidator):
    """通用配置验证器
    
    提供基础的配置验证功能，适用于简单配置场景。
    """
    
    def __init__(self, supported_types: Optional[List[str]] = None, **kwargs):
        """初始化通用验证器
        
        Args:
            supported_types: 支持的配置类型列表
            **kwargs: 其他参数
        """
        super().__init__("GenericValidator", **kwargs)
        self.supported_types = supported_types or []
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        return not self.supported_types or module_type in self.supported_types
    
    def _validate_custom(self, config: Dict[str, Any], result: IValidationResult) -> None:
        """自定义验证逻辑
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        # 通用验证器不执行特定的自定义验证
        pass