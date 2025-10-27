"""适配器工厂测试用例"""

import pytest

from src.infrastructure.graph.adapters.factory import (
    AdapterFactory, 
    get_adapter_factory,
    get_state_adapter,
    get_message_adapter,
    create_state_adapter,
    create_message_adapter
)
from src.infrastructure.graph.adapters.state_adapter import StateAdapter
from src.infrastructure.graph.adapters.message_adapter import MessageAdapter


class TestAdapterFactory:
    """适配器工厂测试类"""
    
    def test_get_state_adapter_singleton(self):
        """测试获取状态适配器（单例模式）"""
        factory = AdapterFactory()
        
        # 第一次获取
        adapter1 = factory.get_state_adapter()
        assert isinstance(adapter1, StateAdapter)
        
        # 第二次获取应该是同一个实例
        adapter2 = factory.get_state_adapter()
        assert adapter1 is adapter2
    
    def test_get_message_adapter_singleton(self):
        """测试获取消息适配器（单例模式）"""
        factory = AdapterFactory()
        
        # 第一次获取
        adapter1 = factory.get_message_adapter()
        assert isinstance(adapter1, MessageAdapter)
        
        # 第二次获取应该是同一个实例
        adapter2 = factory.get_message_adapter()
        assert adapter1 is adapter2
    
    def test_create_state_adapter_new_instance(self):
        """测试创建新的状态适配器实例"""
        factory = AdapterFactory()
        
        # 获取单例实例
        singleton_adapter = factory.get_state_adapter()
        
        # 创建新实例
        new_adapter = factory.create_state_adapter()
        
        # 验证是新实例
        assert isinstance(new_adapter, StateAdapter)
        assert new_adapter is not singleton_adapter
    
    def test_create_message_adapter_new_instance(self):
        """测试创建新的消息适配器实例"""
        factory = AdapterFactory()
        
        # 获取单例实例
        singleton_adapter = factory.get_message_adapter()
        
        # 创建新实例
        new_adapter = factory.create_message_adapter()
        
        # 验证是新实例
        assert isinstance(new_adapter, MessageAdapter)
        assert new_adapter is not singleton_adapter
    
    def test_global_factory_singleton(self):
        """测试全局工厂单例模式"""
        # 第一次获取全局工厂
        factory1 = get_adapter_factory()
        assert isinstance(factory1, AdapterFactory)
        
        # 第二次获取应该是同一个实例
        factory2 = get_adapter_factory()
        assert factory1 is factory2
    
    def test_global_state_adapter(self):
        """测试全局状态适配器"""
        # 获取全局状态适配器
        adapter1 = get_state_adapter()
        assert isinstance(adapter1, StateAdapter)
        
        # 再次获取应该是同一个实例
        adapter2 = get_state_adapter()
        assert adapter1 is adapter2
    
    def test_global_message_adapter(self):
        """测试全局消息适配器"""
        # 获取全局消息适配器
        adapter1 = get_message_adapter()
        assert isinstance(adapter1, MessageAdapter)
        
        # 再次获取应该是同一个实例
        adapter2 = get_message_adapter()
        assert adapter1 is adapter2
    
    def test_create_global_state_adapter(self):
        """测试创建全局状态适配器新实例"""
        # 获取单例实例
        singleton_adapter = get_state_adapter()
        
        # 创建新实例
        new_adapter = create_state_adapter()
        
        # 验证是新实例
        assert isinstance(new_adapter, StateAdapter)
        assert new_adapter is not singleton_adapter
    
    def test_create_global_message_adapter(self):
        """测试创建全局消息适配器新实例"""
        # 获取单例实例
        singleton_adapter = get_message_adapter()
        
        # 创建新实例
        new_adapter = create_message_adapter()
        
        # 验证是新实例
        assert isinstance(new_adapter, MessageAdapter)
        assert new_adapter is not singleton_adapter
    
    def test_factory_independence(self):
        """测试工厂实例独立性"""
        # 创建两个不同的工厂
        factory1 = AdapterFactory()
        factory2 = AdapterFactory()
        
        # 从不同工厂获取的适配器应该是不同的实例
        adapter1 = factory1.get_state_adapter()
        adapter2 = factory2.get_state_adapter()
        
        assert adapter1 is not adapter2
        
        # 消息适配器同理
        msg_adapter1 = factory1.get_message_adapter()
        msg_adapter2 = factory2.get_message_adapter()
        
        assert msg_adapter1 is not msg_adapter2
    
    def test_adapter_functionality(self):
        """测试适配器功能完整性"""
        factory = AdapterFactory()
        
        # 获取状态适配器并测试基本功能
        state_adapter = factory.get_state_adapter()
        assert hasattr(state_adapter, 'to_graph_state')
        assert hasattr(state_adapter, 'from_graph_state')
        
        # 获取消息适配器并测试基本功能
        message_adapter = factory.get_message_adapter()
        assert hasattr(message_adapter, 'to_graph_message')
        assert hasattr(message_adapter, 'from_graph_message')
        assert hasattr(message_adapter, 'to_graph_messages')
        assert hasattr(message_adapter, 'from_graph_messages')


if __name__ == "__main__":
    pytest.main([__file__])