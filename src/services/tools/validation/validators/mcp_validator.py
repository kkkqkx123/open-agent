"""
MCP工具验证器
验证MCP工具的配置和实现
"""

from typing import Dict, Any, List
from src.interfaces.common_infra import ILogger
from ..models import ValidationResult, ValidationStatus
from ..validators.base_validator import BaseValidator


class MCPToolValidator(BaseValidator):
    """MCP工具验证器"""
    
    def __init__(self, logger: ILogger):
        """初始化MCP工具验证器
        
        Args:
            logger: 日志记录器
        """
        super().__init__(logger)
    
    def validate_tool_type(self, tool_type: str, config: Dict[str, Any]) -> ValidationResult:
        """验证MCP工具类型
        
        Args:
            tool_type: 工具类型
            config: 工具配置数据
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(config.get("name", "unknown"), tool_type, ValidationStatus.SUCCESS)
        
        # 验证MCP服务器配置
        mcp_server_url = config.get("mcp_server_url")
        if not mcp_server_url:
            result.add_issue(ValidationStatus.ERROR, "MCP工具缺少mcp_server_url")
        elif not isinstance(mcp_server_url, str):
            result.add_issue(ValidationStatus.ERROR, "mcp_server_url必须是字符串")
        
        # 验证动态Schema配置
        dynamic_schema = config.get("dynamic_schema", False)
        if not isinstance(dynamic_schema, bool):
            result.add_issue(ValidationStatus.WARNING, "dynamic_schema必须是布尔值")
        
        # 验证刷新间隔配置
        refresh_interval = config.get("refresh_interval")
        if refresh_interval is not None and (not isinstance(refresh_interval, int) or refresh_interval <= 0):
            result.add_issue(ValidationStatus.WARNING, "refresh_interval必须是正整数")
        
        # 验证超时配置
        timeout = config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0:
            result.add_issue(ValidationStatus.WARNING, "timeout必须是正整数")
        
        return result
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表"""
        return ["mcp"]