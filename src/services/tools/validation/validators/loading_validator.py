"""
加载验证器
验证工具加载过程的正确性
"""

from typing import Dict, Any, List
from src.interfaces.logger import ILogger
from src.interfaces.tool.base import IToolManager
from ..interfaces import IToolValidator
from ..models import ValidationResult, ValidationStatus


class LoadingValidator(IToolValidator):
    """加载验证器"""
    
    def __init__(self, tool_manager: IToolManager, logger: ILogger):
        """初始化加载验证器
        
        Args:
            tool_manager: 工具管理器
            logger: 日志记录器
        """
        self.tool_manager = tool_manager
        self.logger = logger
    
    async def validate_loading(self, tool_name: str) -> ValidationResult:
        """验证工具加载过程
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(tool_name, "unknown", ValidationStatus.SUCCESS)
        
        try:
            # 尝试加载工具
            tool = await self.tool_manager.get_tool(tool_name)
            if tool:
                result.tool_type = getattr(tool, 'tool_type', 'unknown')
                
                # 验证工具属性
                required_attrs = ["name", "description", "get_schema"]
                for attr in required_attrs:
                    if not hasattr(tool, attr):
                        result.add_issue(
                            ValidationStatus.ERROR,
                            f"工具缺少必需属性: {attr}"
                        )
                
                # 验证Schema获取
                try:
                    schema = tool.get_schema()
                    if not isinstance(schema, dict):
                        result.add_issue(
                            ValidationStatus.ERROR,
                            "工具Schema格式不正确"
                        )
                except Exception as e:
                    result.add_issue(
                        ValidationStatus.ERROR,
                        f"获取工具Schema失败: {e}"
                    )
        
        except Exception as e:
            result.add_issue(
                ValidationStatus.ERROR,
                f"工具加载失败: {e}",
                details={"exception_type": type(e).__name__, "exception_message": str(e)}
            )
        
        return result
    
    def validate_config(self, config_path: str) -> ValidationResult:
        """验证工具配置文件 - 加载验证器不实现此方法"""
        result = ValidationResult("unknown", "unknown", ValidationStatus.WARNING)
        result.add_issue(
            ValidationStatus.WARNING,
            "加载验证器不支持配置验证",
            suggestion="使用配置验证器进行配置验证"
        )
        return result
    
    def validate_tool_type(self, tool_type: str, config: Dict[str, Any]) -> ValidationResult:
        """验证特定工具类型 - 加载验证器不实现此方法"""
        result = ValidationResult(config.get("name", "unknown"), tool_type, ValidationStatus.WARNING)
        result.add_issue(
            ValidationStatus.WARNING,
            "加载验证器不支持类型特定验证",
            suggestion="使用类型特定验证器进行验证"
        )
        return result
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表"""
        return ["rest", "rest", "mcp"]