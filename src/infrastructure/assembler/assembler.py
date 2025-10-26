"""组件组装器实现

提供配置驱动的组件组装功能，支持自动依赖解析和生命周期管理。
"""

import logging
import importlib
from typing import Dict, Any, List, Optional, Type, Set, Tuple
from inspect import isclass, signature

from .interfaces import IComponentAssembler
from .exceptions import (
    AssemblyError,
    ComponentNotFoundError,
    DependencyResolutionError,
    CircularDependencyError,
    ConfigurationError
)
from ..container import IDependencyContainer, ServiceLifetime, DependencyContainer
from ..config_loader import IConfigLoader

logger = logging.getLogger(__name__)


class ComponentAssembler(IComponentAssembler):
    """组件组装器实现
    
    负责根据配置自动组装组件，支持依赖解析和生命周期管理。
    """
    
    def __init__(
        self,
        container: Optional[IDependencyContainer] = None,
        config_loader: Optional[IConfigLoader] = None
    ):
        """初始化组件组装器
        
        Args:
            container: 依赖注入容器
            config_loader: 配置加载器
        """
        self.container = container or DependencyContainer()
        self.config_loader = config_loader
        self._assembly_plan: Dict[str, Any] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._resolved_types: Dict[str, Type] = {}
        self._assembly_order: List[str] = []
        
        logger.info("ComponentAssembler初始化完成")
    
    def assemble(self, config: Dict[str, Any]) -> IDependencyContainer:
        """组装组件
        
        Args:
            config: 组装配置
            
        Returns:
            IDependencyContainer: 组装后的依赖注入容器
            
        Raises:
            AssemblyError: 组装失败时抛出
        """
        try:
            logger.info("开始组件组装过程")
            
            # 1. 验证配置
            errors = self.validate_configuration(config)
            if errors:
                raise ConfigurationError(f"配置验证失败: {'; '.join(errors)}")
            
            # 2. 构建组装计划
            self._build_assembly_plan(config)
            
            # 3. 解析依赖关系
            self._resolve_dependency_graph()
            
            # 4. 确定组装顺序
            self._determine_assembly_order()
            
            # 5. 注册服务
            services_config = config.get("services", {})
            self.register_services(services_config)
            
            # 6. 注册依赖关系
            dependencies_config = config.get("dependencies", {})
            self.register_dependencies(dependencies_config)
            
            # 7. 执行启动钩子
            self._execute_startup_hooks(config)
            
            logger.info("组件组装完成")
            return self.container
            
        except Exception as e:
            logger.error(f"组件组装失败: {e}")
            raise AssemblyError(f"组件组装失败: {e}")
    
    def register_services(self, services_config: Dict[str, Any]) -> None:
        """注册服务
        
        Args:
            services_config: 服务配置
        """
        logger.info("开始注册服务")
        
        for service_name, service_config in services_config.items():
            try:
                # 解析服务类型
                service_type = self._resolve_type(service_name)
                if not service_type:
                    logger.warning(f"无法解析服务类型: {service_name}")
                    continue
                
                # 解析实现类型
                implementation_name = service_config.get("implementation")
                if not implementation_name:
                    logger.warning(f"服务 {service_name} 缺少实现配置")
                    continue
                
                implementation_type = self._resolve_type(implementation_name)
                if not implementation_type:
                    logger.warning(f"无法解析实现类型: {implementation_name}")
                    continue
                
                # 获取生命周期
                lifetime_str = service_config.get("lifetime", "singleton")
                lifetime = self._parse_lifetime(lifetime_str)
                
                # 获取环境
                environment = service_config.get("environment", "default")
                
                # 注册服务
                self.container.register(
                    interface=service_type,
                    implementation=implementation_type,
                    environment=environment,
                    lifetime=lifetime
                )
                
                logger.debug(f"注册服务: {service_name} -> {implementation_name}")
                
            except Exception as e:
                logger.error(f"注册服务 {service_name} 失败: {e}")
                raise AssemblyError(f"注册服务 {service_name} 失败: {e}")
        
        logger.info("服务注册完成")
    
    def register_dependencies(self, dependencies_config: Dict[str, Any]) -> None:
        """注册依赖关系
        
        Args:
            dependencies_config: 依赖配置
        """
        logger.info("开始注册依赖关系")
        
        # 注册单例服务
        singletons = dependencies_config.get("singletons", [])
        for service_name in singletons:
            service_type = self._resolve_type(service_name)
            if service_type and not self.container.has_service(service_type):
                # 如果服务未注册，尝试自动注册
                self._auto_register_service(service_type, ServiceLifetime.SINGLETON)
        
        # 注册作用域服务
        scoped = dependencies_config.get("scoped", [])
        for service_name in scoped:
            service_type = self._resolve_type(service_name)
            if service_type and not self.container.has_service(service_type):
                # 如果服务未注册，尝试自动注册
                self._auto_register_service(service_type, ServiceLifetime.SCOPED)
        
        logger.info("依赖关系注册完成")
    
    def resolve_dependencies(self, service_type: Type) -> Any:
        """解析依赖
        
        Args:
            service_type: 服务类型
            
        Returns:
            Any: 服务实例
        """
        try:
            return self.container.get(service_type)
        except Exception as e:
            raise DependencyResolutionError(f"解析依赖 {service_type} 失败: {e}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """验证配置
        
        Args:
            config: 配置字典
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证必需字段
        if "version" not in config:
            errors.append("缺少版本信息")
        
        if "application" not in config:
            errors.append("缺少应用程序配置")
        
        # 验证服务配置
        services_config = config.get("services", {})
        for service_name, service_config in services_config.items():
            if not isinstance(service_config, dict):
                errors.append(f"服务 {service_name} 配置必须是字典类型")
                continue
            
            if "implementation" not in service_config:
                errors.append(f"服务 {service_name} 缺少实现配置")
        
        # 验证依赖配置
        dependencies_config = config.get("dependencies", {})
        for category, services in dependencies_config.items():
            if not isinstance(services, list):
                errors.append(f"依赖配置 {category} 必须是列表类型")
        
        return errors
    
    def get_assembly_plan(self) -> Dict[str, Any]:
        """获取组装计划
        
        Returns:
            Dict[str, Any]: 组装计划
        """
        return {
            "assembly_order": self._assembly_order,
            "dependency_graph": {
                k: list(v) for k, v in self._dependency_graph.items()
            },
            "resolved_types": list(self._resolved_types.keys())
        }
    
    def _build_assembly_plan(self, config: Dict[str, Any]) -> None:
        """构建组装计划
        
        Args:
            config: 配置字典
        """
        self._assembly_plan = config.copy()
        
        # 预解析所有类型
        services_config = config.get("services", {})
        for service_name in services_config.keys():
            self._resolve_type(service_name)
    
    def _resolve_dependency_graph(self) -> None:
        """解析依赖关系图"""
        self._dependency_graph.clear()
        
        services_config = self._assembly_plan.get("services", {})
        for service_name, service_config in services_config.items():
            dependencies = service_config.get("dependencies", [])
            self._dependency_graph[service_name] = set(dependencies)
    
    def _determine_assembly_order(self) -> None:
        """确定组装顺序（拓扑排序）"""
        # 简单的拓扑排序实现
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node: str) -> None:
            if node in temp_visited:
                raise CircularDependencyError(f"检测到循环依赖: {node}")
            if node in visited:
                return
            
            temp_visited.add(node)
            for dependency in self._dependency_graph.get(node, []):
                visit(dependency)
            temp_visited.remove(node)
            visited.add(node)
            order.append(node)
        
        for node in self._dependency_graph:
            if node not in visited:
                visit(node)
        
        self._assembly_order = order
    
    def _resolve_type(self, type_name: str) -> Optional[Type]:
        """解析类型名称为类型对象
        
        Args:
            type_name: 类型名称
            
        Returns:
            Optional[Type]: 类型对象，如果解析失败则返回None
        """
        if type_name in self._resolved_types:
            return self._resolved_types[type_name]
        
        try:
            # 分割模块路径和类名
            parts = type_name.split(".")
            if len(parts) < 2:
                return None
            
            module_path = ".".join(parts[:-1])
            class_name = parts[-1]
            
            # 导入模块
            module = importlib.import_module(module_path)
            
            # 获取类
            cls = getattr(module, class_name)
            
            # 缓存结果
            self._resolved_types[type_name] = cls
            
            return cls
        except (ImportError, AttributeError) as e:
            logger.warning(f"无法解析类型 {type_name}: {e}")
            return None
    
    def _parse_lifetime(self, lifetime_str: str) -> str:
        """解析生命周期字符串
        
        Args:
            lifetime_str: 生命周期字符串
            
        Returns:
            str: 生命周期常量
        """
        lifetime_map = {
            "singleton": ServiceLifetime.SINGLETON,
            "scoped": ServiceLifetime.SCOPED,
            "transient": ServiceLifetime.TRANSIENT
        }
        return lifetime_map.get(lifetime_str.lower(), ServiceLifetime.SINGLETON)
    
    def _auto_register_service(self, service_type: Type, lifetime: str) -> None:
        """自动注册服务
        
        Args:
            service_type: 服务类型
            lifetime: 生命周期
        """
        try:
            # 尝试查找默认实现
            implementation_name = service_type.__module__ + ".impl." + service_type.__name__
            implementation_type = self._resolve_type(implementation_name)
            
            if implementation_type:
                self.container.register(
                    interface=service_type,
                    implementation=implementation_type,
                    lifetime=lifetime
                )
                logger.debug(f"自动注册服务: {service_type.__name__}")
            else:
                # 如果找不到实现，注册自身
                self.container.register(
                    interface=service_type,
                    implementation=service_type,
                    lifetime=lifetime
                )
                logger.debug(f"自动注册服务（自身）: {service_type.__name__}")
        except Exception as e:
            logger.warning(f"自动注册服务 {service_type.__name__} 失败: {e}")
    
    def _execute_startup_hooks(self, config: Dict[str, Any]) -> None:
        """执行启动钩子
        
        Args:
            config: 配置字典
        """
        startup_config = config.get("startup", {})
        hooks_config = startup_config.get("hooks", {})
        
        # 执行启动前钩子
        before_hooks = hooks_config.get("before_startup", [])
        for hook_name in before_hooks:
            try:
                self._execute_hook(hook_name)
                logger.debug(f"执行启动前钩子: {hook_name}")
            except Exception as e:
                logger.warning(f"执行启动前钩子 {hook_name} 失败: {e}")
        
        # 执行启动后钩子
        after_hooks = hooks_config.get("after_startup", [])
        for hook_name in after_hooks:
            try:
                self._execute_hook(hook_name)
                logger.debug(f"执行启动后钩子: {hook_name}")
            except Exception as e:
                logger.warning(f"执行启动后钩子 {hook_name} 失败: {e}")
    
    def _execute_hook(self, hook_name: str) -> None:
        """执行钩子
        
        Args:
            hook_name: 钩子名称
        """
        # 这里可以实现具体的钩子逻辑
        # 例如：validate_configuration, initialize_logging等
        if hook_name == "validate_configuration":
            # 配置验证逻辑
            pass
        elif hook_name == "initialize_logging":
            # 日志初始化逻辑
            pass
        elif hook_name == "register_signal_handlers":
            # 信号处理器注册逻辑
            pass
        elif hook_name == "start_background_tasks":
            # 后台任务启动逻辑
            pass
        else:
            logger.warning(f"未知的钩子: {hook_name}")