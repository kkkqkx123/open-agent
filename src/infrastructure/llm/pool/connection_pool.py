import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from threading import Lock
from datetime import datetime, timedelta
from .interfaces import IConnectionPool


class HTTPConnectionPool(IConnectionPool):
    """HTTP连接池实现"""
    
    def __init__(
        self,
        max_connections: int = 10,
        max_keepalive: int = 10,
        timeout: float = 30.0
    ):
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.timeout = timeout
        self._pools: Dict[str, List[Dict[str, Any]]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "connection_reuses": 0,
            "created_connections": 0
        }
        self._lock = asyncio.Lock()  # 用于保护共享状态
    
    async def acquire(self, base_url: str) -> aiohttp.ClientSession:
        """获取连接"""
        async with self._lock:
            if base_url not in self._locks:
                self._locks[base_url] = asyncio.Lock()
        
        async with self._locks[base_url]:
            if base_url not in self._pools:
                self._pools[base_url] = []
            
            # 检查是否有可用的空闲连接
            if self._pools[base_url]:
                connection_info = self._pools[base_url].pop()
                connection = connection_info['connection']
                
                # 检查连接是否仍然有效
                if not self._is_connection_valid(connection_info):
                    # 连接已失效，创建新连接
                    await connection.close()
                    connection = await self._create_session(base_url)
                    self._stats["created_connections"] += 1
                else:
                    self._stats["connection_reuses"] += 1
            else:
                # 创建新连接
                connection = await self._create_session(base_url)
                self._stats["created_connections"] += 1
            
            self._stats["total_requests"] += 1
            return connection
    
    async def release(self, base_url: str, connection: aiohttp.ClientSession) -> None:
        """释放连接"""
        async with self._lock:
            if base_url not in self._locks:
                self._locks[base_url] = asyncio.Lock()
        
        async with self._locks[base_url]:
            if base_url not in self._pools:
                self._pools[base_url] = []
            
            # 如果连接池未满，则将连接放回池中
            if len(self._pools[base_url]) < self.max_keepalive:
                connection_info = {
                    'connection': connection,
                    'created_at': datetime.now(),
                    'last_used': datetime.now()
                }
                self._pools[base_url].append(connection_info)
            else:
                # 连接池已满，关闭连接
                await connection.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        stats = self._stats.copy()
        active_connections = sum(len(pool) for pool in self._pools.values())
        stats['active_connections'] = active_connections
        stats['pools_count'] = len(self._pools)
        return stats
    
    async def _create_session(self, base_url: str) -> aiohttp.ClientSession:
        """创建新的HTTP会话"""
        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            keepalive_timeout=30.0
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        return session
    
    def _is_connection_valid(self, connection_info: Dict[str, Any]) -> bool:
        """检查连接是否仍然有效"""
        # 检查连接是否超过保活时间
        age = datetime.now() - connection_info['created_at']
        if age > timedelta(minutes=30):  # 30分钟最大保活时间
            return False
        
        # 检查最后使用时间
        last_used = connection_info['last_used']
        idle_time = datetime.now() - last_used
        if idle_time > timedelta(minutes=10):  # 10分钟无使用则认为失效
            return False
        
        return True
    
    async def close_all(self) -> None:
        """关闭所有连接"""
        for base_url in self._pools:
            for connection_info in self._pools[base_url]:
                await connection_info['connection'].close()
        self._pools.clear()


class ConnectionPoolManager:
    """连接池管理器 - 用于管理全局连接池实例"""
    
    def __init__(self):
        self._pool: Optional[HTTPConnectionPool] = None
    
    def get_pool(self, max_connections: int = 10, max_keepalive: int = 10, timeout: float = 30.0) -> HTTPConnectionPool:
        """获取连接池实例"""
        if self._pool is None:
            self._pool = HTTPConnectionPool(max_connections, max_keepalive, timeout)
        return self._pool
    
    async def close_all(self) -> None:
        """关闭所有连接池"""
        if self._pool:
            await self._pool.close_all()
            self._pool = None


# 全局连接池管理器实例
connection_pool_manager = ConnectionPoolManager()