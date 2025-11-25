"""统一配置管理器实现"""

import logging
import threading
from typing import Dict, Any, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.configuration import IValidationRule
from collections import defaultdict

from src.interfaces.configuration import (
    IConfigurationManager,
    IModuleConfigurator,
    IConfigurationValidator,
    IConfigurationExtensionPoint,
    IConfigurationExtension,
    ConfigurationContext,
    ConfigurationStatus,
    ValidationResult
)
from src.interfaces.container import IDependencyContainer

logger = logging.getLogger(__name__)


class ConfigurationManager(IConfigurationManager):
    """统一配置管理器实现"""
    
    def __init__(self, validator: Optional[IConfigurationValidator] = None):
        self._configurators: Dict[str, IModuleConfigurator] = {}
        self._extension_point = ConfigurationExtensionPoint()
        self._validator = validator
        self._configuration_status: Dict[str, ConfigurationStatus] = {}
        self._configured_modules: List[str] = []
        self._lock = threading.RLock()
        
        logger.debug("ConfigurationManager初始化完成")
    
    def register_configurator(self, module_name: str, configurator: IModuleConfigurator) -> None:
        """注册模块配置器"""
        with self._lock:
            if module_name in self._configurators:
                logger.warning(f"模块配置器已存在，将被覆盖: {module_name}")
            
            self._configurators[module_name] = configurator
            self._configuration_status[module_name] = ConfigurationStatus.NOT_CONFIGURED
            
            logger.debug(f"注册模块配置器: {module_name}")
    
    def unregister_configurator(self, module_name: str) -> None:
        """注销模块配置器"""
        with self._lock:
            if module_name in self._configurators:
                del self._configurators[module_name]
                if module_name in self._configuration_status:
                    del self._configuration_status[module_name]
                if module_name in self._configured_modules:
                    self._configured_modules.remove(module_name)
                
                logger.debug(f"注销模块配置器: {module_name}")
            else:
                logger.warning(f"模块配置器不存在: {module_name}")
    
    def configure_module(self, module_name: str, config: Dict[str, Any]) -> None:
        """配置单个模块"""
        with self._lock:
            configurator = self._configurators.get(module_name)
            if not configurator:
                raise ValueError(f"未找到模块配置器: {module_name}")
            
            try:
                self._configuration_status[module_name] = ConfigurationStatus.CONFIGURING
                
                # 验证配置
                validation_result = configurator.validate_config(config)
                if not validation_result.is_success():
                    self._configuration_status[module_name] = ConfigurationStatus.VALIDATION_FAILED
                    error_msg = f"模块 {module_name} 配置验证失败: {validation_result.errors}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # 检查依赖
                dependencies = configurator.get_dependencies()
                for dep in dependencies:
                    if dep not in self._configured_modules:
                        logger.warning(f"模块 {module_name} 依赖的模块 {dep} 尚未配置")
                
                # 创建配置上下文
                context = ConfigurationContext(
                    module_name=module_name,
                    config=config,
                    environment="default",  # 可以从配置中获取
                    dependencies={dep: self._get_module_config(dep) for dep in dependencies}
                )
                
                # 执行配置扩展
                self._extension_point.execute_extensions(context)
                
                # 执行配置（需要容器实例，这里暂时跳过）
                # configurator.configure(container, config)
                
                self._configuration_status[module_name] = ConfigurationStatus.CONFIGURED
                if module_name not in self._configured_modules:
                    self._configured_modules.append(module_name)
                
                logger.info(f"模块 {module_name} 配置完成")
                
            except Exception as e:
                self._configuration_status[module_name] = ConfigurationStatus.ERROR
                logger.error(f"配置模块 {module_name} 失败: {e}")
                raise
    
    def configure_all_modules(self, config: Dict[str, Any]) -> None:
        """配置所有模块"""
        with self._lock:
            # 按优先级排序配置器
            sorted_configurators = sorted(
                self._configurators.items(),
                key=lambda x: x[1].get_priority()
            )
            
            for module_name, configurator in sorted_configurators:
                module_config = config.get(module_name, {})
                if not module_config:
                    # 使用默认配置
                    module_config = configurator.get_default_config()
                    logger.info(f"使用默认配置配置模块: {module_name}")
                
                try:
                    self.configure_module(module_name, module_config)
                except Exception as e:
                    logger.error(f"配置模块 {module_name} 失败，停止配置流程: {e}")
                    raise
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置"""
        errors = []
        warnings = []
        
        with self._lock:
            for module_name, module_config in config.items():
                configurator = self._configurators.get(module_name)
                if not configurator:
                    errors.append(f"未找到模块配置器: {module_name}")
                    continue
                
                try:
                    result = configurator.validate_config(module_config)
                    errors.extend(result.errors)
                    warnings.extend(result.warnings)
                except Exception as e:
                    errors.append(f"验证模块 {module_name} 配置时发生异常: {e}")
            
            # 使用配置验证器进行额外验证
            if self._validator:
                try:
                    validator_result = self._validator.validate_configuration(config)
                    errors.extend(validator_result.errors)
                    warnings.extend(validator_result.warnings)
                except Exception as e:
                    errors.append(f"配置验证器执行异常: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def reload_configuration(self, module_name: str) -> None:
        """重新加载配置"""
        with self._lock:
            if module_name not in self._configurators:
                raise ValueError(f"未找到模块配置器: {module_name}")
            
            # 重置状态
            self._configuration_status[module_name] = ConfigurationStatus.NOT_CONFIGURED
            if module_name in self._configured_modules:
                self._configured_modules.remove(module_name)
            
            logger.info(f"模块 {module_name} 配置已重置，需要重新配置")
    
    def get_configuration_status(self) -> Dict[str, ConfigurationStatus]:
        """获取配置状态"""
        with self._lock:
            return self._configuration_status.copy()
    
    def get_module_configurator(self, module_name: str) -> Optional[IModuleConfigurator]:
        """获取模块配置器"""
        with self._lock:
            return self._configurators.get(module_name)
    
    def get_configured_modules(self) -> List[str]:
        """获取已配置的模块列表"""
        with self._lock:
            return self._configured_modules.copy()
    
    def _get_module_config(self, module_name: str) -> Dict[str, Any]:
        """获取模块配置（内部方法）"""
        configurator = self._configurators.get(module_name)
        if configurator:
            return configurator.get_default_config()
        return {}
    
    def register_extension(self, extension: IConfigurationExtension) -> None:
        """注册配置扩展"""
        self._extension_point.register_extension(extension)
    
    def unregister_extension(self, extension_name: str) -> None:
        """注销配置扩展"""
        self._extension_point.unregister_extension(extension_name)


class ConfigurationExtensionPoint(IConfigurationExtensionPoint):
    """配置扩展点实现"""
    
    def __init__(self) -> None:
        self._extensions: List[IConfigurationExtension] = []
        self._lock = threading.RLock()
    
    def register_extension(self, extension: IConfigurationExtension) -> None:
        """注册扩展"""
        with self._lock:
            # 检查是否已存在同名扩展
            for existing in self._extensions:
                if existing.get_extension_name() == extension.get_extension_name():
                    logger.warning(f"扩展已存在，将被覆盖: {extension.get_extension_name()}")
                    self._extensions.remove(existing)
                    break
            
            self._extensions.append(extension)
            # 按优先级排序
            self._extensions.sort(key=lambda x: x.get_extension_priority())
            
            logger.debug(f"注册配置扩展: {extension.get_extension_name()}")
    
    def unregister_extension(self, extension_name: str) -> None:
        """注销扩展"""
        with self._lock:
            for extension in self._extensions:
                if extension.get_extension_name() == extension_name:
                    self._extensions.remove(extension)
                    logger.debug(f"注销配置扩展: {extension_name}")
                    return
            
            logger.warning(f"扩展不存在: {extension_name}")
    
    def execute_extensions(self, context: ConfigurationContext) -> None:
        """执行所有扩展"""
        with self._lock:
            for extension in self._extensions:
                try:
                    extension.extend_configuration(context)
                    logger.debug(f"执行配置扩展: {extension.get_extension_name()}")
                except Exception as e:
                    logger.error(f"执行配置扩展 {extension.get_extension_name()} 失败: {e}")
    
    def get_registered_extensions(self) -> List[IConfigurationExtension]:
        """获取已注册的扩展"""
        with self._lock:
            return self._extensions.copy()


class SimpleConfigurationValidator(IConfigurationValidator):
    """简单配置验证器实现"""
    
    def __init__(self) -> None:
        self._rules: Dict[str, List[IValidationRule]] = {}
        self._lock = threading.RLock()
    
    def add_validation_rule(self, module_name: str, rule: IValidationRule) -> None:
        """添加验证规则"""
        with self._lock:
            if module_name not in self._rules:
                self._rules[module_name] = []
            
            # 检查是否已存在同名规则
            for existing in self._rules[module_name]:
                if existing.get_rule_name() == rule.get_rule_name():
                    logger.warning(f"验证规则已存在，将被覆盖: {module_name}.{rule.get_rule_name()}")
                    self._rules[module_name].remove(existing)
                    break
            
            self._rules[module_name].append(rule)
            logger.debug(f"添加验证规则: {module_name}.{rule.get_rule_name()}")
    
    def remove_validation_rule(self, module_name: str, rule_name: str) -> None:
        """移除验证规则"""
        with self._lock:
            if module_name in self._rules:
                for rule in self._rules[module_name]:
                    if rule.get_rule_name() == rule_name:
                        self._rules[module_name].remove(rule)
                        logger.debug(f"移除验证规则: {module_name}.{rule_name}")
                        return
                
                logger.warning(f"验证规则不存在: {module_name}.{rule_name}")
            else:
                logger.warning(f"模块没有验证规则: {module_name}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """验证完整配置"""
        errors = []
        warnings = []
        
        with self._lock:
            for module_name, module_config in config.items():
                if module_name in self._rules:
                    for rule in self._rules[module_name]:
                        try:
                            result = rule.validate(module_config)
                            errors.extend(result.errors)
                            warnings.extend(result.warnings)
                        except Exception as e:
                            errors.append(f"执行验证规则 {rule.get_rule_name()} 时发生异常: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_module_configuration(self, module_name: str, config: Dict[str, Any]) -> ValidationResult:
        """验证模块配置"""
        errors = []
        warnings = []
        
        with self._lock:
            if module_name in self._rules:
                for rule in self._rules[module_name]:
                    try:
                        result = rule.validate(config)
                        errors.extend(result.errors)
                        warnings.extend(result.warnings)
                    except Exception as e:
                        errors.append(f"执行验证规则 {rule.get_rule_name()} 时发生异常: {e}")
            else:
                warnings.append(f"模块 {module_name} 没有配置验证规则")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )