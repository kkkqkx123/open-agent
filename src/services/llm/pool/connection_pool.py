import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, cast
from threading import Lock
from datetime import datetime, timedelta
from .interfaces import IConnectionPool
from ..core.base_factory import BaseFactory


class HTTPConnectionPool(IConnectionPool, BaseFactory):
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
        self._active_connections: Dict[str, List[aiohttp.ClientSession]] = {}  # 跟踪活跃连接
        self._stats: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "connection_reuses": 0,
            "created_connections": 0
        }
        self._lock = asyncio.Lock()  # 用于保护共享状态
    
    def create(self, max_connections: Optional[int] = None, max_keepalive: Optional[int] = None, timeout: Optional[float] = None) -> 'HTTPConnectionPool':
        """
        创建连接池实例（工厂方法）
        
        Args:
            max_connections: 最大连接数
            max_keepalive: 最大保持连接数
            timeout: 超时时间
            
        Returns:
            HTTPConnectionPool: 连接池实例
        """
        # 由于这是单例模式，直接返回自身，但更新配置
        if max_connections is not None:
            self.max_connections = max_connections
        if max_keepalive is not None:
            self.max_keepalive = max_keepalive
        if timeout is not None:
            self.timeout = timeout
        
        return self
    
    async def acquire(self, base_url: str) -> aiohttp.ClientSession:
        """获取连接"""
        async with self._lock:
            if base_url not in self._locks:
                self._locks[base_url] = asyncio.Lock()
            if base_url not in self._active_connections:
                self._active_connections[base_url] = []
        
        async with self._locks[base_url]:
            if base_url not in self._pools:
                self._pools[base_url] = []
            
            # 检查是否有可用的空闲连接
            while self._pools[base_url]:  # 使用while循环确保检查所有可能的无效连接
                connection_info = self._pools[base_url].pop()
                connection = connection_info['connection']
                
                # 检查连接是否仍然有效
                if self._is_connection_valid(connection_info):
                    self._stats["connection_reuses"] += 1
                    # 跟踪活跃连接
                    async with self._lock:
                        self._active_connections[base_url].append(connection)
                    self._stats["total_requests"] += 1
                    return connection
                else:
                    # 连接已失效，关闭它并继续检查下一个
                    try:
                        await connection.close()
                    except Exception:
                        pass  # 忽略关闭连接时的异常
            
            # 没有可用的有效连接，创建新连接
            connection = await self._create_session(base_url)
            self._stats["created_connections"] += 1
            
            # 跟踪活跃连接
            async with self._lock:
                self._active_connections[base_url].append(connection)
            
            self._stats["total_requests"] += 1
            return connection
    
    async def release(self, base_url: str, connection: aiohttp.ClientSession) -> None:
        """释放连接"""
        async with self._lock:
            if base_url not in self._locks:
                self._locks[base_url] = asyncio.Lock()
            if base_url not in self._active_connections:
                self._active_connections[base_url] = []
        
        async with self._locks[base_url]:
            if base_url not in self._pools:
                self._pools[base_url] = []
            
            # 从活跃连接列表中移除
            async with self._lock:
                if connection in self._active_connections[base_url]:
                    self._active_connections[base_url].remove(connection)
            
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
                try:
                    await connection.close()
                except Exception:
                    pass  # 忽略关闭连接时的异常
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        stats = self._stats.copy()
        active_connections = sum(len(pool) for pool in self._pools.values())
        # 加上正在使用的连接数
        active_connections += sum(len(conns) for conns in self._active_connections.values())
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
        try:
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
        except Exception:
            # 如果出现任何异常，认为连接无效
            return False
    
    async def close_all(self) -> None:
        """关闭所有连接"""
        # 关闭池中的连接
        for base_url in list(self._pools.keys()):
            while self._pools[base_url]:
                connection_info = self._pools[base_url].pop()
                try:
                    await connection_info['connection'].close()
                except Exception:
                    # 忽略关闭连接时的异常
                    pass
            self._pools[base_url].clear()
        
        # 关闭活跃连接
        for base_url in list(self._active_connections.keys()):
            while self._active_connections[base_url]:
                connection = self._active_connections[base_url].pop()
                try:
                    await connection.close()
                except Exception:
                    # 忽略关闭连接时的异常
                    pass
            self._active_connections[base_url].clear()
        
        self._pools.clear()
        self._active_connections.clear()


class ConnectionPoolManager(BaseFactory):
    """连接池管理器 - 用于管理全局连接池实例"""
    
    _pool: Optional[HTTPConnectionPool] = None
    
    def create(self, max_connections: int = 10, max_keepalive: int = 10, timeout: float = 30.0) -> HTTPConnectionPool:
        """获取连接池实例"""
        if ConnectionPoolManager._pool is None:
            pool = HTTPConnectionPool(max_connections, max_keepalive, timeout)
            ConnectionPoolManager._pool = cast(Optional[HTTPConnectionPool], pool)
        return cast(HTTPConnectionPool, ConnectionPoolManager._pool)
    
    async def close_all(self) -> None:
        """关闭所有连接池"""
        if self._pool:
            await self._pool.close_all()
            self._pool = None


# 全局连接池管理器实例
connection_pool_manager = ConnectionPoolManager()

# 注册到工厂注册表
BaseFactory.register("connection_pool", HTTPConnectionPool)
BaseFactory.register("connection_pool_manager", ConnectionPoolManager)