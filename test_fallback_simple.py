"""简化的模型降级机制演示"""

import sys
import os
sys.path.insert(0, 'src')

def test_fallback_simple():
    print("=== 简化的模型降级机制演示 ===\n")
    
    try:
        # 直接导入需要的模块
        from llm.clients.mock_client import MockLLMClient
        from llm.config import MockConfig
        from llm.fallback_client import FallbackClientWrapper
        from langchain_core.messages import HumanMessage
        
        # 测试1: 创建Mock客户端
        print("1. 创建Mock客户端:")
        
        # 主客户端（会失败）
        primary_config = MockConfig(
            model_type="mock",
            model_name="mock-primary",
            response_delay=0.1,
            error_rate=1.0,  # 100%错误率
            error_types=["timeout"]
        )
        
        primary_client = MockLLMClient(primary_config)
        print(f"   主客户端创建成功: {primary_client.config.model_name}")
        
        # 降级客户端（不会失败）
        fallback_config = MockConfig(
            model_type="mock",
            model_name="mock-fallback",
            response_delay=0.1,
            error_rate=0.0  # 不会出错
        )
        
        fallback_client = MockLLMClient(fallback_config)
        print(f"   降级客户端创建成功: {fallback_client.config.model_name}")
        print()
        
        # 测试2: 创建降级包装器
        print("2. 创建降级包装器:")
        
        fallback_wrapper = FallbackClientWrapper(
            primary_client=primary_client,
            fallback_models=["mock-fallback"]
        )
        
        print(f"   降级包装器创建成功")
        print(f"   降级模型列表: {fallback_wrapper.fallback_models}")
        print()
        
        # 测试3: 测试降级调用
        print("3. 测试降级调用:")
        
        messages = [HumanMessage(content="你好，请介绍一下你自己")]
        
        try:
            response = fallback_wrapper.generate(messages)
            print(f"   调用成功!")
            print(f"   响应内容: {response.content}")
            
            # 检查是否使用了降级模型
            if hasattr(response, 'metadata') and response.metadata:
                fallback_model = response.metadata.get('fallback_model')
                if fallback_model:
                    print(f"   使用了降级模型: {fallback_model}")
                else:
                    print(f"   使用了主模型")
            
        except Exception as e:
            print(f"   调用失败: {e}")
        
        print()
        
        # 测试4: 测试主客户端直接调用（应该失败）
        print("4. 测试主客户端直接调用:")
        
        try:
            response = primary_client.generate(messages)
            print(f"   意外成功: {response.content}")
        except Exception as e:
            print(f"   预期失败: {type(e).__name__}: {e}")
        
        print()
        
        # 测试5: 测试降级客户端直接调用（应该成功）
        print("5. 测试降级客户端直接调用:")
        
        try:
            response = fallback_client.generate(messages)
            print(f"   调用成功: {response.content}")
        except Exception as e:
            print(f"   意外失败: {e}")
        
        print()
        
        # 测试6: 测试流式降级
        print("6. 测试流式降级:")
        
        try:
            chunks = list(fallback_wrapper.stream_generate(messages))
            print(f"   流式调用成功，收到 {len(chunks)} 个块")
            print(f"   完整响应: {''.join(chunks)}")
        except Exception as e:
            print(f"   流式调用失败: {e}")
        
        print()
        
        # 测试7: 获取模型信息
        print("7. 获取模型信息:")
        
        try:
            info = fallback_wrapper.get_model_info()
            print(f"   模型信息: {info}")
        except Exception as e:
            print(f"   获取模型信息失败: {e}")
        
        print()
        
        print("=== 演示完成 ===")
        
    except ImportError as e:
        print(f"导入错误: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fallback_simple()