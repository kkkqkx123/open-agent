"""配置验证接口与框架定义

包含验证相关的枚举、异常、协议和基础类型定义。
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Protocol, Tuple, Callable
from datetime import datetime
from abc import ABC, abstractmethod
from typing import runtime_checkable

# 从通用领域接口导入IValidationResult
from ..common_domain import IValidationResult


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


class IValidationContext(Protocol):
    """验证上下文接口"""
    
    @property
    def config_type(self) -> str:
        """配置类型"""
        ...
    
    @property
    def config_path(self) -> Optional[str]:
        """配置路径"""
        ...
    
    @property
    def operation_id(self) -> Optional[str]:
        """操作ID"""
        ...
    
    @property
    def strict_mode(self) -> bool:
        """严格模式"""
        ...
    
    @property
    def enable_business_rules(self) -> bool:
        """是否启用业务规则"""
        ...
    
    @property
    def enable_cross_module_validation(self) -> bool:
        """是否启用跨模块验证"""
        ...
    
    @property
    def environment(self) -> str:
        """环境"""
        ...
    
    @property
    def dependent_configs(self) -> Dict[str, Any]:
        """依赖配置"""
        ...
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        ...
    
    @property
    def created_at(self) -> datetime:
        """创建时间"""
        ...
    
    @property
    def validation_history(self) -> List[Dict[str, Any]]:
        """验证历史"""
        ...
    
    def add_dependency(self, config_type: str, config_data: Dict[str, Any]) -> None:
        """添加依赖配置"""
        ...
    
    def get_dependency(self, config_type: str) -> Optional[Dict[str, Any]]:
        """获取依赖配置"""
        ...
    
    def add_metadata(self, key: str, value: Any) -> None:
        """添加元数据"""
        ...
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        ...
    
    def add_validation_step(self, step_name: str, result: Dict[str, Any]) -> None:
        """添加验证步骤记录"""
        ...


class IValidationReport(Protocol):
    """验证报告接口"""
    
    @property
    def config_type(self) -> str:
        """配置类型"""
        ...
    
    @property
    def config_path(self) -> str:
        """配置路径"""
        ...
    
    @property
    def timestamp(self) -> datetime:
        """时间戳"""
        ...
    
    def is_valid(self, min_severity: ValidationSeverity = ValidationSeverity.ERROR) -> bool:
        """检查配置是否有效"""
        ...
    
    def get_fix_suggestions(self) -> List[Any]:
        """获取修复建议"""
        ...


@runtime_checkable
class IValidationRule(Protocol):
    """验证规则接口"""
    
    @property
    def rule_id(self) -> str:
        """规则ID"""
        ...
    
    @property
    def config_type(self) -> str:
        """适用的配置类型"""
        ...
    
    @property
    def priority(self) -> int:
        """优先级"""
        ...
    
    def validate(self, config: Dict[str, Any], context: IValidationContext) -> IValidationResult:
        """执行验证"""
        ...


class IValidationRuleRegistry(Protocol):
    """验证规则注册表接口"""
    
    def register_rule(self, rule: IValidationRule) -> None:
        """注册验证规则"""
        ...
    
    def get_rules(self, config_type: str) -> List[IValidationRule]:
        """获取指定配置类型的所有规则"""
        ...
    
    def validate_config(self, config_type: str, config: Dict[str, Any],
                       context: IValidationContext) -> IValidationResult:
        """使用所有适用的规则验证配置"""
        ...


class IBusinessValidator(Protocol):
    """业务验证器接口"""
    
    def validate(self, config: Dict[str, Any], context: IValidationContext) -> IValidationResult:
        """执行业务验证"""
        ...


class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def supports_module_type(self, module_type: str) -> bool:
        """检查是否支持指定模块类型
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否支持
        """
        pass


class IConfigValidationService(Protocol):
    """配置验证服务接口"""
    
    def validate_config_complete(self,
                                config_type: str,
                                config: Dict[str, Any],
                                context: Optional[IValidationContext] = None) -> Tuple[IValidationResult, IValidationReport]:
        """完整验证配置"""
        ...
    
    def validate_config_file(self,
                           config_path: str,
                           config_type: str,
                           context: Optional[IValidationContext] = None) -> Tuple[IValidationResult, IValidationReport]:
        """验证配置文件"""
        ...
    
    def get_supported_config_types(self) -> List[str]:
        """获取支持的配置类型"""
        ...


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


