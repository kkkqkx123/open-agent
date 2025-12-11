"""
配置验证器

提供LLM配置文件的验证功能。
"""

from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """验证严重程度"""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """验证结果"""
    
    is_valid: bool
    severity: ValidationSeverity
    message: str
    field_path: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """验证报告"""
    
    config_type: str
    provider: Optional[str]
    model: Optional[str]
    results: List[ValidationResult]
    
    @property
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return not any(r.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] for r in self.results)
    
    @property
    def has_warnings(self) -> bool:
        """检查是否有警告"""
        return any(r.severity == ValidationSeverity.WARNING for r in self.results)
    
    @property
    def error_count(self) -> int:
        """错误数量"""
        return sum(1 for r in self.results if r.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])
    
    @property
    def warning_count(self) -> int:
        """警告数量"""
        return sum(1 for r in self.results if r.severity == ValidationSeverity.WARNING)
    
    def get_errors(self) -> List[ValidationResult]:
        """获取所有错误"""
        return [r for r in self.results if r.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
    
    def get_warnings(self) -> List[ValidationResult]:
        """获取所有警告"""
        return [r for r in self.results if r.severity == ValidationSeverity.WARNING]


class ConfigValidator:
    """配置验证器
    
    负责验证LLM配置文件的正确性和完整性。
    """
    
    def __init__(self):
        """初始化配置验证器"""
        self._validators: Dict[str, List[Callable]] = {
            "global": [self._validate_global_config],
            "provider": [self._validate_provider_config],
            "model": [self._validate_model_config],
            "tool": [self._validate_tool_config]
        }
        
        logger.info("配置验证器初始化完成")
    
    def validate_config(
        self,
        config_data: Dict[str, Any],
        config_type: str,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> ValidationReport:
        """
        验证配置
        
        Args:
            config_data: 配置数据
            config_type: 配置类型
            provider: 提供商名称
            model: 模型名称
            
        Returns:
            ValidationReport: 验证报告
        """
        results = []
        
        # 基础验证
        results.extend(self._validate_basic_structure(config_data))
        
        # 类型特定验证
        if config_type in self._validators:
            for validator in self._validators[config_type]:
                results.extend(validator(config_data, provider, model))
        
        # 提供商特定验证
        if provider:
            results.extend(self._validate_provider_specific(config_data, provider))
        
        # 模型特定验证
        if model:
            results.extend(self._validate_model_specific(config_data, model))
        
        return ValidationReport(
            config_type=config_type,
            provider=provider,
            model=model,
            results=results
        )
    
    def _validate_basic_structure(self, config_data: Dict[str, Any]) -> List[ValidationResult]:
        """验证基础结构"""
        results = []
        
        if not isinstance(config_data, dict):
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="配置必须是字典类型",
                suggestion="确保配置文件格式正确"
            ))
            return results
        
        if not config_data:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="配置不能为空",
                suggestion="添加必要的配置项"
            ))
        
        return results
    
    def _validate_global_config(self, config_data: Dict[str, Any], provider: Optional[str], model: Optional[str]) -> List[ValidationResult]:
        """验证全局配置"""
        results = []
        
        # 检查日志配置
        if "logging" in config_data:
            logging_config = config_data["logging"]
            if not isinstance(logging_config, dict):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="logging配置必须是字典类型",
                    field_path="logging",
                    suggestion="检查logging配置格式"
                ))
            else:
                # 验证日志级别
                if "level" in logging_config:
                    level = logging_config["level"]
                    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                    if level not in valid_levels:
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.WARNING,
                            message=f"无效的日志级别: {level}",
                            field_path="logging.level",
                            suggestion=f"使用有效的日志级别: {', '.join(valid_levels)}"
                        ))
        
        # 检查API密钥配置
        if "api_keys" in config_data:
            api_keys = config_data["api_keys"]
            if not isinstance(api_keys, dict):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="api_keys配置必须是字典类型",
                    field_path="api_keys",
                    suggestion="检查api_keys配置格式"
                ))
        
        return results
    
    def _validate_provider_config(self, config_data: Dict[str, Any], provider: Optional[str], model: Optional[str]) -> List[ValidationResult]:
        """验证提供商配置"""
        results = []
        
        # 检查必需字段
        required_fields = ["type", "base_url"]
        for field in required_fields:
            if field not in config_data:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"缺少必需字段: {field}",
                    field_path=field,
                    suggestion=f"添加{field}字段到配置中"
                ))
        
        # 验证提供商类型
        if "type" in config_data:
            provider_type = config_data["type"]
            valid_types = ["openai", "gemini", "anthropic", "mock"]
            if provider_type not in valid_types:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"未知的提供商类型: {provider_type}",
                    field_path="type",
                    suggestion=f"使用有效的提供商类型: {', '.join(valid_types)}"
                ))
        
        # 验证URL格式
        if "base_url" in config_data:
            base_url = config_data["base_url"]
            if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://")):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="base_url必须是有效的HTTP/HTTPS URL",
                    field_path="base_url",
                    suggestion="提供完整的URL，如: https://api.openai.com/v1"
                ))
        
        return results
    
    def _validate_model_config(self, config_data: Dict[str, Any], provider: Optional[str], model: Optional[str]) -> List[ValidationResult]:
        """验证模型配置"""
        results = []
        
        # 检查必需字段
        if "model" not in config_data:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="缺少model字段",
                field_path="model",
                suggestion="添加model字段到配置中"
            ))
        
        # 验证token计算配置
        if "token_calculation" in config_data:
            token_config = config_data["token_calculation"]
            if not isinstance(token_config, dict):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="token_calculation配置必须是字典类型",
                    field_path="token_calculation",
                    suggestion="检查token_calculation配置格式"
                ))
            else:
                # 验证tokenizer类型
                if "type" in token_config:
                    tokenizer_type = token_config["type"]
                    valid_types = ["tiktoken", "huggingface", "custom"]
                    if tokenizer_type not in valid_types:
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.WARNING,
                            message=f"未知的tokenizer类型: {tokenizer_type}",
                            field_path="token_calculation.type",
                            suggestion=f"使用有效的tokenizer类型: {', '.join(valid_types)}"
                        ))
        
        return results
    
    def _validate_tool_config(self, config_data: Dict[str, Any], provider: Optional[str], model: Optional[str]) -> List[ValidationResult]:
        """验证工具配置"""
        results = []
        
        # 检查工具列表
        if "tools" in config_data:
            tools = config_data["tools"]
            if not isinstance(tools, list):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="tools配置必须是列表类型",
                    field_path="tools",
                    suggestion="检查tools配置格式"
                ))
            else:
                # 验证每个工具配置
                for i, tool in enumerate(tools):
                    if not isinstance(tool, dict):
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            message=f"工具[{i}]配置必须是字典类型",
                            field_path=f"tools[{i}]",
                            suggestion="检查工具配置格式"
                        ))
                        continue
                    
                    # 检查工具必需字段
                    if "name" not in tool:
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            message=f"工具[{i}]缺少name字段",
                            field_path=f"tools[{i}].name",
                            suggestion="为工具添加name字段"
                        ))
                    
                    if "description" not in tool:
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.WARNING,
                            message=f"工具[{i}]缺少description字段",
                            field_path=f"tools[{i}].description",
                            suggestion="为工具添加description字段"
                        ))
        
        return results
    
    def _validate_provider_specific(self, config_data: Dict[str, Any], provider: str) -> List[ValidationResult]:
        """验证提供商特定配置"""
        results = []
        
        if provider == "openai":
            results.extend(self._validate_openai_config(config_data))
        elif provider == "gemini":
            results.extend(self._validate_gemini_config(config_data))
        elif provider == "anthropic":
            results.extend(self._validate_anthropic_config(config_data))
        
        return results
    
    def _validate_openai_config(self, config_data: Dict[str, Any]) -> List[ValidationResult]:
        """验证OpenAI特定配置"""
        results = []
        
        # 验证API版本
        if "api_version" in config_data:
            api_version = config_data["api_version"]
            valid_versions = ["2023-05-15", "2023-06-01", "2023-07-01", "2023-10-01", "2023-12-01", "2024-02-01"]
            if api_version not in valid_versions:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"可能过时的API版本: {api_version}",
                    field_path="api_version",
                    suggestion="考虑使用最新的API版本"
                ))
        
        return results
    
    def _validate_gemini_config(self, config_data: Dict[str, Any]) -> List[ValidationResult]:
        """验证Gemini特定配置"""
        results = []
        
        # Gemini特定验证逻辑
        if "api_version" in config_data:
            api_version = config_data["api_version"]
            if api_version != "v1":
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"不支持的API版本: {api_version}",
                    field_path="api_version",
                    suggestion="使用v1 API版本"
                ))
        
        return results
    
    def _validate_anthropic_config(self, config_data: Dict[str, Any]) -> List[ValidationResult]:
        """验证Anthropic特定配置"""
        results = []
        
        # Anthropic特定验证逻辑
        if "api_version" in config_data:
            api_version = config_data["api_version"]
            if api_version != "2023-06-01":
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"可能过时的API版本: {api_version}",
                    field_path="api_version",
                    suggestion="使用2023-06-01 API版本"
                ))
        
        return results
    
    def _validate_model_specific(self, config_data: Dict[str, Any], model: str) -> List[ValidationResult]:
        """验证模型特定配置"""
        results = []
        
        # 模型特定验证逻辑
        if model.startswith("gpt-"):
            results.extend(self._validate_openai_model_config(config_data, model))
        elif model.startswith("gemini-"):
            results.extend(self._validate_gemini_model_config(config_data, model))
        elif model.startswith("claude-"):
            results.extend(self._validate_anthropic_model_config(config_data, model))
        
        return results
    
    def _validate_openai_model_config(self, config_data: Dict[str, Any], model: str) -> List[ValidationResult]:
        """验证OpenAI模型特定配置"""
        results = []
        
        # OpenAI模型特定验证
        if "max_tokens" in config_data:
            max_tokens = config_data["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="max_tokens必须是正整数",
                    field_path="max_tokens",
                    suggestion="设置有效的max_tokens值"
                ))
        
        return results
    
    def _validate_gemini_model_config(self, config_data: Dict[str, Any], model: str) -> List[ValidationResult]:
        """验证Gemini模型特定配置"""
        results = []
        
        # Gemini模型特定验证
        if "max_output_tokens" in config_data:
            max_tokens = config_data["max_output_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="max_output_tokens必须是正整数",
                    field_path="max_output_tokens",
                    suggestion="设置有效的max_output_tokens值"
                ))
        
        return results
    
    def _validate_anthropic_model_config(self, config_data: Dict[str, Any], model: str) -> List[ValidationResult]:
        """验证Anthropic模型特定配置"""
        results = []
        
        # Anthropic模型特定验证
        if "max_tokens" in config_data:
            max_tokens = config_data["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="max_tokens必须是正整数",
                    field_path="max_tokens",
                    suggestion="设置有效的max_tokens值"
                ))
        
        return results
    
    def register_validator(self, config_type: str, validator: Callable) -> None:
        """
        注册自定义验证器
        
        Args:
            config_type: 配置类型
            validator: 验证器函数
        """
        if config_type not in self._validators:
            self._validators[config_type] = []
        
        self._validators[config_type].append(validator)
        logger.info(f"注册自定义验证器: {config_type}")
    
    def unregister_validator(self, config_type: str, validator: Callable) -> bool:
        """
        注销自定义验证器
        
        Args:
            config_type: 配置类型
            validator: 验证器函数
            
        Returns:
            bool: 是否成功注销
        """
        if config_type in self._validators and validator in self._validators[config_type]:
            self._validators[config_type].remove(validator)
            logger.info(f"注销自定义验证器: {config_type}")
            return True
        return False


# 全局配置验证器实例
_global_validator: Optional[ConfigValidator] = None


def get_config_validator() -> ConfigValidator:
    """
    获取全局配置验证器实例
    
    Returns:
        ConfigValidator: 配置验证器实例
    """
    global _global_validator
    if _global_validator is None:
        _global_validator = ConfigValidator()
    return _global_validator