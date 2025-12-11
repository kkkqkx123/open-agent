"""
配置验证器
"""

from typing import Dict, Any, List
from src.interfaces.tool.validator import ValidationType
from src.interfaces.logger import ILogger
from .base_validator import BaseValidator
from .models import ValidationResult, ValidationStatus


class ConfigValidator(BaseValidator):
    """配置验证器"""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """初始化配置验证器
        
        Args:
            logger: 日志记录器
        """
        super().__init__(logger)
        self._required_fields = ["name", "tool_type", "description", "parameters_schema"]
        self._valid_tool_types = ["builtin", "native", "rest", "mcp"]
    
    def get_supported_types(self) -> List[ValidationType]:
        """获取支持的验证类型"""
        return [ValidationType.CONFIG, ValidationType.SCHEMA]
    
    def _do_validate(self, target: Any, validation_type: ValidationType) -> ValidationResult:
        """执行具体验证逻辑"""
        result = self._create_result(target)
        
        if validation_type == ValidationType.CONFIG:
            self._validate_config(target, result)
        elif validation_type == ValidationType.SCHEMA:
            self._validate_schema(target, result)
        
        return result
    
    def _validate_config(self, config: Any, result: ValidationResult) -> None:
        """验证配置"""
        self._log_validation_start(config, ValidationType.CONFIG)
        
        # 验证必需字段
        for field in self._required_fields:
            if not hasattr(config, field) or getattr(config, field) is None:
                result.add_issue(
                    ValidationStatus.ERROR,
                    f"缺少必需字段: {field}",
                    field=field,
                    suggestion=f"请添加 {field} 字段到配置中"
                )
        
        # 验证工具类型
        if hasattr(config, 'tool_type'):
            tool_type = getattr(config, 'tool_type')
            if tool_type not in self._valid_tool_types:
                result.add_issue(
                    ValidationStatus.ERROR,
                    f"无效的工具类型: {tool_type}",
                    tool_type=tool_type,
                    valid_types=self._valid_tool_types,
                    suggestion=f"请使用有效的工具类型: {', '.join(self._valid_tool_types)}"
                )
        
        # 验证字段类型
        self._validate_field_types(config, result)
        
        # 验证工具类型特定配置
        if hasattr(config, 'tool_type'):
            self._validate_tool_type_specific(config, result)
        
        self._log_validation_end(config, ValidationType.CONFIG, result)
    
    def _validate_schema(self, config: Any, result: ValidationResult) -> None:
        """验证参数Schema"""
        self._log_validation_start(config, ValidationType.SCHEMA)
        
        if not hasattr(config, 'parameters_schema'):
            result.add_issue(
                ValidationStatus.ERROR,
                "缺少参数Schema",
                suggestion="请添加 parameters_schema 字段"
            )
            self._log_validation_end(config, ValidationType.SCHEMA, result)
            return
        
        schema = getattr(config, 'parameters_schema')
        
        if not isinstance(schema, dict):
            result.add_issue(
                ValidationStatus.ERROR,
                "参数Schema必须是字典格式",
                schema_type=type(schema).__name__,
                suggestion="请使用字典格式的Schema"
            )
            self._log_validation_end(config, ValidationType.SCHEMA, result)
            return
        
        # 验证Schema基本结构
        self._validate_schema_structure(schema, result)
        
        self._log_validation_end(config, ValidationType.SCHEMA, result)
    
    def _validate_field_types(self, config: Any, result: ValidationResult) -> None:
        """验证字段类型"""
        # 验证名称字段
        if hasattr(config, 'name'):
            name = getattr(config, 'name')
            if not isinstance(name, str) or not name.strip():
                result.add_issue(
                    ValidationStatus.ERROR,
                    "工具名称必须是非空字符串",
                    name=name,
                    suggestion="请提供有效的工具名称"
                )
        
        # 验证工具类型字段
        if hasattr(config, 'tool_type'):
            tool_type = getattr(config, 'tool_type')
            if not isinstance(tool_type, str):
                result.add_issue(
                    ValidationStatus.ERROR,
                    "工具类型必须是字符串",
                    tool_type=tool_type,
                    suggestion="请使用字符串类型的工具类型"
                )
        
        # 验证描述字段
        if hasattr(config, 'description'):
            description = getattr(config, 'description')
            if not isinstance(description, str) or not description.strip():
                result.add_issue(
                    ValidationStatus.ERROR,
                    "工具描述必须是非空字符串",
                    description=description,
                    suggestion="请提供有效的工具描述"
                )
    
    def _validate_tool_type_specific(self, config: Any, result: ValidationResult) -> None:
        """验证工具类型特定配置"""
        tool_type = getattr(config, 'tool_type', None)
        
        if tool_type == "builtin":
            self._validate_builtin_config(config, result)
        elif tool_type == "native":
            self._validate_native_config(config, result)
        elif tool_type == "rest":
            self._validate_rest_config(config, result)
        elif tool_type == "mcp":
            self._validate_mcp_config(config, result)
    
    def _validate_builtin_config(self, config: Any, result: ValidationResult) -> None:
        """验证内置工具配置"""
        if not hasattr(config, 'function_path'):
            result.add_issue(
                ValidationStatus.ERROR,
                "内置工具必须包含 function_path",
                suggestion="请添加 function_path 字段，格式为 'module:function'"
            )
        else:
            function_path = getattr(config, 'function_path')
            if not isinstance(function_path, str) or ':' not in function_path:
                result.add_issue(
                    ValidationStatus.ERROR,
                    "function_path 格式无效",
                    function_path=function_path,
                    suggestion="请使用 'module:function' 格式"
                )
    
    def _validate_native_config(self, config: Any, result: ValidationResult) -> None:
        """验证原生工具配置"""
        if not hasattr(config, 'function_path'):
            result.add_issue(
                ValidationStatus.ERROR,
                "原生工具必须包含 function_path",
                suggestion="请添加 function_path 字段，格式为 'module:function'"
            )
    
    def _validate_rest_config(self, config: Any, result: ValidationResult) -> None:
        """验证REST工具配置"""
        if not hasattr(config, 'api_url'):
            result.add_issue(
                ValidationStatus.ERROR,
                "REST工具必须包含 api_url",
                suggestion="请添加 api_url 字段"
            )
        else:
            api_url = getattr(config, 'api_url')
            if not isinstance(api_url, str) or not api_url.startswith(('http://', 'https://')):
                result.add_issue(
                    ValidationStatus.ERROR,
                    "api_url 必须是有效的HTTP/HTTPS URL",
                    api_url=api_url,
                    suggestion="请使用以 http:// 或 https:// 开头的URL"
                )
    
    def _validate_mcp_config(self, config: Any, result: ValidationResult) -> None:
        """验证MCP工具配置"""
        if not hasattr(config, 'mcp_server_url'):
            result.add_issue(
                ValidationStatus.ERROR,
                "MCP工具必须包含 mcp_server_url",
                suggestion="请添加 mcp_server_url 字段"
            )
        else:
            mcp_server_url = getattr(config, 'mcp_server_url')
            if not isinstance(mcp_server_url, str) or not mcp_server_url.startswith(('http://', 'https://', 'ws://', 'wss://')):
                result.add_issue(
                    ValidationStatus.ERROR,
                    "mcp_server_url 必须是有效的URL",
                    mcp_server_url=mcp_server_url,
                    suggestion="请使用有效的URL格式"
                )
    
    def _validate_schema_structure(self, schema: Dict[str, Any], result: ValidationResult) -> None:
        """验证Schema结构"""
        # 验证type字段
        if "type" not in schema:
            result.add_issue(
                ValidationStatus.ERROR,
                "参数Schema缺少type字段",
                suggestion="请添加 type 字段，通常应为 'object'"
            )
        elif schema["type"] != "object":
            result.add_issue(
                ValidationStatus.ERROR,
                "参数Schema的type字段必须是'object'",
                schema_type=schema["type"],
                suggestion="请将 type 字段设置为 'object'"
            )
        
        # 验证properties字段
        if "properties" not in schema:
            result.add_issue(
                ValidationStatus.ERROR,
                "参数Schema缺少properties字段",
                suggestion="请添加 properties 字段来定义参数"
            )
        elif not isinstance(schema.get("properties", {}), dict):
            result.add_issue(
                ValidationStatus.ERROR,
                "参数Schema的properties字段必须是字典格式",
                properties_type=type(schema["properties"]).__name__,
                suggestion="请使用字典格式的 properties"
            )
        
        # 验证required字段（如果存在）
        required = schema.get("required", [])
        if required and not isinstance(required, list):
            result.add_issue(
                ValidationStatus.ERROR,
                "参数Schema的required字段必须是列表格式",
                required_type=type(required).__name__,
                suggestion="请使用列表格式的 required 字段"
            )
        
        # 验证required中的字段是否都在properties中存在
        properties = schema.get("properties", {})
        for field in required:
            if field not in properties:
                result.add_issue(
                    ValidationStatus.ERROR,
                    f"required字段中包含不存在于properties中的字段: {field}",
                    field=field,
                    suggestion=f"请在 properties 中添加 {field} 字段定义，或从 required 中移除"
                )


# 导出配置验证器
__all__ = [
    "ConfigValidator",
]