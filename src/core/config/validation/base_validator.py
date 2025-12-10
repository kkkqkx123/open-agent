"""基础验证器模块

提供配置验证的基础实现。
"""

import re
import logging
from typing import Dict, Any, List
from abc import ABC

from src.interfaces.common_domain import ValidationResult
from src.interfaces.config import IConfigValidator


class BaseConfigValidator(IConfigValidator, ABC):
    """配置验证器基类
    
    提供基础验证逻辑和扩展点。
    """
    
    def __init__(self, name: str = "BaseValidator"):
        """初始化验证器
        
        Args:
            name: 验证器名称
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        return True
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
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
    
    def _validate_basic_structure(self, config: Dict[str, Any], result: ValidationResult) -> None:
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
    
    def _validate_custom(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """自定义验证逻辑，子类应该重写此方法
        
        Args:
            config: 配置字典
            result: 验证结果
        """
        pass
    
    def _validate_required_fields(self, config: Dict[str, Any], required_fields: List[str], result: ValidationResult) -> None:
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
    
    def _validate_field_types(self, config: Dict[str, Any], type_rules: Dict[str, type], result: ValidationResult) -> None:
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
    
    def _validate_field_values(self, config: Dict[str, Any], value_rules: Dict[str, Dict[str, Any]], result: ValidationResult) -> None:
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
    
    def _validate_class_path(self, class_path: str, result: ValidationResult) -> None:
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
    
    def _validate_file_path(self, file_path: str, result: ValidationResult) -> None:
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
    
    def _log_validation_result(self, result: ValidationResult) -> None:
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