#!/usr/bin/env python3
"""ESC键修复综合测试"""

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

def test_esc_key_comprehensive():
    """综合测试ESC键功能"""
    print("开始ESC键综合测试...")
    
    try:
        # 创建TUI应用实例
        app = TUIApp()
        
        # 测试用例1: 从analytics子界面返回
        print("\n测试用例1: 从analytics子界面返回")
        app._switch_to_subview("analytics")
        assert app.subview_controller.get_current_subview_name() == "analytics"
        assert app.state_manager.current_subview == "analytics"
        
        result = app._handle_escape_key("escape")
        assert result == True
        assert app.subview_controller.get_current_subview_name() is None
        assert app.state_manager.current_subview is None
        print("✅ 测试用例1通过")
        
        # 测试用例2: 从visualization子界面返回
        print("\n测试用例2: 从visualization子界面返回")
        app._switch_to_subview("visualization")
        assert app.subview_controller.get_current_subview_name() == "visualization"
        assert app.state_manager.current_subview == "visualization"
        
        result = app._handle_escape_key("escape")
        assert result == True
        assert app.subview_controller.get_current_subview_name() is None
        assert app.state_manager.current_subview is None
        print("✅ 测试用例2通过")
        
        # 测试用例3: 从system子界面返回
        print("\n测试用例3: 从system子界面返回")
        app._switch_to_subview("system")
        assert app.subview_controller.get_current_subview_name() == "system"
        assert app.state_manager.current_subview == "system"
        
        result = app._handle_escape_key("escape")
        assert result == True
        assert app.subview_controller.get_current_subview_name() is None
        assert app.state_manager.current_subview is None
        print("✅ 测试用例3通过")
        
        # 测试用例4: 从errors子界面返回
        print("\n测试用例4: 从errors子界面返回")
        app._switch_to_subview("errors")
        assert app.subview_controller.get_current_subview_name() == "errors"
        assert app.state_manager.current_subview == "errors"
        
        result = app._handle_escape_key("escape")
        assert result == True
        assert app.subview_controller.get_current_subview_name() is None
        assert app.state_manager.current_subview is None
        print("✅ 测试用例4通过")
        
        # 测试用例5: 在主界面按ESC键（应该不处理）
        print("\n测试用例5: 在主界面按ESC键")
        assert app.subview_controller.get_current_subview_name() is None
        assert app.state_manager.current_subview is None
        
        result = app._handle_escape_key("escape")
        assert result == False  # 在主界面，ESC键不应该被处理
        print("✅ 测试用例5通过")
        
        # 测试用例6: 状态一致性验证
        print("\n测试用例6: 状态一致性验证")
        for subview in ["analytics", "visualization", "system", "errors"]:
            app._switch_to_subview(subview)
            assert app.subview_controller.get_current_subview_name() == subview
            assert app.state_manager.current_subview == subview
            
            app._handle_escape_key("escape")
            assert app.subview_controller.get_current_subview_name() is None
            assert app.state_manager.current_subview is None
            print(f"  ✅ {subview}子界面状态一致性验证通过")
        
        print("✅ 测试用例6通过")
        
        return True
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_esc_key_comprehensive()
    if success:
        print("\n🎉 所有测试通过！ESC键修复完全有效。")
    else:
        print("\n❌ 测试失败！需要进一步修复。")