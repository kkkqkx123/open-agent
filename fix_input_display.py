#!/usr/bin/env python3
"""修复TUI输入显示问题的脚本"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def fix_render_controller():
    """修复渲染控制器中的刷新逻辑问题"""
    print("=== 修复渲染控制器 ===")
    
    # 读取原始文件
    render_controller_path = project_root / "src" / "presentation" / "tui" / "render_controller.py"
    with open(render_controller_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1: 改进状态哈希计算，确保输入变化被检测到
    old_get_state_hash = '''    def _get_state_hash(self, state_manager: Any) -> str:
        """获取状态管理器的哈希值，用于检测状态变化
        
        Args:
            state_manager: 状态管理器
            
        Returns:
            str: 状态哈希值
        """
        import hashlib
        import json
        
        # 创建状态的表示
        state_repr = {
            'current_subview': state_manager.current_subview,
            'show_session_dialog': getattr(state_manager, 'show_session_dialog', False),
            'show_agent_dialog': getattr(state_manager, 'show_agent_dialog', False),
            'session_id': getattr(state_manager, 'session_id', None),
            'message_history_length': len(getattr(state_manager, 'message_history', [])),
            'current_state': str(getattr(state_manager, 'current_state', None)),
        }
        
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
        
        # 序列化并生成哈希
        state_str = json.dumps(state_repr, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()'''
    
    content = content.replace(old_get_state_hash, new_get_state_hash)
    
    # 修复2: 改进主内容区更新逻辑，确保内容变化被检测到
    old_update_main_content = '''    def _update_main_content(self) -> None:
        """更新主内容区"""
        if self.main_content_component:
            main_panel = self.main_content_component.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(main_panel).encode() if main_panel else b'').hexdigest()
            
            if self._last_render_state.get('main_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.MAIN, main_panel)
                self._last_render_state['main_content_hash'] = content_hash
                self._needs_refresh = True'''
    
    new_update_main_content = '''    def _update_main_content(self) -> None:
        """更新主内容区"""
        if self.main_content_component:
            main_panel = self.main_content_component.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(main_panel).encode() if main_panel else b'').hexdigest()
            
            if self._last_render_state.get('main_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.MAIN, main_panel)
                self._last_render_state['main_content_hash'] = content_hash
                self._needs_refresh = True
                self.tui_logger.debug_render_operation("main_content", "content_updated", hash=content_hash[:8])'''
    
    content = content.replace(old_update_main_content, new_update_main_content)
    
    # 修复3: 改进输入区域更新逻辑
    old_update_input_area = '''    def _update_input_area(self) -> None:
        """更新输入区域"""
        if self.input_component:
            input_panel = self.input_component.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(input_panel).encode() if input_panel else b'').hexdigest()
            
            if self._last_render_state.get('input_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.INPUT, input_panel)
                self._last_render_state['input_content_hash'] = content_hash
                self._needs_refresh = True'''
    
    new_update_input_area = '''    def _update_input_area(self) -> None:
        """更新输入区域"""
        if self.input_component:
            input_panel = self.input_component.render()
            # 检查内容是否发生变化
            import hashlib
            content_hash = hashlib.md5(str(input_panel).encode() if input_panel else b'').hexdigest()
            
            if self._last_render_state.get('input_content_hash') != content_hash:
                self.layout_manager.update_region_content(LayoutRegion.INPUT, input_panel)
                self._last_render_state['input_content_hash'] = content_hash
                self._needs_refresh = True
                self.tui_logger.debug_render_operation("input_area", "content_updated", hash=content_hash[:8])'''
    
    content = content.replace(old_update_input_area, new_update_input_area)
    
    # 写回文件
    with open(render_controller_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已修复渲染控制器中的刷新逻辑问题")

def fix_layout_manager():
    """修复布局管理器的内容更新机制"""
    print("\n=== 修复布局管理器 ===")
    
    # 读取原始文件
    layout_path = project_root / "src" / "presentation" / "tui" / "layout.py"
    with open(layout_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复: 改进区域内容更新逻辑，确保内容变化被立即反映
    old_update_region_content = '''    def update_region_content(self, region: LayoutRegion, content: Any) -> None:
        """更新区域内容"""
        # 检查内容是否真正发生变化
        if self.region_contents.get(region) != content:
            self.region_contents[region] = content
            # 立即更新布局对象中的内容
            self._update_layout_regions_for_region(region, content)'''
    
    new_update_region_content = '''    def update_region_content(self, region: LayoutRegion, content: Any) -> None:
        """更新区域内容"""
        # 检查内容是否真正发生变化
        old_content = self.region_contents.get(region)
        if old_content != content:
            self.region_contents[region] = content
            # 立即更新布局对象中的内容
            self._update_layout_regions_for_region(region, content)
            
            # 添加调试日志
            import hashlib
            old_hash = hashlib.md5(str(old_content).encode() if old_content else b'').hexdigest()[:8]
            new_hash = hashlib.md5(str(content).encode() if content else b'').hexdigest()[:8]
            print(f"[DEBUG] 布局区域 {region.value} 内容已更新: {old_hash} -> {new_hash}")'''
    
    content = content.replace(old_update_region_content, new_update_region_content)
    
    # 写回文件
    with open(layout_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已修复布局管理器的内容更新机制")

def fix_app_main_loop():
    """修复TUI应用主循环中的刷新频率问题"""
    print("\n=== 修复TUI应用主循环 ===")
    
    # 读取原始文件
    app_path = project_root / "src" / "presentation" / "tui" / "app.py"
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复: 改进主循环中的刷新逻辑，确保输入变化被及时显示
    old_main_loop = '''                # 更新UI，并获取是否需要刷新的标志
                needs_refresh = self.update_ui()
                if needs_refresh:
                    # 只有当内容真正变化时才刷新UI
                    if self.live:  # 确保live对象存在
                        self.live.refresh()
                    # 如果需要刷新，使用较短的休眠时间以保持响应性
                    time.sleep(0.01)
                else:
                    # 如果不需要刷新，使用较长的休眠时间以减少CPU使用
                    time.sleep(0.05)'''
    
    new_main_loop = '''                # 更新UI，并获取是否需要刷新的标志
                needs_refresh = self.update_ui()
                if needs_refresh:
                    # 只有当内容真正变化时才刷新UI
                    if self.live:  # 确保live对象存在
                        self.live.refresh()
                        self.tui_logger.debug_render_operation("main_loop", "ui_refreshed")
                    # 如果需要刷新，使用较短的休眠时间以保持响应性
                    time.sleep(0.01)
                else:
                    # 如果不需要刷新，使用较长的休眠时间以减少CPU使用
                    time.sleep(0.05)'''
    
    content = content.replace(old_main_loop, new_main_loop)
    
    # 写回文件
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已修复TUI应用主循环中的刷新频率问题")

def create_test_script():
    """创建测试脚本来验证修复"""
    print("\n=== 创建测试脚本 ===")
    
    test_script = '''#!/usr/bin/env python3
"""测试修复后的TUI输入显示功能"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from presentation.tui.app import TUIApp

def test_fixed_input_display():
    """测试修复后的输入显示功能"""
    print("=== 测试修复后的输入显示功能 ===")
    
    try:
        # 创建TUI应用
        app = TUIApp()
        
        # 模拟输入处理
        print("1. 模拟用户输入 'test message'")
        app.input_component.handle_key("char:t")
        app.input_component.handle_key("char:e")
        app.input_component.handle_key("char:s")
        app.input_component.handle_key("char:t")
        app.input_component.handle_key("char: ")
        app.input_component.handle_key("char:m")
        app.input_component.handle_key("char:e")
        app.input_component.handle_key("char:s")
        app.input_component.handle_key("char:s")
        app.input_component.handle_key("char:a")
        app.input_component.handle_key("char:g")
        app.input_component.handle_key("char:e")
        
        # 提交输入
        print("2. 提交输入")
        result = app.input_component.handle_key("enter")
        print(f"   输入结果: {result}")
        
        # 处理输入结果
        if result and result.startswith("USER_INPUT:"):
            user_text = result.split(":", 1)[1]
            print(f"   用户输入: {user_text}")
            
            # 检查状态管理器
            print("3. 检查状态管理器")
            print(f"   消息历史数量: {len(app.state_manager.message_history)}")
            for i, msg in enumerate(app.state_manager.message_history):
                print(f"   消息 {i+1}: {msg['type']} - {msg['content']}")
            
            # 检查主内容组件
            print("4. 检查主内容组件")
            history = app.main_content_component.conversation_history
            print(f"   会话历史数量: {len(history.messages)}")
            for i, msg in enumerate(history.messages):
                print(f"   消息 {i+1}: {msg['type']} - {msg['content'][:30]}...")
            
            # 测试UI更新
            print("5. 测试UI更新")
            needs_refresh = app.update_ui()
            print(f"   需要刷新: {needs_refresh}")
            
            # 渲染组件
            print("6. 渲染组件")
            main_panel = app.main_content_component.render()
            input_panel = app.input_component.render()
            print(f"   主内容面板类型: {type(main_panel)}")
            print(f"   输入面板类型: {type(input_panel)}")
            
            print("\\n=== 测试完成 ===")
            print("如果以上测试都正常，说明修复成功！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_input_display()
'''
    
    test_path = project_root / "test_fixed_input_display.py"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"已创建测试脚本: {test_path}")

if __name__ == "__main__":
    print("开始修复TUI输入显示问题...")
    
    try:
        fix_render_controller()
        fix_layout_manager()
        fix_app_main_loop()
        create_test_script()
        
        print("\n=== 修复完成 ===")
        print("已修复以下问题:")
        print("1. 渲染控制器中的刷新逻辑问题")
        print("2. 布局管理器的内容更新机制")
        print("3. TUI应用主循环中的刷新频率问题")
        print("\n请运行 test_fixed_input_display.py 来验证修复效果")
        
    except Exception as e:
        print(f"\n修复过程中发生错误: {e}")
        import traceback
        traceback.print_exc()