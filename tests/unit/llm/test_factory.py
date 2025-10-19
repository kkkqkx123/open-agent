"""LLM工厂单元测试"""

import pytest
from unittest.mock import Mock, patch

from src.llm.factory import LLMFactory, get_global_factory, set_global_factory, create_client, get_cached_client
from src.llm.config import LLMModuleConfig, LLMClientConfig
from src.llm.exceptions import LLMClientCreationError, UnsupportedModelTypeError


class TestLLMFactory:
    """LLM工厂测试类"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return LLMModuleConfig(
            cache_enabled=True,
            cache_max_size=10
        )
    
    @pytest.fixture
    def factory(self, config):
        """创建工厂实例"""
        return LLMFactory(config)
    
    def test_init(self, config):
        """测试初始化"""
        factory = LLMFactory(config)
        
        assert factory.config == config
        assert factory._client_cache == {}
        assert factory._client_types != {}
        assert "mock" in factory._client_types  # Mock客户端应该被注册
    
    def test_register_client_type(self, factory):
        """测试注册客户端类型"""
        # 创建模拟客户端类
        mock_client_class = Mock()
        
        # 注册客户端类型
        factory.register_client_type("test_type", mock_client_class)
        
        # 验证注册成功
        assert "test_type" in factory._client_types
        assert factory._client_types["test_type"] == mock_client_class
    
    def test_create_client_with_dict(self, factory):
        """测试使用字典创建客户端"""
        # 创建配置字典
        config_dict = {
            "model_type": "mock",
            "model_name": "test-model",
            "response_delay": 0.0,
            "error_rate": 0.0
        }
        
        # 创建客户端
        with patch('src.llm.clients.mock_client.MockLLMClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            client = factory.create_client(config_dict)
            
            # 验证客户端被创建
            mock_client.assert_called_once()
            assert client == mock_instance
    
    def test_create_client_with_config(self, factory):
        """测试使用配置对象创建客户端"""
        # 创建配置对象
        client_config = LLMClientConfig(
            model_type="mock",
            model_name="test-model"
        )
        
        # 创建客户端
        with patch('src.llm.clients.mock_client.MockLLMClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            client = factory.create_client(client_config)
            
            # 验证客户端被创建
            mock_client.assert_called_once()
            assert client == mock_instance
    
    def test_create_client_unsupported_type(self, factory):
        """测试创建不支持的客户端类型"""
        # 创建不支持的配置
        config_dict = {
            "model_type": "unsupported_type",
            "model_name": "test-model"
        }
        
        # 应该抛出错误
        with pytest.raises(UnsupportedModelTypeError):
            factory.create_client(config_dict)
    
    def test_create_client_creation_error(self, factory):
        """测试客户端创建错误"""
        # 创建配置
        config_dict = {
            "model_type": "mock",
            "model_name": "test-model"
        }
        
        # 模拟创建错误
        with patch('src.llm.clients.mock_client.MockLLMClient', side_effect=Exception("创建失败")):
            # 应该抛出错误
            with pytest.raises(LLMClientCreationError):
                factory.create_client(config_dict)
    
    def test_create_client_from_config(self, factory):
        """测试从配置创建客户端"""
        # 创建配置对象
        client_config = LLMClientConfig(
            model_type="mock",
            model_name="test-model"
        )
        
        # 创建客户端
        with patch('src.llm.clients.mock_client.MockLLMClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            client = factory.create_client_from_config(client_config)
            
            # 验证客户端被创建
            mock_client.assert_called_once_with(client_config)
            assert client == mock_instance
    
    def test_get_cached_client(self, factory):
        """测试获取缓存的客户端"""
        # 创建模拟客户端
        mock_client = Mock()
        
        # 缓存客户端
        factory._client_cache["test-model"] = mock_client
        
        # 获取缓存的客户端
        client = factory.get_cached_client("test-model")
        
        # 验证返回正确的客户端
        assert client == mock_client
        
        # 测试不存在的缓存
        client = factory.get_cached_client("non-existent")
        assert client is None
    
    def test_cache_client(self, factory):
        """测试缓存客户端"""
        # 创建模拟客户端
        mock_client = Mock()
        
        # 缓存客户端
        factory.cache_client("test-model", mock_client)
        
        # 验证客户端被缓存
        assert factory.get_cached_client("test-model") == mock_client
    
    def test_cache_client_size_limit(self, config):
        """测试缓存大小限制"""
        # 创建小缓存限制的工厂
        config.cache_max_size = 2
        factory = LLMFactory(config)
        
        # 创建模拟客户端
        mock_client1 = Mock()
        mock_client2 = Mock()
        mock_client3 = Mock()
        
        # 缓存客户端
        factory.cache_client("model1", mock_client1)
        factory.cache_client("model2", mock_client2)
        
        # 验证两个客户端都被缓存
        assert factory.get_cached_client("model1") == mock_client1
        assert factory.get_cached_client("model2") == mock_client2
        
        # 添加第三个客户端，应该移除最旧的
        factory.cache_client("model3", mock_client3)
        
        # 验证最旧的被移除
        assert factory.get_cached_client("model1") is None
        assert factory.get_cached_client("model2") == mock_client2
        assert factory.get_cached_client("model3") == mock_client3
    
    def test_clear_cache(self, factory):
        """测试清除缓存"""
        # 创建模拟客户端
        mock_client = Mock()
        
        # 缓存客户端
        factory.cache_client("test-model", mock_client)
        
        # 验证客户端被缓存
        assert factory.get_cached_client("test-model") == mock_client
        
        # 清除缓存
        factory.clear_cache()
        
        # 验证缓存被清除
        assert factory.get_cached_client("test-model") is None
    
    def test_get_or_create_client_new(self, factory):
        """测试获取或创建新客户端"""
        # 创建配置
        config_dict = {
            "model_type": "mock",
            "model_name": "test-model"
        }
        
        # 创建客户端
        with patch('src.llm.clients.mock_client.MockLLMClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            
            client = factory.get_or_create_client("test-model", config_dict)
            
            # 验证客户端被创建
            mock_client.assert_called_once()
            assert client == mock_instance
            
            # 验证客户端被缓存
            assert factory.get_cached_client("test-model") == mock_instance
    
    def test_get_or_create_client_cached(self, factory):
        """测试获取已缓存的客户端"""
        # 创建模拟客户端
        mock_client = Mock()
        
        # 缓存客户端
        factory.cache_client("test-model", mock_client)
        
        # 获取客户端
        client = factory.get_or_create_client("test-model", {})
        
        # 验证返回缓存的客户端
        assert client == mock_client
    
    def test_list_supported_types(self, factory):
        """测试列出支持的模型类型"""
        # 获取支持的类型
        types = factory.list_supported_types()
        
        # 验证包含基本类型
        assert "mock" in types
        assert isinstance(types, list)
    
    def test_get_cache_info(self, factory):
        """测试获取缓存信息"""
        # 创建模拟客户端
        mock_client = Mock()
        
        # 缓存客户端
        factory.cache_client("test-model", mock_client)
        
        # 获取缓存信息
        info = factory.get_cache_info()
        
        # 验证信息
        assert info["cache_size"] == 1
        assert info["max_cache_size"] == factory.config.cache_max_size
        assert "test-model" in info["cached_models"]
        assert info["cache_enabled"] == factory.config.cache_enabled
    
    def test_global_factory(self):
        """测试全局工厂"""
        # 获取全局工厂
        factory1 = get_global_factory()
        factory2 = get_global_factory()
        
        # 验证是同一个实例
        assert factory1 is factory2
        
        # 设置新的全局工厂
        new_factory = LLMFactory()
        set_global_factory(new_factory)
        
        # 验证全局工厂已更新
        assert get_global_factory() is new_factory
    
    def test_create_client_with_global_factory(self):
        """测试使用全局工厂创建客户端"""
        # 创建配置字典
        config_dict = {
            "model_type": "mock",
            "model_name": "test-model"
        }
        
        # 创建客户端
        with patch('src.llm.factory.get_global_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_client = Mock()
            mock_factory.create_client.return_value = mock_client
            mock_get_factory.return_value = mock_factory
            
            client = create_client(config_dict)
            
            # 验证调用
            mock_factory.create_client.assert_called_once_with(config_dict)
            assert client == mock_client
    
    def test_get_cached_client_with_global_factory(self):
        """测试使用全局工厂获取缓存的客户端"""
        # 使用全局工厂
        with patch('src.llm.factory.get_global_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_client = Mock()
            mock_factory.get_cached_client.return_value = mock_client
            mock_get_factory.return_value = mock_factory
            
            client = get_cached_client("test-model")
            
            # 验证调用
            mock_factory.get_cached_client.assert_called_once_with("test-model")
            assert client == mock_client