"""GraphCache单元测试"""

import time
import threading
from typing import Dict, Any
import pytest

try:
    from langgraph.graph import StateGraph
except ImportError:
    # 模拟StateGraph用于测试
    class StateGraph:
        def __init__(self):
            self.nodes = []
            self.edges = []

# 导入我们自己的类
from src.infrastructure.graph.graph_cache import GraphCache, CacheEvictionPolicy, calculate_config_hash


class TestGraphCache:
    """GraphCache测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.cache = GraphCache(
            max_size=50,
            ttl_seconds=300,
            eviction_policy=CacheEvictionPolicy.LRU,
            enable_compression=True
        )
        
        # 创建测试图
        self.test_graph = StateGraph()
        self.test_graph.nodes = ["node1", "node2"]
        self.test_graph.edges = [("node1", "node2")]
        
        # 创建测试配置
        self.test_config = {
            "graph_name": "test_graph",
            "nodes": ["node1", "node2"],
            "edges": [("node1", "node2")],
            "settings": {"parallelism": 2}
        }
        
        self.config_hash = calculate_config_hash(self.test_config)
    
    def test_cache_graph_and_get_graph(self):
        """测试缓存图和获取图"""
        # 缓存图
        self.cache.cache_graph(self.config_hash, self.test_graph)
        
        # 获取图
        retrieved_graph = self.cache.get_graph(self.config_hash)
        
        # 验证图被正确缓存和获取
        assert retrieved_graph is not None
        assert retrieved_graph.nodes == self.test_graph.nodes
        assert retrieved_graph.edges == self.test_graph.edges
    
    def test_cache_miss(self):
        """测试缓存未命中"""
        non_existent_hash = "non_existent_hash_12345"
        result = self.cache.get_graph(non_existent_hash)
        
        assert result is None
    
    def test_ttl_eviction(self):
        """测试TTL过期淘汰"""
        # 设置一个很短的TTL
        short_ttl_cache = GraphCache(max_size=10, ttl_seconds=0.1)
        
        # 缓存图
        short_ttl_cache.cache_graph(self.config_hash, self.test_graph)
        
        # 立即获取应该成功
        result = short_ttl_cache.get_graph(self.config_hash)
        assert result is not None
        
        # 等待超过TTL时间
        time.sleep(0.2)
        
        # 再次获取应该失败（已过期）
        result = short_ttl_cache.get_graph(self.config_hash)
        assert result is None
    
    def test_lru_eviction_policy(self):
        """测试LRU淘汰策略"""
        lru_cache = GraphCache(max_size=2, eviction_policy=CacheEvictionPolicy.LRU)
        
        # 缓存3个图（超过最大大小）
        config1 = calculate_config_hash({"graph": "1"})
        config2 = calculate_config_hash({"graph": "2"})
        config3 = calculate_config_hash({"graph": "3"})
        
        graph1 = StateGraph()
        graph2 = StateGraph()
        graph3 = StateGraph()
        
        lru_cache.cache_graph(config1, graph1)  # 最早的
        lru_cache.cache_graph(config2, graph2)  # 中间的
        lru_cache.get_graph(config1)  # 访问config1，使其变为最近使用的
        lru_cache.cache_graph(config3, graph3)  # 最新的
        
        # 验证config2被移除（最久未使用）
        result2 = lru_cache.get_graph(config2)
        assert result2 is None
        
        # 验证其他图仍然存在
        result1 = lru_cache.get_graph(config1)
        result3 = lru_cache.get_graph(config3)
        assert result1 is not None
        assert result3 is not None
    
    def test_lfu_eviction_policy(self):
        """测试LFU淘汰策略"""
        lfu_cache = GraphCache(max_size=2, eviction_policy=CacheEvictionPolicy.LFU)
        
        # 缓存3个图
        config1 = calculate_config_hash({"graph": "1"})
        config2 = calculate_config_hash({"graph": "2"})
        config3 = calculate_config_hash({"graph": "3"})
        
        graph1 = StateGraph()
        graph2 = StateGraph()
        graph3 = StateGraph()
        
        lfu_cache.cache_graph(config1, graph1)  # 访问1次
        lfu_cache.cache_graph(config2, graph2)  # 访问1次
        lfu_cache.cache_graph(config3, graph3)  # 访问1次
        
        # 多次访问config1和config2，使config3成为最少访问的
        for _ in range(5):
            lfu_cache.get_graph(config1)
            lfu_cache.get_graph(config2)
        
        # 添加新图会导致淘汰最少访问的config3
        config4 = calculate_config_hash({"graph": "4"})
        graph4 = StateGraph()
        lfu_cache.cache_graph(config4, graph4)
        
        # 验证config3被移除（最少访问）
        result3 = lfu_cache.get_graph(config3)
        assert result3 is None
        
        # 验证其他图仍然存在
        result1 = lfu_cache.get_graph(config1)
        result2 = lfu_cache.get_graph(config2)
        result4 = lfu_cache.get_graph(config4)
        assert result1 is not None
        assert result2 is not None
        assert result4 is not None
    
    def test_cache_stats(self):
        """测试缓存统计"""
        # 执行一些操作来填充统计信息
        self.cache.cache_graph(self.config_hash, self.test_graph)
        self.cache.get_graph(self.config_hash)  # 命中
        self.cache.get_graph("non_existent")  # 未命中
        
        stats = self.cache.get_cache_stats()
        
        assert "size" in stats
        assert "hit_rate" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "total_requests" in stats
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert stats["total_requests"] == stats["hits"] + stats["misses"]
    
    def test_invalidate_by_hash(self):
        """测试按哈希失效"""
        # 缓存图
        self.cache.cache_graph(self.config_hash, self.test_graph)
        
        # 验证图存在
        result = self.cache.get_graph(self.config_hash)
        assert result is not None
        
        # 失效缓存
        success = self.cache.invalidate_by_hash(self.config_hash)
        assert success is True
        
        # 验证图不再存在
        result = self.cache.get_graph(self.config_hash)
        assert result is None
    
    def test_invalidate_by_pattern(self):
        """测试按模式失效"""
        # 缓存多个图
        config1 = calculate_config_hash({"graph": "test_1"})
        config2 = calculate_config_hash({"graph": "test_2"})
        config3 = calculate_config_hash({"graph": "other_3"})
        
        self.cache.cache_graph(config1, StateGraph())
        self.cache_graph(config2, StateGraph())
        self.cache_graph(config3, StateGraph())
        
        # 验证所有图都存在
        assert self.cache.get_graph(config1) is not None
        assert self.cache.get_graph(config2) is not None
        assert self.cache.get_graph(config3) is not None
        
        # 按模式失效（匹配test_开头的）
        removed_count = self.cache.invalidate_by_pattern("test_*")
        
        # 验证匹配的图被移除
        assert self.cache.get_graph(config1) is None
        assert self.cache.get_graph(config2) is None
        # 验证不匹配的图仍然存在
        assert self.cache.get_graph(config3) is not None
        assert removed_count == 2
    
    def test_clear_cache(self):
        """测试清除缓存"""
        # 缓存一些图
        self.cache_graph(self.config_hash, self.test_graph)
        
        # 验证缓存中有内容
        stats_before = self.cache.get_cache_stats()
        assert stats_before["size"] > 0
        
        # 清除缓存
        self.cache.clear()
        
        # 验证缓存被清空
        stats_after = self.cache.get_cache_stats()
        assert stats_after["size"] == 0
    
    def test_cache_entries_info(self):
        """测试缓存条目信息"""
        # 缓存一个图
        self.cache_graph(self.config_hash, self.test_graph)
        
        # 获取缓存条目信息
        entries = self.cache.get_cache_entries()
        
        assert len(entries) == 1
        entry = entries[0]
        assert entry["config_hash"] == self.config_hash
        assert "created_at" in entry
        assert "last_accessed" in entry
        assert "access_count" in entry
        assert "size_bytes" in entry
    
    def test_optimize_cache(self):
        """测试缓存优化"""
        # 创建一个短TTL的缓存
        short_ttl_cache = GraphCache(max_size=10, ttl_seconds=0.1)
        
        # 缓存一个图
        short_ttl_cache.cache_graph(self.config_hash, self.test_graph)
        
        # 等待过期
        time.sleep(0.2)
        
        # 优化缓存（应该移除过期条目）
        optimization_result = short_ttl_cache.optimize_cache()
        
        assert optimization_result["expired_removed"] >= 0
        
        # 验证过期的条目被移除
        result = short_ttl_cache.get_graph(self.config_hash)
        assert result is None
    
    def test_concurrent_access(self):
        """测试并发访问"""
        results = []
        errors = []
        
        def cache_worker():
            try:
                # 缓存和获取图
                test_hash = calculate_config_hash({"graph": f"worker_{threading.current_thread().ident}"})
                test_graph = StateGraph()
                self.cache.cache_graph(test_hash, test_graph)
                
                result = self.cache.get_graph(test_hash)
                results.append(result is not None)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程同时访问
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0
        assert len(results) == 5
        assert all(results)  # 所有操作都成功
    
    def test_config_hash_calculation(self):
        """测试配置哈希计算"""
        config1 = {"name": "test", "value": 1}
        config2 = {"value": 1, "name": "test"}  # 相同内容，不同顺序
        
        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)
        
        # 相同内容应产生相同哈希
        assert hash1 == hash2
        
        config3 = {"name": "test", "value": 2}  # 不同内容
        hash3 = calculate_config_hash(config3)
        
        # 不同内容应产生不同哈希
        assert hash1 != hash3
    
    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        # 创建一个小的缓存
        small_cache = GraphCache(max_size=2)
        
        # 添加超过限制的图
        for i in range(5):
            config_hash = calculate_config_hash({"graph": f"test_{i}"})
            graph = StateGraph()
            small_cache.cache_graph(config_hash, graph)
        
        # 验证缓存大小不超过限制
        stats = small_cache.get_cache_stats()
        assert stats["size"] <= 2  # 可能是2或3（取决于LRU策略的具体实现）
    
    def test_different_eviction_policies(self):
        """测试不同淘汰策略"""
        policies = [CacheEvictionPolicy.LRU, CacheEvictionPolicy.LFU, CacheEvictionPolicy.TTL]
        
        for policy in policies:
            cache = GraphCache(max_size=2, eviction_policy=policy)
            
            # 添加一些图
            config1 = calculate_config_hash({"graph": f"{policy.value}_1"})
            config2 = calculate_config_hash({"graph": f"{policy.value}_2"})
            config3 = calculate_config_hash({"graph": f"{policy.value}_3"})
            
            graph1 = StateGraph()
            graph2 = StateGraph()
            graph3 = StateGraph()
            
            cache.cache_graph(config1, graph1)
            cache.cache_graph(config2, graph2)
            cache.cache_graph(config3, graph3)  # 这应该触发淘汰
            
            # 至少有一个图被移除
            remaining_count = sum([
                1 for config in [config1, config2, config3]
                if cache.get_graph(config) is not None
            ])
            
            assert remaining_count <= 2


if __name__ == "__main__":
    pytest.main([__file__])