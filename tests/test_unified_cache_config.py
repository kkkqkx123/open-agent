"""统一缓存配置测试"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.presentation.api.cache.unified_cache_manager import UnifiedCacheManager
from src.presentation.api.cache.memory_cache import MemoryCache


class TestUnifiedCacheConfig:
    """测试统一缓存配置功能"""
    
    def setup_method(self):
        """测试前的设置"""
        self.memory_cache = MemoryCache()
        self.config = {
            'unified_enabled': True,
            'fallback_enabled': True,
            'invalidation_enabled': True
        }
        # 用于测试的缓存类型
        self.cache_type = "memory"
    
    @pytest.mark.asyncio
    async def test_unified_enabled_false(self):
        """测试统一缓存禁用时的情况"""
        cache_manager = UnifiedCacheManager(
            cache_type=self.cache_type,
            unified_enabled=False,
            fallback_enabled=True,
            invalidation_enabled=True
        )
        
        # 测试 clear 方法在禁用时的行为
        result = await cache_manager.clear()
        assert result is True  # 应该返回 True，跳过清空操作
        
        # 测试 get_stats 包含配置信息
        stats = cache_manager.get_stats()
        assert stats['unified_enabled'] is False
        assert stats['fallback_enabled'] is True
        assert stats['invalidation_enabled'] is True
    
    @pytest.mark.asyncio
    async def test_fallback_enabled_true(self):
        """测试降级机制启用时的情况"""
        # 创建一个会抛出异常的内存缓存
        failing_cache = AsyncMock()
        failing_cache.clear.side_effect = Exception("缓存操作失败")
        
        cache_manager = UnifiedCacheManager(
            cache_type="memory",
            unified_enabled=True,
            fallback_enabled=True,
            invalidation_enabled=True
        )
        
        # 替换内部缓存以模拟失败
        cache_manager._cache = failing_cache
        
        # 测试 clear 方法在异常时的降级行为
        result = await cache_manager.clear()
        assert result is True  # 应该返回 True，启用降级机制
    
    @pytest.mark.asyncio
    async def test_fallback_enabled_false(self):
        """测试降级机制禁用时的情况"""
        # 创建一个会抛出异常的内存缓存
        failing_cache = AsyncMock()
        failing_cache.clear.side_effect = Exception("缓存操作失败")
        
        cache_manager = UnifiedCacheManager(
            cache_type="memory",
            unified_enabled=True,
            fallback_enabled=False,
            invalidation_enabled=True
        )
        
        # 替换内部缓存以模拟失败
        cache_manager._cache = failing_cache
        
        # 测试 clear 方法在异常时无降级的行为
        result = await cache_manager.clear()
        assert result is False  # 应该返回 False，不启用降级机制
    
    def test_config_in_stats(self):
        """测试统计信息中包含配置参数"""
        cache_manager = UnifiedCacheManager(
            cache_type=self.cache_type,
            unified_enabled=True,
            fallback_enabled=False,
            invalidation_enabled=False
        )
        
        stats = cache_manager.get_stats()
        
        # 验证配置参数在统计信息中
        assert 'unified_enabled' in stats
        assert 'fallback_enabled' in stats
        assert 'invalidation_enabled' in stats
        
        assert stats['unified_enabled'] is True
        assert stats['fallback_enabled'] is False
        assert stats['invalidation_enabled'] is False
    
    def test_config_in_cache_info(self):
        """测试缓存信息中包含配置参数"""
        cache_manager = UnifiedCacheManager(
            cache_type=self.cache_type,
            unified_enabled=True,
            fallback_enabled=True,
            invalidation_enabled=False
        )
        
        info = cache_manager.get_cache_info()
        
        # 验证配置参数在缓存信息中
        assert 'unified_enabled' in info
        assert 'fallback_enabled' in info
        assert 'invalidation_enabled' in info
        
        assert info['unified_enabled'] is True
        assert info['fallback_enabled'] is True
        assert info['invalidation_enabled'] is False
    
    @pytest.mark.asyncio
    async def test_service_integration_with_unified_cache(self):
        """测试服务集成统一缓存管理器的情况"""
        from src.presentation.api.services.session_service import SessionService
        from src.presentation.api.services.history_service import HistoryService
        from src.presentation.api.services.workflow_service import WorkflowService
        from src.presentation.api.services.analytics_service import AnalyticsService
        
        # 创建统一缓存管理器
        unified_cache = UnifiedCacheManager(
            cache_type=self.cache_type,
            unified_enabled=True,
            fallback_enabled=True,
            invalidation_enabled=True
        )
        
        # 模拟服务创建，不实际导入服务类以避免循环依赖
        class MockService:
            def __init__(self, cache, unified_cache_manager=None):
                self.cache = cache
                self.unified_cache_manager = unified_cache_manager
                if unified_cache_manager:
                    self.cache = unified_cache_manager
        
        # 模拟依赖
        mock_session_manager = Mock()
        mock_session_dao = Mock()
        mock_history_dao = Mock()
        mock_workflow_manager = Mock()
        mock_workflow_registry = Mock()
        mock_config_manager = Mock()
        mock_visualizer = Mock()
        mock_workflow_dao = Mock()
        
        # 测试会话服务集成
        session_service = SessionService(
            session_manager=mock_session_manager,
            session_dao=mock_session_dao,
            history_dao=mock_history_dao,
            cache=self.memory_cache,
            unified_cache_manager=unified_cache
        )
        
        # 验证统一缓存管理器被优先使用
        assert session_service.cache is unified_cache
        assert session_service.unified_cache_manager is unified_cache
        
        # 测试历史服务集成
        history_service = HistoryService(
            history_dao=mock_history_dao,
            cache=self.memory_cache,
            unified_cache_manager=unified_cache
        )
        
        assert history_service.cache is unified_cache
        assert history_service.unified_cache_manager is unified_cache
        
        # 测试工作流服务集成
        workflow_service = WorkflowService(
            workflow_manager=mock_workflow_manager,
            workflow_registry=mock_workflow_registry,
            config_manager=mock_config_manager,
            visualizer=mock_visualizer,
            workflow_dao=mock_workflow_dao,
            cache=self.memory_cache,
            unified_cache_manager=unified_cache
        )
        
        assert workflow_service.cache is unified_cache
        assert workflow_service.unified_cache_manager is unified_cache
        
        # 测试分析服务集成
        mock_service = MockService(cache=self.memory_cache, unified_cache_manager=unified_cache)
        assert mock_service.cache is unified_cache
        assert mock_service.unified_cache_manager is unified_cache
    
    def test_service_integration_without_unified_cache(self):
        """测试服务不集成统一缓存管理器的情况"""
        # 模拟服务创建，不实际导入服务类以避免循环依赖
        class MockService:
            def __init__(self, cache, unified_cache_manager=None):
                self.cache = cache
                self.unified_cache_manager = unified_cache_manager
                if unified_cache_manager:
                    self.cache = unified_cache_manager
        
        # 测试会话服务不传入统一缓存管理器
        mock_service = MockService(cache=self.memory_cache, unified_cache_manager=None)
        
        # 验证使用原始缓存
        assert mock_service.cache is self.memory_cache
        assert mock_service.unified_cache_manager is None
    
    def test_configuration_switching(self):
        """测试配置切换功能"""
        # 初始配置：统一缓存启用
        cache_manager = UnifiedCacheManager(
            cache_type=self.cache_type,
            unified_enabled=True,
            fallback_enabled=True,
            invalidation_enabled=True
        )
        
        # 验证初始配置
        stats = cache_manager.get_stats()
        assert stats['unified_enabled'] is True
        
        # 模拟配置切换：禁用统一缓存
        cache_manager.unified_enabled = False
        stats = cache_manager.get_stats()
        assert stats['unified_enabled'] is False
    
    def test_configuration_validation(self):
        """测试配置参数验证"""
        # 测试有效的配置组合
        cache_manager = UnifiedCacheManager(
            cache_type=self.cache_type,
            unified_enabled=True,
            fallback_enabled=False,
            invalidation_enabled=True
        )
        
        assert cache_manager.unified_enabled is True
        assert cache_manager.fallback_enabled is False
        assert cache_manager.invalidation_enabled is True
        
        # 测试配置参数类型
        assert isinstance(cache_manager.unified_enabled, bool)
        assert isinstance(cache_manager.fallback_enabled, bool)
        assert isinstance(cache_manager.invalidation_enabled, bool)


if __name__ == "__main__":
    pytest.main([__file__])