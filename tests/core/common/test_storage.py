"""storage.py 单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from core.common.storage import BaseStorage
from core.common.serialization import Serializer
from core.common.utils.temporal import TemporalManager
from core.common.utils.metadata import MetadataManager
from core.common.cache import CacheManager


class TestStorage(BaseStorage):
    """用于测试的存储实现"""
    async def save(self, data):
        """保存数据"""
        return True

    async def load(self, id):
        """加载数据"""
        return None

    async def delete(self, id):
        """删除数据"""
        return True

    async def list(self, filters):
        """列出数据"""
        return []


class TestBaseStorage:
    """测试 BaseStorage 类"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建模拟依赖项
        self.mock_serializer = Mock(spec=Serializer)
        self.mock_temporal = Mock(spec=TemporalManager)
        self.mock_metadata = Mock(spec=MetadataManager)
        self.mock_cache = Mock(spec=CacheManager)
        
        # 设置时间模拟
        self.mock_temporal.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        self.mock_temporal.format_timestamp.return_value = "2023-01-01T12:00:00"
    
    @pytest.mark.asyncio
    async def test_base_storage_initialization(self):
        """测试基础存储初始化"""
        # 测试使用默认依赖项
        storage = TestStorage()
        assert storage.serializer is not None
        assert storage.temporal is not None
        assert storage.metadata is not None
        assert storage.cache is None
        
        # 测试使用自定义依赖项
        storage = TestStorage(
            serializer=self.mock_serializer,
            temporal_manager=self.mock_temporal,
            metadata_manager=self.mock_metadata,
            cache_manager=self.mock_cache
        )
        assert storage.serializer == self.mock_serializer
        assert storage.temporal == self.mock_temporal
        assert storage.metadata == self.mock_metadata
        assert storage.cache == self.mock_cache
    
    @pytest.mark.asyncio
    async def test_save_with_metadata(self):
        """测试保存数据并处理元数据"""
        # 创建存储实例
        storage = TestStorage(
            serializer=self.mock_serializer,
            temporal_manager=self.mock_temporal,
            metadata_manager=self.mock_metadata
        )
        
        # 模拟存储的save方法
        storage.save = AsyncMock(return_value=True)
        
        # 准备测试数据
        data = {"id": "test_id", "content": "test_content"}
        metadata = {"category": "test", "priority": "high"}
        
        # 模拟元数据规范化
        self.mock_metadata.normalize_metadata.return_value = metadata
        
        # 调用方法
        result = await storage.save_with_metadata(data, metadata)
        
        # 验证结果
        assert result is True
        # 验证save被调用
        storage.save.assert_called_once()
        # 验证时间戳被添加
        called_data = storage.save.call_args[0][0]
        assert called_data["created_at"] == "2023-01-01T12:00:00"
        assert called_data["updated_at"] == "2023-01-01T12:00:00"
        # 验证元数据被添加
        assert called_data["metadata"] == metadata
        
        # 验证时间管理器被调用
        self.mock_temporal.now.assert_called()
        self.mock_temporal.format_timestamp.assert_called()
        
        # 验证元数据管理器被调用
        self.mock_metadata.normalize_metadata.assert_called_once_with(metadata)
    
    @pytest.mark.asyncio
    async def test_save_with_metadata_with_ttl(self):
        """测试带TTL的保存数据"""
        # 创建存储实例，包含缓存
        storage = TestStorage(
            serializer=self.mock_serializer,
            temporal_manager=self.mock_temporal,
            metadata_manager=self.mock_metadata,
            cache_manager=self.mock_cache
        )
        
        # 模拟方法
        storage.save = AsyncMock(return_value=True)
        assert storage.cache is not None
        storage.cache.set = AsyncMock()
        
        # 准备测试数据
        data = {"id": "test_id", "content": "test_content"}
        metadata = {"category": "test"}
        
        self.mock_metadata.normalize_metadata.return_value = metadata
        
        # 调用方法
        result = await storage.save_with_metadata(data, metadata, ttl=300)
        
        # 验证结果
        assert result is True
        # 验证缓存被设置
        storage.cache.set.assert_called_once_with("test_id", data, ttl=300)
    
    @pytest.mark.asyncio
    async def test_save_with_metadata_without_cache(self):
        """测试无缓存时保存数据"""
        # 创建存储实例，不包含缓存
        storage = TestStorage(
            serializer=self.mock_serializer,
            temporal_manager=self.mock_temporal,
            metadata_manager=self.mock_metadata
        )
        
        # 模拟方法
        storage.save = AsyncMock(return_value=True)
        
        # 准备测试数据
        data = {"id": "test_id", "content": "test_content"}
        metadata = {"category": "test"}
        
        self.mock_metadata.normalize_metadata.return_value = metadata
        
        # 调用方法
        result = await storage.save_with_metadata(data, metadata)
        
        # 验证结果
        assert result is True
        # 验证缓存没有被调用（因为没有缓存）
    
    @pytest.mark.asyncio
    async def test_load_with_cache_hit(self):
        """测试从缓存加载数据（缓存命中）"""
        # 创建存储实例，包含缓存
        storage = TestStorage(cache_manager=self.mock_cache)
        
        # 模拟缓存返回数据
        cached_data = {"id": "test_id", "content": "cached_content"}
        assert storage.cache is not None
        storage.cache.get = AsyncMock(return_value=cached_data)
        
        # 不应该调用存储的load方法
        storage.load = AsyncMock()
        
        # 调用方法
        result = await storage.load_with_cache("test_id")
        
        # 验证结果
        assert result == cached_data
        # 验证缓存被查询
        storage.cache.get.assert_called_once_with("test_id")
        # 验证存储的load方法没有被调用
        storage.load.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_load_with_cache_miss(self):
        """测试从缓存加载数据（缓存未命中）"""
        # 创建存储实例，包含缓存
        storage = TestStorage(cache_manager=self.mock_cache)
        
        # 模拟缓存未命中
        assert storage.cache is not None
        storage.cache.get = AsyncMock(return_value=None)
        
        # 模拟存储返回数据
        stored_data = {"id": "test_id", "content": "stored_content"}
        storage.load = AsyncMock(return_value=stored_data)
        
        # 模拟缓存设置
        storage.cache.set = AsyncMock()
        
        # 调用方法
        result = await storage.load_with_cache("test_id")
        
        # 验证结果
        assert result == stored_data
        # 验证缓存被查询
        storage.cache.get.assert_called_once_with("test_id")
        # 验证存储的load方法被调用
        storage.load.assert_called_once_with("test_id")
        # 验证数据被缓存
        storage.cache.set.assert_called_once_with("test_id", stored_data)
    
    @pytest.mark.asyncio
    async def test_load_with_cache_miss_no_data(self):
        """测试从缓存加载数据（缓存未命中，无数据）"""
        # 创建存储实例，包含缓存
        storage = TestStorage(cache_manager=self.mock_cache)
        
        # 模拟缓存未命中
        assert storage.cache is not None
        storage.cache.get = AsyncMock(return_value=None)
        
        # 模拟存储返回None
        storage.load = AsyncMock(return_value=None)
        
        # 调用方法
        result = await storage.load_with_cache("test_id")
        
        # 验证结果
        assert result is None
        # 验证缓存被查询
        storage.cache.get.assert_called_once_with("test_id")
        # 验证存储的load方法被调用
        storage.load.assert_called_once_with("test_id")
    
    @pytest.mark.asyncio
    async def test_update_with_metadata(self):
        """测试更新数据并处理元数据"""
        # 创建存储实例
        storage = TestStorage(
            temporal_manager=self.mock_temporal,
            metadata_manager=self.mock_metadata
        )
        
        # 模拟现有数据
        existing_data = {
            "id": "test_id",
            "content": "old_content",
            "metadata": {"category": "old", "priority": "low"}
        }
        storage.load = AsyncMock(return_value=existing_data)
        storage.save = AsyncMock(return_value=True)
        
        # 模拟元数据合并
        merged_metadata = {"category": "new", "priority": "low", "status": "active"}
        self.mock_metadata.merge_metadata.return_value = merged_metadata
        
        # 准备更新数据
        updates = {"content": "new_content", "extra_field": "extra_value"}
        metadata_updates = {"category": "new", "status": "active"}
        
        # 调用方法
        result = await storage.update_with_metadata("test_id", updates, metadata_updates)
        
        # 验证结果
        assert result is True
        # 验证load被调用
        storage.load.assert_called_once_with("test_id")
        # 验证save被调用
        storage.save.assert_called_once()
        
        # 检查保存的数据
        saved_data = storage.save.call_args[0][0]
        assert saved_data["content"] == "new_content"
        assert saved_data["extra_field"] == "extra_value"
        assert saved_data["updated_at"] == "2023-01-01T12:00:00"
        assert saved_data["metadata"] == merged_metadata
        
        # 验证元数据合并被调用
        self.mock_metadata.merge_metadata.assert_called_once_with(
            {"category": "old", "priority": "low"},
            metadata_updates
        )
    
    @pytest.mark.asyncio
    async def test_update_with_metadata_no_existing_data(self):
        """测试更新不存在的数据"""
        # 创建存储实例
        storage = TestStorage()
        
        # 模拟无现有数据
        storage.load = AsyncMock(return_value=None)
        storage.save = AsyncMock()  # 需要显式设置 save 为 Mock 对象
        
        # 调用方法
        result = await storage.update_with_metadata("nonexistent_id", {"content": "new_content"})
        
        # 验证结果
        assert result is False
        # 验证save没有被调用
        storage.save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_with_metadata_no_metadata_updates(self):
        """测试更新数据但不更新元数据"""
        # 创建存储实例
        storage = TestStorage(temporal_manager=self.mock_temporal)
        
        # 模拟现有数据（无元数据）
        existing_data = {
            "id": "test_id",
            "content": "old_content"
        }
        storage.load = AsyncMock(return_value=existing_data)
        storage.save = AsyncMock(return_value=True)
        
        # 准备更新数据
        updates = {"content": "new_content"}
        
        # 调用方法
        result = await storage.update_with_metadata("test_id", updates)
        
        # 验证结果
        assert result is True
        # 验证save被调用
        storage.save.assert_called_once()
        
        # 检查保存的数据
        saved_data = storage.save.call_args[0][0]
        assert saved_data["content"] == "new_content"
        assert saved_data["updated_at"] == "2023-01-01T12:00:00"
    
    @pytest.mark.asyncio
    async def test_update_with_metadata_with_cache(self):
        """测试更新数据并更新缓存"""
        # 创建存储实例，包含缓存
        storage = TestStorage(
            temporal_manager=self.mock_temporal,
            cache_manager=self.mock_cache
        )
        
        # 模拟现有数据
        existing_data = {
            "id": "test_id",
            "content": "old_content"
        }
        storage.load = AsyncMock(return_value=existing_data)
        storage.save = AsyncMock(return_value=True)
        assert storage.cache is not None
        storage.cache.set = AsyncMock()
        
        # 准备更新数据
        updates = {"content": "new_content"}
        
        # 调用方法
        result = await storage.update_with_metadata("test_id", updates)
        
        # 验证结果
        assert result is True
        # 验证缓存被更新
        storage.cache.set.assert_called_once_with("test_id", existing_data)
    
    @pytest.mark.asyncio
    async def test_list_by_metadata(self):
        """测试根据元数据过滤列表"""
        # 创建存储实例
        storage = TestStorage()
        
        # 模拟数据列表
        all_data = [
            {
                "id": "1",
                "content": "data1",
                "metadata": {"category": "A", "priority": "high"}
            },
            {
                "id": "2", 
                "content": "data2",
                "metadata": {"category": "B", "priority": "low"}
            },
            {
                "id": "3",
                "content": "data3", 
                "metadata": {"category": "A", "priority": "low"}
            }
        ]
        storage.list = AsyncMock(return_value=all_data)
        
        # 测试过滤
        result = await storage.list_by_metadata({"category": "A"})
        
        # 验证结果
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"
        
        # 验证list被调用
        storage.list.assert_called_once_with({})
    
    @pytest.mark.asyncio
    async def test_list_by_metadata_with_limit(self):
        """测试带限制的元数据过滤列表"""
        # 创建存储实例
        storage = TestStorage()
        
        # 模拟数据列表
        all_data = [
            {
                "id": "1",
                "content": "data1",
                "metadata": {"category": "A", "priority": "high"}
            },
            {
                "id": "2",
                "content": "data2", 
                "metadata": {"category": "A", "priority": "low"}
            },
            {
                "id": "3",
                "content": "data3",
                "metadata": {"category": "A", "priority": "medium"}
            }
        ]
        storage.list = AsyncMock(return_value=all_data)
        
        # 测试过滤并限制为2个结果
        result = await storage.list_by_metadata({"category": "A"}, limit=2)
        
        # 验证结果
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
    
    @pytest.mark.asyncio
    async def test_list_by_metadata_no_matches(self):
        """测试元数据过滤无匹配"""
        # 创建存储实例
        storage = TestStorage()
        
        # 模拟数据列表
        all_data = [
            {
                "id": "1",
                "content": "data1", 
                "metadata": {"category": "A", "priority": "high"}
            },
            {
                "id": "2",
                "content": "data2",
                "metadata": {"category": "B", "priority": "low"}
            }
        ]
        storage.list = AsyncMock(return_value=all_data)
        
        # 测试过滤无匹配
        result = await storage.list_by_metadata({"category": "C"})
        
        # 验证结果
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_delete_with_cache(self):
        """测试删除数据并清理缓存"""
        # 创建存储实例，包含缓存
        storage = TestStorage(cache_manager=self.mock_cache)
        
        # 模拟删除操作
        storage.delete = AsyncMock(return_value=True)
        assert storage.cache is not None
        storage.cache.delete = AsyncMock()
        
        # 调用方法
        result = await storage.delete_with_cache("test_id")
        
        # 验证结果
        assert result is True
        # 验证删除被调用
        storage.delete.assert_called_once_with("test_id")
        # 验证缓存清理被调用
        storage.cache.delete.assert_called_once_with("test_id")
    
    @pytest.mark.asyncio
    async def test_delete_with_cache_failure(self):
        """测试删除失败时不清理缓存"""
        # 创建存储实例，包含缓存
        storage = TestStorage(cache_manager=self.mock_cache)
        
        # 模拟删除失败
        storage.delete = AsyncMock(return_value=False)
        assert storage.cache is not None
        storage.cache.delete = AsyncMock()
        
        # 调用方法
        result = await storage.delete_with_cache("test_id")
        
        # 验证结果
        assert result is False
        # 验证删除被调用
        storage.delete.assert_called_once_with("test_id")
        # 验证缓存清理没有被调用
        storage.cache.delete.assert_not_called()


# 运行测试的辅助函数
def run_storage_tests():
    """运行存储测试"""
    print("运行 BaseStorage 测试...")
    # 这里可以添加更多特定的测试用例


if __name__ == "__main__":
    pytest.main([__file__])