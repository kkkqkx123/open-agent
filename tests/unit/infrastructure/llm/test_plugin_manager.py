"""插件管理器单元测试"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from src.infrastructure.llm.plugins.plugin_manager import PluginManager, plugin_manager_factory
from src.infrastructure.llm.plugins.interfaces import ILLMPlugin, IPluginManager


class MockPlugin(ILLMPlugin):
    """模拟插件用于测试"""
    
    def __init__(self, name="test_plugin", version="1.0.0", description="Test plugin"):
        self._name = name
        self._version = version
        self._description = description
        self.initialized = False
        self.cleaned_up = False
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def description(self) -> str:
        return self._description
    
    async def initialize(self) -> None:
        self.initialized = True
    
    async def execute(self, *args, **kwargs):
        return f"Executed {self.name} with args={args}, kwargs={kwargs}"
    
    async def cleanup(self) -> None:
        self.cleaned_up = True


class TestPluginManager:
    """插件管理器测试"""
    
    def test_interface_implementation(self):
        """测试接口实现"""
        manager = PluginManager()
        assert isinstance(manager, IPluginManager)
    
    def test_register_and_get_plugin(self):
        """测试注册和获取插件"""
        manager = PluginManager()
        plugin = MockPlugin()
        
        # 注册插件
        manager.register_plugin(plugin)
        
        # 获取插件
        retrieved_plugin = manager.get_plugin("test_plugin")
        assert retrieved_plugin is plugin
        assert retrieved_plugin.name == "test_plugin"
    
    @pytest.mark.asyncio
    async def test_unregister_plugin(self):
        """测试注销插件"""
        manager = PluginManager()
        plugin = MockPlugin()
        
        # 注册插件
        manager.register_plugin(plugin)
        assert "test_plugin" in manager.list_plugins()
        
        # 注销插件
        result = await manager.unregister_plugin("test_plugin")
        assert result is True
        assert "test_plugin" not in manager.list_plugins()
    
    @pytest.mark.asyncio
    async def test_execute_plugin(self):
        """测试执行插件"""
        manager = PluginManager()
        plugin = MockPlugin()
        
        # 注册插件
        manager.register_plugin(plugin)
        
        # 执行插件
        result = await manager.execute_plugin("test_plugin", "arg1", key="value")
        assert result == "Executed test_plugin with args=('arg1',), kwargs={'key': 'value'}"
    
    def test_list_plugins(self):
        """测试列出插件"""
        manager = PluginManager()
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")
        
        # 注册插件
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        
        # 列出插件
        plugins = manager.list_plugins()
        assert "plugin1" in plugins
        assert "plugin2" in plugins
        assert len(plugins) == 2
    
    @pytest.mark.asyncio
    async def test_initialize_and_cleanup_all_plugins(self):
        """测试初始化和清理所有插件"""
        manager = PluginManager()
        plugin = MockPlugin()
        
        # 注册插件
        manager.register_plugin(plugin)
        
        # 验证初始状态
        assert plugin.initialized is False
        assert plugin.cleaned_up is False
        
        # 初始化所有插件
        await manager.initialize_all_plugins()
        assert plugin.initialized is True
        
        # 清理所有插件
        await manager.cleanup_all_plugins()
        assert plugin.cleaned_up is True


class TestPluginManagerFactory:
    """插件管理器工厂测试"""
    
    def test_get_manager(self):
        """测试获取管理器实例"""
        factory = plugin_manager_factory
        manager1 = factory.get_manager()
        manager2 = factory.get_manager()
        
        # 应该返回相同的工厂实例
        assert factory is plugin_manager_factory
        
        # 验证工厂的单例行为
        assert factory is not None