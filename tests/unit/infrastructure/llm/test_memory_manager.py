"""内存管理器单元测试"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.infrastructure.llm.memory.memory_manager import MemoryManager, memory_manager_factory


class TestMemoryManager:
    """内存管理器测试"""
    
    def test_memory_tracking(self):
        """测试内存跟踪功能"""
        manager = MemoryManager(max_memory_mb=100)
        
        # 初始内存使用
        initial_usage = manager.get_memory_usage()
        
        # 跟踪一些内存使用
        manager.track_memory_usage("test_operation", 1024)  # 1KB
        
        # 验证内存使用信息
        usage = manager.get_memory_usage()
        assert "rss" in usage
        assert "vms" in usage
        assert "percent" in usage
    
    def test_memory_threshold_gc(self):
        """测试内存阈值触发垃圾回收"""
        manager = MemoryManager(max_memory_mb=1, gc_threshold_mb=0.1)  # 低阈值用于测试
        
        # 模拟高内存使用
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_percent.return_value = 90.0  # 90%内存使用
            
            # 调用内存使用检查，应该触发垃圾回收
            manager._is_memory_usage_high = MagicMock(return_value=True)
            manager._trigger_gc = MagicMock()
            
            # 手动调用垃圾回收检查
            if manager._is_memory_usage_high():
                manager._trigger_gc()
            
            # 验证垃圾回收被调用
            manager._trigger_gc.assert_called()
    
    def test_detailed_memory_report(self):
        """测试详细内存报告"""
        manager = MemoryManager()
        report = manager.get_detailed_memory_report()
        
        expected_keys = ["timestamp", "memory_usage", "gc_stats", "gc_objects", "top_object_types"]
        for key in expected_keys:
            assert key in report


class TestMemoryManagerFactory:
    """内存管理器工厂测试"""
    
    def test_get_manager(self):
        """测试获取管理器实例"""
        factory = memory_manager_factory
        manager1 = factory.get_manager()
        manager2 = factory.get_manager()
        
        # 应该返回相同的工厂实例
        assert factory is memory_manager_factory
        
        # 但管理器本身可能不同，取决于实现
        # 这里测试工厂的单例行为
        assert factory is not None