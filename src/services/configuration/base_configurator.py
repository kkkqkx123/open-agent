"""模块配置器基类实现"""

import logging
from typing import Dict, Any, List, Optional, Type, Callable
from abc import ABC, abstractmethod

from src.interfaces.configuration import (
    IModuleConfigurator,
    ValidationResult,
    ConfigurationContext
)
from src.interfaces.container import IDependencyContainer

logger = logging.getLogger(__name__)


class BaseModuleConfigurator(IModuleConfigurator):
    """模块配置器基类"""
    
    def __init__(self, module_name: Optional[str] = None):
        self._module_name = module_name or self.get_module_name()
        self._default_config: Optional[Dict[str, Any]] = None
        self._dependencies: List[str] = []
        self._priority = 0
    
    def configure(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置模块服务"""
        try:
            # 验证和合并配置
            validated_config = self.validate_and_merge_config(config)
            
            # 检查功能启用状态
            if not validated_config.get("enabled", True):
                logger.info(f"{self._module_name}功能已禁用")
                return
            
            # 执行具体配置
            self._configure_services(container, validated_config)
            
            logger.info(f"{self._module_name}服务配置完成")
            
        except Exception as e:
            logger.error(f"配置{self._module_name}服务失败: {e}")
            raise
    
    def validate_and_merge_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """验证和合并配置"""
        default_config = self.get_default_config()
        if config is None:
            return default_config
        
        # 合并配置
        merged_config = {**default_config, **config}
        
        # 验证配置
        validation_result = self.validate_config(merged_config)
        if not validation_result.is_success():
            error_msg = f"配置验证失败: {validation_result.errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 输出警告
        if validation_result.warnings:
            for warning in validation_result.warnings:
                logger.warning(f"配置警告: {warning}")
        
        return merged_config
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置"""
        errors = []
        warnings = []
        
        try:
            # 基础验证
            if not isinstance(config, dict):
                errors.append("配置必须是字典类型")
                return ValidationResult(False, errors, warnings)
            
            # 检查必需字段
            required_fields = self.get_required_fields()
            for field in required_fields:
                if field not in config:
                    errors.append(f"缺少必需字段: {field}")
            
            # 检查字段类型
            field_types = self.get_field_types()
            for field, expected_type in field_types.items():
                if field in config and not isinstance(config[field], expected_type):
                    errors.append(f"字段 {field} 类型错误，期望 {expected_type.__name__}")
            
            # 执行自定义验证
            custom_result = self._validate_custom(config)
            errors.extend(custom_result.errors)
            warnings.extend(custom_result.warnings)
            
        except Exception as e:
            errors.append(f"配置验证异常: {e}")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        if self._default_config is None:
            self._default_config = self._create_default_config()
        return self._default_config.copy()
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的模块列表"""
        return self._dependencies.copy()
    
    def get_priority(self) -> int:
        """获取配置优先级"""
        return self._priority
    
    def get_module_name(self) -> str:
        """获取模块名称"""
        return self._module_name
    
    def add_dependency(self, module_name: str) -> None:
        """添加依赖模块"""
        if module_name not in self._dependencies:
            self._dependencies.append(module_name)
    
    def set_priority(self, priority: int) -> None:
        """设置优先级"""
        self._priority = priority
    
    @abstractmethod
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置服务的具体实现（子类必须实现）"""
        pass
    
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置（子类可以重写）"""
        return {
            "enabled": True,
            "version": "1.0.0"
        }
    
    def get_required_fields(self) -> List[str]:
        """获取必需字段列表（子类可以重写）"""
        return []
    
    def get_field_types(self) -> Dict[str, Type]:
        """获取字段类型映射（子类可以重写）"""
        return {}
    
    def _validate_custom(self, config: Dict[str, Any]) -> ValidationResult:
        """自定义验证逻辑（子类可以重写）"""
        return ValidationResult(True, [], [])


class SimpleModuleConfigurator(BaseModuleConfigurator):
    """简单模块配置器实现"""
    
    def __init__(self, module_name: str, service_registrations: List[Dict[str, Any]]):
        super().__init__(module_name)
        self._service_registrations = service_registrations
    
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置服务"""
        for registration in self._service_registrations:
            interface = registration.get("interface")
            implementation = registration.get("implementation")
            factory = registration.get("factory")
            lifetime = registration.get("lifetime", "singleton")
            
            if interface and implementation:
                container.register(interface, implementation, lifetime=lifetime)
            elif interface and factory:
                container.register_factory(interface, factory, lifetime=lifetime)
            else:
                logger.warning(f"无效的服务注册配置: {registration}")


class ConditionalModuleConfigurator(BaseModuleConfigurator):
    """条件模块配置器实现"""
    
    def __init__(self, module_name: str, condition_func: Callable[[Dict[str, Any]], bool], child_configurator: IModuleConfigurator):
        super().__init__(module_name)
        self._condition_func = condition_func
        self._child_configurator = child_configurator
    
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """根据条件配置服务"""
        if self._condition_func(config):
            logger.info(f"条件满足，配置模块: {self._module_name}")
            self._child_configurator.configure(container, config)
        else:
            logger.info(f"条件不满足，跳过模块配置: {self._module_name}")
    
    def get_default_config(self) -> Dict[str, Any]:
        return self._child_configurator.get_default_config()
    
    def get_dependencies(self) -> List[str]:
        return self._child_configurator.get_dependencies()
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        return self._child_configurator.validate_config(config)


class CompositeModuleConfigurator(BaseModuleConfigurator):
    """复合模块配置器实现"""
    
    def __init__(self, module_name: str, child_configurators: List[IModuleConfigurator]):
        super().__init__(module_name)
        self._child_configurators = child_configurators
    
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """配置所有子配置器"""
        for configurator in self._child_configurators:
            try:
                configurator.configure(container, config)
            except Exception as e:
                logger.error(f"子配置器 {configurator.get_module_name()} 配置失败: {e}")
                raise
    
    def get_default_config(self) -> Dict[str, Any]:
        # 合并所有子配置器的默认配置
        merged_config = {}
        for configurator in self._child_configurators:
            child_config = configurator.get_default_config()
            merged_config.update(child_config)
        return merged_config
    
    def get_dependencies(self) -> List[str]:
        # 合并所有子配置器的依赖
        all_dependencies = []
        for configurator in self._child_configurators:
            all_dependencies.extend(configurator.get_dependencies())
        return list(set(all_dependencies))  # 去重
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        # 验证所有子配置器
        all_errors = []
        all_warnings = []
        
        for configurator in self._child_configurators:
            result = configurator.validate_config(config)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return ValidationResult(len(all_errors) == 0, all_errors, all_warnings)


class ConfigurableModuleConfigurator(BaseModuleConfigurator):
    """可配置模块配置器实现"""
    
    def __init__(self, module_name: str):
        super().__init__(module_name)
        self._config_sections: Dict[str, Callable[[IDependencyContainer, Dict[str, Any]], None]] = {}
    
    def add_config_section(self, section_name: str, config_func: Callable[[IDependencyContainer, Dict[str, Any]], None]) -> None:
        """添加配置段"""
        self._config_sections[section_name] = config_func
    
    def _configure_services(self, container: IDependencyContainer, config: Dict[str, Any]) -> None:
        """按配置段配置服务"""
        for section_name, config_func in self._config_sections.items():
            section_config = config.get(section_name, {})
            try:
                config_func(container, section_config)
                logger.debug(f"配置段 {section_name} 完成")
            except Exception as e:
                logger.error(f"配置段 {section_name} 失败: {e}")
                raise