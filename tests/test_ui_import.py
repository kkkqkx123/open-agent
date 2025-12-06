"""测试UI消息系统导入

仅测试UI消息系统的基本导入功能。
"""

def test_import_ui_interfaces():
    """测试UI接口导入"""
    try:
        from src.interfaces.ui.messages import (
            IUIMessage,
            IUIMessageRenderer,
            IUIMessageAdapter,
            IUIMessageManager,
            IUIMessageController
        )
        print("✓ UI接口导入成功")
        return True
    except Exception as e:
        print(f"✗ UI接口导入失败: {e}")
        return False

def test_import_ui_messages():
    """测试UI消息类导入"""
    try:
        from src.adapters.ui.messages import (
            BaseUIMessage,
            UserUIMessage,
            AssistantUIMessage,
            SystemUIMessage,
            ToolUIMessage,
            WorkflowUIMessage
        )
        print("✓ UI消息类导入成功")
        return True
    except Exception as e:
        print(f"✗ UI消息类导入失败: {e}")
        return False

def test_import_ui_manager():
    """测试UI消息管理器导入"""
    try:
        from src.adapters.ui.message_manager import UIMessageManager, DefaultUIMessageRenderer
        print("✓ UI消息管理器导入成功")
        return True
    except Exception as e:
        print(f"✗ UI消息管理器导入失败: {e}")
        return False

def test_import_ui_controller():
    """测试TUI消息控制器导入"""
    try:
        from src.adapters.tui.ui_message_controller import TUIUIMessageController
        print("✓ TUI消息控制器导入成功")
        return True
    except Exception as e:
        print(f"✗ TUI消息控制器导入失败: {e}")
        return False

def test_basic_ui_message_creation():
    """测试基本UI消息创建"""
    try:
        from src.adapters.ui.messages import UserUIMessage
        
        # 创建一个简单的用户消息
        message = UserUIMessage(content="测试消息")
        
        # 验证基本属性
        assert message.message_id is not None
        assert message.message_type == "user"
        assert message.content == "测试消息"
        assert message.display_content == "测试消息"
        
        print("✓ 基本UI消息创建成功")
        return True
    except Exception as e:
        print(f"✗ 基本UI消息创建失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试UI消息系统导入...")
    
    results = []
    results.append(test_import_ui_interfaces())
    results.append(test_import_ui_messages())
    results.append(test_import_ui_manager())
    results.append(test_import_ui_controller())
    results.append(test_basic_ui_message_creation())
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有导入测试通过!")
    else:
        print("✗ 部分导入测试失败")