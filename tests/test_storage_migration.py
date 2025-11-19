"""存储迁移测试

测试新存储系统的功能和向后兼容性。
"""

import pytest
import tempfile
import os
import time
from typing import Dict, Any

from src.core.state.entities import StateSnapshot, StateHistoryEntry
from src.adapters.storage import (
    MemoryStateStorageAdapter,
    SQLiteStateStorageAdapter,
    FileStateStorageAdapter,
    LegacyStorageAdapter,
    create_storage_adapter
)
from src.services.storage import StorageManager, StorageConfigManager
from src.services.container.storage_registry import (
    register_storage_services,
    register_storage_adapter,
    get_storage_manager
)


class TestStorageAdapters:
    """存储适配器测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def memory_adapter(self):
        """内存存储适配器fixture"""
        return MemoryStateStorageAdapter(
            max_size=1000,
            enable_ttl=False,
            enable_compression=False
        )
    
    @pytest.fixture
    def sqlite_adapter(self, temp_dir):
        """SQLite存储适配器fixture"""
        db_path = os.path.join(temp_dir, "test.db")
        return SQLiteStateStorageAdapter(
            db_path=db_path,
            enable_backup=False
        )
    
    @pytest.fixture
    def file_adapter(self, temp_dir):
        """文件存储适配器fixture"""
        base_path = os.path.join(temp_dir, "file_storage")
        return FileStateStorageAdapter(
            base_path=base_path,
            enable_backup=False
        )
    
    def test_memory_adapter_basic_operations(self, memory_adapter):
        """测试内存存储适配器基本操作"""
        # 创建历史记录条目
        entry = StateHistoryEntry(
            history_id="test_history_1",
            agent_id="test_agent",
            session_id="test_session",
            thread_id="test_thread",
            timestamp=time.time(),
            data={"message": "Hello, World!"}
        )
        
        # 保存历史记录条目
        assert memory_adapter.save_history_entry(entry) is True
        
        # 获取历史记录条目
        loaded_entry = memory_adapter.get_history_entry("test_history_1")
        assert loaded_entry is not None
        assert loaded_entry.history_id == "test_history_1"
        assert loaded_entry.data["message"] == "Hello, World!"
        
        # 获取代理的历史记录
        entries = memory_adapter.get_history_entries("test_agent")
        assert len(entries) == 1
        assert entries[0].history_id == "test_history_1"
        
        # 更新历史记录条目
        updates = {"data": {"message": "Updated message"}}
        assert memory_adapter.update_history_entry("test_history_1", updates) is True
        
        # 验证更新
        updated_entry = memory_adapter.get_history_entry("test_history_1")
        assert updated_entry.data["message"] == "Updated message"
        
        # 删除历史记录条目
        assert memory_adapter.delete_history_entry("test_history_1") is True
        
        # 验证删除
        deleted_entry = memory_adapter.get_history_entry("test_history_1")
        assert deleted_entry is None
    
    def test_sqlite_adapter_basic_operations(self, sqlite_adapter):
        """测试SQLite存储适配器基本操作"""
        # 创建历史记录条目
        entry = StateHistoryEntry(
            history_id="test_history_1",
            agent_id="test_agent",
            session_id="test_session",
            thread_id="test_thread",
            timestamp=time.time(),
            data={"message": "Hello, SQLite!"}
        )
        
        # 保存历史记录条目
        assert sqlite_adapter.save_history_entry(entry) is True
        
        # 获取历史记录条目
        loaded_entry = sqlite_adapter.get_history_entry("test_history_1")
        assert loaded_entry is not None
        assert loaded_entry.history_id == "test_history_1"
        assert loaded_entry.data["message"] == "Hello, SQLite!"
        
        # 获取代理的历史记录
        entries = sqlite_adapter.get_history_entries("test_agent")
        assert len(entries) == 1
        assert entries[0].history_id == "test_history_1"
        
        # 删除历史记录条目
        assert sqlite_adapter.delete_history_entry("test_history_1") is True
        
        # 验证删除
        deleted_entry = sqlite_adapter.get_history_entry("test_history_1")
        assert deleted_entry is None
    
    def test_file_adapter_basic_operations(self, file_adapter):
        """测试文件存储适配器基本操作"""
        # 创建历史记录条目
        entry = StateHistoryEntry(
            history_id="test_history_1",
            agent_id="test_agent",
            session_id="test_session",
            thread_id="test_thread",
            timestamp=time.time(),
            data={"message": "Hello, File!"}
        )
        
        # 保存历史记录条目
        assert file_adapter.save_history_entry(entry) is True
        
        # 获取历史记录条目
        loaded_entry = file_adapter.get_history_entry("test_history_1")
        assert loaded_entry is not None
        assert loaded_entry.history_id == "test_history_1"
        assert loaded_entry.data["message"] == "Hello, File!"
        
        # 获取代理的历史记录
        entries = file_adapter.get_history_entries("test_agent")
        assert len(entries) == 1
        assert entries[0].history_id == "test_history_1"
        
        # 删除历史记录条目
        assert file_adapter.delete_history_entry("test_history_1") is True
        
        # 验证删除
        deleted_entry = file_adapter.get_history_entry("test_history_1")
        assert deleted_entry is None
    
    def test_snapshot_operations(self, memory_adapter):
        """测试快照操作"""
        # 创建状态快照
        snapshot = StateSnapshot(
            snapshot_id="test_snapshot_1",
            agent_id="test_agent",
            timestamp=time.time(),
            state_data={"counter": 42, "status": "active"}
        )
        
        # 保存状态快照
        assert memory_adapter.save_snapshot(snapshot) is True
        
        # 加载状态快照
        loaded_snapshot = memory_adapter.load_snapshot("test_snapshot_1")
        assert loaded_snapshot is not None
        assert loaded_snapshot.snapshot_id == "test_snapshot_1"
        assert loaded_snapshot.state_data["counter"] == 42
        assert loaded_snapshot.state_data["status"] == "active"
        
        # 获取代理的快照列表
        snapshots = memory_adapter.get_snapshots_by_agent("test_agent")
        assert len(snapshots) == 1
        assert snapshots[0].snapshot_id == "test_snapshot_1"
        
        # 删除状态快照
        assert memory_adapter.delete_snapshot("test_snapshot_1") is True
        
        # 验证删除
        deleted_snapshot = memory_adapter.load_snapshot("test_snapshot_1")
        assert deleted_snapshot is None
    
    def test_legacy_adapter_compatibility(self, memory_adapter):
        """测试向后兼容适配器"""
        # 创建向后兼容适配器
        legacy_adapter = LegacyStorageAdapter(memory_adapter)
        
        # 使用旧版本接口保存数据
        data = {
            "type": "history_entry",
            "history_id": "legacy_test_1",
            "agent_id": "test_agent",
            "session_id": "test_session",
            "thread_id": "test_thread",
            "timestamp": time.time(),
            "data": {"message": "Legacy test"}
        }
        
        # 保存数据
        saved_id = legacy_adapter.save(data)
        assert saved_id == "legacy_test_1"
        
        # 加载数据
        loaded_data = legacy_adapter.load("legacy_test_1")
        assert loaded_data is not None
        assert loaded_data["history_id"] == "legacy_test_1"
        assert loaded_data["data"]["message"] == "Legacy test"
        
        # 检查数据是否存在
        assert legacy_adapter.exists("legacy_test_1") is True
        
        # 列出数据
        results = legacy_adapter.list({"agent_id": "test_agent"})
        assert len(results) == 1
        assert results[0]["history_id"] == "legacy_test_1"
        
        # 计算数据数量
        count = legacy_adapter.count({"agent_id": "test_agent"})
        assert count == 1
        
        # 删除数据
        assert legacy_adapter.delete("legacy_test_1") is True
        
        # 验证删除
        assert legacy_adapter.exists("legacy_test_1") is False
    
    def test_storage_factory(self):
        """测试存储适配器工厂"""
        # 创建内存存储适配器
        memory_adapter = create_storage_adapter("memory", {
            "max_size": 1000,
            "enable_ttl": False
        })
        assert isinstance(memory_adapter, MemoryStateStorageAdapter)
        
        # 创建SQLite存储适配器
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "factory_test.db")
            sqlite_adapter = create_storage_adapter("sqlite", {
                "db_path": db_path,
                "enable_backup": False
            })
            assert isinstance(sqlite_adapter, SQLiteStateStorageAdapter)
        
        # 创建文件存储适配器
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = os.path.join(temp_dir, "factory_test")
            file_adapter = create_storage_adapter("file", {
                "base_path": base_path,
                "enable_backup": False
            })
            assert isinstance(file_adapter, FileStateStorageAdapter)


class TestStorageServices:
    """存储服务测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_storage_manager(self, temp_dir):
        """测试存储管理器"""
        # 创建存储管理器
        manager = StorageManager()
        
        # 注册内存存储适配器
        assert await manager.register_adapter(
            "memory",
            "memory",
            {"max_size": 1000},
            set_as_default=True
        ) is True
        
        # 注册SQLite存储适配器
        db_path = os.path.join(temp_dir, "manager_test.db")
        assert await manager.register_adapter(
            "sqlite",
            "sqlite",
            {"db_path": db_path, "enable_backup": False}
        ) is True
        
        # 获取默认适配器
        default_adapter = await manager.get_default_adapter()
        assert default_adapter is not None
        
        # 获取指定适配器
        sqlite_adapter = await manager.get_adapter("sqlite")
        assert sqlite_adapter is not None
        
        # 列出适配器
        adapters = await manager.list_adapters()
        assert len(adapters) == 2
        
        # 健康检查
        health = await manager.health_check()
        assert "memory" in health
        assert "sqlite" in health
        
        # 关闭存储管理器
        await manager.close()
    
    def test_storage_config_manager(self):
        """测试存储配置管理器"""
        # 创建存储配置管理器
        config_manager = StorageConfigManager()
        
        # 获取默认配置
        memory_config = config_manager.get_config("memory_default")
        assert memory_config is not None
        assert memory_config.storage_type.value == "memory"
        
        sqlite_config = config_manager.get_config("sqlite_default")
        assert sqlite_config is not None
        assert sqlite_config.storage_type.value == "sqlite"
        
        file_config = config_manager.get_config("file_default")
        assert file_config is not None
        assert file_config.storage_type.value == "file"
        
        # 从模板创建配置
        assert config_manager.create_config_from_template(
            "memory_default",
            "custom_memory",
            {"max_size": 2000}
        ) is True
        
        custom_config = config_manager.get_config("custom_memory")
        assert custom_config is not None
        assert custom_config.config["max_size"] == 2000
        
        # 列出配置
        memory_configs = config_manager.list_configs("memory")
        assert len(memory_configs) >= 2  # memory_default 和 custom_memory
        
        # 设置默认配置
        assert config_manager.set_default_config("custom_memory") is True
        assert config_manager.get_default_config().name == "custom_memory"
        
        # 导出配置
        exported_configs = config_manager.export_configs()
        assert "configs" in exported_configs
        assert "custom_memory" in exported_configs["configs"]


class TestStorageMigration:
    """存储迁移测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_basic_migration(self, temp_dir):
        """测试基本迁移功能"""
        from src.services.storage import StorageMigrationService
        
        # 创建源和目标适配器
        source_adapter = MemoryStateStorageAdapter(max_size=1000)
        
        db_path = os.path.join(temp_dir, "migration_test.db")
        target_adapter = SQLiteStateStorageAdapter(db_path=db_path, enable_backup=False)
        
        # 连接适配器
        await source_adapter._backend.connect()
        await target_adapter._backend.connect()
        
        # 在源适配器中添加一些数据
        entry = StateHistoryEntry(
            history_id="migration_test_1",
            agent_id="test_agent",
            session_id="test_session",
            thread_id="test_thread",
            timestamp=time.time(),
            data={"message": "Migration test"}
        )
        source_adapter.save_history_entry(entry)
        
        # 创建迁移服务
        migration_service = StorageMigrationService()
        
        # 创建迁移任务
        task_id = await migration_service.create_migration_task(
            "test_migration",
            source_adapter,
            target_adapter,
            {"batch_size": 10, "validate_data": True}
        )
        
        # 开始迁移
        assert await migration_service.start_migration(task_id) is True
        
        # 等待迁移完成
        import asyncio
        await asyncio.sleep(0.1)  # 等待一小段时间
        
        # 获取迁移状态
        status = await migration_service.get_migration_status(task_id)
        assert status is not None
        assert status["name"] == "test_migration"
        
        # 关闭服务
        await migration_service.close()
        await source_adapter._backend.disconnect()
        await target_adapter._backend.disconnect()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])