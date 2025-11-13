"""Gemini服务器端缓存管理器测试"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Any, Dict, List, Optional, Union

from src.infrastructure.llm.cache.gemini_server_cache_manager import GeminiServerCacheManager


class MockGeminiClient:
    """模拟Gemini客户端用于测试"""
    
    def __init__(self):
        self.caches = MockCachesManager()


class MockCachesManager:
    """模拟缓存管理器用于测试"""
    
    def __init__(self):
        self._caches: Dict[str, MockCache] = {}
    
    def create(self, model: str, config: Any) -> MockCache:
        cache_id = f"cache_{len(self._caches)}"
        cache = MockCache(cache_id, model)
        self._caches[cache_id] = cache
        return cache
    
    def get(self, name: str) -> Optional[MockCache]:
        return self._caches.get(name)
    
    def delete(self, name: str) -> bool:
        if name in self._caches:
            del self._caches[name]
            return True
        return False
    
    def update(self, name: str, config: Any) -> bool:
        if name in self._caches:
            # 模拟更新操作
            cache = self._caches[name]
            if hasattr(config, 'ttl'):
                cache._ttl = config.ttl
            return True
        return False
    
    def list(self) -> List[MockCache]:
        return list(self._caches.values())


class MockCache:
    """模拟缓存对象用于测试"""
    
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self._contents = []
        self._system_instruction = None
        self._ttl = "3600s"
        self._display_name = None
        self._created_at = datetime.now()
    
    @property
    def expire_time(self) -> str:
        # 模拟一个未来的过期时间
        expire = datetime.now() + timedelta(hours=1)
        return expire.isoformat() + "Z"


class MockContent:
    """模拟内容对象用于测试"""
    
    def __init__(self, text: str = "", uri: str = "", size: int = 0):
        self.text = text
        self.uri = uri
        self.size = size


class TestGeminiServerCacheManager:
    """测试Gemini服务器端缓存管理器"""
    
    def test_init(self):
        """测试初始化"""
        mock_client = MockGeminiClient()
        model_name = "gemini-2.0-flash-001"
        
        manager = GeminiServerCacheManager(mock_client, model_name)
        
        assert manager._client == mock_client
        assert manager._model_name == model_name
        assert manager._cache_registry == {}
        assert manager._cache_metadata == {}
    
    def test_init_empty_model_name(self):
        """测试空模型名称时抛出异常"""
        mock_client = MockGeminiClient()
        
        with pytest.raises(ValueError, match="模型名称不能为空"):
            GeminiServerCacheManager(mock_client, "")
    
    def test_create_cache_success(self):
        """测试成功创建缓存"""
        mock_client = MockGeminiClient()
        manager = GeminiServerCacheManager(mock_client, "gemini-2.0-flash-001")
        
        contents = ["test content"]
        system_instruction = "You are helpful"
        ttl = "1800s"
        display_name = "test_cache"
        
        cache = manager.create_cache(contents, system_instruction, ttl, display_name)
        
        assert cache is not None
        assert hasattr(cache, 'name')
        assert cache.model == "gemini-2.0-flash-001"
        
        # 验证缓存已注册
        cache_key = manager._generate_cache_key(contents, system_instruction)
        assert cache_key in manager._cache_registry
        assert manager._cache_registry[cache_key] == cache.name
        
        # 验证元数据
        assert cache.name in manager._cache_metadata
        metadata = manager._cache_metadata[cache.name]
        assert metadata["cache_key"] == cache_key
        assert metadata["display_name"] == display_name
        assert metadata["ttl"] == ttl
        assert metadata["contents_count"] == 1
    
    def test_get_cache_success(self):
        """测试成功获取缓存"""
        mock_client = MockGeminiClient()
        manager = GeminiServerCacheManager(mock_client, "gemini-2.0-flash-001")
        
        # 先创建缓存
        cache = manager.create_cache(["test content"], display_name="test_cache")
        cache_name = cache.name
        
        # 获取缓存
        retrieved_cache = manager.get_cache(cache_name)
        assert retrieved_cache is not None
        assert retrieved_cache.name == cache_name
    
    def test_delete_cache_success(self):
        """测试成功删除缓存"""
        mock_client = MockGeminiClient()
        manager = GeminiServerCacheManager(mock_client, "gemini-2.0-flash-001")
        
        # 创建缓存
        cache = manager.create_cache(["test content"], display_name="test_cache")
        cache_name = cache.name
        
        # 删除缓存
        result = manager.delete_cache(cache_name)
        assert result is True
        
        # 验证缓存已删除
        assert cache_name not in manager._cache_metadata
    
    def test_should_use_server_cache_large_content(self):
        """测试大内容使用服务器端缓存的判断"""
        mock_client = MockGeminiClient()
        manager = GeminiServerCacheManager(mock_client, "gemini-2.0-flash-001")
        
        # 小内容
        small_contents = [MockContent(text="small", size=1024)]
        assert manager.should_use_server_cache(small_contents, 2048) is False
        
        # 大内容
        large_contents = [MockContent(text="large" * 1024, size=4096)]  # 超过阈值
        assert manager.should_use_server_cache(large_contents, 2048) is True
    
    def test_generate_cache_key(self):
        """测试生成缓存键"""
        mock_client = MockGeminiClient()
        manager = GeminiServerCacheManager(mock_client, "gemini-2.0-flash-001")
        
        contents = ["test content"]
        system_instruction = "You are helpful"
        
        key1 = manager._generate_cache_key(contents, system_instruction)
        key2 = manager._generate_cache_key(contents, system_instruction)
        
        # 相同参数应该生成相同键
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5哈希长度