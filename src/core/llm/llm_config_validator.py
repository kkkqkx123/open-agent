"""LLM配置验证框架

提供全面的LLM配置验证功能，包括Provider配置验证。
"""

from typing import Dict, Any, List, Optional, Type, Callable, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from src.services.logger import get_logger
from src.core.common.exceptions.config import ConfigError

logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """验证严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """验证规则"""
    field_path: str  # 字段路径，如 "model_type", "timeout"
    required: bool = True
    field_type: Optional[Type] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None  # 最小字符串长度
    max_length: Optional[int] = None  # 最大字符串长度
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None  # 正则表达式模式
    custom_validator: Optional[Callable[[Any], bool]] = None
    severity: ValidationSeverity = ValidationSeverity.ERROR
    error_message: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        # 根据错误、警告和信息确定整体有效性
        self.is_valid = not any(
            msg for msg in self.errors 
            if "CRITICAL" in msg or "ERROR" in msg
        )
    
    def add_error(self, message: str) -> None:
        """添加错误"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """添加警告"""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.info.append(message)
    
    def has_issues(self) -> bool:
        """是否有问题（错误或警告）"""
        return bool(self.errors or self.warnings)
    
    def get_summary(self) -> str:
        """获取验证摘要"""
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} 个错误")
        if self.warnings:
            parts.append(f"{len(self.warnings)} 个警告")
        if self.info:
            parts.append(f"{len(self.info)} 个信息")
        
        status = "通过" if self.is_valid else "失败"
        return f"验证{status}：{', '.join(parts)}" if parts else f"验证{status}"


class LLMConfigValidator:
    """LLM配置验证器
    
    提供：
    1. 基础配置验证
    2. Provider配置验证
    3. 继承关系验证
    4. 配置完整性验证
    """
    
    def __init__(self) -> None:
        """初始化验证器"""
        self.rules: List[ValidationRule] = []
        self._setup_default_rules()
        logger.debug("LLM配置验证器初始化完成")
    
    def _setup_default_rules(self) -> None:
        """设置默认验证规则"""
        # 基础LLM配置验证规则
        self.rules.extend([
            ValidationRule(
                field_path="model_type",
                required=True,
                field_type=str,
                allowed_values=["openai", "gemini", "anthropic", "claude", "mock", "siliconflow"],
                severity=ValidationSeverity.ERROR,
                error_message="model_type必须是支持的类型",
                description="LLM模型提供商类型"
            ),
            ValidationRule(
                field_path="model_name",
                required=True,
                field_type=str,
                min_length=1,
                severity=ValidationSeverity.ERROR,
                error_message="model_name是必需的非空字符串",
                description="模型名称"
            ),
            ValidationRule(
                field_path="timeout",
                required=False,
                field_type=int,
                min_value=1,
                max_value=300,
                severity=ValidationSeverity.WARNING,
                error_message="timeout建议设置为1-300之间的整数",
                description="请求超时时间（秒）"
            ),
            ValidationRule(
                field_path="max_retries",
                required=False,
                field_type=int,
                min_value=0,
                max_value=10,
                severity=ValidationSeverity.WARNING,
                error_message="max_retries建议设置为0-10之间的整数",
                description="最大重试次数"
            ),
            ValidationRule(
                field_path="temperature",
                required=False,
                field_type=float,
                min_value=0.0,
                max_value=2.0,
                severity=ValidationSeverity.WARNING,
                error_message="temperature必须在0.0-2.0之间",
                description="生成温度参数"
            ),
            ValidationRule(
                field_path="max_tokens",
                required=False,
                field_type=int,
                min_value=1,
                max_value=100000,
                severity=ValidationSeverity.WARNING,
                error_message="max_tokens建议设置为1-100000之间的整数",
                description="最大生成令牌数"
            ),
            ValidationRule(
                field_path="api_key",
                required=False,
                field_type=str,
                custom_validator=lambda x: x and len(x.strip()) > 0,
                severity=ValidationSeverity.WARNING,
                error_message="api_key应该设置有效的值",
                description="API密钥"
            ),
            ValidationRule(
                field_path="base_url",
                required=False,
                field_type=str,
                pattern=r"^https?://.*",
                severity=ValidationSeverity.INFO,
                error_message="base_url应该是有效的HTTP/HTTPS URL",
                description="API基础URL"
            ),
        ])
        
        # Provider特定验证规则
        self._setup_provider_specific_rules()
    
    def _setup_provider_specific_rules(self) -> None:
        """设置Provider特定验证规则"""
        # OpenAI特定规则
        self.rules.extend([
            ValidationRule(
                field_path="model_type",
                field_type=str,
                allowed_values=["openai"],
                custom_validator=lambda config: self._validate_openai_config(config),
                severity=ValidationSeverity.WARNING,
                error_message="OpenAI配置验证失败",
                description="OpenAI特定配置验证"
            ),
        ])
        
        # Anthropic特定规则
        self.rules.extend([
            ValidationRule(
                field_path="model_type",
                field_type=str,
                allowed_values=["anthropic"],
                custom_validator=lambda config: self._validate_anthropic_config(config),
                severity=ValidationSeverity.WARNING,
                error_message="Anthropic配置验证失败",
                description="Anthropic特定配置验证"
            ),
        ])
    
    def validate_config(self, config: Dict[str, Any], config_path: Optional[str] = None) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            config_path: 配置文件路径（可选）
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])
        
        # 基础字段验证
        for rule in self.rules:
            self._validate_rule(config, rule, result, config_path)
        
        # Provider配置验证
        if "_provider_meta" in config:
            self._validate_provider_config(config, result, config_path)
        
        # 继承关系验证
        if "inherits_from" in config:
            self._validate_inheritance(config, result, config_path)
        
        # 配置完整性验证
        self._validate_config_completeness(config, result, config_path)
        
        logger.debug(f"配置验证完成: {result.get_summary()}")
        return result
    
    def _validate_rule(self, config: Dict[str, Any], rule: ValidationRule, 
                      result: ValidationResult, config_path: Optional[str]) -> None:
        """验证单个规则
        
        Args:
            config: 配置数据
            rule: 验证规则
            result: 验证结果
            config_path: 配置文件路径
        """
        try:
            value = self._get_nested_value(config, rule.field_path)
            
            # 检查必需字段
            if rule.required and value is None:
                message = f"必需字段 '{rule.field_path}' 缺失"
                if rule.error_message:
                    message += f": {rule.error_message}"
                self._add_message(result, rule.severity, message)
                return
            
            # 如果值为None且不是必需的，跳过其他验证
            if value is None:
                return
            
            # 类型验证
            if rule.field_type and not isinstance(value, rule.field_type):
                message = (f"字段 '{rule.field_path}' 类型错误: "
                          f"期望 {rule.field_type.__name__}, 实际 {type(value).__name__}")
                self._add_message(result, rule.severity, message)
                return
            
            # 数值范围验证
            if isinstance(value, (int, float)):
                if rule.min_value is not None and value < rule.min_value:
                    message = (f"字段 '{rule.field_path}' 值过小: "
                              f"最小值 {rule.min_value}, 实际值 {value}")
                    self._add_message(result, rule.severity, message)
                
                if rule.max_value is not None and value > rule.max_value:
                    message = (f"字段 '{rule.field_path}' 值过大: "
                              f"最大值 {rule.max_value}, 实际值 {value}")
                    self._add_message(result, rule.severity, message)
            
            # 字符串长度验证
            if isinstance(value, str) and hasattr(rule, 'min_length') and rule.min_length is not None:
                if len(value) < rule.min_length:
                    message = (f"字段 '{rule.field_path}' 长度过短: "
                              f"最小长度 {rule.min_length}, 实际长度 {len(value)}")
                    self._add_message(result, rule.severity, message)
            
            # 允许值验证
            if rule.allowed_values and value not in rule.allowed_values:
                message = (f"字段 '{rule.field_path}' 值无效: "
                          f"允许值 {rule.allowed_values}, 实际值 {value}")
                self._add_message(result, rule.severity, message)
            
            # 正则表达式验证
            if rule.pattern and isinstance(value, str):
                import re
                if not re.match(rule.pattern, value):
                    message = f"字段 '{rule.field_path}' 格式无效: {rule.error_message}"
                    self._add_message(result, rule.severity, message)
            
            # 自定义验证
            if rule.custom_validator:
                try:
                    if not rule.custom_validator(config):
                        message = (f"字段 '{rule.field_path}' 自定义验证失败: "
                                  f"{rule.error_message or '未知错误'}")
                        self._add_message(result, rule.severity, message)
                except Exception as e:
                    message = f"字段 '{rule.field_path}' 自定义验证器出错: {e}"
                    self._add_message(result, ValidationSeverity.ERROR, message)
                    
        except Exception as e:
            message = f"验证字段 '{rule.field_path}' 时出错: {str(e)}"
            self._add_message(result, ValidationSeverity.ERROR, message)
    
    def _validate_provider_config(self, config: Dict[str, Any], result: ValidationResult, 
                                 config_path: Optional[str]) -> None:
        """验证Provider配置
        
        Args:
            config: 配置数据
            result: 验证结果
            config_path: 配置文件路径
        """
        provider_meta = config.get("_provider_meta")
        if not provider_meta:
            return
        
        provider_name = provider_meta.get("provider_name")
        model_name = provider_meta.get("model_name")
        
        if not provider_name or not model_name:
            result.add_warning("Provider配置元信息不完整")
            return
        
        # 验证Provider和模型的一致性
        if config.get("model_type") and config.get("model_type") != provider_name:
            result.add_warning(f"model_type ({config.get('model_type')}) 与provider_name ({provider_name}) 不一致")
        
        # 验证配置文件路径
        common_config_path = provider_meta.get("common_config_path")
        model_config_path = provider_meta.get("model_config_path")
        
        if config_path and model_config_path:
            expected_path = Path(config_path).as_posix()
            actual_path = model_config_path
            if expected_path != actual_path:
                result.add_info(f"配置文件路径不匹配: 期望 {expected_path}, 实际 {actual_path}")
    
    def _validate_inheritance(self, config: Dict[str, Any], result: ValidationResult, 
                            config_path: Optional[str]) -> None:
        """验证继承关系
        
        Args:
            config: 配置数据
            result: 验证结果
            config_path: 配置文件路径
        """
        inherits_from = config.get("inherits_from")
        if not inherits_from:
            return
        
        if isinstance(inherits_from, str):
            # 验证单个继承路径
            self._validate_inheritance_path(inherits_from, result, config_path)
        elif isinstance(inherits_from, list):
            # 验证多个继承路径
            for path in inherits_from:
                self._validate_inheritance_path(path, result, config_path)
        else:
            result.add_error(f"inherits_from 必须是字符串或字符串列表，实际类型: {type(inherits_from).__name__}")
    
    def _validate_inheritance_path(self, path: str, result: ValidationResult, 
                                 config_path: Optional[str]) -> None:
        """验证单个继承路径
        
        Args:
            path: 继承路径
            result: 验证结果
            config_path: 配置文件路径
        """
        if not isinstance(path, str) or not path.strip():
            result.add_error("继承路径不能为空")
            return
        
        # 检查路径格式
        if path.startswith("provider/"):
            # Provider路径验证
            parts = path.split("/")
            if len(parts) < 3:
                result.add_error(f"Provider继承路径格式错误: {path}，应为 provider/provider_name/file_name")
            else:
                provider_name = parts[1]
                file_name = parts[2]
                if not provider_name or not file_name:
                    result.add_error(f"Provider继承路径缺少必要部分: {path}")
        elif path.startswith("/"):
            # 绝对路径验证
            if len(path.strip("/").split("/")) < 2:
                result.add_error(f"绝对继承路径格式错误: {path}")
        else:
            # 相对路径验证
            if not config_path:
                result.add_warning(f"相对继承路径 {path} 需要配置文件路径信息进行验证")
    
    def _validate_config_completeness(self, config: Dict[str, Any], result: ValidationResult, 
                                    config_path: Optional[str]) -> None:
        """验证配置完整性
        
        Args:
            config: 配置数据
            result: 验证结果
            config_path: 配置文件路径
        """
        # 检查API密钥配置
        if config.get("model_type") in ["openai", "anthropic", "gemini"]:
            if not config.get("api_key") and not config.get("base_url"):
                result.add_warning(f"{config.get('model_type')} 模型建议设置 api_key 或 base_url")
        
        # 检查模型参数合理性
        temperature = config.get("temperature")
        max_tokens = config.get("max_tokens")
        
        if temperature is not None and max_tokens is not None:
            if temperature > 1.5 and max_tokens > 4000:
                result.add_info("高温度值与大token数组合可能影响生成质量")
        
        # 检查网络配置
        timeout = config.get("timeout")
        max_retries = config.get("max_retries")
        
        if timeout is not None and max_retries is not None:
            total_timeout = timeout * (max_retries + 1)
            if total_timeout > 300:
                result.add_warning(f"总超时时间可能过长: {total_timeout}秒")
    
    def _validate_openai_config(self, config: Dict[str, Any]) -> bool:
        """验证OpenAI特定配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否有效
        """
        # OpenAI特定验证逻辑
        model_name = config.get("model_name", "")
        
        # 检查模型名称格式
        if not model_name.startswith(("gpt-", "text-", "code-", "davinci-", "curie-", "babbage-", "ada-")):
            # 可能是自定义模型，发出警告而不是错误
            logger.warning(f"OpenAI模型名称格式不常见: {model_name}")
        
        return True
    
    def _validate_anthropic_config(self, config: Dict[str, Any]) -> bool:
        """验证Anthropic特定配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 是否有效
        """
        # Anthropic特定验证逻辑
        model_name = config.get("model_name", "")
        
        # 检查模型名称格式
        if not model_name.startswith("claude-"):
            logger.warning(f"Anthropic模型名称格式不常见: {model_name}")
        
        return True
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字典中的值
        
        Args:
            data: 字典数据
            path: 字段路径
            
        Returns:
            字段值
        """
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _add_message(self, result: ValidationResult, severity: ValidationSeverity, message: str) -> None:
        """添加验证消息
        
        Args:
            result: 验证结果
            severity: 严重程度
            message: 消息内容
        """
        if severity == ValidationSeverity.ERROR or severity == ValidationSeverity.CRITICAL:
            result.add_error(f"[{severity.value.upper()}] {message}")
        elif severity == ValidationSeverity.WARNING:
            result.add_warning(f"[WARNING] {message}")
        else:
            result.add_info(f"[INFO] {message}")
    
    def add_rule(self, rule: ValidationRule) -> None:
        """添加验证规则
        
        Args:
            rule: 验证规则
        """
        self.rules.append(rule)
        logger.debug(f"添加验证规则: {rule.field_path}")
    
    def remove_rule(self, field_path: str) -> bool:
        """移除验证规则
        
        Args:
            field_path: 字段路径
            
        Returns:
            bool: 是否成功移除
        """
        original_count = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.field_path != field_path]
        removed = len(self.rules) < original_count
        
        if removed:
            logger.debug(f"移除验证规则: {field_path}")
        
        return removed
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """获取规则摘要
        
        Returns:
            Dict[str, Any]: 规则摘要信息
        """
        rules_by_severity: Dict[str, List[str]] = {}
        for rule in self.rules:
            severity = rule.severity.value
            if severity not in rules_by_severity:
                rules_by_severity[severity] = []
            rules_by_severity[severity].append(rule.field_path)
        
        return {
            "total_rules": len(self.rules),
            "rules_by_severity": rules_by_severity,
            "required_fields": [rule.field_path for rule in self.rules if rule.required],
            "optional_fields": [rule.field_path for rule in self.rules if not rule.required]
        }