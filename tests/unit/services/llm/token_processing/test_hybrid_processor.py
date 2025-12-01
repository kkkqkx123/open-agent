"""测试混合Token处理器"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.services.llm.token_processing.hybrid_processor import HybridTokenProcessor
from src.services.llm.token_processing.token_types import TokenUsage


class TestHybridTokenProcessor:
    """测试HybridTokenProcessor类"""
    
    def test_initialization_default(self):
        """测试默认初始化"""
        processor = HybridTokenProcessor()
        
        assert processor.model_name == "gpt-3.5-turbo"
        assert processor.provider == "openai"
        assert processor.prefer_api is True
        assert processor.enable_conversation_tracking is False
        assert processor.supports_caching() is True
        assert processor.supports_degradation() is True
        assert processor.supports_conversation_tracking() is True
    
    def test_initialization_custom(self):
        """测试自定义初始化"""
        processor = HybridTokenProcessor(
            model_name="gpt-4",
            provider="anthropic",
            prefer_api=False,
            enable_degradation=False,
            cache_size=500,
            enable_conversation_tracking=True
        )
        
        assert processor.model_name == "gpt-4"
        assert processor.provider == "anthropic"
        assert processor.prefer_api is False
        assert processor.enable_degradation is False
        assert processor.enable_conversation_tracking is True
    
    def test_count_tokens_prefer_local(self):
        """测试优先使用本地计算"""
        processor = HybridTokenProcessor(prefer_api=False)
        
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 20
            
            result = processor.count_tokens("test text")
            
            assert result == 20
            mock_local.assert_called_once_with("test text")
    
    def test_count_tokens_with_api_response(self):
        """测试使用API响应计算"""
        processor = HybridTokenProcessor(prefer_api=True)
        
        # 模拟API响应
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 25  # 本地估算值更高
            
            result = processor.count_tokens("test text", api_response)
            
            # 应该使用API结果（不需要降级）
            assert result == 15
            mock_local.assert_called_once_with("test text")
    
    def test_count_tokens_with_degradation(self):
        """测试降级策略"""
        processor = HybridTokenProcessor(prefer_api=True, enable_degradation=True)
        
        # 模拟API响应（token数很低，需要降级）
        api_response = {
            "usage": {
                "prompt_tokens": 2,
                "completion_tokens": 1,
                "total_tokens": 3  # 远低于本地估算
            }
        }
        
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 25  # 本地估算值更高
            
            result = processor.count_tokens("test text", api_response)
            
            # 应该降级到本地计算
            assert result == 25
            mock_local.assert_called_once_with("test text")
    
    def test_count_tokens_with_cache(self):
        """测试缓存功能"""
        processor = HybridTokenProcessor(prefer_api=True)
        
        # 先添加到缓存
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        cache_key = processor._generate_cache_key("test text")
        processor._add_to_cache(cache_key, usage)
        
        with patch.object(processor, '_count_tokens_local') as mock_local:
            result = processor.count_tokens("test text")
            
            # 应该从缓存获取
            assert result == 15
            mock_local.assert_not_called()
    
    def test_count_messages_tokens(self):
        """测试消息token计算"""
        processor = HybridTokenProcessor(prefer_api=False)
        
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        
        with patch.object(processor, '_count_messages_tokens_local') as mock_local:
            mock_local.return_value = 10
            
            result = processor.count_messages_tokens(messages)
            
            assert result == 10
            mock_local.assert_called_once_with(messages)
    
    def test_parse_response(self):
        """测试解析API响应"""
        processor = HybridTokenProcessor()
        
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        usage = processor.parse_response(api_response)
        
        assert usage is not None
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15
        assert usage.source == "api"
        assert processor._last_usage == usage
    
    def test_parse_response_invalid(self):
        """测试解析无效API响应"""
        processor = HybridTokenProcessor()
        
        # 没有usage字段的响应
        api_response = {"error": "invalid response"}
        
        usage = processor.parse_response(api_response)
        
        assert usage is None
        assert processor._last_usage is None
    
    def test_update_from_api_response(self):
        """测试从API响应更新"""
        processor = HybridTokenProcessor()
        
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        result = processor.update_from_api_response(api_response, "test text")
        
        assert result is True
        assert processor._last_usage is not None
        assert processor._last_usage.total_tokens == 15
        
        # 检查缓存
        cache_key = processor._generate_cache_key("test text")
        cached_usage = processor._get_from_cache(cache_key)
        assert cached_usage is not None
        assert cached_usage.total_tokens == 15
    
    def test_update_from_api_response_no_context(self):
        """测试从API响应更新（无上下文）"""
        processor = HybridTokenProcessor()
        
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        result = processor.update_from_api_response(api_response)
        
        assert result is False  # 没有上下文，不应该缓存
    
    def test_is_supported_response(self):
        """测试检查是否支持响应"""
        processor = HybridTokenProcessor()
        
        # 支持的响应
        supported_response = {"usage": {"total_tokens": 15}}
        assert processor.is_supported_response(supported_response) is True
        
        # 不支持的响应
        unsupported_response = {"error": "invalid"}
        assert processor.is_supported_response(unsupported_response) is False
    
    def test_conversation_tracking(self):
        """测试对话跟踪功能"""
        processor = HybridTokenProcessor(enable_conversation_tracking=True)
        
        # 添加消息
        message = HumanMessage(content="Hello")
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 5
            
            processor.count_tokens("Hello")
            
            # 检查消息是否添加到历史
            assert len(processor._conversation_history) == 1
            assert processor._conversation_history[0]["type"] == "human"
            assert processor._conversation_history[0]["token_count"] == 5
    
    def test_conversation_stats(self):
        """测试对话统计"""
        processor = HybridTokenProcessor(enable_conversation_tracking=True)
        
        # 添加一些消息
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 5
            
            processor.count_tokens("Hello")
            processor.count_tokens("How are you?")
            
            stats = processor.get_conversation_stats()
            
            assert stats is not None
            assert stats["total_messages"] == 2
            assert stats["total_tokens"] == 10
            assert stats["average_tokens_per_message"] == 5.0
    
    def test_clear_conversation_history(self):
        """测试清空对话历史"""
        processor = HybridTokenProcessor(enable_conversation_tracking=True)
        
        # 添加消息
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 5
            processor.count_tokens("Hello")
            
            assert len(processor._conversation_history) == 1
            
            # 清空历史
            processor.clear_conversation_history()
            
            assert len(processor._conversation_history) == 0
            assert processor._stats["conversation_messages"] == 0
    
    def test_set_conversation_tracking_enabled(self):
        """测试设置对话跟踪"""
        processor = HybridTokenProcessor(enable_conversation_tracking=False)
        
        # 启用对话跟踪
        processor.set_conversation_tracking_enabled(True)
        assert processor.enable_conversation_tracking is True
        
        # 禁用对话跟踪
        processor.set_conversation_tracking_enabled(False)
        assert processor.enable_conversation_tracking is False
    
    def test_set_prefer_api(self):
        """测试设置优先API"""
        processor = HybridTokenProcessor()
        
        processor.set_prefer_api(False)
        assert processor.prefer_api is False
        
        processor.set_prefer_api(True)
        assert processor.prefer_api is True
    
    def test_force_local_calculation(self):
        """测试强制本地计算"""
        processor = HybridTokenProcessor()
        
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 20
            
            result = processor.force_local_calculation("test text")
            
            assert result == 20
            mock_local.assert_called_once_with("test text")
    
    def test_force_api_calculation_with_cache(self):
        """测试强制API计算（有缓存）"""
        processor = HybridTokenProcessor()
        
        # 添加缓存
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        cache_key = processor._generate_cache_key("test text")
        processor._add_to_cache(cache_key, usage)
        
        result = processor.force_api_calculation("test text")
        
        assert result == 15
    
    def test_force_api_calculation_no_cache(self):
        """测试强制API计算（无缓存）"""
        processor = HybridTokenProcessor()
        
        with patch('logging.Logger.warning') as mock_warning:
            result = processor.force_api_calculation("test text")
            
            assert result is None
            mock_warning.assert_called_once()
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        processor = HybridTokenProcessor(
            model_name="gpt-4",
            provider="openai",
            prefer_api=True,
            enable_conversation_tracking=True
        )
        
        info = processor.get_model_info()
        
        assert info["model_name"] == "gpt-4"
        assert info["provider"] == "openai"
        assert info["processor_type"] == "HybridTokenProcessor"
        assert info["prefer_api"] is True
        assert info["enable_conversation_tracking"] is True
        assert "cache_stats" in info
        assert "conversation_stats" in info
    
    def test_error_handling(self):
        """测试错误处理"""
        processor = HybridTokenProcessor()
        
        # 模拟异常
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.side_effect = Exception("Test error")
            
            result = processor.count_tokens("test text")
            
            assert result is None
            assert processor._stats["failed_calculations"] == 1
    
    def test_stats_tracking(self):
        """测试统计跟踪"""
        processor = HybridTokenProcessor()
        
        # 执行一些操作
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 10
            
            processor.count_tokens("test1")  # 成功
            processor.count_tokens("test2")  # 成功
            
        # 检查统计
        stats = processor.get_stats()
        assert stats["total_requests"] == 2
        assert stats["successful_calculations"] == 2
        assert stats["failed_calculations"] == 0
        
        # 重置统计
        processor.reset_stats()
        stats = processor.get_stats()
        assert stats["total_requests"] == 0
        assert stats["successful_calculations"] == 0