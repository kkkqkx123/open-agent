"""数据验证工具

提供通用的数据验证功能，可被多个模块使用。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional
from pydantic import BaseModel, ValidationError


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


class IValidator(ABC):
    """验证器接口"""

    @abstractmethod
    def validate(
        self, data: Dict[str, Any], model: Type[BaseModel]
    ) -> ValidationResult:
        """验证数据

        Args:
            data: 数据字典
            model: Pydantic模型类

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
    def validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        pass

    @abstractmethod
    def validate_token_counter_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Token计数器配置

        Args:
            config: 配置字典

        Returns:
            验证结果
        """
        pass


class Validator(IValidator):
    """数据验证器实现"""

    def validate(
        self, data: Dict[str, Any], model: Type[BaseModel]
    ) -> ValidationResult:
        """验证数据

        Args:
            data: 数据字典
            model: Pydantic模型类

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        try:
            # 使用Pydantic模型验证数据
            model(**data)
        except ValidationError as e:
            result.is_valid = False
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = f"字段 '{field_path}': {error['msg']}"
                result.add_error(error_msg)
        except Exception as e:
            result.is_valid = False
            result.add_error(f"验证数据时发生错误: {str(e)}")

        return result

    def validate_structure(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> ValidationResult:
        """验证数据结构

        Args:
            data: 数据字典
            required_fields: 必需字段列表

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        for field in required_fields:
            if field not in data:
                result.add_error(f"缺少必需字段: {field}")

        return result

    def validate_types(
        self, data: Dict[str, Any], type_mapping: Dict[str, type]
    ) -> ValidationResult:
        """验证数据类型

        Args:
            data: 数据字典
            type_mapping: 字段类型映射

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        for field, expected_type in type_mapping.items():
            if field in data and not isinstance(data[field], expected_type):
                result.add_error(
                    f"字段 '{field}' 类型错误，期望 {expected_type.__name__}，实际 {type(data[field]).__name__}"
                )

        return result

    def validate_values(
        self, data: Dict[str, Any], value_constraints: Dict[str, Any]
    ) -> ValidationResult:
        """验证数据值

        Args:
            data: 数据字典
            value_constraints: 值约束字典

        Returns:
            验证结果
        """
        result = ValidationResult(True)

        for field, constraints in value_constraints.items():
            if field in data:
                value = data[field]

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

    def validate_email(self, email: str) -> bool:
        """验证邮箱格式

        Args:
            email: 邮箱地址

        Returns:
            是否有效
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_url(self, url: str) -> bool:
        """验证URL格式

        Args:
            url: URL地址

        Returns:
            是否有效
        """
        import re
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
        return re.match(pattern, url) is not None

    def validate_phone(self, phone: str) -> bool:
        """验证手机号格式

        Args:
            phone: 手机号

        Returns:
            是否有效
        """
        import re
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None

    # 为了向后兼容，保留配置系统特定的方法
    def _validate_config(
        self, config: Dict[str, Any], model: Type[BaseModel]
    ) -> ValidationResult:
        """验证配置（内部方法）

        Args:
            config: 配置字典
            model: Pydantic模型类

        Returns:
            验证结果
        """
        return self.validate(config, model)

    def validate_global_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证全局配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 基本实现，可以被子类覆盖
        return ValidationResult(True)

    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 基本实现，可以被子类覆盖
        return ValidationResult(True)

    def validate_tool_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证工具配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 基本实现，可以被子类覆盖
        return ValidationResult(True)

    def validate_token_counter_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Token计数器配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        # 基本实现，可以被子类覆盖
        return ValidationResult(True)