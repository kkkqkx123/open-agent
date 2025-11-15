"""应用程序统一配置入口

提供统一的依赖注入配置入口，整合各层配置。
"""

import logging
from typing import Dict, Any, Optional

from src.di.unified_container import UnifiedContainerManager
from src.infrastructure.container import IDependencyContainer
from src.infrastructure.di.infrastructure_config import InfrastructureConfig
from src.domain.di.domain_config import DomainConfig
from src.application.di.application_config import ApplicationConfig
from src.presentation.di.presentation_config import PresentationConfig

logger = logging.getLogger(__name__)


class ApplicationConfig:
    """应用程序统一配置入口
    
    负责整合各层的DI配置，提供统一的配置入口。
    """
    
    def __init__(self, environment: str = "default"):
        """初始化应用程序配置
        
        Args:
            environment: 环境名称
        """
        self.environment = environment
        self.container: Optional[IDependencyContainer] = None
        self.unified_manager: Optional[UnifiedContainerManager] = None
        
        logger.debug(f"ApplicationConfig初始化完成，环境: {environment}")
    
    def configure(self, 
                 config_path: str = "configs",
                 enable_monitoring: bool = True,
                 enable_validation: bool = True,
                 additional_services: Optional[Dict[str, Any]] = None) -> IDependencyContainer:
        """配置应用程序的所有服务
        
        Args:
            config_path: 配置文件路径
            enable_monitoring: 是否启用监控
            enable_validation: 是否启用验证
            additional_services: 额外服务配置
            
        Returns:
            配置好的依赖注入容器
        """
        logger.info(f"开始配置应用程序的所有服务，环境: {self.environment}")
        
        try:
            # 创建统一容器管理器
            self.unified_manager = UnifiedContainerManager()
            
            # 配置基础设施层（最底层）
            logger.info("开始配置基础设施层服务...")
            InfrastructureConfig.configure(self.unified_manager.container, self.environment)
            
            # 配置领域层
            logger.info("开始配置领域层服务...")
            DomainConfig.configure(self.unified_manager.container, self.environment)
            
            # 配置应用层
            logger.info("开始配置应用层服务...")
            ApplicationConfig.configure(self.unified_manager.container, self.environment)
            
            # 配置表示层（最顶层）
            logger.info("开始配置表示层服务...")
            PresentationConfig.configure(self.unified_manager.container, self.environment)
            
            # 注册额外服务
            if additional_services:
                logger.info("注册额外服务...")
                self._register_additional_services(additional_services)
            
            # 验证配置
            if enable_validation:
                logger.info("验证配置...")
                validation_result = self.unified_manager.validate_configuration()
                if not validation_result["valid"]:
                    logger.error(f"配置验证失败: {validation_result['errors']}")
                    raise RuntimeError(f"配置验证失败: {validation_result['errors']}")
                
                if validation_result["warnings"]:
                    for warning in validation_result["warnings"]:
                        logger.warning(warning)
            
            # 设置容器
            self.container = self.unified_manager.get_container()
            
            logger.info(f"所有层服务配置完成，环境: {self.environment}")
            return self.container
            
        except Exception as e:
            logger.error(f"配置过程中发生错误: {e}")
            self.unified_manager = None
            raise
    
    def _register_additional_services(self, services_config: Dict[str, Any]) -> None:
        """注册额外服务
        
        Args:
            services_config: 服务配置字典
        """
        if not self.unified_manager or not self.container:
            logger.warning("容器未配置，无法注册额外服务")
            return
        
        for service_name, service_config in services_config.items():
            try:
                self._register_single_service(service_name, service_config)
            except Exception as e:
                logger.error(f"注册服务 {service_name} 失败: {e}")
    
    def _register_single_service(self, service_name: str, service_config: Dict[str, Any]) -> None:
        """注册单个服务
        
        Args:
            service_name: 服务名称
            service_config: 服务配置
        """
        # 获取服务类型
        service_type = self._resolve_service_type(service_config.get("type"))
        if not service_type:
            logger.warning(f"无法解析服务类型: {service_config.get('type')}")
            return
        
        # 获取实现类型
        implementation_type = self._resolve_service_type(service_config.get("implementation"))
        if not implementation_type:
            logger.warning(f"无法解析实现类型: {service_config.get('implementation')}")
            return
        
        # 获取生命周期
        from src.infrastructure.infrastructure_types import ServiceLifetime
        lifetime = service_config.get("lifetime", ServiceLifetime.SINGLETON)
        
        # 获取环境
        environment = service_config.get("environment", "default")
        
        # 注册服务
        self.unified_manager.container.register(
            service_type,
            implementation_type,
            environment=environment,
            lifetime=lifetime
        )
        
        logger.debug(f"服务 {service_name} 注册完成")
    
    def _resolve_service_type(self, type_str: Optional[str]) -> Optional[type]:
        """解析服务类型字符串
        
        Args:
            type_str: 类型字符串
            
        Returns:
            解析后的类型，如果解析失败则返回None
        """
        if not type_str:
            return None
        
        try:
            # 简单的类型解析，可以根据需要扩展
            module_path, class_name = type_str.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError, ValueError):
            return None
    
    def get_container(self) -> IDependencyContainer:
        """获取配置好的容器
        
        Returns:
            配置好的依赖注入容器
            
        Raises:
            RuntimeError: 如果容器尚未配置
        """
        if not self.container:
            raise RuntimeError("容器尚未配置，请先调用configure()")
        return self.container
    
    def validate_configuration(self) -> Dict[str, Any]:
        """验证配置
        
        Returns:
            验证结果
        """
        if not self.unified_manager:
            return {
                "valid": False,
                "error": "统一容器管理器未初始化"
            }
        
        return self.unified_manager.validate_configuration()
    
    def get_module_info(self) -> Dict[str, Any]:
        """获取模块信息
        
        Returns:
            模块信息字典
        """
        if not self.unified_manager:
            return {
                "valid": False,
                "error": "统一容器管理器未初始化"
            }
        
        return self.unified_manager.get_module_info()
    
    def reload_module(self, module_name: str) -> None:
        """重新加载模块
        
        Args:
            module_name: 模块名称
        """
        if not self.unified_manager:
            raise RuntimeError("统一容器管理器未初始化")
        
        logger.info(f"重新加载模块: {module_name}")
        self.unified_manager.reload_module(module_name)
    
    def reset(self) -> None:
        """重置配置"""
        if self.unified_manager:
            self.unified_manager.reset()
        
        self.container = None
        logger.info("应用程序配置已重置")


# 全局配置实例
_global_config: Optional[ApplicationConfig] = None


def get_global_config(environment: str = "default") -> ApplicationConfig:
    """获取全局配置实例
    
    Args:
        environment: 环境名称
        
    Returns:
        全局配置实例
    """
    global _global_config
    if _global_config is None or _global_config.environment != environment:
        _global_config = ApplicationConfig(environment)
    
    return _global_config


def reset_global_config() -> None:
    """重置全局配置"""
    global _global_config
    if _global_config:
        _global_config.reset()
    _global_config = None