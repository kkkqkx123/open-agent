"""
提示词与工作流集成测试
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.services.workflow.building.builder_service import WorkflowBuilderService
from src.core.workflow.graph.nodes.llm_node import LLMNode
from src.services.prompts.registry import PromptRegistry
from src.services.prompts.injector import PromptInjector
from src.services.prompts.cache.memory_cache import MemoryPromptCache
from src.core.prompts.type_registry import get_global_registry
from src.interfaces.prompts.models import (
    PromptMeta,
    PromptConfig,
    PromptType,
    PromptStatus
)
from src.interfaces.state.workflow import IWorkflowState
from src.core.state.workflow_state import WorkflowState
from src.core.common.exceptions.prompts import PromptNotFoundError


class TestPromptWorkflowIntegration:
    """提示词与工作流集成测试"""
    
    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端"""
        client = AsyncMock()
        response = Mock()
        response.content = "Test response"
        client.generate = AsyncMock(return_value=response)
        return client
    
    @pytest.fixture
    def prompt_registry(self):
        """创建提示词注册表"""
        # 创建模拟加载器
        mock_loader = AsyncMock()
        
        registry = PromptRegistry(mock_loader)
        return registry
    
    @pytest.fixture
    def prompt_injector(self):
        """创建提示词注入器"""
        cache = MemoryPromptCache()
        type_registry = get_global_registry()
        return PromptInjector(cache, type_registry)
    
    @pytest.fixture
    def workflow_builder(self, prompt_registry, prompt_injector):
        """创建工作流构建器"""
        builder = WorkflowBuilderService()
        builder.configure_prompt_system(prompt_registry, prompt_injector)
        return builder
    
    @pytest.fixture
    async def sample_prompts(self, prompt_registry):
        """创建示例提示词"""
        system_prompt = PromptMeta(
            id="system_prompt",
            name="System Prompt",
            type=PromptType.SYSTEM,
            content="You are a helpful assistant.",
            status=PromptStatus.ACTIVE
        )
        
        user_prompt = PromptMeta(
            id="user_prompt",
            name="User Prompt",
            type=PromptType.USER_COMMAND,
            content="Please help me with: {{task}}",
            status=PromptStatus.ACTIVE
        )
        
        rules_prompt = PromptMeta(
            id="rules_prompt",
            name="Rules Prompt",
            type=PromptType.RULES,
            content="1. Be polite\n2. Be helpful\n3. Be concise",
            status=PromptStatus.ACTIVE
        )
        
        await prompt_registry.register(system_prompt)
        await prompt_registry.register(user_prompt)
        await prompt_registry.register(rules_prompt)
        
        return {
            "system": system_prompt,
            "user": user_prompt,
            "rules": rules_prompt
        }
    
    @pytest.mark.asyncio
    async def test_build_workflow_with_prompts(
        self,
        workflow_builder,
        sample_prompts
    ):
        """测试构建带提示词的工作流"""
        config = {
            "name": "test_workflow",
            "description": "Test workflow with prompts",
            "nodes": [
                {
                    "id": "llm_node",
                    "type": "llm",
                    "config": {
                        "max_tokens": 100,
                        "temperature": 0.7
                    },
                    "prompts": {
                        "system_prompt": "system_prompt",
                        "user_prompt": "user_prompt",
                        "variables": {
                            "task": "test task"
                        }
                    }
                }
            ],
            "edges": []
        }
        
        workflow = workflow_builder.build_workflow(config)
        
        assert workflow is not None
        assert "llm_node" in workflow.nodes
    
    @pytest.mark.asyncio
    async def test_enhanced_llm_node_execution(
        self,
        prompt_registry,
        prompt_injector,
        sample_prompts,
        mock_llm_client
    ):
        """测试增强LLM节点执行"""
        # 创建节点
        node = LLMNode(
            llm_client=mock_llm_client,
            prompt_registry=prompt_registry,
            prompt_injector=prompt_injector
        )
        
        # 配置提示词系统
        node.configure_prompt_system(prompt_registry, prompt_injector)
        
        # 创建状态
        state = WorkflowState()
        input_data = {"user_input": "Hello"}
        
        # 执行节点
        config = {
            "system_prompt_id": "system_prompt",
            "user_prompt_id": "user_prompt",
            "prompt_variables": {
                "task": "test task"
            },
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        result = await node.execute(state, config)
        
        assert result is not None
        assert "llm_response" in result.metadata
        mock_llm_client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prompt_injection_in_workflow(
        self,
        workflow_builder,
        sample_prompts
    ):
        """测试工作流中的提示词注入"""
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Hello")]
        prompt_ids = ["system_prompt", "rules_prompt"]
        
        injected_messages = await workflow_builder.inject_prompts_to_messages(
            messages,
            prompt_ids,
            {"task": "test"}
        )
        
        # 应该包含原始消息和注入的提示词
        assert len(injected_messages) >= 2
        assert injected_messages[-1] == messages[0]  # 原始消息在最后
    
    @pytest.mark.asyncio
    async def test_prompt_reference_resolution(
        self,
        workflow_builder,
        prompt_registry,
        sample_prompts
    ):
        """测试提示词引用解析"""
        # 创建带引用的提示词
        ref_prompt = PromptMeta(
            id="ref_prompt",
            name="Reference Prompt",
            type=PromptType.SYSTEM,
            content="Base: {{ref:system_prompt}}\nAdditional context",
            status=PromptStatus.ACTIVE
        )
        
        await prompt_registry.register(ref_prompt)
        
        # 解析引用
        resolved = await workflow_builder.resolve_prompt_references(
            "Base: {{ref:system_prompt}}\nAdditional context",
            {"task": "test"}
        )
        
        assert "You are a helpful assistant" in resolved
        assert "Additional context" in resolved
    
    @pytest.mark.asyncio
    async def test_workflow_prompt_validation(
        self,
        workflow_builder,
        sample_prompts
    ):
        """测试工作流提示词验证"""
        # 创建有效的工作流配置
        config = {
            "name": "test_workflow",
            "nodes": [
                {
                    "id": "llm_node",
                    "type": "llm",
                    "config": {},
                    "prompts": {
                        "system_prompt": "system_prompt",
                        "user_prompt": "user_prompt"
                    }
                }
            ]
        }
        
        workflow_builder.build_workflow(config)
        
        # 验证提示词
        errors = workflow_builder.validate_config(config)
        assert len(errors) == 0  # 应该没有错误
    
    @pytest.mark.asyncio
    async def test_workflow_with_invalid_prompts(
        self,
        workflow_builder
    ):
        """测试包含无效提示词的工作流"""
        config = {
            "name": "test_workflow",
            "nodes": [
                {
                    "id": "llm_node",
                    "type": "llm",
                    "config": {},
                    "prompts": {
                        "system_prompt": "nonexistent_prompt",
                        "user_prompt": "user_prompt"
                    }
                }
            ]
        }
        
        # 应该抛出错误
        with pytest.raises(Exception):
            workflow_builder.build_workflow(config)
    
    @pytest.mark.asyncio
    async def test_prompt_caching_in_workflow(
        self,
        workflow_builder,
        sample_prompts
    ):
        """测试工作流中的提示词缓存"""
        # 第一次注入
        messages1 = await workflow_builder.inject_prompts_to_messages(
            [],
            ["system_prompt"],
            {}
        )
        
        # 第二次注入（应该使用缓存）
        messages2 = await workflow_builder.inject_prompts_to_messages(
            [],
            ["system_prompt"],
            {}
        )
        
        # 结果应该相同
        assert len(messages1) == len(messages2)
        assert type(messages1[0]) == type(messages2[0])
    
    @pytest.mark.asyncio
    async def test_complex_workflow_with_multiple_nodes(
        self,
        workflow_builder,
        sample_prompts
    ):
        """测试复杂工作流与多个节点"""
        config = {
            "name": "complex_workflow",
            "description": "Complex workflow with multiple nodes",
            "nodes": [
                {
                    "id": "node1",
                    "type": "llm",
                    "config": {"max_tokens": 100},
                    "prompts": {
                        "system_prompt": "system_prompt",
                        "user_prompt": "user_prompt",
                        "variables": {"task": "task1"}
                    }
                },
                {
                    "id": "node2",
                    "type": "llm",
                    "config": {"max_tokens": 200},
                    "prompts": {
                        "system_prompt": "system_prompt",
                        "user_prompt": "user_prompt",
                        "variables": {"task": "task2"}
                    }
                }
            ],
            "edges": [
                {
                    "source": "node1",
                    "target": "node2"
                }
            ]
        }
        
        workflow = workflow_builder.build_workflow(config)
        
        # 验证工作流结构
        assert len(workflow.nodes) == 2
        assert "node1" in workflow.nodes
        assert "node2" in workflow.nodes
        assert len(workflow.edges) == 1
    
    @pytest.mark.asyncio
    async def test_prompt_variables_substitution(
        self,
        workflow_builder,
        sample_prompts
    ):
        """测试提示词变量替换"""
        # 创建带变量的提示词
        var_prompt = PromptMeta(
            id="var_prompt",
            name="Variable Prompt",
            type=PromptType.USER_COMMAND,
            content="Hello {{name}}, your task is: {{task}}",
            status=PromptStatus.ACTIVE
        )
        
        # 注册提示词到注册表
        await workflow_builder._prompt_service._prompt_registry.register(var_prompt)
        
        # 注入带变量的提示词
        messages = await workflow_builder.inject_prompts_to_messages(
            [],
            ["var_prompt"],
            {
                "name": "Alice",
                "task": "testing"
            }
        )
        
        # 验证变量替换
        content = messages[0].content
        assert "Alice" in content
        assert "testing" in content
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(
        self,
        workflow_builder,
        sample_prompts
    ):
        """测试工作流中的错误处理"""
        # 测试不存在的提示词
        with pytest.raises(Exception):
            await workflow_builder.inject_prompts_to_messages(
                [],
                ["nonexistent_prompt"],
                {}
            )
        
        # 测试无效的引用
        with pytest.raises(Exception):
            await workflow_builder.resolve_prompt_references(
                "{{ref:nonexistent_prompt}}",
                {}
            )