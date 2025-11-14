#!/usr/bin/env python3
"""LLM包装器使用示例"""

import asyncio
import logging
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.config.core.loader import YamlConfigLoader
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.enhanced_fallback_manager import EnhancedFallbackManager
from src.infrastructure.llm.polling_pool import PollingPoolManager
from src.infrastructure.llm.wrappers import LLMWrapperFactory
from src.infrastructure.graph.nodes.llm_node import LLMNode
from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from langchain_core.messages import HumanMessage, AIMessage

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLMClient(ILLMClient):
    """模拟LLM客户端"""
    
    def __init__(self, config):
        self.model_name = config.get("model_name", "mock_model")
    
    def generate(self, messages, parameters=None, **kwargs):
        """生成响应"""
        content = f"[{self.model_name}] 响应: {messages[-1].content if messages else '无消息'}"
        return LLMResponse(
            content=content,
            message=messages[-1] if messages else HumanMessage(content=""),
            model=self.model_name,
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20)
        )
    
    async def generate_async(self, messages, parameters=None, **kwargs):
        """异步生成响应"""
        return self.generate(messages, parameters, **kwargs)
    
    def stream_generate(self, messages, parameters=None, **kwargs):
        """流式生成"""
        response = self.generate(messages, parameters, **kwargs)
        for word in response.content.split():
            yield word + " "
    
    async def stream_generate_async(self, messages, parameters=None, **kwargs):
        """异步流式生成"""
        response = self.generate(messages, parameters, **kwargs)
        for word in response.content.split():
            yield word + " "
    
    def get_token_count(self, text):
        """计算token数量"""
        return len(text) // 4
    
    def get_messages_token_count(self, messages):
        """计算消息token数量"""
        total = 0
        for msg in messages:
            if isinstance(msg.content, str):
                total += self.get_token_count(msg.content)
        return total
    
    def supports_function_calling(self):
        """检查是否支持函数调用"""
        return False
    
    def get_model_info(self):
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "provider": "mock",
            "capabilities": ["text_generation"]
        }


async def demonstrate_task_group_wrapper(wrapper_factory):
    """演示任务组包装器使用"""
    logger.info("=== 任务组包装器演示 ===")
    
    # 创建快速任务组包装器
    fast_wrapper = wrapper_factory.create_task_group_wrapper(
        name="fast_wrapper",
        config={
            "target": "fast_group.echelon1",
            "fallback_groups": ["fast_group.echelon2", "fast_group.echelon3"]
        }
    )
    
    # 创建思考任务组包装器
    thinking_wrapper = wrapper_factory.create_task_group_wrapper(
        name="thinking_wrapper",
        config={
            "target": "thinking_group.echelon1",
            "fallback_groups": ["thinking_group.echelon2", "fast_group.echelon1"]
        }
    )
    
    # 测试快速任务
    messages = [HumanMessage(content="请快速回答：什么是机器学习？")]
    
    logger.info("使用快速任务组包装器...")
    response = await fast_wrapper.generate_async(messages)
    logger.info(f"快速响应: {response.content}")
    
    # 测试思考任务
    messages = [HumanMessage(content="请深入分析：人工智能的未来发展趋势")]
    
    logger.info("使用思考任务组包装器...")
    response = await thinking_wrapper.generate_async(messages)
    logger.info(f"思考响应: {response.content}")
    
    # 显示统计信息
    fast_stats = fast_wrapper.get_stats()
    thinking_stats = thinking_wrapper.get_stats()
    
    logger.info(f"快速包装器统计: {fast_stats}")
    logger.info(f"思考包装器统计: {thinking_stats}")


async def demonstrate_polling_pool_wrapper(wrapper_factory):
    """演示轮询池包装器使用"""
    logger.info("=== 轮询池包装器演示 ===")
    
    # 创建快速轮询池包装器
    fast_pool_wrapper = wrapper_factory.create_polling_pool_wrapper(
        name="fast_pool_wrapper",
        config={
            "max_instance_attempts": 2
        }
    )
    
    # 创建思考轮询池包装器
    thinking_pool_wrapper = wrapper_factory.create_polling_pool_wrapper(
        name="thinking_pool_wrapper",
        config={
            "max_instance_attempts": 3
        }
    )
    
    # 测试快速轮询池
    messages = [HumanMessage(content="简单问题：2+2等于多少？")]
    
    logger.info("使用快速轮询池包装器...")
    response = await fast_pool_wrapper.generate_async(messages)
    logger.info(f"轮询池响应: {response.content}")
    
    # 测试思考轮询池
    messages = [HumanMessage(content="复杂问题：解释量子计算的基本原理")]
    
    logger.info("使用思考轮询池包装器...")
    response = await thinking_pool_wrapper.generate_async(messages)
    logger.info(f"轮询池响应: {response.content}")
    
    # 显示统计信息
    fast_stats = fast_pool_wrapper.get_stats()
    thinking_stats = thinking_pool_wrapper.get_stats()
    
    logger.info(f"快速轮询池统计: {fast_stats}")
    logger.info(f"思考轮询池统计: {thinking_stats}")


def demonstrate_llm_node_with_wrappers(wrapper_factory, mock_client):
    """演示LLM节点使用包装器"""
    logger.info("=== LLM节点包装器演示 ===")
    
    # 创建LLM节点
    llm_node = LLMNode(
        llm_client=mock_client,
        wrapper_factory=wrapper_factory
    )
    
    # 创建包装器
    wrapper_factory.create_task_group_wrapper(
        "demo_fast_wrapper",
        {"target": "fast_group.echelon1"}
    )
    
    wrapper_factory.create_polling_pool_wrapper(
        "demo_pool_wrapper"
    )
    
    # 测试使用任务组包装器
    state = {"messages": []}
    config = {
        "llm_wrapper": "demo_fast_wrapper",
        "system_prompt": "你是一个快速响应的助手",
        "max_tokens": 1000
    }
    
    logger.info("使用任务组包装器的LLM节点...")
    result = llm_node.execute(state, config)
    logger.info(f"节点执行结果: {result.metadata}")
    
    # 测试使用轮询池包装器
    state = {"messages": []}
    config = {
        "llm_wrapper": "demo_pool_wrapper",
        "system_prompt": "你是一个高效的助手",
        "max_tokens": 1500
    }
    
    logger.info("使用轮询池包装器的LLM节点...")
    result = llm_node.execute(state, config)
    logger.info(f"节点执行结果: {result.metadata}")


def demonstrate_wrapper_factory_management(wrapper_factory):
    """演示包装器工厂管理功能"""
    logger.info("=== 包装器工厂管理演示 ===")
    
    # 列出所有包装器
    wrappers = wrapper_factory.list_wrappers()
    logger.info(f"当前包装器: {wrappers}")
    
    # 获取包装器统计
    stats = wrapper_factory.get_wrapper_stats()
    logger.info(f"包装器统计: {stats}")
    
    # 健康检查
    health_status = wrapper_factory.health_check_all()
    logger.info(f"健康检查结果: {health_status}")
    
    # 重置统计
    wrapper_factory.reset_all_stats()
    logger.info("已重置所有包装器统计信息")


async def demonstrate_fallback_integration(fallback_manager):
    """演示降级管理器集成"""
    logger.info("=== 降级管理器集成演示 ===")
    
    try:
        # 使用任务组降级
        result = await fallback_manager.execute_with_task_group_fallback(
            primary_target="fast_group.echelon1",
            prompt="测试降级功能"
        )
        logger.info(f"降级成功: {result}")
    except Exception as e:
        logger.info(f"降级失败（预期）: {e}")
    
    # 获取降级历史
    history = fallback_manager.get_fallback_history()
    logger.info(f"降级历史: {history}")
    
    # 获取熔断器状态
    circuit_status = fallback_manager.get_circuit_breaker_status()
    logger.info(f"熔断器状态: {circuit_status}")


async def main():
    """主函数"""
    logger.info("开始LLM包装器使用演示")
    
    try:
        # 初始化配置加载器
        config_loader = YamlConfigLoader()
        
        # 初始化任务组管理器
        task_group_manager = TaskGroupManager(config_loader)
        task_group_manager.load_config()
        
        # 初始化降级管理器
        fallback_manager = EnhancedFallbackManager(task_group_manager)
        
        # 初始化轮询池管理器
        polling_pool_manager = PollingPoolManager(task_group_manager)
        
        # 初始化包装器工厂
        wrapper_factory = LLMWrapperFactory(
            task_group_manager=task_group_manager,
            polling_pool_manager=polling_pool_manager,
            fallback_manager=fallback_manager
        )
        
        # 创建模拟LLM客户端
        mock_client = MockLLMClient({"model_name": "demo_model"})
        
        # 演示各种功能
        await demonstrate_task_group_wrapper(wrapper_factory)
        await demonstrate_polling_pool_wrapper(wrapper_factory)
        demonstrate_llm_node_with_wrappers(wrapper_factory, mock_client)
        demonstrate_wrapper_factory_management(wrapper_factory)
        await demonstrate_fallback_integration(fallback_manager)
        
        logger.info("演示完成")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())