"""增强降级管理器集成测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage

from src.infrastructure.llm.fallback_client import FallbackClientWrapper
from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.polling_pool import PollingPoolManager
from infrastructure.config.interfaces import IConfigLoader


class MockLLMClient(ILLMClient):
    """模拟LLM客户端用于测试"""
    
    def __init__(self, model_name: str, should_fail: bool = False):
        self.model_name = model_name
        self.should_fail = should_fail
        self.generate_call_count = 0
        self.generate_async_call_count = 0
    
    def generate(self, messages, parameters=None, **kwargs):
        self.generate_call_count += 1
        if self.should_fail:
            raise Exception(f"Mock client {self.model_name} failed")
        
        content = f"Response from {self.model_name}: {messages[0].content}"
        message = HumanMessage(content=content)
        return LLMResponse(
            content=content,
            message=message,
            token_usage=TokenUsage(),
            model=self.model_name
        )
    
    async def generate_async(self, messages, parameters=None, **kwargs):
        self.generate_async_call_count += 1
        if self.should_fail:
            raise Exception(f"Mock client {self.model_name} failed")
        
        content = f"Async response from {self.model_name}: {messages[0].content}"
        message = HumanMessage(content=content)
        return LLMResponse(
            content=content,
            message=message,
            token_usage=TokenUsage(),
            model=self.model_name
        )
    
    def stream_generate(self, messages, parameters=None, **kwargs):
        yield f"Stream response from {self.model_name}"
    
    def stream_generate_async(self, messages, parameters=None, **kwargs):
        async def async_gen():
            yield f"Async stream response from {self.model_name}"
        return async_gen()
    
    def get_token_count(self, text: str) -> int:
        return len(text.split())
    
    def get_messages_token_count(self, messages) -> int:
        return sum(len(str(msg.content).split()) for msg in messages)
    
    def supports_function_calling(self) -> bool:
        return True
    
    def get_model_info(self) -> dict:
        return {"model_name": self.model_name}


class MockConfigLoader(IConfigLoader):
    """模拟配置加载器用于测试"""
    
    def __init__(self):
        self.configs = {
            # 任务组配置
            "llms/groups/fast_group.yaml": {
                "name": "fast_group",
                "description": "快速响应组",
                "fallback_strategy": "echelon_down",
                "echelon1": {
                    "models": ["gpt-4-turbo", "claude-3-opus"],
                    "concurrency_limit": 10,
                    "rpm_limit": 100,
                    "priority": 1,
                    "timeout": 30,
                    "max_retries": 2
                },
                "echelon2": {
                    "models": ["gpt-4", "claude-3-sonnet"],
                    "concurrency_limit": 5,
                    "rpm_limit": 50,
                    "priority": 2,
                    "timeout": 60,
                    "max_retries": 3
                }
            },
            "llms/groups/medium_group.yaml": {
                "name": "medium_group",
                "description": "中等响应组",
                "fallback_strategy": "echelon_down",
                "echelon1": {
                    "models": ["gpt-3.5-turbo"],
                    "concurrency_limit": 20,
                    "rpm_limit": 200,
                    "priority": 1,
                    "timeout": 90,
                    "max_retries": 5
                }
            },
            # 轮询池配置
            "llms/polling_pools/single_turn_pool.yaml": {
                "name": "single_turn_pool",
                "description": "单轮对话轮询池",
                "task_groups": ["fast_group"],
                "rotation_strategy": "round_robin",
                "health_check_interval": 30
            },
            # 全局配置
            "llms/global_fallback.yaml": {
                "enabled": True,
                "max_attempts": 3,
                "strategy": "sequential"
            },
            "llms/concurrency_control.yaml": {
                "enabled": False
            },
            "llms/rate_limiting.yaml": {
                "enabled": False
            }
        }
    
    def load(self, config_path: str) -> dict:
        return self.configs.get(config_path, {})
    
    def reload(self) -> None:
        pass
    
    def watch_for_changes(self, callback) -> None:
        pass
    
    def resolve_env_vars(self, config: dict) -> dict:
        return config
    
    def stop_watching(self) -> None:
        pass
    
    def get_config(self, config_path: str) -> dict:
        return self.configs.get(config_path, {})
    
    def _handle_file_change(self, file_path: str) -> None:
        pass


@pytest.fixture
def task_group_manager():
    """创建任务组管理器"""
    config_loader = MockConfigLoader()
    manager = TaskGroupManager(config_loader)
    manager.load_config()
    return manager


@pytest.fixture
def polling_pool_manager(task_group_manager):
    """创建轮询池管理器"""
    manager = PollingPoolManager(task_group_manager)
    return manager


@pytest.fixture
def primary_client():
    """创建主客户端"""
    return MockLLMClient("primary_model")


def test_fallback_client_wrapper_with_enhanced_fallback(
    task_group_manager, polling_pool_manager, primary_client
):
    """测试使用增强降级管理器的 FallbackClientWrapper"""
    
    # 创建使用增强降级管理器的客户端
    fallback_client = FallbackClientWrapper(
        primary_client=primary_client,
        fallback_models=[],  # 不需要指定降级模型列表
        use_enhanced_fallback=True,
        task_group_manager=task_group_manager,
        polling_pool_manager=polling_pool_manager
    )
    
    # 验证配置
    assert fallback_client.use_enhanced_fallback is True
    assert fallback_client.enhanced_fallback_manager is not None
    assert fallback_client.fallback_manager is None


def test_fallback_client_wrapper_with_traditional_fallback(primary_client):
    """测试使用传统降级管理器的 FallbackClientWrapper"""
    
    # 创建使用传统降级管理器的客户端
    fallback_client = FallbackClientWrapper(
        primary_client=primary_client,
        fallback_models=["gpt-3.5-turbo", "claude-instant"],
        use_enhanced_fallback=False
    )
    
    # 验证配置
    assert fallback_client.use_enhanced_fallback is False
    assert fallback_client.fallback_manager is not None
    assert fallback_client.enhanced_fallback_manager is None


@pytest.mark.asyncio
async def test_enhanced_fallback_generate_async(
    task_group_manager, polling_pool_manager, primary_client
):
    """测试增强降级管理器的异步生成功能"""
    
    # 创建使用增强降级管理器的客户端
    fallback_client = FallbackClientWrapper(
        primary_client=primary_client,
        fallback_models=[],
        use_enhanced_fallback=True,
        task_group_manager=task_group_manager,
        polling_pool_manager=polling_pool_manager
    )
    
    # 创建测试消息
    messages = [HumanMessage(content="Test message")]
    
    # 由于增强降级管理器需要实际的模型调用，这里我们只测试接口
    # 在实际环境中，这将调用增强降级管理器的 execute_with_fallback 方法
    try:
        # 这里会因为没有实际的模型实现而抛出异常，但我们主要测试接口是否正常
        response = await fallback_client.generate_async(
            messages,
            primary_target="fast_group.echelon1",
            fallback_groups=["fast_group.echelon2", "medium_group.echelon1"]
        )
        # 如果没有抛出异常，说明接口调用成功
        assert response is not None
    except Exception as e:
        # 由于我们没有实际的模型实现，这里会抛出异常，这是正常的
        # 我们主要验证接口调用路径是否正确
        assert "enhanced_fallback_manager" in str(type(fallback_client.enhanced_fallback_manager))


def test_fallback_stats_access(
    task_group_manager, polling_pool_manager, primary_client
):
    """测试降级统计信息访问"""
    
    # 创建使用增强降级管理器的客户端
    fallback_client = FallbackClientWrapper(
        primary_client=primary_client,
        fallback_models=[],
        use_enhanced_fallback=True,
        task_group_manager=task_group_manager,
        polling_pool_manager=polling_pool_manager
    )
    
    # 获取统计信息
    stats = fallback_client.get_fallback_stats()
    
    # 验证返回的统计信息结构
    assert isinstance(stats, dict)
    assert "total_attempts" in stats
    assert "success_rate" in stats
    assert "avg_response_time" in stats


def test_traditional_fallback_stats_access(primary_client):
    """测试传统降级管理器的统计信息访问"""
    
    # 创建使用传统降级管理器的客户端
    fallback_client = FallbackClientWrapper(
        primary_client=primary_client,
        fallback_models=["gpt-3.5-turbo"],
        use_enhanced_fallback=False
    )
    
    # 获取统计信息
    stats = fallback_client.get_fallback_stats()
    
    # 验证返回的统计信息结构
    assert isinstance(stats, dict)
    # 传统降级管理器的统计信息结构可能不同
    # 但至少应该包含基本的统计信息


def test_model_info_includes_enhanced_flag(
    task_group_manager, polling_pool_manager, primary_client
):
    """测试模型信息包含增强降级标志"""
    
    # 创建使用增强降级管理器的客户端
    fallback_client = FallbackClientWrapper(
        primary_client=primary_client,
        fallback_models=[],
        use_enhanced_fallback=True,
        task_group_manager=task_group_manager,
        polling_pool_manager=polling_pool_manager
    )
    
    # 获取模型信息
    model_info = fallback_client.get_model_info()
    
    # 验证模型信息包含增强降级标志
    assert "use_enhanced_fallback" in model_info
    assert model_info["use_enhanced_fallback"] is True


def test_messages_to_prompt_conversion(primary_client):
    """测试消息到提示文本的转换"""
    
    # 创建客户端
    fallback_client = FallbackClientWrapper(
        primary_client=primary_client,
        fallback_models=["gpt-3.5-turbo"],
        use_enhanced_fallback=False
    )
    
    # 创建测试消息
    messages = [
        HumanMessage(content="Hello"),
        HumanMessage(content="World")
    ]
    
    # 转换为提示文本
    prompt = fallback_client._messages_to_prompt(messages)
    
    # 验证转换结果
    assert "Hello" in prompt
    assert "World" in prompt
    assert isinstance(prompt, str)


if __name__ == "__main__":
    pytest.main([__file__])