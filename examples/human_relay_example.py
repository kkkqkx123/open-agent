"""
HumanRelay LLM 使用示例

这个示例展示了如何使用HumanRelay LLM进行单轮和多轮对话。
"""

import asyncio
from langchain_core.messages import HumanMessage, AIMessage

from src.infrastructure.llm.factory import create_client


async def single_turn_example():
    """单轮对话示例"""
    print("=== HumanRelay 单轮对话示例 ===")
    
    # 创建单轮模式客户端
    config = {
        "model_type": "human-relay-s",
        "model_name": "human-relay-s",
        "parameters": {
            "mode": "single",
            "frontend_timeout": 300
        },
        "human_relay_config": {
            "frontend_interface": {
                "interface_type": "mock",  # 使用Mock模式进行演示
                "mock_response": "这是一个模拟的Web LLM回复：Python是一种高级编程语言，具有简洁易读的语法。",
                "mock_delay": 1.0
            }
        }
    }
    
    client = create_client(config)
    
    # 发送消息
    messages = [
        HumanMessage(content="请介绍一下Python编程语言的特点。")
    ]
    
    try:
        response = await client.generate_async(messages)
        print(f"用户问题: {messages[0].content}")
        print(f"Web LLM回复: {response.content}")
        print(f"模式: {response.metadata['mode']}")
        print(f"Token使用: {response.token_usage.total_tokens}")
    except Exception as e:
        print(f"错误: {e}")
    
    print()


async def multi_turn_example():
    """多轮对话示例"""
    print("=== HumanRelay 多轮对话示例 ===")
    
    # 创建多轮模式客户端
    config = {
        "model_type": "human-relay-m",
        "model_name": "human-relay-m",
        "parameters": {
            "mode": "multi",
            "max_history_length": 10
        },
        "human_relay_config": {
            "frontend_interface": {
                "interface_type": "mock",
                "mock_response": "这是多轮对话的回复。",
                "mock_delay": 0.5
            }
        }
    }
    
    client = create_client(config)
    
    # 第一轮对话
    messages1 = [HumanMessage(content="什么是机器学习？")]
    try:
        response1 = await client.generate_async(messages1)
        print(f"第一轮 - 用户: {messages1[0].content}")
        print(f"第一轮 - Web LLM: {response1.content}")
        print(f"对话历史长度: {len(client.conversation_history)}")
    except Exception as e:
        print(f"第一轮错误: {e}")
        return
    
    # 第二轮对话
    messages2 = [HumanMessage(content="能详细解释一下监督学习吗？")]
    try:
        response2 = await client.generate_async(messages2)
        print(f"\n第二轮 - 用户: {messages2[0].content}")
        print(f"第二轮 - Web LLM: {response2.content}")
        print(f"对话历史长度: {len(client.conversation_history)}")
        
        # 显示对话历史
        print("\n对话历史:")
        for i, msg in enumerate(client.conversation_history, 1):
            role = "用户" if msg.type == "human" else "AI"
            print(f"  {i}. {role}: {msg.content}")
    except Exception as e:
        print(f"第二轮错误: {e}")
    
    print()


async def stream_generation_example():
    """流式生成示例"""
    print("=== HumanRelay 流式生成示例 ===")
    
    config = {
        "model_type": "human-relay-s",
        "model_name": "human-relay-s",
        "parameters": {"mode": "single"},
        "human_relay_config": {
            "frontend_interface": {
                "interface_type": "mock",
                "mock_response": "这是一个流式生成的回复示例。",
                "mock_delay": 0.1
            }
        }
    }
    
    client = create_client(config)
    
    messages = [HumanMessage(content="请演示流式生成。")]
    
    try:
        print("流式输出: ", end="", flush=True)
        async for chunk in client.stream_generate_async(messages):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"流式生成错误: {e}")
    
    print()


async def configuration_example():
    """配置示例"""
    print("=== HumanRelay 配置示例 ===")
    
    # 自定义配置
    config = {
        "model_type": "human_relay",
        "model_name": "custom-human-relay",
        "parameters": {
            "mode": "single",
            "frontend_timeout": 600  # 10分钟超时
        },
        "human_relay_config": {
            "prompt_template": """
🎯 **自定义任务**
请分析以下内容：

{prompt}

💡 **分析要求：**
- 提供详细分析
- 给出具体建议
- 使用中文回复

📝 **分析结果：**
""",
            "frontend_interface": {
                "interface_type": "mock",
                "mock_response": "基于自定义配置的分析结果：这是一个需要深入分析的话题。",
                "mock_delay": 0.5
            }
        }
    }
    
    client = create_client(config)
    
    messages = [HumanMessage(content="分析人工智能在教育领域的应用前景。")]
    
    try:
        response = await client.generate_async(messages)
        print(f"自定义配置回复: {response.content}")
        print(f"自定义模板: {'自定义任务' in client.prompt_template}")
    except Exception as e:
        print(f"配置示例错误: {e}")
    
    print()


async def error_handling_example():
    """错误处理示例"""
    print("=== HumanRelay 错误处理示例 ===")
    
    # 模拟超时配置
    config = {
        "model_type": "human-relay-s",
        "model_name": "human-relay-s",
        "parameters": {
            "mode": "single",
            "frontend_timeout": 1  # 1秒超时
        },
        "human_relay_config": {
            "frontend_interface": {
                "interface_type": "mock",
                "mock_response": "回复",
                "mock_delay": 2.0  # 模拟2秒延迟，会超时
            }
        }
    }
    
    client = create_client(config)
    
    messages = [HumanMessage(content="测试超时处理。")]
    
    try:
        response = await client.generate_async(messages)
        print(f"意外成功: {response.content}")
    except Exception as e:
        print(f"预期的超时错误: {type(e).__name__}: {e}")
    
    print()


async def main():
    """主函数"""
    print("HumanRelay LLM 使用示例")
    print("=" * 50)
    print()
    
    # 运行各种示例
    await single_turn_example()
    await multi_turn_example()
    await stream_generation_example()
    await configuration_example()
    await error_handling_example()
    
    print("所有示例运行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())