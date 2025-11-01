#!/usr/bin/env python3
"""测试ESC键修复"""

import sys
import time
import threading
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.presentation.tui.app import TUIApp
from src.infrastructure.container import get_global_container
from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.config.models.global_config import GlobalConfig
from src.infrastructure.logger.logger import set_global_config

def test_esc_key_fix():
    """测试ESC键修复"""
    print("开始测试ESC键修复...")
    
    try:
        # 创建TUI应用实例
        app = TUIApp()
        
        # 模拟进入analytics子界面
        print("模拟进入analytics子界面...")
        app._switch_to_subview("analytics")
        
        # 验证初始状态
        print(f"子界面控制器状态: {app.subview_controller.get_current_subview_name()}")
        print(f"状态管理器状态: {app.state_manager.current_subview}")
        
        # 模拟ESC键按下
        print("模拟ESC键按下...")
        result = app._handle_escape_key("escape")
        print(f"ESC键处理结果: {result}")
        
        # 验证返回主界面后的状态
        print(f"返回主界面后 - 子界面控制器状态: {app.subview_controller.get_current_subview_name()}")
        print(f"返回主界面后 - 状态管理器状态: {app.state_manager.current_subview}")
        
        # 验证状态一致性
        controller_state = app.subview_controller.get_current_subview_name()
        manager_state = app.state_manager.current_subview
        
        if controller_state == manager_state:
            print("✅ 状态同步成功！")
            return True
        else:
            print(f"❌ 状态不一致！控制器: {controller_state}, 管理器: {manager_state}")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_esc_key_fix()
    if success:
        print("测试通过！ESC键修复有效。")
    else:
        print("测试失败！需要进一步修复。")