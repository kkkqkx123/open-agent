"""
配置验证器
验证工具配置文件的格式和内容
"""

from typing import Dict, Any, List
from src.core.config.config_manager import ConfigManager, get_default_manager
from src.interfaces.common_infra import ILogger
from ..interfaces import IToolValidator
from ..models import ValidationResult, ValidationStatus


class ConfigValidator(IToolValidator):
    """配置验证器"""
    
    def __init__(self, config_manager: ConfigManager, logger: ILogger):
        """初始化配置验证器
         
        Args:
            config_manager: 配置管理器
            logger: 日志记录器
        """
        self.config_manager = config_manager
        self.logger = logger
    
    def validate_config(self, config_path: str) -> ValidationResult:
        """验证工具配置文件
         
        Args:
            config_path: 配置文件路径
             
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult("unknown", "unknown", ValidationStatus.SUCCESS)
         
        try:
            # 使用统一配置管理器加载配置
            config_data = self.config_manager.load_config_for_module(config_path, "tools")
            result.metadata["config_data"] = config_data
             
            # 验证必需字段
            required_fields = ["name", "tool_type", "description", "parameters_schema"]
            for field in required_fields:
                if field not in config_data:
                    result.add_issue(
                        ValidationStatus.ERROR,
                        f"缺少必需字段: {field}",
                        field=field
                    )
             
            # 验证工具类型
            tool_type = config_data.get("tool_type")
            if tool_type not in ["rest", "native", "mcp"]:
                result.add_issue(
                    ValidationStatus.ERROR,
                    f"无效的工具类型: {tool_type}",
                    tool_type=tool_type
                )
             
            # 验证参数Schema
            if "parameters_schema" in config_data:
                schema_errors = self._validate_schema(config_data["parameters_schema"])
                for error in schema_errors:
                    result.add_issue(ValidationStatus.ERROR, error)
             
            # 更新结果元数据
            result.tool_name = config_data.get("name", "unknown")
            result.tool_type = tool_type or "unknown"
             
        except Exception as e:
            result.add_issue(ValidationStatus.ERROR, f"配置文件加载失败: {e}")
         
        return result
    
    async def validate_loading(self, tool_name: str) -> ValidationResult:
        """验证工具加载过程 - 配置验证器不实现此方法"""
        result = ValidationResult(tool_name, "unknown", ValidationStatus.WARNING)
        result.add_issue(
            ValidationStatus.WARNING,
            "配置验证器不支持加载验证",
            suggestion="使用加载验证器进行加载验证"
        )
        return result
    
    def validate_tool_type(self, tool_type: str, config: Dict[str, Any]) -> ValidationResult:
        """验证特定工具类型 - 配置验证器不实现此方法"""
        result = ValidationResult(config.get("name", "unknown"), tool_type, ValidationStatus.WARNING)
        result.add_issue(
            ValidationStatus.WARNING,
            "配置验证器不支持类型特定验证",
            suggestion="使用类型特定验证器进行验证"
        )
        return result
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表"""
        return ["rest", "native", "mcp"]
    
    def _validate_schema(self, schema: Dict[str, Any]) -> List[str]:
        """验证参数Schema
        
        Args:
            schema: 参数Schema
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证Schema基本结构
        if not isinstance(schema, dict):
            errors.append("参数Schema必须是字典格式")
            return errors
        
        # 验证type字段
        if "type" not in schema:
            errors.append("参数Schema缺少type字段")
        elif schema["type"] != "object":
            errors.append("参数Schema的type字段必须是'object'")
        
        # 验证properties字段
        if "properties" not in schema:
            errors.append("参数Schema缺少properties字段")
        elif not isinstance(schema.get("properties", {}), dict):
            errors.append("参数Schema的properties字段必须是字典格式")
        
        # 验证required字段（如果存在）
        required = schema.get("required", [])
        if required and not isinstance(required, list):
            errors.append("参数Schema的required字段必须是列表格式")
        
        # 验证required中的字段是否都在properties中存在
        properties = schema.get("properties", {})
        for field in required:
            if field not in properties:
                errors.append(f"required字段中包含不存在于properties中的字段: {field}")
        
        return errors