"""存储服务依赖注入使用示例"""

import asyncio
import logging
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any

from src.services.container import (
    DependencyContainer,
    StorageServiceBindings,
)
from src.interfaces.sessions import ISessionService
from src.interfaces.threads import IThreadService

logger = get_logger(__name__)


def load_config_from_yaml(config_path: str) -> Dict[str, Any]:
    """从 YAML 加载配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    import yaml
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


async def example_basic_usage():
    """基本使用示例"""
    logger.info("Starting basic usage example...")
    
    # 创建容器
    container = DependencyContainer()
    
    # 加载配置
    config = {
        "session": {
            "primary_backend": "sqlite",
            "secondary_backends": ["file"],
            "sqlite": {"db_path": "./data/sessions.db"},
            "file": {"base_path": "./sessions_backup"},
            "storage_path": "./sessions",
        },
        "thread": {
            "primary_backend": "sqlite",
            "secondary_backends": ["file"],
            "sqlite": {"db_path": "./data/threads.db"},
            "file": {"base_path": "./threads_backup"},
        },
    }
    
    # 注册存储服务
    storage_bindings = StorageServiceBindings()
    storage_bindings.register_services(container, config)
    
    # 从容器获取服务
    session_service = container.get(ISessionService)
    thread_service = container.get(IThreadService)
    
    logger.info(f"Session service: {type(session_service).__name__}")
    logger.info(f"Thread service: {type(thread_service).__name__}")
    
    logger.info("Basic usage example completed!")


async def example_from_yaml_config():
    """从 YAML 配置加载的示例"""
    logger.info("Starting YAML config example...")
    
    # 创建容器
    container = DependencyContainer()
    
    # 加载 YAML 配置
    try:
        config = load_config_from_yaml("./configs/storage_example.yaml")
    except FileNotFoundError:
        logger.warning("Config file not found, using default config")
        config = {
            "session": {
                "primary_backend": "sqlite",
                "secondary_backends": [],
                "sqlite": {"db_path": "./data/sessions.db"},
            },
            "thread": {
                "primary_backend": "sqlite",
                "secondary_backends": [],
                "sqlite": {"db_path": "./data/threads.db"},
            },
        }
    
    # 注册存储服务
    storage_bindings = StorageServiceBindings()
    storage_bindings.register_services(container, config)
    
    # 获取服务
    session_service = container.get(ISessionService)
    thread_service = container.get(IThreadService)
    
    logger.info(f"Session service loaded: {type(session_service).__name__}")
    logger.info(f"Thread service loaded: {type(thread_service).__name__}")
    
    logger.info("YAML config example completed!")


async def example_custom_backends():
    """自定义后端配置示例"""
    logger.info("Starting custom backends example...")
    
    # 创建容器
    container = DependencyContainer()
    
    # 配置：仅使用 SQLite，无备份
    config = {
        "session": {
            "primary_backend": "sqlite",
            "secondary_backends": [],  # 无备份
            "sqlite": {"db_path": "./data/sessions_prod.db"},
            "storage_path": "./sessions",
        },
        "thread": {
            "primary_backend": "sqlite",
            "secondary_backends": [],  # 无备份
            "sqlite": {"db_path": "./data/threads_prod.db"},
        },
    }
    
    # 注册存储服务
    storage_bindings = StorageServiceBindings()
    storage_bindings.register_services(container, config)
    
    session_service = container.get(ISessionService)
    thread_service = container.get(IThreadService)
    
    logger.info(f"Production config - Session service: {type(session_service).__name__}")
    logger.info(f"Production config - Thread service: {type(thread_service).__name__}")
    
    logger.info("Custom backends example completed!")


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def main():
    """运行所有示例"""
    setup_logging()
    
    try:
        logger.info("=" * 80)
        logger.info("Storage Service Dependency Injection Examples")
        logger.info("=" * 80)
        
        await example_basic_usage()
        logger.info("")
        
        await example_from_yaml_config()
        logger.info("")
        
        await example_custom_backends()
        
        logger.info("=" * 80)
        logger.info("All examples completed successfully!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Example failed with error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
