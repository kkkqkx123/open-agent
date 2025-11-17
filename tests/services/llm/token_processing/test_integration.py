"""集成测试

测试token_processing模块各组件之间的协同工作。
"""

import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.services.llm.token_processing import (
    TokenUsage,
    HybridTokenProcessor,
    ConversationTracker
)


class TestTokenProcessingIntegration:
    """测试Token处理模块的集成功能"""
    
    def test_hybrid_processor_with_conversation_tracking(self):
        """测试混合处理器与对话跟踪的集成"""
        # 创建启用对话跟踪的混合处理器
        processor = HybridTokenProcessor(
            model_name="gpt-3.5-turbo",
            provider="openai",
            prefer_api=True,
            enable_degradation=True,
            enable_conversation_tracking=True
        )
        
        # 模拟对话
        messages = [
            HumanMessage(content="Hello, how are you?"),
            AIMessage(content="I'm doing well, thank you!"),
            HumanMessage(content="What can you help me with?"),
            AIMessage(content="I can help you with many things!")
        ]
        
        # 处理消息
        total_tokens = 0
        for message in messages:
            with patch.object(processor, '_count_tokens_local') as mock_local:
                mock_local.return_value = len(message.content.split()) * 2  # 模拟本地计算
                
                tokens = processor.count_messages_tokens([message])
                assert tokens is not None
                total_tokens += tokens
        
        # 验证对话统计
        conversation_stats = processor.get_conversation_stats()
        assert conversation_stats is not None
        assert conversation_stats["total_messages"] == 4
        assert conversation_stats["total_tokens"] == total_tokens
        
        # 验证处理器统计
        stats = processor.get_stats()
        assert stats["total_requests"] == 4
        assert stats["successful_calculations"] == 4
    
    def test_hybrid_processor_degradation_scenario(self):
        """测试混合处理器的降级场景"""
        processor = HybridTokenProcessor(
            model_name="gpt-3.5-turbo",
            provider="openai",
            prefer_api=True,
            enable_degradation=True,
            enable_conversation_tracking=True
        )
        
        # 模拟API响应（token数很低）
        api_response = {
            "usage": {
                "prompt_tokens": 2,
                "completion_tokens": 1,
                "total_tokens": 3  # 远低于本地估算
            }
        }
        
        # 模拟本地计算返回较高的值
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 20  # 本地估算更高
            
            # 应该降级到本地计算
            tokens = processor.count_tokens("Test message", api_response)
            assert tokens == 20
            
            # 验证降级事件被记录
            stats = processor.get_stats()
            assert stats["degradation_events"] == 1
    
    def test_hybrid_processor_caching_scenario(self):
        """测试混合处理器的缓存场景"""
        processor = HybridTokenProcessor(
            model_name="gpt-3.5-turbo",
            provider="openai",
            prefer_api=True,
            cache_size=10
        )
        
        # 第一次计算（应该缓存结果）
        api_response = {
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 15  # 与API结果相同，不需要降级
            
            # 第一次计算
            tokens1 = processor.count_tokens("Test message", api_response)
            assert tokens1 == 15
            
            # 第二次计算（应该从缓存获取）
            tokens2 = processor.count_tokens("Test message")
            assert tokens2 == 15
            
            # 验证缓存统计
            cache_stats = processor.get_cache_stats()
            assert cache_stats["cache_hits"] == 1
            assert cache_stats["cache_size"] == 1
    
    def test_conversation_tracker_full_workflow(self):
        """测试对话跟踪器的完整工作流"""
        tracker = ConversationTracker(max_history=100)
        
        # 开始会话
        session_id = tracker.start_session("test_session")
        
        # 添加对话
        conversation = [
            (HumanMessage(content="Hello"), 5),
            (AIMessage(content="Hi there!"), 7),
            (HumanMessage(content="How are you?"), 4),
            (AIMessage(content="I'm doing well!"), 6)
        ]
        
        for message, tokens in conversation:
            tracker.add_message(message, tokens)
        
        # 结束会话
        session_info = tracker.end_session()
        
        # 验证会话信息
        assert session_info is not None
        assert session_info["session_id"] == "test_session"
        assert session_info["message_count"] == 4
        assert session_info["token_usage"]["total_tokens"] == 22
        
        # 验证统计信息
        stats = tracker.get_stats()
        assert stats["total_messages"] == 4
        assert stats["total_tokens"] == 22
        assert stats["sessions_count"] == 1
        
        # 验证消息类型统计
        message_types = stats["message_types"]
        assert message_types["human"] == 2
        assert message_types["ai"] == 2
    
    def test_conversation_tracker_export_import(self):
        """测试对话跟踪器的导出功能"""
        tracker = ConversationTracker()
        
        # 添加一些数据
        session_id = tracker.start_session("export_test")
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.add_message(AIMessage(content="Hi"), 3)
        tracker.end_session()
        
        # 测试JSON导出
        json_export = tracker.export_conversation("json")
        assert "sessions" in json_export
        assert "export_test" in json_export
        
        # 测试文本导出
        txt_export = tracker.export_conversation("txt")
        assert "export_test" in txt_export
        assert "[human]" in txt_export
        assert "[ai]" in txt_export
        
        # 测试CSV导出
        csv_export = tracker.export_conversation("csv")
        assert "Session ID" in csv_export
        assert "export_test" in csv_export
        assert "5" in csv_export
        assert "3" in csv_export
    
    def test_token_usage_serialization(self):
        """测试TokenUsage的序列化功能"""
        # 创建TokenUsage
        original = TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            source="api",
            additional_info={"model": "gpt-4", "cost": 0.01}
        )
        
        # 转换为字典
        data = original.to_dict()
        
        # 从字典恢复
        restored = TokenUsage.from_dict(data)
        
        # 验证数据一致性
        assert restored.prompt_tokens == original.prompt_tokens
        assert restored.completion_tokens == original.completion_tokens
        assert restored.total_tokens == original.total_tokens
        assert restored.source == original.source
        assert restored.additional_info == original.additional_info
    
    def test_error_handling_integration(self):
        """测试错误处理的集成"""
        processor = HybridTokenProcessor()
        
        # 模拟本地计算异常
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.side_effect = Exception("Calculation error")
            
            # 应该优雅地处理错误
            result = processor.count_tokens("test message")
            assert result is None
            
            # 验证错误统计
            stats = processor.get_stats()
            assert stats["failed_calculations"] == 1
            assert stats["successful_calculations"] == 0
    
    def test_performance_monitoring(self):
        """测试性能监控功能"""
        processor = HybridTokenProcessor(enable_conversation_tracking=True)
        
        # 执行多次计算
        with patch.object(processor, '_count_tokens_local') as mock_local:
            mock_local.return_value = 10
            
            for i in range(100):
                processor.count_tokens(f"Message {i}")
        
        # 验证性能统计
        stats = processor.get_stats()
        assert stats["total_requests"] == 100
        assert stats["successful_calculations"] == 100
        assert stats["success_rate_percent"] == 100.0
        
        # 验证对话统计
        conversation_stats = processor.get_conversation_stats()
        assert conversation_stats is not None
        assert conversation_stats["total_messages"] == 100
        assert conversation_stats["total_tokens"] == 1000
    
    def test_memory_management(self):
        """测试内存管理功能"""
        # 测试缓存内存管理
        processor = HybridTokenProcessor(cache_size=5)
        
        # 添加超过缓存大小的项目
        for i in range(10):
            with patch.object(processor, '_count_tokens_local') as mock_local:
                mock_local.return_value = i * 10
                
                api_response = {
                    "usage": {
                        "prompt_tokens": i * 5,
                        "completion_tokens": i * 5,
                        "total_tokens": i * 10
                    }
                }
                
                processor.count_tokens(f"Message {i}", api_response)
        
        # 验证缓存大小限制
        cache_stats = processor.get_cache_stats()
        assert cache_stats["cache_size"] <= 5
        
        # 测试对话历史内存管理
        tracker = ConversationTracker(max_history=3)
        
        # 添加超过限制的消息
        for i in range(5):
            message = HumanMessage(content=f"Message {i}")
            tracker.add_message(message, i + 1)
        
        # 验证历史大小限制
        assert len(tracker._messages) <= 3
    
    def test_configuration_flexibility(self):
        """测试配置灵活性"""
        # 测试不同的配置组合
        configs = [
            {
                "prefer_api": True,
                "enable_degradation": True,
                "enable_conversation_tracking": True,
                "cache_size": 100
            },
            {
                "prefer_api": False,
                "enable_degradation": False,
                "enable_conversation_tracking": False,
                "cache_size": 50
            },
            {
                "prefer_api": True,
                "enable_degradation": True,
                "enable_conversation_tracking": False,
                "cache_size": 200
            }
        ]
        
        for config in configs:
            processor = HybridTokenProcessor(**config)
            
            # 验证配置
            assert processor.prefer_api == config["prefer_api"]
            assert processor.is_degradation_enabled() == config["enable_degradation"]
            assert processor.enable_conversation_tracking == config["enable_conversation_tracking"]
            assert processor.cache_size == config["cache_size"]
            
            # 验证功能支持
            assert processor.supports_caching() is True
            assert processor.supports_degradation() is True
            assert processor.supports_conversation_tracking() is True
    
    def test_concurrent_access(self):
        """测试并发访问安全性"""
        import threading
        import time
        
        processor = HybridTokenProcessor(enable_conversation_tracking=True)
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    with patch.object(processor, '_count_tokens_local') as mock_local:
                        mock_local.return_value = worker_id * 10 + i
                        
                        result = processor.count_tokens(f"Worker {worker_id} Message {i}")
                        results.append(result)
                        time.sleep(0.001)  # 模拟处理时间
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 workers * 10 messages each
        
        # 验证统计
        stats = processor.get_stats()
        assert stats["total_requests"] == 50
        assert stats["successful_calculations"] == 50