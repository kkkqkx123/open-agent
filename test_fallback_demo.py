"""模型降级机制演示"""

import sys
import os
sys.path.insert(0, 'src/llm')

def test_fallback_mechanism():
    print("=== 模型降级机制演示 ===\n")
    
    try:
        from factory import get_global_factory, create_client
        from config import LLMClientConfig
        from langchain_core.messages import HumanMessage
        
        # 创建工厂实例
        factory = get_global_factory()
        
        # 测试1: 创建带降级的客户端
        print("1. 测试创建带降级的客户端:")
        
        # 主配置（使用mock客户端模拟失败）
        primary_config = {
            "model_type": "mock",
            "model_name": "mock-primary",
            "response_delay": 0.1,
            "error_rate": 0.5,  # 50%错误率
            "error_types": ["timeout", "rate_limit"],
            "fallback_enabled": True,
            "fallback_models": ["mock-fallback-1", "mock-fallback-2"]
        }
        
        # 降级模型配置
        fallback_config_1 = {
            "model_type": "mock",
            "model_name": "mock-fallback-1",
            "response_delay": 0.1,
            "error_rate": 0.0,  # 不出错
            "fallback_enabled": False
        }
        
        fallback_config_2 = {
            "model_type": "mock",
            "model_name": "mock-fallback-2",
            "response_delay": 0.1,
            "error_rate": 0.0,  # 不出错
            "fallback_enabled": False
        }
        
        # 创建并缓存降级客户端
        factory.create_client(fallback_config_1)
        factory.create_client(fallback_config_2)
        
        # 创建主客户端（会自动包装为降级客户端）
        primary_client = factory.create_client(primary_config)
        
        print(f"   主客户端类型: {type(primary_client).__name__}")
        print(f"   降级模型: {primary_config['fallback_models']}")
        print("   ✓ 带降级的客户端创建成功")
        print()
        
        # 测试2: 测试降级调用
        print("2. 测试降级调用:")
        
        messages = [HumanMessage(content="你好，请介绍一下你自己")]
        
        # 多次调用，观察降级行为
        for i in range(5):
            try:
                response = primary_client.generate(messages)
                print(f"   调用 {i+1}: 成功")
                print(f"   响应内容: {response.content[:50]}...")
                
                # 检查是否使用了降级模型
                if hasattr(response, 'metadata') and response.metadata:
                    fallback_model = response.metadata.get('fallback_model')
                    if fallback_model:
                        print(f"   使用了降级模型: {fallback_model}")
                    else:
                        print(f"   使用了主模型")
                
            except Exception as e:
                print(f"   调用 {i+1}: 失败 - {e}")
            
            print()
        
        # 测试3: 获取降级统计
        print("3. 测试降级统计:")
        if hasattr(primary_client, 'get_fallback_stats'):
            stats = primary_client.get_fallback_stats()
            print(f"   降级统计: {stats}")
        else:
            print("   当前客户端不支持降级统计")
        print()
        
        # 测试4: 测试流式降级
        print("4. 测试流式降级:")
        try:
            chunks = list(primary_client.stream_generate(messages))
            print(f"   流式调用成功，收到 {len(chunks)} 个块")
            print(f"   完整响应: {''.join(chunks)[:50]}...")
        except Exception as e:
            print(f"   流式调用失败: {e}")
        print()
        
        print("=== 演示完成 ===")
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("可能是因为相对导入问题")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fallback_mechanism()