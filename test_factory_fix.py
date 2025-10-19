#!/usr/bin/env python3
"""测试工厂修复的简单脚本"""

import sys
sys.path.insert(0, '.')

try:
    from src.llm.factory import LLMFactory
    from src.llm.config import LLMClientConfig
    
    # 创建工厂实例
    factory = LLMFactory()
    print("✓ LLMFactory 创建成功")
    
    # 创建一个简单的配置
    config_dict = {
        "model_type": "mock",
        "model_name": "mock-model",
        "api_key": "test-key"
    }
    
    # 尝试创建客户端
    client = factory.create_client(config_dict)
    print("✓ Mock客户端创建成功")
    
    # 测试客户端类型
    print(f"✓ 客户端类型: {type(client).__name__}")
    
    print("\n所有测试通过！原始问题已修复。")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()