"""Cache单元测试"""

import threading
from src.core.common.utils.cache import Cache


class TestCache:
    """Cache测试类"""

    def test_init(self):
        """测试初始化"""
        cache = Cache()
        assert cache.name == "default"
        assert cache._cache == {}
        # 检查_lock是否是可锁定对象（替代isinstance检查）
        assert hasattr(cache._lock, 'acquire') and hasattr(cache._lock, 'release')

        cache_named = Cache(name="test_cache")
        assert cache_named.name == "test_cache"

    def test_set_and_get(self):
        """测试设置和获取缓存值"""
        cache = Cache()

        # 设置值
        cache.set("key1", "value1")
        cache.set("key2", 42)
        cache.set("key3", {"nested": "value"})

        # 获取值
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == 42
        assert cache.get("key3") == {"nested": "value"}

        # 获取不存在的键
        assert cache.get("nonexistent") is None

    def test_clear(self):
        """测试清空缓存"""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.size() == 2

        cache.clear()

        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_remove(self):
        """测试移除缓存项"""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # 移除存在的键
        result = cache.remove("key1")
        assert result is True
        assert cache.get("key1") is None
        assert cache.size() == 1

        # 移除不存在的键
        result = cache.remove("nonexistent")
        assert result is False

    def test_remove_by_pattern(self):
        """测试按模式移除缓存项"""
        cache = Cache()
        cache.set("user_123", "data1")
        cache.set("user_456", "data2")
        cache.set("product_abc", "data3")
        cache.set("product_def", "data4")
        cache.set("other_key", "data5")

        # 按模式移除用户相关键
        count = cache.remove_by_pattern("user_")
        assert count == 2
        assert cache.get("user_123") is None
        assert cache.get("user_456") is None
        assert cache.get("product_abc") == "data3"
        assert cache.get("product_def") == "data4"
        assert cache.get("other_key") == "data5"

        # 按模式移除产品相关键
        count = cache.remove_by_pattern("product_")
        assert count == 2
        assert cache.get("product_abc") is None
        assert cache.get("product_def") is None

    def test_size(self):
        """测试获取缓存大小"""
        cache = Cache()

        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

        cache.remove("key1")
        assert cache.size() == 1

    def test_keys(self):
        """测试获取所有缓存键"""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        keys = cache.keys()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys

        cache.remove("key2")
        keys = cache.keys()
        assert len(keys) == 2
        assert "key2" not in keys

    def test_has(self):
        """测试检查缓存是否存在"""
        cache = Cache()
        cache.set("key1", "value1")

        assert cache.has("key1") is True
        assert cache.has("nonexistent") is False

    def test_get_or_set(self):
        """测试获取或设置缓存值"""
        cache = Cache()

        # 第一次获取，使用工厂函数创建值
        value = cache.get_or_set("key1", lambda: "computed_value")
        assert value == "computed_value"
        assert cache.get("key1") == "computed_value"

        # 第二次获取，直接返回缓存值
        value = cache.get_or_set("key1", lambda: "new_computed_value")
        assert value == "computed_value"  # 应该返回缓存的值，而不是新计算的值

    def test_get_stats(self):
        """测试获取缓存统计信息"""
        cache = Cache(name="test_cache")
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()
        assert stats["name"] == "test_cache"
        assert stats["size"] == 2
        assert "key1" in stats["keys"]
        assert "key2" in stats["keys"]

    def test_thread_safety(self):
        """测试线程安全性"""
        cache = Cache()
        results = []

        def worker(thread_id):
            for i in range(10):
                key = f"thread_{thread_id}_key_{i}"
                cache.set(key, f"value_{thread_id}_{i}")
                value = cache.get(key)
                results.append((key, value))

        # 创建多个线程同时操作缓存
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证结果
        assert len(results) == 30  # 3个线程 * 10次操作
        assert cache.size() == 30  # 应该有30个不同的键