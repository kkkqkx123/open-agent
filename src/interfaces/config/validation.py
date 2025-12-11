"""配置验证接口与框架定义

包含验证相关的枚举、异常、协议和基础类型定义。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime


class ValidationLevel(Enum):
    """验证级别"""
    SYNTAX = "syntax"           # 语法验证：YAML/JSON格式
    SCHEMA = "schema"           # 模式验证：数据结构
    SEMANTIC = "semantic"       # 语义验证：业务逻辑
    DEPENDENCY = "dependency"   # 依赖验证：外部依赖
    PERFORMANCE = "performance" # 性能验证：性能指标


class ValidationSeverity(Enum):
    """验证严重性级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IFixSuggestion(Protocol):
    """修复建议接口"""
    
    @property
    def description(self) -> str:
        """修复描述"""
        ...
    
    @property
    def auto_fixable(self) -> bool:
        """是否可自动修复"""
        ...
    
    def apply_fix(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用修复
        
        Args:
            config: 原始配置
            
        Returns:
            修复后的配置
        """
        ...


@dataclass
class FixSuggestion:
    """修复建议实现"""
    description: str
    auto_fixable: bool = False
    fix_func: Optional[callable] = None
    
    def apply_fix(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用修复"""
        if self.fix_func:
            return self.fix_func(config)
        return config
