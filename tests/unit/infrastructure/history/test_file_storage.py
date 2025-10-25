"""FileHistoryStorage单元测试"""

import pytest
import json
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from typing import Union, List
from unittest.mock import patch, mock_open

from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.domain.history.models import MessageRecord, ToolCallRecord, MessageType


class TestFileHistoryStorage:
    """FileHistoryStorage测试"""

    def test_init_creates_directory(self) -> None:
        """测试初始化时创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "history"
            storage = FileHistoryStorage(base_path)
            
            assert storage.base_path == base_path
            assert base_path.exists()
            assert base_path.is_dir()

    def test_get_session_file_path(self) -> None:
        """测试获取会话文件路径"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            # 模拟当前日期为2023年10月
            with patch('src.infrastructure.history.storage.file_storage.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202310"
                
                session_file = storage._get_session_file("test-session")
                
                expected_path = base_path / "sessions" / "202310" / "test-session.jsonl"
                assert session_file == expected_path

    def test_store_message_record(self) -> None:
        """测试存储消息记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            record = MessageRecord(
                record_id="msg-1",
                session_id="test-session",
                timestamp=datetime(2023, 10, 25, 12, 0, 0),
                message_type=MessageType.USER,
                content="测试消息",
                metadata={"source": "test"}
            )
            
            result = storage.store_record(record)
            
            assert result is True
            
            # 验证文件是否创建并包含正确内容
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202310"
                session_file = storage._get_session_file("test-session")
                
                assert session_file.exists()
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    line = f.readline().strip()
                    stored_data = json.loads(line)
                    
                    assert stored_data['record_id'] == "msg-1"
                    assert stored_data['session_id'] == "test-session"
                    assert stored_data['message_type'] == "user"
                    assert stored_data['content'] == "测试消息"
                    assert stored_data['metadata']['source'] == "test"

    def test_store_tool_call_record(self) -> None:
        """测试存储工具调用记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            record = ToolCallRecord(
                record_id="tool-1",
                session_id="test-session",
                timestamp=datetime(2023, 10, 25, 12, 0, 0),
                tool_name="test_tool",
                tool_input={"param1": "value1", "param2": 123},
                tool_output={"result": "success"},
                metadata={"execution_time": 1.5}
            )
            
            result = storage.store_record(record)
            
            assert result is True
            
            # 验证文件内容
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202310"
                session_file = storage._get_session_file("test-session")
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    line = f.readline().strip()
                    stored_data = json.loads(line)
                    
                    assert stored_data['record_id'] == "tool-1"
                    assert stored_data['session_id'] == "test-session"
                    assert stored_data['tool_name'] == "test_tool"
                    assert stored_data['tool_input']['param1'] == "value1"
                    assert stored_data['tool_input']['param2'] == 123
                    assert stored_data['tool_output']['result'] == "success"
                    assert stored_data['metadata']['execution_time'] == 1.5

    def test_store_multiple_records(self) -> None:
        """测试存储多条记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            records: List[Union[MessageRecord, ToolCallRecord]] = [
                MessageRecord(
                    record_id="msg-1",
                    session_id="test-session",
                    timestamp=datetime(2023, 10, 25, 12, 0, 0),
                    content="消息1"
                ),
                ToolCallRecord(
                    record_id="tool-1",
                    session_id="test-session",
                    timestamp=datetime(2023, 10, 25, 12, 1, 0),
                    tool_name="test_tool"
                ),
                MessageRecord(
                    record_id="msg-2",
                    session_id="test-session",
                    timestamp=datetime(2023, 10, 25, 12, 2, 0),
                    content="消息2"
                )
            ]
            
            # 存储所有记录
            for record in records:
                result = storage.store_record(record)
                assert result is True
            
            # 验证文件包含所有记录
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202310"
                session_file = storage._get_session_file("test-session")
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    assert len(lines) == 3
                    
                    # 验证每条记录
                    for i, line in enumerate(lines):
                        stored_data = json.loads(line.strip())
                        assert stored_data['record_id'] == records[i].record_id

    def test_store_records_different_sessions(self) -> None:
        """测试存储不同会话的记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            record1 = MessageRecord(
                record_id="msg-1",
                session_id="session-1",
                timestamp=datetime(2023, 10, 25, 12, 0, 0),
                content="会话1消息"
            )
            
            record2 = MessageRecord(
                record_id="msg-2",
                session_id="session-2",
                timestamp=datetime(2023, 10, 25, 12, 0, 0),
                content="会话2消息"
            )
            
            # 存储记录
            storage.store_record(record1)
            storage.store_record(record2)
            
            # 验证创建了不同的文件
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202310"
                
                session1_file = storage._get_session_file("session-1")
                session2_file = storage._get_session_file("session-2")
                
                assert session1_file.exists()
                assert session2_file.exists()
                assert session1_file != session2_file

    def test_store_record_handles_exceptions(self) -> None:
        """测试存储记录时处理异常"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            record = MessageRecord(
                record_id="msg-1",
                session_id="test-session",
                timestamp=datetime.now(),
                content="测试消息"
            )
            
            # 模拟文件写入异常
            with patch('builtins.open', side_effect=IOError("写入错误")):
                result = storage.store_record(record)
                assert result is False

    def test_thread_safety(self) -> None:
        """测试线程安全性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            results = []
            
            def store_record_worker(record_id: str) -> None:
                record = MessageRecord(
                    record_id=record_id,
                    session_id="test-session",
                    timestamp=datetime.now(),
                    content=f"消息{record_id}"
                )
                result = storage.store_record(record)
                results.append(result)
            
            # 创建多个线程同时写入
            threads = []
            for i in range(10):
                thread = threading.Thread(target=store_record_worker, args=(f"msg-{i}",))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 验证所有操作都成功
            assert all(results)
            assert len(results) == 10
            
            # 验证文件包含所有记录
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202310"
                session_file = storage._get_session_file("test-session")
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    assert len(lines) == 10

    def test_unicode_content(self) -> None:
        """测试Unicode内容存储"""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileHistoryStorage(base_path)
            
            record = MessageRecord(
                record_id="msg-unicode",
                session_id="test-session",
                timestamp=datetime.now(),
                content="测试中文内容 🚀 emoji",
                metadata={"note": "备注中文"}
            )
            
            result = storage.store_record(record)
            assert result is True
            
            # 验证Unicode内容正确保存
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202310"
                session_file = storage._get_session_file("test-session")
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    line = f.readline().strip()
                    stored_data = json.loads(line)
                    
                    assert stored_data['content'] == "测试中文内容 🚀 emoji"
                    assert stored_data['metadata']['note'] == "备注中文"