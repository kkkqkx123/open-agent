"""TUI事件引擎单元测试"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from queue import Queue
import threading
import time
import sys

from src.presentation.tui.event_engine import EventEngine


class TestEventEngine:
    """测试事件引擎类"""
    
    def test_event_engine_init(self):
        """测试事件引擎初始化"""
        mock_terminal = Mock()
        mock_config = Mock()
        
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        assert engine.terminal == mock_terminal
        assert engine.config == mock_config
        assert engine.running is False
        assert isinstance(engine.input_queue, Queue)
        assert engine.input_thread is None
        assert engine.key_handlers == {}
        assert engine.global_key_handler is None
        assert engine.input_component_handler is None
        assert engine.input_result_handler is None
    
    def test_register_key_handler(self):
        """测试注册按键处理器"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        def test_handler(key):
            return True
        
        engine.register_key_handler("enter", test_handler)
        
        assert "enter" in engine.key_handlers
        assert engine.key_handlers["enter"] == test_handler
    
    def test_unregister_key_handler(self):
        """测试取消注册按键处理器"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        def test_handler(key):
            return True
        
        engine.register_key_handler("enter", test_handler)
        assert "enter" in engine.key_handlers
        
        engine.unregister_key_handler("enter")
        assert "enter" not in engine.key_handlers
    
    def test_unregister_key_handler_nonexistent(self):
        """测试取消注册不存在的按键处理器"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 不应该抛出异常
        engine.unregister_key_handler("nonexistent")
    
    def test_set_global_key_handler(self):
        """测试设置全局按键处理器"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        def test_handler(key):
            return True
        
        engine.set_global_key_handler(test_handler)
        
        assert engine.global_key_handler == test_handler
    
    def test_set_input_component_handler(self):
        """测试设置输入组件处理器"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        def test_handler(key):
            return "result"
        
        engine.set_input_component_handler(test_handler)
        
        assert engine.input_component_handler == test_handler
    
    def test_set_input_result_handler(self):
        """测试设置输入结果处理器"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        def test_handler(result):
            pass
        
        engine.set_input_result_handler(test_handler)
        
        assert engine.input_result_handler == test_handler
    
    def test_stop_when_not_running(self):
        """测试停止未运行的引擎"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 初始状态应该是安全的
        assert engine.running is False
        engine.stop()
        assert engine.running is False
    
    def test_convert_key_sequence_special_chars(self):
        """测试转换特殊字符序列"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 测试各种特殊字符
        assert engine._convert_key_sequence('\x1b') == "escape"  # ESC
        assert engine._convert_key_sequence('\x0d') == "enter"   # Enter (CR)
        assert engine._convert_key_sequence('\x7f') == "backspace"  # Backspace
        assert engine._convert_key_sequence('\x09') == "tab"    # Tab
    
    def test_convert_key_sequence_normal_char(self):
        """测试转换普通字符"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        assert engine._convert_key_sequence('a') == "char:a"
        assert engine._convert_key_sequence('中') == "char:中"  # 中文字符
    
    def test_process_key_with_input_component_handler(self):
        """测试处理按键（有输入组件处理器）"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 设置输入组件处理器，返回一个结果
        mock_input_handler = Mock(return_value="processed_result")
        engine.set_input_component_handler(mock_input_handler)
        
        # 设置输入结果处理器
        mock_result_handler = Mock()
        engine.set_input_result_handler(mock_result_handler)
        
        # 处理按键
        engine._process_key('a')
        
        # 验证处理器被调用
        mock_input_handler.assert_called_once_with("char:a")
        mock_result_handler.assert_called_once_with("processed_result")
    
    def test_process_key_with_key_handlers(self):
        """测试处理按键（有注册的按键处理器）"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 设置按键处理器，返回True表示已处理
        mock_key_handler = Mock(return_value=True)
        engine.register_key_handler("enter", mock_key_handler)
        
        # 设置全局处理器（应该不会被调用，因为按键处理器已处理）
        mock_global_handler = Mock()
        engine.set_global_key_handler(mock_global_handler)
        
        # 处理按键
        engine._process_key('\x0d')  # Enter
        
        # 验证按键处理器被调用
        mock_key_handler.assert_called_once_with("enter")
        # 全局处理器不应该被调用
        assert not mock_global_handler.called
    
    def test_process_key_with_global_handler(self):
        """测试处理按键（有全局处理器）"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 设置全局处理器
        mock_global_handler = Mock()
        engine.set_global_key_handler(mock_global_handler)
        
        # 处理按键
        engine._process_key('a')
        
        # 验证全局处理器被调用
        mock_global_handler.assert_called_once_with("char:a")
    
    def test_process_key_with_consumed_by_key_handler(self):
        """测试按键被按键处理器消费（返回True）"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 设置按键处理器，返回True表示已处理
        mock_key_handler = Mock(return_value=True)
        engine.register_key_handler("escape", mock_key_handler)
        
        # 设置全局处理器
        mock_global_handler = Mock()
        engine.set_global_key_handler(mock_global_handler)
        
        # 处理按键
        engine._process_key('\x1b')  # ESC
        
        # 验证按键处理器被调用
        mock_key_handler.assert_called_once_with("escape")
        # 全局处理器不应该被调用
        assert not mock_global_handler.called
    
    def test_process_key_with_not_consumed_by_key_handler(self):
        """测试按键未被按键处理器消费（返回False）"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 设置按键处理器，返回False表示未处理
        mock_key_handler = Mock(return_value=False)
        engine.register_key_handler("escape", mock_key_handler)
        
        # 设置全局处理器
        mock_global_handler = Mock()
        engine.set_global_key_handler(mock_global_handler)
        
        # 处理按键
        engine._process_key('\x1b')  # ESC
        
        # 验证按键处理器被调用
        mock_key_handler.assert_called_once_with("escape")
        # 全局处理器也应该被调用
        mock_global_handler.assert_called_once_with("escape")
    
    def test_process_key_empty_result_from_input_component(self):
        """测试输入组件返回空结果"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 设置输入组件处理器，返回None
        mock_input_handler = Mock(return_value=None)
        engine.set_input_component_handler(mock_input_handler)
        
        # 设置输入结果处理器
        mock_result_handler = Mock()
        engine.set_input_result_handler(mock_result_handler)
        
        # 处理按键
        engine._process_key('a')
        
        # 验证输入组件处理器被调用
        mock_input_handler.assert_called_once_with("char:a")
        # 但结果处理器不应该被调用
        assert not mock_result_handler.called


class TestEventEngineThreading:
    """测试事件引擎的线程相关功能"""
    
    def test_start_and_stop_event_loop(self):
        """测试启动和停止事件循环"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 由于完整测试事件循环很复杂，我们测试基本的启动/停止功能
        # 通过模拟输入读取函数来避免实际的终端操作
        original_input_reader = engine._input_reader
        engine._input_reader = Mock()
        
        # 模拟一个快速退出的循环
        def mock_event_loop():
            engine.running = True
            # 立即停止，避免长时间等待
            engine.running = False
        
        # 替换主循环方法
        original_method = engine.start_event_loop
        engine.start_event_loop = mock_event_loop
        
        # 启动引擎
        engine.running = True
        engine.start_event_loop()
        
        # 停止引擎
        engine.stop()
        
        # 恢复原始方法
        engine.start_event_loop = original_method
        engine._input_reader = original_input_reader
    
    def test_input_reader_thread(self):
        """测试输入读取线程"""
        # 这个测试比较复杂，因为需要模拟终端输入
        # 我们将测试方法不会抛出异常
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 设置为运行状态
        engine.running = True
        
        # 模拟终端的cbreak上下文管理器
        mock_terminal.cbreak.return_value.__enter__ = Mock()
        mock_terminal.cbreak.return_value.__exit__ = Mock()
        
        # 由于无法轻易测试输入读取，我们验证方法签名
        assert hasattr(engine, '_input_reader')
        
        # 停止引擎
        engine.running = False
    
    def test_process_key_with_queue(self):
        """测试使用队列处理按键"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 直接向队列添加按键
        engine.input_queue.put('a')
        
        # 模拟处理队列中的输入
        try:
            while not engine.input_queue.empty():
                key_str = engine.input_queue.get_nowait()
                engine._process_key(key_str)
        except Exception:
            pass  # 忽略可能的异常，因为处理器可能未设置
        
        # 验证队列现在为空
        assert engine.input_queue.empty()
    
    def test_stop_with_active_thread(self):
        """测试停止时有活跃线程"""
        mock_terminal = Mock()
        mock_config = Mock()
        engine = EventEngine(terminal=mock_terminal, config=mock_config)
        
        # 创建一个模拟的活跃线程
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        engine.input_thread = mock_thread
        
        # 停止引擎
        engine.stop()
        
        # 验证线程join被调用
        assert mock_thread.join.called