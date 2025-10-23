import asyncio
from src.presentation.tui.components.input_panel import InputPanel
from src.presentation.tui.config import get_tui_config


class MockSubmitCallback:
    """模拟提交回调"""
    def __init__(self):
        self.submitted_texts = []
    
    def callback(self, text: str):
        """提交回调"""
        print(f"收到提交的文本: {text}")
        self.submitted_texts.append(text)


def test_enter_key_submission():
    """测试Enter键提交功能"""
    print("=== 测试Enter键提交功能 ===")
    
    # 创建输入面板 - 使用默认配置
    config = get_tui_config()
    input_panel = InputPanel(config)
    
    # 创建模拟回调
    mock_callback = MockSubmitCallback()
    
    # 设置提交回调
    input_panel.set_submit_callback(mock_callback.callback)
    
    # 模拟输入文本
    test_text = "Hello, world!"
    print(f"输入文本: {test_text}")
    
    # 逐个字符输入
    for char in test_text:
        result = input_panel.handle_key(f"char:{char}")
        print(f"输入字符 '{char}'，返回: {result}")
    
    # 检查输入缓冲区
    current_text = input_panel.input_buffer.get_text()
    print(f"当前缓冲区文本: '{current_text}'")
    
    # 模拟按Enter键
    print("按Enter键...")
    result = input_panel.handle_key("enter")
    print(f"Enter键返回: {result}")
    
    # 检查是否已提交
    print(f"已提交的文本数量: {len(mock_callback.submitted_texts)}")
    if mock_callback.submitted_texts:
        print(f"提交的文本: {mock_callback.submitted_texts[0]}")
    
    # 检查输入缓冲区是否已清空
    current_text_after = input_panel.input_buffer.get_text()
    print(f"提交后缓冲区文本: '{current_text_after}'")
    
    # 验证结果
    if mock_callback.submitted_texts and mock_callback.submitted_texts[0] == test_text:
        print("✓ Enter键提交功能正常工作")
        return True
    else:
        print("✗ Enter键提交功能存在问题")
        return False


def test_multiline_enter_handling():
    """测试多行模式下的Enter键处理"""
    print("\n=== 测试多行模式下的Enter键处理 ===")
    
    # 创建输入面板 - 使用默认配置
    config = get_tui_config()
    input_panel = InputPanel(config)
    
    # 创建模拟回调
    mock_callback = MockSubmitCallback()
    input_panel.set_submit_callback(mock_callback.callback)
    
    # 模拟输入文本
    test_text = "Hello"
    print(f"输入文本: {test_text}")
    
    # 逐个字符输入
    for char in test_text:
        input_panel.handle_key(f"char:{char}")
    
    # 切换到多行模式
    input_panel.handle_key("ctrl+m")
    print("切换到多行模式")
    
    # 再按Enter键（应为换行而不是提交）
    result = input_panel.handle_key("enter")
    print(f"多行模式下Enter键返回: {result}")
    
    # 检查输入缓冲区
    current_text = input_panel.input_buffer.get_text()
    print(f"多行模式下缓冲区文本: '{repr(current_text)}'")
    
    # 如果缓冲区包含换行符，说明Enter键被正确处理为换行
    if '\n' in current_text and not mock_callback.submitted_texts:
        print("✓ 多行模式下Enter键换行功能正常")
        
        # 继续测试提交功能：在空行按Enter应该提交
        result2 = input_panel.handle_key("enter")
        print(f"空行下Enter键返回: {result2}")
        current_text2 = input_panel.input_buffer.get_text()
        print(f"提交后缓冲区文本: '{repr(current_text2)}'")
        print(f"已提交的文本数量: {len(mock_callback.submitted_texts)}")
        
        if mock_callback.submitted_texts and mock_callback.submitted_texts[0] == "Hello":
            print("✓ 多行模式下提交功能正常")
            return True
        else:
            print("✗ 多行模式下提交功能存在问题")
            return False
    else:
        print("✗ 多行模式下Enter键处理存在问题")
        return False


if __name__ == "__main__":
    success1 = test_enter_key_submission()
    success2 = test_multiline_enter_handling()
    
    if success1 and success2:
        print("\n✓ 所有测试通过")
    else:
        print("\n✗ 部分测试失败")