"""配置验证器接口定义

支持新的验证架构，包括验证上下文、验证报告和增强功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Protocol
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from ..common_domain import ValidationResult


class ValidationSeverity(Enum):
    """验证严重程度枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationLevel(Enum):
    """验证级别枚举"""
    SYNTAX = "syntax"           # 语法验证：YAML/JSON格式
    SCHEMA = "schema"           # 模式验证：数据结构
    SEMANTIC = "semantic"       # 语义验证：业务逻辑
    DEPENDENCY = "dependency"   # 依赖验证：外部依赖
    PERFORMANCE = "performance" # 性能验证：性能指标


@dataclass
class ValidationContext:
    """验证上下文
    
    提供验证过程中需要的上下文信息。
    """
    config_type: str
    config_path: Optional[str] = None
    operation_id: Optional[str] = None
    strict_mode: bool = False
    enable_business_rules: bool = True
    enable_cross_module_validation: bool = True
    environment: str = "development"
    enable_cache: bool = True
    cache_key: Optional[str] = None
    dependent_configs: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.dependent_configs is None:
            self.dependent_configs = {}
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


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
    
    def validate(self, config: Dict[str, Any], context: ValidationContext) -> ValidationResult:
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
                       context: ValidationContext) -> ValidationResult:
        """使用所有适用的规则验证配置"""
        ...


class IBusinessValidator(Protocol):
    """业务验证器接口"""
    
    def validate(self, config: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """执行业务验证"""
        ...


class ConfigValidationResult(ValidationResult):
    """配置验证结果 - 扩展通用验证结果"""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None, info: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        super().__init__(is_valid=is_valid, errors=errors or [],
                        warnings=warnings or [], metadata=metadata or {})
        self.info = info or []
    
    def add_info(self, message: str) -> None:
        """添加信息"""
        self.info.append(message)
    
    def merge(self, other: 'ConfigValidationResult') -> None:
        """合并另一个验证结果"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        if not other.is_valid:
            self.is_valid = False
    
    def has_messages(self, severity: ValidationSeverity) -> bool:
        """检查是否有指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return len(self.errors) > 0
        elif severity == ValidationSeverity.WARNING:
            return len(self.warnings) > 0
        elif severity == ValidationSeverity.INFO:
            return len(self.info) > 0
        return False
    
    def get_messages(self, severity: ValidationSeverity) -> List[str]:
        """获取指定严重程度的消息"""
        if severity == ValidationSeverity.ERROR:
            return self.errors
        elif severity == ValidationSeverity.WARNING:
            return self.warnings
        elif severity == ValidationSeverity.INFO:
            return self.info
        return []


class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
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


class IEnhancedConfigValidator(IConfigValidator):
    """增强配置验证器接口
    
    提供更高级的验证功能，包括上下文验证和报告生成。
    """
    
    def validate_with_context(self,
                            config: Dict[str, Any],
                            context: ValidationContext) -> ValidationResult:
        """带上下文的验证
        
        Args:
            config: 配置数据
            context: 验证上下文
            
        Returns:
            验证结果
        """
        # 默认实现，子类可以重写
        return self.validate(config)
    
    def validate_with_report(self,
                           config: Dict[str, Any],
                           context: Optional[ValidationContext] = None) -> Tuple[ValidationResult, IValidationReport]:
        """验证配置并生成详细报告
        
        Args:
            config: 配置数据
            context: 验证上下文
            
        Returns:
            验证结果和验证报告的元组
        """
        # 默认实现，子类应该重写
        if context is None:
            context = ValidationContext(config_type="unknown")
        
        result = self.validate_with_context(config, context)
        
        # 创建简单报告
        from ..common_domain import BaseContext
        simple_report = type('SimpleValidationReport', (), {
            'config_type': context.config_type,
            'config_path': context.config_path or "",
            'timestamp': datetime.now(),
            'is_valid': lambda min_severity=ValidationSeverity.ERROR: result.is_valid,
            'get_fix_suggestions': lambda: []
        })()
        
        return result, simple_report
    
    def validate_file(self,
                     config_path: str,
                     context: Optional[ValidationContext] = None) -> Tuple[ValidationResult, IValidationReport]:
        """验证配置文件
        
        Args:
            config_path: 配置文件路径
            context: 验证上下文
            
        Returns:
            验证结果和验证报告的元组
        """
        # 默认实现，子类应该重写
        raise NotImplementedError("子类必须实现 validate_file 方法")


class IConfigValidationService(Protocol):
    """配置验证服务接口"""
    
    def validate_config_complete(self,
                               config_type: str,
                               config: Dict[str, Any],
                               context: Optional[ValidationContext] = None) -> Tuple[ValidationResult, IValidationReport]:
        """完整验证配置"""
        ...
    
    def validate_config_file(self,
                           config_path: str,
                           config_type: str,
                           context: Optional[ValidationContext] = None) -> Tuple[ValidationResult, IValidationReport]:
        """验证配置文件"""
        ...
    
    def get_supported_config_types(self) -> List[str]:
        """获取支持的配置类型"""
        ...