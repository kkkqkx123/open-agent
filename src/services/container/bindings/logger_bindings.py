"""日志服务依赖注入绑定配置

统一注册日志相关服务，包括ILogger接口和LogRedactor等。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
"""

import sys
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager

from src.interfaces.logger import ILogger, IBaseHandler, ILogRedactor, ILoggerFactory, LogLevel
from src.interfaces.container.core import ServiceLifetime
from src.services.container.core.base_service_bindings import BaseServiceBindings


class LoggerLifecycleManager:
    """日志系统生命周期管理器"""
    
    def __init__(self) -> None:
        self._shutdown_handlers: List[Callable] = []
        self._is_shutdown = False
    
    def register_shutdown_handler(self, handler: Callable) -> None:
        """注册关闭处理器"""
        if not self._is_shutdown:
            self._shutdown_handlers.append(handler)
    
    def shutdown(self) -> None:
        """优雅关闭日志系统"""
        if self._is_shutdown:
            return
        
        self._is_shutdown = True
        
        # 执行所有关闭处理器
        for handler in reversed(self._shutdown_handlers):
            try:
                handler()
            except Exception as e:
                print(f"[ERROR] 关闭处理器执行失败: {e}", file=sys.stderr)
        
        self._shutdown_handlers.clear()


# 全局生命周期管理器实例
_lifecycle_manager = LoggerLifecycleManager()

class LoggerServiceBindings(BaseServiceBindings):
    """日志服务绑定类
    
    负责注册所有日志相关服务，包括：
    - ILoggerFactory
    - ILogRedactor
    - IBaseHandler列表
    - ILogger服务
    
    重构后使用接口依赖，避免循环依赖。
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证日志配置"""
        errors = []
        
        # 验证日志级别
        log_level = config.get("log_level", "INFO")
        try:
            LogLevel.from_string(log_level)
        except ValueError:
            valid_levels = [level.value for level in LogLevel]
            errors.append(f"无效的日志级别: {log_level}，有效值: {valid_levels}")
        
        # 验证日志输出配置
        log_outputs = config.get("log_outputs", [])
        if not isinstance(log_outputs, list):
            errors.append("log_outputs必须是列表类型")
        else:
            for i, output in enumerate(log_outputs):
                if not isinstance(output, dict):
                    errors.append(f"log_outputs[{i}]必须是字典类型")
                    continue
                
                # 验证输出类型
                output_type = output.get("type")
                if not output_type:
                    errors.append(f"log_outputs[{i}]缺少type字段")
                elif output_type not in ["console", "file", "json"]:
                    errors.append(f"log_outputs[{i}]无效的type: {output_type}")
                
                # 验证文件输出配置
                if output_type == "file" and not output.get("filename"):
                    errors.append(f"log_outputs[{i}]文件输出缺少filename配置")
        
        # 验证脱敏配置
        redactor_config = config.get("log_redactor", {})
        if redactor_config and not isinstance(redactor_config, dict):
            errors.append("log_redactor必须是字典类型")
        elif redactor_config:
            patterns = redactor_config.get("patterns")
            if patterns is not None and not isinstance(patterns, list):
                errors.append("log_redactor.patterns必须是列表类型")
        
        # 验证业务配置
        business_config = config.get("business_config", {})
        if business_config and not isinstance(business_config, dict):
            errors.append("business_config必须是字典类型")
        elif business_config:
            # 验证审计关键词
            audit_keywords = business_config.get("audit_keywords")
            if audit_keywords is not None and not isinstance(audit_keywords, list):
                errors.append("business_config.audit_keywords必须是列表类型")
            
            # 验证业务规则
            business_rules = business_config.get("business_rules")
            if business_rules is not None and not isinstance(business_rules, list):
                errors.append("business_config.business_rules必须是列表类型")
        
        if errors:
            raise ValueError(f"日志配置验证失败: {errors}")
    
    def _do_register_services(
        self, 
        container: Any, 
        config: Dict[str, Any], 
        environment: str = "default"
    ) -> None:
        """执行日志服务注册"""
        _register_logger_factory(container, config, environment)
        _register_log_redactor(container, config, environment)
        _register_handlers(container, config, environment)
        _register_logger_service(container, config, environment)
    
    def _post_register(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 为日志服务设置注入层
            self.setup_service_injection(
                container,
                ILogger,
                self._create_fallback_logger
            )
            
            # 设置全局logger实例（向后兼容）
            logger_instance = container.get(ILogger)
            from src.services.logger.injection import set_logger_instance
            set_logger_instance(logger_instance)
            
            if logger_instance:
                logger_instance.debug(f"已设置logger实例和注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置logger注入层失败: {e}", file=sys.stderr)
    
    def _create_fallback_logger(self) -> ILogger:
        """创建fallback logger"""
        from src.services.logger.injection import _StubLogger
        return _StubLogger()


def _register_logger_factory(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册日志工厂"""
    # 延迟导入具体实现，避免循环依赖
    def create_logger_factory() -> ILoggerFactory:
        from src.infrastructure.logger.factory.logger_factory import LoggerFactory
        return LoggerFactory()
    
    container.register_factory(
        ILoggerFactory,
        create_logger_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )


def _register_log_redactor(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册日志脱敏器"""
    redactor_config = config.get("log_redactor", {})
    
    def redactor_factory() -> ILogRedactor:
        # 延迟导入具体实现，避免循环依赖
        if redactor_config:
            from src.infrastructure.logger.core.redactor import CustomLogRedactor
            return CustomLogRedactor(redactor_config)
        
        secret_patterns = config.get("secret_patterns", [])
        if secret_patterns:
            from src.infrastructure.logger.core.redactor import LogRedactor
            redactor = LogRedactor()
            for pattern in secret_patterns:
                redactor.add_pattern(pattern)
            return redactor
        
        from src.infrastructure.logger.core.redactor import LogRedactor
        return LogRedactor()
    
    container.register_factory(
        ILogRedactor,
        redactor_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )


def _register_handlers(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册日志处理器"""
    def handlers_factory() -> List[IBaseHandler]:
        logger_factory = container.get(ILoggerFactory)
        handlers: List[IBaseHandler] = []
        log_outputs = config.get("log_outputs", [{"type": "console"}])
        
        for output_config in log_outputs:
            handler = _create_handler_from_config(output_config, logger_factory)
            if handler:
                handlers.append(handler)
        
        return handlers
    
    container.register_factory(
        List[IBaseHandler],
        handlers_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )


def _create_handler_from_config(output_config: Dict[str, Any], logger_factory: ILoggerFactory) -> Optional[IBaseHandler]:
    """根据配置创建处理器"""
    handler_type = output_config.get("type", "console")
    handler_level_str = output_config.get("level", "INFO")
    handler_level = LogLevel.from_string(handler_level_str)
    
    if handler_type == "console":
        formatter_name = output_config.get("formatter", "color")
        use_colors = output_config.get("use_colors")
        return logger_factory.create_console_handler(handler_level, formatter_name, use_colors)
    
    elif handler_type == "file":
        filename = output_config.get("filename", "logs/app.log")
        formatter_name = output_config.get("formatter", "text")
        encoding = output_config.get("encoding", "utf-8")
        max_bytes = output_config.get("max_bytes")
        backup_count = output_config.get("backup_count", 0)
        return logger_factory.create_file_handler(
            filename, handler_level, formatter_name, encoding, max_bytes, backup_count
        )
    
    elif handler_type == "json":
        filename = output_config.get("filename", "logs/app.json")
        encoding = output_config.get("encoding", "utf-8")
        max_bytes = output_config.get("max_bytes")
        backup_count = output_config.get("backup_count", 0)
        ensure_ascii = output_config.get("ensure_ascii", False)
        indent = output_config.get("indent")
        sort_keys = output_config.get("sort_keys", False)
        return logger_factory.create_json_handler(
            filename, handler_level, encoding, max_bytes, backup_count,
            ensure_ascii, indent, sort_keys
        )
    
    return None


def _register_logger_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册Logger服务"""
    def logger_factory() -> ILogger:
        # 延迟导入具体实现，避免循环依赖
        from src.services.logger.logger_service import LoggerService
        
        logger_factory_instance = container.get(ILoggerFactory)
        redactor = container.get(ILogRedactor)
        handlers = container.get(List[IBaseHandler])
        
        logger_name = f"{environment}_application"
        infra_logger = logger_factory_instance.create_logger(
            name=logger_name,
            handlers=handlers,
            redactor=redactor,
            config=config
        )
        
        business_config = config.get("business_config", {})
        return LoggerService(logger_name, infra_logger, business_config)
    
    container.register_factory(
        ILogger,
        logger_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )

