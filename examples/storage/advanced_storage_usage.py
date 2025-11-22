"""高级存储使用示例

展示如何使用新的存储注册表和流式操作功能。
"""

import asyncio
import logging
from typing import Dict, Any, List

from src.adapters.storage.factory import StorageAdapterFactory
from src.adapters.storage.registry import StorageRegistry, storage_registry
from src.adapters.storage.utils.memory_optimizer import get_global_optimizer, configure_global_optimizer


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_storage_usage():
    """基本存储使用示例"""
    logger.info("=== 基本存储使用示例 ===")
    
    # 创建存储适配器工厂
    factory = StorageAdapterFactory()
    
    # 创建SQLite存储适配器
    storage = factory.create_adapter("sqlite", {
        "db_path": "example_storage.db",
        "connection_pool_size": 5,
        "enable_ttl": True,
        "default_ttl_seconds": 3600
    })
    
    # 连接到存储
    await storage.connect()
    
    try:
        # 保存一些数据
        for i in range(10):
            data = {
                "id": f"item_{i}",
                "content": f"这是第{i}个项目的数据",
                "type": "example",
                "metadata": {"index": i, "category": "test"}
            }
            await storage.save(data)
        
        # 加载数据
        item = await storage.load("item_5")
        logger.info(f"加载的项目: {item}")
        
        # 列出所有数据
        all_items = await storage.list({})
        logger.info(f"总共有 {len(all_items)} 个项目")
        
        # 使用过滤器
        filtered_items = await storage.list({"type": "example"})
        logger.info(f"类型为'example'的项目有 {len(filtered_items)} 个")
        
    finally:
        # 断开连接
        await storage.disconnect()


async def streaming_example():
    """流式操作示例"""
    logger.info("=== 流式操作示例 ===")
    
    # 创建存储适配器
    factory = StorageAdapterFactory()
    storage = factory.create_adapter("sqlite", {
        "db_path": "streaming_example.db",
        "enable_ttl": True
    })
    
    await storage.connect()
    
    try:
        # 创建大量数据
        logger.info("创建大量测试数据...")
        for i in range(1000):
            data = {
                "id": f"stream_item_{i}",
                "content": f"流式数据项目 {i}",
                "type": "stream_test",
                "metadata": {"batch": i // 100, "index": i}
            }
            await storage.save(data)
        
        # 使用流式列表处理大数据集
        logger.info("使用流式列表处理大数据集...")
        total_processed = 0
        batch_count = 0
        
        async for batch in storage.stream_list(
            filters={"type": "stream_test"},
            batch_size=50,
            max_memory_mb=10
        ):
            batch_count += 1
            total_processed += len(batch)
            logger.info(f"处理批次 {batch_count}: {len(batch)} 个项目")
            
            # 模拟处理数据
            for item in batch:
                # 这里可以添加实际的数据处理逻辑
                pass
        
        logger.info(f"总共处理了 {total_processed} 个项目，分为 {batch_count} 个批次")
        
    finally:
        await storage.disconnect()


async def memory_optimization_example():
    """内存优化示例"""
    logger.info("=== 内存优化示例 ===")
    
    # 配置内存优化器
    configure_global_optimizer(
        initial_batch_size=100,
        min_batch_size=10,
        max_batch_size=500,
        memory_threshold_percent=70.0,
        adjustment_factor=0.8
    )
    
    # 获取内存优化器
    memory_optimizer = get_global_optimizer()
    
    # 创建存储适配器
    factory = StorageAdapterFactory()
    storage = factory.create_adapter("sqlite", {
        "db_path": "memory_optimization.db",
        "enable_ttl": True
    })
    
    await storage.connect()
    
    try:
        # 创建大量数据
        logger.info("创建大量测试数据...")
        for i in range(2000):
            data = {
                "id": f"memory_test_{i}",
                "content": "x" * 1000,  # 较大的内容
                "type": "memory_test",
                "metadata": {"index": i}
            }
            await storage.save(data)
        
        # 显示初始内存状态
        initial_stats = memory_optimizer.get_stats()
        logger.info(f"初始内存状态: {initial_stats['memory_stats']}")
        
        # 使用流式列表处理大数据集，观察内存优化
        logger.info("使用流式列表处理大数据集，观察内存优化...")
        total_processed = 0
        
        async for batch in storage.stream_list(
            filters={"type": "memory_test"},
            batch_size=100,  # 初始批次大小
            max_memory_mb=20
        ):
            total_processed += len(batch)
            
            # 每10个批次显示一次内存状态
            if total_processed % 1000 == 0:
                current_stats = memory_optimizer.get_stats()
                logger.info(f"已处理 {total_processed} 个项目")
                logger.info(f"当前批次大小: {current_stats['current_batch_size']}")
                logger.info(f"内存使用: {current_stats['memory_stats']['process_memory_mb']} MB")
        
        # 显示最终内存状态
        final_stats = memory_optimizer.get_stats()
        logger.info(f"最终内存状态: {final_stats['memory_stats']}")
        logger.info(f"批次调整次数: {final_stats['total_adjustments']}")
        
    finally:
        await storage.disconnect()


async def registry_example():
    """存储注册表示例"""
    logger.info("=== 存储注册表示例 ===")
    
    # 显示已注册的存储类型
    logger.info("已注册的存储类型:")
    for storage_type, info in storage_registry.list_storage_types().items():
        logger.info(f"  - {storage_type}: {info['description']}")
    
    # 获取存储类型信息
    sqlite_info = storage_registry.get_storage_type_info("sqlite")
    logger.info(f"SQLite存储信息: {sqlite_info}")
    
    # 使用注册表创建存储适配器
    factory = StorageAdapterFactory()
    
    # 创建不同类型的存储适配器
    sqlite_storage = factory.create_adapter("sqlite", {
        "db_path": "registry_example_sqlite.db"
    })
    
    memory_storage = factory.create_adapter("memory", {
        "max_items": 100
    })
    
    # 连接存储
    await sqlite_storage.connect()
    await memory_storage.connect()
    
    try:
        # 在SQLite存储中保存数据
        await sqlite_storage.save({
            "id": "sqlite_test",
            "content": "这是SQLite存储中的数据",
            "type": "registry_test"
        })
        
        # 在内存存储中保存数据
        await memory_storage.save({
            "id": "memory_test",
            "content": "这是内存存储中的数据",
            "type": "registry_test"
        })
        
        # 从不同存储中加载数据
        sqlite_data = await sqlite_storage.load("sqlite_test")
        memory_data = await memory_storage.load("memory_test")
        
        logger.info(f"SQLite数据: {sqlite_data}")
        logger.info(f"内存数据: {memory_data}")
        
    finally:
        # 断开连接
        await sqlite_storage.disconnect()
        await memory_storage.disconnect()


async def custom_storage_type_example():
    """自定义存储类型示例"""
    logger.info("=== 自定义存储类型示例 ===")
    
    # 注册自定义存储类型
    from src.adapters.storage.backends.sqlite_backend import SQLiteStorageBackend
    
    storage_registry.register(
        "custom_sqlite",
        SQLiteStorageBackend,
        description="自定义SQLite存储",
        metadata={
            "category": "database",
            "features": ["persistent", "custom"],
            "performance": {
                "read_speed": "fast",
                "write_speed": "fast"
            }
        },
        factory=lambda config: SQLiteStorageBackend(**config)
    )
    
    # 使用自定义存储类型
    factory = StorageAdapterFactory()
    custom_storage = factory.create_adapter("custom_sqlite", {
        "db_path": "custom_storage.db",
        "cache_size": 5000,  # 自定义配置
        "enable_wal_mode": True
    })
    
    await custom_storage.connect()
    
    try:
        # 保存数据
        await custom_storage.save({
            "id": "custom_test",
            "content": "这是自定义存储中的数据",
            "type": "custom_example"
        })
        
        # 加载数据
        data = await custom_storage.load("custom_test")
        logger.info(f"自定义存储数据: {data}")
        
        # 健康检查
        health = await custom_storage.health_check()
        logger.info(f"存储健康状态: {health['status']}")
        
    finally:
        await custom_storage.disconnect()


async def main():
    """主函数"""
    logger.info("开始高级存储使用示例")
    
    try:
        # 运行各种示例
        await basic_storage_usage()
        await streaming_example()
        await memory_optimization_example()
        await registry_example()
        await custom_storage_type_example()
        
        logger.info("所有示例执行完成")
        
    except Exception as e:
        logger.error(f"示例执行出错: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())