#!/usr/bin/env python3
"""测试 Anthropic 客户端修复"""

import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_anthropic_client():
    """测试 Anthropic 客户端初始化"""
    try:
        from llm.config import AnthropicConfig
        from llm.clients.anthropic_client import AnthropicClient
        
        # 创建一个简单的配置
        config = AnthropicConfig(
            model_type='anthropic',
            model_name='claude-3-5-sonnet-20241022',
            api_key='test-key'
        )
        
        # 尝试创建客户端
        client = AnthropicClient(config)
        print('✓ AnthropicClient 创建成功')
        return True
        
    except Exception as e:
        print(f'✗ 错误: {e}')
        return False

if __name__ == "__main__":
    success = test_anthropic_client()
    if success:
        print("\n所有测试通过！")
    else:
        print("\n测试失败！")
        sys.exit(1)