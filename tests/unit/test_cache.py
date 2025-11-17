"""
缓存系统测试
"""

import time
import pytest

from src.core.common.cache import (
    CacheManager,
    get_global_cache_manager,
    get_cache,
    clear_cache,
    ConfigCache,
    LLMCache,
    GraphCache,
    simple_cached,
    config_cached,
    llm_cached,
    graph_cached
)


class TestCacheManager:
    """测试缓存管理器"""
    
    def test_cache_manager_creation(self):
        """测试缓存管理器创建"""
        manager = CacheManager()
        assert manager is not None
    
    def test_get_cache_creation(self):
        """测试缓存创建"""
        manager = CacheManager()
        
        # 第一次获取创建新缓存
        cache1 = manager.get_cache("test_cache")
        assert cache1 is not None
        
        # 第二次获取返回同一缓存
        cache2 = manager.get_cache("test_cache")
        assert cache1 is cache2
    
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
    
    def test_cache_with_ttl(self):
        """测试带TTL的缓存"""
        manager = CacheManager()
        
        cache = manager.get_cache("ttl_cache", maxsize=10, ttl=1)
        cache["key1"] = "value1"
        
        # 立即获取应该成功
        assert cache.get("key1") == "value1"
        
        # 等待过期
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_without_ttl(self):
        """测试不带TTL的缓存"""
        manager = CacheManager()
        
        cache = manager.get_cache("no_ttl_cache", maxsize=10)
        cache["key1"] = "value1"
        
        # 应该能获取
        assert cache.get("key1") == "value1"
        
        # 等待后应该还能获取（无过期）
        time.sleep(0.1)
        assert cache.get("key1") == "value1"
    
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
    
    def test_clear_all_caches(self):
        """测试清除所有缓存"""
        manager = CacheManager()
        
        cache1 = manager.get_cache("cache1")
        cache2 = manager.get_cache("cache2")
        
        cache1["key1"] = "value1"
        cache2["key2"] = "value2"
        
        assert len(cache1) == 1
        assert len(cache2) == 1
        
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
    
    def test_get_cache_info(self):
        """测试获取缓存信息"""
        manager = CacheManager()
        
        cache = manager.get_cache("info_test", maxsize=50, ttl=100)
        cache["key1"] = "value1"
        
        info = manager.get_cache_info("info_test")
        
        assert info["name"] == "info_test"
        assert info["size"] == 1
        assert info["maxsize"] == 50
        assert "type" in info
    
    def test_get_all_cache_info(self):
        """测试获取所有缓存信息"""
        manager = CacheManager()
        
        cache1 = manager.get_cache("cache1", maxsize=100)
        cache2 = manager.get_cache("cache2", maxsize=200)
        
        cache1["key1"] = "value1"
        cache2["key2"] = "value2"
        
        all_info = manager.get_all_cache_info()
        
        assert "cache1" in all_info
        assert "cache2" in all_info
        assert all_info["cache1"]["size"] == 1
        assert all_info["cache2"]["size"] == 1


class TestGlobalCacheManager:
    """测试全局缓存管理器"""
    
    def test_global_manager_singleton(self):
        """测试全局管理器单例"""
        manager1 = get_global_cache_manager()
        manager2 = get_global_cache_manager()
        assert manager1 is manager2
    
    def test_get_global_cache_manager(self):
        """测试获取全局缓存管理器"""
        manager1 = get_global_cache_manager()
        manager2 = get_global_cache_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, CacheManager)
    
    def test_get_cache_function(self):
        """测试获取缓存函数"""
        cache = get_cache("test_func_cache")
        assert cache is not None
        
        # 再次获取应该返回同一缓存
        cache2 = get_cache("test_func_cache")
        assert cache is cache2
    
    def test_clear_cache_function(self):
        """测试清除缓存函数"""
        cache = get_cache("clear_func_test")
        cache["key1"] = "value1"
        
        assert len(cache) == 1
        
        clear_cache("clear_func_test")
        assert len(cache) == 0
        
        # 清除所有缓存
        cache["key2"] = "value2"
        clear_cache()
        assert len(cache) == 0
    
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


class TestSpecializedCaches:
    """测试专用缓存类"""
    
    def test_config_cache(self):
        """测试配置缓存"""
        cache = ConfigCache()
        
        cache.put("config1", {"setting": "value"})
        result = cache.get("config1")
        
        assert result == {"setting": "value"}
        
        cache.clear()
        assert cache.get("config1") is None
    
    def test_llm_cache(self):
        """测试LLM缓存"""
        cache = LLMCache()
        
        cache.put("prompt1", "response1")
        result = cache.get("prompt1")
        
        assert result == "response1"
        
        cache.clear()
        assert cache.get("prompt1") is None
    
    def test_graph_cache(self):
        """测试图缓存"""
        cache = GraphCache()
        
        cache.put("graph1", {"nodes": 5, "edges": 10})
        result = cache.get("graph1")
        
        assert result == {"nodes": 5, "edges": 10}
        
        cache.clear()
        assert cache.get("graph1") is None


class TestCacheDecorators:
    """测试缓存装饰器"""
    
    def test_simple_cached_decorator(self):
        """测试简单缓存装饰器"""
        call_count = 0
        
        @simple_cached("decorator_test", maxsize=10, ttl=1)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x * y + time.time()
        
        # 第一次调用
        result1 = expensive_function(2, 3)
        assert call_count == 1
        
        # 第二次调用相同参数，应该使用缓存
        result2 = expensive_function(2, 3)
        assert call_count == 1
        assert result1 == result2
        
        # 不同参数应该重新计算
        result3 = expensive_function(3, 4)
        assert call_count == 2
        assert result3 != result1
    
    def test_config_cached_decorator(self):
        """测试配置缓存装饰器"""
        call_count = 0
        
        @config_cached(maxsize=5)
        def load_config(config_name):
            nonlocal call_count
            call_count += 1
            return f"config_{config_name}_{time.time()}"
        
        # 测试缓存
        result1 = load_config("app")
        assert call_count == 1
        
        result2 = load_config("app")
        assert call_count == 1
        assert result1 == result2
        
        result3 = load_config("db")
        assert call_count == 2
    
    def test_llm_cached_decorator(self):
        """测试LLM缓存装饰器"""
        call_count = 0
        
        @llm_cached(maxsize=10, ttl=1)
        def llm_call(prompt):
            nonlocal call_count
            call_count += 1
            return f"Response to: {prompt}"
        
        # 测试缓存
        result1 = llm_call("Hello")
        assert call_count == 1
        
        result2 = llm_call("Hello")
        assert call_count == 1
        assert result1 == result2
        
        result3 = llm_call("Hi")
        assert call_count == 2
    
    def test_graph_cached_decorator(self):
        """测试图缓存装饰器"""
        call_count = 0
        
        @graph_cached(maxsize=5, ttl=1)
        def build_graph(node_count, edge_count):
            nonlocal call_count
            call_count += 1
            return {"graph": {"nodes": node_count, "edges": edge_count}, "built_at": time.time()}
        
        # 测试缓存
        result1 = build_graph(5, 10)
        assert call_count == 1
        assert result1["graph"]["nodes"] == 5
        
        # 第二次调用相同参数，应该使用缓存
        result2 = build_graph(5, 10)
        assert call_count == 1
        assert result1 == result2
        
        # 不同参数应该重新计算
        result3 = build_graph(10, 20)
        assert call_count == 2
        assert result3["graph"]["nodes"] == 10


class TestCachePerformance:
    """测试缓存性能"""
    
    def test_cache_performance(self):
        """测试缓存性能"""
        cache = get_cache("performance_test", maxsize=1000)
        
        # 测试写入性能
        start_time = time.time()
        for i in range(100):
            cache[f"key_{i}"] = f"value_{i}"
        write_time = time.time() - start_time
        
        # 测试读取性能
        start_time = time.time()
        for i in range(100):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        read_time = time.time() - start_time
        
        # 性能应该在合理范围内（这里只是简单检查）
        assert write_time < 1.0  # 写入100项应该在1秒内
        assert read_time < 0.1  # 读取100项应该在0.1秒内
    
    def test_cache_performance_large_scale(self):
        """测试大规模缓存性能"""
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
        
        # 性能应该在合理范围内
        assert write_time < 1.0  # 写入应该在1秒内完成
        assert read_time < 0.5   # 读取应该在0.5秒内完成
    
    def test_memory_efficiency(self):
        """测试内存效率"""
        cache = get_cache("memory_test", maxsize=10)
        
        # 添加超过最大大小的数据
        for i in range(20):
            cache[f"key_{i}"] = f"value_{i}" * 100  # 较大的值
        
        # 缓存大小应该不超过最大值（使用len()而不是size()）
        assert len(cache) <= 10
        
        # 最近添加的项应该存在
        assert cache.get("key_19") is not None
        assert cache.get("key_18") is not None


if __name__ == "__main__":
    pytest.main([__file__])