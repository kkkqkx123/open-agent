"""配置实现基类

定义配置实现的基础接口和抽象类，提供配置加载、处理和转换的通用框架。
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from src.interfaces.config import IConfigLoader, IConfigProcessor
from src.infrastructure.validation.result import ValidationResult
from src.interfaces.common_domain import IValidationResult
from src.interfaces.config.schema import ISchemaGenerator, IConfigSchema
from src.interfaces.config.impl import IConfigImpl
from .shared import CacheManager, DiscoveryManager

logger = logging.getLogger(__name__)


class BaseConfigImpl(IConfigImpl):
    """配置实现基类
     
    提供配置加载、处理和转换的通用流程。
    """
     
    def __init__(self,
                  module_type: str,
                  config_loader: IConfigLoader,
                  processor_chain: 'ConfigProcessorChain',
                  schema: 'IConfigSchema'):
        """初始化配置实现
        
        Args:
            module_type: 模块类型
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        self.module_type = module_type
        self.config_loader = config_loader
        self.processor_chain = processor_chain
        self.schema = schema
        self._base_path = Path("configs")
        
        # 整合的共享组件
        self.cache_manager = CacheManager()
        self.discovery_manager = DiscoveryManager(config_loader)
        
        logger.debug(f"初始化{module_type}模块配置实现")
    
    def load_config(self, config_path: str, use_cache: bool = True) -> Dict[str, Any]:
        """加载配置的通用流程
        
        Args:
            config_path: 配置文件路径
            use_cache: 是否使用缓存
            
        Returns:
            处理后的配置数据
        """
        logger.debug(f"开始加载{self.module_type}模块配置: {config_path}")
        
        try:
            # 1. 检查缓存
            cache_key = f"{self.module_type}:{config_path}"
            if use_cache:
                cached_config = self.cache_manager.get(cache_key)
                if cached_config is not None:
                    logger.debug(f"从缓存加载{self.module_type}模块配置: {config_path}")
                    if isinstance(cached_config, dict):
                        return cached_config
                    else:
                        logger.warning(f"缓存中的配置不是字典类型，重新加载: {cache_key}")
            
            # 2. 加载原始配置
            logger.debug(f"加载原始配置文件: {config_path}")
            raw_config = self.config_loader.load(config_path)
            
            # 3. 应用处理器链（包含所有通用处理）
            logger.debug(f"应用处理器链处理配置")
            processed_config = self.processor_chain.process(raw_config, config_path)
            
            # 4. 应用模块特定转换
            logger.debug(f"转换为{self.module_type}模块特定格式")
            final_config = self.transform_config(processed_config)
            
            # 5. 验证配置
            logger.debug(f"验证配置数据")
            validation_result = self.validate_config(final_config)
            
            if not validation_result.is_valid:
                error_msg = f"{self.module_type}模块配置验证失败: " + "; ".join(validation_result.errors)
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 6. 缓存结果
            if use_cache:
                self.cache_manager.set(cache_key, final_config)
            
            logger.info(f"{self.module_type}模块配置加载成功: {config_path}")
            return final_config
            
        except Exception as e:
            logger.error(f"加载{self.module_type}模块配置失败: {e}")
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> IValidationResult:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            验证结果
        """
        if self.schema:
            return self.schema.validate(config)
        
        # 如果没有模式，返回成功
        return ValidationResult(is_valid=True, errors=[], warnings=[])
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为模块特定格式
        
        子类应该重写此方法以实现模块特定的转换逻辑。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        # 默认实现：不做转换
        return config
    
    def set_base_path(self, base_path: Path) -> None:
        """设置配置基础路径
        
        Args:
            base_path: 基础路径
        """
        self._base_path = base_path
        # Note: base_path is a read-only property on IConfigLoader, cannot be set directly
        # The config_loader must handle base_path internally or through initialization
    
    def get_config_path(self, config_name: str) -> str:
        """获取配置文件完整路径
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置文件路径
        """
        # 构建模块特定的配置路径
        module_path = self._base_path / self.module_type / config_name
        
        # 如果没有扩展名，添加.yaml
        if not module_path.suffix:
            module_path = module_path.with_suffix('.yaml')
        
        return str(module_path)
    
    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            重新加载的配置数据
        """
        logger.info(f"重新加载{self.module_type}模块配置: {config_path}")
        return self.load_config(config_path)
    
    def get_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """获取当前配置
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            当前配置数据
        """
        # 获取默认配置路径
        config_name = f"{self.module_type}"
        config_path = self.get_config_path(config_name)
        return self.load_config(config_path, use_cache)
    
    def discover_configs(self, pattern: str = "*") -> list[str]:
        """发现配置文件
        
        Args:
            pattern: 文件模式（支持通配符）
            
        Returns:
            配置文件路径列表
        """
        return self.discovery_manager.discover_module_configs(self.module_type, pattern)
    
    def get_config_info(self, config_path: str) -> Dict[str, Any]:
        """获取配置文件信息
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置文件信息
        """
        return self.discovery_manager.get_config_info(config_path)
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径，如果为None则清除所有缓存
        """
        if config_path:
            cache_key = f"{self.module_type}:{config_path}"
            self.cache_manager.delete(cache_key)
        else:
            # 清除模块相关的所有缓存
            self.cache_manager.clear()
    
    def validate_config_structure(self, config: Dict[str, Any], required_keys: list[str]) -> IValidationResult:
        """验证配置结构
        
        Args:
            config: 配置数据
            required_keys: 必需的键列表
            
        Returns:
            验证结果
        """
        # 使用基础设施层的验证功能
        from src.infrastructure.config.validation.base_validator import GenericConfigValidator
        validator = GenericConfigValidator()
        result = validator.validate(config)
        
        # 验证必需字段
        for key in required_keys:
            if key not in config:
                result.add_error(f"缺少必需的配置键: {key}")
        
        return result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return self.cache_manager.get_stats()


class ConfigProcessorChain(IConfigProcessor):
    """配置处理器链实现
    
    组合多个处理器，按顺序执行它们。
    """
    
    def __init__(self) -> None:
        self._processors: list[IConfigProcessor] = []
        logger.debug("配置处理器链初始化完成")
    
    def get_name(self) -> str:
        """获取处理器链名称
        
        Returns:
            处理器链名称
        """
        return "ConfigProcessorChain"
    
    def add_processor(self, processor: IConfigProcessor) -> None:
        """添加处理器
        
        Args:
            processor: 配置处理器（需要实现 IConfigProcessor 接口）
        """
        self._processors.append(processor)
        logger.debug(f"已添加配置处理器: {processor.__class__.__name__}")
    
    def remove_processor(self, processor: IConfigProcessor) -> bool:
        """移除处理器
        
        Args:
            processor: 配置处理器
            
        Returns:
            是否成功移除
        """
        if processor in self._processors:
            self._processors.remove(processor)
            logger.debug(f"已移除配置处理器: {processor.__class__.__name__}")
            return True
        return False
    
    def clear_processors(self) -> None:
        """清除所有处理器"""
        self._processors.clear()
        logger.debug("已清除所有配置处理器")
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """应用处理器链
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        result = config
        
        for i, processor in enumerate(self._processors):
            try:
                logger.debug(f"执行处理器 {i+1}/{len(self._processors)}: {processor.__class__.__name__}")
                result = processor.process(result, config_path)
            except Exception as e:
                logger.error(f"处理器 {processor.__class__.__name__} 执行失败: {e}")
                raise
        
        logger.debug(f"配置处理完成，共执行 {len(self._processors)} 个处理器")
        return result
    
    def get_processors(self) -> list[IConfigProcessor]:
        """获取处理器列表
        
        Returns:
            处理器列表
        """
        return self._processors.copy()
    
    def get_processor_count(self) -> int:
        """获取处理器数量
        
        Returns:
            处理器数量
        """
        return len(self._processors)
    
    def get_processor_names(self) -> list[str]:
        """获取处理器名称列表
        
        Returns:
            处理器名称列表
        """
        return [processor.__class__.__name__ for processor in self._processors]


class BaseSchemaGenerator(ISchemaGenerator):
    """Schema生成器基类
    
    提供Schema生成的通用功能和缓存机制。
    """
    
    def __init__(self, generator_type: str, config_provider: Optional['IConfigImpl'] = None):
        """初始化Schema生成器
        
        Args:
            generator_type: 生成器类型
            config_provider: 配置实现
        """
        self.generator_type = generator_type
        self.config_provider = config_provider
        
        # 使用统一的缓存管理器和键生成器
        self.cache_manager = CacheManager()
        from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator
        self.key_generator = DefaultCacheKeyGenerator()
        
        logger.debug(f"初始化{generator_type} Schema生成器")
    
    def get_generator_type(self) -> str:
        """获取生成器类型
        
        Returns:
            str: 生成器类型
        """
        return self.generator_type
    
    def generate_schema_from_type(self, config_type: str) -> Dict[str, Any]:
        """从配置类型生成Schema
        
        Args:
            config_type: 配置类型（注：此实现中忽略此参数，使用config_provider获取配置）
        
        Returns:
            Dict[str, Any]: JSON Schema
            
        Raises:
            ValueError: 如果config_provider未设置
        """
        if not self.config_provider:
            raise ValueError("config_provider is required for this method")
        
        # 获取配置数据
        config_data = self.config_provider.get_config()
        return self.generate_schema_from_config(config_data)
    