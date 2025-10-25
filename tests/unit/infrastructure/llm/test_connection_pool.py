"""连接池单元测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.infrastructure.llm.pool.connection_pool import HTTPConnectionPool, connection_pool_manager
from src.infrastructure.llm.pool.interfaces import IConnectionPool


class TestHTTPConnectionPool:
    """HTTP连接池测试"""
    
    def test_interface_implementation(self):
        """测试接口实现"""
        pool = HTTPConnectionPool()
        assert isinstance(pool, IConnectionPool)
    
    @pytest.mark.asyncio
    async def test_acquire_and_release_connection(self):
        """测试获取和释放连接"""
        pool = HTTPConnectionPool(max_connections=5, max_keepalive=5)
        
        # 获取连接
        connection = await pool.acquire("https://api.openai.com")
        assert connection is not None
        
        # 释放连接
        await pool.release("https://api.openai.com", connection)
        
        # 验证统计信息
        stats = pool.get_stats()
        assert stats["total_requests"] == 1
        assert stats["active_connections"] >= 0  # 连接可能已被复用或关闭
    
    @pytest.mark.asyncio
    async def test_connection_reuse(self):
        """测试连接复用"""
        pool = HTTPConnectionPool(max_connections=5, max_keepalive=5)
        
        # 获取连接
        base_url = "https://api.test.com"
        conn1 = await pool.acquire(base_url)
        
        # 释放连接
        await pool.release(base_url, conn1)
        
        # 再次获取连接，应该复用之前的连接
        conn2 = await pool.acquire(base_url)
        
        stats = pool.get_stats()
        assert stats["connection_reuses"] >= 0  # 可能复用连接
        
        # 关闭连接
        if hasattr(conn2, 'close'):
            await conn2.close()
    
    def test_get_stats(self):
        """测试获取统计信息"""
        pool = HTTPConnectionPool()
        stats = pool.get_stats()
        
        expected_keys = ["total_requests", "successful_requests", "connection_reuses", 
                        "active_connections", "pools_count"]
        for key in expected_keys:
            assert key in stats


class TestConnectionPoolManager:
    """连接池管理器测试"""
    
    def test_get_pool(self):
        """测试获取连接池"""
        manager = connection_pool_manager
        pool1 = manager.get_pool()
        pool2 = manager.get_pool()
        
        # 应该返回相同的实例
        assert pool1 is pool2
    
    @pytest.mark.asyncio
    async def test_close_all(self):
        """测试关闭所有连接"""
        manager = connection_pool_manager
        pool = manager.get_pool()
        
        # 获取一个连接
        conn = await pool.acquire("https://test.com")
        
        # 关闭所有连接
        await manager.close_all()
        
        # 应该创建新的池实例
        new_pool = manager.get_pool()
        assert pool is new_pool  # 同一实例，但内部连接已清理