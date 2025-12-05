"""日志依赖注入容器使用示例

展示如何使用优化后的日志依赖注入容器。
"""

from src.services.container import (
    get_global_container,
    LoggerServiceBindings
)
from src.interfaces.logger import ILogger


def example_basic_usage():
    """基本使用示例"""
    # 获取全局容器
    container = get_global_container()
    
    # 日志配置
    logger_config = {
        "log_level": "INFO",
        "log_outputs": [
            {
                "type": "console",
                "level": "INFO",
                "formatter": "color"
            },
            {
                "type": "file",
                "level": "DEBUG",
                "formatter": "json",
                "filename": "logs/app.log",
                "max_bytes": 10485760,
                "backup_count": 5
            }
        ],
        "secret_patterns": [
            "sk-[a-zA-Z0-9]{20,}",
            "\\w+@\\w+\\.\\w+"
        ],
        "business_config": {
            "enable_audit": True,
            "audit_keywords": ["login", "logout", "auth"],
            "enable_business_filter": True,
            "business_rules": [
                {
                    "type": "level_filter",
                    "min_level": "INFO"
                }
            ]
        }
    }
    
    # 设置全局日志服务（推荐方式）
    logger_bindings = LoggerServiceBindings()
    logger_bindings.register_services(container, logger_config, environment="production")
    
    # 获取日志服务
    logger = container.get(ILogger)
    
    # 使用日志服务
    logger.info("应用启动成功")
    logger.error("这是一个错误消息", user_id="123", action="login")


def example_environment_specific():
    """环境特定配置示例"""
    container = get_global_container()
    
    # 开发环境配置
    dev_config = {
        "log_level": "DEBUG",
        "log_outputs": [
            {
                "type": "console",
                "level": "DEBUG",
                "formatter": "color"
            }
        ]
    }
    
    # 使用开发环境配置
    logger_bindings = LoggerServiceBindings()
    logger_bindings.register_services(container, dev_config, environment="development")
    
    logger = container.get(ILogger)
    logger.debug("开发环境调试信息")


def example_test_isolation():
    """测试隔离示例"""
    container = get_global_container()
    
    # 使用隔离的测试日志环境
    test_config = {
        "log_level": "DEBUG",
        "log_outputs": [{"type": "console", "level": "DEBUG"}]
    }
    
    # 使用测试环境注册日志服务
    logger_bindings = LoggerServiceBindings()
    logger_bindings.register_services(container, test_config, environment="test_example")
    
    logger = container.get(ILogger)
    logger.info("测试环境的日志消息")


def example_manual_test_setup():
    """手动测试设置示例"""
    container = get_global_container()
    
    # 手动注册测试日志服务
    test_config = {
        "log_level": "DEBUG",
        "log_outputs": [
            {
                "type": "console",
                "level": "DEBUG",
                "formatter": "color"
            }
        ],
        "business_config": {
            "enable_audit": False,
            "enable_business_filter": False
        }
    }
    
    # 使用测试环境注册日志服务
    logger_bindings = LoggerServiceBindings()
    logger_bindings.register_services(container, test_config, environment="my_test")
    
    logger = container.get(ILogger)
    logger.debug("测试日志消息")


def example_lifecycle_management():
    """生命周期管理示例"""
    # 设置日志服务
    container = get_global_container()
    config = {
        "log_level": "INFO",
        "log_outputs": [{"type": "console", "level": "INFO"}]
    }
    
    logger_bindings = LoggerServiceBindings()
    logger_bindings.register_services(container, config)
    
    # 应用逻辑
    logger = container.get(ILogger)
    logger.info("应用运行中...")
    
    print("日志服务已设置并运行")


def example_error_handling():
    """错误处理示例"""
    container = get_global_container()
    
    # 无效配置
    invalid_config = {
        "log_level": "INVALID_LEVEL",  # 无效的日志级别
        "log_outputs": "not_a_list"    # 应该是列表
    }
    
    try:
        logger_bindings = LoggerServiceBindings()
        logger_bindings.register_services(container, invalid_config)
    except ValueError as e:
        print(f"配置验证失败: {e}")
        
        # 使用默认配置
        default_config = {
            "log_level": "INFO",
            "log_outputs": [{"type": "console", "level": "INFO"}]
        }
        logger_bindings = LoggerServiceBindings()
        logger_bindings.register_services(container, default_config)


if __name__ == "__main__":
    """运行所有示例"""
    print("=== 基本使用示例 ===")
    example_basic_usage()
    
    print("\n=== 环境特定配置示例 ===")
    example_environment_specific()
    
    print("\n=== 测试隔离示例 ===")
    example_test_isolation()
    
    print("\n=== 手动测试设置示例 ===")
    example_manual_test_setup()
    
    print("\n=== 生命周期管理示例 ===")
    example_lifecycle_management()
    
    print("\n=== 错误处理示例 ===")
    example_error_handling()