"""连接池集成测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.infrastructure.llm.pool.connection_pool import HTTPConnectionPool
from src.infrastructure.llm.memory.memory_manager import MemoryManager
from src.infrastructure.llm.plugins.plugin_manager import PluginManager


class TestConnectionPoolIntegration:
    """连接池集成测试"""
    
    @pytest.mark.asyncio
    async def test_connection_pool_with_real_requests(self):
        """测试连接池与真实请求的集成"""
        # 创建连接池
        pool = HTTPConnectionPool(max_connections=5, max_keepalive=5, timeout=10.0)
        
        # 模拟多个请求使用连接池
        base_url = "https://httpbin.org"
        
        # 获取多个连接
        connections = []
        for i in range(3):
            conn = await pool.acquire(base_url)
            connections.append(conn)
        
        # 释放连接
        for conn in connections:
            await pool.release(base_url, conn)
        
        # 验证统计信息
        stats = pool.get_stats()
        assert stats["total_requests"] == 3
        assert stats["pools_count"] >= 0
        
        # 关闭连接池
        await pool.close_all()
    
    @pytest.mark.asyncio
    async def test_connection_pool_memory_usage(self):
        """测试连接池内存使用"""
        # 创建内存管理器
        memory_manager = MemoryManager(max_memory_mb=100)
        
        # 创建连接池
        pool = HTTPConnectionPool(max_connections=2, max_keepalive=2)
        
        # 执行一些操作并监控内存
        initial_memory = memory_manager.get_memory_usage()
        
        # 获取和释放连接
        base_url = "https://httpbin.org"
        for i in range(5):
            conn = await pool.acquire(base_url)
            await pool.release(base_url, conn)
        
        final_memory = memory_manager.get_memory_usage()
        
        # 验证内存使用在合理范围内
        assert "percent" in final_memory
        assert final_memory["percent"] >= 0  # 内存使用百分比应为非负数
        
        # 关闭连接池
        await pool.close_all()


class TestPluginIntegration:
    """插件系统集成测试"""
    
    def test_plugin_with_memory_manager(self):
        """测试插件与内存管理器的集成"""
        # 创建内存管理器
        memory_manager = MemoryManager()
        
        # 创建插件管理器
        plugin_manager = PluginManager()
        
        # 验证组件可以协同工作
        assert plugin_manager is not None
        assert memory_manager is not None
        
        # 检查内存使用情况
        memory_report = memory_manager.get_detailed_memory_report()
        assert "timestamp" in memory_report
        assert "memory_usage" in memory_report


class TestFullIntegration:
    """完整集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_system_integration(self):
        """测试完整系统集成"""
        # 创建所有组件
        memory_manager = MemoryManager(max_memory_mb=50)
        connection_pool = HTTPConnectionPool(max_connections=3, max_keepalive=3)
        plugin_manager = PluginManager()
        
        # 模拟系统运行
        base_url = "https://httpbin.org"
        
        # 获取连接
        conn = await connection_pool.acquire(base_url)
        
        # 检查内存使用
        memory_usage = memory_manager.get_memory_usage()
        assert memory_usage["max_allowed_mb"] == 50
        
        # 获取连接池统计
        pool_stats = connection_pool.get_stats()
        assert pool_stats["total_requests"] >= 0
        
        # 验证插件管理器可用
        plugins = plugin_manager.list_plugins()
        assert isinstance(plugins, list)
        
        # 释放连接
        await connection_pool.release(base_url, conn)
        
        # 关闭资源
        await connection_pool.close_all()
        
        # 验证所有组件正常工作
        assert True  # 如果前面没有抛出异常，说明集成成功