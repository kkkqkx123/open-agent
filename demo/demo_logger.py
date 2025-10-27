#!/usr/bin/env python3
"""日志系统与配置系统集成演示"""

import os
import sys
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.infrastructure.container import DependencyContainer
from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.config.config_system import ConfigSystem
from src.infrastructure.config.config_merger import ConfigMerger
from src.infrastructure.config.config_validator import ConfigValidator
from src.infrastructure.logger import (
    get_logger,
    initialize_logging_integration,
    get_global_error_handler,
    ErrorType,
    error_handler
)
from src.infrastructure.config import register_config_callback, CallbackPriority
from src.infrastructure.config.config_callback_manager import ConfigChangeContext


def main() -> None:
    """主函数"""
    print("=== 日志系统与配置系统集成演示 ===\n")
    
    # 1. 初始化依赖注入容器
    print("1. 初始化依赖注入容器...")
    container = DependencyContainer()
    from src.infrastructure.config_loader import IConfigLoader
    from src.infrastructure.config.config_merger import IConfigMerger
    from src.infrastructure.config.config_validator import IConfigValidator
    container.register_factory(IConfigLoader, YamlConfigLoader)  # type: ignore
    container.register_factory(IConfigMerger, ConfigMerger)  # type: ignore
    container.register_factory(IConfigValidator, ConfigValidator)  # type: ignore
    container.register(ConfigSystem, ConfigSystem)
    
    # 2. 获取服务
    print("2. 获取服务...")
    from src.infrastructure.config_loader import IConfigLoader
    from src.infrastructure.config.config_merger import IConfigMerger
    from src.infrastructure.config.config_validator import IConfigValidator
    config_loader = container.get(IConfigLoader)  # type: ignore
    config_merger = container.get(IConfigMerger)  # type: ignore
    config_validator = container.get(IConfigValidator)  # type: ignore
    config_system = container.get(ConfigSystem)
    
    # 3. 初始化日志系统与配置系统集成
    print("3. 初始化日志系统与配置系统集成...")
    initialize_logging_integration()
    
    # 4. 获取日志记录器
    print("4. 获取日志记录器...")
    logger = get_logger("demo_app")
    
    # 5. 记录不同级别的日志
    print("5. 记录不同级别的日志...")
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    # 6. 测试敏感信息脱敏
    print("\n6. 测试敏感信息脱敏...")
    logger.info("API Key: sk-abc123def4567890123456")
    logger.info("邮箱: user@example.com")
    logger.info("手机号: 13812345678")
    
    # 7. 注册自定义配置变更回调
    print("\n7. 注册自定义配置变更回调...")
    
    def on_config_change(context: ConfigChangeContext) -> None:
        logger.info(f"检测到配置变更: {context.config_path}")
        if context.old_config and context.new_config:
            old_level = context.old_config.get("log_level", "未设置")
            new_level = context.new_config.get("log_level", "未设置")
            if old_level != new_level:
                logger.info(f"日志级别变更: {old_level} -> {new_level}")
    
    register_config_callback(
        "demo_config_callback",
        on_config_change,
        priority=CallbackPriority.NORMAL,
        filter_paths=["global.yaml"]
    )
    
    # 8. 测试错误处理
    print("\n8. 测试错误处理...")
    
    @error_handler(ErrorType.USER_ERROR)
    def test_function() -> None:
        """测试函数"""
        raise ValueError("这是一个测试错误")
    
    try:
        test_function()
    except Exception as e:
        logger.info(f"捕获到处理后的错误: {e}")
    
    # 9. 测试配置热重载
    print("\n9. 测试配置热重载...")
    print("请修改 configs/global.yaml 中的 log_level，然后按回车键继续...")
    input()
    
    # 10. 等待一段时间观察日志输出
    print("\n10. 等待配置变更生效...")
    time.sleep(2)
    
    # 11. 再次记录日志以验证配置变更
    print("\n11. 再次记录日志以验证配置变更...")
    logger.info("配置变更后的日志测试")
    
    # 12. 显示错误统计
    print("\n12. 显示错误统计...")
    global_error_handler = get_global_error_handler()
    error_stats = global_error_handler.get_error_stats()
    print(f"总错误数: {error_stats['total_errors']}")
    print(f"错误类型分布: {error_stats['error_types']}")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()