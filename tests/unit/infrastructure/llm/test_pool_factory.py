"""连接池工厂单元测试"""

import pytest
from unittest.mock import patch, MagicMock

from src.infrastructure.llm.pool.factory import ConnectionPoolFactory, pool_factory
from src.infrastructure.llm.pool.connection_pool import HTTPConnectionPool


class TestConnectionPoolFactory:
    """连接池工厂测试"""
    
    def test_create_connection_pool_with_default_params(self):
        """测试使用默认参数创建连接池"""
        with patch('src.infrastructure.llm.pool.factory.connection_pool_manager') as mock_manager:
            mock_pool = MagicMock(spec=HTTPConnectionPool)
            mock_manager.get_pool.return_value = mock_pool
            
            factory = ConnectionPoolFactory()
            pool = factory.create_connection_pool()
            
            mock_manager.get_pool.assert_called_once_with(
                max_connections=10,
                max_keepalive=10,
                timeout=30.0
            )
            assert pool == mock_pool
    
    def test_create_connection_pool_with_custom_params(self):
        """测试使用自定义参数创建连接池"""
        with patch('src.infrastructure.llm.pool.factory.connection_pool_manager') as mock_manager:
            mock_pool = MagicMock(spec=HTTPConnectionPool)
            mock_manager.get_pool.return_value = mock_pool
            
            factory = ConnectionPoolFactory()
            pool = factory.create_connection_pool(
                max_connections=20,
                max_keepalive=5,
                timeout=60.0
            )
            
            mock_manager.get_pool.assert_called_once_with(
                max_connections=20,
                max_keepalive=5,
                timeout=60.0
            )
            assert pool == mock_pool
    
    def test_get_global_connection_pool(self):
        """测试获取全局连接池"""
        with patch('src.infrastructure.llm.pool.factory.connection_pool_manager') as mock_manager:
            mock_pool = MagicMock(spec=HTTPConnectionPool)
            mock_manager.get_pool.return_value = mock_pool
            
            factory = ConnectionPoolFactory()
            pool = factory.get_global_connection_pool()
            
            mock_manager.get_pool.assert_called_once_with()
            assert pool == mock_pool
    
    def test_static_methods(self):
        """测试静态方法"""
        # 验证方法是静态的
        assert ConnectionPoolFactory.create_connection_pool.__self__ is None
        assert ConnectionPoolFactory.get_global_connection_pool.__self__ is None


class TestGlobalPoolFactory:
    """全局连接池工厂测试"""
    
    def test_global_factory_singleton(self):
        """测试全局工厂单例"""
        factory1 = pool_factory
        factory2 = pool_factory
        
        assert factory1 is factory2
        assert isinstance(factory1, ConnectionPoolFactory)
    
    def test_global_factory_create_connection_pool(self):
        """测试全局工厂创建连接池"""
        with patch('src.infrastructure.llm.pool.factory.connection_pool_manager') as mock_manager:
            mock_pool = MagicMock(spec=HTTPConnectionPool)
            mock_manager.get_pool.return_value = mock_pool
            
            pool = pool_factory.create_connection_pool(
                max_connections=15,
                max_keepalive=8,
                timeout=45.0
            )
            
            mock_manager.get_pool.assert_called_once_with(
                max_connections=15,
                max_keepalive=8,
                timeout=45.0
            )
            assert pool == mock_pool
    
    def test_global_factory_get_global_connection_pool(self):
        """测试全局工厂获取全局连接池"""
        with patch('src.infrastructure.llm.pool.factory.connection_pool_manager') as mock_manager:
            mock_pool = MagicMock(spec=HTTPConnectionPool)
            mock_manager.get_pool.return_value = mock_pool
            
            pool = pool_factory.get_global_connection_pool()
            
            mock_manager.get_pool.assert_called_once_with()
            assert pool == mock_pool