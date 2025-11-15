"""共享组件性能基准测试"""

import pytest
import asyncio
import time
from datetime import datetime
from src.infrastructure.common.serialization.universal_serializer import UniversalSerializer
from src.infrastructure.common.cache.enhanced_cache_manager import EnhancedCacheManager
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor
from src.infrastructure.common.id_generator.id_generator import IDGenerator
from src.infrastructure.common.temporal.temporal_manager import TemporalManager
from src.infrastructure.common.metadata.metadata_manager import MetadataManager


class TestSharedComponentsPerformance:
    """共享组件性能测试"""
    
    @pytest.fixture
    def setup_components(self):
        """设置测试组件"""
        serializer = UniversalSerializer()
        cache_manager = EnhancedCacheManager(max_size=1000, default_ttl=300)
        monitor = PerformanceMonitor()
        id_generator = IDGenerator()
        temporal = TemporalManager()
        metadata = MetadataManager()
        
        return serializer, cache_manager, monitor, id_generator, temporal, metadata
    
    def test_serialization_performance(self, setup_components):
        """测试序列化性能"""
        serializer, _, _, _, _, _ = setup_components
        
        # 准备测试数据
        large_data = {
            "messages": [{"content": f"Message {i}"} for i in range(1000)],
            "metadata": {"key": "value" for _ in range(100)},
            "timestamp": datetime.now()
        }
        
        # 测试JSON序列化性能
        start_time = time.time()
        for _ in range(100):
            serialized = serializer.serialize(large_data, "json")
            deserialized = serializer.deserialize(serialized, "json")
        json_duration = time.time() - start_time
        
        # 测试紧凑JSON序列化性能
        start_time = time.time()
        for _ in range(100):
            serialized = serializer.serialize(large_data, "compact_json")
            deserialized = serializer.deserialize(serialized, "compact_json")
        compact_duration = time.time() - start_time
        
        # 测试Pickle序列化性能
        start_time = time.time()
        for _ in range(100):
            serialized = serializer.serialize(large_data, "pickle")
            deserialized = serializer.deserialize(serialized, "pickle")
        pickle_duration = time.time() - start_time
        
        print(f"JSON序列化: {json_duration:.3f}s")
        print(f"紧凑JSON序列化: {compact_duration:.3f}s")
        print(f"Pickle序列化: {pickle_duration:.3f}s")
        
        # 验证性能要求
        assert json_duration < 5.0  # 5秒内完成100次序列化
        assert compact_duration < 5.0
        assert pickle_duration < 5.0
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, setup_components):
        """测试缓存性能"""
        _, cache_manager, _, _, _, _ = setup_components
        
        # 准备测试数据
        test_data = {"key": "value", "data": "x" * 1000}
        
        # 测试写入性能
        start_time = time.time()
        for i in range(1000):
            await cache_manager.set(f"key_{i}", test_data)
        write_duration = time.time() - start_time
        
        # 测试读取性能
        start_time = time.time()
        for i in range(1000):
            await cache_manager.get(f"key_{i}")
        read_duration = time.time() - start_time
        
        # 测试缓存命中率
        stats = cache_manager.get_stats()
        
        print(f"缓存写入: {write_duration:.3f}s (1000次)")
        print(f"缓存读取: {read_duration:.3f}s (1000次)")
        print(f"缓存命中率: {stats['hit_rate']:.2%}")
        
        # 验证性能要求
        assert write_duration < 2.0  # 2秒内完成1000次写入
        assert read_duration < 1.0    # 1秒内完成1000次读取
        assert stats["hit_rate"] > 0.99  # 命中率超过99%
    
    def test_monitoring_performance(self, setup_components):
        """测试性能监控开销"""
        _, _, monitor, _, _, _ = setup_components
        
        # 测试监控开销
        start_time = time.time()
        for i in range(10000):
            operation_id = monitor.start_operation("test_operation")
            # 模拟操作
            time.sleep(0.0001)  # 0.1ms
            monitor.end_operation(operation_id, "test_operation", True)
        monitoring_duration = time.time() - start_time
        
        stats = monitor.get_stats("test_operation")
        
        print(f"监控开销: {monitoring_duration:.3f}s (10000次操作)")
        print(f"平均操作时间: {stats['avg_duration']:.6f}s")
        
        # 验证监控开销
        assert monitoring_duration < 5.0  # 5秒内完成10000次监控
        assert stats["total_operations"] == 10000
    
    def test_id_generation_performance(self, setup_components):
        """测试ID生成性能"""
        _, _, _, id_generator, _, _ = setup_components
        
        # 测试不同类型ID的生成性能
        start_time = time.time()
        for _ in range(10000):
            id_generator.generate_id()
        basic_duration = time.time() - start_time
        
        start_time = time.time()
        for _ in range(10000):
            id_generator.generate_uuid()
        uuid_duration = time.time() - start_time
        
        start_time = time.time()
        for _ in range(10000):
            id_generator.generate_session_id()
        session_duration = time.time() - start_time
        
        print(f"基础ID生成: {basic_duration:.3f}s (10000次)")
        print(f"UUID生成: {uuid_duration:.3f}s (10000次)")
        print(f"会话ID生成: {session_duration:.3f}s (10000次)")
        
        # 验证性能要求
        assert basic_duration < 1.0  # 1秒内完成10000次生成
        assert uuid_duration < 1.0
        assert session_duration < 1.0
    
    def test_temporal_performance(self, setup_components):
        """测试时间管理性能"""
        _, _, _, _, temporal, _ = setup_components
        
        # 测试时间戳生成性能
        start_time = time.time()
        timestamps = []
        for _ in range(10000):
            timestamps.append(temporal.now())
        now_duration = time.time() - start_time
        
        # 测试时间戳格式化性能
        start_time = time.time()
        formatted = []
        for ts in timestamps:
            formatted.append(temporal.format_timestamp(ts, "iso"))
        format_duration = time.time() - start_time
        
        # 测试时间戳解析性能
        start_time = time.time()
        parsed = []
        for fmt in formatted:
            parsed.append(temporal.parse_timestamp(fmt, "iso"))
        parse_duration = time.time() - start_time
        
        print(f"时间戳生成: {now_duration:.3f}s (10000次)")
        print(f"时间戳格式化: {format_duration:.3f}s (10000次)")
        print(f"时间戳解析: {parse_duration:.3f}s (10000次)")
        
        # 验证性能要求
        assert now_duration < 1.0  # 1秒内完成10000次生成
        assert format_duration < 2.0  # 2秒内完成10000次格式化
        assert parse_duration < 2.0  # 2秒内完成10000次解析
    
    def test_metadata_performance(self, setup_components):
        """测试元数据管理性能"""
        _, _, _, _, _, metadata = setup_components
        
        # 准备测试元数据
        test_metadata = {
            "user_id": 123,
            "tags": ["tag1", "tag2", "tag3"],
            "nested": {
                "level1": {
                    "level2": {"value": "deep"}
                }
            },
            "timestamp": datetime.now(),
            "list_of_objects": [{"id": i, "name": f"item_{i}"} for i in range(100)]
        }
        
        # 测试元数据标准化性能
        start_time = time.time()
        for _ in range(1000):
            normalized = metadata.normalize_metadata(test_metadata)
        normalize_duration = time.time() - start_time
        
        # 测试元数据合并性能
        start_time = time.time()
        for i in range(1000):
            update = {"update_key": i, "timestamp": datetime.now()}
            merged = metadata.merge_metadata(test_metadata, update)
        merge_duration = time.time() - start_time
        
        print(f"元数据标准化: {normalize_duration:.3f}s (1000次)")
        print(f"元数据合并: {merge_duration:.3f}s (1000次)")
        
        # 验证性能要求
        assert normalize_duration < 1.0  # 1秒内完成1000次标准化
        assert merge_duration < 1.0      # 1秒内完成1000次合并
    
    @pytest.mark.asyncio
    async def test_integrated_performance(self, setup_components):
        """测试集成性能"""
        serializer, cache_manager, monitor, id_generator, temporal, metadata = setup_components
        
        # 模拟完整的操作流程
        start_time = time.time()
        
        for i in range(100):
            # 生成ID
            operation_id = id_generator.generate_id("operation")
            
            # 开始监控
            monitor_id = monitor.start_operation("integrated_test")
            
            # 创建数据
            data = {
                "id": operation_id,
                "timestamp": temporal.now(),
                "metadata": metadata.normalize_metadata({
                    "index": i,
                    "tags": [f"tag_{j}" for j in range(5)]
                })
            }
            
            # 序列化数据
            serialized = serializer.serialize(data, "compact_json")
            
            # 缓存数据
            await cache_manager.set(operation_id, data, ttl=300)
            
            # 从缓存读取
            cached_data = await cache_manager.get(operation_id)
            
            # 反序列化
            deserialized = serializer.deserialize(serialized, "compact_json")
            
            # 结束监控
            monitor.end_operation(monitor_id, "integrated_test", True)
        
        total_duration = time.time() - start_time
        
        # 获取性能统计
        stats = monitor.get_stats("integrated_test")
        cache_stats = cache_manager.get_stats()
        
        print(f"集成操作: {total_duration:.3f}s (100次完整流程)")
        print(f"平均操作时间: {stats['avg_duration']:.6f}s")
        print(f"缓存命中率: {cache_stats['hit_rate']:.2%}")
        
        # 验证性能要求
        assert total_duration < 5.0  # 5秒内完成100次完整流程
        assert stats["total_operations"] == 100
        assert stats["success_rate"] == 1.0
        assert cache_stats["hit_rate"] > 0.95  # 缓存命中率超过95%
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, setup_components):
        """测试内存使用情况"""
        import psutil
        import os
        
        _, cache_manager, _, _, _, _ = setup_components
        
        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量数据操作
        large_data = {"data": "x" * 10000}  # 10KB数据
        
        # 写入大量缓存项
        for i in range(1000):
            await cache_manager.set(f"large_key_{i}", large_data)
        
        # 读取所有缓存项
        for i in range(1000):
            await cache_manager.get(f"large_key_{i}")
        
        # 获取最终内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"初始内存: {initial_memory:.2f}MB")
        print(f"最终内存: {final_memory:.2f}MB")
        print(f"内存增长: {memory_increase:.2f}MB")
        
        # 验证内存使用合理（增长不超过100MB）
        assert memory_increase < 100  # 内存增长不超过100MB
        
        # 清理缓存
        for i in range(1000):
            await cache_manager.remove(f"large_key_{i}")
        
        # 验证缓存统计
        stats = cache_manager.get_stats()
        assert stats["size"] == 0  # 缓存应该被清空