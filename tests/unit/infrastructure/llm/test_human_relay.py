"""HumanRelay客户端单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.infrastructure.llm.clients.human_relay import HumanRelayClient
from src.infrastructure.llm.config import HumanRelayConfig
from src.infrastructure.llm.models import LLMResponse, TokenUsage
from src.infrastructure.llm.exceptions import LLMTimeoutError, LLMInvalidRequestError


class TestHumanRelayClient:
    """HumanRelay客户端测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """创建Mock配置"""
        return HumanRelayConfig(
            model_type="human_relay",
            model_name="test-human-relay",
            mode="single",
            frontend_config={"interface_type": "mock"}
        )
    
    @pytest.fixture
    def mock_frontend(self):
        """创建Mock前端接口"""
        frontend = Mock()
        frontend.prompt_user = AsyncMock(return_value="Mock Web LLM response")
        frontend.wait_with_timeout = AsyncMock(return_value="Mock Web LLM response")
        frontend.validate_timeout = Mock(return_value=300)
        return frontend
    
    @pytest.mark.asyncio
    async def test_single_turn_generate(self, mock_config, mock_frontend):
        """测试单轮对话模式"""
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            client = HumanRelayClient(mock_config)
            
            messages = [HumanMessage(content="测试消息")]
            parameters = {"temperature": 0.7}
            
            response = await client._single_turn_generate(messages, parameters)
            
            # 验证响应格式
            assert isinstance(response, LLMResponse)
            assert response.content == "Mock Web LLM response"
            assert response.model == "test-human-relay"
            assert response.metadata["mode"] == "single"
            
            # 验证前端调用
            mock_frontend.wait_with_timeout.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multi_turn_generate(self, mock_config, mock_frontend):
        """测试多轮对话模式"""
        mock_config.mode = "multi"
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            client = HumanRelayClient(mock_config)
            
            # 第一轮对话
            messages1 = [HumanMessage(content="第一轮消息")]
            response1 = await client._multi_turn_generate(messages1, {})
            
            # 第二轮对话
            messages2 = [HumanMessage(content="第二轮消息")]
            response2 = await client._multi_turn_generate(messages2, {})
            
            # 验证历史管理
            assert len(client.conversation_history) == 2
            assert response2.content == "Mock Web LLM response"
            assert response2.metadata["mode"] == "multi"
            
            # 验证前端调用次数
            assert mock_frontend.wait_with_timeout.call_count == 2
    
    def test_conversation_history_management(self, mock_config):
        """测试对话历史管理"""
        mock_config.max_history_length = 3
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface'):
            client = HumanRelayClient(mock_config)
            
            # 添加消息到历史
            messages = [
                HumanMessage(content="消息1"),
                HumanMessage(content="消息2"),
                HumanMessage(content="消息3"),
                HumanMessage(content="消息4")  # 超过限制
            ]
            
            client._update_conversation_history(messages)
            
            # 验证历史长度限制
            assert len(client.conversation_history) == 3
            assert client.conversation_history[0].content == "消息2"  # 最早的消息被移除
    
    def test_prompt_building_single_mode(self, mock_config):
        """测试单轮模式提示词构建"""
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface'):
            client = HumanRelayClient(mock_config)
            
            messages = [
                HumanMessage(content="用户消息"),
                AIMessage(content="AI回复"),
                HumanMessage(content="最新消息")
            ]
            
            prompt = client._build_full_prompt(messages)
            
            assert "最新消息" in prompt
            assert "用户消息" in prompt  # 应该包含所有消息
            assert "请将以下提示词输入到Web LLM中" in prompt
    
    def test_prompt_building_multi_mode(self, mock_config):
        """测试多轮模式提示词构建"""
        mock_config.mode = "multi"
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface'):
            client = HumanRelayClient(mock_config)
            
            # 先添加一些历史
            client.conversation_history = [
                HumanMessage(content="历史消息1"),
                AIMessage(content="历史回复1")
            ]
            
            new_messages = [HumanMessage(content="新消息")]
            prompt = client._build_incremental_prompt(new_messages)
            
            assert "新消息" in prompt
            assert "历史消息1" in prompt  # 应该包含历史
            assert "请继续对话，将以下提示词输入到Web LLM中" in prompt
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_config):
        """测试超时处理"""
        mock_frontend = Mock()
        mock_frontend.wait_with_timeout = AsyncMock(side_effect=LLMTimeoutError("前端超时"))
        mock_frontend.validate_timeout = Mock(return_value=300)
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            client = HumanRelayClient(mock_config)
            
            with pytest.raises(LLMTimeoutError):
                await client._single_turn_generate([HumanMessage(content="测试")], {})
    
    def test_token_count_estimation(self, mock_config):
        """测试Token计数估算"""
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface'):
            client = HumanRelayClient(mock_config)
            
            # 测试文本token计数
            text = "这是一个测试文本"
            token_count = client.get_token_count(text)
            assert token_count > 0
            assert token_count == len(text) // 4  # 简单估算逻辑
            
            # 测试消息token计数
            messages = [HumanMessage(content="测试消息")]
            message_token_count = client.get_messages_token_count(messages)
            assert message_token_count > 0
    
    def test_function_calling_support(self, mock_config):
        """测试函数调用支持"""
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface'):
            client = HumanRelayClient(mock_config)
            assert client.supports_function_calling() is True
    
    def test_conversation_history_operations(self, mock_config):
        """测试对话历史操作"""
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface'):
            client = HumanRelayClient(mock_config)
            
            # 测试清除历史
            client.conversation_history = [HumanMessage(content="测试")]
            client.clear_conversation_history()
            assert len(client.conversation_history) == 0
            
            # 测试获取历史
            history = [HumanMessage(content="测试1"), AIMessage(content="测试2")]
            client.conversation_history = history
            retrieved_history = client.get_conversation_history()
            assert len(retrieved_history) == 2
            assert retrieved_history is not client.conversation_history  # 应该是副本
            
            # 测试设置历史
            new_history = [HumanMessage(content="新消息")]
            client.set_conversation_history(new_history)
            assert len(client.conversation_history) == 1
            assert client.conversation_history[0].content == "新消息"
    
    def test_timeout_validation(self, mock_config):
        """测试超时验证"""
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface') as mock_create:
            mock_frontend = Mock()
            mock_frontend.validate_timeout.return_value = 300
            mock_create.return_value = mock_frontend
            
            client = HumanRelayClient(mock_config)
            
            # 测试从参数获取超时
            timeout = client._get_timeout({"frontend_timeout": 600})
            assert timeout == 600
            
            # 测试从配置获取超时
            timeout = client._get_timeout({})
            assert timeout == 300  # 默认值
    
    @pytest.mark.asyncio
    async def test_stream_generate(self, mock_config, mock_frontend):
        """测试流式生成"""
        mock_frontend.wait_with_timeout = AsyncMock(return_value="测试回复")
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            client = HumanRelayClient(mock_config)
            
            messages = [HumanMessage(content="测试")]
            
            # 测试异步流式生成
            chunks = []
            async for chunk in client._do_stream_generate_async(messages, {}):
                chunks.append(chunk)
            
            assert "".join(chunks) == "测试回复"
            
            # 测试同步流式生成
            chunks = list(client._do_stream_generate(messages, {}))
            assert "".join(chunks) == "测试回复"
    
    def test_empty_messages_validation(self, mock_config):
        """测试空消息验证"""
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface'):
            client = HumanRelayClient(mock_config)
            
            # 测试空消息列表
            with pytest.raises(LLMInvalidRequestError):
                client._build_full_prompt([])
            
            with pytest.raises(LLMInvalidRequestError):
                client._build_incremental_prompt([])


class TestHumanRelayConfig:
    """HumanRelay配置测试类"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = HumanRelayConfig(
            model_type="human_relay",
            model_name="test",
            mode="single"
        )
        assert config.mode == "single"
        assert config.max_history_length == 50
    
    def test_invalid_model_type(self):
        """测试无效模型类型"""
        with pytest.raises(ValueError, match="HumanRelayConfig的model_type必须为'human_relay'"):
            HumanRelayConfig(
                model_type="invalid",
                model_name="test"
            )
    
    def test_default_templates(self):
        """测试默认模板"""
        config = HumanRelayConfig(
            model_type="human_relay",
            model_name="test"
        )
        
        assert "请将以下提示词输入到Web LLM中" in config.prompt_template
        assert "请继续对话，将以下提示词输入到Web LLM中" in config.incremental_prompt_template
        assert "{prompt}" in config.prompt_template
        assert "{incremental_prompt}" in config.incremental_prompt_template
        assert "{conversation_history}" in config.incremental_prompt_template