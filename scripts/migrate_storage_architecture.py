#!/usr/bin/env python3
"""
存储架构迁移脚本

帮助用户从旧存储架构迁移到新架构。
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.state.entities import StateSnapshot, StateHistoryEntry
from src.adapters.storage import (
    MemoryStateStorageAdapter,
    SQLiteStateStorageAdapter,
    FileStateStorageAdapter,
    LegacyStorageAdapter,
    create_storage_adapter
)
from src.services.storage import StorageManager, StorageConfigManager, StorageMigrationService
from src.services.container.storage_registry import initialize_storage_services


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StorageArchitectureMigrator:
    """存储架构迁移器"""
    
    def __init__(self):
        """初始化迁移器"""
        self.config_manager = StorageConfigManager()
        self.migration_service = StorageMigrationService()
        
    async def migrate_from_legacy(
        self,
        legacy_config: Dict[str, Any],
        new_adapter_type: str,
        new_config: Dict[str, Any]
    ) -> bool:
        """从旧架构迁移到新架构
        
        Args:
            legacy_config: 旧架构配置
            new_adapter_type: 新适配器类型
            new_config: 新适配器配置
            
        Returns:
            是否迁移成功
        """
        try:
            logger.info("开始从旧架构迁移到新架构...")
            
            # 创建旧架构适配器（模拟）
            legacy_adapter = self._create_legacy_adapter(legacy_config)
            
            # 创建新架构适配器
            new_adapter = create_storage_adapter(new_adapter_type, new_config)
            
            # 连接适配器
            await legacy_adapter._backend.connect()
            await new_adapter._backend.connect()
            
            # 创建迁移任务
            task_id = await self.migration_service.create_migration_task(
                "legacy_to_new",
                legacy_adapter,
                new_adapter,
                {
                    "batch_size": 100,
                    "validate_data": True,
                    "migrate_history": True,
                    "migrate_snapshots": True
                }
            )
            
            # 开始迁移
            logger.info(f"开始迁移任务: {task_id}")
            await self.migration_service.start_migration(task_id)
            
            # 监控迁移进度
            await self._monitor_migration(task_id)
            
            # 验证迁移结果
            validation_result = await self.migration_service.validate_migration(
                legacy_adapter, new_adapter
            )
            
            if validation_result.get("overall_match", False):
                logger.info("迁移验证通过")
                success = True
            else:
                logger.error(f"迁移验证失败: {validation_result}")
                success = False
            
            # 断开连接
            await legacy_adapter._backend.disconnect()
            await new_adapter._backend.disconnect()
            
            # 关闭迁移服务
            await self.migration_service.close()
            
            return success
            
        except Exception as e:
            logger.error(f"迁移失败: {e}")
            return False
    
    def _create_legacy_adapter(self, config: Dict[str, Any]) -> LegacyStorageAdapter:
        """创建旧架构适配器（模拟）
        
        Args:
            config: 配置参数
            
        Returns:
            旧架构适配器
        """
        # 根据配置创建新适配器，然后包装为向后兼容适配器
        adapter_type = config.get("type", "memory")
        adapter_config = config.get("config", {})
        
        new_adapter = create_storage_adapter(adapter_type, adapter_config)
        return LegacyStorageAdapter(new_adapter)
    
    async def _monitor_migration(self, task_id: str) -> None:
        """监控迁移进度
        
        Args:
            task_id: 任务ID
        """
        while True:
            status = await self.migration_service.get_migration_status(task_id)
            
            if status is None:
                logger.error("无法获取迁移状态")
                break
            
            logger.info(
                f"迁移进度: {status['progress']:.1f}% "
                f"({status['processed_items']}/{status['total_items']})"
            )
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                if status["status"] == "completed":
                    logger.info("迁移完成")
                elif status["status"] == "failed":
                    logger.error(f"迁移失败: {status.get('error_message', 'Unknown error')}")
                else:
                    logger.info("迁移已取消")
                break
            
            await asyncio.sleep(1)
    
    async def setup_new_architecture(self, config_file: str = "configs/storage.yaml") -> bool:
        """设置新架构
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            是否设置成功
        """
        try:
            logger.info("设置新存储架构...")
            
            # 初始化存储服务
            initialize_storage_services()
            
            # 加载配置文件
            if os.path.exists(config_file):
                await self._load_config_file(config_file)
                logger.info(f"已加载配置文件: {config_file}")
            else:
                logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
                await self._setup_default_config()
            
            logger.info("新架构设置完成")
            return True
            
        except Exception as e:
            logger.error(f"设置新架构失败: {e}")
            return False
    
    async def _load_config_file(self, config_file: str) -> None:
        """加载配置文件
        
        Args:
            config_file: 配置文件路径
        """
        import yaml
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 注册适配器配置
        adapters_config = config_data.get("adapters", {})
        
        for name, adapter_config in adapters_config.items():
            if adapter_config.get("enabled", True):
                from src.services.container.storage_registry import register_storage_adapter
                
                register_storage_adapter(
                    name=name,
                    adapter_type=adapter_config["type"],
                    config=adapter_config["config"],
                    set_as_default=adapter_config.get("is_default", False)
                )
    
    async def _setup_default_config(self) -> None:
        """设置默认配置"""
        from src.services.container.storage_registry import register_storage_adapter
        
        # 注册默认内存存储适配器
        register_storage_adapter(
            name="memory",
            adapter_type="memory",
            config={
                "max_size": 1000,
                "enable_ttl": False,
                "enable_compression": False
            }
        )
        
        # 注册默认SQLite存储适配器
        register_storage_adapter(
            name="sqlite",
            adapter_type="sqlite",
            config={
                "db_path": "storage.db",
                "enable_backup": True
            },
            set_as_default=True
        )
    
    async def test_new_architecture(self) -> bool:
        """测试新架构
        
        Returns:
            是否测试通过
        """
        try:
            logger.info("测试新存储架构...")
            
            from src.services.container.storage_registry import get_storage_manager
            
            # 获取存储管理器
            manager = get_storage_manager()
            
            # 测试适配器列表
            adapters = await manager.list_adapters()
            logger.info(f"已注册 {len(adapters)} 个适配器")
            
            # 测试健康检查
            health = await manager.health_check()
            logger.info(f"健康检查结果: {health}")
            
            # 测试默认适配器
            default_adapter = await manager.get_default_adapter()
            if default_adapter:
                # 创建测试数据
                test_entry = StateHistoryEntry(
                    history_id="test_migration",
                    agent_id="test_agent",
                    session_id="test_session",
                    thread_id="test_thread",
                    timestamp=time.time(),
                    data={"message": "Migration test"}
                )
                
                # 测试保存和加载
                success = default_adapter.save_history_entry(test_entry)
                if success:
                    loaded_entry = default_adapter.get_history_entry("test_migration")
                    if loaded_entry and loaded_entry.data["message"] == "Migration test":
                        logger.info("新架构测试通过")
                        return True
            
            logger.error("新架构测试失败")
            return False
            
        except Exception as e:
            logger.error(f"测试新架构失败: {e}")
            return False


async def main():
    """主函数"""
    print("=" * 60)
    print("存储架构迁移脚本")
    print("=" * 60)
    
    migrator = StorageArchitectureMigrator()
    
    # 设置新架构
    print("\n1. 设置新存储架构...")
    success = await migrator.setup_new_architecture()
    if not success:
        print("设置新架构失败，退出")
        return
    
    # 测试新架构
    print("\n2. 测试新存储架构...")
    success = await migrator.test_new_architecture()
    if not success:
        print("测试新架构失败，退出")
        return
    
    # 询问是否进行迁移
    print("\n3. 是否进行数据迁移？")
    print("注意：如果您有旧架构的数据，可以选择进行迁移")
    choice = input("输入 'y' 进行迁移，其他键跳过: ").lower().strip()
    
    if choice == 'y':
        print("\n开始数据迁移...")
        
        # 示例：从内存存储迁移到SQLite存储
        legacy_config = {
            "type": "memory",
            "config": {
                "max_size": 1000,
                "enable_ttl": False
            }
        }
        
        new_config = {
            "db_path": "migrated_storage.db",
            "enable_backup": True
        }
        
        success = await migrator.migrate_from_legacy(
            legacy_config,
            "sqlite",
            new_config
        )
        
        if success:
            print("数据迁移完成")
        else:
            print("数据迁移失败")
    
    print("\n" + "=" * 60)
    print("存储架构迁移脚本执行完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())