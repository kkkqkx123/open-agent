from typing import Dict, Any, Optional
from .connection_pool import HTTPConnectionPool, connection_pool_manager


class ConnectionPoolFactory:
    """连接池工厂 - 用于创建和管理连接池实例"""
    
    @staticmethod
    def create_connection_pool(
        max_connections: int = 10,
        max_keepalive: int = 10,
        timeout: float = 30.0
    ) -> HTTPConnectionPool:
        """
        创建连接池实例
        
        Args:
            max_connections: 最大连接数
            max_keepalive: 最大保活连接数
            timeout: 连接超时时间（秒）
        
        Returns:
            HTTPConnectionPool: 连接池实例
        """
        return connection_pool_manager.create(
            max_connections=max_connections,
            max_keepalive=max_keepalive,
            timeout=timeout
        )
    
    @staticmethod
    def get_global_connection_pool() -> HTTPConnectionPool:
        """
        获取全局连接池实例
        
        Returns:
            HTTPConnectionPool: 全局连接池实例
        """
        return connection_pool_manager.create()


# 全局连接池工厂实例
pool_factory = ConnectionPoolFactory()