"""
统一配置管理器 - 支持所有模块的配置管理

基于统一配置系统设计，提供模块化、可扩展的配置管理解决方案。
"""

from pathlib import Path
from typing import Dict, Any, Optional, TypeVar, List

import logging
from src.interfaces.config import (
    IConfigLoader, IConfigValidator, IConfigManager,
    IConfigInheritanceHandler, IModuleConfigRegistry, IConfigMapperRegistry,
    ICrossModuleResolver, IModuleConfigLoader, ModuleConfig
)
from src.infrastructure.validation.result import ValidationResult
from src.interfaces.config import (
    ConfigError,
    ConfigurationLoadError as ConfigNotFoundError,
    ConfigurationValidationError as ConfigValidationError
)
from src.infrastructure.config.impl.base_impl import ConfigProcessorChain
from src.infrastructure.config.validation.base_validator import GenericConfigValidator
from src.interfaces.config.mapper import IConfigMapper

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Any)


class ConfigManager(IConfigManager):
    """统一配置管理器 - 支持所有模块的配置管理"""
    
    def __init__(self,
                 config_loader: IConfigLoader,
                 processor_chain: Optional[ConfigProcessorChain] = None,
                 validator_registry: Optional[IConfigValidator] = None,
                 module_registry: Optional[IModuleConfigRegistry] = None,
                 mapper_registry: Optional[IConfigMapperRegistry] = None,
                 cross_module_resolver: Optional[ICrossModuleResolver] = None,
                 base_path: Optional[Path] = None,
                 inheritance_handler: Optional[IConfigInheritanceHandler] = None):
        """初始化统一配置管理器
        
        Args:
            config_loader: 配置加载器（通过依赖注入）
            processor_chain: 配置处理器链（可选）
            validator_registry: 验证器注册表（可选）
            module_registry: 模块配置注册表（可选）
            mapper_registry: 配置映射器注册表（可选）
            cross_module_resolver: 跨模块引用解析器（可选）
            base_path: 配置文件基础路径（可选）
            inheritance_handler: 继承处理器（可选）
        """
        self.base_path = base_path or Path("configs")
        
        # 通过依赖注入使用配置加载器
        self.loader = config_loader
        
        # 初始化处理器链（如果未提供则创建默认的）
        if processor_chain is None:
            self.processor_chain = ConfigProcessorChain()
        else:
            self.processor_chain = processor_chain
        
        # 继承处理器（用于工作流配置等）
        self._inheritance_handler = inheritance_handler
        
        # 模块特定验证器注册表
        self._module_validators: Dict[str, IConfigValidator] = {}
        
        # 默认验证器
        self._default_validator = GenericConfigValidator(name="DefaultValidator")
        
        # 统一配置系统组件
        self.validator_registry = validator_registry
        self.module_registry = module_registry or ModuleConfigRegistry()
        self.mapper_registry = mapper_registry or ConfigMapperRegistry()
        self.cross_module_resolver = cross_module_resolver or CrossModuleResolver(self)
        
        # 模块特定加载器
        self._module_loaders: Dict[str, IModuleConfigLoader] = {}
        
        logger.info("统一配置管理器初始化完成")
    
    def load_config(self, config_path: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置 - 支持模块特定处理
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型（可选）
            
        Returns:
            配置数据
        """
        try:
            # 1. 加载原始配置
            logger.debug(f"加载配置文件: {config_path}")
            if module_type and module_type in self._module_loaders:
                raw_config = self._module_loaders[module_type].load(config_path)
            else:
                raw_config = self.loader.load(config_path)
            
            # 2. 获取模块特定的处理器链
            processor_chain = self._get_processor_chain(module_type)
            
            # 3. 处理配置
            logger.debug(f"处理配置: {config_path}")
            processed_config = processor_chain.process(raw_config, config_path)
            
            # 4. 解析跨模块引用
            if module_type and self.cross_module_resolver:
                logger.debug(f"解析跨模块引用: {config_path}")
                processed_config = self.cross_module_resolver.resolve(module_type, processed_config)
            
            # 5. 获取模块特定的验证器
            validator = self._get_validator(module_type)
            logger.debug(f"验证配置: {config_path}")
            validation_result = validator.validate(processed_config)
            
            if not validation_result.is_valid:
                error_msg = f"配置验证失败 {config_path}: " + "; ".join(validation_result.errors)
                logger.error(error_msg)
                raise ConfigValidationError(error_msg)
            
            # 6. 应用模块特定的后处理
            if module_type and self.module_registry:
                logger.debug(f"应用模块后处理: {config_path}")
                processed_config = self.module_registry.post_process(module_type, processed_config)
            
            logger.info(f"配置加载成功: {config_path}")
            return processed_config
            
        except ConfigNotFoundError:
            raise
        except Exception as e:
            logger.error(f"配置加载失败 {config_path}: {e}")
            if isinstance(e, (ConfigError, ConfigValidationError)):
                raise
            raise ConfigError(f"配置加载失败: {e}") from e
    
    def load_config_with_module(self, config_path: str, module_type: str) -> Dict[str, Any]:
        """加载模块特定配置
        
        Args:
            config_path: 配置文件路径
            module_type: 模块类型
            
        Returns:
            配置数据
        """
        return self.load_config(config_path, module_type=module_type)
    
    def save_config(self, config: Dict[str, Any], config_path: str) -> None:
        """保存配置文件
        
        Args:
            config: 配置数据
            config_path: 配置文件路径
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "save_config is not implemented in core layer. Use services layer."
        )
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "get_config is not implemented in core layer. Use services layer."
        )
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "set_config is not implemented in core layer. Use services layer."
        )
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        # 使用验证器验证配置，返回ValidationResult
        validation_result = self._default_validator.validate(config)
        
        # 确保返回的是ValidationResult类型
        if isinstance(validation_result, ValidationResult):
            return validation_result
        
        # 如果返回其他类型，转换为ValidationResult
        return ValidationResult(
            is_valid=getattr(validation_result, 'is_valid', True),
            errors=getattr(validation_result, 'errors', []),
            warnings=getattr(validation_result, 'warnings', []),
            info=getattr(validation_result, 'info', []),
            metadata=getattr(validation_result, 'metadata', {})
        )
    
    def register_module_validator(self, module_type: str, validator: IConfigValidator) -> None:
        """注册模块特定验证器
        
        Args:
            module_type: 模块类型
            validator: 验证器
        """
        self._module_validators[module_type] = validator
        logger.info(f"已注册模块验证器: {module_type}")
    
    def register_module_config(self, module_type: str, config: ModuleConfig) -> None:
        """注册模块配置
        
        Args:
            module_type: 模块类型
            config: 模块配置
        """
        if self.module_registry:
            self.module_registry.register_module(module_type, config)
            # 注记：处理器和验证器通过名称存储，具体创建延迟到使用时进行
            # config.processors 是处理器名称列表，config.validator 是验证器名称
            # 实际的处理器对象应通过工厂或容器模式创建
        logger.info(f"已注册模块配置: {module_type}")
    
    def register_module_loader(self, module_type: str, loader: IModuleConfigLoader) -> None:
        """注册模块特定加载器
        
        Args:
            module_type: 模块类型
            loader: 模块加载器
        """
        self._module_loaders[module_type] = loader
        logger.info(f"已注册模块加载器: {module_type}")
    
    def _get_processor_chain(self, module_type: Optional[str]) -> ConfigProcessorChain:
        """获取模块特定的处理器链
        
        Args:
            module_type: 模块类型
            
        Returns:
            ConfigProcessorChain: 处理器链
        """
        # 简化实现，实际应该根据模块类型返回特定的处理器链
        return self.processor_chain
    
    def get_module_config(self, module_type: str) -> Dict[str, Any]:
        """获取模块配置
        
        Args:
            module_type: 模块类型
            
        Returns:
            模块配置
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "get_module_config is not implemented in core layer. Use services layer."
        )
    
    def reload_module_configs(self, module_type: str) -> None:
        """重新加载模块配置
        
        Args:
            module_type: 模块类型
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "reload_module_configs is not implemented in core layer. Use services layer."
        )
    
    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            重新加载的配置数据
        """
        # 基础实现，直接重新加载
        return self.load_config(config_path)
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径，如果为None则清除所有缓存
        """
        # 基础实现，不包含高级功能
        raise NotImplementedError(
            "invalidate_cache is not implemented in core layer. Use services layer."
        )
    
    def _get_validator(self, module_type: Optional[str]) -> IConfigValidator:
        """获取模块特定的验证器
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置验证器
        """
        if module_type and module_type in self._module_validators:
            return self._module_validators[module_type]
        
        # 返回默认验证器
        return self._default_validator

    def list_config_files(self, config_directory: str) -> List[str]:
        """列出指定目录下的配置文件
        
        Args:
            config_directory: 配置目录路径
            
        Returns:
            配置文件路径列表
        """
        try:
            # 构建完整路径
            full_path = self.base_path / config_directory
            
            if not full_path.exists():
                logger.warning(f"配置目录不存在: {full_path}")
                return []
            
            # 支持的配置文件扩展名
            supported_extensions = {'.yaml', '.yml', '.json'}
            config_files = []
            
            # 遍历目录，查找配置文件
            for ext in supported_extensions:
                for file_path in full_path.glob(f"*{ext}"):
                    if file_path.is_file():
                        # 返回相对于配置目录的路径
                        relative_path = file_path.relative_to(full_path)
                        config_files.append(str(relative_path))
            
            logger.debug(f"在目录 {config_directory} 中找到 {len(config_files)} 个配置文件")
            return config_files
            
        except Exception as e:
            logger.error(f"列出配置文件失败 {config_directory}: {e}")
            return []

class ModuleConfigRegistry(IModuleConfigRegistry):
    """模块配置注册表实现"""
    
    def __init__(self) -> None:
        self._modules: Dict[str, ModuleConfig] = {}
        self._cross_module_resolvers: List[ICrossModuleResolver] = []
    
    def register_module(self, module_type: str, config: ModuleConfig) -> None:
        """注册模块配置"""
        self._modules[module_type] = config
    
    def get_module_config(self, module_type: str) -> Optional[ModuleConfig]:
        """获取模块配置"""
        return self._modules.get(module_type)
    
    def post_process(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """模块特定后处理"""
        module_config = self._modules.get(module_type)
        if module_config and module_config.post_processor:
            return module_config.post_processor(config)
        return config


class ConfigMapperRegistry(IConfigMapperRegistry):
    """配置映射器注册表实现"""
    
    def __init__(self) -> None:
        self._mappers: Dict[str, IConfigMapper] = {}
    
    def register_mapper(self, module_type: str, mapper: IConfigMapper) -> None:
        """注册配置映射器"""
        self._mappers[module_type] = mapper
    
    def get_mapper(self, module_type: str) -> Optional[IConfigMapper]:
        """获取配置映射器"""
        return self._mappers.get(module_type)
    
    def dict_to_entity(self, module_type: str, config_data: Dict[str, Any]) -> Any:
        """将配置字典转换为业务实体"""
        mapper = self.get_mapper(module_type)
        if not mapper:
            raise ValueError(f"未找到模块 {module_type} 的配置映射器")
        return mapper.dict_to_entity(config_data)
    
    def entity_to_dict(self, module_type: str, entity: Any) -> Dict[str, Any]:
        """将业务实体转换为配置字典"""
        mapper = self.get_mapper(module_type)
        if not mapper:
            raise ValueError(f"未找到模块 {module_type} 的配置映射器")
        return mapper.entity_to_dict(entity)


class CrossModuleResolver(ICrossModuleResolver):
    """跨模块引用解析器实现"""
    
    def __init__(self, config_manager: IConfigManager):
        self.config_manager = config_manager
    
    def resolve(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析跨模块引用"""
        import re
        import json
        
        def replace_reference(match: re.Match) -> str:
            ref_module = match.group(1)
            ref_path = match.group(2)
            
            # 加载引用的配置
            ref_config = self.config_manager.load_config(ref_path, ref_module)
            
            # 获取引用值
            keys = ref_path.split('.')
            value = ref_config
            for key in keys:
                value = value.get(key, {})
            
            return str(value)
        
        # 递归解析所有引用
        pattern = r'\$\{([^\.]+)\.([^}]+)\}'
        config_str = json.dumps(config)
        
        while re.search(pattern, config_str):
            config_str = re.sub(pattern, replace_reference, config_str)
        
        result = json.loads(config_str)
        if isinstance(result, dict):
            return result
        else:
            # 如果解析结果不是字典，返回空字典
            logger.warning(f"配置解析结果不是字典类型: {type(result)}")
            return {}
