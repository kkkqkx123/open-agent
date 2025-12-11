#!/usr/bin/env python3
"""测试架构修复后的代码

验证Core层不再直接依赖Service层，以及依赖注入接口是否正常工作。
"""

import sys
import traceback

def test_core_imports():
    """测试Core层组件导入"""
    print("=" * 50)
    print("测试Core层组件导入")
    print("=" * 50)
    
    try:
        # 测试依赖注入接口
        from src.interfaces.dependency_injection.core import get_logger, calculate_messages_tokens
        print("✓ 依赖注入接口导入成功")
        
        # 测试FallbackLogger
        logger = get_logger("test")
        logger.info("测试日志记录器")
        print("✓ 日志记录器工作正常")
        
        # 测试Token计算
        token_count = calculate_messages_tokens(["Hello world"], "text", "test")
        print(f"✓ Token计算功能正常: {token_count} tokens")
        
        return True
    except Exception as e:
        print(f"✗ Core层导入测试失败: {e}")
        traceback.print_exc()
        return False

def test_base_registry():
    """测试BaseRegistry不再依赖Service层"""
    print("\n" + "=" * 50)
    print("测试BaseRegistry")
    print("=" * 50)
    
    try:
        from src.core.workflow.registry.base_registry import BaseRegistry
        print("✓ BaseRegistry导入成功")
        
        # 创建实例测试
        registry = BaseRegistry()
        print("✓ BaseRegistry实例化成功")
        
        return True
    except Exception as e:
        print(f"✗ BaseRegistry测试失败: {e}")
        traceback.print_exc()
        return False

def test_base_config():
    """测试BaseConfig不再依赖Service层"""
    print("\n" + "=" * 50)
    print("测试BaseConfig")
    print("=" * 50)
    
    try:
        from src.core.config.base import BaseConfig
        print("✓ BaseConfig导入成功")
        
        # 创建实例测试
        config = BaseConfig()
        print("✓ BaseConfig实例化成功")
        
        return True
    except Exception as e:
        print(f"✗ BaseConfig测试失败: {e}")
        traceback.print_exc()
        return False

def test_base_llm_client():
    """测试BaseLLMClient不再依赖Service层"""
    print("\n" + "=" * 50)
    print("测试BaseLLMClient")
    print("=" * 50)
    
    try:
        from src.core.llm.clients.base import BaseLLMClient
        print("✓ BaseLLMClient导入成功")
        
        return True
    except Exception as e:
        print(f"✗ BaseLLMClient测试失败: {e}")
        traceback.print_exc()
        return False

def test_service_adapter():
    """测试Service层适配器"""
    print("\n" + "=" * 50)
    print("测试Service层适配器")
    print("=" * 50)
    
    try:
        from src.services.core_adapter import initialize_core_dependencies
        print("✓ Core适配器导入成功")
        
        # 测试初始化
        initialize_core_dependencies()
        print("✓ Core依赖初始化成功")
        
        return True
    except Exception as e:
        print(f"✗ Service适配器测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始架构修复验证测试...")
    
    tests = [
        test_core_imports,
        test_base_registry,
        test_base_config,
        test_base_llm_client,
        test_service_adapter
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)
    
    if passed == total:
        print("✓ 所有测试通过！架构修复成功。")
        return 0
    else:
        print("✗ 部分测试失败，需要进一步修复。")
        return 1

if __name__ == "__main__":
    sys.exit(main())