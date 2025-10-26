"""应用程序启动器

提供完整的应用启动流程，支持环境特定的配置覆盖和健康检查。
"""

import os
import sys
import logging
import signal
import threading
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from src.infrastructure.container import get_global_container
from infrastructure.container import EnhancedDependencyContainer
from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.assembler import ComponentAssembler, AssemblyError
from src.infrastructure.exceptions import InfrastructureError

logger = logging.getLogger(__name__)


class ApplicationBootstrap:
    """应用程序启动器
    
    负责应用程序的完整启动流程，包括配置加载、组件组装、
    依赖注入设置和健康检查等。
    """
    
    def __init__(self, config_path: str = "configs/application.yaml"):
        """初始化应用启动器
        
        Args:
            config_path: 应用配置文件路径
        """
        self.config_path = config_path
        self.container = EnhancedDependencyContainer()
        self.config_loader = YamlConfigLoader()
        self.assembler = ComponentAssembler(self.container, self.config_loader)
        self._shutdown_handlers: List[Callable] = []
        self._background_threads: List[threading.Thread] = []
        self._is_running = False
        self._startup_time: Optional[float] = None
        
        # 注册信号处理器
        self._register_signal_handlers()
        
        logger.info(f"ApplicationBootstrap初始化完成，配置路径: {config_path}")
    
    def bootstrap(self) -> DependencyContainer:
        """启动应用程序
        
        Returns:
            DependencyContainer: 配置完成的依赖注入容器
            
        Raises:
            InfrastructureError: 启动失败时抛出
        """
        try:
            import time
            start_time = time.time()
            
            logger.info("开始应用程序启动流程")
            
            # 1. 加载应用配置
            app_config = self._load_application_config()
            
            # 2. 设置环境
            self._setup_environment(app_config)
            
            # 3. 初始化日志系统
            self._initialize_logging(app_config)
            
            # 4. 执行启动前钩子
            self._execute_pre_startup_hooks(app_config)
            
            # 5. 组装组件
            self._assemble_components(app_config)
            
            # 6. 注册全局容器
            self._register_global_container()
            
            # 7. 启动后台任务
            self._start_background_tasks(app_config)
            
            # 8. 执行启动后钩子
            self._execute_post_startup_hooks(app_config)
            
            # 9. 执行健康检查
            self._perform_health_checks(app_config)
            
            # 10. 标记为运行中
            self._is_running = True
            self._startup_time = time.time() - start_time
            
            logger.info(f"应用程序启动完成，耗时: {self._startup_time:.2f}秒")
            return self.container
            
        except Exception as e:
            logger.error(f"应用程序启动失败: {e}")
            self._shutdown()
            raise InfrastructureError(f"应用程序启动失败: {e}")
    
    def shutdown(self) -> None:
        """关闭应用程序"""
        logger.info("开始应用程序关闭流程")
        self._shutdown()
        logger.info("应用程序关闭完成")
    
    def is_running(self) -> bool:
        """检查应用程序是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        return self._is_running
    
    def get_startup_time(self) -> Optional[float]:
        """获取启动时间
        
        Returns:
            Optional[float]: 启动时间（秒），如果未启动则返回None
        """
        return self._startup_time
    
    def add_shutdown_handler(self, handler: Callable) -> None:
        """添加关闭处理器
        
        Args:
            handler: 关闭处理器函数
        """
        self._shutdown_handlers.append(handler)
    
    def _load_application_config(self) -> Dict[str, Any]:
        """加载应用配置
        
        Returns:
            Dict[str, Any]: 应用配置
        """
        try:
            config = self.config_loader.load(self.config_path)
            logger.info(f"成功加载应用配置: {self.config_path}")
            return config
        except Exception as e:
            raise InfrastructureError(f"加载应用配置失败: {e}")
    
    def _setup_environment(self, config: Dict[str, Any]) -> None:
        """设置环境
        
        Args:
            config: 应用配置
        """
        # 获取环境配置
        app_config = config.get("application", {})
        env = app_config.get("environment", "development")
        
        # 设置容器环境
        self.container.set_environment(env)
        
        # 设置环境变量
        env_prefix = app_config.get("env_prefix", "AGENT_")
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # 设置环境特定的配置覆盖
                config_key = key[len(env_prefix):].lower()
                if config_key not in config:
                    config[config_key] = value
        
        logger.info(f"环境设置完成: {env}")
    
    def _initialize_logging(self, config: Dict[str, Any]) -> None:
        """初始化日志系统
        
        Args:
            config: 应用配置
        """
        # 获取日志配置
        environments = config.get("environments", {})
        current_env = self.container.get_environment()
        env_config = environments.get(current_env, {})
        
        log_level = env_config.get("log_level", "INFO")
        
        # 配置根日志器
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger.info(f"日志系统初始化完成，级别: {log_level}")
    
    def _execute_pre_startup_hooks(self, config: Dict[str, Any]) -> None:
        """执行启动前钩子
        
        Args:
            config: 应用配置
        """
        startup_config = config.get("startup", {})
        hooks_config = startup_config.get("hooks", {})
        before_hooks = hooks_config.get("before_startup", [])
        
        for hook_name in before_hooks:
            try:
                self._execute_hook(hook_name, config)
                logger.debug(f"执行启动前钩子: {hook_name}")
            except Exception as e:
                logger.warning(f"执行启动前钩子 {hook_name} 失败: {e}")
    
    def _assemble_components(self, config: Dict[str, Any]) -> None:
        """组装组件
        
        Args:
            config: 应用配置
        """
        try:
            self.container = self.assembler.assemble(config)
            logger.info("组件组装完成")
        except AssemblyError as e:
            raise InfrastructureError(f"组件组装失败: {e}")
    
    def _register_global_container(self) -> None:
        """注册全局容器"""
        # 设置全局容器实例
        import src.infrastructure.container as container_module
        container_module._global_container = self.container
        
        logger.info("全局容器注册完成")
    
    def _start_background_tasks(self, config: Dict[str, Any]) -> None:
        """启动后台任务
        
        Args:
            config: 应用配置
        """
        startup_config = config.get("startup", {})
        auto_register = startup_config.get("auto_register", [])
        
        # 自动注册组件
        if "workflow_templates" in auto_register:
            self._register_workflow_templates()
        
        if "agent_types" in auto_register:
            self._register_agent_types()
        
        if "tool_types" in auto_register:
            self._register_tool_types()
        
        logger.info("后台任务启动完成")
    
    def _execute_post_startup_hooks(self, config: Dict[str, Any]) -> None:
        """执行启动后钩子
        
        Args:
            config: 应用配置
        """
        startup_config = config.get("startup", {})
        hooks_config = startup_config.get("hooks", {})
        after_hooks = hooks_config.get("after_startup", [])
        
        for hook_name in after_hooks:
            try:
                self._execute_hook(hook_name, config)
                logger.debug(f"执行启动后钩子: {hook_name}")
            except Exception as e:
                logger.warning(f"执行启动后钩子 {hook_name} 失败: {e}")
    
    def _perform_health_checks(self, config: Dict[str, Any]) -> None:
        """执行健康检查
        
        Args:
            config: 应用配置
        """
        startup_config = config.get("startup", {})
        health_config = startup_config.get("health_check", {})
        
        if not health_config.get("enabled", False):
            logger.info("健康检查已禁用")
            return
        
        # 检查关键服务
        critical_services = [
            "IConfigLoader",
            "ILLMFactory",
            "IToolManager",
            "IAgentFactory"
        ]
        
        for service_name in critical_services:
            try:
                service_type = self.assembler._resolve_type(service_name)
                if service_type and self.container.has_service(service_type):
                    instance = self.container.get(service_type)
                    logger.debug(f"健康检查通过: {service_name}")
                else:
                    logger.warning(f"健康检查失败: {service_name} 未注册")
            except Exception as e:
                logger.error(f"健康检查失败: {service_name} - {e}")
        
        logger.info("健康检查完成")
    
    def _execute_hook(self, hook_name: str, config: Dict[str, Any]) -> None:
        """执行钩子
        
        Args:
            hook_name: 钩子名称
            config: 应用配置
        """
        if hook_name == "validate_configuration":
            self._hook_validate_configuration(config)
        elif hook_name == "initialize_logging":
            # 日志已在_initialize_logging中初始化
            pass
        elif hook_name == "register_signal_handlers":
            # 信号处理器已在__init__中注册
            pass
        elif hook_name == "start_background_tasks":
            # 后台任务已在_start_background_tasks中启动
            pass
        else:
            logger.warning(f"未知的钩子: {hook_name}")
    
    def _hook_validate_configuration(self, config: Dict[str, Any]) -> None:
        """验证配置钩子
        
        Args:
            config: 应用配置
        """
        # 验证版本兼容性
        version = config.get("version", "1.0")
        if not version:
            raise InfrastructureError("缺少版本信息")
        
        # 验证必需的配置项
        required_sections = ["application", "assembly", "dependencies"]
        for section in required_sections:
            if section not in config:
                raise InfrastructureError(f"缺少必需的配置节: {section}")
        
        logger.info("配置验证通过")
    
    def _register_workflow_templates(self) -> None:
        """注册工作流模板"""
        try:
            from src.application.workflow.templates.registry import get_global_template_registry
            registry = get_global_template_registry()
            
            # 注册到容器
            from src.application.workflow.interfaces import IWorkflowTemplateRegistry
            self.container.register_instance(IWorkflowTemplateRegistry, registry)
            
            logger.info("工作流模板注册完成")
        except Exception as e:
            logger.warning(f"注册工作流模板失败: {e}")
    
    def _register_agent_types(self) -> None:
        """注册Agent类型"""
        try:
            from src.domain.agent.factory import AgentFactory
            from src.domain.agent.interfaces import IAgentFactory
            
            # 注册Agent工厂
            if not self.container.has_service(IAgentFactory):
                llm_factory = self.container.get(self.assembler._resolve_type("ILLMFactory"))
                tool_executor = self.container.get(self.assembler._resolve_type("IToolExecutor"))
                
                agent_factory = AgentFactory(llm_factory, tool_executor)
                self.container.register_instance(IAgentFactory, agent_factory)
            
            logger.info("Agent类型注册完成")
        except Exception as e:
            logger.warning(f"注册Agent类型失败: {e}")
    
    def _register_tool_types(self) -> None:
        """注册工具类型"""
        try:
            # 这里可以添加工具类型的注册逻辑
            logger.info("工具类型注册完成")
        except Exception as e:
            logger.warning(f"注册工具类型失败: {e}")
    
    def _register_signal_handlers(self) -> None:
        """注册信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}，开始关闭应用程序")
            self.shutdown()
        
        # 注册常见信号
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 在Windows上，SIGBREAK可能不可用
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def _shutdown(self) -> None:
        """关闭应用程序"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # 执行关闭处理器
        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.warning(f"执行关闭处理器失败: {e}")
        
        # 停止后台线程
        for thread in self._background_threads:
            if thread.is_alive():
                # 这里应该实现优雅的线程停止逻辑
                logger.debug(f"等待后台线程结束: {thread.name}")
                thread.join(timeout=5.0)
                if thread.is_alive():
                    logger.warning(f"后台线程未能在超时时间内结束: {thread.name}")
        
        # 清理容器
        self.container.clear()


# 全局启动器实例
_global_bootstrap: Optional[ApplicationBootstrap] = None


def get_global_bootstrap() -> ApplicationBootstrap:
    """获取全局启动器实例
    
    Returns:
        ApplicationBootstrap: 全局启动器实例
    """
    global _global_bootstrap
    if _global_bootstrap is None:
        _global_bootstrap = ApplicationBootstrap()
    return _global_bootstrap


def bootstrap_application(config_path: str = "configs/application.yaml") -> DependencyContainer:
    """启动应用程序的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        DependencyContainer: 配置完成的依赖注入容器
    """
    bootstrap = ApplicationBootstrap(config_path)
    return bootstrap.bootstrap()


def shutdown_application() -> None:
    """关闭应用程序的便捷函数"""
    global _global_bootstrap
    if _global_bootstrap:
        _global_bootstrap.shutdown()