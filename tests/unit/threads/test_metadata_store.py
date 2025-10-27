"""Thread元数据存储单元测试"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from src.infrastructure.threads.metadata_store import (
    IThreadMetadataStore,
    FileThreadMetadataStore,
    MemoryThreadMetadataStore
)


class TestFileThreadMetadataStore:
    """文件Thread元数据存储测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def metadata_store(self, temp_dir):
        """创建文件元数据存储实例"""
        return FileThreadMetadataStore(temp_dir)
    
    @pytest.mark.asyncio
    async def test_save_metadata_success(self, metadata_store, temp_dir):
        """测试成功保存元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active",
            "created_at": "2023-01-01T00:00:00"
        }
        
        # 执行测试
        result = await metadata_store.save_metadata(thread_id, metadata)
        
        # 验证结果
        assert result is True
        
        # 验证文件是否创建
        metadata_file = temp_dir / "thread_metadata" / f"{thread_id}.json"
        assert metadata_file.exists()
        
        # 验证文件内容
        with open(metadata_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data == metadata
    
    @pytest.mark.asyncio
    async def test_save_metadata_failure(self, metadata_store):
        """测试保存元数据失败"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {"thread_id": thread_id}
        
        # 模拟文件写入失败
        with patch('builtins.open', side_effect=IOError("写入失败")):
            # 执行测试
            result = await metadata_store.save_metadata(thread_id, metadata)
            
            # 验证结果
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_metadata_exists(self, metadata_store, temp_dir):
        """测试获取存在的元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active"
        }
        
        # 创建元数据文件
        metadata_dir = temp_dir / "thread_metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / f"{thread_id}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)
        
        # 执行测试
        result = await metadata_store.get_metadata(thread_id)
        
        # 验证结果
        assert result == metadata
    
    @pytest.mark.asyncio
    async def test_get_metadata_not_exists(self, metadata_store):
        """测试获取不存在的元数据"""
        # 执行测试
        result = await metadata_store.get_metadata("nonexistent_thread")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_metadata_file_error(self, metadata_store):
        """测试获取元数据时文件读取错误"""
        # 模拟文件读取错误
        with patch('builtins.open', side_effect=IOError("读取失败")):
            # 执行测试
            result = await metadata_store.get_metadata("thread_test123")
            
            # 验证结果
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_metadata_success(self, metadata_store, temp_dir):
        """测试成功更新元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        original_metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active",
            "created_at": "2023-01-01T00:00:00"
        }
        
        # 创建原始元数据文件
        metadata_dir = temp_dir / "thread_metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / f"{thread_id}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(original_metadata, f)
        
        # 执行更新
        updates = {
            "status": "completed",
            "description": "Updated thread"
        }
        result = await metadata_store.update_metadata(thread_id, updates)
        
        # 验证结果
        assert result is True
        
        # 验证文件内容
        with open(metadata_file, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        
        assert updated_data["thread_id"] == thread_id
        assert updated_data["graph_id"] == "test_graph"
        assert updated_data["status"] == "completed"
        assert updated_data["description"] == "Updated thread"
        assert updated_data["created_at"] == "2023-01-01T00:00:00"
    
    @pytest.mark.asyncio
    async def test_update_metadata_not_exists(self, metadata_store):
        """测试更新不存在的元数据"""
        # 执行更新
        updates = {"status": "completed"}
        result = await metadata_store.update_metadata("nonexistent_thread", updates)
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_metadata_success(self, metadata_store, temp_dir):
        """测试成功删除元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {"thread_id": thread_id}
        
        # 创建元数据文件
        metadata_dir = temp_dir / "thread_metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / f"{thread_id}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)
        
        # 验证文件存在
        assert metadata_file.exists()
        
        # 执行删除
        result = await metadata_store.delete_metadata(thread_id)
        
        # 验证结果
        assert result is True
        assert not metadata_file.exists()
    
    @pytest.mark.asyncio
    async def test_delete_metadata_not_exists(self, metadata_store):
        """测试删除不存在的元数据"""
        # 执行删除
        result = await metadata_store.delete_metadata("nonexistent_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_threads(self, metadata_store, temp_dir):
        """测试列出所有Threads"""
        # 准备测试数据
        threads_data = [
            {"thread_id": "thread1", "status": "active"},
            {"thread_id": "thread2", "status": "completed"},
            {"thread_id": "thread3", "status": "active"}
        ]
        
        # 创建元数据文件
        metadata_dir = temp_dir / "thread_metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        for thread in threads_data:
            metadata_file = metadata_dir / f"{thread['thread_id']}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(thread, f)
        
        # 执行测试
        result = await metadata_store.list_threads()
        
        # 验证结果
        assert len(result) == 3
        
        # 验证内容（由于文件系统遍历顺序不确定，我们只验证数量和内容）
        result_thread_ids = {t["thread_id"] for t in result}
        expected_thread_ids = {"thread1", "thread2", "thread3"}
        assert result_thread_ids == expected_thread_ids
    
    @pytest.mark.asyncio
    async def test_list_threads_with_invalid_files(self, metadata_store, temp_dir):
        """测试列出Threads时包含无效文件"""
        # 准备测试数据
        valid_thread = {"thread_id": "thread1", "status": "active"}
        
        # 创建元数据文件
        metadata_dir = temp_dir / "thread_metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建有效的元数据文件
        valid_file = metadata_dir / "thread1.json"
        with open(valid_file, 'w', encoding='utf-8') as f:
            json.dump(valid_thread, f)
        
        # 创建无效的JSON文件
        invalid_file = metadata_dir / "thread2.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json")
        
        # 创建非JSON文件
        non_json_file = metadata_dir / "readme.txt"
        with open(non_json_file, 'w', encoding='utf-8') as f:
            f.write("This is not a JSON file")
        
        # 执行测试
        result = await metadata_store.list_threads()
        
        # 验证结果（应该只包含有效的文件）
        assert len(result) == 1
        assert result[0]["thread_id"] == "thread1"
    
    @pytest.mark.asyncio
    async def test_thread_exists_true(self, metadata_store, temp_dir):
        """测试Thread存在（存在）"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {"thread_id": thread_id}
        
        # 创建元数据文件
        metadata_dir = temp_dir / "thread_metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / f"{thread_id}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)
        
        # 执行测试
        result = await metadata_store.thread_exists(thread_id)
        
        # 验证结果
        assert result is True
    
    @pytest.mark.asyncio
    async def test_thread_exists_false(self, metadata_store):
        """测试Thread存在（不存在）"""
        # 执行测试
        result = await metadata_store.thread_exists("nonexistent_thread")
        
        # 验证结果
        assert result is False


class TestMemoryThreadMetadataStore:
    """内存Thread元数据存储测试类"""
    
    @pytest.fixture
    def metadata_store(self):
        """创建内存元数据存储实例"""
        return MemoryThreadMetadataStore()
    
    @pytest.mark.asyncio
    async def test_save_metadata_success(self, metadata_store):
        """测试成功保存元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active"
        }
        
        # 执行测试
        result = await metadata_store.save_metadata(thread_id, metadata)
        
        # 验证结果
        assert result is True
        
        # 验证数据是否保存
        saved_metadata = await metadata_store.get_metadata(thread_id)
        assert saved_metadata == metadata
    
    @pytest.mark.asyncio
    async def test_get_metadata_exists(self, metadata_store):
        """测试获取存在的元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active"
        }
        
        # 保存元数据
        await metadata_store.save_metadata(thread_id, metadata)
        
        # 执行测试
        result = await metadata_store.get_metadata(thread_id)
        
        # 验证结果
        assert result == metadata
        
        # 验证返回的是副本（修改返回值不应影响存储）
        result["status"] = "modified"
        original_metadata = await metadata_store.get_metadata(thread_id)
        assert original_metadata["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_metadata_not_exists(self, metadata_store):
        """测试获取不存在的元数据"""
        # 执行测试
        result = await metadata_store.get_metadata("nonexistent_thread")
        
        # 验证结果
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_metadata_success(self, metadata_store):
        """测试成功更新元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        original_metadata = {
            "thread_id": thread_id,
            "graph_id": "test_graph",
            "status": "active",
            "created_at": "2023-01-01T00:00:00"
        }
        
        # 保存原始元数据
        await metadata_store.save_metadata(thread_id, original_metadata)
        
        # 执行更新
        updates = {
            "status": "completed",
            "description": "Updated thread"
        }
        result = await metadata_store.update_metadata(thread_id, updates)
        
        # 验证结果
        assert result is True
        
        # 验证更新后的数据
        updated_metadata = await metadata_store.get_metadata(thread_id)
        assert updated_metadata["thread_id"] == thread_id
        assert updated_metadata["graph_id"] == "test_graph"
        assert updated_metadata["status"] == "completed"
        assert updated_metadata["description"] == "Updated thread"
        assert updated_metadata["created_at"] == "2023-01-01T00:00:00"
    
    @pytest.mark.asyncio
    async def test_update_metadata_not_exists(self, metadata_store):
        """测试更新不存在的元数据"""
        # 执行更新
        updates = {"status": "completed"}
        result = await metadata_store.update_metadata("nonexistent_thread", updates)
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_metadata_success(self, metadata_store):
        """测试成功删除元数据"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {"thread_id": thread_id}
        
        # 保存元数据
        await metadata_store.save_metadata(thread_id, metadata)
        
        # 验证数据存在
        assert await metadata_store.thread_exists(thread_id)
        
        # 执行删除
        result = await metadata_store.delete_metadata(thread_id)
        
        # 验证结果
        assert result is True
        assert not await metadata_store.thread_exists(thread_id)
    
    @pytest.mark.asyncio
    async def test_delete_metadata_not_exists(self, metadata_store):
        """测试删除不存在的元数据"""
        # 执行删除
        result = await metadata_store.delete_metadata("nonexistent_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_threads(self, metadata_store):
        """测试列出所有Threads"""
        # 准备测试数据
        threads_data = [
            {"thread_id": "thread1", "status": "active"},
            {"thread_id": "thread2", "status": "completed"},
            {"thread_id": "thread3", "status": "active"}
        ]
        
        # 保存元数据
        for thread in threads_data:
            await metadata_store.save_metadata(thread["thread_id"], thread)
        
        # 执行测试
        result = await metadata_store.list_threads()
        
        # 验证结果
        assert len(result) == 3
        
        # 验证内容
        result_thread_ids = {t["thread_id"] for t in result}
        expected_thread_ids = {"thread1", "thread2", "thread3"}
        assert result_thread_ids == expected_thread_ids
        
        # 验证返回的是副本
        result[0]["status"] = "modified"
        original_metadata = await metadata_store.get_metadata(result[0]["thread_id"])
        assert original_metadata["status"] != "modified"
    
    @pytest.mark.asyncio
    async def test_thread_exists_true(self, metadata_store):
        """测试Thread存在（存在）"""
        # 准备测试数据
        thread_id = "thread_test123"
        metadata = {"thread_id": thread_id}
        
        # 保存元数据
        await metadata_store.save_metadata(thread_id, metadata)
        
        # 执行测试
        result = await metadata_store.thread_exists(thread_id)
        
        # 验证结果
        assert result is True
    
    @pytest.mark.asyncio
    async def test_thread_exists_false(self, metadata_store):
        """测试Thread存在（不存在）"""
        # 执行测试
        result = await metadata_store.thread_exists("nonexistent_thread")
        
        # 验证结果
        assert result is False
    
    @pytest.mark.asyncio
    async def test_clear(self, metadata_store):
        """测试清空所有元数据"""
        # 准备测试数据
        threads_data = [
            {"thread_id": "thread1", "status": "active"},
            {"thread_id": "thread2", "status": "completed"}
        ]
        
        # 保存元数据
        for thread in threads_data:
            await metadata_store.save_metadata(thread["thread_id"], thread)
        
        # 验证数据存在
        assert await metadata_store.thread_exists("thread1")
        assert await metadata_store.thread_exists("thread2")
        
        # 执行清空
        metadata_store.clear()
        
        # 验证数据已清空
        assert not await metadata_store.thread_exists("thread1")
        assert not await metadata_store.thread_exists("thread2")
        
        result = await metadata_store.list_threads()
        assert len(result) == 0