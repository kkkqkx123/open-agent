"""连接池单元测试"""

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.infrastructure.llm.pool.connection_pool import HTTPConnectionPool, ConnectionPoolManager, connection_pool_manager
from src.infrastructure.llm.pool.interfaces import IConnectionPool


class TestHTTPConnectionPool:
    """HTTP连接池测试"""
    
    @pytest.fixture
    def pool(self):
        """创建连接池实例"""
        return HTTPConnectionPool(max_connections=5, max_keepalive=3, timeout=10.0)
    
    @pytest.mark.asyncio
    async def test_acquire_new_connection(self, pool):
        """测试获取新连接"""
        base_url = "https://api.example.com"
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            connection = await pool.acquire(base_url)
            
            assert connection == mock_session
            mock_session_class.assert_called_once()
            assert pool._stats["created_connections"] == 1
            assert pool._stats["total_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_acquire_reused_connection(self, pool):
        """测试重用连接"""
        base_url = "https://api.example.com"
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 第一次获取连接
            connection1 = await pool.acquire(base_url)
            await pool.release(base_url, connection1)
            
            # 第二次获取连接，应该重用
            connection2 = await pool.acquire(base_url)
            
            assert connection2 == connection1
            assert pool._stats["created_connections"] == 1
            assert pool._stats["connection_reuses"] == 1
            assert pool._stats["total_requests"] == 2
    
    @pytest.mark.asyncio
    async def test_acquire_invalid_connection(self, pool):
        """测试获取无效连接时创建新连接"""
        base_url = "https://api.example.com"
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session1 = AsyncMock()
            mock_session2 = AsyncMock()
            mock_session_class.side_effect = [mock_session1, mock_session2]
            
            # 创建并释放一个连接
            connection1 = await pool.acquire(base_url)
            await pool.release(base_url, connection1)
            
            # 模拟连接过期
            connection_info = pool._pools[base_url][0]
            connection_info['created_at'] = datetime.now() - timedelta(minutes=35)
            
            # 再次获取连接，应该创建新连接
            connection2 = await pool.acquire(base_url)
            
            assert connection2 == mock_session2
            assert pool._stats["created_connections"] == 2
            assert pool._stats["connection_reuses"] == 0
    
    @pytest.mark.asyncio
    async def test_release_connection_pool_full(self, pool):
        """测试连接池满时关闭连接"""
        base_url = "https://api.example.com"
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_sessions = [AsyncMock() for _ in range(5)]
            mock_session_class.side_effect = mock_sessions
            
            # 创建超过max_keepalive数量的连接
            connections = []
            for i in range(5):
                conn = await pool.acquire(base_url)
                connections.append(conn)
                await pool.release(base_url, conn)
            
            # 验证只有max_keepalive个连接被保留
            assert len(pool._pools[base_url]) == pool.max_keepalive
            
            # 验证多余的连接被关闭
            closed_count = sum(1 for conn in mock_sessions if conn.close.called)
            assert closed_count == 2  # 5 - 3 = 2
    
    @pytest.mark.asyncio
    async def test_get_stats(self, pool):
        """测试获取统计信息"""
        base_url = "https://api.example.com"
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # 执行一些操作
            connection = await pool.acquire(base_url)
            await pool.release(base_url, connection)
            
            stats = pool.get_stats()
            
            assert stats["total_requests"] == 1
            assert stats["created_connections"] == 1
            assert stats["active_connections"] == 1
            assert stats["pools_count"] == 1
    
    @pytest.mark.asyncio
    async def test_close_all(self, pool):
        """测试关闭所有连接"""
        base_url1 = "https://api.example1.com"
        base_url2 = "https://api.example2.com"
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_sessions = [AsyncMock() for _ in range(4)]
            mock_session_class.side_effect = mock_sessions
            
            # 创建连接
            conn1 = await pool.acquire(base_url1)
            conn2 = await pool.acquire(base_url2)
            await pool.release(base_url1, conn1)
            await pool.release(base_url2, conn2)
            
            # 关闭所有连接
            await pool.close_all()
            
            # 验证所有连接被关闭
            for mock_session in mock_sessions:
                mock_session.close.assert_called_once()
            
            # 验证连接池被清空
            assert len(pool._pools) == 0
    
    def test_is_connection_valid(self, pool):
        """测试连接有效性检查"""
        # 创建有效的连接信息
        valid_connection_info = {
            'connection': AsyncMock(),
            'created_at': datetime.now() - timedelta(minutes=10),
            'last_used': datetime.now() - timedelta(minutes=5)
        }
        
        # 创建过期的连接信息
        expired_connection_info = {
            'connection': AsyncMock(),
            'created_at': datetime.now() - timedelta(minutes=35),
            'last_used': datetime.now() - timedelta(minutes=5)
        }
        
        # 创建空闲时间过长的连接信息
        idle_connection_info = {
            'connection': AsyncMock(),
            'created_at': datetime.now() - timedelta(minutes=10),
            'last_used': datetime.now() - timedelta(minutes=15)
        }
        
        assert pool._is_connection_valid(valid_connection_info) == True
        assert pool._is_connection_valid(expired_connection_info) == False
        assert pool._is_connection_valid(idle_connection_info) == False


class TestConnectionPoolManager:
    """连接池管理器测试"""
    
    def test_get_pool(self):
        """测试获取连接池"""
        manager = ConnectionPoolManager()
        
        # 第一次获取应该创建新实例
        pool1 = manager.get_pool(max_connections=10, max_keepalive=5, timeout=20.0)
        assert isinstance(pool1, HTTPConnectionPool)
        assert pool1.max_connections == 10
        assert pool1.max_keepalive == 5
        assert pool1.timeout == 20.0
        
        # 第二次获取应该返回相同实例
        pool2 = manager.get_pool()
        assert pool1 is pool2
    
    @pytest.mark.asyncio
    async def test_close_all(self):
        """测试关闭所有连接池"""
        manager = ConnectionPoolManager()
        
        with patch.object(HTTPConnectionPool, 'close_all', new_callable=AsyncMock) as mock_close:
            pool = manager.get_pool()
            await manager.close_all()
            
            mock_close.assert_called_once()
            assert manager._pool is None


class TestGlobalConnectionPoolManager:
    """全局连接池管理器测试"""
    
    def test_global_manager_singleton(self):
        """测试全局管理器单例"""
        manager1 = connection_pool_manager
        manager2 = connection_pool_manager
        
        assert manager1 is manager2
    
    def test_global_manager_get_pool(self):
        """测试全局管理器获取连接池"""
        pool = connection_pool_manager.get_pool()
        assert isinstance(pool, HTTPConnectionPool)


class TestConnectionPoolInterface:
    """连接池接口测试"""
    
    def test_interface_compliance(self):
        """测试接口合规性"""
        pool = HTTPConnectionPool()
        assert isinstance(pool, IConnectionPool)
        
        # 验证接口方法存在
        assert hasattr(pool, 'acquire')
        assert hasattr(pool, 'release')
        assert hasattr(pool, 'get_stats')
        
        # 验证方法是异步的
        import inspect
        assert inspect.iscoroutinefunction(pool.acquire)
        assert inspect.iscoroutinefunction(pool.release)