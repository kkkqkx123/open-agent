"""History模块TUI集成测试"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

from src.application.history.manager import HistoryManager
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.application.history.adapters.tui_adapter import TUIHistoryAdapter
from src.presentation.tui.state_manager import StateManager
from src.domain.history.models import MessageRecord, ToolCallRecord, MessageType, HistoryQuery, HistoryResult


class TestTUIIntegration:
    """TUI与History模块集成测试"""

    def test_end_to_end_message_recording(self) -> None:
        """端到端消息记录测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 设置存储
            storage = FileHistoryStorage(Path(temp_dir))
            manager = HistoryManager(storage)
            
            # 设置状态管理器
            state_manager = StateManager()
            state_manager.session_id = "test-session"
            
            # 设置适配器
            adapter = TUIHistoryAdapter(manager, state_manager)
            
            # 模拟用户消息
            adapter.on_user_message("你好")
            
            # 模拟助手回复
            adapter.on_assistant_message("你好！我是AI助手")
            
            # 模拟工具调用
            adapter.on_tool_call(
                "search_tool", 
                {"query": "Python测试"}, 
                {"results": ["结果1", "结果2"]}
            )
            
            # 验证文件被创建
            with pytest.MonkeyPatch().context() as m:
                mock_datetime = Mock()
                mock_datetime.now.return_value.strftime.return_value = "202310"
                m.setattr('datetime.datetime', mock_datetime)
                
                session_file = storage._get_session_file("test-session")
                assert session_file.exists()
                
                # 验证文件内容
                with open(session_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    assert len(lines) == 3
                    
                    # 验证用户消息
                    user_data = json.loads(lines[0].strip())
                    assert user_data['message_type'] == 'user'
                    assert user_data['content'] == "你好"
                    
                    # 验证助手消息
                    assistant_data = json.loads(lines[1].strip())
                    assert assistant_data['message_type'] == 'assistant'
                    assert assistant_data['content'] == "你好！我是AI助手"
                    
                    # 验证工具调用
                    tool_data = json.loads(lines[2].strip())
                    assert tool_data['tool_name'] == "search_tool"
                    assert tool_data['tool_input']['query'] == "Python测试"
                    assert tool_data['tool_output']['results'] == ["结果1", "结果2"]

    def test_multiple_sessions_isolation(self) -> None:
        """多会话隔离测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileHistoryStorage(Path(temp_dir))
            manager = HistoryManager(storage)
            
            # 创建第一个会话
            state_manager1 = StateManager()
            state_manager1.session_id = "session-1"
            adapter1 = TUIHistoryAdapter(manager, state_manager1)
            
            # 创建第二个会话
            state_manager2 = StateManager()
            state_manager2.session_id = "session-2"
            adapter2 = TUIHistoryAdapter(manager, state_manager2)
            
            # 在不同会话中记录消息
            adapter1.on_user_message("会话1的消息")
            adapter2.on_user_message("会话2的消息")
            
            # 验证会话隔离
            with pytest.MonkeyPatch().context() as m:
                mock_datetime = Mock()
                mock_datetime.now.return_value.strftime.return_value = "202310"
                m.setattr('datetime.datetime', mock_datetime)
                
                session1_file = storage._get_session_file("session-1")
                session2_file = storage._get_session_file("session-2")
                
                # 验证两个文件都存在且不同
                assert session1_file.exists()
                assert session2_file.exists()
                assert session1_file != session2_file
                
                # 验证文件内容
                with open(session1_file, 'r', encoding='utf-8') as f:
                    content1 = f.read()
                    assert "会话1的消息" in content1
                    assert "会话2的消息" not in content1
                
                with open(session2_file, 'r', encoding='utf-8') as f:
                    content2 = f.read()
                    assert "会话2的消息" in content2
                    assert "会话1的消息" not in content2

    def test_no_session_id_behavior(self) -> None:
        """无会话ID行为测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileHistoryStorage(Path(temp_dir))
            manager = HistoryManager(storage)
            
            # 创建无会话ID的状态管理器
            state_manager = StateManager()
            state_manager.session_id = None
            adapter = TUIHistoryAdapter(manager, state_manager)
            
            # 尝试记录消息
            adapter.on_user_message("这条消息不应该被记录")
            adapter.on_assistant_message("这条回复也不应该被记录")
            adapter.on_tool_call("test_tool", {"param": "value"})
            
            # 验证没有创建任何文件
            with pytest.MonkeyPatch().context() as m:
                mock_datetime = Mock()
                mock_datetime.now.return_value.strftime.return_value = "202310"
                m.setattr('datetime.datetime', mock_datetime)
                
                # 尝试获取会话文件路径
                session_file = storage._get_session_file(None)
                
                # 验证文件不存在
                assert not session_file.exists()

    def test_complex_workflow_simulation(self) -> None:
        """复杂工作流模拟测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileHistoryStorage(Path(temp_dir))
            manager = HistoryManager(storage)
            
            state_manager = StateManager()
            state_manager.session_id = "complex-session"
            adapter = TUIHistoryAdapter(manager, state_manager)
            
            # 模拟复杂对话流程
            adapter.on_user_message("帮我分析一下这段代码的性能")
            adapter.on_assistant_message("我来帮你分析代码性能。首先让我检查代码结构...")
            adapter.on_tool_call("code_analyzer", {"code": "def test(): pass"}, {"complexity": "O(1)"})
            adapter.on_assistant_message("根据分析结果，这段代码的时间复杂度是O(1)，性能很好。")
            adapter.on_user_message("能帮我优化一下吗？")
            adapter.on_assistant_message("当然可以。让我尝试几种优化方案...")
            adapter.on_tool_call("optimizer", {"code": "def test(): pass", "target": "speed"}, {"optimized_code": "def optimized_test(): pass"})
            adapter.on_assistant_message("这是优化后的代码，性能提升了20%。")
            
            # 验证所有记录都被保存
            with pytest.MonkeyPatch().context() as m:
                mock_datetime = Mock()
                mock_datetime.now.return_value.strftime.return_value = "202310"
                m.setattr('datetime.datetime', mock_datetime)
                
                session_file = storage._get_session_file("complex-session")
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 应该有8条记录（3条用户消息，4条助手消息，2条工具调用）
                    assert len(lines) == 8
                    
                    # 验证消息类型交替
                    records = [json.loads(line.strip()) for line in lines]
                    message_types = [r.get('message_type') or r.get('record_type') for r in records]
                    expected_types = ['user', 'assistant', 'tool_call', 'assistant', 'user', 'assistant', 'tool_call', 'assistant']
                    assert message_types == expected_types

    def test_error_handling_integration(self) -> None:
        """错误处理集成测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建只读目录来模拟写入错误
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # 只读权限
            
            try:
                storage = FileHistoryStorage(readonly_dir)
                manager = HistoryManager(storage)
                
                state_manager = StateManager()
                state_manager.session_id = "error-session"
                adapter = TUIHistoryAdapter(manager, state_manager)
                
                # 尝试记录消息应该失败但不崩溃
                adapter.on_user_message("这条消息会失败")
                
                # 验证没有抛出异常
                # 注意：实际的错误处理取决于FileHistoryStorage的实现
                # 这里只是验证集成不会导致程序崩溃
                
            finally:
                # 恢复权限以便清理
                readonly_dir.chmod(0o755)

    def test_unicode_and_special_characters(self) -> None:
        """Unicode和特殊字符集成测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileHistoryStorage(Path(temp_dir))
            manager = HistoryManager(storage)
            
            state_manager = StateManager()
            state_manager.session_id = "unicode-session"
            adapter = TUIHistoryAdapter(manager, state_manager)
            
            # 测试各种特殊字符
            unicode_messages = [
                "中文测试消息",
                "English message with émojis 🚀🎉",
                "Special chars: \n\t\"'\\",
                "Math: ∑∏∫∆∇∂",
                "RTL: العربية",
                "Mixed: 中文English🌟العربية"
            ]
            
            for msg in unicode_messages:
                adapter.on_user_message(msg)
                adapter.on_assistant_message(f"回复: {msg}")
            
            # 验证所有Unicode字符都被正确保存
            with pytest.MonkeyPatch().context() as m:
                mock_datetime = Mock()
                mock_datetime.now.return_value.strftime.return_value = "202310"
                m.setattr('datetime.datetime', mock_datetime)
                
                session_file = storage._get_session_file("unicode-session")
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # 验证所有消息都被保存
                    assert len(lines) == len(unicode_messages) * 2  # 每条消息都有用户和助手回复
                    
                    # 解析每条记录并验证内容
                    for i, msg in enumerate(unicode_messages):
                        # 用户消息
                        user_record = json.loads(lines[i * 2].strip())
                        assert user_record['message_type'] == 'user'
                        assert user_record['content'] == msg
                        
                        # 助手回复
                        assistant_record = json.loads(lines[i * 2 + 1].strip())
                        assert assistant_record['message_type'] == 'assistant'
                        assert assistant_record['content'] == f"回复: {msg}"

    def test_large_data_handling(self) -> None:
        """大数据处理集成测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileHistoryStorage(Path(temp_dir))
            manager = HistoryManager(storage)
            
            state_manager = StateManager()
            state_manager.session_id = "large-data-session"
            adapter = TUIHistoryAdapter(manager, state_manager)
            
            # 创建大型数据
            large_text = "A" * 10000  # 10KB文本
            large_tool_input = {"data": list(range(1000))}
            large_tool_output = {"results": [{"id": i, "text": "B" * 100} for i in range(100)]}
            
            # 记录大型数据
            adapter.on_user_message(large_text)
            adapter.on_tool_call("large_tool", large_tool_input, large_tool_output)
            
            # 验证大型数据被正确保存
            with pytest.MonkeyPatch().context() as m:
                mock_datetime = Mock()
                mock_datetime.now.return_value.strftime.return_value = "202310"
                m.setattr('datetime.datetime', mock_datetime)
                
                session_file = storage._get_session_file("large-data-session")
                
                # 验证文件大小
                assert session_file.stat().st_size > 20000  # 应该大于20KB
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    assert len(lines) == 2
                    
                    # 验证大型文本
                    user_data = json.loads(lines[0].strip())
                    assert user_data['content'] == large_text
                    
                    # 验证大型工具数据
                    tool_data = json.loads(lines[1].strip())
                    assert tool_data['tool_input'] == large_tool_input
                    assert tool_data['tool_output'] == large_tool_output

    def test_concurrent_access_simulation(self) -> None:
        """并发访问模拟测试"""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileHistoryStorage(Path(temp_dir))
            manager = HistoryManager(storage)
            
            # 创建多个状态管理器和适配器模拟并发
            def worker_session(session_id: str, message_count: int) -> None:
                state_manager = StateManager()
                state_manager.session_id = session_id
                adapter = TUIHistoryAdapter(manager, state_manager)
                
                for i in range(message_count):
                    adapter.on_user_message(f"消息 {i} from {session_id}")
                    time.sleep(0.001)  # 短暂延迟模拟真实场景
            
            # 创建多个线程
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker_session, args=(f"session-{i}", 5))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 验证所有会话的数据都被正确保存
            with pytest.MonkeyPatch().context() as m:
                mock_datetime = Mock()
                mock_datetime.now.return_value.strftime.return_value = "202310"
                m.setattr('datetime.datetime', mock_datetime)
                
                for i in range(3):
                    session_file = storage._get_session_file(f"session-{i}")
                    assert session_file.exists()
                    
                    with open(session_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        assert len(lines) == 5  # 每个会话5条消息