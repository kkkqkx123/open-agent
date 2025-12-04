"""日志服务依赖注入绑定配置

统一注册日志相关服务，包括ILogger接口和LogRedactor等。
更新后使用基础设施层的组件。
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING

from src.interfaces.logger import ILogger, IBaseHandler, ILogRedactor, LogLevel
from src.interfaces.common_infra import ServiceLifetime
from src.services.logger.logger_service import LoggerService
from src.infrastructure.logger.core.redactor import LogRedactor, CustomLogRedactor
from src.infrastructure.logger.factory.logger_factory import LoggerFactory

if TYPE_CHECKING:
    pass


def register_logger_services(container, config: Dict[str, Any], environment: str = "default") -> None:
    """注册日志相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    
    示例配置:
    ```yaml
    log_level: "INFO"
    log_outputs:
      - type: "console"
        level: "INFO"
        formatter: "color"
      - type: "file"
        level: "DEBUG"
        formatter: "json"
        filename: "logs/app.log"
        max_bytes: 10485760
        backup_count: 5
    
    log_redactor:
      hash_sensitive: false
      patterns:
        - pattern: "custom_pattern"
          replacement: "***CUSTOM***"
    
    business_config:
      enable_audit: true
      audit_keywords: ["login", "logout", "auth"]
      enable_business_filter: true
      business_rules:
        - type: "level_filter"
          min_level: "INFO"
    ```
    """
    try:
        # 注册日志工厂
        register_logger_factory(container, config, environment)
        
        # 注册日志脱敏器
        register_log_redactor(container, config, environment)
        
        # 注册日志处理器
        register_handlers(container, config, environment)
        
        # 注册Logger服务
        register_logger_service(container, config, environment)
        
    except Exception as e:
        # 避免在注册过程中使用logger，直接输出
        print(f"注册日志服务失败: {e}")
        raise


def register_logger_factory(container, config: Dict[str, Any], environment: str = "default") -> None:
    """注册日志工厂"""
    
    def logger_factory_factory() -> LoggerFactory:
        """创建日志工厂实例"""
        return LoggerFactory()
    
    # 注册日志工厂为单例
    container.register_factory(
        LoggerFactory,
        logger_factory_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )


def register_log_redactor(container, config: Dict[str, Any], environment: str = "default") -> None:
    """注册日志脱敏器"""
    
    # 获取脱敏配置
    redactor_config = config.get("log_redactor", {})
    
    # 创建脱敏器工厂函数
    def redactor_factory() -> ILogRedactor:
        if redactor_config:
            # 使用自定义脱敏器
            return CustomLogRedactor(redactor_config)
        else:
            # 使用默认脱敏器，但从全局配置中获取敏感模式
            secret_patterns = config.get("secret_patterns", [])
            if secret_patterns:
                # 创建带有自定义模式的默认脱敏器
                redactor = LogRedactor()
                for pattern in secret_patterns:
                    redactor.add_pattern(pattern)
                return redactor
            return LogRedactor()
    
    # 注册脱敏器为单例
    container.register_factory(
        ILogRedactor,
        redactor_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )


def register_handlers(container, config: Dict[str, Any], environment: str = "default") -> None:
    """注册日志处理器"""
    
    def handlers_factory() -> List[IBaseHandler]:
        """创建处理器列表"""
        # 获取日志工厂
        logger_factory = container.get(LoggerFactory)
        
        # 从配置创建处理器
        handlers = []
        log_outputs = config.get("log_outputs", [{"type": "console"}])
        
        for output_config in log_outputs:
            handler = create_handler_from_config(output_config, logger_factory)
            if handler:
                handlers.append(handler)
        
        return handlers
    
    # 注册处理器列表为单例
    container.register_factory(
        List[IBaseHandler],
        handlers_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )


def create_handler_from_config(output_config: Dict[str, Any], logger_factory: LoggerFactory) -> Optional[IBaseHandler]:
    """根据配置创建处理器
    
    Args:
        output_config: 输出配置
        logger_factory: 日志工厂实例
        
    Returns:
        处理器实例或None
    """
    handler_type = output_config.get("type", "console")
    handler_level_str = output_config.get("level", "INFO")
    handler_level = _log_level_from_string(handler_level_str)
    
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
    
    else:
        # 跳过未知类型的处理器
        return None


def _log_level_from_string(level_str: str) -> LogLevel:
    """从字符串创建日志级别"""
    return LogLevel.from_string(level_str)


def register_logger_service(container, config: Dict[str, Any], environment: str = "default") -> None:
    """注册Logger服务"""
    
    def logger_factory() -> ILogger:
        # 获取日志工厂
        logger_factory_instance = container.get(LoggerFactory)
        
        # 获取脱敏器
        redactor = container.get(ILogRedactor)
        
        # 获取处理器列表
        handlers = container.get(List[IBaseHandler])
        
        # 创建基础设施层日志记录器
        logger_name = f"{environment}_application"
        infra_logger = logger_factory_instance.create_logger(
            name=logger_name,
            handlers=handlers,
            config=config
        )
        
        # 创建业务层日志服务
        business_config = config.get("business_config", {})
        return LoggerService(logger_name, infra_logger, business_config)
    
    # 注册LoggerService为单例
    container.register_factory(
        ILogger,
        logger_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )


def register_test_logger_services(container, config: Optional[Dict[str, Any]] = None) -> None:
    """注册测试环境的日志服务
    
    Args:
        container: 依赖注入容器
        config: 测试配置，如果为None则使用默认测试配置
    """
    
    # 默认测试配置
    if config is None:
        config = {
            "log_level": "DEBUG",
            "log_outputs": [
                {
                    "type": "console",
                    "level": "DEBUG",
                    "formatter": "color"
                }
            ],
            "secret_patterns": [
                "sk-[a-zA-Z0-9]{20,}",
                "\\w+@\\w+\\.\\w+"
            ],
            "business_config": {
                "enable_audit": False,
                "enable_business_filter": False
            }
        }
    
    # 注册测试环境服务
    register_logger_services(container, config, environment="test")


def register_production_logger_services(container, config: Dict[str, Any]) -> None:
    """注册生产环境的日志服务
    
    Args:
        container: 依赖注入容器
        config: 生产环境配置
    """
    
    # 确保生产环境配置合理
    production_config = config.copy()
    
    # 生产环境默认使用INFO级别
    if "log_level" not in production_config:
        production_config["log_level"] = "INFO"
    
    # 确保有日志输出配置
    if "log_outputs" not in production_config:
        production_config["log_outputs"] = [
            {
                "type": "file",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/production.log",
                "max_bytes": 52428800,  # 50MB
                "backup_count": 10
            }
        ]
    
    # 生产环境业务配置
    if "business_config" not in production_config:
        production_config["business_config"] = {
            "enable_audit": True,
            "audit_keywords": ["login", "logout", "auth", "payment", "admin"],
            "enable_business_filter": True,
            "business_rules": [
                {
                    "type": "level_filter",
                    "min_level": "INFO"
                }
            ]
        }
    
    # 注册生产环境服务
    register_logger_services(container, production_config, environment="production")


def register_development_logger_services(container, config: Dict[str, Any]) -> None:
    """注册开发环境的日志服务
    
    Args:
        container: 依赖注入容器
        config: 开发环境配置
    """
    
    # 确保开发环境配置合理
    development_config = config.copy()
    
    # 开发环境默认使用DEBUG级别
    if "log_level" not in development_config:
        development_config["log_level"] = "DEBUG"
    
    # 确保有控制台输出
    if "log_outputs" not in development_config:
        development_config["log_outputs"] = [
            {
                "type": "console",
                "level": "DEBUG",
                "formatter": "color"
            }
        ]
    
    # 开发环境业务配置
    if "business_config" not in development_config:
        development_config["business_config"] = {
            "enable_audit": True,
            "audit_keywords": ["login", "logout", "auth"],
            "enable_business_filter": False
        }
    
    # 注册开发环境服务
    register_logger_services(container, development_config, environment="development")


def get_logger_service_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """获取日志服务配置摘要
    
    Args:
        config: 完整配置字典
        
    Returns:
        Dict[str, Any]: 日志服务配置摘要
    """
    return {
        "log_level": config.get("log_level", "INFO"),
        "log_outputs_count": len(config.get("log_outputs", [])),
        "has_secret_patterns": bool(config.get("secret_patterns")),
        "has_custom_redactor": bool(config.get("log_redactor")),
        "redactor_hash_sensitive": config.get("log_redactor", {}).get("hash_sensitive", False),
        "has_business_config": bool(config.get("business_config")),
        "audit_enabled": config.get("business_config", {}).get("enable_audit", False),
        "business_filter_enabled": config.get("business_config", {}).get("enable_business_filter", False)
    }


def validate_logger_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """验证日志服务配置
    
    Args:
        config: 配置字典
        
    Returns:
        tuple[bool, list[str]]: (是否有效, 错误列表)
    """
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
    
    return len(errors) == 0, errors