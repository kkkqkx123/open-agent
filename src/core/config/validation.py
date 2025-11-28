"""统一验证模块

提供完整的验证功能，整合之前分散在多个文件中的验证相关功能。
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Tuple, Callable, Type
from datetime import datetime
import logging
import re
import yaml
import json
from pathlib import Path


class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX = "syntax"           # 语法验证：YAML/JSON格式
    SCHEMA = "schema"           # 模式验证：数据结构
    SEMANTIC = "semantic"       # 语义验证：业务逻辑
    DEPENDENCY = "dependency"   # 依赖验证：外部依赖
    PERFORMANCE = "performance" # 性能验证：性能指标


class ValidationSeverity(Enum):
    """验证严重性级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """验证结果数据结构"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """添加错误信息"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """添加警告信息"""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.info.append(message)
    
    def merge(self, other: 'ValidationResult') -> None:
        """合并另一个验证结果"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        if not other.is_valid:
            self.is_valid = False
    
    def has_messages(self, severity: ValidationSeverity) -> bool:
        """检查是否有指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return len(self.errors) > 0
        elif severity == ValidationSeverity.WARNING:
            return len(self.warnings) > 0
        elif severity == ValidationSeverity.INFO:
            return len(self.info) > 0
        return False
    
    def get_messages(self, severity: ValidationSeverity) -> List[str]:
        """获取指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return self.errors
        elif severity == ValidationSeverity.WARNING:
            return self.warnings
        elif severity == ValidationSeverity.INFO:
            return self.info
        return []


class EnhancedValidationResult:
    """增强的验证结果"""
    
    def __init__(self, rule_id: str, level: ValidationLevel, passed: bool, message: str = ""):
        self.rule_id = rule_id
        self.level = level
        self.passed = passed
        self.message = message
        self.suggestions: List[str] = []
        self.fix_suggestions: List['FixSuggestion'] = []
        self.timestamp = datetime.now()
        self.severity: ValidationSeverity = ValidationSeverity.WARNING
    
    def add_warning(self, warning: str) -> None:
        """添加警告信息"""
        self.message = warning
        self.severity = ValidationSeverity.WARNING


class ValidationReport:
    """验证报告"""
    
    def __init__(self, config_type: str):
        self.config_type = config_type  # 修复：添加config_type属性
        self.config_path = config_type  # 保持向后兼容性，添加config_path属性
        self.timestamp = datetime.now()
        self.level_results: Dict[ValidationLevel, List[EnhancedValidationResult]] = {}
        self.summary: Dict[str, int] = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": 0
        }
    
    def get_results_by_level(self, level: str) -> List[EnhancedValidationResult]:
        """根据级别获取验证结果"""
        level_enum = ValidationLevel(level.lower())
        return self.level_results.get(level_enum, [])
    
    def add_level_results(self, level: ValidationLevel, results: List[EnhancedValidationResult]) -> None:
        """添加级别验证结果"""
        self.level_results[level] = results
        self._update_summary(level, results)
    
    def get_fix_suggestions(self) -> List['FixSuggestion']:
        """获取所有修复建议"""
        suggestions = []
        for results in self.level_results.values():
            for result in results:
                if not result.passed:
                    suggestions.extend(result.fix_suggestions)
        return suggestions
    
    def is_valid(self, min_severity: ValidationSeverity = ValidationSeverity.ERROR) -> bool:
        """检查配置是否有效"""
        # 定义严重性级别顺序
        severity_order = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.ERROR: 2,
            ValidationSeverity.CRITICAL: 3
        }
        
        for results in self.level_results.values():
            for result in results:
                if not result.passed:
                    # 比较严重性级别
                    if severity_order.get(result.severity, 0) >= severity_order.get(min_severity, 0):
                        return False
        return True
    
    @property
    def is_valid_property(self) -> bool:
        """配置是否有效的属性版本"""
        return self.is_valid()
    
    def _update_summary(self, level: ValidationLevel, results: List[EnhancedValidationResult]) -> None:
        """更新摘要统计"""
        self.summary["total_rules"] += len(results)
        
        for result in results:
            if result.passed:
                self.summary["passed"] += 1
            else:
                self.summary["failed"] += 1
                
                if result.severity == ValidationSeverity.WARNING:
                    self.summary["warnings"] += 1
                elif result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    self.summary["errors"] += 1


class FixSuggestion:
    """修复建议"""
    
    def __init__(self, description: str, fix_action: Callable, confidence: float = 0.8):
        self.description = description
        self.fix_action = fix_action
        self.confidence = confidence
    
    def apply(self) -> None:
        """应用修复建议"""
        if self.fix_action:
            self.fix_action()


class ConfigFixer:
    """配置修复器"""
    
    def __init__(self):
        self.fix_strategies = {}
        self._register_fix_strategies()
    
    def suggest_fixes(self, config: Dict[str, Any], field_issues: List[Dict[str, Any]]) -> List[FixSuggestion]:
        """提供修复建议
        
        Args:
            config: 配置数据
            field_issues: 字段问题列表，格式为[{'field': '字段名', 'type': '问题类型', 'value': '当前值'}]
            
        Returns:
            修复建议列表
        """
        suggestions = []
        
        for issue in field_issues:
            field = issue['field']
            issue_type = issue['type']
            
            if issue_type == 'missing_field':
                default_value = issue.get('default_value')
                description = f"添加缺失字段 '{field}'"
                fix_action = lambda f=field, v=default_value: self._fix_missing_field(config, f, v)
                suggestions.append(FixSuggestion(description, fix_action))
            
            elif issue_type == 'invalid_type':
                expected_type = issue.get('expected_type', str)
                description = f"修复字段 '{field}' 的类型错误"
                fix_action = lambda f=field, t=expected_type: self._fix_invalid_type(config, f, t)
                suggestions.append(FixSuggestion(description, fix_action))
            
            elif issue_type == 'invalid_value':
                valid_values = issue.get('valid_values', [])
                description = f"修复字段 '{field}' 的无效值"
                fix_action = lambda f=field, v=valid_values: self._fix_invalid_value(config, f, v)
                suggestions.append(FixSuggestion(description, fix_action))
        
        return suggestions
    
    def _register_fix_strategies(self) -> None:
        """注册修复策略"""
        self.fix_strategies = {
            "missing_field": self._fix_missing_field,
            "invalid_type": self._fix_invalid_type,
            "invalid_value": self._fix_invalid_value
        }
    
    def _fix_missing_field(self, config: Dict[str, Any], field: str, default_value: Any) -> None:
        """修复缺失字段"""
        if field not in config:
            config[field] = default_value
    
    def _fix_invalid_type(self, config: Dict[str, Any], field: str, expected_type: Type) -> None:
        """修复类型错误"""
        if field in config and not isinstance(config[field], expected_type):
            # 尝试类型转换或使用默认值
            try:
                config[field] = expected_type(config[field])
            except (ValueError, TypeError):
                config[field] = self._get_default_value(expected_type)
    
    def _fix_invalid_value(self, config: Dict[str, Any], field: str, valid_values: List[Any]) -> None:
        """修复无效值"""
        if field in config and config[field] not in valid_values:
            # 使用第一个有效值作为默认值
            config[field] = valid_values[0] if valid_values else None
    
    def _get_default_value(self, expected_type: Type) -> Any:
        """获取默认值"""
        if expected_type == str:
            return ""
        elif expected_type == int:
            return 0
        elif expected_type == float:
            return 0.0
        elif expected_type == bool:
            return False
        elif expected_type == list:
            return []
        elif expected_type == dict:
            return {}
        else:
            return None


class ValidationCache:
    """验证缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # 生存时间（秒）
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存结果"""
        if key in self._cache:
            result, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self.ttl:
                return result
            else:
                del self._cache[key]  # 过期清理
        return None
    
    def set(self, key: str, result: Any) -> None:
        """设置缓存结果"""
        if len(self._cache) >= self.max_size:
            # LRU淘汰策略
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[key] = (result, datetime.now())


def load_config_file(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix.lower() == '.json':
            return json.load(f)
        else:
            # 尝试作为YAML加载
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError:
                raise ValueError(f"不支持的配置文件格式: {config_path}")


def generate_cache_key(config_path: str, levels: List[ValidationLevel]) -> str:
    """生成缓存键"""
    level_names = "_".join(level.value for level in sorted(levels, key=lambda x: x.value))
    return f"{config_path}_{level_names}"


class BaseConfigValidator:
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
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()
        
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


logger = logging.getLogger(__name__)