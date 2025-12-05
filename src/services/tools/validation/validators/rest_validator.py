"""
REST工具验证器
验证REST工具的配置和实现
"""

from typing import Dict, Any, List
from src.interfaces.logger import ILogger
from ..models import ValidationResult, ValidationStatus
from ..validators.base_validator import BaseValidator


class RestToolValidator(BaseValidator):
    """REST工具验证器"""
    
    def __init__(self, logger: ILogger):
        """初始化REST工具验证器
        
        Args:
            logger: 日志记录器
        """
        super().__init__(logger)
    
    def validate_tool_type(self, tool_type: str, config: Dict[str, Any]) -> ValidationResult:
        """验证REST工具类型
        
        Args:
            tool_type: 工具类型
            config: 工具配置数据
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(config.get("name", "unknown"), tool_type, ValidationStatus.SUCCESS)
        
        # 验证API配置
        api_url = config.get("api_url")
        if not api_url:
            result.add_issue(ValidationStatus.ERROR, "REST工具缺少api_url")
        elif not isinstance(api_url, str):
            result.add_issue(ValidationStatus.ERROR, "api_url必须是字符串")
        
        # 验证HTTP方法
        method = config.get("method", "POST")
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if method.upper() not in valid_methods:
            result.add_issue(ValidationStatus.ERROR, f"无效的HTTP方法: {method}")
        
        # 验证认证配置
        auth_method = config.get("auth_method", "api_key")
        valid_auth_methods = ["api_key", "api_key_header", "oauth", "none"]
        if auth_method not in valid_auth_methods:
            result.add_issue(ValidationStatus.ERROR, f"无效的认证方法: {auth_method}")
        
        if auth_method in ["api_key", "api_key_header"] and not config.get("api_key"):
            result.add_issue(ValidationStatus.WARNING, "API密钥认证方法缺少api_key")
        
        # 验证超时配置
        timeout = config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0:
            result.add_issue(ValidationStatus.WARNING, "timeout必须是正整数")
        
        return result
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表"""
        return ["rest"]