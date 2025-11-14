"""缓存接口测试"""

import pytest
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from src.infrastructure.llm.cache.interfaces import ICacheProvider, ICacheKeyGenerator


class MockCacheProvider(ICacheProvider):
    """模拟缓存提供者用于测试"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._ttl: Dict[str, Optional[int]] = {}
        self._created: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._data:
            return None
        # 简单过期检查（实际测试中不需要）
        return self._data[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._data[key] = value
        self._ttl[key] = ttl
        self._created[key] = datetime.now().timestamp()
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            del self._ttl[key]
            del self._created[key]
            return True
        return False
    
    def clear(self) -> None:
        self._data.clear()
        self._ttl.clear()
        self._created.clear()
    
    def exists(self, key: str) -> bool:
        return key in self._data
    
    def get_size(self) -> int:
        return len(self._data)
    
    def cleanup_expired(self) -> int:
        return 0  # 简化实现
    
    async def get_async(self, key: str) -> Optional[Any]:
        return self.get(key)
    
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.set(key, value, ttl)


class MockKeyGenerator(ICacheKeyGenerator):
    """模拟键生成器用于测试"""
    
    def generate_key(self, *args, **kwargs) -> str:
        # 对位置参数进行哈希
        args_str = str(args)
        # 对关键字参数按键名排序后进行哈希，确保顺序无关性
        sorted_kwargs_items = sorted(kwargs.items())
        kwargs_str = str(sorted_kwargs_items)
        return f"key_{hash(args_str + kwargs_str)}"


class TestICacheProvider:
    """测试缓存提供者接口"""
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        provider = MockCacheProvider()
        
        # 检查所有抽象方法都被实现
        required_methods = [
            'get', 'set', 'delete', 'clear', 'exists', 
            'get_size', 'cleanup_expired', 'get_async', 'set_async'
        ]
        
        for method in required_methods:
            assert hasattr(provider, method), f"方法 {method} 不存在"
            assert callable(getattr(provider, method)), f"方法 {method} 不可调用"
    
    def test_get_returns_none_for_nonexistent_key(self):
        """测试获取不存在键返回None"""
        provider = MockCacheProvider()
        result = provider.get("nonexistent")
        assert result is None
    
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        provider = MockCacheProvider()
        
        provider.set("key1", "value1")
        result = provider.get("key1")
        assert result == "value1"
    
    def test_set_with_ttl(self):
        """测试设置带TTL的缓存"""
        provider = MockCacheProvider()
        
        provider.set("key1", "value1", ttl=60)
        result = provider.get("key1")
        assert result == "value1"
    
    def test_delete_existing_key(self):
        """测试删除存在的键"""
        provider = MockCacheProvider()
        
        provider.set("key1", "value1")
        result = provider.delete("key1")
        assert result is True
        assert provider.get("key1") is None
    
    def test_delete_nonexistent_key(self):
        """测试删除不存在的键"""
        provider = MockCacheProvider()
        result = provider.delete("nonexistent")
        assert result is False
    
    def test_clear_all(self):
        """测试清空所有缓存"""
        provider = MockCacheProvider()
        
        provider.set("key1", "value1")
        provider.set("key2", "value2")
        
        provider.clear()
        
        assert provider.get_size() == 0
        assert provider.get("key1") is None
        assert provider.get("key2") is None
    
    def test_exists(self):
        """测试键存在性检查"""
        provider = MockCacheProvider()
        
        provider.set("key1", "value1")
        
        assert provider.exists("key1") is True
        assert provider.exists("nonexistent") is False
    
    def test_get_size(self):
        """测试获取缓存大小"""
        provider = MockCacheProvider()
        
        assert provider.get_size() == 0
        
        provider.set("key1", "value1")
        assert provider.get_size() == 1
        
        provider.set("key2", "value2")
        assert provider.get_size() == 2
        
        provider.delete("key1")
        assert provider.get_size() == 1
    
    def test_cleanup_expired(self):
        """测试清理过期缓存"""
        provider = MockCacheProvider()
        
        count = provider.cleanup_expired()
        assert isinstance(count, int)
        assert count >= 0
    
    @pytest.mark.asyncio
    async def test_async_get(self):
        """测试异步获取"""
        provider = MockCacheProvider()
        
        provider.set("key1", "value1")
        result = await provider.get_async("key1")
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_async_get_nonexistent(self):
        """测试异步获取不存在的键"""
        provider = MockCacheProvider()
        result = await provider.get_async("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_async_set(self):
        """测试异步设置"""
        provider = MockCacheProvider()
        
        await provider.set_async("key1", "value1")
        result = await provider.get_async("key1")
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_async_set_with_ttl(self):
        """测试异步设置带TTL"""
        provider = MockCacheProvider()
        
        await provider.set_async("key1", "value1", ttl=60)
        result = await provider.get_async("key1")
        assert result == "value1"


class TestICacheKeyGenerator:
    """测试缓存键生成器接口"""
    
    def test_interface_methods_exist(self):
        """测试接口方法存在"""
        generator = MockKeyGenerator()
        
        assert hasattr(generator, 'generate_key'), "方法 generate_key 不存在"
        assert callable(generator.generate_key), "方法 generate_key 不可调用"
    
    def test_generate_key_with_args(self):
        """测试使用位置参数生成键"""
        generator = MockKeyGenerator()
        
        key1 = generator.generate_key("arg1", "arg2")
        key2 = generator.generate_key("arg1", "arg2")
        key3 = generator.generate_key("arg2", "arg1")
        
        # 相同参数应该生成相同键
        assert key1 == key2
        
        # 不同参数应该生成不同键
        assert key1 != key3
    
    def test_generate_key_with_kwargs(self):
        """测试使用关键字参数生成键"""
        generator = MockKeyGenerator()
        
        key1 = generator.generate_key(a="value1", b="value2")
        key2 = generator.generate_key(a="value1", b="value2")
        key3 = generator.generate_key(b="value2", a="value1")  # 顺序不同
        
        # 相同参数应该生成相同键
        assert key1 == key2
        
        # 参数顺序不同也应该生成相同键
        assert key1 == key3
    
    def test_generate_key_with_mixed_args(self):
        """测试混合位置和关键字参数"""
        generator = MockKeyGenerator()
        
        key1 = generator.generate_key("arg1", "arg2", a="value1", b="value2")
        key2 = generator.generate_key("arg1", "arg2", a="value1", b="value2")
        key3 = generator.generate_key("arg2", "arg1", a="value1", b="value2")  # 位置参数不同
        
        # 相同参数应该生成相同键
        assert key1 == key2
        
        # 位置参数不同应该生成不同键
        assert key1 != key3
    
    def test_generate_key_returns_string(self):
        """测试返回类型为字符串"""
        generator = MockKeyGenerator()
        
        key = generator.generate_key("test")
        assert isinstance(key, str)
        assert len(key) > 0


class TestCacheInterfaceContract:
    """测试缓存接口契约"""
    
    def test_cache_provider_is_abstract(self):
        """测试缓存提供者不能直接实例化"""
        # ICacheProvider 是抽象类，验证其抽象性
        assert hasattr(ICacheProvider, '__abstractmethods__')
        assert len(ICacheProvider.__abstractmethods__) > 0
    
    def test_cache_key_generator_is_abstract(self):
        """测试键生成器不能直接实例化"""
        # ICacheKeyGenerator 是抽象类，验证其抽象性
        assert hasattr(ICacheKeyGenerator, '__abstractmethods__')
        assert len(ICacheKeyGenerator.__abstractmethods__) > 0
    
    def test_concrete_implementation_is_allowed(self):
        """测试具体实现是允许的"""
        # 确保抽象类可以被继承
        class ConcreteProvider(MockCacheProvider):
            pass
        
        class ConcreteGenerator(MockKeyGenerator):
            pass
        
        provider = ConcreteProvider()
        generator = ConcreteGenerator()
        
        assert isinstance(provider, ICacheProvider)
        assert isinstance(generator, ICacheKeyGenerator)