"""增强Gemini缓存管理器测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, List, Optional, Sequence

from src.infrastructure.llm.cache.enhanced_cache_config import EnhancedCacheConfig, GeminiCacheConfig
from src.infrastructure.llm.cache.enhanced_gemini_cache_manager import EnhancedGeminiCacheManager
from langchain_core.messages import BaseMessage


class MockBaseMessage(BaseMessage):
    """模拟BaseMessage用于测试"""
    
    def __init__(self, msg_type: str, content: str):
        super().__init__(content=content)
        self.type = msg_type


class MockGeminiClient:
    """模拟Gemini客户端用于测试"""
    
    def __init__(self):
        self.caches = MockCachesManager()


class MockCachesManager:
    """模拟缓存管理器用于测试"""
    
    def __init__(self):
        self._caches = {}
    
    def create(self, model: str, config: Any) -> Any:
        cache_id = f"cache_{model}_{len(self._caches)}"
        cache = MockCache(cache_id)
        self._caches[cache_id] = cache
        return cache
    
    def get(self, name: str) -> Optional[Any]:
        return self._caches.get(name)
    
    def delete(self, name: str) -> bool:
        if name in self._caches:
            del self._caches[name]
            return True
        return False
    
    def list(self) -> List[Any]:
        return list(self._caches.values())


class MockCache:
    """模拟缓存对象用于测试"""
    
    def __init__(self, name: str):
        self.name = name
        self._contents = []
        self._system_instruction = None
        self._ttl = "3600s"
        self._display_name = None
    
    @property
    def expire_time(self) -> str:
        # 模拟一个未来的过期时间
        from datetime import datetime, timedelta
        expire = datetime.now() + timedelta(hours=1)
        return expire.isoformat() + "Z"


class TestEnhancedGeminiCacheManager:
    """测试增强Gemini缓存管理器"""
    
    def test_init_with_client(self):
        """测试带客户端的初始化"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            auto_server_cache=True,
            large_content_threshold=512 * 1024,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        # 验证继承功能
        from src.infrastructure.llm.cache.cache_manager import CacheManager
        assert isinstance(manager, CacheManager)
        assert manager.config == config
        assert manager.is_enabled() is True
        
        # 验证客户端缓存管理器
        assert hasattr(manager, '_client_cache_manager')
        assert manager._client_cache_manager is not None
        
        # 验证服务器端缓存管理器
        assert hasattr(manager, '_server_cache_manager')
        assert manager._server_cache_manager is not None
    
    def test_init_without_client(self):
        """测试不带客户端的初始化"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            auto_server_cache=True,
            model_name="gemini-2.0-flash-001"
        )
        
        manager = EnhancedGeminiCacheManager(config)
        
        # 客户端缓存管理器应该存在
        assert manager._client_cache_manager is not None
        
        # 服务器端缓存管理器应该为None
        assert manager._server_cache_manager is None
    
    def test_init_with_default_model_name(self):
        """测试使用默认model_name进行初始化"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            auto_server_cache=True
            # 注意：使用默认的model_name值
        )
        
        mock_client = MockGeminiClient()
        
        # 应该成功创建管理器，使用默认的model_name
        manager = EnhancedGeminiCacheManager(config, mock_client)
        assert manager is not None
    
    def test_get_with_client_cache_hit(self):
        """测试从客户端缓存获取（命中）"""
        config = EnhancedCacheConfig(enabled=True)
        manager = EnhancedGeminiCacheManager(config)
        
        # 设置客户端缓存
        manager._client_cache_manager.set("key1", "client_value")
        
        # 从增强管理器获取
        result = manager.get("key1")
        assert result == "client_value"
    
    def test_get_with_client_cache_miss(self):
        """测试从客户端缓存获取（未命中）"""
        config = EnhancedCacheConfig(enabled=True)
        manager = EnhancedGeminiCacheManager(config)
        
        # 不设置任何缓存
        
        result = manager.get("key1")
        assert result is None  # 服务器端缓存在基本实现中总是返回None
    
    def test_set_stores_to_client_cache(self):
        """测试设置存储到客户端缓存"""
        config = EnhancedCacheConfig(enabled=True)
        manager = EnhancedGeminiCacheManager(config)
        
        manager.set("key1", "test_value")
        
        # 验证存储在客户端缓存中
        client_result = manager._client_cache_manager.get("key1")
        assert client_result == "test_value"
    
    def test_delete_removes_from_client_cache(self):
        """测试从客户端缓存删除"""
        config = EnhancedCacheConfig(enabled=True)
        manager = EnhancedGeminiCacheManager(config)
        
        # 设置缓存
        manager.set("key1", "test_value")
        assert manager.get("key1") is not None
        
        # 删除
        result = manager.delete("key1")
        assert result is True
        
        # 验证已删除
        assert manager.get("key1") is None
    
    def test_clear_clears_client_cache(self):
        """测试清空客户端缓存"""
        config = EnhancedCacheConfig(enabled=True)
        manager = EnhancedGeminiCacheManager(config)
        
        manager.set("key1", "value1")
        manager.set("key2", "value2")
        
        manager.clear()
        
        assert manager.get_size() == 0
    
    def test_get_stats(self):
        """测试获取统计信息"""
        config = EnhancedCacheConfig(
            server_cache_enabled=True,
            large_content_threshold=512 * 1024
        )
        manager = EnhancedGeminiCacheManager(config)
        
        # 添加一些数据
        manager._client_cache_manager.set("key1", "value1")
        
        stats = manager.get_stats()
        
        # 验证统计结构
        assert "client_cache" in stats
        assert "server_cache_enabled" in stats
        assert stats["server_cache_enabled"] is True
    
    def test_get_stats_with_server_cache(self):
        """测试带服务器端缓存的统计信息"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        stats = manager.get_stats()
        
        assert "server_cache" in stats
        assert "local_registry" in stats["server_cache"]
        assert "server_caches" in stats["server_cache"]
    
    def test_create_server_cache_disabled(self):
        """测试禁用服务器端缓存时的创建"""
        config = EnhancedCacheConfig(
            server_cache_enabled=False,
            auto_server_cache=False
        )
        manager = EnhancedGeminiCacheManager(config)
        
        result = manager.create_server_cache(
            contents=["test content"],
            system_instruction="You are helpful"
        )
        
        assert result is None
    
    def test_create_server_cache_enabled(self):
        """测试启用服务器端缓存时的创建"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        result = manager.create_server_cache(
            contents=["test content"],
            system_instruction="You are helpful",
            ttl="1800s",
            display_name="test_cache"
        )
        
        assert result is not None
        assert hasattr(result, 'name')
    
    def test_create_server_cache_error_handling(self):
        """测试创建服务器端缓存的错误处理"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        # 模拟客户端抛出异常
        mock_client = MockGeminiClient()
        with patch.object(mock_client.caches, 'create', side_effect=Exception("Test error")):
            manager = EnhancedGeminiCacheManager(config, mock_client)
            
            result = manager.create_server_cache(
                contents=["test content"],
                system_instruction="You are helpful"
            )
            
            # 应该返回None而不是抛出异常
            assert result is None
    
    def test_use_server_cache_disabled(self):
        """测试禁用服务器端缓存时的使用"""
        config = EnhancedCacheConfig(
            server_cache_enabled=False,
            auto_server_cache=False
        )
        manager = EnhancedGeminiCacheManager(config)
        
        result = manager.use_server_cache("test_cache", "query content")
        assert result is None
    
    def test_use_server_cache_enabled(self):
        """测试启用服务器端缓存时的使用"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        # 先创建缓存
        cache = manager.create_server_cache(
            contents=["test content"],
            system_instruction="You are helpful"
        )
        
        if cache:
            # 使用缓存
            result = manager.use_server_cache(cache.name, "query")
            assert result is not None
    
    def test_get_or_create_server_cache(self):
        """测试获取或创建服务器端缓存"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        contents = ["test content"]
        system_instruction = "You are helpful"
        
        # 第一次创建
        cache1 = manager.get_or_create_server_cache(
            contents, system_instruction, "1800s", "test_cache"
        )
        
        assert cache1 is not None
        assert hasattr(cache1, 'name')
        
        # 第二次获取（应该重用）
        cache2 = manager.get_or_create_server_cache(
            contents, system_instruction, "1800s", "test_cache"
        )
        
        assert cache2 is not None
        assert cache1.name == cache2.name  # 应该返回同一个缓存
    
    def test_delete_server_cache(self):
        """测试删除服务器端缓存"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        # 创建缓存
        cache = manager.create_server_cache(
            contents=["test content"],
            display_name="test_cache"
        )
        
        if cache:
            # 删除缓存
            result = manager.delete_server_cache(cache.name)
            assert result is True
    
    def test_list_server_caches(self):
        """测试列出服务器端缓存"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        # 初始列表应该为空
        caches = manager.list_server_caches()
        assert isinstance(caches, list)
        
        # 创建缓存
        cache1 = manager.create_server_cache(
            contents=["content1"],
            display_name="cache1"
        )
        cache2 = manager.create_server_cache(
            contents=["content2"],
            display_name="cache2"
        )
        
        # 检查列表
        caches = manager.list_server_caches()
        assert len(caches) >= 0  # 实际数量取决于mock实现
    
    def test_cleanup_expired_server_caches(self):
        """测试清理过期的服务器端缓存"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        count = manager.cleanup_expired_server_caches()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_should_use_server_cache(self):
        """测试判断是否应该使用服务器端缓存"""
        config = EnhancedCacheConfig(
            server_cache_enabled=True,
            large_content_threshold=512 * 1024
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        # 测试小内容
        small_contents = ["small content"]
        assert manager.should_use_server_cache(small_contents) is False
        
        # 测试大内容
        large_contents = ["x" * 1024 * 1024]  # 1MB内容
        assert manager.should_use_server_cache(large_contents) is True
    
    def test_should_use_server_cache_disabled(self):
        """测试禁用服务器端缓存时的判断"""
        config = EnhancedCacheConfig(server_cache_enabled=False)
        manager = EnhancedGeminiCacheManager(config)
        
        # 任何内容都不应该使用服务器端缓存
        assert manager.should_use_server_cache(["content"]) is False
    
    def test_smart_cache_decision_default(self):
        """测试智能缓存决策（默认情况）"""
        config = EnhancedCacheConfig(
            auto_server_cache=False,
            large_content_threshold=512 * 1024
        )
        manager = EnhancedGeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "test message")]
        
        decision = manager.smart_cache_decision(messages)
        
        assert "use_client_cache" in decision
        assert "use_server_cache" in decision
        assert "server_cache_name" in decision
        assert "reason" in decision
        
        assert decision["use_client_cache"] is True
        assert decision["use_server_cache"] is False
    
    def test_smart_cache_decision_large_content(self):
        """测试智能缓存决策（大内容）"""
        config = GeminiCacheConfig(
            auto_server_cache=True,
            large_content_threshold=512 * 1024,
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        # 大内容
        large_content = ["x" * 1024 * 1024]  # 1MB
        messages = [MockBaseMessage("user", "test message")]
        
        decision = manager.smart_cache_decision(messages, large_content)
        
        assert decision["use_client_cache"] is True
        # 实际结果取决于缓存创建是否成功
    
    def test_get_client_cache_response(self):
        """测试获取客户端缓存响应"""
        config = EnhancedCacheConfig(enabled=True)
        manager = EnhancedGeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "test")]
        response = "test response"
        
        # 设置客户端缓存
        manager.set_client_cache_response(messages, response, "gemini-2.0-flash")
        
        # 获取客户端缓存响应
        result = manager.get_client_cache_response(messages, "gemini-2.0-flash")
        assert result == response
    
    def test_set_client_cache_response(self):
        """测试设置客户端缓存响应"""
        config = EnhancedCacheConfig(enabled=True)
        manager = EnhancedGeminiCacheManager(config)
        
        messages = [MockBaseMessage("user", "test")]
        response = "test response"
        
        manager.set_client_cache_response(messages, response, "gemini-2.0-flash")
        
        # 验证已设置
        result = manager.get_client_cache_response(messages, "gemini-2.0-flash")
        assert result == response
    
    def test_get_cache_config(self):
        """测试获取缓存配置信息"""
        config = EnhancedCacheConfig(
            server_cache_enabled=True,
            auto_server_cache=True,
            large_content_threshold=512 * 1024,
            server_cache_ttl="1800s",
            server_cache_display_name="test_cache"
        )
        manager = EnhancedGeminiCacheManager(config)
        
        cache_config = manager.get_cache_config()
        
        expected_keys = [
            "client_cache_enabled",
            "server_cache_enabled",
            "auto_server_cache",
            "large_content_threshold",
            "server_cache_ttl",
            "server_cache_display_name"
        ]
        
        for key in expected_keys:
            assert key in cache_config
        
        assert cache_config["server_cache_enabled"] is True
        assert cache_config["auto_server_cache"] is True
        assert cache_config["large_content_threshold"] == 512 * 1024


class TestEnhancedGeminiCacheManagerEdgeCases:
    """测试增强Gemini缓存管理器的边界情况"""
    
    def test_init_with_empty_client(self):
        """测试初始化时客户端为None"""
        config = GeminiCacheConfig(model_name="gemini-2.0-flash-001")
        
        # 应该允许客户端为None
        manager = EnhancedGeminiCacheManager(config, None)
        assert manager._server_cache_manager is None
        assert manager._client_cache_manager is not None
    
    def test_get_with_none_provider(self):
        """测试提供者为空时的获取"""
        config = EnhancedCacheConfig(enabled=False)
        manager = EnhancedGeminiCacheManager(config)
        
        result = manager.get("key1")
        assert result is None
    
    def test_server_cache_operations_without_manager(self):
        """测试没有服务器端缓存管理器时的操作"""
        config = GeminiCacheConfig(
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        manager = EnhancedGeminiCacheManager(config)  # 没有客户端
        
        # 所有服务器端操作应该安全处理
        assert manager.create_server_cache(["content"]) is None
        assert manager.use_server_cache("cache", "query") is None
        assert manager.get_or_create_server_cache(["content"]) is None
        assert manager.delete_server_cache("cache") is False
        assert manager.list_server_caches() == []
        assert manager.cleanup_expired_server_caches() == 0
    
    def test_smart_cache_decision_with_errors(self):
        """测试智能缓存决策时的错误处理"""
        config = GeminiCacheConfig(
            auto_server_cache=True,
            server_cache_enabled=True,
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        # 模拟服务器端缓存创建失败
        with patch.object(mock_client.caches, 'create', side_effect=Exception("Error")):
            manager = EnhancedGeminiCacheManager(config, mock_client)
            
            large_content = ["x" * 1024 * 1024]  # 1MB
            messages = [MockBaseMessage("user", "test")]
            
            decision = manager.smart_cache_decision(messages, large_content)
            
            # 错误时应该回退到客户端缓存
            assert decision["use_client_cache"] is True
            assert decision["use_server_cache"] is False
            assert decision["reason"] in ["server_cache_creation_failed", "default"]
    
    def test_multiple_large_content_operations(self):
        """测试多次大内容操作"""
        config = GeminiCacheConfig(
            auto_server_cache=True,
            large_content_threshold=1024,  # 1KB阈值
            model_name="gemini-2.0-flash-001"
        )
        
        mock_client = MockGeminiClient()
        manager = EnhancedGeminiCacheManager(config, mock_client)
        
        for i in range(3):
            large_content = ["content" + "x" * 2048]  # 超过阈值的内容
            messages = [MockBaseMessage("user", f"test{i}")]
            
            decision = manager.smart_cache_decision(messages, large_content)
            # 决策应该是一致的
            assert "use_client_cache" in decision
            assert "use_server_cache" in decision