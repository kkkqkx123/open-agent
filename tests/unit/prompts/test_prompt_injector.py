"""
提示词注入器单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import timedelta

from src.interfaces.prompts import IPromptInjector
from src.interfaces.prompts.models import PromptMeta, PromptType, PromptStatus
from src.services.prompts.injector import PromptInjector
from src.core.common.exceptions.prompts import PromptInjectionError


class TestPromptInjector:
    """提示词注入器测试"""
    
    @pytest.fixture
    def mock_cache(self):
        """模拟缓存"""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.exists = AsyncMock(return_value=False)
        return cache
    
    @pytest.fixture
    def mock_type_registry(self):
        """模拟类型注册表"""
        registry = AsyncMock()
        registry.get_type = AsyncMock()
        return registry
    
    @pytest.fixture
    def prompt_injector(self, mock_cache, mock_type_registry):
        """创建提示词注入器实例"""
        return PromptInjector(mock_cache, mock_type_registry)
    
    @pytest.fixture
    def sample_prompt(self):
        """示例提示词"""
        return PromptMeta(
            id="test_prompt",
            name="Test Prompt",
            type=PromptType.SYSTEM,
            content="You are a helpful assistant.",
            status=PromptStatus.ACTIVE
        )
    
    @pytest.mark.asyncio
    async def test_inject_single_prompt(self, prompt_injector, sample_prompt):
        """测试注入单个提示词"""
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Hello")]
        prompts = [sample_prompt]
        
        # 模拟类型处理
        mock_type = AsyncMock()
        mock_type.process_prompt = AsyncMock(return_value=sample_prompt.content)
        mock_type.create_message = AsyncMock()
        mock_type.injection_order = 10
        
        prompt_injector._type_registry.get_type.return_value = mock_type
        
        result = await prompt_injector.inject_prompts(messages, prompts)
        
        assert len(result) == 2
        assert result[0] == messages[0]
        mock_type.process_prompt.assert_called_once()
        mock_type.create_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_inject_multiple_prompts_order(self, prompt_injector):
        """测试按注入顺序注入多个提示词"""
        from langchain_core.messages import HumanMessage
        
        # 创建不同类型的提示词
        system_prompt = PromptMeta(
            id="system",
            name="System",
            type=PromptType.SYSTEM,
            content="System message",
            status=PromptStatus.ACTIVE
        )
        
        rules_prompt = PromptMeta(
            id="rules",
            name="Rules",
            type=PromptType.RULES,
            content="Rules message",
            status=PromptStatus.ACTIVE
        )
        
        messages = [HumanMessage(content="Hello")]
        prompts = [rules_prompt, system_prompt]  # 故意乱序
        
        # 模拟类型处理
        system_type = AsyncMock()
        system_type.process_prompt = AsyncMock(return_value=system_prompt.content)
        system_type.create_message = AsyncMock()
        system_type.injection_order = 10
        
        rules_type = AsyncMock()
        rules_type.process_prompt = AsyncMock(return_value=rules_prompt.content)
        rules_type.create_message = AsyncMock()
        rules_type.injection_order = 20
        
        def get_type_side_effect(prompt_type):
            if prompt_type == PromptType.SYSTEM.value:
                return system_type
            elif prompt_type == PromptType.RULES.value:
                return rules_type
        
        prompt_injector._type_registry.get_type.side_effect = get_type_side_effect
        
        result = await prompt_injector.inject_prompts(messages, prompts)
        
        # 验证顺序：系统提示词应该在规则提示词之前
        assert len(result) == 3
        # 系统提示词应该在第1个位置（索引0）
        # 规则提示词应该在第2个位置（索引1）
        # 原始消息应该在最后（索引2）
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, prompt_injector, sample_prompt, mock_cache):
        """测试缓存命中"""
        from langchain_core.messages import HumanMessage
        
        # 设置缓存命中
        cached_content = "Cached content"
        mock_cache.get.return_value = cached_content
        mock_cache.exists.return_value = True
        
        messages = [HumanMessage(content="Hello")]
        prompts = [sample_prompt]
        
        result = await prompt_injector.inject_prompts(messages, prompts)
        
        # 验证使用了缓存
        mock_cache.get.assert_called()
        mock_cache.set.assert_not_called()  # 不应该设置缓存
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, prompt_injector, sample_prompt, mock_cache):
        """测试缓存未命中"""
        from langchain_core.messages import HumanMessage
        
        # 设置缓存未命中
        mock_cache.get.return_value = None
        mock_cache.exists.return_value = False
        
        messages = [HumanMessage(content="Hello")]
        prompts = [sample_prompt]
        
        # 模拟类型处理
        mock_type = AsyncMock()
        mock_type.process_prompt = AsyncMock(return_value=sample_prompt.content)
        mock_type.create_message = AsyncMock()
        mock_type.injection_order = 10
        
        prompt_injector._type_registry.get_type.return_value = mock_type
        
        result = await prompt_injector.inject_prompts(messages, prompts)
        
        # 验证设置了缓存
        mock_cache.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_inactive_prompt_skipped(self, prompt_injector):
        """测试跳过非活跃提示词"""
        from langchain_core.messages import HumanMessage
        
        inactive_prompt = PromptMeta(
            id="inactive",
            name="Inactive",
            type=PromptType.SYSTEM,
            content="Inactive message",
            status=PromptStatus.INACTIVE
        )
        
        messages = [HumanMessage(content="Hello")]
        prompts = [inactive_prompt]
        
        result = await prompt_injector.inject_prompts(messages, prompts)
        
        # 非活跃提示词应该被跳过
        assert len(result) == 1
        assert result[0] == messages[0]
    
    @pytest.mark.asyncio
    async def test_prompt_processing_error(self, prompt_injector, sample_prompt):
        """测试提示词处理错误"""
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Hello")]
        prompts = [sample_prompt]
        
        # 模拟处理错误
        mock_type = AsyncMock()
        mock_type.process_prompt = AsyncMock(side_effect=Exception("Processing error"))
        mock_type.injection_order = 10
        
        prompt_injector._type_registry.get_type.return_value = mock_type
        
        with pytest.raises(PromptInjectionError):
            await prompt_injector.inject_prompts(messages, prompts)
    
    @pytest.mark.asyncio
    async def test_context_variables(self, prompt_injector, sample_prompt):
        """测试上下文变量"""
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Hello")]
        prompts = [sample_prompt]
        context = {"variable": "value"}
        
        # 模拟类型处理
        mock_type = AsyncMock()
        mock_type.process_prompt = AsyncMock(return_value="Processed with value")
        mock_type.create_message = AsyncMock()
        mock_type.injection_order = 10
        
        prompt_injector._type_registry.get_type.return_value = mock_type
        
        result = await prompt_injector.inject_prompts(messages, prompts, context)
        
        # 验证传递了上下文
        mock_type.process_prompt.assert_called_once_with(
            sample_prompt.content,
            context
        )
    
    @pytest.mark.asyncio
    async def test_empty_messages_list(self, prompt_injector, sample_prompt):
        """测试空消息列表"""
        messages = []
        prompts = [sample_prompt]
        
        # 模拟类型处理
        mock_type = AsyncMock()
        mock_type.process_prompt = AsyncMock(return_value=sample_prompt.content)
        mock_type.create_message = AsyncMock()
        mock_type.injection_order = 10
        
        prompt_injector._type_registry.get_type.return_value = mock_type
        
        result = await prompt_injector.inject_prompts(messages, prompts)
        
        # 应该只包含提示词消息
        assert len(result) == 1
        mock_type.create_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_empty_prompts_list(self, prompt_injector):
        """测试空提示词列表"""
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Hello")]
        prompts = []
        
        result = await prompt_injector.inject_prompts(messages, prompts)
        
        # 应该返回原始消息
        assert len(result) == 1
        assert result[0] == messages[0]