"""TUI输入面板组件单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

from src.presentation.tui.components.input_panel_component import (
    InputHistory, InputBuffer
)
from src.presentation.tui.components.input_panel import InputPanel
from src.presentation.tui.components.input_panel_component import SlashCommandProcessor as CommandProcessor


class TestInputHistory:
    """测试输入历史记录组件"""
    
    def test_input_history_init(self):
        """测试输入历史记录初始化"""
        history = InputHistory()
        
        assert history.max_history == 100
        assert history.history == []
        assert history.current_index == -1
        assert history.temp_input == ""
    
    def test_input_history_init_custom_max(self):
        """测试自定义最大历史记录数的初始化"""
        history = InputHistory(max_history=50)
        
        assert history.max_history == 50
    
    def test_add_entry(self):
        """测试添加历史记录"""
        history = InputHistory()
        
        history.add_entry("test input 1")
        history.add_entry("test input 2")
        
        assert len(history.history) == 2
        assert history.history[0] == "test input 1"
        assert history.history[1] == "test input 2"
        assert history.current_index == -1
    
    def test_add_entry_duplicate(self):
        """测试添加重复输入（不应添加）"""
        history = InputHistory()
        
        history.add_entry("test input")
        history.add_entry("test input")  # 重复输入
        
        assert len(history.history) == 1
        assert history.history[0] == "test input"
    
    def test_add_entry_empty(self):
        """测试添加空输入（不应添加）"""
        history = InputHistory()
        
        history.add_entry("")
        history.add_entry("   ")  # 只有空格
        
        assert len(history.history) == 0
    
    def test_add_entry_limit(self):
        """测试历史记录数量限制"""
        history = InputHistory(max_history=2)
        
        history.add_entry("input 1")
        history.add_entry("input 2")
        history.add_entry("input 3")  # 应该移除第一个输入
        
        assert len(history.history) == 2
        assert history.history[0] == "input 2"
        assert history.history[1] == "input 3"
    
    def test_navigate_up(self):
        """测试向上导航历史记录"""
        history = InputHistory()
        history.add_entry("input 1")
        history.add_entry("input 2")
        history.add_entry("input 3")
        
        # 从当前输入开始
        current = "current input"
        
        # 第一次向上导航
        result = history.navigate_up(current)
        assert result == "input 3"
        assert history.current_index == 0
        
        # 继续向上
        result = history.navigate_up(result)
        assert result == "input 2"
        assert history.current_index == 1
        
        # 继续向上
        result = history.navigate_up(result)
        assert result == "input 1"
        assert history.current_index == 2
    
    def test_navigate_up_at_beginning(self):
        """测试在历史记录开始处继续向上导航"""
        history = InputHistory()
        history.add_entry("input 1")
        history.add_entry("input 2")
        
        # 导航到最开始
        current = "current"
        for _ in range(3):  # 超过历史记录数量
            current = history.navigate_up(current)
        
        assert current == "input 1"  # 应该停留在第一个
    
    def test_navigate_down(self):
        """测试向下导航历史记录"""
        history = InputHistory()
        history.add_entry("input 1")
        history.add_entry("input 2")
        history.add_entry("input 3")
        
        # 先向上导航到某个位置
        current = history.navigate_up("current")
        current = history.navigate_up(current)  # 现在在 input 2
        
        # 向下导航
        result = history.navigate_down(current)
        assert result == "input 3"
        assert history.current_index == 0
    
    def test_navigate_down_at_end(self):
        """测试在历史记录末尾继续向下导航"""
        history = InputHistory()
        history.add_entry("input 1")
        history.add_entry("input 2")
        
        # 向上然后向下回到当前输入
        current = history.navigate_up("original input")
        result = history.navigate_down(current)
        
        assert result == "original input"
        assert history.current_index == -1
    
    def test_reset_navigation(self):
        """测试重置导航状态"""
        history = InputHistory()
        history.add_entry("input 1")
        
        # 导航到历史记录
        history.navigate_up("current")
        assert history.current_index != -1
        
        # 重置
        history.reset_navigation()
        assert history.current_index == -1
        assert history.temp_input == ""
    
    def test_clear_history(self):
        """测试清空历史记录"""
        history = InputHistory()
        history.add_entry("input 1")
        history.add_entry("input 2")
        
        history.clear_history()
        
        assert history.history == []
        assert history.current_index == -1
        assert history.temp_input == ""
    
    def test_get_recent_history(self):
        """测试获取最近历史记录"""
        history = InputHistory()
        history.add_entry("input 1")
        history.add_entry("input 2")
        history.add_entry("input 3")
        
        recent = history.get_recent_history(2)
        
        assert len(recent) == 2
        assert recent[0] == "input 2"
        assert recent[1] == "input 3"


class TestCommandProcessor:
    """测试命令处理器组件"""
    
    def test_command_processor_init(self):
        """测试命令处理器初始化"""
        processor = CommandProcessor()
        
        assert len(processor.commands) > 0 # 有内置命令
        assert "help" in processor.commands
        assert "clear" in processor.commands
        assert "exit" in processor.commands
        assert "save" in processor.commands
        assert "load" in processor.commands
        assert "new" in processor.commands
        assert "pause" in processor.commands
        assert "resume" in processor.commands
        assert "stop" in processor.commands
        assert "studio" in processor.commands
        assert "sessions" in processor.commands
        assert "agents" in processor.commands
        
        assert "h" in processor.command_aliases  # 别名
        assert "q" in processor.command_aliases  # 别名
    
    def test_is_command(self):
        """测试判断是否是命令"""
        processor = CommandProcessor()
        
        assert processor.is_command("/help") is True
        assert processor.is_command("/clear") is True
        assert processor.is_command("regular text") is False
        assert processor.is_command("not/a/command") is False
    
    def test_parse_command(self):
        """测试解析命令"""
        processor = CommandProcessor()
        
        # 测试简单命令
        cmd, args = processor.parse_command("/help")
        assert cmd == "help"
        assert args == []
        
        # 测试带参数的命令
        cmd, args = processor.parse_command("/load session123")
        assert cmd == "load"
        assert args == ["session123"]
        
        # 测试多个参数的命令
        cmd, args = processor.parse_command("/load session123 param2")
        assert cmd == "load"
        assert args == ["session123", "param2"]
        
        # 测试别名
        cmd, args = processor.parse_command("/h")
        assert cmd == "help"
        assert args == []
    
    def test_execute_command_help(self):
        """测试执行帮助命令"""
        processor = CommandProcessor()
        
        result = processor.execute_command("/help")
        assert result is not None
        assert "可用命令:" in result
        
        result = processor.execute_command("/help clear")
        assert result is not None
        assert "/clear" in result
    
    def test_execute_command_clear(self):
        """测试执行清屏命令"""
        processor = CommandProcessor()
        
        result = processor.execute_command("/clear")
        assert result == "CLEAR_SCREEN"
    
    def test_execute_command_exit(self):
        """测试执行退出命令"""
        processor = CommandProcessor()
        
        result = processor.execute_command("/exit")
        assert result == "EXIT"
    
    def test_execute_command_save(self):
        """测试执行保存命令"""
        processor = CommandProcessor()
        
        result = processor.execute_command("/save")
        assert result == "SAVE_SESSION"
    
    def test_execute_command_load(self):
        """测试执行加载命令"""
        processor = CommandProcessor()
        
        result = processor.execute_command("/load session123")
        assert result == "LOAD_SESSION:session123"
    
    def test_execute_command_new(self):
        """测试执行新建会话命令"""
        processor = CommandProcessor()
        
        result = processor.execute_command("/new")
        assert result == "NEW_SESSION"
    
    def test_execute_command_workflow(self):
        """测试执行工作流相关命令"""
        processor = CommandProcessor()
        
        assert processor.execute_command("/pause") == "PAUSE_WORKFLOW"
        assert processor.execute_command("/resume") == "RESUME_WORKFLOW"
        assert processor.execute_command("/stop") == "STOP_WORKFLOW"
    
    def test_execute_command_studio_sessions_agents(self):
        """测试执行Studio、会话、Agent命令"""
        processor = CommandProcessor()
        
        assert processor.execute_command("/studio") == "OPEN_STUDIO"
        assert processor.execute_command("/sessions") == "OPEN_SESSIONS"
        assert processor.execute_command("/agents") == "OPEN_AGENTS"
    
    def test_execute_invalid_command(self):
        """测试执行无效命令"""
        processor = CommandProcessor()
        
        result = processor.execute_command("/invalid")
        assert result is not None
        assert "未知命令: invalid" in result
    
    def test_execute_command_with_context(self):
        """测试带上下文执行命令"""
        processor = CommandProcessor()
        
        # 测试历史记录命令
        context = {
            'input_history': InputHistory()
        }
        context['input_history'].add_entry("test input")
        
        result = processor.execute_command("/history", context)
        assert result is not None
        assert "最近输入历史:" in result
        assert "test input" in result
    
    def test_register_command(self):
        """测试注册自定义命令"""
        processor = CommandProcessor()
        
        def custom_handler(args):
            return "custom result"
        
        processor.register_command("custom", custom_handler, "Custom command", ["c"])
        
        assert "custom" in processor.commands
        assert "c" in processor.command_aliases
        assert processor.command_aliases["c"] == "custom"
        
        result = processor.execute_command("/custom")
        assert result == "custom result"


class TestInputBuffer:
    """测试输入缓冲区组件"""
    
    def test_input_buffer_init(self):
        """测试输入缓冲区初始化"""
        buffer = InputBuffer()
        
        assert buffer.buffer == ""
        assert buffer.cursor_position == 0
        assert buffer.multiline_mode is False
        assert buffer.lines == []
        assert buffer.current_line == 0
    
    def test_insert_text_single_line(self):
        """测试单行模式插入文本"""
        buffer = InputBuffer()
        
        buffer.insert_text("hello")
        assert buffer.buffer == "hello"
        assert buffer.cursor_position == 5
        
        buffer.insert_text(" world")
        assert buffer.buffer == "hello world"
        assert buffer.cursor_position == 11
    
    def test_insert_text_at_position(self):
        """测试在特定位置插入文本"""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor_position = 2  # 在 "he" 之后
        
        buffer.insert_text("XX")
        assert buffer.buffer == "heXXllo"
        assert buffer.cursor_position == 4
    
    def test_delete_char_backward(self):
        """测试向后删除字符"""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor_position = 3  # 在 "hel" 之后
        
        buffer.delete_char(backward=True)
        assert buffer.buffer == "helo"
        assert buffer.cursor_position == 2
    
    def test_delete_char_forward(self):
        """测试向前删除字符"""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor_position = 2  # 在 "he" 之后
        
        buffer.delete_char(backward=False)
        assert buffer.buffer == "helo"
        assert buffer.cursor_position == 2
    
    def test_move_cursor(self):
        """测试移动光标"""
        buffer = InputBuffer()
        buffer.set_text("hello")
        
        # 测试左右移动
        buffer.move_cursor("right")
        # 根据InputBuffer的实现，移动光标后位置会改变
        # 验证没有异常发生
        buffer.move_cursor("left")
        # 验证没有异常发生
        
        # 测试home和end
        buffer.move_cursor("end")
        assert buffer.cursor_position == 5
        
        buffer.move_cursor("home")
        assert buffer.cursor_position == 0
    
    def test_toggle_multiline(self):
        """测试切换多行模式"""
        buffer = InputBuffer()
        buffer.set_text("line1\nline2\nline3")
        
        # 切换到多行模式
        buffer.toggle_multiline()
        assert buffer.multiline_mode is True
        assert buffer.lines == ["line1", "line2", "line3"]
        assert buffer.current_line == 2 # 最后一行
        assert buffer.cursor_position == 5  # 最后一行的长度
        
        # 切换回单行模式
        buffer.toggle_multiline()
        assert buffer.multiline_mode is False
        assert buffer.buffer == "line1\nline2\nline3"
    
    def test_get_set_text(self):
        """测试获取和设置文本"""
        buffer = InputBuffer()
        
        buffer.set_text("test text")
        assert buffer.get_text() == "test text"
        
        buffer.toggle_multiline()
        buffer.set_text("line1\nline2")
        assert buffer.get_text() == "line1\nline2"
    
    def test_clear(self):
        """测试清空缓冲区"""
        buffer = InputBuffer()
        buffer.set_text("test text")
        buffer.toggle_multiline()
        
        buffer.clear()
        
        assert buffer.buffer == ""
        assert buffer.cursor_position == 0
        assert buffer.multiline_mode is False
        assert buffer.lines == []
        assert buffer.current_line == 0
    
    def test_is_empty(self):
        """测试判断是否为空"""
        buffer = InputBuffer()
        
        assert buffer.is_empty() is True
        
        buffer.set_text("text")
        assert buffer.is_empty() is False
        
        buffer.set_text("")
        assert buffer.is_empty() is True
        
        buffer.toggle_multiline()
        buffer.set_text("line1\nline2")
        assert buffer.is_empty() is False
        
        buffer.set_text("\n\n")  # 只有换行符
        assert buffer.is_empty() is True  # 认为空白行也是空的


class TestInputPanelComponent:
    """测试输入面板组件"""
    
    def test_input_panel_component_init(self):
        """测试输入面板组件初始化"""
        from src.presentation.tui.config import TUIConfig
        
        config = TUIConfig.__new__(TUIConfig)  # 创建一个空的配置对象
        panel = InputPanel(config)
        
        assert panel.config == config
        assert panel.input_buffer is not None
        assert panel.input_history is not None
        assert panel.command_processors is not None
        assert panel.is_processing is False
        assert panel.show_help is False
        assert panel.placeholder == "在此输入消息... (使用 /help 查看命令, @选择文件, #选择工作流)"
        assert panel.on_submit is None
        assert panel.on_command is None
    
    def test_input_panel_component_init_without_config(self):
        """测试无配置初始化输入面板组件"""
        panel = InputPanel()
        
        assert panel.config is None
        assert panel.input_buffer is not None
        assert panel.input_history is not None
        assert panel.command_processors is not None
    
    def test_set_callbacks(self):
        """测试设置回调函数"""
        panel = InputPanel()
        
        def submit_callback(text):
            pass
        
        def command_callback(cmd, args):
            pass
        
        panel.set_submit_callback(submit_callback)
        panel.set_command_callback(command_callback)
        
        assert panel.on_submit == submit_callback
        assert panel.on_command == command_callback
    
    def test_handle_key_enter_empty(self):
        """测试回车键处理（空输入）"""
        panel = InputPanel()
        
        result = panel.handle_key("enter")
        
        assert result is None
        assert panel.input_buffer.is_empty() is True
    
    def test_handle_key_enter_command(self):
        """测试回车键处理（命令输入）"""
        panel = InputPanel()
        
        # 设置输入为命令
        panel.input_buffer.set_text("/help")
        
        # 模拟提交回调
        mock_submit = Mock()
        panel.set_submit_callback(mock_submit)
        
        # 模拟命令回调
        mock_command = Mock()
        panel.set_command_callback(mock_command)
        
        result = panel.handle_key("enter")
        
        # 对于命令，不应该调用提交回调，而是执行命令
        assert mock_submit.called is False
        # 对于特殊命令如help，会返回结果
        assert result is not None
    
    def test_handle_key_enter_text(self):
        """测试回车键处理（普通文本）"""
        panel = InputPanel()
        
        # 设置输入为普通文本
        panel.input_buffer.set_text("hello world")
        
        # 设置提交回调
        mock_submit = Mock()
        panel.set_submit_callback(mock_submit)
        
        result = panel.handle_key("enter")
        
        # 验证提交回调被调用
        mock_submit.assert_called_once_with("hello world")
        assert result is None
        assert panel.input_buffer.is_empty() is True
        assert len(panel.input_history.history) == 1
    
    def test_handle_key_navigation(self):
        """测试导航键处理"""
        panel = InputPanel()
        panel.input_history.add_entry("previous input")
        
        # 测试向上键
        panel.handle_key("up")
        # 检查输入缓冲区是否更新为历史记录
        # 这里我们只验证方法不抛出异常
        
        # 测试向下键
        panel.handle_key("down")
        
        # 测试左右键
        panel.handle_key("left")
        panel.handle_key("right")
        
        # 测试home和end
        panel.handle_key("home")
        panel.handle_key("end")
    
    def test_handle_key_editing(self):
        """测试编辑键处理"""
        panel = InputPanel()
        panel.input_buffer.set_text("hello")
        
        # 测试退格键
        panel.handle_key("backspace")
        # 缓冲区应该变为"hell"
        
        # 测试删除键
        panel.handle_key("delete")
        # 在当前位置删除字符
        
        # 测试字符输入
        panel.handle_key("char:w")
        # 应该在当前位置插入字符'w'
    
    def test_handle_key_tab(self):
        """测试Tab键处理"""
        panel = InputPanel()
        panel.input_buffer.set_text("/hel")  # 不完整的命令
        
        # 测试Tab自动补全（虽然实现可能不完整，但至少不报错）
        panel.handle_key("tab")
    
    def test_handle_key_enter_multiline_scenarios(self):
        """测试回车键处理的各种多行输入场景"""
        panel = InputPanel()
        
        # 测试1: 以反斜杠结尾的输入（应该继续编辑）
        panel.input_buffer.set_text("line1\\")
        result = panel.handle_key("enter")
        assert result is None
        assert panel.input_buffer.get_text() == "line1\n"
        
        # 测试2: 以空格结尾的输入（应该提交）
        panel.input_buffer.clear()
        panel.input_buffer.set_text("hello ")
        mock_submit = Mock()
        panel.set_submit_callback(mock_submit)
        
        result = panel.handle_key("enter")
        assert result is None
        mock_submit.assert_called_once_with("hello ")
        assert panel.input_buffer.is_empty() is True
        
        # 测试3: 包含换行符但不在多行模式（现在应该可以提交）- 这是主要的修复
        panel.input_buffer.clear()
        panel.input_buffer.set_text("line1\nline2")
        panel.input_buffer.multiline_mode = False
        mock_submit2 = Mock()
        panel.set_submit_callback(mock_submit2)
        
        result = panel.handle_key("enter")
        assert result is None
        mock_submit2.assert_called_once_with("line1\nline2")  # 现在应该提交
        assert panel.input_buffer.is_empty() is True  # 输入应该被清空
        
        # 测试4: 普通单行文本（应该提交）
        panel.input_buffer.clear()
        panel.input_buffer.set_text("hello world")
        mock_submit3 = Mock()
        panel.set_submit_callback(mock_submit3)
        
        result = panel.handle_key("enter")
        assert result is None
        mock_submit3.assert_called_once_with("hello world")
        assert panel.input_buffer.is_empty() is True
        
        # 测试5: 普通单行文本（应该提交）
        panel.input_buffer.clear()
        panel.input_buffer.set_text("hello world")
        mock_submit4 = Mock()
        panel.set_submit_callback(mock_submit4)
        
        result = panel.handle_key("enter")
        assert result is None
        mock_submit4.assert_called_once_with("hello world")
        assert panel.input_buffer.is_empty() is True

    def test_handle_key_multiline_toggle(self):
        """测试多行模式切换键"""
        panel = InputPanel()
        
        initial_mode = panel.input_buffer.multiline_mode
        panel.handle_key("ctrl+m")  # 切换多行模式
        assert panel.input_buffer.multiline_mode != initial_mode
    
    def test_set_processing(self):
        """测试设置处理状态"""
        panel = InputPanel()
        
        panel.set_processing(True)
        assert panel.is_processing is True
        
        panel.set_processing(False)
        assert panel.is_processing is False
    
    def test_render(self):
        """测试渲染方法"""
        panel = InputPanel()
        
        # 验证渲染方法不抛出异常
        rendered = panel.render()
        assert rendered is not None
        
        # 设置处理状态并再次渲染
        panel.set_processing(True)
        rendered = panel.render()
        assert rendered is not None

    def test_callback_event_handling(self):
        """测试回调事件处理"""
        panel = InputPanel()
        
        # 跟踪回调调用
        submit_calls = []
        command_calls = []
        
        def submit_callback(text: str) -> None:
            submit_calls.append(text)
        
        def command_callback(cmd: str, args: List[str]) -> None:
            command_calls.append((cmd, args))
        
        # 设置回调
        panel.set_submit_callback(submit_callback)
        panel.set_command_callback(command_callback)
        
        # 测试普通消息提交
        panel.input_buffer.set_text("hello world")
        result = panel.handle_key("enter")
        
        assert result is None  # 普通消息返回None
        assert len(submit_calls) == 1
        assert submit_calls[0] == "hello world"
        assert len(command_calls) == 0
        assert panel.input_buffer.is_empty()  # 输入应该被清空
        
        # 测试命令处理
        panel.input_buffer.set_text("/help")
        result = panel.handle_key("enter")
        
        assert result is not None  # 命令返回结果
        assert "可用命令" in result
        assert len(submit_calls) == 1  # 没有新的提交
        assert len(command_calls) == 0  # 命令通过结果返回，不通过命令回调
        assert panel.input_buffer.is_empty()  # 输入应该被清空
        
        # 测试多行输入提交
        panel.input_buffer.set_text("line1\nline2")
        result = panel.handle_key("enter")
        
        assert result is None  # 多行消息返回None
        assert len(submit_calls) == 2
        assert submit_calls[1] == "line1\nline2"
        assert len(command_calls) == 0
        assert panel.input_buffer.is_empty()  # 输入应该被清空
        
        # 测试反斜杠续行（不提交）
        panel.input_buffer.set_text("continue\\")
        result = panel.handle_key("enter")
        
        assert result is None  # 续行返回None
        assert len(submit_calls) == 2  # 没有新的提交
        assert len(command_calls) == 0
        assert not panel.input_buffer.is_empty()  # 输入不应该被清空
        assert panel.input_buffer.get_text() == "continue\n"  # 应该添加换行符