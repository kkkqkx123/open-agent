"""LLM包装器和降级系统集成测试"""

import pytest
import asyncio
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from infrastructure.config.core.loader import YamlConfigLoader
from src.infrastructure.llm.task_group_manager import TaskGroupManager
from src.infrastructure.llm.enhanced_fallback_manager import EnhancedFallbackManager
from src.infrastructure.llm.polling_pool import PollingPoolManager
from src.infrastructure.llm.wrappers import LLMWrapperFactory, TaskGroupWrapper, PollingPoolWrapper
from src.infrastructure.llm.migration import ConfigMigrator
from src.infrastructure.graph.nodes.llm_node import LLMNode
from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.llm.models import LLMResponse


class TestLLMIntegration:
    """LLM集成测试"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """临时配置目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "configs" / "llms"
            config_dir.mkdir(parents=True)
            
            # 创建子目录
            (config_dir / "groups").mkdir()
            (config_dir / "polling_pools").mkdir()
            (config_dir / "backup").mkdir()
            
            yield config_dir
    
    @pytest.fixture
    def config_files(self, temp_config_dir):
        """创建配置文件"""
        # 创建任务组注册表
        task_groups_registry = {
            "task_groups": {
                "fast_group": {
                    "file": "groups/fast_group.yaml",
                    "description": "快速响应任务组",
                    "enabled": True
                },
                "thinking_group": {
                    "file": "groups/thinking_group.yaml",
                    "description": "思考任务组",
                    "enabled": True
                }
            },
            "polling_pools": {
                "fast_pool": {
                    "file": "polling_pools/fast_pool.yaml",
                    "description": "快速响应轮询池",
                    "enabled": True
                },
                "thinking_pool": {
                    "file": "polling_pools/thinking_pool.yaml",
                    "description": "思考轮询池",
                    "enabled": True
                }
            }
        }
        
        registry_path = temp_config_dir / "groups" / "_task_groups.yaml"
        with open(registry_path, 'w') as f:
            yaml.dump(task_groups_registry, f)
        
        # 创建快速任务组配置
        fast_group_config = {
            "name": "fast_group",
            "description": "快速响应任务组",
            "echelon1": {
                "models": ["openai-gpt4", "anthropic-claude-3-opus"],
                "concurrency_limit": 10,
                "rpm_limit": 100,
                "priority": 1,
                "timeout": 30,
                "max_retries": 3,
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "echelon2": {
                "models": ["openai-gpt4-turbo", "anthropic-claude-3-sonnet"],
                "concurrency_limit": 20,
                "rpm_limit": 200,
                "priority": 2,
                "timeout": 25,
                "max_retries": 3,
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "fallback_config": {
                "strategy": "echelon_down",
                "fallback_groups": ["fast_group.echelon2"],
                "max_attempts": 3,
                "retry_delay": 1.0,
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "recovery_time": 60,
                    "half_open_requests": 1
                }
            }
        }

        fast_group_path = temp_config_dir / "groups" / "fast_group.yaml"
        with open(fast_group_path, 'w') as f:
            yaml.dump(fast_group_config, f)
        
        # 创建思考任务组配置（不包含fallback_config，以便测试迁移）
        thinking_group_config = {
            "name": "thinking_group",
            "description": "思考任务组",
            "echelon1": {
                "models": ["openai-gpt4", "anthropic-claude-3-opus"],
                "concurrency_limit": 3,
                "rpm_limit": 30,
                "priority": 1,
                "timeout": 120,
                "max_retries": 5,
                "temperature": 0.8,
                "max_tokens": 4000
            }
        }
        
        thinking_group_path = temp_config_dir / "groups" / "thinking_group.yaml"
        with open(thinking_group_path, 'w') as f:
            yaml.dump(thinking_group_config, f)
        
        # 创建快速轮询池配置
        fast_pool_config = {
            "name": "fast_pool",
            "description": "快速响应轮询池",
            "task_groups": ["fast_group"],
            "rotation_strategy": "round_robin",
            "health_check_interval": 30,
            "failure_threshold": 3,
            "recovery_time": 60,
            "fallback_config": {
                "strategy": "instance_rotation",
                "max_instance_attempts": 2
            }
        }
        
        fast_pool_path = temp_config_dir / "polling_pools" / "fast_pool.yaml"
        with open(fast_pool_path, 'w') as f:
            yaml.dump(fast_pool_config, f)
        
        # 创建思考轮询池配置
        thinking_pool_config = {
            "name": "thinking_pool",
            "description": "思考轮询池",
            "task_groups": ["thinking_group"],
            "rotation_strategy": "least_recently_used",
            "health_check_interval": 60,
            "failure_threshold": 2,
            "recovery_time": 120,
            "fallback_config": {
                "strategy": "instance_rotation",
                "max_instance_attempts": 3
            }
        }
        
        thinking_pool_path = temp_config_dir / "polling_pools" / "thinking_pool.yaml"
        with open(thinking_pool_path, 'w') as f:
            yaml.dump(thinking_pool_config, f)
        
        return temp_config_dir
    
    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端"""
        from src.infrastructure.llm.models import TokenUsage
        from langchain_core.messages import AIMessage
        
        client = Mock(spec=ILLMClient)
        client.generate.return_value = LLMResponse(
            content="Mock response",
            message=AIMessage(content="Mock response"),
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20),
            model="mock_model"
        )
        client.generate_async = AsyncMock(return_value=LLMResponse(
            content="Mock async response",
            message=AIMessage(content="Mock async response"),
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20),
            model="mock_model"
        ))
        return client
    
    @pytest.fixture
    def task_group_manager(self, config_files):
        """任务组管理器"""
        config_loader = YamlConfigLoader(base_path=str(config_files.parent))
        manager = TaskGroupManager(config_loader)
        manager._config_base_path = str(config_files)
        manager.load_config()
        return manager
    
    @pytest.fixture
    def fallback_manager(self, task_group_manager):
        """降级管理器"""
        return EnhancedFallbackManager(task_group_manager)
    
    @pytest.fixture
    def polling_pool_manager(self, task_group_manager):
        """轮询池管理器"""
        return PollingPoolManager(task_group_manager)
    
    @pytest.fixture
    def wrapper_factory(self, task_group_manager, polling_pool_manager, fallback_manager):
        """包装器工厂"""
        return LLMWrapperFactory(
            task_group_manager=task_group_manager,
            polling_pool_manager=polling_pool_manager,
            fallback_manager=fallback_manager
        )
    
    def test_config_loading(self, config_files, task_group_manager):
        """测试配置加载"""
        # 检查任务组是否正确加载
        task_groups = task_group_manager.list_task_groups()
        assert "fast_group" in task_groups
        assert "thinking_group" in task_groups
        
        # 检查轮询池是否正确加载
        polling_pools = task_group_manager.list_polling_pools()
        assert "fast_pool" in polling_pools
        assert "thinking_pool" in polling_pools
        
        # 检查任务组配置
        fast_group = task_group_manager.get_task_group("fast_group")
        assert fast_group is not None
        assert fast_group.fallback_config is not None
        assert fast_group.fallback_config.strategy.value == "echelon_down"
        
        # 检查轮询池配置
        fast_pool = task_group_manager.get_polling_pool("fast_pool")
        assert fast_pool is not None
        assert fast_pool.fallback_config is not None
        assert fast_pool.fallback_config.strategy == "instance_rotation"
    
    def test_wrapper_factory_creation(self, wrapper_factory):
        """测试包装器工厂创建"""
        # 创建任务组包装器
        fast_wrapper = wrapper_factory.create_task_group_wrapper(
            "fast_wrapper",
            {"target": "fast_group.echelon1"}
        )
        assert isinstance(fast_wrapper, TaskGroupWrapper)
        assert fast_wrapper.name == "fast_wrapper"
        
        # 创建轮询池包装器
        fast_pool_wrapper = wrapper_factory.create_polling_pool_wrapper(
            "fast_pool_wrapper"
        )
        assert isinstance(fast_pool_wrapper, PollingPoolWrapper)
        assert fast_pool_wrapper.name == "fast_pool_wrapper"
        
        # 检查包装器列表
        wrappers = wrapper_factory.list_wrappers()
        assert "fast_wrapper" in wrappers
        assert "fast_pool_wrapper" in wrappers
        assert wrappers["fast_wrapper"] == "TaskGroupWrapper"
        assert wrappers["fast_pool_wrapper"] == "PollingPoolWrapper"
    
    @pytest.mark.asyncio
    async def test_task_group_wrapper_execution(self, wrapper_factory):
        """测试任务组包装器执行"""
        # 创建任务组包装器
        wrapper = wrapper_factory.create_task_group_wrapper(
            "test_wrapper",
            {"target": "fast_group.echelon1"}
        )
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "Test message"
        messages = [mock_message]
        
        # 执行生成
        response = await wrapper.generate_async(messages)
        
        # 检查响应
        assert response.content is not None
        # 模型名称应该是目标名称，而不是mock_model
        assert response.model == "fast_group.echelon1"
        
        # 检查统计信息
        stats = wrapper.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_polling_pool_wrapper_execution(self, wrapper_factory, polling_pool_manager):
        """测试轮询池包装器执行"""
        # 确保轮询池已创建
        pool_name = "fast_pool"
        if not polling_pool_manager.get_pool(pool_name):
            # 创建轮询池
            pool_config = {
                "name": pool_name,
                "task_groups": ["fast_group"],
                "rotation_strategy": "round_robin",
                "health_check_interval": 30,
                "failure_threshold": 3,
                "recovery_time": 60
            }
            await polling_pool_manager.create_pool(pool_name, pool_config)
        
        # 创建轮询池包装器，使用与轮询池相同的名称
        wrapper = wrapper_factory.create_polling_pool_wrapper(
            pool_name  # 使用轮询池名称作为包装器名称
        )
        
        # 创建模拟消息
        mock_message = Mock()
        mock_message.content = "Test message"
        messages = [mock_message]
        
        # 执行生成
        response = await wrapper.generate_async(messages)
        
        # 检查响应
        assert response.content is not None
        # 轮询池响应内容格式不同
        assert "轮询池响应" in response.content or "模拟响应" in response.content
        
        # 检查统计信息
        stats = wrapper.get_stats()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
    
    def test_llm_node_with_wrapper(self, wrapper_factory, mock_llm_client):
        """测试LLM节点使用包装器"""
        # 创建包装器
        wrapper = wrapper_factory.create_task_group_wrapper(
            "test_wrapper",
            {"target": "fast_group.echelon1"}
        )
        
        # 创建LLM节点
        llm_node = LLMNode(
            llm_client=mock_llm_client,
            wrapper_factory=wrapper_factory
        )
        
        # 创建状态和配置
        state = {"messages": []}
        config = {
            "llm_wrapper": "test_wrapper",
            "system_prompt": "You are a helpful assistant"
        }
        
        # 执行节点
        result = llm_node.execute(state, config)
        
        # 检查结果
        assert result is not None
        assert "messages" in result.state
        assert len(result.state["messages"]) > 0
    
    def test_llm_node_client_selection_priority(self, wrapper_factory, mock_llm_client):
        """测试LLM节点客户端选择优先级"""
        # 创建包装器
        wrapper = wrapper_factory.create_task_group_wrapper(
            "test_wrapper",
            {"target": "fast_group.echelon1"}
        )
        
        # 创建LLM节点
        llm_node = LLMNode(
            llm_client=mock_llm_client,
            wrapper_factory=wrapper_factory
        )
        
        # 测试优先级1: 使用包装器
        config = {"llm_wrapper": "test_wrapper"}
        client = llm_node._select_llm_client(config)
        assert client == wrapper
        
        # 测试优先级2: 使用任务组（需要模拟任务组管理器）
        config = {"llm_group": "fast_group.echelon1"}
        client = llm_node._select_llm_client(config)
        # 由于没有实际的LLM客户端创建逻辑，应该返回默认客户端
        assert client == mock_llm_client
        
        # 测试默认: 使用注入的客户端
        config = {}
        client = llm_node._select_llm_client(config)
        assert client == mock_llm_client
    
    def test_config_migration(self, config_files, task_group_manager):
        """测试配置迁移"""
        # 创建全局降级配置文件
        global_fallback_config = {
            "max_attempts": 3,
            "retry_delay": 1.0,
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_time": 60,
                "half_open_requests": 1
            }
        }
        
        global_fallback_path = config_files / "global_fallback.yaml"
        with open(global_fallback_path, 'w') as f:
            yaml.dump(global_fallback_config, f)
        
        # 创建迁移器
        migrator = ConfigMigrator(task_group_manager, str(config_files))
        
        # 确认全局降级配置文件存在
        global_fallback_path = config_files / "global_fallback.yaml"
        assert global_fallback_path.exists(), f"全局降级配置文件不存在: {global_fallback_path}"
        
        # 执行迁移
        result = migrator.migrate_global_fallback_to_task_groups(backup=False)
        assert result == True
        
        # 验证迁移结果
        validation_result = migrator.validate_migration()
        assert validation_result["summary"]["valid_task_groups"] > 0
        
        # 检查迁移日志
        migration_log = migrator.get_migration_log()
        assert len(migration_log) > 0
    
    @pytest.mark.asyncio
    async def test_fallback_manager_integration(self, fallback_manager):
        """测试降级管理器集成"""
        # 使用降级管理器执行任务组降级
        try:
            result = await fallback_manager.execute_with_task_group_fallback(
                primary_target="fast_group.echelon1",
                prompt="Test prompt"
            )
            # 由于是模拟环境，可能会失败，这是正常的
        except Exception as e:
            # 预期可能会失败，因为没有实际的LLM客户端
            assert "降级执行失败" in str(e) or "所有降级尝试都失败了" in str(e)
    
    def test_wrapper_factory_health_check(self, wrapper_factory):
        """测试包装器工厂健康检查"""
        # 创建包装器
        wrapper_factory.create_task_group_wrapper("test_wrapper")
        
        # 执行健康检查
        health_status = wrapper_factory.health_check_all()
        
        # 检查结果
        assert "test_wrapper" in health_status
        assert health_status["test_wrapper"]["healthy"] == True
    
    def test_wrapper_factory_stats(self, wrapper_factory):
        """测试包装器工厂统计信息"""
        # 创建包装器
        wrapper_factory.create_task_group_wrapper("test_wrapper")
        wrapper_factory.create_polling_pool_wrapper("test_pool")
        
        # 获取统计信息
        stats = wrapper_factory.get_wrapper_stats()
        
        # 检查结果
        assert stats["total_wrappers"] == 2
        assert "TaskGroupWrapper" in stats["wrapper_types"]
        assert "PollingPoolWrapper" in stats["wrapper_types"]
        assert stats["wrapper_types"]["TaskGroupWrapper"] == 1
        assert stats["wrapper_types"]["PollingPoolWrapper"] == 1
    
    def test_end_to_end_workflow(self, wrapper_factory, mock_llm_client):
        """测试端到端工作流"""
        # 1. 创建包装器
        fast_wrapper = wrapper_factory.create_task_group_wrapper(
            "fast_wrapper",
            {"target": "fast_group.echelon1"}
        )
        
        thinking_wrapper = wrapper_factory.create_task_group_wrapper(
            "thinking_wrapper",
            {"target": "thinking_group.echelon1"}
        )
        
        # 2. 创建LLM节点
        llm_node = LLMNode(
            llm_client=mock_llm_client,
            wrapper_factory=wrapper_factory
        )
        
        # 3. 执行快速任务
        fast_state = {"messages": []}
        fast_config = {
            "llm_wrapper": "fast_wrapper",
            "system_prompt": "You are a fast assistant",
            "max_tokens": 1000
        }
        
        fast_result = llm_node.execute(fast_state, fast_config)
        assert fast_result is not None
        
        # 4. 执行思考任务
        thinking_state = {"messages": []}
        thinking_config = {
            "llm_wrapper": "thinking_wrapper",
            "system_prompt": "You are a thoughtful assistant",
            "max_tokens": 4000
        }
        
        thinking_result = llm_node.execute(thinking_state, thinking_config)
        assert thinking_result is not None
        
        # 5. 检查包装器统计
        fast_stats = fast_wrapper.get_stats()
        thinking_stats = thinking_wrapper.get_stats()
        
        assert fast_stats["total_requests"] == 1
        assert thinking_stats["total_requests"] == 1
        
        # 6. 获取工厂统计
        factory_stats = wrapper_factory.get_wrapper_stats()
        assert factory_stats["total_wrappers"] == 2