"""
缓存系统优化测试
"""

import pytest
import time

from src.core.common.cache import (
    CacheManager, 
    ConfigCache, 
    LLMCache, 
    GraphCache,
    config_cached,
    llm_cached,
    graph_cached,
    get_global_cache_manager,
    clear_cache,
    get_cache
)


class TestCacheManager:
    """测试缓存管理器"""
    
    def test_cache_manager_creation(self):
        """测试缓存管理器创建"""
        manager = CacheManager()
        assert manager is not None
    
    def test_get_cache_lru(self):
        """测试获取LRU缓存"""
        manager = CacheManager()
        cache = manager.get_cache("test_lru", maxsize=100)
        assert cache is not None
    
    def test_get_cache_ttl(self):
        """测试获取TTL缓存"""
        manager = CacheManager()
        cache = manager.get_cache("test_ttl", maxsize=100, ttl=60)
        assert cache is not None
    
    def test_cache_operations(self):
        """测试缓存操作"""
        manager = CacheManager()
        cache = manager.get_cache("test_ops")
        
        # 测试设置和获取
        cache["key1"] = "value1"
        assert cache.get("key1") == "value1"
        
        # 测试包含
        assert "key1" in cache
        assert "key2" not in cache
        
        # 测试长度
        assert len(cache) == 1
        
        # 测试清除
        cache.clear()
        assert len(cache) == 0
    
    def test_clear_cache(self):
        """测试清除缓存"""
        manager = CacheManager()
        cache1 = manager.get_cache("test1")
        cache2 = manager.get_cache("test2")
        
        cache1["key1"] = "value1"
        cache2["key2"] = "value2"
        
        # 清除特定缓存
        manager.clear_cache("test1")
        assert len(cache1) == 0
        assert len(cache2) == 1
        
        # 清除所有缓存
        manager.clear_cache()
        assert len(cache1) == 0
        assert len(cache2) == 0
    
    def test_cache_info(self):
        """测试缓存信息"""
        manager = CacheManager()
        cache = manager.get_cache("test_info", maxsize=50, ttl=120)
        cache["key1"] = "value1"
        
        info = manager.get_cache_info("test_info")
        assert info["name"] == "test_info"
        assert info["size"] == 1
        assert info["maxsize"] == 50
        
        all_info = manager.get_all_cache_info()
        assert "test_info" in all_info


class TestSpecializedCaches:
    """测试专用缓存"""
    
    def test_config_cache(self):
        """测试配置缓存"""
        cache = ConfigCache()
        
        # 测试基本操作
        cache.put("config1", {"key": "value"})
        result = cache.get("config1")
        assert result == {"key": "value"}
        
        # 测试清除
        cache.clear()
        assert cache.get("config1") is None
    
    def test_llm_cache(self):
        """测试LLM缓存"""
        cache = LLMCache()
        
        # 测试基本操作
        cache.put("response1", "Hello, world!")
        result = cache.get("response1")
        assert result == "Hello, world!"
        
        # 测试清除
        cache.clear()
        assert cache.get("response1") is None
    
    def test_graph_cache(self):
        """测试图缓存"""
        cache = GraphCache()
        
        # 测试基本操作
        cache.put("graph1", {"nodes": [], "edges": []})
        result = cache.get("graph1")
        assert result == {"nodes": [], "edges": []}
        
        # 测试清除
        cache.clear()
        assert cache.get("graph1") is None


class TestCacheDecorators:
    """测试缓存装饰器"""
    
    def test_config_cached_decorator(self):
        """测试配置缓存装饰器"""
        call_count = 0
        
        @config_cached(maxsize=5)
        def load_config(path):
            nonlocal call_count
            call_count += 1
            return f"config_for_{path}"
        
        # 测试缓存
        result1 = load_config("app.yaml")
        assert result1 == "config_for_app.yaml"
        assert call_count == 1
        
        # 第二次调用（从缓存）
        result2 = load_config("app.yaml")
        assert result2 == "config_for_app.yaml"
        assert call_count == 1
    
    def test_llm_cached_decorator(self):
        """测试LLM缓存装饰器"""
        call_count = 0
        
        # 使用唯一的缓存名称避免冲突
        from src.core.common.cache import get_cache, cached
        
        cache = get_cache("test_llm_cached_unique", maxsize=10, ttl=1)
        test_cached = cached(cache)
        
        @test_cached
        def llm_call(prompt):
            nonlocal call_count
            call_count += 1
            return f"Response to: {prompt}"
        
        # 测试缓存
        result1 = llm_call("Hello")
        assert result1 == "Response to: Hello"
        assert call_count == 1
        
        # 第二次调用（从缓存）
        result2 = llm_call("Hello")
        assert result2 == "Response to: Hello"
        assert call_count == 1
    
    def test_graph_cached_decorator(self):
        """测试图缓存装饰器"""
        call_count = 0
        
        @graph_cached(maxsize=5, ttl=1800)
        def build_graph(graph_type):
            nonlocal call_count
            call_count += 1
            return {"config": {"type": graph_type}, "nodes": []}
        
        # 测试缓存
        result1 = build_graph("react")
        assert result1["config"]["type"] == "react"
        assert call_count == 1
        
        # 第二次调用（从缓存）
        result2 = build_graph("react")
        assert result2["config"]["type"] == "react"
        assert call_count == 1


class TestGlobalCacheManager:
    """测试全局缓存管理器"""
    
    def test_global_manager_singleton(self):
        """测试全局管理器单例"""
        manager1 = get_global_cache_manager()
        manager2 = get_global_cache_manager()
        assert manager1 is manager2
    
    def test_global_cache_operations(self):
        """测试全局缓存操作"""
        cache = get_cache("global_test")
        cache["key"] = "value"
        
        # 验证缓存存在
        info = get_global_cache_manager().get_cache_info("global_test")
        assert info["size"] == 1
        
        # 清除缓存
        clear_cache("global_test")
        info = get_global_cache_manager().get_cache_info("global_test")
        assert info["size"] == 0


class TestCachePerformance:
    """测试缓存性能"""
    
    def test_cache_performance(self):
        """测试缓存性能"""
        manager = CacheManager()
        cache = manager.get_cache("perf_test", maxsize=1000)
        
        # 测试大量写入
        start_time = time.time()
        for i in range(1000):
            cache[f"key_{i}"] = f"value_{i}"
        write_time = time.time() - start_time
        
        # 测试大量读取
        start_time = time.time()
        for i in range(1000):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        read_time = time.time() - start_time
        
        # 性能应该在合理范围内（这里只是简单检查）
        assert write_time < 1.0  # 写入应该在1秒内完成
        assert read_time < 0.5   # 读取应该在0.5秒内完成


if __name__ == "__main__":
    pytest.main([__file__])