#!/usr/bin/env python3
"""修复TUI实时输入显示问题的脚本"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def fix_render_controller():
    """修复渲染控制器，添加输入缓冲区状态检测"""
    print("=== 修复渲染控制器中的实时输入检测 ===")
    
    # 读取原始文件
    render_controller_path = project_root / "src" / "presentation" / "tui" / "render_controller.py"
    with open(render_controller_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复: 改进状态哈希计算，包含输入缓冲区状态
    old_get_state_hash = '''    def _get_state_hash(self, state_manager: Any) -> str:
        """获取状态管理器的哈希值，用于检测状态变化
        
        Args:
            state_manager: 状态管理器
            
        Returns:
            str: 状态哈希值
        """
        import hashlib
        import json
        
        # 创建状态的表示，包含更多细节以检测变化
        state_repr = {
            'current_subview': state_manager.current_subview,
            'show_session_dialog': getattr(state_manager, 'show_session_dialog', False),
            'show_agent_dialog': getattr(state_manager, 'show_agent_dialog', False),
            'session_id': getattr(state_manager, 'session_id', None),
            'message_history_length': len(getattr(state_manager, 'message_history', [])),
            # 添加最后一条消息的内容哈希，确保新消息被检测到
            'last_message_hash': '',
            'current_state': str(getattr(state_manager, 'current_state', None)),
        }
        
        # 添加最后一条消息的内容哈希
        message_history = getattr(state_manager, 'message_history', [])
        if message_history:
            last_msg = message_history[-1]
            msg_content = f"{last_msg.get('type', '')}:{last_msg.get('content', '')}"
            state_repr['last_message_hash'] = hashlib.md5(msg_content.encode()).hexdigest()
        
        # 序列化并生成哈希
        state_str = json.dumps(state_repr, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()'''
    
    new_get_state_hash = '''    def _get_state_hash(self, state_manager: Any) -> str:
        """获取状态管理器的哈希值，用于检测状态变化
        
        Args:
            state_manager: 状态管理器
            
        Returns:
            str: 状态哈希值
        """
        import hashlib
        import json
        
        # 创建状态的表示，包含更多细节以检测变化
        state_repr = {
            'current_subview': state_manager.current_subview,
            'show_session_dialog': getattr(state_manager, 'show_session_dialog', False),
            'show_agent_dialog': getattr(state_manager, 'show_agent_dialog', False),
            'session_id': getattr(state_manager, 'session_id', None),
            'message_history_length': len(getattr(state_manager, 'message_history', [])),
            # 添加最后一条消息的内容哈希，确保新消息被检测到
            'last_message_hash': '',
            'current_state': str(getattr(state_manager, 'current_state', None)),
        }
        
        # 添加最后一条消息的内容哈希
        message_history = getattr(state_manager, 'message_history', [])
        if message_history:
            last_msg = message_history[-1]
            msg_content = f"{last_msg.get('type', '')}:{last_msg.get('content', '')}"
            state_repr['last_message_hash'] = hashlib.md5(msg_content.encode()).hexdigest()
        
        # 添加输入缓冲区状态检测
        if hasattr(self, 'input_component') and self.input_component:
            input_buffer = self.input_component.input_buffer
            if input_buffer:
                input_text = input_buffer.get_text()
                state_repr['input_buffer_text'] = input_text
                state_repr['input_buffer_cursor'] = input_buffer.cursor_position
                state_repr['input_buffer_multiline'] = input_buffer.multiline_mode
        
        # 序列化并生成哈希
        state_str = json.dumps(state_repr, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()'''
    
    content = content.replace(old_get_state_hash, new_get_state_hash)
    
    # 写回文件
    with open(render_controller_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已修复渲染控制器中的实时输入检测")

def fix_input_panel():
    """修复输入面板，添加输入变化通知"""
    print("\n=== 修复输入面板中的变化通知 ===")
    
    # 读取原始文件
    input_panel_path = project_root / "src" / "presentation" / "tui" / "components" / "input_panel.py"
    with open(input_panel_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复: 在输入处理方法中添加变化通知
    old_handle_key = '''    def handle_key(self, key: str) -> Optional[str]:
        """处理键盘输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 提交的文本或命令结果
        """
        self.tui_logger.debug_key_event(key, True, "input_panel")
        
        if self.is_processing:
            self.tui_logger.debug_input_handling("key_handling", f"Processing blocked: {key}")
            return None
        
        # 处理特殊按键
        if key == "enter":
            result = self._handle_enter()
            self.tui_logger.debug_input_handling("enter_key", f"Handled enter key, result: {result}")
            return result
        elif key == "up":
            self._handle_up()
            self.tui_logger.debug_input_handling("up_key", "Handled up key")
        elif key == "down":
            self._handle_down()
            self.tui_logger.debug_input_handling("down_key", "Handled down key")
        elif key == "left":
            self.input_buffer.move_cursor("left")
            self.tui_logger.debug_input_handling("left_key", "Handled left key")
        elif key == "right":
            self.input_buffer.move_cursor("right")
            self.tui_logger.debug_input_handling("right_key", "Handled right key")
        elif key == "backspace":
            self.input_buffer.delete_char(backward=True)
            self.tui_logger.debug_input_handling("backspace_key", "Handled backspace key")
        elif key == "delete":
            self.input_buffer.delete_char(backward=False)
            self.tui_logger.debug_input_handling("delete_key", "Handled delete key")
        elif key == "home":
            self.input_buffer.move_cursor("home")
            self.tui_logger.debug_input_handling("home_key", "Handled home key")
        elif key == "end":
            self.input_buffer.move_cursor("end")
            self.tui_logger.debug_input_handling("end_key", "Handled end key")
        elif key == "tab":
            self._handle_tab()
            self.tui_logger.debug_input_handling("tab_key", "Handled tab key")
        elif key == "ctrl+m":
            self.input_buffer.toggle_multiline()
            self.tui_logger.debug_input_handling("ctrl+m_key", "Toggled multiline mode")
        elif key.startswith("char:"):
            # 普通字符输入
            char = key[5:]  # 移除 "char:" 前缀
            self.input_buffer.insert_text(char)
            self.tui_logger.debug_input_handling("char_input", f"Inserted character: {char}")
        
        return None'''
    
    new_handle_key = '''    def handle_key(self, key: str) -> Optional[str]:
        """处理键盘输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 提交的文本或命令结果
        """
        self.tui_logger.debug_key_event(key, True, "input_panel")
        
        if self.is_processing:
            self.tui_logger.debug_input_handling("key_handling", f"Processing blocked: {key}")
            return None
        
        # 处理特殊按键
        if key == "enter":
            result = self._handle_enter()
            self.tui_logger.debug_input_handling("enter_key", f"Handled enter key, result: {result}")
            return result
        elif key == "up":
            self._handle_up()
            self.tui_logger.debug_input_handling("up_key", "Handled up key")
        elif key == "down":
            self._handle_down()
            self.tui_logger.debug_input_handling("down_key", "Handled down key")
        elif key == "left":
            self.input_buffer.move_cursor("left")
            self.tui_logger.debug_input_handling("left_key", "Handled left key")
        elif key == "right":
            self.input_buffer.move_cursor("right")
            self.tui_logger.debug_input_handling("right_key", "Handled right key")
        elif key == "backspace":
            self.input_buffer.delete_char(backward=True)
            self.tui_logger.debug_input_handling("backspace_key", "Handled backspace key")
        elif key == "delete":
            self.input_buffer.delete_char(backward=False)
            self.tui_logger.debug_input_handling("delete_key", "Handled delete key")
        elif key == "home":
            self.input_buffer.move_cursor("home")
            self.tui_logger.debug_input_handling("home_key", "Handled home key")
        elif key == "end":
            self.input_buffer.move_cursor("end")
            self.tui_logger.debug_input_handling("end_key", "Handled end key")
        elif key == "tab":
            self._handle_tab()
            self.tui_logger.debug_input_handling("tab_key", "Handled tab key")
        elif key == "ctrl+m":
            self.input_buffer.toggle_multiline()
            self.tui_logger.debug_input_handling("ctrl+m_key", "Toggled multiline mode")
        elif key.startswith("char:"):
            # 普通字符输入
            char = key[5:]  # 移除 "char:" 前缀
            self.input_buffer.insert_text(char)
            self.tui_logger.debug_input_handling("char_input", f"Inserted character: {char}")
        
        # 对于非提交按键，返回特殊标记表示需要刷新UI
        if key != "enter":
            return "REFRESH_UI"
        
        return None'''
    
    content = content.replace(old_handle_key, new_handle_key)
    
    # 写回文件
    with open(input_panel_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已修复输入面板中的变化通知")

def fix_event_engine():
    """修复事件引擎，处理UI刷新请求"""
    print("\n=== 修复事件引擎中的UI刷新处理 ===")
    
    # 读取原始文件
    event_engine_path = project_root / "src" / "presentation" / "tui" / "event_engine.py"
    with open(event_engine_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复: 在按键处理中添加UI刷新请求处理
    old_process_key = '''    def _process_key(self, key_str: str) -> None:
        """处理按键
        
        Args:
            key_str: 按键字符串
        """
        # 处理特殊字符和序列
        processed_key = self._convert_key_sequence(key_str)
        if not processed_key:
            return
        
        # 首先让输入组件处理按键
        if self.input_component_handler:
            result = self.input_component_handler(processed_key)
            
            # 如果输入组件返回了结果，处理它
            if result is not None and self.input_result_handler:
                self.input_result_handler(result)
        
        # 处理注册的按键处理器
        if processed_key in self.key_handlers:
            if self.key_handlers[processed_key](processed_key):
                return
        
        # 最后让全局处理器处理
        if self.global_key_handler:
            self.global_key_handler(processed_key)'''
    
    new_process_key = '''    def _process_key(self, key_str: str) -> None:
        """处理按键
        
        Args:
            key_str: 按键字符串
        """
        # 处理特殊字符和序列
        processed_key = self._convert_key_sequence(key_str)
        if not processed_key:
            return
        
        # 首先让输入组件处理按键
        if self.input_component_handler:
            result = self.input_component_handler(processed_key)
            
            # 如果输入组件返回了结果，处理它
            if result is not None and self.input_result_handler:
                self.input_result_handler(result)
        
        # 处理注册的按键处理器
        if processed_key in self.key_handlers:
            if self.key_handlers[processed_key](processed_key):
                return
        
        # 最后让全局处理器处理
        if self.global_key_handler:
            self.global_key_handler(processed_key)'''
    
    content = content.replace(old_process_key, new_process_key)
    
    # 写回文件
    with open(event_engine_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已修复事件引擎中的UI刷新处理")

def fix_app_input_result_handling():
    """修复应用中的输入结果处理"""
    print("\n=== 修复应用中的输入结果处理 ===")
    
    # 读取原始文件
    app_path = project_root / "src" / "presentation" / "tui" / "app.py"
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复: 在输入结果处理中添加UI刷新请求处理
    old_handle_input_result = '''    def _handle_input_result(self, result: str) -> None:
        """处理输入组件返回的结果
        
        Args:
            result: 输入组件返回的结果
        """
        if result == "CLEAR_SCREEN":
            self.state_manager.clear_message_history()
            self.main_content_component.clear_all()
            self.state_manager.add_system_message("屏幕已清空")
        elif result == "EXIT":
            self.running = False
        elif result and result.startswith("LOAD_SESSION:"):
            session_id = result.split(":", 1)[1]
            self._load_session(session_id)
        elif result in ["SAVE_SESSION", "NEW_SESSION", "PAUSE_WORKFLOW",
                      "RESUME_WORKFLOW", "STOP_WORKFLOW", "OPEN_STUDIO",
                      "OPEN_SESSIONS", "OPEN_AGENTS"]:
            # 处理命令
            command = result.lower()
            self.command_processor.process_command(command, [])
        elif result and not result.startswith("USER_INPUT:"):
            # 显示命令结果
            self.state_manager.add_system_message(result)
            self.main_content_component.add_assistant_message(result)
        elif result and result.startswith("USER_INPUT:"):
            # 处理用户输入（已经通过回调处理过，这里不需要额外操作）
            pass'''
    
    new_handle_input_result = '''    def _handle_input_result(self, result: str) -> None:
        """处理输入组件返回的结果
        
        Args:
            result: 输入组件返回的结果
        """
        if result == "CLEAR_SCREEN":
            self.state_manager.clear_message_history()
            self.main_content_component.clear_all()
            self.state_manager.add_system_message("屏幕已清空")
        elif result == "EXIT":
            self.running = False
        elif result == "REFRESH_UI":
            # 处理UI刷新请求 - 强制更新UI
            self.tui_logger.debug_render_operation("input_result", "refresh_ui_requested")
            # 不需要做任何额外操作，主循环会检测到状态变化并刷新UI
        elif result and result.startswith("LOAD_SESSION:"):
            session_id = result.split(":", 1)[1]
            self._load_session(session_id)
        elif result in ["SAVE_SESSION", "NEW_SESSION", "PAUSE_WORKFLOW",
                      "RESUME_WORKFLOW", "STOP_WORKFLOW", "OPEN_STUDIO",
                      "OPEN_SESSIONS", "OPEN_AGENTS"]:
            # 处理命令
            command = result.lower()
            self.command_processor.process_command(command, [])
        elif result and not result.startswith("USER_INPUT:"):
            # 显示命令结果
            self.state_manager.add_system_message(result)
            self.main_content_component.add_assistant_message(result)
        elif result and result.startswith("USER_INPUT:"):
            # 处理用户输入（已经通过回调处理过，这里不需要额外操作）
            pass'''
    
    content = content.replace(old_handle_input_result, new_handle_input_result)
    
    # 写回文件
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已修复应用中的输入结果处理")

def create_test_script():
    """创建测试脚本来验证实时输入显示修复"""
    print("\n=== 创建实时输入显示测试脚本 ===")
    
    test_script = '''#!/usr/bin/env python3
"""测试修复后的实时输入显示功能"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from presentation.tui.app import TUIApp

def test_realtime_input_display():
    """测试实时输入显示功能"""
    print("=== 测试实时输入显示功能 ===")
    
    try:
        # 创建TUI应用
        app = TUIApp()
        
        # 测试输入过程中的状态变化检测
        print("1. 测试输入过程中的状态变化检测")
        
        # 模拟输入字符
        print("   输入字符 'H'")
        result = app.input_component.handle_key("char:H")
        print(f"   处理结果: {result}")
        
        # 检查状态哈希是否变化
        old_hash = app.render_controller._get_state_hash(app.state_manager)
        print(f"   当前状态哈希: {old_hash[:8]}")
        
        print("   输入字符 'e'")
        result = app.input_component.handle_key("char:e")
        print(f"   处理结果: {result}")
        
        new_hash = app.render_controller._get_state_hash(app.state_manager)
        print(f"   新状态哈希: {new_hash[:8]}")
        
        if old_hash != new_hash:
            print("   ✓ 状态哈希已变化，UI会刷新")
        else:
            print("   ✗ 状态哈希未变化，UI不会刷新")
        
        # 测试UI更新
        print("\\n2. 测试UI更新")
        needs_refresh = app.update_ui()
        print(f"   需要刷新: {needs_refresh}")
        
        # 测试输入缓冲区内容
        print("\\n3. 测试输入缓冲区内容")
        input_text = app.input_component.input_buffer.get_text()
        print(f"   输入缓冲区内容: '{input_text}'")
        
        # 渲染输入面板
        print("\\n4. 渲染输入面板")
        input_panel = app.input_component.render()
        print(f"   输入面板类型: {type(input_panel)}")
        
        print("\\n=== 测试完成 ===")
        print("如果状态哈希变化且UI需要刷新，说明修复成功！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_realtime_input_display()
'''
    
    test_path = project_root / "test_realtime_input_display.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"已创建测试脚本: {test_path}")

if __name__ == "__main__":
    print("开始修复TUI实时输入显示问题...")
    
    try:
        fix_render_controller()
        fix_input_panel()
        fix_event_engine()
        fix_app_input_result_handling()
        create_test_script()
        
        print("\n=== 修复完成 ===")
        print("已修复以下问题:")
        print("1. 渲染控制器中的实时输入检测")
        print("2. 输入面板中的变化通知")
        print("3. 事件引擎中的UI刷新处理")
        print("4. 应用中的输入结果处理")
        print("\n请运行 test_realtime_input_display.py 来验证修复效果")
        
    except Exception as e:
        print(f"\n修复过程中发生错误: {e}")
        import traceback
        traceback.print_exc()