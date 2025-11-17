"""
工具验证器

提供工具参数和配置的验证功能。
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from src.core.tools.config import ToolConfig, NativeToolConfig, RestToolConfig, MCPToolConfig


class ToolValidator:
    """工具验证器

    用于验证工具配置和参数。
    """

    @classmethod
    def validate_tool_config(cls, config: ToolConfig) -> List[str]:
        """验证工具配置

        Args:
            config: 工具配置

        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []

        # 基础验证
        if not config.name:
            errors.append("工具名称不能为空")
        elif not cls._is_valid_name(config.name):
            errors.append("工具名称只能包含字母、数字、下划线和连字符")

        if not config.description:
            errors.append("工具描述不能为空")

        if not config.parameters_schema:
            errors.append("参数Schema不能为空")
        elif not cls._validate_json_schema(config.parameters_schema):
            errors.append("参数Schema格式不正确")

        # 类型特定验证
        if isinstance(config, NativeToolConfig):
            errors.extend(cls._validate_native_tool_config(config))
        elif isinstance(config, RestToolConfig):
            errors.extend(cls._validate_rest_tool_config(config))
        elif isinstance(config, MCPToolConfig):
            errors.extend(cls._validate_mcp_tool_config(config))

        return errors

    @classmethod
    def _validate_rest_tool_config(cls, config: RestToolConfig) -> List[str]:
        """验证REST工具配置

        Args:
            config: REST工具配置

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        # 验证API URL
        if not config.api_url:
            errors.append("API URL不能为空")
        elif not cls._is_valid_url(config.api_url):
            errors.append("API URL格式不正确")

        # 验证HTTP方法
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if config.method.upper() not in valid_methods:
            errors.append(f"HTTP方法必须是以下之一: {', '.join(valid_methods)}")

        # 验证认证方法
        valid_auth_methods = ["api_key", "api_key_header", "oauth", "none"]
        if config.auth_method not in valid_auth_methods:
            errors.append(f"认证方法必须是以下之一: {', '.join(valid_auth_methods)}")

        # 验证API密钥
        if config.auth_method in ["api_key", "api_key_header"] and not config.api_key:
            errors.append("使用API密钥认证时，API密钥不能为空")

        # 验证超时时间
        if config.timeout <= 0:
            errors.append("超时时间必须大于0")

        # 验证重试配置
        if config.retry_count < 0:
            errors.append("重试次数不能小于0")

        if config.retry_delay < 0:
            errors.append("重试延迟不能小于0")

        return errors

    @classmethod
    def _validate_mcp_tool_config(cls, config: MCPToolConfig) -> List[str]:
        """验证MCP工具配置

        Args:
            config: MCP工具配置

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        # 验证MCP服务器URL
        if not config.mcp_server_url:
            errors.append("MCP服务器URL不能为空")
        elif not cls._is_valid_url(config.mcp_server_url):
            errors.append("MCP服务器URL格式不正确")

        # 验证超时时间
        if config.timeout <= 0:
            errors.append("超时时间必须大于0")

        # 验证刷新间隔
        if config.refresh_interval is not None and config.refresh_interval <= 0:
            errors.append("刷新间隔必须大于0")

        return errors

    @classmethod
    def _validate_native_tool_config(cls, config: NativeToolConfig) -> List[str]:
        """验证原生工具配置

        Args:
            config: 原生工具配置

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        # 验证函数路径
        if config.function_path and not cls._is_valid_function_path(
            config.function_path
        ):
            errors.append("函数路径格式不正确，应为 'module.submodule:function_name'")

        # 验证超时时间
        if config.timeout <= 0:
            errors.append("超时时间必须大于0")

        return errors

    @classmethod
    def validate_parameters(
        cls, parameters: Dict[str, Any], schema: Dict[str, Any]
    ) -> List[str]:
        """验证参数

        Args:
            parameters: 参数字典
            schema: 参数Schema

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        # 验证必需参数
        required = schema.get("required", [])
        for param in required:
            if param not in parameters:
                errors.append(f"缺少必需参数: {param}")

        # 验证参数类型和格式
        properties = schema.get("properties", {})
        for param_name, param_value in parameters.items():
            if param_name in properties:
                param_errors = cls._validate_parameter_value(
                    param_name, param_value, properties[param_name]
                )
                errors.extend(param_errors)
            else:
                errors.append(f"未知参数: {param_name}")

        return errors

    @classmethod
    def _validate_parameter_value(
        cls, name: str, value: Any, schema: Dict[str, Any]
    ) -> List[str]:
        """验证参数值

        Args:
            name: 参数名称
            value: 参数值
            schema: 参数Schema

        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        param_type = schema.get("type")

        # 类型验证
        if param_type == "string" and not isinstance(value, str):
            errors.append(f"参数 {name} 应为字符串类型")
        elif param_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"参数 {name} 应为数字类型")
        elif param_type == "integer" and not isinstance(value, int):
            errors.append(f"参数 {name} 应为整数类型")
        elif param_type == "boolean" and not isinstance(value, bool):
            errors.append(f"参数 {name} 应为布尔类型")
        elif param_type == "array" and not isinstance(value, list):
            errors.append(f"参数 {name} 应为数组类型")
        elif param_type == "object" and not isinstance(value, dict):
            errors.append(f"参数 {name} 应为对象类型")

        # 枚举值验证
        if "enum" in schema and value not in schema["enum"]:
            errors.append(f"参数 {name} 应为以下值之一: {schema['enum']}")

        # 字符串格式验证
        if param_type == "string" and "pattern" in schema:
            pattern = schema["pattern"]
            if not re.match(pattern, str(value)):
                errors.append(f"参数 {name} 格式不正确，应符合模式: {pattern}")

        # 数值范围验证
        if param_type in ["number", "integer"]:
            if "minimum" in schema and value < schema["minimum"]:
                errors.append(f"参数 {name} 不能小于 {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                errors.append(f"参数 {name} 不能大于 {schema['maximum']}")

        # 数组长度验证
        if param_type == "array":
            if (
                isinstance(value, (list, tuple))
                and "minItems" in schema
                and len(value) < schema["minItems"]
            ):
                errors.append(f"参数 {name} 数组长度不能小于 {schema['minItems']}")
            if (
                isinstance(value, (list, tuple))
                and "maxItems" in schema
                and len(value) > schema["maxItems"]
            ):
                errors.append(f"参数 {name} 数组长度不能大于 {schema['maxItems']}")

        # 字符串长度验证
        if param_type == "string":
            if (
                isinstance(value, str)
                and "minLength" in schema
                and len(value) < schema["minLength"]
            ):
                errors.append(f"参数 {name} 长度不能小于 {schema['minLength']}")
            if (
                isinstance(value, str)
                and "maxLength" in schema
                and len(value) > schema["maxLength"]
            ):
                errors.append(f"参数 {name} 长度不能大于 {schema['maxLength']}")

        return errors

    @classmethod
    def _is_valid_name(cls, name: str) -> bool:
        """验证名称格式

        Args:
            name: 名称

        Returns:
            bool: 是否有效
        """
        # 只允许字母、数字、下划线和连字符
        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, name))

    @classmethod
    def _is_valid_url(cls, url: str) -> bool:
        """验证URL格式

        Args:
            url: URL

        Returns:
            bool: 是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @classmethod
    def _is_valid_function_path(cls, path: str) -> bool:
        """验证函数路径格式

        Args:
            path: 函数路径

        Returns:
            bool: 是否有效
        """
        # 格式应为 module.submodule:function_name
        pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*:[a-zA-Z_][a-zA-Z0-9_]*$"
        return bool(re.match(pattern, path))

    @classmethod
    def _validate_json_schema(cls, schema: Dict[str, Any]) -> bool:
        """验证JSON Schema格式

        Args:
            schema: Schema字典

        Returns:
            bool: 是否有效
        """
        # 基础验证
        if not isinstance(schema, dict):
            return False

        # 检查必需字段
        if "type" not in schema:
            return False

        if schema["type"] != "object":
            return False

        if "properties" not in schema:
            return False

        if not isinstance(schema["properties"], dict):
            return False

        # 检查required字段
        if "required" in schema:
            if not isinstance(schema["required"], list):
                return False

        return True

    @classmethod
    def sanitize_tool_name(cls, name: str) -> str:
        """清理工具名称

        Args:
            name: 原始名称

        Returns:
            str: 清理后的名称
        """
        # 移除非法字符，替换为下划线
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)

        # 确保不以数字或连字符开头
        if sanitized and (sanitized[0].isdigit() or sanitized[0] == "-"):
            sanitized = f"tool_{sanitized}"

        return sanitized

    @classmethod
    def validate_tool_set_config(
        cls, tools: List[str], available_tools: List[str]
    ) -> List[str]:
        """验证工具集配置

        Args:
            tools: 工具集配置中的工具列表
            available_tools: 可用工具列表

        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        available_set = set(available_tools)

        for tool in tools:
            if tool not in available_set:
                errors.append(f"工具集中引用的工具不存在: {tool}")

        return errors
