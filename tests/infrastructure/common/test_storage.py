"""存储模块单元测试

测试基础设施层存储系统的基本功能。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.infrastructure.common.storage import BaseStorage
from src.infrastructure.common.serialization import Serializer
from src.infrastructure.common.utils.temporal import TemporalManager
from src.infrastructure.common.utils.metadata import MetadataManager
from src.infrastructure.common.cache import CacheManager


class TestBaseStorage:
    """测试基础存储类"""

    @pytest.fixture
    def mock_dependencies(self):
        """创建模拟依赖项"""
        mock_serializer = Mock(spec=Serializer)
        mock_temporal = Mock(spec=TemporalManager)
        mock_metadata = Mock(spec=MetadataManager)
        mock_cache = AsyncMock(spec=CacheManager)
        
        # 设置默认返回值
        mock_temporal.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_temporal.format_timestamp.return_value = "2023-01-01T12:00:00"
        mock_metadata.normalize_metadata.return_value = {"normalized": True}
        mock_metadata.merge_metadata.return_value = {"merged": True}
        
        return {
            "serializer": mock_serializer,
            "temporal": mock_temporal,
            "metadata": mock_metadata,
            "cache": mock_cache,
        }

    @pytest.fixture
    def storage(self, mock_dependencies):
        """创建存储实例"""
        # 创建BaseStorage的子类以测试具体方法
        class ConcreteStorage(BaseStorage):
            async def save(self, data: Dict[str, Any]) -> str:
                return "test_id"
            
            async def load(self, id: str) -> Optional[Dict[str, Any]]:
                return {"id": id, "data": "test"} if id else None
            
            async def delete(self, id: str) -> bool:
                return True if id else False
            
            async def update(self, id: str, updates: Dict[str, Any]) -> bool:
                return True
            
            async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
                return [{"id": "1", "data": "test1"}, {"id": "2", "data": "test2"}]
            
            async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
                return []
            
            async def exists(self, id: str) -> bool:
                return True
            
            async def count(self, filters: Dict[str, Any]) -> int:
                return 0
            
            async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
                return True
            
            async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
                return ["id1"]
            
            async def batch_delete(self, ids: List[str]) -> int:
                return 0
            
            def stream_list(self, filters: Dict[str, Any], batch_size: int = 100):
                async def _empty_iterator():
                    yield []
                return _empty_iterator()
            
            async def health_check(self) -> Dict[str, Any]:
                return {}
        
        return ConcreteStorage(
            serializer=mock_dependencies["serializer"],
            temporal_manager=mock_dependencies["temporal"],
            metadata_manager=mock_dependencies["metadata"],
            cache_manager=mock_dependencies["cache"],
        )

    @pytest.mark.asyncio
    async def test_storage_initialization(self, mock_dependencies):
        """测试存储初始化"""
        class ConcreteStorage(BaseStorage):
            async def save(self, data: Dict[str, Any]) -> str:
                return "test_id"
            async def load(self, id: str) -> Optional[Dict[str, Any]]:
                return None
            async def delete(self, id: str) -> bool:
                return True
            async def update(self, id: str, updates: Dict[str, Any]) -> bool:
                return True
            async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
                return []
            async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
                return []
            async def exists(self, id: str) -> bool:
                return True
            async def count(self, filters: Dict[str, Any]) -> int:
                return 0
            async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
                return True
            async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
                return []
            async def batch_delete(self, ids: List[str]) -> int:
                return 0
            def stream_list(self, filters: Dict[str, Any], batch_size: int = 100):
                async def _empty_iterator():
                    yield []
                return _empty_iterator()
            async def health_check(self) -> Dict[str, Any]:
                return {}
        
        storage = ConcreteStorage(
            serializer=mock_dependencies["serializer"],
            temporal_manager=mock_dependencies["temporal"],
            metadata_manager=mock_dependencies["metadata"],
            cache_manager=mock_dependencies["cache"],
        )
        
        assert storage.serializer == mock_dependencies["serializer"]
        assert storage.temporal == mock_dependencies["temporal"]
        assert storage.metadata == mock_dependencies["metadata"]
        assert storage.cache == mock_dependencies["cache"]

    @pytest.mark.asyncio
    async def test_save_with_metadata(self, storage, mock_dependencies):
        """测试保存数据并处理元数据"""
        data = {"key": "value"}
        metadata = {"meta": "data"}
        
        # 模拟save方法
        with patch.object(storage, 'save', AsyncMock(return_value="saved_id")):
            result = await storage.save_with_metadata(data, metadata, ttl=3600)
        
        assert result is True
        mock_dependencies["temporal"].format_timestamp.assert_called()
        mock_dependencies["metadata"].normalize_metadata.assert_called_with(metadata)
        
        # 验证缓存调用
        if storage.cache:
            storage.cache.set.assert_called_once_with("saved_id", data, ttl=3600)

    @pytest.mark.asyncio
    async def test_save_with_metadata_no_cache(self, mock_dependencies):
        """测试无缓存时保存数据"""
        # 创建没有缓存的存储
        class ConcreteStorage(BaseStorage):
            async def save(self, data: Dict[str, Any]) -> str:
                return "test_id"
            async def load(self, id: str) -> Optional[Dict[str, Any]]:
                return None
            async def delete(self, id: str) -> bool:
                return True
            async def update(self, id: str, updates: Dict[str, Any]) -> bool:
                return True
            async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
                return []
            async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
                return []
            async def exists(self, id: str) -> bool:
                return True
            async def count(self, filters: Dict[str, Any]) -> int:
                return 0
            async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
                return True
            async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
                return []
            async def batch_delete(self, ids: List[str]) -> int:
                return 0
            def stream_list(self, filters: Dict[str, Any], batch_size: int = 100):
                async def _empty_iterator():
                    yield []
                return _empty_iterator()
            async def health_check(self) -> Dict[str, Any]:
                return {}
        
        storage = ConcreteStorage(
            serializer=mock_dependencies["serializer"],
            temporal_manager=mock_dependencies["temporal"],
            metadata_manager=mock_dependencies["metadata"],
            cache_manager=None,  # 无缓存
        )
        
        with patch.object(storage, 'save', AsyncMock(return_value="saved_id")):
            result = await storage.save_with_metadata({"key": "value"})
        
        assert result is True
        # 缓存不应被调用
        mock_dependencies["cache"].set.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_with_cache_hit(self, storage, mock_dependencies):
        """测试从缓存加载数据（命中）"""
        cached_data = {"id": "test_id", "data": "cached"}
        mock_dependencies["cache"].get.return_value = cached_data
        
        with patch.object(storage, 'load') as mock_load:
            result = await storage.load_with_cache("test_id")
            
            assert result == cached_data
            mock_dependencies["cache"].get.assert_called_once_with("test_id")
            # 不应调用底层load方法
            mock_load.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_with_cache_miss(self, storage, mock_dependencies):
        """测试从缓存加载数据（未命中）"""
        mock_dependencies["cache"].get.return_value = None
        storage_data = {"id": "test_id", "data": "from_storage"}
        storage.load = AsyncMock(return_value=storage_data)
        
        result = await storage.load_with_cache("test_id")
        
        assert result == storage_data
        mock_dependencies["cache"].get.assert_called_once_with("test_id")
        storage.load.assert_called_once_with("test_id")
        # 应缓存结果
        mock_dependencies["cache"].set.assert_called_once_with("test_id", storage_data)

    @pytest.mark.asyncio
    async def test_load_with_cache_no_cache(self, mock_dependencies):
        """测试无缓存时加载数据"""
        class ConcreteStorage(BaseStorage):
            async def save(self, data: Dict[str, Any]) -> str:
                return "test_id"
            async def load(self, id: str) -> Optional[Dict[str, Any]]:
                return {"id": id, "data": "test"}
            async def delete(self, id: str) -> bool:
                return True
            async def update(self, id: str, updates: Dict[str, Any]) -> bool:
                return True
            async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
                return []
            async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
                return []
            async def exists(self, id: str) -> bool:
                return True
            async def count(self, filters: Dict[str, Any]) -> int:
                return 0
            async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
                return True
            async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
                return []
            async def batch_delete(self, ids: List[str]) -> int:
                return 0
            def stream_list(self, filters: Dict[str, Any], batch_size: int = 100):
                async def _empty_iterator():
                    yield []
                return _empty_iterator()
            async def health_check(self) -> Dict[str, Any]:
                return {}
        
        storage = ConcreteStorage(
            serializer=mock_dependencies["serializer"],
            temporal_manager=mock_dependencies["temporal"],
            metadata_manager=mock_dependencies["metadata"],
            cache_manager=None,
        )
        
        result = await storage.load_with_cache("test_id")
        assert result == {"id": "test_id", "data": "test"}
        # 缓存不应被调用
        mock_dependencies["cache"].get.assert_not_called()
        mock_dependencies["cache"].set.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_with_metadata(self, storage, mock_dependencies):
        """测试更新数据并处理元数据"""
        existing_data = {
            "id": "test_id",
            "key": "old_value",
            "created_at": "2023-01-01T00:00:00",
            "metadata": {"old": "meta"}
        }
        
        storage.load = AsyncMock(return_value=existing_data)
        storage.save = AsyncMock(return_value="updated_id")
        
        updates = {"key": "new_value"}
        metadata_updates = {"new": "meta"}
        
        result = await storage.update_with_metadata(
            "test_id", updates, metadata_updates
        )
        
        assert result is True
        storage.load.assert_called_once_with("test_id")
        storage.save.assert_called_once()
        
        # 验证时间戳更新
        mock_dependencies["temporal"].format_timestamp.assert_called()
        
        # 验证元数据合并
        mock_dependencies["metadata"].merge_metadata.assert_called_once_with(
            {"old": "meta"}, {"new": "meta"}
        )
        
        # 验证缓存更新
        if storage.cache:
            storage.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_with_metadata_not_found(self, storage):
        """测试更新不存在的数据"""
        storage.load = AsyncMock(return_value=None)
        
        with patch.object(storage, 'save') as mock_save:
            result = await storage.update_with_metadata(
                "nonexistent", {"key": "value"}
            )
            
            assert result is False
            mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_by_metadata(self, storage):
        """测试根据元数据过滤列表"""
        # 模拟list方法返回带元数据的数据
        storage.list = AsyncMock(return_value=[
            {"id": "1", "metadata": {"type": "A", "status": "active"}},
            {"id": "2", "metadata": {"type": "B", "status": "active"}},
            {"id": "3", "metadata": {"type": "A", "status": "inactive"}},
        ])
        
        filters = {"type": "A", "status": "active"}
        result = await storage.list_by_metadata(filters)
        
        assert len(result) == 1
        assert result[0]["id"] == "1"
        
        # 测试无匹配
        filters = {"type": "C"}
        result = await storage.list_by_metadata(filters)
        assert len(result) == 0
        
        # 测试限制数量
        storage.list = AsyncMock(return_value=[
            {"id": "1", "metadata": {"type": "A"}},
            {"id": "2", "metadata": {"type": "A"}},
            {"id": "3", "metadata": {"type": "A"}},
        ])
        
        result = await storage.list_by_metadata({"type": "A"}, limit=2)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_with_cache(self, storage, mock_dependencies):
        """测试删除数据并清理缓存"""
        storage.delete = AsyncMock(return_value=True)
        
        result = await storage.delete_with_cache("test_id")
        
        assert result is True
        storage.delete.assert_called_once_with("test_id")
        
        # 验证缓存清理
        if storage.cache:
            storage.cache.delete.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_delete_with_cache_failure(self, storage, mock_dependencies):
        """测试删除数据失败时不清理缓存"""
        storage.delete = AsyncMock(return_value=False)
        
        result = await storage.delete_with_cache("test_id")
        
        assert result is False
        storage.delete.assert_called_once_with("test_id")
        
        # 缓存不应被清理
        if storage.cache:
            storage.cache.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_with_cache_no_cache(self, mock_dependencies):
        """测试无缓存时删除数据"""
        class ConcreteStorage(BaseStorage):
            async def save(self, data: Dict[str, Any]) -> str:
                return "test_id"
            async def load(self, id: str) -> Optional[Dict[str, Any]]:
                return None
            async def delete(self, id: str) -> bool:
                return True
            async def update(self, id: str, updates: Dict[str, Any]) -> bool:
                return True
            async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
                return []
            async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
                return []
            async def exists(self, id: str) -> bool:
                return True
            async def count(self, filters: Dict[str, Any]) -> int:
                return 0
            async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
                return True
            async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
                return []
            async def batch_delete(self, ids: List[str]) -> int:
                return 0
            def stream_list(self, filters: Dict[str, Any], batch_size: int = 100):
                async def _empty_iterator():
                    yield []
                return _empty_iterator()
            async def health_check(self) -> Dict[str, Any]:
                return {}
        
        storage = ConcreteStorage(
            serializer=mock_dependencies["serializer"],
            temporal_manager=mock_dependencies["temporal"],
            metadata_manager=mock_dependencies["metadata"],
            cache_manager=None,
        )
        
        result = await storage.delete_with_cache("test_id")
        assert result is True
        # 缓存不应被调用
        mock_dependencies["cache"].delete.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])