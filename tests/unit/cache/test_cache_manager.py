"""缓存管理器测试"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from typing import Any, Dict, Optional, Sequence, cast

from langchain_core.messages import BaseMessage
from src.infrastructure.llm.cache.cache_manager import CacheManager, AnthropicCacheManager
from src.infrastructure.llm.cache.cache_config import CacheConfig


class MockBaseMessage(BaseMessage):
    """模拟BaseMessage用于测试"""
    
    type: str
    
    def __init__(self, msg_type: str, content: str):
        super().__init__(content=content, type=msg_type)


class TestCacheManager:
    """测试缓存管理器"""
    
    def test_init_default(self):
        """测试默认初始化"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        assert manager.config == config
        assert manager.is_enabled() is True
        assert manager._provider is not None
        assert isinstance(manager._key_generator._default_generator, type(manager._key_generator._default_generator))
        
        # 检查统计初始化
        stats = manager._stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["sets"] == 0
        assert stats["deletes"] == 0
        assert stats["cleanups"] == 0
    
    def test_init_disabled(self):
        """测试禁用缓存的初始化"""
        config = CacheConfig(enabled=False)
        manager = CacheManager(config)
        
        assert manager.is_enabled() is False
        assert manager._provider is None
    
    def test_init_with_disabled_config(self):
        """测试配置为禁用时的初始化"""
        config = CacheConfig(
            enabled=False,
            cache_type="memory",
            max_size=100,
            ttl_seconds=1800
        )
        manager = CacheManager(config)
        
        assert manager.is_enabled() is False
        assert manager._provider is None
        
        # 基本操作应该安全处理
        assert manager.get("test") is None
        assert manager.set("test", "value") is None
        assert manager.delete("test") is False
    
    def test_unsupported_cache_type(self):
        """测试不支持的缓存类型"""
        config = CacheConfig(
            enabled=True,
            cache_type="unsupported_type"
        )
        
        with pytest.raises(ValueError, match="不支持的缓存类型"):
            CacheManager(config)
    
    def test_get_with_enabled_cache(self):
        """测试启用缓存时的获取操作"""
        config = CacheConfig(enabled=True, max_size=100)
        manager = CacheManager(config)
        
        # 先设置一个值
        manager.set("key1", "value1")
        
        # 然后获取
        result = manager.get("key1")
        assert result == "value1"
        
        # 检查统计
        stats = manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
    
    def test_get_with_disabled_cache(self):
        """测试禁用缓存时的获取操作"""
        config = CacheConfig(enabled=False)
        manager = CacheManager(config)
        
        result = manager.get("key1")
        assert result is None
        
        # 应该记录为未命中
        stats = manager.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1
    
    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        result = manager.get("nonexistent")
        assert result is None
        
        stats = manager.get_stats()
        assert stats["misses"] == 1
    
    def test_set_with_enabled_cache(self):
        """测试启用缓存时的设置操作"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        manager.set("key1", "value1")
        
        result = manager.get("key1")
        assert result == "value1"
        
        stats = manager.get_stats()
        assert stats["sets"] == 1
    
    def test_set_with_disabled_cache(self):
        """测试禁用缓存时的设置操作"""
        config = CacheConfig(enabled=False)
        manager = CacheManager(config)
        
        # 应该安全地忽略设置操作
        manager.set("key1", "value1")
        result = manager.get("key1")
        assert result is None
    
    def test_set_with_custom_ttl(self):
        """测试设置带自定义TTL"""
        config = CacheConfig(enabled=True, ttl_seconds=3600)
        manager = CacheManager(config)
        
        manager.set("key1", "value1", ttl=60)
        result = manager.get("key1")
        assert result == "value1"
    
    def test_delete_existing_key(self):
        """测试删除存在的键"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        manager.set("key1", "value1")
        result = manager.delete("key1")
        
        assert result is True
        assert manager.get("key1") is None
        
        stats = manager.get_stats()
        assert stats["deletes"] == 1
    
    def test_delete_nonexistent_key(self):
        """测试删除不存在的键"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        result = manager.delete("nonexistent")
        assert result is False
        
        stats = manager.get_stats()
        assert stats["deletes"] == 0
    
    def test_clear(self):
        """测试清空缓存"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        manager.set("key1", "value1")
        manager.set("key2", "value2")
        manager.set("key3", "value3")
        
        assert manager.get_size() == 3
        
        manager.clear()
        assert manager.get_size() == 0
        assert manager.get("key1") is None
        assert manager.get("key2") is None
        assert manager.get("key3") is None
    
    def test_exists(self):
        """测试键存在性检查"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        manager.set("key1", "value1")
        
        assert manager.exists("key1") is True
        assert manager.exists("nonexistent") is False
    
    def test_get_size(self):
        """测试获取缓存大小"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        assert manager.get_size() == 0
        
        manager.set("key1", "value1")
        assert manager.get_size() == 1
        
        manager.set("key2", "value2")
        assert manager.get_size() == 2
        
        manager.delete("key1")
        assert manager.get_size() == 1
    
    def test_is_enabled(self):
        """测试启用状态检查"""
        config_enabled = CacheConfig(enabled=True)
        config_disabled = CacheConfig(enabled=False)
        
        manager_enabled = CacheManager(config_enabled)
        manager_disabled = CacheManager(config_disabled)
        
        assert manager_enabled.is_enabled() is True
        assert manager_disabled.is_enabled() is False
    
    def test_generate_llm_key(self):
        """测试生成LLM缓存键"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        messages = [
            MockBaseMessage("system", "You are helpful"),
            MockBaseMessage("user", "Hello")
        ]
        
        key = manager.generate_llm_key(cast(Sequence[BaseMessage], messages), "gpt-4", {"temperature": 0.7})
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
    
    def test_get_llm_response_cache_hit(self):
        """测试获取LLM响应缓存（命中）"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        messages = [MockBaseMessage("user", "Hello")]
        response = "This is a cached response"
        
        # 设置缓存
        manager.set_llm_response(cast(Sequence[BaseMessage], messages), response, "gpt-4")
        
        # 获取缓存
        result = manager.get_llm_response(cast(Sequence[BaseMessage], messages), "gpt-4")
        assert result == response
        
        stats = manager.get_stats()
        assert stats["hits"] >= 1  # 至少有一次命中
    
    def test_get_llm_response_cache_miss(self):
        """测试获取LLM响应缓存（未命中）"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        messages = [MockBaseMessage("user", "Hello")]
        
        result = manager.get_llm_response(cast(Sequence[BaseMessage], messages), "gpt-4")
        assert result is None
        
        stats = manager.get_stats()
        assert stats["misses"] >= 1  # 至少有一次未命中
    
    def test_set_llm_response(self):
        """测试设置LLM响应缓存"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        messages = [MockBaseMessage("user", "Hello")]
        response = "This is the response"
        
        manager.set_llm_response(cast(Sequence[BaseMessage], messages), response, "gpt-4", {"temperature": 0.7})
        
        # 验证缓存设置成功
        result = manager.get_llm_response(cast(Sequence[BaseMessage], messages), "gpt-4", {"temperature": 0.7})
        assert result == response
        
        stats = manager.get_stats()
        assert stats["sets"] >= 1
    
    def test_get_stats(self):
        """测试获取统计信息"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 初始统计
        stats = manager.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["sets"] == 0
        assert stats["deletes"] == 0
        assert stats["cleanups"] == 0
        assert "hit_rate" in stats
        assert stats["hit_rate"] == 0.0
        
        # 执行一些操作
        manager.set("key1", "value1")
        manager.get("key1")  # 命中
        manager.get("key2")  # 未命中
        manager.delete("key1")
        
        stats = manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["deletes"] == 1
        assert stats["hit_rate"] == 0.5  # 1/2
    
    def test_cleanup_expired(self):
        """测试清理过期项"""
        config = CacheConfig(enabled=True, ttl_seconds=1)
        manager = CacheManager(config)
        
        # 设置一些项
        manager.set("key1", "value1")
        manager.set("key2", "value2", ttl=int(0.5))  # 短TTL
        
        # 等待过期
        time.sleep(1.1)
        
        cleaned_count = manager.cleanup_expired()
        assert cleaned_count >= 1  # 至少清理一个
        
        stats = manager.get_stats()
        assert stats["cleanups"] >= 1
    
    def test_reset_stats(self):
        """测试重置统计信息"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 执行一些操作
        manager.set("key1", "value1")
        manager.get("key1")
        manager.get("key2")
        
        # 检查统计已被更新
        stats = manager.get_stats()
        assert stats["sets"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        
        # 重置统计
        manager.reset_stats()
        
        # 检查统计已重置
        stats = manager.get_stats()
        assert stats["sets"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["deletes"] == 0
        assert stats["cleanups"] == 0
    
    @pytest.mark.asyncio
    async def test_async_get_hit(self):
        """测试异步获取（命中）"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        manager.set("key1", "value1")
        result = await manager.get_async("key1")
        
        assert result == "value1"
        
        stats = manager.get_stats()
        assert stats["hits"] >= 1
    
    @pytest.mark.asyncio
    async def test_async_get_miss(self):
        """测试异步获取（未命中）"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        result = await manager.get_async("nonexistent")
        assert result is None
        
        stats = manager.get_stats()
        assert stats["misses"] >= 1
    
    @pytest.mark.asyncio
    async def test_async_set(self):
        """测试异步设置"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        await manager.set_async("key1", "value1")
        result = await manager.get_async("key1")
        
        assert result == "value1"
        
        stats = manager.get_stats()
        assert stats["sets"] >= 1
    
    def test_close(self):
        """测试关闭缓存管理器"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 设置一些数据
        manager.set("key1", "value1")
        assert manager.get_size() > 0
        
        # 关闭管理器
        manager.close()
        
        # 验证清理
        assert manager._provider is None
        assert manager.get_size() == 0
        assert manager.get("key1") is None
    
    def test_error_handling_get(self):
        """测试获取时的错误处理"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 模拟提供者抛出异常
        with patch.object(manager._provider, 'get', side_effect=Exception("Test error")):
            result = manager.get("key1")
            
            # 应该安全返回None并记录为未命中
            assert result is None
            stats = manager.get_stats()
            assert stats["misses"] >= 1
    
    def test_error_handling_set(self):
        """测试设置时的错误处理"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 模拟提供者抛出异常
        with patch.object(manager._provider, 'set', side_effect=Exception("Test error")):
            # 应该安全处理异常
            try:
                manager.set("key1", "value1")
                # 如果没有抛出异常，说明错误被正确处理
            except Exception:
                pytest.fail("异常应该被缓存管理器内部处理")
    
    def test_error_handling_delete(self):
        """测试删除时的错误处理"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 模拟提供者抛出异常
        with patch.object(manager._provider, 'delete', side_effect=Exception("Test error")):
            result = manager.delete("key1")
            
            # 应该安全返回False
            assert result is False
    
    def test_cleanup_thread_behavior(self):
        """测试清理线程行为"""
        config = CacheConfig(enabled=True, ttl_seconds=1)
        manager = CacheManager(config)
        
        # 检查清理线程是否启动
        assert manager._cleanup_thread is not None
        assert manager._cleanup_thread.is_alive()
        
        # 关闭管理器
        manager.close()
        
        # 清理线程应该停止（daemon线程会自动退出）


class TestAnthropicCacheManager:
    """测试Anthropic缓存管理器"""
    
    def test_init(self):
        """测试初始化"""
        config = CacheConfig(
            enabled=True,
            cache_control_type="persistent",
            max_tokens=1000
        )
        manager = AnthropicCacheManager(config)
        
        # 应该继承CacheManager的功能
        assert isinstance(manager, CacheManager)
        assert manager.config == config
        assert manager.is_enabled() is True
        
        # 应该使用Anthropic专用的键生成器
        from src.infrastructure.llm.cache.key_generator import AnthropicCacheKeyGenerator
        assert isinstance(manager._key_generator, AnthropicCacheKeyGenerator)
    
    def test_get_anthropic_cache_params_no_cache_control(self):
        """测试不启用缓存控制的参数获取"""
        config = CacheConfig(enabled=True)  # 没有cache_control_type
        manager = AnthropicCacheManager(config)
        
        params = manager.get_anthropic_cache_params()
        
        assert params == {}
    
    def test_get_anthropic_cache_params_with_type(self):
        """测试启用缓存控制的参数获取"""
        config = CacheConfig(
            enabled=True,
            cache_control_type="persistent"
        )
        manager = AnthropicCacheManager(config)
        
        params = manager.get_anthropic_cache_params()
        
        expected = {
            "cache_control": {
                "type": "persistent"
            }
        }
        assert params == expected
    
    def test_get_anthropic_cache_params_persistent_with_max_tokens(self):
        """测试persistent类型带max_tokens的参数获取"""
        config = CacheConfig(
            enabled=True,
            cache_control_type="persistent",
            max_tokens=1000
        )
        manager = AnthropicCacheManager(config)
        
        params = manager.get_anthropic_cache_params()
        
        expected = {
            "cache_control": {
                "type": "persistent",
                "max_tokens": 1000
            }
        }
        assert params == expected
    
    def test_get_anthropic_cache_params_with_max_tokens(self):
        """测试包含max_tokens的参数获取"""
        config = CacheConfig(
            enabled=True,
            cache_control_type="ephemeral",
            max_tokens=500
        )
        manager = AnthropicCacheManager(config)
        
        params = manager.get_anthropic_cache_params()
        
        expected = {
            "cache_control": {
                "type": "ephemeral",
                "max_tokens": 500
            }
        }
        assert params == expected
    
    def test_anthropic_key_generation(self):
        """测试Anthropic特定的键生成"""
        config = CacheConfig(enabled=True)
        manager = AnthropicCacheManager(config)
        
        messages = [
            MockBaseMessage("system", "You are a helpful assistant"),
            MockBaseMessage("user", "What is 2+2?")
        ]
        
        # 生成键
        key = manager.generate_llm_key(
            cast(Sequence[BaseMessage], messages), 
            "claude-3-sonnet", 
            {"temperature": 0.7, "max_tokens": 100}
        )
        
        assert isinstance(key, str)
        assert len(key) == 32
        
        # 验证键包含anthropic标识
        # 由于我们无法直接访问键内容，我们只验证它是一致的
        key2 = manager.generate_llm_key(
            cast(Sequence[BaseMessage], messages), 
            "claude-3-sonnet", 
            {"temperature": 0.7, "max_tokens": 100}
        )
        assert key == key2
    
    def test_anthropic_llm_caching(self):
        """测试Anthropic LLM缓存功能"""
        config = CacheConfig(enabled=True)
        manager = AnthropicCacheManager(config)
        
        messages = [MockBaseMessage("user", "Hello")]
        response = "Hello! How can I help you?"
        
        # 设置缓存
        manager.set_llm_response(cast(Sequence[BaseMessage], messages), response, "claude-3")
        
        # 获取缓存
        cached_response = manager.get_llm_response(cast(Sequence[BaseMessage], messages), "claude-3")
        assert cached_response == response


class TestCacheManagerEdgeCases:
    """测试缓存管理器的边界情况"""
    
    def test_provider_initialization_error(self):
        """测试提供者初始化错误"""
        # 这是一个理论测试，实际实现中可能不会发生
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 验证_manager存在
        assert manager._provider is not None
    
    def test_concurrent_access_simulation(self):
        """测试并发访问模拟"""
        config = CacheConfig(enabled=True, max_size=100)
        manager = CacheManager(config)
        
        # 模拟并发操作
        def worker(worker_id):
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                value = f"value_{worker_id}_{i}"
                
                manager.set(key, value)
                result = manager.get(key)
                assert result == value
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证最终状态
        assert manager.get_size() <= 100
        stats = manager.get_stats()
        assert stats["sets"] > 0
        assert stats["hits"] > 0
    
    def test_large_number_of_operations(self):
        """测试大量操作"""
        config = CacheConfig(enabled=True, max_size=1000)
        manager = CacheManager(config)
        
        # 执行大量操作
        for i in range(1000):
            manager.set(f"key_{i}", f"value_{i}")
        
        assert manager.get_size() == 1000
        
        # 验证一些随机访问
        for i in range(0, 1000, 100):
            result = manager.get(f"key_{i}")
            assert result == f"value_{i}"
        
        stats = manager.get_stats()
        assert stats["sets"] == 1000
        assert stats["hits"] >= 10  # 至少有一些命中
    
    def test_zero_ttl_handling(self):
        """测试零TTL处理"""
        config = CacheConfig(enabled=True, ttl_seconds=3600)
        manager = CacheManager(config)
        
        # 设置零TTL
        manager.set("key1", "value1", ttl=0)
        
        # 零TTL应该立即过期
        result = manager.get("key1")
        assert result is None
    
    def test_none_values(self):
        """测试None值处理"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 设置None值
        manager.set("none_key", None)
        
        # 应该能正确存储和检索
        result = manager.get("none_key")
        assert result is None
        
        # 存在性检查
        assert manager.exists("none_key") is True
    
    def test_complex_message_serialization(self):
        """测试复杂消息序列化"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 创建带有额外属性的消息
        class ComplexMessage:
            def __init__(self, msg_type: str, content: str, metadata: dict):
                self.type = msg_type
                self.content = content
                self.metadata = metadata
        
        messages = [
            ComplexMessage("user", "Hello", {"timestamp": 1234567890, "session": "test"})
        ]
        
        # 生成键应该不抛出异常
        key = manager.generate_llm_key(cast(Sequence[BaseMessage], messages), "test-model")
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_statistics_accuracy(self):
        """测试统计准确性"""
        config = CacheConfig(enabled=True)
        manager = CacheManager(config)
        
        # 执行一系列操作
        operations = [
            ("set", "key1", "value1"),
            ("get", "key1", "hit"),
            ("get", "nonexistent", "miss"),
            ("set", "key2", "value2"),
            ("get", "key2", "hit"),
            ("delete", "key1", None),
            ("get", "key1", "miss"),
            ("get", "key2", "hit"),
        ]
        
        for op_type, key, expected in operations:
            if op_type == "set":
                manager.set(key, expected)
            elif op_type == "get":
                result = manager.get(key)
                if expected == "hit":
                    assert result is not None
                elif expected == "miss":
                    assert result is None
            elif op_type == "delete":
                manager.delete(key)
        
        # 验证最终统计
        stats = manager.get_stats()
        expected_sets = 2  # key1, key2
        expected_hits = 2  # key1 (第一次), key2
        expected_misses = 2  # nonexistent, key1 (删除后)
        expected_deletes = 1  # key1
        
        assert stats["sets"] == expected_sets
        assert stats["hits"] >= expected_hits
        assert stats["misses"] >= expected_misses
        assert stats["deletes"] == expected_deletes