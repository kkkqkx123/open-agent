"""配置验证器 - 向后兼容适配器

注意：此类已迁移到 src/infrastructure/utils/validator.py
建议直接使用新的 Validator 工具类。
"""

from typing import Dict, Any, List, Type, Optional
from pydantic import BaseModel
from ...utils.validator import Validator as UtilsValidator
from ...utils.validator import ValidationResult as UtilsValidationResult
from ...utils.validator import IValidator as UtilsIValidator

from ..models.global_config import GlobalConfig
from ..models.llm_config import LLMConfig
from ..models.tool_config import ToolConfig
from ..models.token_counter_config import TokenCounterConfig

# 保持接口兼容
ValidationResult = UtilsValidationResult
IConfigValidator = UtilsIValidator

class ConfigValidator(UtilsValidator):
    """配置验证器 - 向后兼容适配器"""
    
    def validate_config(
        self, config: Dict[str, Any], model: Type[BaseModel]
    ) -> ValidationResult:
        """验证配置（向后兼容方法）

        Args:
            config: 配置字典
            model: Pydantic模型类

        Returns:
            验证结果
        """
        return self._validate_config(config, model)

    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, LLMConfig)

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
                    result.add_error("retry_config.max_retries必须是非负整数")
                
                base_delay = retry_config.get("base_delay")
                if base_delay is not None and (not isinstance(base_delay, (int, float)) or base_delay <= 0):
                    result.add_error("retry_config.base_delay必须是正数")
                
                max_delay = retry_config.get("max_delay")
                if max_delay is not None and (not isinstance(max_delay, (int, float)) or max_delay <= 0):
                    result.add_error("retry_config.max_delay必须是正数")
                
                exponential_base = retry_config.get("exponential_base")
                if exponential_base is not None and (not isinstance(exponential_base, (int, float)) or exponential_base <= 1):
                    result.add_error("retry_config.exponential_base必须大于1")
            
            # 验证超时配置
            timeout_config = config.get("timeout_config", {})
            if isinstance(timeout_config, dict):
                request_timeout = timeout_config.get("request_timeout")
                if request_timeout is not None and (not isinstance(request_timeout, int) or request_timeout <= 0):
                    result.add_error("timeout_config.request_timeout必须是正整数")
                
                connect_timeout = timeout_config.get("connect_timeout")
                if connect_timeout is not None and (not isinstance(connect_timeout, int) or connect_timeout <= 0):
                    result.add_error("timeout_config.connect_timeout必须是正整数")
                
                read_timeout = timeout_config.get("read_timeout")
                if read_timeout is not None and (not isinstance(read_timeout, int) or read_timeout <= 0):
                    result.add_error("timeout_config.read_timeout必须是正整数")
                
                write_timeout = timeout_config.get("write_timeout")
                if write_timeout is not None and (not isinstance(write_timeout, int) or write_timeout <= 0):
                    result.add_error("timeout_config.write_timeout必须是正整数")

        return result

    def validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, ToolConfig)

        # 额外的业务逻辑验证
        if result.is_valid:
            # 检查是否配置了工具
            if not config.get("tools"):
                result.add_warning("未配置任何工具，工具集可能为空")

        return result

    def validate_global_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证全局配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, GlobalConfig)

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

    def validate_token_counter_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Token计数器配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, TokenCounterConfig)

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

    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, LLMConfig)

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
                    result.add_error("retry_config.max_retries必须是非负整数")
                
                base_delay = retry_config.get("base_delay")
                if base_delay is not None and (not isinstance(base_delay, (int, float)) or base_delay <= 0):
                    result.add_error("retry_config.base_delay必须是正数")
                
                max_delay = retry_config.get("max_delay")
                if max_delay is not None and (not isinstance(max_delay, (int, float)) or max_delay <= 0):
                    result.add_error("retry_config.max_delay必须是正数")
                
                exponential_base = retry_config.get("exponential_base")
                if exponential_base is not None and (not isinstance(exponential_base, (int, float)) or exponential_base <= 1):
                    result.add_error("retry_config.exponential_base必须大于1")
            
            # 验证超时配置
            timeout_config = config.get("timeout_config", {})
            if isinstance(timeout_config, dict):
                request_timeout = timeout_config.get("request_timeout")
                if request_timeout is not None and (not isinstance(request_timeout, int) or request_timeout <= 0):
                    result.add_error("timeout_config.request_timeout必须是正整数")
                
                connect_timeout = timeout_config.get("connect_timeout")
                if connect_timeout is not None and (not isinstance(connect_timeout, int) or connect_timeout <= 0):
                    result.add_error("timeout_config.connect_timeout必须是正整数")
                
                read_timeout = timeout_config.get("read_timeout")
                if read_timeout is not None and (not isinstance(read_timeout, int) or read_timeout <= 0):
                    result.add_error("timeout_config.read_timeout必须是正整数")
                
                write_timeout = timeout_config.get("write_timeout")
                if write_timeout is not None and (not isinstance(write_timeout, int) or write_timeout <= 0):
                    result.add_error("timeout_config.write_timeout必须是正整数")

        return result

    def validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, ToolConfig)

        # 额外的业务逻辑验证
        if result.is_valid:
            # 检查是否配置了工具
            if not config.get("tools"):
                result.add_warning("未配置任何工具，工具集可能为空")

        return result

    def validate_global_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证全局配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, GlobalConfig)

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

    def validate_token_counter_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Token计数器配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, TokenCounterConfig)

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

    def validate_config_structure(
        self, config: Dict[str, Any], required_fields: List[str]
    ) -> ValidationResult:
        """验证配置结构

        Args:
            config: 配置字典
            required_fields: 必需字段列表

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        for field in required_fields:
            if field not in config:
                result.add_error(f"缺少必需字段: {field}")

        return result

    def validate_config_types(
        self, config: Dict[str, Any], type_mapping: Dict[str, type]
    ) -> ValidationResult:
        """验证配置类型

        Args:
            config: 配置字典
            type_mapping: 字段类型映射

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        for field, expected_type in type_mapping.items():
            if field in config and not isinstance(config[field], expected_type):
                result.add_error(
                    f"字段 '{field}' 类型错误，期望 {expected_type.__name__}，实际 {type(config[field]).__name__}"
                )

        return result

    def validate_config_values(
        self, config: Dict[str, Any], value_constraints: Dict[str, Any]
    ) -> ValidationResult:
        """验证配置值

        Args:
            config: 配置字典
            value_constraints: 值约束字典

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        for field, constraints in value_constraints.items():
            if field in config:
                value = config[field]

                # 检查枚举值
                if "enum" in constraints and value not in constraints["enum"]:
                    result.add_error(
                        f"字段 '{field}' 值无效，允许的值: {constraints['enum']}"
                    )

                # 检查范围
                if "min" in constraints and value < constraints["min"]:
                    result.add_error(
                        f"字段 '{field}' 值过小，最小值: {constraints['min']}"
                    )

                if "max" in constraints and value > constraints["max"]:
                    result.add_error(
                        f"字段 '{field}' 值过大，最大值: {constraints['max']}"
                    )

                # 检查长度
                if hasattr(value, "__len__"):
                    if (
                        "min_length" in constraints
                        and len(value) < constraints["min_length"]
                    ):
                        result.add_error(
                            f"字段 '{field}' 长度过短，最小长度: {constraints['min_length']}"
                        )

                    if (
                        "max_length" in constraints
                        and len(value) > constraints["max_length"]
                    ):
                        result.add_error(
                            f"字段 '{field}' 长度过长，最大长度: {constraints['max_length']}"
                        )

                # 检查正则表达式
                if "pattern" in constraints and not constraints["pattern"].match(
                    str(value)
                ):
                    result.add_error(f"字段 '{field}' 格式无效")

        return result
