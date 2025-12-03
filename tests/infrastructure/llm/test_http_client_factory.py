"""HTTP客户端工厂测试

测试HTTP客户端工厂的创建和管理功能。
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from typing import cast

from src.infrastructure.llm.http_client.http_client_factory import (
    HttpClientFactory,
    get_http_client_factory,
    create_http_client
)
from src.infrastructure.llm.http_client.openai_http_client import OpenAIHttpClient
from src.infrastructure.llm.http_client.gemini_http_client import GeminiHttpClient
from src.infrastructure.llm.http_client.anthropic_http_client import AnthropicHttpClient
from src.interfaces.llm.http_client import ILLMHttpClient


class TestHttpClientFactory:
    """HTTP客户端工厂测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.factory = HttpClientFactory()
    
    def test_get_supported_providers(self):
        """测试获取支持的提供商列表"""
        providers = self.factory.get_supported_providers()
        
        assert isinstance(providers, list)
        assert "openai" in providers
        assert "gemini" in providers
        assert "anthropic" in providers
    
    def test_create_openai_client_with_api_key(self):
        """测试创建OpenAI客户端（使用API密钥）"""
        client = self.factory.create_client(
            provider="openai",
            model="gpt-4",
            api_key="test-api-key"
        )
        
        assert isinstance(client, OpenAIHttpClient)
        assert client.api_key == "test-api-key"
    
    def test_create_gemini_client_with_api_key(self):
        """测试创建Gemini客户端（使用API密钥）"""
        client = self.factory.create_client(
            provider="gemini",
            model="gemini-1.5-pro",
            api_key="test-gemini-key"
        )
        
        assert isinstance(client, GeminiHttpClient)
        assert client.api_key == "test-gemini-key"
    
    def test_create_anthropic_client_with_api_key(self):
        """测试创建Anthropic客户端（使用API密钥）"""
        client = self.factory.create_client(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            api_key="test-anthropic-key"
        )
        
        assert isinstance(client, AnthropicHttpClient)
        assert client.api_key == "test-anthropic-key"
    
    def test_create_client_unsupported_provider(self):
        """测试创建不支持的提供商客户端"""
        with pytest.raises(ValueError, match="不支持的提供商"):
            self.factory.create_client(provider="unsupported")
    
    def test_create_client_missing_api_key(self):
        """测试创建客户端时缺少API密钥"""
        with patch.object(self.factory.config_discovery, 'load_provider_config') as mock_load:
            mock_load.return_value = {}  # 返回空配置
            
            with pytest.raises(ValueError, match="缺少API密钥配置"):
                self.factory.create_client(provider="openai")
    
    def test_client_caching(self):
        """测试客户端缓存功能"""
        # 创建第一个客户端
        client1 = self.factory.create_client(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        # 创建相同参数的客户端，应该返回缓存实例
        client2 = self.factory.create_client(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        assert client1 is client2
    
    def test_register_provider(self):
        """测试注册新提供商"""
        # 使用一个真实的HTTP客户端实现进行测试，而不是Mock
        # 注册提供商
        self.factory.register_provider("test_provider", OpenAIHttpClient)
        
        # 验证提供商已注册
        providers = self.factory.get_supported_providers()
        assert "test_provider" in providers
    
    def test_register_provider_invalid_class(self):
        """测试注册无效的客户端类"""
        class InvalidClient:
            pass
        
        with pytest.raises(ValueError, match="客户端类必须实现ILLMHttpClient接口"):
            self.factory.register_provider("invalid", cast(type[ILLMHttpClient], InvalidClient))
    
    def test_clear_cache(self):
        """测试清除缓存"""
        # 创建客户端
        client = self.factory.create_client(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        # 验证缓存中有客户端
        assert len(self.factory._client_cache) > 0
        
        # 清除缓存
        self.factory.clear_cache()
        
        # 验证缓存已清空
        assert len(self.factory._client_cache) == 0
    
    def test_reload_configs(self):
        """测试重新加载配置"""
        with patch.object(self.factory.config_discovery, 'reload_configs') as mock_reload:
            self.factory.reload_configs()
            mock_reload.assert_called_once()


class TestGlobalFactory:
    """全局工厂测试类"""
    
    def test_get_http_client_factory(self):
        """测试获取全局工厂实例"""
        factory1 = get_http_client_factory()
        factory2 = get_http_client_factory()
        
        # 应该返回同一个实例
        assert factory1 is factory2
    
    def test_create_http_client_convenience_function(self):
        """测试便捷创建函数"""
        with patch('src.infrastructure.llm.http_client.http_client_factory.get_http_client_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_client = Mock()
            mock_factory.create_client.return_value = mock_client
            mock_get_factory.return_value = mock_factory
            
            # 调用便捷函数
            client = create_http_client(
                provider="openai",
                model="gpt-4",
                api_key="test-key"
            )
            
            # 验证调用
            mock_factory.create_client.assert_called_once_with(
                provider="openai",
                model="gpt-4",
                api_key="test-key"
            )
            assert client is mock_client


if __name__ == "__main__":
    pytest.main([__file__])