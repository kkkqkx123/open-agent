"""配置验证器

配置专用验证器，在通用数据验证基础上添加业务规则验证和高级功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.infrastructure.common.utils.validator import Validator as UtilsValidator
from src.infrastructure.common.utils.validator import ValidationResult as UtilsValidationResult
from src.interfaces.common_domain import IValidationResult

from ..models.global_config import GlobalConfig
from ..models.llm_config import LLMConfig
from ..models.tool_config import ToolConfig
from ..models.token_counter_config import TokenCounterConfig

# 导入增强功能模块
from src.infrastructure.config.validation import (
    ValidationLevel,
    ValidationSeverity,
    generate_cache_key,
    ValidationReport,
    IValidationResult,
    ConfigFixer,
    FixSuggestion
)
from src.infrastructure.config.config_loader import load_config_file
from src.infrastructure.cache.core.cache_manager import CacheManager

# 创建ValidationCache类
class ValidationCache:
    """验证缓存类"""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        """获取缓存值"""
        return self.cache.get(key)
    
    def set(self, key, value):
        """设置缓存值"""
        self.cache[key] = value

# 保持接口兼容
ValidationResult = UtilsValidationResult


class IConfigValidator(ABC):
    """配置验证接口"""

    @abstractmethod
    def validate_global_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证全局配置"""
        pass

    @abstractmethod
    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置"""
        pass

    @abstractmethod
    def validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置"""
        pass

    @abstractmethod
    def validate_token_counter_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Token计数器配置"""
        pass

    # 新增增强方法
    @abstractmethod
    def validate_global_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证全局配置并返回详细报告"""
        pass

    @abstractmethod
    def validate_llm_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证LLM配置并返回详细报告"""
        pass

    @abstractmethod
    def validate_tool_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证工具配置并返回详细报告"""
        pass

    @abstractmethod
    def validate_token_counter_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证Token计数器配置并返回详细报告"""
        pass

    @abstractmethod
    def validate_config_with_cache(self, config_path: str, config_type: str) -> ValidationReport:
        """带缓存的配置验证"""
        pass

    @abstractmethod
    def suggest_config_fixes(self, config: Dict[str, Any], config_type: str) -> List[FixSuggestion]:
        """为配置提供修复建议"""
        pass


class ConfigValidator(UtilsValidator, IConfigValidator):
    """配置验证器
    
    在通用数据验证基础上添加配置特定的业务规则验证和高级功能。
    """
    
    def __init__(self):
        super().__init__()
        self.cache = ValidationCache()
        self.config_fixer = ConfigFixer()

    def validate_global_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证全局配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate(config, GlobalConfig)

        # 额外的业务逻辑验证
        if result.is_valid:
            # 检查日志输出配置
            log_outputs = config.get("log_outputs", [])
            if not log_outputs:
                result.add_warning("未配置日志输出，日志可能不会被记录")
            else:
                # 检查文件日志输出是否配置了路径
                for output in log_outputs:
                    if output.get("type") == "file" and not output.get("path"):
                        result.add_warning("文件日志输出未配置路径，可能无法写入日志")

            # 检查敏感信息模式
            secret_patterns = config.get("secret_patterns", [])
            if not secret_patterns:
                result.add_warning("未配置敏感信息模式，日志可能泄露敏感信息")

            # 检查环境配置
            if config.get("env") == "production" and config.get("debug"):
                result.add_warning("生产环境不建议启用调试模式")

        return result

    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate(config, LLMConfig)

        # 额外的业务逻辑验证
        if result.is_valid:
            # 检查API密钥是否已配置（如果需要）
            if config.get("model_type") in [
                "openai",
                "gemini",
                "anthropic",
            ] and not config.get("api_key"):
                result.add_warning("未配置API密钥，可能需要在运行时通过环境变量提供")

            # 检查基础URL是否已配置（如果需要）
            if not config.get("base_url") and config.get("model_type") not in [
                "openai"
            ]:
                result.add_warning("未配置基础URL，可能使用默认值")
            
            # 验证重试配置
            retry_config = config.get("retry_config", {})
            if isinstance(retry_config, dict):
                max_retries = retry_config.get("max_retries")
                if max_retries is not None and (not isinstance(max_retries, int) or max_retries < 0):
                    result.add_error(f"retry_config.max_retries必须是非负整数，当前值: {max_retries}")
                
                base_delay = retry_config.get("base_delay")
                if base_delay is not None and (not isinstance(base_delay, (int, float)) or base_delay <= 0):
                    result.add_error(f"retry_config.base_delay必须是正数，当前值: {base_delay}")
                
                max_delay = retry_config.get("max_delay")
                if max_delay is not None and (not isinstance(max_delay, (int, float)) or max_delay <= 0):
                    result.add_error(f"retry_config.max_delay必须是正数，当前值: {max_delay}")
                
                exponential_base = retry_config.get("exponential_base")
                if exponential_base is not None and (not isinstance(exponential_base, (int, float)) or exponential_base <= 1):
                    result.add_error(f"retry_config.exponential_base必须大于1，当前值: {exponential_base}")
            
            # 验证超时配置
            timeout_config = config.get("timeout_config", {})
            if isinstance(timeout_config, dict):
                request_timeout = timeout_config.get("request_timeout")
                if request_timeout is not None and (not isinstance(request_timeout, int) or request_timeout <= 0):
                    result.add_error(f"timeout_config.request_timeout必须是正整数，当前值: {request_timeout}")
                
                connect_timeout = timeout_config.get("connect_timeout")
                if connect_timeout is not None and (not isinstance(connect_timeout, int) or connect_timeout <= 0):
                    result.add_error(f"timeout_config.connect_timeout必须是正整数，当前值: {connect_timeout}")
                
                read_timeout = timeout_config.get("read_timeout")
                if read_timeout is not None and (not isinstance(read_timeout, int) or read_timeout <= 0):
                    result.add_error(f"timeout_config.read_timeout必须是正整数，当前值: {read_timeout}")
                
                write_timeout = timeout_config.get("write_timeout")
                if write_timeout is not None and (not isinstance(write_timeout, int) or write_timeout <= 0):
                    result.add_error(f"timeout_config.write_timeout必须是正整数，当前值: {write_timeout}")

        return result

    def validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate(config, ToolConfig)

        # 额外的业务逻辑验证
        if result.is_valid:
            # 检查是否配置了工具
            if not config.get("tools"):
                result.add_warning("未配置任何工具，工具集可能为空")

        return result

    def validate_token_counter_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Token计数器配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate(config, TokenCounterConfig)

        # 额外的业务逻辑验证
        if result.is_valid:
            # 检查增强模式配置
            if config.get("enhanced", False):
                # 增强模式建议配置缓存
                if not config.get("cache"):
                    result.add_warning("增强模式建议配置缓存以提高性能")
                
                # 增强模式建议配置校准
                if not config.get("calibration"):
                    result.add_warning("增强模式建议配置校准以提高准确性")

            # 检查模型类型和名称的匹配性
            model_type = config.get("model_type")
            model_name = config.get("model_name")

            if model_type == "openai" and model_name and not model_name.startswith(("gpt-", "text-", "code-")):
                result.add_warning(f"OpenAI模型名称 {model_name} 可能不符合命名规范")
            elif model_type == "anthropic" and model_name and not "claude" in model_name.lower():
                result.add_warning(f"Anthropic模型名称 {model_name} 可能不符合命名规范")
            elif model_type == "gemini" and model_name and not "gemini" in model_name.lower():
                result.add_warning(f"Gemini模型名称 {model_name} 可能不符合命名规范")

        return result

    # 新增增强功能方法
    def _validate_config_with_report(self, config: Dict[str, Any], config_type: str,
                                   validation_method) -> ValidationReport:
        """通用验证报告方法"""
        report = ValidationReport(f"{config_type}_config")
        # 基础验证
        basic_result = validation_method(config)
        
        # 直接创建FrameworkValidationResult
        from src.infrastructure.config.validation.framework import FrameworkValidationResult
        
        # 确定消息和严重性
        message = "基础验证结果"
        severity = ValidationSeverity.INFO
        
        if not basic_result.is_valid:
            message = "; ".join(basic_result.errors)
            severity = ValidationSeverity.ERROR
        elif basic_result.has_warnings():
            message = "; ".join(basic_result.warnings)
            severity = ValidationSeverity.WARNING
        
        # 创建FrameworkValidationResult
        framework_result = FrameworkValidationResult(
            rule_id=f"{config_type}_config_basic",
            level=ValidationLevel.SCHEMA,
            passed=basic_result.is_valid,
            message="Enhanced validation result"
        )
        report.add_level_results(ValidationLevel.SCHEMA, [framework_result])
        return report

    def validate_global_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证全局配置并返回详细报告"""
        return self._validate_config_with_report(config, "global", self.validate_global_config)

    def validate_llm_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证LLM配置并返回详细报告"""
        return self._validate_config_with_report(config, "llm", self.validate_llm_config)

    def validate_tool_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证工具配置并返回详细报告"""
        return self._validate_config_with_report(config, "tool", self.validate_tool_config)

    def validate_token_counter_config_with_report(self, config: Dict[str, Any]) -> ValidationReport:
        """验证Token计数器配置并返回详细报告"""
        return self._validate_config_with_report(config, "token_counter", self.validate_token_counter_config)

    def validate_config_with_cache(self, config_path: str, config_type: str) -> ValidationReport:
        """带缓存的配置验证"""
        cache_key = f"{config_path}_{config_type}"
        cached_result = self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        # 根据配置类型加载并验证配置
        config_data = load_config_file(config_path)
        
        if config_type == "global":
            result = self.validate_global_config_with_report(config_data)
        elif config_type == "llm":
            result = self.validate_llm_config_with_report(config_data)
        elif config_type == "tool":
            result = self.validate_tool_config_with_report(config_data)
        elif config_type == "token_counter":
            result = self.validate_token_counter_config_with_report(config_data)
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")
        
        self.cache.set(cache_key, result)
        return result

    def suggest_config_fixes(self, config: Dict[str, Any], config_type: str) -> List[FixSuggestion]:
        """为配置提供修复建议"""
        # 先验证配置获取问题
        if config_type == "global":
            report = self.validate_global_config_with_report(config)
        elif config_type == "llm":
            report = self.validate_llm_config_with_report(config)
        elif config_type == "tool":
            report = self.validate_tool_config_with_report(config)
        elif config_type == "token_counter":
            report = self.validate_token_counter_config_with_report(config)
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")
        
        # 从报告中提取修复建议
        return report.get_fix_suggestions()
