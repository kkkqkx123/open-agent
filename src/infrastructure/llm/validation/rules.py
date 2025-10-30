"""验证规则"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .validation_result import ValidationResult, ValidationIssue, ValidationSeverity


class ValidationRule(ABC):
    """验证规则接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """规则名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """规则描述"""
        pass
    
    @abstractmethod
    def validate(self, config: Any, field: str, value: Any, context: Optional[Dict[str, Any]]) -> Optional[ValidationIssue]:
        """
        验证配置
        
        Args:
            config: 配置对象
            field: 字段名
            value: 字段值
            context: 上下文信息
            
        Returns:
            ValidationIssue: 验证问题，None表示验证通过
        """
        pass
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return []


class ValidationRuleRegistry:
    """验证规则注册表"""
    
    def __init__(self) -> None:
        """初始化注册表"""
        self._rules: Dict[str, ValidationRule] = {}
        self._field_rules: Dict[str, List[ValidationRule]] = {}
    
    def register_rule(self, rule: ValidationRule) -> None:
        """
        注册验证规则
        
        Args:
            rule: 验证规则
        """
        self._rules[rule.name] = rule
        
        # 更新字段映射
        for field in rule.applicable_fields:
            if field not in self._field_rules:
                self._field_rules[field] = []
            self._field_rules[field].append(rule)
    
    def get_rules_for_field(self, field: str) -> List[ValidationRule]:
        """
        获取字段的验证规则
        
        Args:
            field: 字段名
            
        Returns:
            List[ValidationRule]: 验证规则列表
        """
        return self._field_rules.get(field, [])
    
    def get_rule(self, name: str) -> Optional[ValidationRule]:
        """
        获取验证规则
        
        Args:
            name: 规则名称
            
        Returns:
            ValidationRule: 验证规则，None表示不存在
        """
        return self._rules.get(name)
    
    def get_all_rules(self) -> Dict[str, ValidationRule]:
        """获取所有规则"""
        return self._rules.copy()
    
    def validate_field(self, config: Any, field: str, value: Any,
                    context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        验证单个字段
        
        Args:
            config: 配置对象
            field: 字段名
            value: 字段值
            context: 上下文信息
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        rules = self.get_rules_for_field(field)
        for rule in rules:
            issue = rule.validate(config, field, value, context)
            if issue:
                result.add_issue(
                    field=issue.field,  # 使用issue中的字段名，而不是传入的字段名
                    message=issue.message,
                    severity=issue.severity,
                    code=issue.code,
                    context=issue.context
                )
        
        return result
    
    def validate_config(self, config: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        验证整个配置
        
        Args:
            config: 配置对象
            context: 上下文信息
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True)
        
        # 获取配置的所有字段
        if hasattr(config, '__dataclass_fields__'):
            fields = config.__dataclass_fields__
            for field_name, field_info in fields.items():
                value = getattr(config, field_name)
                field_result = self.validate_field(config, field_name, value, context)
                result.merge(field_result)
        else:
            # 对于非dataclass对象，使用字典属性
            if hasattr(config, '__dict__'):
                for field_name, value in config.__dict__.items():
                    if not field_name.startswith('_'):
                        field_result = self.validate_field(config, field_name, value, context)
                        result.merge(field_result)
        
        return result


# 内置验证规则

class RequiredFieldRule(ValidationRule):
    """必填字段验证规则"""
    
    def __init__(self, field_name: str, message: Optional[str] = None):
        """
        初始化必填字段验证规则
        
        Args:
            field_name: 字段名
            message: 自定义错误消息
        """
        self._field_name = field_name
        self._message = message or f"{field_name}是必填字段"
    
    @property
    def name(self) -> str:
        """规则名称"""
        return f"required_field_{self._field_name}"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return self._message
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return [self._field_name]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证必填字段"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return ValidationIssue(
                field=field,
                message=self._message,
                severity=ValidationSeverity.ERROR,
                code="REQUIRED_FIELD"
            )
        return None


class TypeValidationRule(ValidationRule):
    """类型验证规则"""
    
    def __init__(self, field_name: str, expected_type: type, message: Optional[str] = None):
        """
        初始化类型验证规则
        
        Args:
            field_name: 字段名
            expected_type: 期望的类型
            message: 自定义错误消息
        """
        self._field_name = field_name
        self._expected_type = expected_type
        self._message = message or f"{field_name}必须是{expected_type.__name__}类型"
    
    @property
    def name(self) -> str:
        """规则名称"""
        return f"type_validation_{self._field_name}"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return self._message
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return [self._field_name]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证类型"""
        if not isinstance(value, self._expected_type):
            return ValidationIssue(
                field=field,
                message=self._message,
                severity=ValidationSeverity.WARNING,
                code="TYPE_MISMATCH",
                context={
                    "expected_type": self._expected_type.__name__,
                    "actual_type": type(value).__name__
                }
            )
        return None


class RangeValidationRule(ValidationRule):
    """范围验证规则"""
    
    def __init__(self, field_name: str, min_value: Any = None, max_value: Any = None, 
                 message: Optional[str] = None):
        """
        初始化范围验证规则
        
        Args:
            field_name: 字段名
            min_value: 最小值
            max_value: 最大值
            message: 自定义错误消息
        """
        self._field_name = field_name
        self._min_value = min_value
        self._max_value = max_value
        self._message = message or f"{field_name}必须在{min_value}到{max_value}之间"
    
    @property
    def name(self) -> str:
        """规则名称"""
        return f"range_validation_{self._field_name}"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return self._message
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return [self._field_name]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证范围"""
        if self._min_value is not None and value < self._min_value:
            return ValidationIssue(
                field=field,
                message=f"{field}不能小于{self._min_value}",
                severity=ValidationSeverity.ERROR,
                code="VALUE_TOO_SMALL",
                context={"min_value": self._min_value, "actual_value": value}
            )
        
        if self._max_value is not None and value > self._max_value:
            return ValidationIssue(
                field=field,
                message=f"{field}不能大于{self._max_value}",
                severity=ValidationSeverity.WARNING,
                code="VALUE_TOO_LARGE",
                context={"max_value": self._max_value, "actual_value": value}
            )
        
        return None


class PatternValidationRule(ValidationRule):
    """模式匹配验证规则"""
    
    def __init__(self, field_name: str, pattern: str, message: Optional[str] = None):
        """
        初始化模式匹配验证规则
        
        Args:
            field_name: 字段名
            pattern: 正则表达式模式
            message: 自定义错误消息
        """
        import re
        self._field_name = field_name
        self._pattern = re.compile(pattern)
        self._message = message or f"{field_name}格式不正确"
    
    @property
    def name(self) -> str:
        """规则名称"""
        return f"pattern_validation_{self._field_name}"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return self._message
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return [self._field_name]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证模式匹配"""
        if isinstance(value, str) and not self._pattern.match(value):
            return ValidationIssue(
                field=field,
                message=self._message,
                severity=ValidationSeverity.WARNING,
                code="PATTERN_MISMATCH",
                context={"pattern": self._pattern.pattern}
            )
        return None


class EnumValidationRule(ValidationRule):
    """枚举值验证规则"""
    
    def __init__(self, field_name: str, valid_values: List[Any], message: Optional[str] = None):
        """
        初始化枚举值验证规则
        
        Args:
            field_name: 字段名
            valid_values: 有效值列表
            message: 自定义错误消息
        """
        self._field_name = field_name
        self._valid_values = valid_values
        self._message = message or f"{field_name}必须是以下值之一: {valid_values}"
    
    @property
    def name(self) -> str:
        """规则名称"""
        return f"enum_validation_{self._field_name}"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return self._message
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return [self._field_name]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证枚举值"""
        if value not in self._valid_values:
            return ValidationIssue(
                field=field,
                message=self._message,
                severity=ValidationSeverity.ERROR,
                code="INVALID_ENUM_VALUE",
                context={
                    "valid_values": self._valid_values,
                    "actual_value": value
                }
            )
        return None


# 预定义的验证规则

class ModelNameValidationRule(ValidationRule):
    """模型名称验证规则"""
    
    def __init__(self):
        """初始化模型名称验证规则"""
        self._valid_models = [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "gemini-pro",
            "human-relay-s",
            "human-relay-m",
            "mock"
        ]
    
    @property
    def name(self) -> str:
        """规则名称"""
        return "model_name_validation"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return "验证模型名称是否在支持列表中"
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return ["model_name"]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证模型名称"""
        if isinstance(value, str) and value not in self._valid_models:
            return ValidationIssue(
                field=field,
                message=f"不支持的模型名称: {value}",
                severity=ValidationSeverity.ERROR,
                code="UNSUPPORTED_MODEL",
                context={
                    "supported_models": self._valid_models,
                    "actual_model": value
                }
            )
        return None


class APITokenValidationRule(ValidationRule):
    """API密钥验证规则"""
    
    def __init__(self):
        """初始化API密钥验证规则"""
        pass
    
    @property
    def name(self) -> str:
        """规则名称"""
        return "api_key_validation"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return "验证API密钥格式和有效性"
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return ["api_key"]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证API密钥"""
        if value is None:
            return ValidationIssue(
                field=field,
                message="API密钥不能为空",
                severity=ValidationSeverity.ERROR,
                code="MISSING_API_KEY"
            )
        
        if isinstance(value, str):
            # 检查是否是环境变量引用
            if value.startswith("${") and value.endswith("}"):
                # 环境变量引用，暂时跳过验证
                return None
            
            # 检查基本格式
            if not value.startswith("sk-") and not value.startswith("x-"):
                return ValidationIssue(
                    field=field,
                    message="API密钥格式不正确",
                    severity=ValidationSeverity.WARNING,
                    code="INVALID_API_KEY_FORMAT"
                )
        
        return None


class URLValidationRule(ValidationRule):
    """URL验证规则"""
    
    def __init__(self):
        """初始化URL验证规则"""
        pass
    
    @property
    def name(self) -> str:
        """规则名称"""
        return "url_validation"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return "验证URL格式和可访问性"
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return ["base_url"]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证URL"""
        if value is None:
            return ValidationIssue(
                field=field,
                message="URL不能为空",
                severity=ValidationSeverity.WARNING,
                code="MISSING_URL"
            )
        
        if isinstance(value, str):
            # 基本URL格式检查
            if not (value.startswith("http://") or value.startswith("https://")):
                return ValidationIssue(
                    field=field,
                    message="URL必须以http://或https://开头",
                    severity=ValidationSeverity.WARNING,
                    code="INVALID_URL_FORMAT"
                )
            
            # 检查URL格式
            try:
                from urllib.parse import urlparse
                parsed = urlparse(value)
                if not parsed.scheme or not parsed.netloc:
                    return ValidationIssue(
                        field=field,
                        message="URL格式不正确",
                        severity=ValidationSeverity.WARNING,
                        code="INVALID_URL_FORMAT"
                    )
            except Exception:
                return ValidationIssue(
                    field=field,
                    message="URL格式解析失败",
                    severity=ValidationSeverity.WARNING,
                    code="URL_PARSE_ERROR"
                )
        
        return None


class TimeoutValidationRule(ValidationRule):
    """超时验证规则"""
    
    def __init__(self):
        """初始化超时验证规则"""
        self._min_timeout = 1
        self._max_timeout = 3600  # 1小时
    
    @property
    def name(self) -> str:
        """规则名称"""
        return "timeout_validation"
    
    @property
    def description(self) -> str:
        """规则描述"""
        return "验证超时设置是否合理"
    
    @property
    def applicable_fields(self) -> List[str]:
        """适用的字段列表"""
        return ["timeout", "max_retries"]
    
    def validate(self, config: Any, field: str, value: Any, 
                    context: Optional[Dict[str, Any]] = None) -> Optional[ValidationIssue]:
        """验证超时设置"""
        if value is not None and (value < self._min_timeout or value > self._max_timeout):
            return ValidationIssue(
                field=field,
                message=f"超时时间应在{self._min_timeout}到{self._max_timeout}秒之间",
                severity=ValidationSeverity.WARNING,
                code="INVALID_TIMEOUT",
                context={
                    "min_timeout": self._min_timeout,
                    "max_timeout": self._max_timeout,
                    "actual_timeout": value
                }
            )
        
        return None


# 创建默认规则注册表
def create_default_rule_registry() -> ValidationRuleRegistry:
    """创建默认验证规则注册表"""
    registry = ValidationRuleRegistry()
    
    # 注册基础规则
    registry.register_rule(RequiredFieldRule("model_name"))
    registry.register_rule(TypeValidationRule("model_type", str))
    registry.register_rule(RangeValidationRule("temperature", 0.0, 2.0))
    registry.register_rule(RangeValidationRule("top_p", 0.0, 1.0))
    registry.register_rule(RangeValidationRule("max_tokens", 1, 32000))
    registry.register_rule(RequiredFieldRule("api_key"))
    registry.register_rule(URLValidationRule())
    registry.register_rule(TimeoutValidationRule())
    
    # 注册特定规则
    registry.register_rule(ModelNameValidationRule())
    registry.register_rule(APITokenValidationRule())
    
    return registry