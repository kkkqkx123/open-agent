"""环境配置管理

提供环境特定的配置管理功能。
"""

import logging
from typing import Dict, Any, Type, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EnvironmentConfig(ABC):
    """环境配置基类"""
    
    @abstractmethod
    def should_register_service(self, service_type: Type) -> bool:
        """判断是否应该注册服务
        
        Args:
            service_type: 服务类型
            
        Returns:
            是否应该注册
        """
        pass
    
    @abstractmethod
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        """获取服务配置
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务配置字典
        """
        pass


class DefaultConfig(EnvironmentConfig):
    """默认环境配置"""
    
    def should_register_service(self, service_type: Type) -> bool:
        """默认环境注册所有服务"""
        return True
    
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            "enable_debug": False,
            "enable_profiling": False,
            "log_level": "INFO"
        }


class DevelopmentConfig(EnvironmentConfig):
    """开发环境配置"""
    
    def should_register_service(self, service_type: Type) -> bool:
        """开发环境注册所有服务"""
        return True
    
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        """返回开发环境特定配置"""
        return {
            "enable_debug": True,
            "enable_profiling": True,
            "log_level": "DEBUG",
            "enable_hot_reload": True,
            "enable_developer_tools": True
        }


class TestConfig(EnvironmentConfig):
    """测试环境配置"""
    
    def should_register_service(self, service_type: Type) -> bool:
        """测试环境注册所有服务，但使用Mock实现"""
        return True
    
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        """返回测试环境特定配置"""
        return {
            "enable_debug": True,
            "enable_profiling": False,
            "log_level": "DEBUG",
            "use_mock_implementations": True,
            "enable_test_fixtures": True
        }


class ProductionConfig(EnvironmentConfig):
    """生产环境配置"""
    
    def should_register_service(self, service_type: Type) -> bool:
        """生产环境只注册必要服务，过滤掉调试和开发相关服务"""
        return not self._is_debug_service(service_type)
    
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        """返回生产环境特定配置"""
        return {
            "enable_debug": False,
            "enable_profiling": False,
            "log_level": "INFO",
            "enable_caching": True,
            "enable_optimization": True,
            "enable_monitoring": True
        }
    
    def _is_debug_service(self, service_type: Type) -> bool:
        """判断是否为调试服务"""
        service_name = service_type.__name__.lower()
        debug_keywords = ["debug", "test", "mock", "dev", "profiler"]
        return any(keyword in service_name for keyword in debug_keywords)


class EnvironmentConfigManager:
    """环境配置管理器
    
    管理不同环境的配置，提供环境特定的服务注册策略。
    """
    
    def __init__(self):
        """初始化环境配置管理器"""
        self.environments = {
            "default": DefaultConfig(),
            "development": DevelopmentConfig(),
            "test": TestConfig(),
            "production": ProductionConfig()
        }
        self.current_environment = "default"
        
        # 环境特定服务配置
        self.service_overrides: Dict[str, Dict[str, Any]] = {}
    
    def set_environment(self, environment: str) -> None:
        """设置当前环境
        
        Args:
            environment: 环境名称
        """
        if environment not in self.environments:
            raise ValueError(f"不支持的环境: {environment}")
        
        self.current_environment = environment
        logger.info(f"环境设置为: {environment}")
    
    def get_current_environment(self) -> str:
        """获取当前环境
        
        Returns:
            当前环境名称
        """
        return self.current_environment
    
    def get_current_config(self) -> EnvironmentConfig:
        """获取当前环境配置
        
        Returns:
            当前环境的配置对象
        """
        if self.current_environment == "default":
            return DefaultConfig()
        
        return self.environments[self.current_environment]
    
    def should_register_service(self, service_type: Type, environment: Optional[str] = None) -> bool:
        """判断是否应该注册服务
        
        Args:
            service_type: 服务类型
            environment: 环境名称，如果为None则使用当前环境
            
        Returns:
            是否应该注册服务
        """
        env = environment or self.current_environment
        config = self.environments.get(env, DefaultConfig())
        return config.should_register_service(service_type)
    
    def get_service_config(self, service_type: Type, environment: Optional[str] = None) -> Dict[str, Any]:
        """获取服务配置
        
        Args:
            service_type: 服务类型
            environment: 环境名称，如果为None则使用当前环境
            
        Returns:
            服务配置字典
        """
        env = environment or self.current_environment
        config = self.environments.get(env, DefaultConfig())
        
        # 获取基础配置
        base_config = config.get_service_config(service_type)
        
        # 应用服务特定覆盖
        service_name = service_type.__name__
        if env in self.service_overrides and service_name in self.service_overrides[env]:
            base_config.update(self.service_overrides[env][service_name])
        
        return base_config
    
    def register_service_override(self, 
                               environment: str, 
                               service_name: str, 
                               config: Dict[str, Any]) -> None:
        """注册服务配置覆盖
        
        Args:
            environment: 环境名称
            service_name: 服务名称
            config: 配置覆盖
        """
        if environment not in self.service_overrides:
            self.service_overrides[environment] = {}
        
        self.service_overrides[environment][service_name] = config
        logger.debug(f"注册服务配置覆盖: {environment}.{service_name}")
    
    def get_environment_specific_implementation(self, 
                                           interface: Type, 
                                           environment: Optional[str] = None) -> Optional[Type]:
        """获取环境特定的实现类型
        
        Args:
            interface: 接口类型
            environment: 环境名称，如果为None则使用当前环境
            
        Returns:
            环境特定的实现类型，如果没有则返回None
        """
        env = environment or self.current_environment
        
        # 这里可以根据接口类型和环境返回特定的实现
        # 例如，测试环境返回Mock实现，生产环境返回优化实现等
        
        # 示例：为测试环境提供Mock实现
        if env == "test" and hasattr(interface, "__name__"):
            interface_name = interface.__name__
            if interface_name.startswith("I"):
                mock_name = f"Mock{interface_name[1:]}"
                # 尝试在相应的模块中查找Mock实现
                try:
                    module_name = interface.__module__.replace(".interfaces", ".mocks")
                    module = __import__(module_name, fromlist=[mock_name])
                    return getattr(module, mock_name, None)
                except (ImportError, AttributeError):
                    pass
        
        return None
    
    def validate_environment(self, environment: str) -> Dict[str, Any]:
        """验证环境配置
        
        Args:
            environment: 环境名称
            
        Returns:
            验证结果
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if environment not in self.environments:
            result["valid"] = False
            result["errors"].append(f"不支持的环境: {environment}")
            return result
        
        # 检查环境特定配置
        if environment in self.service_overrides:
            for service_name, config in self.service_overrides[environment].items():
                if not isinstance(config, dict):
                    result["warnings"].append(f"服务 {service_name} 的配置不是字典类型")
        
        return result