"""统一配置管理相关接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
from enum import Enum


class ConfigurationStatus(Enum):
    """配置状态枚举"""
    NOT_CONFIGURED = "not_configured"
    CONFIGURING = "configuring"
    CONFIGURED = "configured"
    VALIDATION_FAILED = "validation_failed"
    ERROR = "error"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def is_success(self) -> bool:
        return self.is_valid and len(self.errors) == 0


@dataclass
class ConfigurationContext:
    """配置上下文"""
    module_name: str
    config: Dict[str, Any]
    environment: str
    dependencies: Optional[Dict[str, Any]] = None
    
    def get_dependency(self, key: str, default: Any = None) -> Any:
        """获取依赖配置"""
        if self.dependencies is None:
            return default
        return self.dependencies.get(key, default)


class IValidationRule(ABC):
    """验证规则接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置"""
        pass
    
    @abstractmethod
    def get_rule_name(self) -> str:
        """获取规则名称"""
        pass


class IModuleConfigurator(ABC):
    """模块配置器接口"""
    
    @abstractmethod
    def configure(self, container: 'IDependencyContainer', config: Dict[str, Any]) -> None:
        """配置模块服务"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置"""
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """获取依赖的模块列表"""
        pass
    
    def get_priority(self) -> int:
        """获取配置优先级，数字越小优先级越高"""
        return 0
    
    def get_module_name(self) -> str:
        """获取模块名称"""
        return self.__class__.__name__.replace('Configurator', '').lower()


class IConfigurationValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def add_validation_rule(self, module_name: str, rule: IValidationRule) -> None:
        """添加验证规则"""
        pass
    
    @abstractmethod
    def remove_validation_rule(self, module_name: str, rule_name: str) -> None:
        """移除验证规则"""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """验证完整配置"""
        pass
    
    @abstractmethod
    def validate_module_configuration(self, module_name: str, config: Dict[str, Any]) -> ValidationResult:
        """验证模块配置"""
        pass


class IConfigurationTemplate(ABC):
    """配置模板接口"""
    
    @abstractmethod
    def get_template_name(self) -> str:
        """获取模板名称"""
        pass
    
    @abstractmethod
    def get_template_content(self) -> Dict[str, Any]:
        """获取模板内容"""
        pass
    
    @abstractmethod
    def render(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """渲染模板"""
        pass
    
    @abstractmethod
    def validate_template(self) -> ValidationResult:
        """验证模板格式"""
        pass


class IConfigurationManager(ABC):
    """统一配置管理器接口"""
    
    @abstractmethod
    def register_configurator(self, module_name: str, configurator: IModuleConfigurator) -> None:
        """注册模块配置器"""
        pass
    
    @abstractmethod
    def unregister_configurator(self, module_name: str) -> None:
        """注销模块配置器"""
        pass
    
    @abstractmethod
    def configure_module(self, module_name: str, config: Dict[str, Any]) -> None:
        """配置单个模块"""
        pass
    
    @abstractmethod
    def configure_all_modules(self, config: Dict[str, Any]) -> None:
        """配置所有模块"""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置"""
        pass
    
    @abstractmethod
    def reload_configuration(self, module_name: str) -> None:
        """重新加载配置"""
        pass
    
    @abstractmethod
    def get_configuration_status(self) -> Dict[str, ConfigurationStatus]:
        """获取配置状态"""
        pass
    
    @abstractmethod
    def get_module_configurator(self, module_name: str) -> Optional[IModuleConfigurator]:
        """获取模块配置器"""
        pass
    
    @abstractmethod
    def get_configured_modules(self) -> List[str]:
        """获取已配置的模块列表"""
        pass


class IConfigurationExtension(ABC):
    """配置扩展接口"""
    
    @abstractmethod
    def get_extension_name(self) -> str:
        """获取扩展名称"""
        pass
    
    @abstractmethod
    def extend_configuration(self, context: ConfigurationContext) -> None:
        """扩展配置"""
        pass
    
    def get_extension_priority(self) -> int:
        """获取扩展优先级"""
        return 0


class IConfigurationExtensionPoint(ABC):
    """配置扩展点接口"""
    
    @abstractmethod
    def register_extension(self, extension: IConfigurationExtension) -> None:
        """注册扩展"""
        pass
    
    @abstractmethod
    def unregister_extension(self, extension_name: str) -> None:
        """注销扩展"""
        pass
    
    @abstractmethod
    def execute_extensions(self, context: ConfigurationContext) -> None:
        """执行所有扩展"""
        pass
    
    @abstractmethod
    def get_registered_extensions(self) -> List[IConfigurationExtension]:
        """获取已注册的扩展"""
        pass


# 避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.interfaces.container import IDependencyContainer