"""测试对话跟踪器"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage

from src.services.llm.token_processing.conversation_tracker import ConversationTracker
from src.services.llm.token_processing.token_types import TokenUsage


class TestConversationTracker:
    """测试ConversationTracker类"""
    
    def test_initialization(self):
        """测试初始化"""
        tracker = ConversationTracker(max_history=100)
        
        assert tracker.max_history == 100
        assert len(tracker._messages) == 0
        assert len(tracker._sessions) == 0
        assert tracker._current_session is None
        assert tracker._stats["total_messages"] == 0
        assert tracker._stats["total_tokens"] == 0
    
    def test_start_session(self):
        """测试开始会话"""
        tracker = ConversationTracker()
        
        # 开始新会话
        session_id = tracker.start_session()
        
        assert session_id.startswith("session_")
        assert tracker._current_session is not None
        assert tracker._current_session["session_id"] == session_id
        assert "start_time" in tracker._current_session
        assert tracker._current_session["messages"] == []
        assert tracker._current_session["message_count"] == 0
    
    def test_start_session_with_id(self):
        """测试使用指定ID开始会话"""
        tracker = ConversationTracker()
        
        session_id = tracker.start_session("test_session_123")
        
        assert session_id == "test_session_123"
        assert tracker._current_session is not None
        assert tracker._current_session["session_id"] == "test_session_123"
    
    def test_end_session(self):
        """测试结束会话"""
        tracker = ConversationTracker()
        
        # 开始会话
        session_id = tracker.start_session()
        
        # 添加一些消息
        message = HumanMessage(content="Hello")
        tracker.add_message(message, 5)
        
        # 结束会话
        session_info = tracker.end_session()
        
        assert session_info is not None
        assert session_info["session_id"] == session_id
        assert "start_time" in session_info
        assert "end_time" in session_info
        assert "duration" in session_info
        assert session_info["message_count"] == 1
        assert session_info["token_usage"].total_tokens == 5
        assert tracker._current_session is None
        assert len(tracker._sessions) == 1
    
    def test_end_session_no_current(self):
        """测试结束会话（无当前会话）"""
        tracker = ConversationTracker()
        
        session_info = tracker.end_session()
        
        assert session_info is None
        assert len(tracker._sessions) == 0
    
    def test_add_message(self):
        """测试添加消息"""
        tracker = ConversationTracker()
        
        # 开始会话
        tracker.start_session()
        
        # 添加消息
        message = HumanMessage(content="Hello world")
        token_count = 5
        api_usage = TokenUsage(prompt_tokens=3, completion_tokens=2, total_tokens=5)
        
        tracker.add_message(message, token_count, api_usage)
        
        # 检查当前会话
        assert tracker._current_session is not None
        assert tracker._current_session["message_count"] == 1
        assert tracker._current_session["token_usage"].total_tokens == 5
        assert tracker._current_session["token_usage"].prompt_tokens == 3
        assert tracker._current_session["token_usage"].completion_tokens == 2
        
        # 检查全局消息历史
        assert len(tracker._messages) == 1
        assert tracker._messages[0]["message_type"] == "human"
        assert tracker._messages[0]["token_count"] == 5
        assert tracker._messages[0]["api_usage"] == api_usage
    
    def test_add_message_without_session(self):
        """测试添加消息（无会话）"""
        tracker = ConversationTracker()
        
        # 添加消息（应该自动开始会话）
        message = HumanMessage(content="Hello")
        tracker.add_message(message, 5)
        
        assert tracker._current_session is not None
        assert tracker._current_session["message_count"] == 1
        assert len(tracker._sessions) == 0  # 会话还未结束
    
    def test_add_messages(self):
        """测试批量添加消息"""
        tracker = ConversationTracker()
        
        # 开始会话
        tracker.start_session()
        
        # 添加多个消息
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]
        token_count = 10
        api_usage = TokenUsage(prompt_tokens=6, completion_tokens=4, total_tokens=10)
        
        tracker.add_messages(messages, token_count, api_usage)
        
        # 检查当前会话
        assert tracker._current_session is not None
        assert tracker._current_session["message_count"] == 2
        assert tracker._current_session["token_usage"].total_tokens == 10
        
        # 检查全局消息历史
        assert len(tracker._messages) == 2
        assert tracker._messages[0]["message_type"] == "human"
        assert tracker._messages[1]["message_type"] == "ai"
    
    def test_get_conversation_tokens(self):
        """测试获取对话token数"""
        tracker = ConversationTracker()
        
        # 无会话时
        assert tracker.get_conversation_tokens() == 0
        
        # 有会话时
        tracker.start_session()
        message = HumanMessage(content="Hello")
        tracker.add_message(message, 5)
        
        assert tracker.get_conversation_tokens() == 5
    
    def test_get_session_tokens(self):
        """测试获取会话token数"""
        tracker = ConversationTracker()
        
        # 开始并结束会话
        session_id = tracker.start_session()
        message = HumanMessage(content="Hello")
        tracker.add_message(message, 5)
        tracker.end_session()
        
        # 获取存在的会话
        tokens = tracker.get_session_tokens(session_id)
        assert tokens == 5
        
        # 获取不存在的会话
        tokens = tracker.get_session_tokens("nonexistent")
        assert tokens is None
    
    def test_get_stats(self):
        """测试获取统计信息"""
        tracker = ConversationTracker()
        
        # 添加一些会话和消息
        session_id1 = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        session_id2 = tracker.start_session()
        tracker.add_message(HumanMessage(content="How are you?"), 8)
        tracker.add_message(AIMessage(content="I'm fine!"), 7)
        tracker.end_session()
        
        # 开始当前会话
        tracker.start_session()
        tracker.add_message(HumanMessage(content="Goodbye"), 3)
        
        stats = tracker.get_stats()
        
        assert stats["total_messages"] == 4
        assert stats["total_tokens"] == 23
        assert stats["sessions_count"] == 2
        assert "current_session" in stats
        assert "message_types" in stats
        assert "session_stats" in stats
        
        # 检查当前会话统计
        current_session = stats["current_session"]
        assert current_session["message_count"] == 1
        assert current_session["token_usage"]["total_tokens"] == 3
    
    def test_get_recent_messages(self):
        """测试获取最近消息"""
        tracker = ConversationTracker()
        
        # 添加一些消息
        for i in range(15):
            message = HumanMessage(content=f"Message {i}")
            tracker.add_message(message, i + 1)
        
        # 获取最近10条消息
        recent = tracker.get_recent_messages(10)
        
        assert len(recent) == 10
        # 应该是最后10条消息（5-14）
        assert recent[0]["content_preview"] == "Message 5"
        assert recent[-1]["content_preview"] == "Message 14"
    
    def test_get_session_history(self):
        """测试获取会话历史"""
        tracker = ConversationTracker()
        
        # 创建多个会话
        session_id1 = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        session_id2 = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hi"), 3)
        tracker.end_session()
        
        # 获取所有会话
        all_sessions = tracker.get_session_history()
        assert len(all_sessions) == 2
        
        # 获取指定会话
        specific_session = tracker.get_session_history(session_id1)
        assert len(specific_session) == 1
        assert specific_session[0]["session_id"] == session_id1
    
    def test_clear_history(self):
        """测试清空历史"""
        tracker = ConversationTracker()
        
        # 添加一些数据
        tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        assert len(tracker._messages) == 1
        assert len(tracker._sessions) == 1
        assert tracker._current_session is None
        
        # 清空历史
        tracker.clear_history()
        
        assert len(tracker._messages) == 0
        assert len(tracker._sessions) == 0
        assert tracker._current_session is None
        assert tracker._stats["total_messages"] == 0
        assert tracker._stats["total_tokens"] == 0
    
    def test_clear_session_history(self):
        """测试清空会话历史"""
        tracker = ConversationTracker()
        
        # 创建多个会话
        session_id1 = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        session_id2 = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hi"), 3)
        tracker.end_session()
        
        # 清空指定会话
        tracker.clear_session_history(session_id1)
        
        assert len(tracker._sessions) == 1
        assert tracker._sessions[0]["session_id"] == session_id2
        
        # 清空当前会话
        tracker.start_session()
        tracker.add_message(HumanMessage(content="Current"), 2)
        tracker.clear_session_history()
        
        assert len(tracker._sessions) == 0
        assert tracker._current_session is None
    
    def test_export_conversation_json(self):
        """测试导出对话（JSON格式）"""
        tracker = ConversationTracker()
        
        # 添加一些数据
        session_id = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        # 导出为JSON
        json_export = tracker.export_conversation("json")
        
        assert "sessions" in json_export
        assert "current_session" in json_export
        assert "stats" in json_export
        
        # 验证JSON格式
        import json
        data = json.loads(json_export)
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["session_id"] == session_id
    
    def test_export_conversation_txt(self):
        """测试导出对话（文本格式）"""
        tracker = ConversationTracker()
        
        # 添加一些数据
        session_id = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        # 导出为文本
        txt_export = tracker.export_conversation("txt")
        
        assert f"Session: {session_id}" in txt_export
        assert "Messages: 1" in txt_export
        assert "Tokens: 5" in txt_export
        assert "[human]" in txt_export
    
    def test_export_conversation_csv(self):
        """测试导出对话（CSV格式）"""
        tracker = ConversationTracker()
        
        # 添加一些数据
        session_id = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        # 导出为CSV
        csv_export = tracker.export_conversation("csv")
        
        assert "Session ID" in csv_export
        assert "Timestamp" in csv_export
        assert "Message Type" in csv_export
        assert session_id in csv_export
        assert "5" in csv_export
    
    def test_export_conversation_invalid_format(self):
        """测试导出对话（无效格式）"""
        tracker = ConversationTracker()
        
        with pytest.raises(ValueError, match="不支持的导出格式"):
            tracker.export_conversation("invalid")
    
    def test_max_history_limit(self):
        """测试历史记录限制"""
        tracker = ConversationTracker(max_history=3)
        
        # 添加超过限制的消息
        for i in range(5):
            message = HumanMessage(content=f"Message {i}")
            tracker.add_message(message, i + 1)
        
        # 应该只保留最新的3条消息
        assert len(tracker._messages) == 3
        assert tracker._messages[0]["content_preview"] == "Message 2"
        assert tracker._messages[2]["content_preview"] == "Message 4"
    
    def test_message_content_preview(self):
        """测试消息内容预览"""
        tracker = ConversationTracker()
        
        # 添加长消息
        long_content = "This is a very long message that should be truncated when added to the conversation history"
        message = HumanMessage(content=long_content)
        tracker.add_message(message, 20)
        
        # 检查预览
        preview = tracker._messages[0]["content_preview"]
        assert len(preview) <= 103  # 100 + "..."
        assert preview.endswith("...")
    
    def test_session_duration(self):
        """测试会话持续时间"""
        tracker = ConversationTracker()
        
        # 开始会话
        start_time = datetime.now()
        tracker.start_session()
        
        # 模拟一些时间过去
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = start_time + timedelta(seconds=30)
            
            # 结束会话
            session_info = tracker.end_session()
            
            assert session_info is not None
            assert session_info["duration"] == 30.0
    
    def test_message_type_stats(self):
        """测试消息类型统计"""
        tracker = ConversationTracker()
        
        # 添加不同类型的消息
        tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.add_message(AIMessage(content="Hi"), 3)
        tracker.add_message(HumanMessage(content="How are you?"), 8)
        tracker.end_session()
        
        stats = tracker.get_stats()
        message_types = stats["message_types"]
        
        assert message_types["human"] == 2
        assert message_types["ai"] == 1
    
    def test_session_stats(self):
        """测试会话统计"""
        tracker = ConversationTracker()
        
        # 创建多个会话
        session_id1 = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hello"), 5)
        tracker.end_session()
        
        session_id2 = tracker.start_session()
        tracker.add_message(HumanMessage(content="Hi"), 15)
        tracker.end_session()
        
        stats = tracker.get_stats()
        session_stats = stats["session_stats"]
        
        assert session_stats["total_sessions"] == 2
        assert session_stats["average_tokens_per_session"] == 10.0
        assert session_stats["max_tokens_per_session"] == 15
        assert session_stats["min_tokens_per_session"] == 5