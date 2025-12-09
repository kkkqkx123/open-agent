"""存储验证混入类

提供数据验证功能。
"""

import re
from typing import Dict, Any, Optional, List, Callable
from src.services.logger.injection import get_logger

from ..exceptions import ValidationError


logger = get_logger(__name__)


class StorageValidationMixin:
    """存储验证混入类
    
    提供通用的数据验证功能。
    """
    
    def __init__(self):
        """初始化验证混入"""
        self._validators: Dict[str, Callable] = {}
        self._field_validators: Dict[str, List[Callable]] = {}
        
        # 注册默认验证器
        self._register_default_validators()
    
    def _register_default_validators(self) -> None:
        """注册默认验证器"""
        # ID验证器
        self.register_validator("id", self._validate_id)
        
        # 状态验证器
        self.register_validator("status", self._validate_status)
        
        # 时间戳验证器
        self.register_validator("timestamp", self._validate_timestamp)
        
        # JSON数据验证器
        self.register_validator("json", self._validate_json_data)
        
        # 标签验证器
        self.register_validator("tags", self._validate_tags)
        
        # 列表验证器
        self.register_validator("list", self._validate_list)
    
    def register_validator(self, name: str, validator: Callable) -> None:
        """注册验证器
        
        Args:
            name: 验证器名称
            validator: 验证函数
        """
        self._validators[name] = validator
    
    def register_field_validator(self, field_name: str, validator: Callable) -> None:
        """注册字段验证器
        
        Args:
            field_name: 字段名
            validator: 验证函数
        """
        if field_name not in self._field_validators:
            self._field_validators[field_name] = []
        self._field_validators[field_name].append(validator)
    
    def validate_data(self, data: Dict[str, Any], validation_rules: Dict[str, Any]) -> None:
        """验证数据
        
        Args:
            data: 要验证的数据
            validation_rules: 验证规则
            
        Raises:
            ValidationError: 验证失败时抛出
        """
        # 验证必需字段
        if "required_fields" in validation_rules:
            self._validate_required_fields(data, validation_rules["required_fields"])
        
        # 验证字段类型
        if "field_types" in validation_rules:
            self._validate_field_types(data, validation_rules["field_types"])
        
        # 验证字段值
        if "field_values" in validation_rules:
            self._validate_field_values(data, validation_rules["field_values"])
        
        # 使用自定义验证器
        if "validators" in validation_rules:
            self._apply_validators(data, validation_rules["validators"])
        
        # 应用字段验证器
        self._apply_field_validators(data)
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """验证必需字段
        
        Args:
            data: 数据字典
            required_fields: 必需字段列表
            
        Raises:
            ValidationError: 缺少必需字段时抛出
        """
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValidationError(f"Missing required field: {field}", field_name=field)
    
    def _validate_field_types(self, data: Dict[str, Any], field_types: Dict[str, type]) -> None:
        """验证字段类型
        
        Args:
            data: 数据字典
            field_types: 字段类型定义
            
        Raises:
            ValidationError: 字段类型不匹配时抛出
        """
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    raise ValidationError(
                        f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}",
                        field_name=field
                    )
    
    def _validate_field_values(self, data: Dict[str, Any], field_values: Dict[str, Any]) -> None:
        """验证字段值
        
        Args:
            data: 数据字典
            field_values: 字段值约束
            
        Raises:
            ValidationError: 字段值无效时抛出
        """
        for field, constraints in field_values.items():
            if field in data and data[field] is not None:
                value = data[field]
                
                # 验证枚举值
                if "enum" in constraints and value not in constraints["enum"]:
                    raise ValidationError(
                        f"Field '{field}' must be one of {constraints['enum']}, got {value}",
                        field_name=field
                    )
                
                # 验证最小值
                if "min" in constraints and value < constraints["min"]:
                    raise ValidationError(
                        f"Field '{field}' must be >= {constraints['min']}, got {value}",
                        field_name=field
                    )
                
                # 验证最大值
                if "max" in constraints and value > constraints["max"]:
                    raise ValidationError(
                        f"Field '{field}' must be <= {constraints['max']}, got {value}",
                        field_name=field
                    )
                
                # 验证正则表达式
                if "pattern" in constraints and not re.match(constraints["pattern"], str(value)):
                    raise ValidationError(
                        f"Field '{field}' does not match pattern {constraints['pattern']}",
                        field_name=field
                    )
                
                # 验证长度
                if "length" in constraints:
                    if len(value) != constraints["length"]:
                        raise ValidationError(
                            f"Field '{field}' must have length {constraints['length']}, got {len(value)}",
                            field_name=field
                        )
                
                # 验证最小长度
                if "min_length" in constraints and len(value) < constraints["min_length"]:
                    raise ValidationError(
                        f"Field '{field}' must have length >= {constraints['min_length']}, got {len(value)}",
                        field_name=field
                    )
                
                # 验证最大长度
                if "max_length" in constraints and len(value) > constraints["max_length"]:
                    raise ValidationError(
                        f"Field '{field}' must have length <= {constraints['max_length']}, got {len(value)}",
                        field_name=field
                    )
    
    def _apply_validators(self, data: Dict[str, Any], validators: Dict[str, List[str]]) -> None:
        """应用验证器
        
        Args:
            data: 数据字典
            validators: 验证器配置
        """
        for field, validator_names in validators.items():
            if field in data:
                for validator_name in validator_names:
                    if validator_name in self._validators:
                        validator = self._validators[validator_name]
                        validator(data[field], field)
    
    def _apply_field_validators(self, data: Dict[str, Any]) -> None:
        """应用字段验证器
        
        Args:
            data: 数据字典
        """
        for field_name, validators in self._field_validators.items():
            if field_name in data:
                for validator in validators:
                    validator(data[field_name], field_name)
    
    def _validate_id(self, value: Any, field_name: str) -> None:
        """验证ID
        
        Args:
            value: ID值
            field_name: 字段名
            
        Raises:
            ValidationError: ID无效时抛出
        """
        if not isinstance(value, str):
            raise ValidationError(f"Field '{field_name}' must be a string", field_name=field_name)
        
        if not value or not value.strip():
            raise ValidationError(f"Field '{field_name}' cannot be empty", field_name=field_name)
    
    def _validate_status(self, value: Any, field_name: str) -> None:
        """验证状态
        
        Args:
            value: 状态值
            field_name: 字段名
            
        Raises:
            ValidationError: 状态无效时抛出
        """
        valid_statuses = ["active", "inactive", "completed", "failed", "paused", "pending"]
        
        if value not in valid_statuses:
            raise ValidationError(
                f"Field '{field_name}' must be one of {valid_statuses}, got {value}",
                field_name=field_name
            )
    
    def _validate_timestamp(self, value: Any, field_name: str) -> None:
        """验证时间戳
        
        Args:
            value: 时间戳值
            field_name: 字段名
            
        Raises:
            ValidationError: 时间戳无效时抛出
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Field '{field_name}' must be a number", field_name=field_name)
        
        if value < 0:
            raise ValidationError(f"Field '{field_name}' must be positive", field_name=field_name)
        
        # 检查是否为合理的时间戳（在过去10年内）
        import time
        current_time = time.time()
        if value > current_time + 31536000:  # 超过当前时间1年
            raise ValidationError(f"Field '{field_name}' is too far in the future", field_name=field_name)
        
        if value < current_time - 315360000:  # 超过当前时间10年前
            raise ValidationError(f"Field '{field_name}' is too far in the past", field_name=field_name)
    
    def _validate_json_data(self, value: Any, field_name: str) -> None:
        """验证JSON数据
        
        Args:
            value: JSON数据
            field_name: 字段名
            
        Raises:
            ValidationError: JSON数据无效时抛出
        """
        if not isinstance(value, (dict, list)):
            raise ValidationError(f"Field '{field_name}' must be JSON data (dict or list)", field_name=field_name)
    
    def _validate_tags(self, value: Any, field_name: str) -> None:
        """验证标签
        
        Args:
            value: 标签列表
            field_name: 字段名
            
        Raises:
            ValidationError: 标签无效时抛出
        """
        if not isinstance(value, list):
            raise ValidationError(f"Field '{field_name}' must be a list", field_name=field_name)
        
        for tag in value:
            if not isinstance(tag, str):
                raise ValidationError(f"All tags in '{field_name}' must be strings", field_name=field_name)
            
            if not tag.strip():
                raise ValidationError(f"Tags in '{field_name}' cannot be empty", field_name=field_name)
    
    def _validate_list(self, value: Any, field_name: str) -> None:
        """验证列表
        
        Args:
            value: 列表值
            field_name: 字段名
            
        Raises:
            ValidationError: 列表无效时抛出
        """
        if not isinstance(value, list):
            raise ValidationError(f"Field '{field_name}' must be a list", field_name=field_name)