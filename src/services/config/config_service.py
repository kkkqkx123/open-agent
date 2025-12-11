"""配置服务 - 所有模块配置的统一入口

提供模块化、可扩展的配置管理服务，支持跨模块引用和依赖管理。
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from src.interfaces.config import (
    IConfigManager,
    IModuleConfigService,
    IConfigMapperRegistry,
    IConfigChangeListener,
    IConfigMonitor,
    IConfigVersionManager,
    IConfigStorage,
    ConfigChangeEvent,
    ValidationResult,
    ModuleConfig,
    ModuleDependency,
    ConfigVersion
)
from src.interfaces.dependency_injection import get_logger

logger = get_logger(__name__)


class ConfigService:
    """配置服务 - 所有模块配置的统一入口"""
    
    def __init__(self, 
                 config_manager: IConfigManager,
                 module_services: Optional[Dict[str, IModuleConfigService]] = None,
                 mapper_registry: Optional[IConfigMapperRegistry] = None,
                 config_monitor: Optional[IConfigMonitor] = None,
                 version_manager: Optional[IConfigVersionManager] = None):
        """初始化配置服务
        
        Args:
            config_manager: 配置管理器
            module_services: 模块特定服务字典
            mapper_registry: 配置映射器注册表
            config_monitor: 配置监控器
            version_manager: 版本管理器
        """
        self.config_manager = config_manager
        self.module_services = module_services or {}
        self.mapper_registry = mapper_registry
        self.config_monitor = config_monitor
        self.version_manager = version_manager
        
        # 配置变更监听器
        self._change_listeners: List[IConfigChangeListener] = []
        
        # 模块依赖管理
        self._module_dependencies: Dict[str, List[ModuleDependency]] = {}
        
        logger.info("配置服务初始化完成")
    
    def load_module_config(self, module_type: str, config_path: str) -> Any:
        """加载模块配置
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            
        Returns:
            Any: 配置实体
        """
        try:
            logger.debug(f"加载模块配置: {module_type}:{config_path}")
            
            # 检查是否有模块特定服务
            if module_type in self.module_services:
                service = self.module_services[module_type]
                config = service.load_config(config_path)
            else:
                # 使用通用配置管理器加载
                config_data = self.config_manager.load_config(config_path, module_type)
                
                # 如果有映射器，转换为业务实体
                if self.mapper_registry:
                    try:
                        config = self.mapper_registry.dict_to_entity(module_type, config_data)
                    except ValueError:
                        # 如果没有映射器，直接返回配置数据
                        config = config_data
                else:
                    config = config_data
            
            logger.info(f"模块配置加载成功: {module_type}:{config_path}")
            return config
            
        except Exception as e:
            logger.error(f"加载模块配置失败: {module_type}:{config_path}, 错误: {e}")
            raise
    
    def save_module_config(self, module_type: str, config: Any, config_path: str) -> None:
        """保存模块配置
        
        Args:
            module_type: 模块类型
            config: 配置实体
            config_path: 配置文件路径
        """
        try:
            logger.debug(f"保存模块配置: {module_type}:{config_path}")
            
            # 检查是否有模块特定服务
            if module_type in self.module_services:
                service = self.module_services[module_type]
                service.save_config(config, config_path)
            else:
                # 如果有映射器，转换为配置字典
                if self.mapper_registry:
                    try:
                        config_data = self.mapper_registry.entity_to_dict(module_type, config)
                    except ValueError:
                        # 如果没有映射器，直接使用配置数据
                        config_data = config
                else:
                    config_data = config
                
                # 使用通用配置管理器保存
                self.config_manager.save_config(config_data, config_path)
            
            logger.info(f"模块配置保存成功: {module_type}:{config_path}")
            
        except Exception as e:
            logger.error(f"保存模块配置失败: {module_type}:{config_path}, 错误: {e}")
            raise
    
    def validate_module_config(self, module_type: str, config: Any) -> ValidationResult:
        """验证模块配置
        
        Args:
            module_type: 模块类型
            config: 配置实体
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            logger.debug(f"验证模块配置: {module_type}")
            
            # 检查是否有模块特定服务
            if module_type in self.module_services:
                service = self.module_services[module_type]
                return service.validate_config(config)
            else:
                # 使用通用验证器
                if isinstance(config, dict):
                    return self.config_manager.validate_config(config)
                else:
                    # 如果是业务实体，先转换为字典再验证
                    if self.mapper_registry:
                        try:
                            config_data = self.mapper_registry.entity_to_dict(module_type, config)
                            return self.config_manager.validate_config(config_data)
                        except ValueError:
                            pass
                    
                    # 如果无法转换，返回成功
                    return ValidationResult(is_valid=True, errors=[], warnings=[])
            
        except Exception as e:
            logger.error(f"验证模块配置失败: {module_type}, 错误: {e}")
            return ValidationResult(is_valid=False, errors=[str(e)], warnings=[])
    
    def register_module_service(self, module_type: str, service: IModuleConfigService) -> None:
        """注册模块特定服务
        
        Args:
            module_type: 模块类型
            service: 模块配置服务
        """
        self.module_services[module_type] = service
        logger.info(f"已注册模块服务: {module_type}")
    
    def start_watching(self, module_type: str, config_path: str) -> None:
        """开始监控配置文件
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
        """
        if self.config_monitor:
            self.config_monitor.start_watching(module_type, config_path)
            logger.info(f"开始监控配置文件: {module_type}:{config_path}")
        else:
            logger.warning("配置监控器未设置，无法开始监控")
    
    def add_change_listener(self, listener: IConfigChangeListener) -> None:
        """添加配置变更监听器
        
        Args:
            listener: 配置变更监听器
        """
        self._change_listeners.append(listener)
        
        # 如果有配置监控器，也添加到监控器
        if self.config_monitor:
            self.config_monitor.add_change_listener(listener)
        
        logger.info("已添加配置变更监听器")
    
    def save_config_version(self, module_type: str, config_path: str, config: Dict[str, Any], 
                           version: str, comment: str = "") -> None:
        """保存配置版本
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            config: 配置数据
            version: 版本号
            comment: 版本注释
        """
        if self.version_manager:
            self.version_manager.save_version(module_type, config_path, config, version, comment)
            logger.info(f"已保存配置版本: {module_type}:{config_path}:{version}")
        else:
            logger.warning("版本管理器未设置，无法保存版本")
    
    def load_config_version(self, module_type: str, config_path: str, version: str) -> Dict[str, Any]:
        """加载指定版本的配置
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            version: 版本号
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        if self.version_manager:
            config = self.version_manager.load_version(module_type, config_path, version)
            logger.info(f"已加载配置版本: {module_type}:{config_path}:{version}")
            return config
        else:
            logger.warning("版本管理器未设置，无法加载版本")
            raise ValueError("版本管理器未设置")
    
    def rollback_config(self, module_type: str, config_path: str, version: str) -> None:
        """回滚配置到指定版本
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            version: 版本号
        """
        if self.version_manager:
            self.version_manager.rollback(module_type, config_path, version)
            logger.info(f"已回滚配置版本: {module_type}:{config_path}:{version}")
        else:
            logger.warning("版本管理器未设置，无法回滚")
            raise ValueError("版本管理器未设置")
    
    def list_config_versions(self, module_type: str, config_path: str) -> List[ConfigVersion]:
        """列出版本信息
        
        Args:
            module_type: 模块类型
            config_path: 配置文件路径
            
        Returns:
            List[ConfigVersion]: 版本列表
        """
        if self.version_manager:
            versions = self.version_manager.list_versions(module_type, config_path)
            logger.info(f"已获取版本列表: {module_type}:{config_path}, 共{len(versions)}个版本")
            return versions
        else:
            logger.warning("版本管理器未设置，无法列出版本")
            return []
    
    def register_module_dependency(self, module_type: str, dependency: ModuleDependency) -> None:
        """注册模块依赖
        
        Args:
            module_type: 模块类型
            dependency: 模块依赖
        """
        if module_type not in self._module_dependencies:
            self._module_dependencies[module_type] = []
        self._module_dependencies[module_type].append(dependency)
        logger.info(f"已注册模块依赖: {module_type} -> {dependency.module_type}")
    
    def resolve_module_dependencies(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析模块依赖
        
        Args:
            module_type: 模块类型
            config: 配置数据
            
        Returns:
            Dict[str, Any]: 解析后的配置数据
        """
        resolved_config = config.copy()
        
        if module_type in self._module_dependencies:
            for dependency in self._module_dependencies[module_type]:
                try:
                    # 加载依赖配置
                    dep_config = self.load_module_config(dependency.module_type, dependency.config_path)
                    
                    # 合并依赖配置
                    resolved_config = self._merge_dependency(resolved_config, dep_config, dependency)
                    
                except Exception as e:
                    logger.error(f"解析模块依赖失败: {module_type} -> {dependency.module_type}, 错误: {e}")
                    # 继续处理其他依赖
        
        return resolved_config
    
    def _merge_dependency(self, config: Dict[str, Any], dep_config: Any, dependency: ModuleDependency) -> Dict[str, Any]:
        """合并依赖配置
        
        Args:
            config: 当前配置
            dep_config: 依赖配置
            dependency: 依赖定义
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        # 简化实现，实际应该根据依赖定义进行更复杂的合并
        if isinstance(dep_config, dict):
            for field in dependency.required_fields:
                if field in dep_config:
                    config[field] = dep_config[field]
            
            for field in dependency.optional_fields:
                if field in dep_config and field not in config:
                    config[field] = dep_config[field]
        
        return config
    
    def _notify_config_changed(self, event: ConfigChangeEvent) -> None:
        """通知配置变更
        
        Args:
            event: 配置变更事件
        """
        for listener in self._change_listeners:
            try:
                listener.on_config_changed(event)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败: {e}")


# 创建默认实例
default_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """获取默认配置服务实例
    
    Returns:
        ConfigService: 配置服务实例
    """
    global default_config_service
    if default_config_service is None:
        raise ValueError("配置服务未初始化，请先调用 create_config_service")
    return default_config_service


def create_config_service(config_manager: IConfigManager,
                         mapper_registry: Optional[IConfigMapperRegistry] = None) -> ConfigService:
    """创建配置服务实例
    
    Args:
        config_manager: 配置管理器
        mapper_registry: 配置映射器注册表
        
    Returns:
        ConfigService: 配置服务实例
    """
    global default_config_service
    default_config_service = ConfigService(
        config_manager=config_manager,
        mapper_registry=mapper_registry
    )
    return default_config_service