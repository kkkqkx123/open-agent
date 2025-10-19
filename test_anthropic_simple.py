#!/usr/bin/env python3
"""简单测试 Anthropic 客户端修复"""

def test_anthropic_client():
    """测试 Anthropic 客户端初始化"""
    try:
        from langchain_anthropic import ChatAnthropic
        
        # 尝试创建 ChatAnthropic 实例，使用与我们代码相同的参数
        client = ChatAnthropic(
            model='claude-3-5-sonnet-20241022',
            api_key='test-key',
            temperature=0.7,
            max_tokens=1000,
            timeout=30,
            max_retries=3,
            default_headers={},
            model_kwargs={}
        )
        print('✓ ChatAnthropic 创建成功，参数正确')
        return True
        
    except Exception as e:
        print(f'✗ 错误: {e}')
        return False

if __name__ == "__main__":
    success = test_anthropic_client()
    if success:
        print("\n测试通过！Anthropic 客户端参数修复成功。")
    else:
        print("\n测试失败！")