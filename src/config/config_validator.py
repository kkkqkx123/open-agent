"""配置验证器"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional
from pydantic import BaseModel, ValidationError

from .models.global_config import GlobalConfig
from .models.llm_config import LLMConfig
from .models.agent_config import AgentConfig
from .models.tool_config import ToolConfig


class ValidationResult:
    """验证结果"""

    def __init__(
        self,
        is_valid: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        """初始化验证结果

        Args:
            is_valid: 是否有效
            errors: 错误列表
            warnings: 警告列表
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        """添加错误

        Args:
            error: 错误信息
        """
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """添加警告

        Args:
            warning: 警告信息
        """
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """检查是否有错误

        Returns:
            是否有错误
        """
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """检查是否有警告

        Returns:
            是否有警告
        """
        return len(self.warnings) > 0


class IConfigValidator(ABC):
    """配置验证器接口"""

    @abstractmethod
    def validate_config(
        self, config: Dict[str, Any], model: Type[BaseModel]
    ) -> ValidationResult:
        """验证配置

        Args:
            config: 配置字典
            model: Pydantic模型类

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    def validate_agent_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Agent配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    def validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    def validate_global_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证全局配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        pass


class ConfigValidator(IConfigValidator):
    """配置验证器实现"""

    def validate_config(
        self, config: Dict[str, Any], model: Type[BaseModel]
    ) -> ValidationResult:
        """验证配置

        Args:
            config: 配置字典
            model: Pydantic模型类

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        try:
            # 使用Pydantic模型验证配置
            model(**config)
        except ValidationError as e:
            result.is_valid = False
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = f"字段 '{field_path}': {error['msg']}"
                result.add_error(error_msg)
        except Exception as e:
            result.is_valid = False
            result.add_error(f"验证配置时发生错误: {str(e)}")

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

        return result

    def validate_agent_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Agent配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        result = self.validate_config(config, AgentConfig)

        # 额外的业务逻辑验证
        if result.is_valid:
            # 检查是否配置了工具或工具集
            if not config.get("tools") and not config.get("tool_sets"):
                result.add_warning("未配置任何工具或工具集，Agent可能无法执行任务")

            # 检查系统提示词是否为空
            if not config.get("system_prompt"):
                result.add_warning("系统提示词为空，可能影响Agent行为")

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
