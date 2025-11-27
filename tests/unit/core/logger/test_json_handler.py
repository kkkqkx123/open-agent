"""JsonHandler 类的单元测试"""

import json
import os
import tempfile
import threading
import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

from src.core.logger.handlers.json_handler import JsonHandler
from src.core.logger.log_level import LogLevel


class TestJsonHandler:
    """JsonHandler 测试类"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        temp_filename = os.path.join("logs", "test_json_handler_default.json")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            assert handler.level == LogLevel.INFO
            assert handler.filename == temp_filename
            assert handler.mode == "a"
            assert handler.encoding == "utf-8"
            assert handler.ensure_ascii is False
            assert handler.stream is not None
            assert isinstance(handler._lock, threading.Lock)
        finally:
            # 清理临时文件
            if handler is not None:
                try:
                    handler.close()
                except:
                    pass
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except:
                    pass

    def test_init_custom_values(self):
        """测试自定义值初始化"""
        temp_filename = os.path.join("logs", "test_json_handler_custom.json")
        handler = None
        
        try:
            custom_level = LogLevel.DEBUG
            config = {
                "filename": temp_filename,
                "mode": "w",
                "encoding": "utf-8",
                "ensure_ascii": True
            }
            
            handler = JsonHandler(level=custom_level, config=config)
            
            assert handler.level == custom_level
            assert handler.filename == temp_filename
            assert handler.mode == "w"
            assert handler.encoding == "utf-8"
            assert handler.ensure_ascii is True
        finally:
            # 清理临时文件
            if handler is not None:
                try:
                    handler.close()
                except:
                    pass
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except:
                    pass

    def test_init_with_directory_creation(self):
        """测试目录创建功能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "subdir", "test.json")
            
            config = {"filename": test_file}
            handler = JsonHandler(config=config)
            
            # 验证目录被创建
            assert os.path.exists(os.path.dirname(test_file))
            assert handler.filename == test_file
            
            handler.close()  # 清理

    def test_emit_basic_record(self):
        """测试基本记录输出"""
        temp_filename = os.path.join("logs", "test_json_handler_basic.json")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            record = {
                "timestamp": datetime(2023, 1, 15, 10, 30, 45),
                "name": "test_logger",
                "level": LogLevel.INFO,
                "message": "Test message"
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容并验证是有效的JSON
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 解析JSON并验证内容
            parsed = json.loads(content)
            assert parsed["timestamp"] == "2023-01-15T10:30:45"
            assert parsed["name"] == "test_logger"
            assert parsed["level"] == "INFO"
            assert parsed["message"] == "Test message"
        finally:
            # 清理临时文件
            if handler is not None:
                try:
                    handler.close()
                except:
                    pass
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except:
                    pass

    def test_emit_with_datetime(self):
        """测试包含日期时间的记录输出"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            record = {
                "timestamp": datetime(2023, 1, 15, 10, 30, 45, 123456),
                "created_at": datetime(2023, 1, 14, 8, 15, 30),
                "message": "Test with datetime"
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容并验证日期时间格式化
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            parsed = json.loads(content)
            assert parsed["timestamp"] == "2023-01-15T10:30:45.123456"
            assert parsed["created_at"] == "2023-01-14T08:15:30"
            assert parsed["message"] == "Test with datetime"
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_emit_with_log_levels(self):
        """测试包含不同日志级别的记录输出"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            record = {
                "level": LogLevel.ERROR,
                "min_level": LogLevel.DEBUG,
                "max_level": LogLevel.CRITICAL,
                "message": "Test with log levels"
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容并验证日志级别格式化
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            parsed = json.loads(content)
            assert parsed["level"] == "ERROR"
            assert parsed["min_level"] == "DEBUG"
            assert parsed["max_level"] == "CRITICAL"
            assert parsed["message"] == "Test with log levels"
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_emit_with_complex_data(self):
        """测试包含复杂数据的记录输出"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            record = {
                "timestamp": datetime(2023, 1, 15, 10, 30, 45),
                "level": LogLevel.WARNING,
                "message": "Complex data test",
                "data": {
                    "nested": {
                        "value": 123,
                        "list": [1, 2, 3]
                    }
                },
                "numbers": [1, 2, 3.14],
                "boolean": True,
                "none_value": None
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容并验证复杂数据
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            parsed = json.loads(content)
            assert parsed["timestamp"] == "2023-01-15T10:30:45"
            assert parsed["level"] == "WARNING"
            assert parsed["message"] == "Complex data test"
            assert parsed["data"]["nested"]["value"] == 123
            assert parsed["data"]["nested"]["list"] == [1, 2, 3]
            assert parsed["numbers"] == [1, 2, 3.14]
            assert parsed["boolean"] is True
            assert parsed["none_value"] is None
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_emit_with_unicode_characters(self):
        """测试包含Unicode字符的记录输出"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename, "ensure_ascii": False}
            handler = JsonHandler(config=config)
            
            record = {
                "message": "测试消息：包含中文和特殊字符 🚀",
                "emoji": "🎉",
                "chinese": "中文测试",
                "special": "特殊字符：@#$%^&*()"
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容并验证Unicode字符
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            parsed = json.loads(content)
            assert parsed["message"] == "测试消息：包含中文和特殊字符 🚀"
            assert parsed["emoji"] == "🎉"
            assert parsed["chinese"] == "中文测试"
            assert parsed["special"] == "特殊字符：@#$%^&*()"
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_emit_level_filtering(self):
        """测试日志级别过滤"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(level=LogLevel.WARNING, config=config)
            
            # 测试低于设置级别的记录（应该被过滤）
            debug_record = {"message": "debug", "level": LogLevel.DEBUG}
            info_record = {"message": "info", "level": LogLevel.INFO}
            
            handler.handle(debug_record)
            handler.handle(info_record)
            handler.flush()
            
            # 读取文件内容，应该为空或没有过滤的消息
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "debug" not in content
            assert "info" not in content
            
            # 测试等于或高于设置级别的记录（应该被处理）
            warning_record = {"message": "warning", "level": LogLevel.WARNING}
            error_record = {"message": "error", "level": LogLevel.ERROR}
            
            handler.handle(warning_record)
            handler.handle(error_record)
            handler.flush()
            handler.close()
            
            # 读取文件内容，应该包含过滤后的消息
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "warning" in content
            assert "error" in content
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_flush_method(self):
        """测试刷新方法"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            # 调用flush方法不应该抛出异常
            handler.flush()
            
            handler.close()
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_close_method(self):
        """测试关闭方法"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            # 确保流是打开的
            assert handler.stream is not None
            assert not handler.stream.closed
            
            # 关闭处理器
            handler.close()
            
            # 验证流已关闭
            assert handler.stream is None
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                # 如果文件仍被打开，先关闭再删除
                try:
                    os.unlink(temp_filename)
                except PermissionError:
                    pass

    def test_handle_error(self):
        """测试错误处理"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            # 模拟写入错误
            original_stream = handler.stream
            handler.stream = None # 设置为None以触发错误处理
            
            record = {
                "message": "Test message",
                "level": LogLevel.INFO
            }
            
            # 这不应该抛出异常
            handler.emit(record)
            
            # 恢复流以进行清理
            handler.stream = original_stream
            handler.close()
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except PermissionError:
                    pass

    def test_prepare_json_record(self):
        """测试JSON记录准备方法"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            record = {
                "timestamp": datetime(2023, 1, 15, 10, 30, 45),
                "level": LogLevel.INFO,
                "normal_string": "normal value",
                "number": 42,
                "boolean": True,
                "none_value": None,
                "list": [1, 2, 3],
                "dict": {"key": "value"}
            }
            
            result = handler._prepare_json_record(record)
            
            assert result["timestamp"] == "2023-01-15T10:30:45"
            assert result["level"] == "INFO"
            assert result["normal_string"] == "normal value"
            assert result["number"] == 42
            assert result["boolean"] is True
            assert result["none_value"] is None
            assert result["list"] == [1, 2, 3]
            assert result["dict"] == {"key": "value"}
            
            handler.close()
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_concurrent_writes(self):
        """测试并发写入"""
        temp_filename = os.path.join("logs", "test_json_handler_concurrent.json")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            def write_record(message):
                record = {
                    "message": message,
                    "level": LogLevel.INFO,
                    "timestamp": datetime.now()
                }
                handler.emit(record)
            
            # 创建多个线程并发写入
            threads = []
            for i in range(3):
                thread = threading.Thread(target=write_record, args=[f"Message {i}"])
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            handler.flush()
            handler.close()
            
            # 读取文件内容验证 - 每行应该是有效的JSON
            with open(temp_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 验证每一行都是有效的JSON且包含消息
            for i, line in enumerate(lines):
                if line.strip():  # 忽略空行
                    parsed = json.loads(line.strip())
                    assert "Message" in parsed["message"]
        finally:
            # 清理临时文件
            if handler is not None:
                try:
                    handler.close()
                except:
                    pass
            import time
            time.sleep(0.01)
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except:
                    pass

    def test_set_level(self):
        """测试设置日志级别"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            handler.set_level(LogLevel.DEBUG)
            assert handler.level == LogLevel.DEBUG
            
            handler.set_level(LogLevel.CRITICAL)
            assert handler.level == LogLevel.CRITICAL
            
            handler.close()
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_empty_record(self):
        """测试空记录"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            record = {}
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容验证是有效的空JSON对象
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            parsed = json.loads(content)
            assert parsed == {}
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_none_stream_handling(self):
        """测试流为None的情况"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            # 临时将流设为None以测试保护机制
            original_stream = handler.stream
            handler.stream = None
            
            record = {"message": "test", "level": LogLevel.INFO}
            
            # 这不应该抛出异常
            handler.emit(record)
            
            # 恢复流用于清理
            handler.stream = original_stream
            handler.close()
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except PermissionError:
                    pass

    def test_nested_objects(self):
        """测试嵌套对象"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = JsonHandler(config=config)
            
            record = {
                "level": LogLevel.ERROR,
                "message": "Nested object test",
                "nested": {
                    "timestamp": datetime(2023, 1, 15, 10, 30, 45),
                    "level": LogLevel.WARNING,
                    "data": {
                        "deep": {
                            "value": "deep value"
                        }
                    }
                }
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容验证嵌套对象
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            parsed = json.loads(content)
            assert parsed["level"] == "ERROR"
            assert parsed["message"] == "Nested object test"
            assert parsed["nested"]["timestamp"] == "2023-01-15T10:30:45"
            assert parsed["nested"]["level"] == "WARNING"
            assert parsed["nested"]["data"]["deep"]["value"] == "deep value"
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)