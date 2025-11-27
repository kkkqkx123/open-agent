"""FileHandler 类的单元测试"""

import os
import tempfile
import threading
import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

from src.core.logger.handlers.file_handler import FileHandler
from src.core.logger.log_level import LogLevel
from src.core.logger.formatters.text_formatter import TextFormatter


class TestFileHandler:
    """FileHandler 测试类"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        # 使用项目内的临时文件
        temp_filename = os.path.join("logs", "test_file_handler_default.log")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            assert handler.level == LogLevel.INFO
            assert handler.filename == temp_filename
            assert handler.mode == "a"
            assert handler.encoding == "utf-8"
            assert isinstance(handler._formatter, TextFormatter)
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
        temp_filename = os.path.join("logs", "test_file_handler_custom.log")
        handler = None
        
        try:
            custom_level = LogLevel.DEBUG
            config = {
                "filename": temp_filename,
                "mode": "w",
                "encoding": "utf-8"
            }
            
            handler = FileHandler(level=custom_level, config=config)
            
            assert handler.level == custom_level
            assert handler.filename == temp_filename
            assert handler.mode == "w"
            assert handler.encoding == "utf-8"
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
            test_file = os.path.join(temp_dir, "subdir", "test.log")
            
            config = {"filename": test_file}
            handler = FileHandler(config=config)
            
            # 验证目录被创建
            assert os.path.exists(os.path.dirname(test_file))
            assert handler.filename == test_file
            
            handler.close()  # 清理

    def test_emit_basic_record(self):
        """测试基本记录输出"""
        temp_filename = os.path.join("logs", "test_file_handler_basic.log")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            record = {
                "timestamp": datetime(2023, 1, 15, 10, 30, 45),
                "name": "test_logger",
                "level": LogLevel.INFO,
                "message": "Test message"
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容验证
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "Test message" in content
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

    def test_emit_with_formatter(self):
        """测试使用格式化器输出"""
        temp_filename = os.path.join("logs", "test_file_handler_formatter.log")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            # 设置自定义格式化器
            mock_formatter = Mock()
            mock_formatter.format.return_value = "Custom formatted message"
            handler.set_formatter(mock_formatter)
            
            record = {
                "timestamp": datetime(2023, 1, 15, 10, 30, 45),
                "name": "test_logger",
                "level": LogLevel.INFO,
                "message": "Test message"
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 验证格式化器被调用
            mock_formatter.format.assert_called_once_with(record)
            
            # 读取文件内容验证使用了自定义格式
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "Custom formatted message" in content
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

    def test_emit_level_filtering(self):
        """测试日志级别过滤"""
        temp_filename = os.path.join("logs", "test_file_handler_filtering.log")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(level=LogLevel.WARNING, config=config)
            
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

    def test_flush_method(self):
        """测试刷新方法"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            # 调用flush方法不应该抛出异常
            handler.flush()
            
            handler.close()
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_close_method(self):
        """测试关闭方法"""
        temp_filename = os.path.join("logs", "test_file_handler_close.log")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            # 确保流是打开的
            assert handler.stream is not None
            assert not handler.stream.closed
            
            # 关闭处理器
            handler.close()
            
            # 验证流已关闭
            assert handler.stream is None
        finally:
            # 清理临时文件
            if handler is not None:
                try:
                    handler.close()
                except:
                    pass
            if os.path.exists(temp_filename):
                # 如果文件仍被打开，先关闭再删除
                try:
                    os.unlink(temp_filename)
                except PermissionError:
                    pass

    def test_handle_error(self):
        """测试错误处理"""
        temp_filename = os.path.join("logs", "test_file_handler_error.log")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            # 模拟写入错误
            original_stream = handler.stream
            handler.stream = None  # 设置为None以触发错误处理
            
            record = {
                "message": "Test message",
                "level": LogLevel.INFO
            }
            
            # 这不应该抛出异常
            handler.emit(record)
            
            # 恢复流以进行清理
            if original_stream:
                handler.stream = original_stream
            if handler:
                handler.close()
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
                except PermissionError:
                    pass

    def test_init_with_nonexistent_directory(self):
        """测试不存在目录的初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "nonexistent", "subdir", "test.log")
            
            config = {"filename": test_file}
            handler = FileHandler(config=config)
            
            # 验证目录被创建
            assert os.path.exists(os.path.dirname(test_file))
            
            handler.close()  # 清理

    def test_emit_with_special_characters(self):
        """测试特殊字符输出"""
        temp_filename = os.path.join("logs", "test_file_handler_special.log")
        handler = None
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            record = {
                "message": "测试消息：包含中文和特殊字符 🚀",
                "level": LogLevel.INFO
            }
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 读取文件内容验证
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "测试消息" in content
            assert "🚀" in content
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

    def test_concurrent_writes(self):
        """测试并发写入"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            def write_record(message):
                record = {"message": message, "level": LogLevel.INFO}
                handler.emit(record)
            
            # 创建多个线程并发写入
            threads = []
            for i in range(5):
                thread = threading.Thread(target=write_record, args=[f"Message {i}"])
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            handler.flush()
            handler.close()
            
            # 读取文件内容验证
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证所有消息都写入了
            for i in range(5):
                assert f"Message {i}" in content
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_set_formatter(self):
        """测试设置格式化器"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            mock_formatter = Mock()
            handler.set_formatter(mock_formatter)
            
            assert handler._formatter == mock_formatter
            
            handler.close()
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_set_level(self):
        """测试设置日志级别"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
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
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
            record = {}
            
            handler.emit(record)
            handler.flush()
            handler.close()
            
            # 验证没有异常
            assert os.path.exists(temp_filename)
        finally:
            # 清理临时文件
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_none_stream_handling(self):
        """测试流为None的情况"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            config = {"filename": temp_filename}
            handler = FileHandler(config=config)
            
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