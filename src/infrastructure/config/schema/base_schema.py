"""配置模式基类

提供所有配置模式的基础实现和公共验证逻辑。
"""

from typing import Dict, Any, Optional
import logging

from src.interfaces.config.schema import IConfigSchema
from src.infrastructure.validation.result import ValidationResult

logger = logging.getLogger(__name__)


class BaseSchema(IConfigSchema):
    """配置模式基类实现
    
    提供配置模式的基础验证逻辑和公共方法。
    """
    
    def __init__(self, schema_definition: Optional[Dict[str, Any]] = None):
        """初始化配置模式
        
        Args:
            schema_definition: 模式定义
        """
        self.schema_definition = schema_definition or {}
    
    def get_schema_type(self) -> str:
        """获取模式类型
        
        Returns:
            str: 模式类型
        """
        return "base"
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        # 基础验证逻辑
        errors = []
        
        # 检查必需字段
        required_fields = self.schema_definition.get("required", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查字段类型
        properties = self.schema_definition.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in config:
                field_value = config[field_name]
                expected_type = field_schema.get("type")
                
                if expected_type and not self._check_type(field_value, expected_type):
                    errors.append(f"字段 {field_name} 类型错误，期望 {expected_type}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值类型
        
        Args:
            value: 值
            expected_type: 期望类型
            
        Returns:
            类型是否匹配
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)  # type: ignore[arg-type]
        
        return True  # 未知类型，默认通过
