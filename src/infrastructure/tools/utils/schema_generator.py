"""
Schema生成器

提供从Python函数和类型生成JSON Schema的功能。
"""

import inspect
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_type_hints,
    Callable,
    cast,
)
from enum import Enum


class SchemaGenerator:
    """Schema生成器

    用于从Python函数和类型生成JSON Schema。
    """

    # Python类型到JSON Schema类型的映射
    TYPE_MAPPING = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
        type(None): {"type": "null"},
    }

    @classmethod
    def from_function(
        cls, func: Callable[..., Any], description: Optional[str] = None
    ) -> Dict[str, Any]:
        """从函数生成Schema

        Args:
            func: Python函数
            description: 函数描述（可选）

        Returns:
            Dict[str, Any]: JSON Schema
        """
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        properties: Dict[str, Dict[str, Any]] = {}
        required: List[str] = []

        for param_name, param in sig.parameters.items():
            # 跳过self参数（方法）
            if param_name == "self":
                continue

            # 获取参数类型
            param_type = type_hints.get(param_name, param.annotation)

            # 生成属性Schema
            prop_schema = cls._generate_property_schema(param, param_type)
            properties[param_name] = prop_schema

            # 检查是否必需
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "description": description
            or func.__doc__
            or f"函数 {func.__name__} 的参数",
        }

    @classmethod
    def _generate_property_schema(
        cls, param: Optional[inspect.Parameter], param_type: Union[Type, Any]
    ) -> Dict[str, Any]:
        """生成属性Schema

        Args:
            param: 参数对象
            param_type: 参数类型

        Returns:
            Dict[str, Any]: 属性Schema
        """
        # 处理基本类型
        if param_type in cls.TYPE_MAPPING:
            schema: Dict[str, Any] = cls.TYPE_MAPPING[param_type].copy()
        # 处理Union类型（Optional）
        elif hasattr(param_type, "__origin__") and param_type.__origin__ is Union:
            # Optional[T] 实际上是 Union[T, None]
            args = param_type.__args__
            if len(args) == 2 and type(None) in args:
                # Optional类型
                non_none_type = args[0] if args[1] is type(None) else args[1]
                schema = cls._generate_property_schema(param, non_none_type)
            else:
                # 复杂Union类型
                any_of_schemas = [
                    cls._generate_property_schema(param, arg) for arg in args
                ]
                schema = {"anyOf": any_of_schemas}
        # 处理List类型
        elif hasattr(param_type, "__origin__") and param_type.__origin__ is list:
            item_type = param_type.__args__[0] if param_type.__args__ else Any
            items_schema = cls._generate_property_schema(param, item_type)
            schema = {"type": "array", "items": items_schema}
        # 处理Dict类型
        elif hasattr(param_type, "__origin__") and param_type.__origin__ is dict:
            schema = {"type": "object"}
        # 处理Enum类型
        elif inspect.isclass(param_type) and issubclass(param_type, Enum):
            enum_values = [e.value for e in param_type]
            schema = {"type": "string", "enum": enum_values}
        # 处理自定义类
        elif inspect.isclass(param_type):
            schema = cls._from_class(param_type)
        else:
            # 默认为字符串
            schema = {"type": "string"}

        # 添加默认值
        if param and param.default != inspect.Parameter.empty:
            schema["default"] = param.default

        # 添加描述
        if param and param.annotation != inspect.Parameter.empty:
            schema["description"] = f"参数 {param.name}"

        return schema

    @classmethod
    def _from_class(cls, cls_type: Type) -> Dict[str, Any]:
        """从类生成Schema

        Args:
            cls_type: 类类型

        Returns:
            Dict[str, Any]: 类Schema
        """
        # 简单实现，返回对象类型
        return {"type": "object", "description": f"对象类型: {cls_type.__name__}"}

    @classmethod
    def from_dict(
        cls, example: Dict[str, Any], description: Optional[str] = None
    ) -> Dict[str, Any]:
        """从示例字典生成Schema

        Args:
            example: 示例字典
            description: 描述（可选）

        Returns:
            Dict[str, Any]: JSON Schema
        """
        properties: Dict[str, Dict[str, Any]] = {}
        required: List[str] = []

        for key, value in example.items():
            prop_schema = cls._infer_schema_from_value(value)
            properties[key] = prop_schema
            required.append(key)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "description": description or "从示例生成的Schema",
        }

    @classmethod
    def _infer_schema_from_value(cls, value: Any) -> Dict[str, Any]:
        """从值推断Schema

        Args:
            value: 值

        Returns:
            Dict[str, Any]: 属性Schema
        """
        if isinstance(value, str):
            return {"type": "string"}
        elif isinstance(value, int):
            return {"type": "integer"}
        elif isinstance(value, float):
            return {"type": "number"}
        elif isinstance(value, bool):
            return {"type": "boolean"}
        elif isinstance(value, list):
            if value:
                item_schema = cls._infer_schema_from_value(value[0])
                return {"type": "array", "items": item_schema}
            else:
                return {"type": "array"}
        elif isinstance(value, dict):
            properties: Dict[str, Dict[str, Any]] = {}
            for k, v in value.items():
                properties[k] = cls._infer_schema_from_value(v)
            return {"type": "object", "properties": properties}
        else:
            return {"type": "string"}

    @classmethod
    def merge_schemas(cls, schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个Schema

        Args:
            schemas: Schema列表

        Returns:
            Dict[str, Any]: 合并后的Schema
        """
        if not schemas:
            return {"type": "object", "properties": {}}

        if len(schemas) == 1:
            return schemas[0]

        # 合并属性
        merged_properties: Dict[str, Dict[str, Any]] = {}
        merged_required: List[str] = []

        for schema in schemas:
            properties = schema.get("properties", {})
            if isinstance(properties, dict):
                merged_properties.update(properties)

            required = schema.get("required", [])
            if isinstance(required, list):
                merged_required.extend(required)

        # 去重必需参数
        merged_required = list(set(merged_required))

        return {
            "type": "object",
            "properties": merged_properties,
            "required": merged_required,
            "description": "合并的Schema",
        }

    @classmethod
    def create_response_schema(
        cls, response_type: Union[Type, Any], description: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建响应Schema

        Args:
            response_type: 响应类型
            description: 描述（可选）

        Returns:
            Dict[str, Any]: 响应Schema
        """
        schema: Dict[str, Any] = {}
        if response_type in cls.TYPE_MAPPING:
            schema = cls.TYPE_MAPPING[response_type].copy()
        elif hasattr(response_type, "__origin__") and response_type.__origin__ is list:
            item_type = response_type.__args__[0] if response_type.__args__ else Any
            items_schema = cls._generate_property_schema(None, item_type)
            schema = {"type": "array", "items": items_schema}
        elif hasattr(response_type, "__origin__") and response_type.__origin__ is dict:
            schema = {"type": "object"}
        else:
            schema = {"type": "object"}

        if description:
            schema["description"] = description

        return schema
