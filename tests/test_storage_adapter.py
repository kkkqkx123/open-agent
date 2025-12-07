"""存储适配器测试

测试存储适配器的功能和集成。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.interfaces.storage.base import IStorage
from src.interfaces.storage.exceptions import StorageError
from src.adapters.storage.adapter.storage_adapter import StorageAdapter
from src.adapters.storage.adapter.data_transformer import DefaultDataTransformer
from src.infrastructure.error_management.impl.storage_adapter import StorageAdapterErrorHandler


class TestStorageAdapter:
    """存储适配器测试类"""
    
    @pytest.fixture
    def mock_backend(self):
        """模拟存储后端"""
        backend = Mock(spec=IStorage)
        backend.save = AsyncMock(return_value="test_id")
        backend.load = AsyncMock(return_value={"key": "value"})
        backend.update = AsyncMock(return_value=True)
        backend.delete = AsyncMock(return_value=True)
        backend.exists = AsyncMock(return_value=True)
        backend.list = AsyncMock(return_value=[{"key": "value"}])
        backend.count = AsyncMock(return_value=1)
        backend.batch_save = AsyncMock(return_value=["id1", "id2"])
        backend.batch_delete = AsyncMock(return_value=2)
        backend.health_check = AsyncMock(return_value={"status": "healthy"})
        return backend
    
    @pytest.fixture
    def data_transformer(self):
        """数据转换器"""
        return DefaultDataTransformer()
    
    @pytest.fixture
    def error_handler(self):
        """错误处理器"""
        return StorageAdapterErrorHandler()
    
    @pytest.fixture
    def storage_adapter(self, mock_backend, data_transformer, error_handler):
        """存储适配器"""
        return StorageAdapter(
            backend=mock_backend,
            transformer=data_transformer,
            error_handler=error_handler
        )
    
    @pytest.mark.asyncio
    async def test_save(self, storage_adapter, mock_backend):
        """测试保存数据"""
        data = {"test": "data"}
        result = await storage_adapter.save(data)
        
        assert result == "test_id"
        mock_backend.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load(self, storage_adapter, mock_backend):
        """测试加载数据"""
        result = await storage_adapter.load("test_id")
        
        assert result == {"key": "value"}
        mock_backend.load.assert_called_once_with("test_id")
    
    @pytest.mark.asyncio
    async def test_update(self, storage_adapter, mock_backend):
        """测试更新数据"""
        updates = {"key": "new_value"}
        result = await storage_adapter.update("test_id", updates)
        
        assert result is True
        mock_backend.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete(self, storage_adapter, mock_backend):
        """测试删除数据"""
        result = await storage_adapter.delete("test_id")
        
        assert result is True
        mock_backend.delete.assert_called_once_with("test_id")
    
    @pytest.mark.asyncio
    async def test_exists(self, storage_adapter, mock_backend):
        """测试检查数据存在性"""
        result = await storage_adapter.exists("test_id")
        
        assert result is True
        mock_backend.exists.assert_called_once_with("test_id")
    
    @pytest.mark.asyncio
    async def test_list(self, storage_adapter, mock_backend):
        """测试列出数据"""
        filters = {"type": "test"}
        result = await storage_adapter.list(filters, 10)
        
        assert result == [{"key": "value"}]
        mock_backend.list.assert_called_once_with(filters, 10)
    
    @pytest.mark.asyncio
    async def test_count(self, storage_adapter, mock_backend):
        """测试计数数据"""
        filters = {"type": "test"}
        result = await storage_adapter.count(filters)
        
        assert result == 1
        mock_backend.count.assert_called_once_with(filters)
    
    @pytest.mark.asyncio
    async def test_batch_save(self, storage_adapter, mock_backend):
        """测试批量保存"""
        data_list = [{"key": "value1"}, {"key": "value2"}]
        result = await storage_adapter.batch_save(data_list)
        
        assert result == ["id1", "id2"]
        mock_backend.batch_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_delete(self, storage_adapter, mock_backend):
        """测试批量删除"""
        ids = ["id1", "id2"]
        result = await storage_adapter.batch_delete(ids)
        
        assert result == 2
        mock_backend.batch_delete.assert_called_once_with(ids)
    
    @pytest.mark.asyncio
    async def test_health_check(self, storage_adapter, mock_backend):
        """测试健康检查"""
        result = await storage_adapter.health_check()
        
        assert "status" in result
        assert "adapter" in result
        mock_backend.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_with_error(self, storage_adapter, mock_backend):
        """测试保存数据时的错误处理"""
        mock_backend.save.side_effect = StorageError("保存失败")
        
        with pytest.raises(StorageError):
            await storage_adapter.save({"test": "data"})
    
    @pytest.mark.asyncio
    async def test_load_not_found(self, storage_adapter, mock_backend):
        """测试加载不存在的数据"""
        mock_backend.load.return_value = None
        
        result = await storage_adapter.load("nonexistent_id")
        
        assert result is None


class TestDataTransformer:
    """数据转换器测试类"""
    
    @pytest.fixture
    def transformer(self):
        """数据转换器"""
        return DefaultDataTransformer()
    
    def test_to_storage_format_dict(self, transformer):
        """测试字典转存储格式"""
        data = {"key": "value", "number": 42}
        result = transformer.to_storage_format(data)
        
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42
        assert "_processed_at" in result
    
    def test_from_storage_format_dict(self, transformer):
        """测试存储格式转字典"""
        data = {"key": "value", "number": 42, "_processed_at": "2023-01-01T00:00:00"}
        result = transformer.from_storage_format(data)
        
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42
        assert "_processed_at" not in result
    
    def test_to_storage_format_object(self, transformer):
        """测试对象转存储格式"""
        class TestObject:
            def __init__(self):
                self.value = "test"
            
            def to_dict(self):
                return {"value": self.value}
        
        obj = TestObject()
        result = transformer.to_storage_format(obj)
        
        assert isinstance(result, dict)
        assert result["value"] == "test"
    
    def test_to_storage_format_basic_types(self, transformer):
        """测试基本类型转存储格式"""
        # 字符串
        result = transformer.to_storage_format("test")
        assert result["value"] == "test"
        assert result["type"] == "str"
        
        # 数字
        result = transformer.to_storage_format(42)
        assert result["value"] == 42
        assert result["type"] == "int"
        
        # 布尔值
        result = transformer.to_storage_format(True)
        assert result["value"] is True
        assert result["type"] == "bool"
    
    def test_from_storage_format_basic_types(self, transformer):
        """测试存储格式转基本类型"""
        # 字符串
        result = transformer.from_storage_format({"value": "test", "type": "str"})
        assert result == "test"
        
        # 数字
        result = transformer.from_storage_format({"value": "42", "type": "int"})
        assert result == 42
        
        # 布尔值
        result = transformer.from_storage_format({"value": "true", "type": "bool"})
        assert result is True


class TestStorageAdapterErrorHandler:
    """存储适配器错误处理器测试类"""
    
    @pytest.fixture
    def error_handler(self):
        """错误处理器"""
        return StorageAdapterErrorHandler(max_retries=2)
    
    @pytest.mark.asyncio
    async def test_successful_operation(self, error_handler):
        """测试成功操作"""
        operation = Mock(return_value="success")
        result = await error_handler.handle("test_operation", operation)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, error_handler):
        """测试连接错误重试"""
        from src.interfaces.storage.exceptions import StorageConnectionError
        
        operation = Mock()
        operation.side_effect = [
            StorageConnectionError("连接失败"),
            StorageConnectionError("连接失败"),
            "success"
        ]
        
        result = await error_handler.handle("test_operation", operation)
        
        assert result == "success"
        assert operation.call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, error_handler):
        """测试超过最大重试次数"""
        from src.interfaces.storage.exceptions import StorageConnectionError
        
        operation = Mock()
        operation.side_effect = StorageConnectionError("连接失败")
        
        with pytest.raises(StorageConnectionError):
            await error_handler.handle("test_operation", operation)
        
        assert operation.call_count == 3  # 初始调用 + 2次重试
    
    @pytest.mark.asyncio
    async def test_non_retryable_error(self, error_handler):
        """测试不可重试错误"""
        from src.interfaces.storage.exceptions import StorageValidationError
        
        operation = Mock()
        operation.side_effect = StorageValidationError("验证失败")
        
        with pytest.raises(StorageValidationError):
            await error_handler.handle("test_operation", operation)
        
        assert operation.call_count == 1  # 不重试


if __name__ == "__main__":
    pytest.main([__file__])