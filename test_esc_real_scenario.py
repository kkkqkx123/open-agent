#!/usr/bin/env python3
"""ESC键真实场景测试"""

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

def test_esc_real_scenario():
    """测试ESC键在真实场景下的行为"""
    print("开始ESC键真实场景测试...")
    
    try:
        # 创建TUI应用实例
        app = TUIApp()
        
        # 模拟真实的使用流程
        print("\n1. 模拟用户进入analytics子界面")
        app._switch_to_subview("analytics")
        
        # 验证状态
        controller_state = app.subview_controller.get_current_subview_name()
        manager_state = app.state_manager.current_subview
        
        print(f"   子界面控制器状态: {controller_state}")
        print(f"   状态管理器状态: {manager_state}")
        
        assert controller_state == "analytics"
        assert manager_state == "analytics"
        print("   ✅ 进入analytics子界面成功")
        
        print("\n2. 模拟用户按下ESC键返回主界面")
        
        # 模拟事件引擎调用全局按键处理
        result = app._handle_global_key("escape")
        
        print(f"   ESC键处理结果: {result}")
        
        # 验证返回主界面后的状态
        controller_state = app.subview_controller.get_current_subview_name()
        manager_state = app.state_manager.current_subview
        
        print(f"   返回主界面后 - 子界面控制器状态: {controller_state}")
        print(f"   返回主界面后 - 状态管理器状态: {manager_state}")
        
        assert result == True  # ESC键应该被处理
        assert controller_state is None
        assert manager_state is None
        print("   ✅ 返回主界面成功")
        
        print("\n3. 模拟用户再次进入不同子界面")
        app._switch_to_subview("visualization")
        
        controller_state = app.subview_controller.get_current_subview_name()
        manager_state = app.state_manager.current_subview
        
        print(f"   进入visualization子界面 - 控制器状态: {controller_state}")
        print(f"   进入visualization子界面 - 管理器状态: {manager_state}")
        
        assert controller_state == "visualization"
        assert manager_state == "visualization"
        print("   ✅ 进入visualization子界面成功")
        
        print("\n4. 再次测试ESC键返回")
        result = app._handle_global_key("escape")
        
        controller_state = app.subview_controller.get_current_subview_name()
        manager_state = app.state_manager.current_subview
        
        print(f"   ESC键处理结果: {result}")
        print(f"   返回主界面后 - 控制器状态: {controller_state}")
        print(f"   返回主界面后 - 管理器状态: {manager_state}")
        
        assert result == True
        assert controller_state is None
        assert manager_state is None
        print("   ✅ 再次返回主界面成功")
        
        print("\n5. 测试状态一致性")
        # 测试所有子界面
        for subview in ["analytics", "visualization", "system", "errors"]:
            app._switch_to_subview(subview)
            
            # 验证进入子界面
            assert app.subview_controller.get_current_subview_name() == subview
            assert app.state_manager.current_subview == subview
            
            # 测试ESC键返回
            result = app._handle_global_key("escape")
            assert result == True
            
            # 验证返回主界面
            assert app.subview_controller.get_current_subview_name() is None
            assert app.state_manager.current_subview is None
            
            print(f"   ✅ {subview}子界面ESC键功能正常")
        
        return True
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_esc_real_scenario()
    if success:
        print("\n🎉 真实场景测试通过！ESC键修复在实际应用中有效。")
    else:
        print("\n❌ 真实场景测试失败！需要进一步修复。")