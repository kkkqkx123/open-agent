"""LLM任务组配置使用示例"""

import asyncio
import logging
from pathlib import Path

from src.core.config.config_loader import ConfigLoader
from src.core.llm.task_group_manager import TaskGroupManager
from src.core.llm.polling_pool import PollingPoolManager
from src.core.llm.enhanced_fallback_manager import EnhancedFallbackManager
from src.core.llm.concurrency_controller import ConcurrencyAndRateLimitManager, ConcurrencyLevel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    # 1. 初始化配置加载器
    config_loader = ConfigLoader()
    
    # 2. 创建任务组管理器
    task_group_manager = TaskGroupManager(config_loader)
    
    # 3. 加载任务组配置
    try:
        config = task_group_manager.load_config()
        logger.info("任务组配置加载成功")
        logger.info(f"可用任务组: {list(config.task_groups.keys())}")
        logger.info(f"可用轮询池: {list(config.polling_pools.keys())}")
    except Exception as e:
        logger.error(f"任务组配置加载失败: {e}")
        return
    
    # 4. 创建轮询池管理器
    polling_pool_manager = PollingPoolManager(task_group_manager)
    
    # 5. 创建轮询池
    try:
        # 获取轮询池配置
        single_turn_pool_config = config.get_polling_pool("single_turn_pool")
        if single_turn_pool_config:
            pool = await polling_pool_manager.create_pool("single_turn_pool", vars(single_turn_pool_config))
            logger.info("单轮对话轮询池创建成功")
            
            # 获取轮询池状态
            status = pool.get_status()
            logger.info(f"轮询池状态: {status}")
        
        # 创建高并发轮询池
        high_concurrency_pool_config = config.get_polling_pool("high_concurrency_pool")
        if high_concurrency_pool_config:
            pool = await polling_pool_manager.create_pool("high_concurrency_pool", vars(high_concurrency_pool_config))
            logger.info("高并发轮询池创建成功")
    
    except Exception as e:
        logger.error(f"轮询池创建失败: {e}")
    
    # 6. 创建降级管理器
    fallback_manager = EnhancedFallbackManager(task_group_manager, polling_pool_manager)
    logger.info("降级管理器创建成功")
    
    # 7. 演示任务组使用
    await demonstrate_task_group_usage(task_group_manager, fallback_manager)
    
    # 8. 演示并发控制
    await demonstrate_concurrency_control(config)
    
    # 9. 清理资源
    await polling_pool_manager.shutdown_all()
    logger.info("所有轮询池已关闭")


async def demonstrate_task_group_usage(task_group_manager, fallback_manager):
    """演示任务组使用"""
    logger.info("=== 演示任务组使用 ===")
    
    # 1. 解析组引用
    group_refs = [
        "fast_group.echelon1",
        "plan_group.echelon2", 
        "thinking_group.echelon1",
        "fast_small_group.translation",
        "execute_group.echelon2"
    ]
    
    for ref in group_refs:
        group_name, echelon_or_task = task_group_manager.parse_group_reference(ref)
        models = task_group_manager.get_models_for_group(ref)
        logger.info(f"组引用 {ref}: 组={group_name}, 层级/任务={echelon_or_task}, 模型={models}")
    
    # 2. 验证组引用
    valid_refs = ["fast_group.echelon1", "fast_small_group.translation"]
    invalid_refs = ["nonexistent_group.echelon1", "fast_group.nonexistent_echelon"]
    
    for ref in valid_refs + invalid_refs:
        is_valid = task_group_manager.validate_group_reference(ref)
        logger.info(f"组引用 {ref} 验证结果: {is_valid}")
    
    # 3. 演示降级策略
    try:
        result = await fallback_manager.execute_with_fallback(
            primary_target="fast_group.echelon1",
            fallback_groups=["fast_group.echelon2", "fast_group.echelon3"],
            prompt="请解释什么是机器学习？"
        )
        logger.info(f"LLM调用成功: {result}")
    except Exception as e:
        logger.info(f"LLM调用失败（预期）: {e}")
    
    # 4. 查看降级历史
    history = fallback_manager.get_fallback_history(5)
    logger.info(f"最近的降级历史: {len(history)} 条记录")
    for attempt in history:
        logger.info(f"  尝试 {attempt.attempt_number}: {attempt.target} - {attempt.strategy.value} - {'成功' if attempt.success else '失败'}")
    
    # 5. 查看熔断器状态
    circuit_status = fallback_manager.get_circuit_breaker_status()
    logger.info(f"熔断器状态: {circuit_status}")
    
    # 6. 查看统计信息
    stats = fallback_manager.get_statistics()
    logger.info(f"降级统计: {stats}")


async def demonstrate_concurrency_control(config):
    """演示并发控制"""
    logger.info("=== 演示并发控制 ===")
    
    # 创建并发管理器
    concurrency_manager = ConcurrencyAndRateLimitManager(
        config.concurrency_control.__dict__,
        config.rate_limiting.__dict__
    )
    
    # 测试并发控制
    test_identifiers = ["fast_group", "plan_group", "thinking_group"]
    
    for identifier in test_identifiers:
        # 尝试获取执行许可
        can_execute = await concurrency_manager.check_and_acquire(
            ConcurrencyLevel.GROUP, identifier, timeout=1.0
        )
        
        if can_execute:
            logger.info(f"成功获取执行许可: {identifier}")
            
            # 模拟执行
            await asyncio.sleep(0.1)
            
            # 释放许可
            concurrency_manager.release(ConcurrencyLevel.GROUP, identifier)
            logger.info(f"释放执行许可: {identifier}")
        else:
            logger.info(f"无法获取执行许可: {identifier}")
    
    # 查看并发控制状态
    status = concurrency_manager.get_status()
    logger.info(f"并发控制状态: {status}")


def demonstrate_config_structure():
    """演示配置结构"""
    logger.info("=== 配置结构演示 ===")
    
    config_path = Path("configs/llms/groups/_task_groups.yaml")
    if config_path.exists():
        logger.info(f"任务组配置文件位置: {config_path}")
        logger.info("配置文件包含以下主要部分:")
        logger.info("  - task_groups: 任务组定义")
        logger.info("  - polling_pools: 轮询池配置")
        logger.info("  - global_fallback: 全局降级配置")
        logger.info("  - concurrency_control: 并发控制配置")
        logger.info("  - rate_limiting: 速率限制配置")
    
    workflow_config_path = Path("configs/workflows/llm_task_group_example.yaml")
    if workflow_config_path.exists():
        logger.info(f"工作流示例配置文件位置: {workflow_config_path}")
        logger.info("工作流配置展示了如何在节点中使用任务组")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
    
    # 显示配置结构信息
    demonstrate_config_structure()