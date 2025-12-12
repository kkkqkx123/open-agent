"""配置注册中心

管理所有配置实现、处理器和提供者的注册和获取。
"""

from typing import Dict, Any, Optional, List, Type
import logging
from pathlib import Path

from .impl.base_impl import IConfigImpl, ConfigProcessorChain
from .schema.base_schema import IConfigSchema
from .processor.base_processor import IConfigProcessor

logger = logging.getLogger(__name__)


class ConfigRegistry:
    """配置注册中心
    
    管理所有配置实现、处理器和模式的注册和获取。
    """
    
    def __init__(self):
        """初始化配置注册中心"""
        # 配置实现注册表
        self._implementations: Dict[str, IConfigImpl] = {}
        
        # 处理器注册表
        self._processors: Dict[str, IConfigProcessor] = {}
        
        # 模式注册表 - 使用简单的字典存储
        self._schemas: Dict[str, IConfigSchema] = {}
        
        # 处理器链注册表
        self._processor_chains: Dict[str, ConfigProcessorChain] = {}
        
        # 配置工厂注册表
        self._factories: Dict[str, Type] = {}
        
        logger.debug("初始化配置注册中心")
    
    # ==================== 配置实现管理 ====================
    
    def register_implementation(self, module_type: str, impl: IConfigImpl) -> None:
        """注册配置实现
        
        Args:
            module_type: 模块类型
            impl: 配置实现
        """
        self._implementations[module_type] = impl
        logger.debug(f"注册{module_type}模块配置实现")
    
    def get_implementation(self, module_type: str) -> Optional[IConfigImpl]:
        """获取配置实现
        
        Args:
            module_type: 模块类型
            
        Returns:
            配置实现
        """
        return self._implementations.get(module_type)
    
    def has_implementation(self, module_type: str) -> bool:
        """检查是否存在配置实现
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否存在
        """
        return module_type in self._implementations
    
    def unregister_implementation(self, module_type: str) -> bool:
        """注销配置实现
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否成功注销
        """
        if module_type in self._implementations:
            del self._implementations[module_type]
            logger.debug(f"注销{module_type}模块配置实现")
            return True
        return False
    
    def get_registered_implementations(self) -> List[str]:
        """获取已注册的配置实现列表
        
        Returns:
            模块类型列表
        """
        return list(self._implementations.keys())
    
    # ==================== 处理器管理 ====================
    
    def register_processor(self, name: str, processor: IConfigProcessor) -> None:
        """注册配置处理器
        
        Args:
            name: 处理器名称
            processor: 配置处理器
        """
        self._processors[name] = processor
        logger.debug(f"注册配置处理器: {name}")
    
    def get_processor(self, name: str) -> Optional[IConfigProcessor]:
        """获取配置处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            配置处理器
        """
        return self._processors.get(name)
    
    def has_processor(self, name: str) -> bool:
        """检查是否存在处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            是否存在
        """
        return name in self._processors
    
    def unregister_processor(self, name: str) -> bool:
        """注销配置处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            是否成功注销
        """
        if name in self._processors:
            del self._processors[name]
            logger.debug(f"注销配置处理器: {name}")
            return True
        return False
    
    def get_registered_processors(self) -> List[str]:
        """获取已注册的处理器列表
        
        Returns:
            处理器名称列表
        """
        return list(self._processors.keys())
    
    # ==================== 处理器链管理 ====================
    
    def create_processor_chain(self, module_type: str, processor_names: List[str]) -> ConfigProcessorChain:
        """创建处理器链
        
        Args:
            module_type: 模块类型
            processor_names: 处理器名称列表
            
        Returns:
            处理器链
        """
        chain = ConfigProcessorChain()
        
        for processor_name in processor_names:
            processor = self.get_processor(processor_name)
            if processor:
                chain.add_processor(processor)
            else:
                logger.warning(f"未找到处理器: {processor_name}")
        
        # 缓存处理器链
        self._processor_chains[module_type] = chain
        logger.debug(f"为{module_type}模块创建处理器链")
        
        return chain
    
    def get_processor_chain(self, module_type: str) -> Optional[ConfigProcessorChain]:
        """获取处理器链
        
        Args:
            module_type: 模块类型
            
        Returns:
            处理器链
        """
        return self._processor_chains.get(module_type)
    
    def has_processor_chain(self, module_type: str) -> bool:
        """检查是否存在处理器链
        
        Args:
            module_type: 模块类型
            
        Returns:
            是否存在
        """
        return module_type in self._processor_chains
    
    
    # ==================== 模式管理 ====================
    
    def register_schema(self, config_type: str, schema: IConfigSchema) -> None:
        """注册配置模式
        
        Args:
            config_type: 配置类型
            schema: 配置模式
        """
        self._schemas[config_type] = schema
    
    def get_schema(self, config_type: str) -> Optional[IConfigSchema]:
        """获取配置模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            配置模式
        """
        return self._schemas.get(config_type)
    
    def has_schema(self, config_type: str) -> bool:
        """检查是否存在配置模式
        
        Args:
            config_type: 配置类型
            
        Returns:
            是否存在
        """
        return config_type in self._schemas
    
    # ==================== 工厂管理 ====================
    
    def register_factory(self, name: str, factory_class: Type) -> None:
        """注册配置工厂
        
        Args:
            name: 工厂名称
            factory_class: 工厂类
        """
        self._factories[name] = factory_class
        logger.debug(f"注册配置工厂: {name}")
    
    def get_factory(self, name: str) -> Optional[Type]:
        """获取配置工厂
        
        Args:
            name: 工厂名称
            
        Returns:
            工厂类
        """
        return self._factories.get(name)
    
    def has_factory(self, name: str) -> bool:
        """检查是否存在配置工厂
        
        Args:
            name: 工厂名称
            
        Returns:
            是否存在
        """
        return name in self._factories
    
    def get_registered_factories(self) -> List[str]:
        """获取已注册的工厂列表
        
        Returns:
            工厂名称列表
        """
        return list(self._factories.keys())
    
    # ==================== 统计和状态 ====================
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册中心统计信息
        
        Returns:
            统计信息
        """
        return {
            "implementations": {
                "count": len(self._implementations),
                "modules": list(self._implementations.keys())
            },
            "processors": {
                "count": len(self._processors),
                "names": list(self._processors.keys())
            },
            "processor_chains": {
                "count": len(self._processor_chains),
                "modules": list(self._processor_chains.keys())
            },
            "schemas": {
                "count": len(self._schemas),
                "types": list(self._schemas.keys())
            },
            "factories": {
                "count": len(self._factories),
                "names": list(self._factories.keys())
            }
        }
    
    def validate_registry(self) -> Dict[str, Any]:
        """验证注册中心完整性
        
        Returns:
            验证结果
        """
        issues = []
        warnings = []
        
        # 检查处理器链是否有有效的处理器
        for module_type, chain in self._processor_chains.items():
            if not chain.get_processors():
                issues.append(f"模块{module_type}的处理器链为空")
        
        # 检查是否有必要的处理器
        required_processors = ["validation", "transformation"]
        for processor_name in required_processors:
            if processor_name not in self._processors:
                warnings.append(f"缺少推荐处理器: {processor_name}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def clear_registry(self) -> None:
        """清空注册中心"""
        self._implementations.clear()
        self._processors.clear()
        self._processor_chains.clear()
        self._factories.clear()
        
        # 清空模式注册表
        self._schemas.clear()
        logger.debug("清空配置注册中心")


# 全局配置注册中心实例
_global_registry: Optional[ConfigRegistry] = None


def get_global_registry() -> ConfigRegistry:
    """获取全局配置注册中心
    
    Returns:
        配置注册中心实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ConfigRegistry()
    return _global_registry


def set_global_registry(registry: ConfigRegistry) -> None:
    """设置全局配置注册中心
    
    Args:
        registry: 配置注册中心实例
    """
    global _global_registry
    _global_registry = registry