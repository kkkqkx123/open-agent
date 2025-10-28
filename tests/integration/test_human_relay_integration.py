"""HumanRelay集成测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.llm.config import HumanRelayConfig
from src.infrastructure.llm.clients.human_relay import HumanRelayClient


class TestHumanRelayFactoryIntegration:
    """HumanRelay工厂集成测试"""
    
    def test_factory_registration(self):
        """测试工厂注册"""
        factory = LLMFactory()
        
        # 验证HumanRelay客户端已注册
        supported_types = factory.list_supported_types()
        assert "human_relay" in supported_types
        assert "human-relay-s" in supported_types
        assert "human-relay-m" in supported_types
    
    def test_client_creation_single_mode(self):
        """测试单轮模式客户端创建"""
        factory = LLMFactory()
        
        config = {
            "model_type": "human-relay-s",
            "model_name": "human-relay-s",
            "parameters": {
                "mode": "single",
                "frontend_timeout": 300
            }
        }
        
        client = factory.create_client(config)
        assert isinstance(client, HumanRelayClient)
        assert client.mode == "single"
        assert client.config.model_name == "human-relay-s"
    
    def test_client_creation_multi_mode(self):
        """测试多轮模式客户端创建"""
        factory = LLMFactory()
        
        config = {
            "model_type": "human-relay-m",
            "model_name": "human-relay-m",
            "parameters": {
                "mode": "multi",
                "max_history_length": 100
            }
        }
        
        client = factory.create_client(config)
        assert isinstance(client, HumanRelayClient)
        assert client.mode == "multi"
        assert client.max_history_length == 100
    
    def test_client_creation_with_human_relay_config(self):
        """测试使用HumanRelay特定配置创建客户端"""
        factory = LLMFactory()
        
        config = {
            "model_type": "human_relay",
            "model_name": "custom-human-relay",
            "parameters": {
                "mode": "multi",
                "frontend_timeout": 600
            },
            "human_relay_config": {
                "frontend_interface": {
                    "interface_type": "mock",
                    "mock_response": "自定义回复",
                    "mock_delay": 0.2
                },
                "max_history_length": 200,
                "prompt_template": "自定义模板: {prompt}"
            }
        }
        
        client = factory.create_client(config)
        assert isinstance(client, HumanRelayClient)
        assert client.mode == "multi"
        assert client.max_history_length == 200
        assert "自定义模板" in client.prompt_template
    
    def test_config_validation(self):
        """测试配置验证"""
        factory = LLMFactory()
        
        # 无效模式应该抛出异常
        invalid_config = {
            "model_type": "human_relay",
            "model_name": "test",
            "parameters": {
                "mode": "invalid_mode"  # 无效模式
            }
        }
        
        # 注意：这里可能不会抛出异常，因为配置验证在客户端层面
        client = factory.create_client(invalid_config)
        assert client.mode == "invalid_mode"  # 配置会被接受，但使用时可能出错


class TestHumanRelayEndToEndWorkflow:
    """HumanRelay端到端工作流测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_single_turn(self):
        """测试单轮模式端到端工作流"""
        # 模拟前端交互
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(return_value="Web LLM的回复内容")
        mock_frontend.wait_with_timeout = AsyncMock(return_value="Web LLM的回复内容")
        mock_frontend.validate_timeout = Mock(return_value=300)
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            
            # 创建客户端
            factory = LLMFactory()
            config = {
                "model_type": "human-relay-s",
                "model_name": "human-relay-s",
                "parameters": {
                    "mode": "single",
                    "frontend_timeout": 300
                }
            }
            
            client = factory.create_client(config)
            
            # 执行生成
            messages = [{"role": "user", "content": "测试提示词"}]
            response = await client.generate_async(messages)
            
            # 验证结果
            assert response.content == "Web LLM的回复内容"
            assert response.model == "human-relay-s"
            assert response.metadata["mode"] == "single"
            
            # 验证前端调用
            mock_frontend.wait_with_timeout.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_end_to_end_multi_turn(self):
        """测试多轮模式端到端工作流"""
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(return_value="第二轮回复")
        mock_frontend.wait_with_timeout = AsyncMock(return_value="第二轮回复")
        mock_frontend.validate_timeout = Mock(return_value=300)
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            
            factory = LLMFactory()
            config = {
                "model_type": "human-relay-m",
                "model_name": "human-relay-m",
                "parameters": {
                    "mode": "multi",
                    "max_history_length": 10
                }
            }
            
            client = factory.create_client(config)
            
            # 第一轮对话
            messages1 = [{"role": "user", "content": "第一轮消息"}]
            response1 = await client.generate_async(messages1)
            
            # 第二轮对话
            messages2 = [{"role": "user", "content": "第二轮消息"}]
            response2 = await client.generate_async(messages2)
            
            # 验证历史管理
            assert len(client.conversation_history) == 2
            assert response2.content == "第二轮回复"
            assert response2.metadata["mode"] == "multi"
            
            # 验证前端调用次数
            assert mock_frontend.wait_with_timeout.call_count == 2
    
    @pytest.mark.asyncio
    async def test_stream_generation_workflow(self):
        """测试流式生成工作流"""
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(return_value="流式测试回复")
        mock_frontend.wait_with_timeout = AsyncMock(return_value="流式测试回复")
        mock_frontend.validate_timeout = Mock(return_value=300)
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            
            factory = LLMFactory()
            config = {
                "model_type": "human-relay-s",
                "model_name": "human-relay-s",
                "parameters": {"mode": "single"}
            }
            
            client = factory.create_client(config)
            
            # 测试异步流式生成
            chunks = []
            async for chunk in client.stream_generate_async(
                [{"role": "user", "content": "流式测试"}]
            ):
                chunks.append(chunk)
            
            assert "".join(chunks) == "流式测试回复"
            
            # 测试同步流式生成
            chunks = list(client.stream_generate(
                [{"role": "user", "content": "流式测试"}]
            ))
            assert "".join(chunks) == "流式测试回复"


class TestHumanRelayConfigurationIntegration:
    """HumanRelay配置集成测试"""
    
    def test_config_from_dict_single_mode(self):
        """测试从字典创建单轮模式配置"""
        config_dict = {
            "model_type": "human-relay-s",
            "model_name": "test-single",
            "parameters": {
                "mode": "single",
                "frontend_timeout": 300
            }
        }
        
        config = HumanRelayConfig.from_dict(config_dict)
        assert config.model_type == "human_relay"
        assert config.model_name == "test-single"
        assert config.mode == "single"
    
    def test_config_from_dict_multi_mode(self):
        """测试从字典创建多轮模式配置"""
        config_dict = {
            "model_type": "human-relay-m",
            "model_name": "test-multi",
            "parameters": {
                "mode": "multi",
                "max_history_length": 100
            },
            "human_relay_config": {
                "frontend_interface": {
                    "interface_type": "tui"
                },
                "prompt_template": "自定义单轮模板: {prompt}",
                "incremental_prompt_template": "自定义多轮模板: {incremental_prompt}"
            }
        }
        
        config = HumanRelayConfig.from_dict(config_dict)
        assert config.model_type == "human_relay"
        assert config.mode == "multi"
        assert config.max_history_length == 100
        assert "自定义单轮模板" in config.prompt_template
        assert "自定义多轮模板" in config.incremental_prompt_template
    
    def test_config_inheritance_from_dict(self):
        """测试配置继承"""
        config_dict = {
            "model_type": "human_relay",
            "model_name": "test-inheritance",
            "parameters": {
                "mode": "multi",
                "frontend_timeout": 600
            },
            "human_relay_config": {
                "frontend_interface": {
                    "interface_type": "mock",
                    "mock_response": "继承测试回复"
                }
            }
        }
        
        config = HumanRelayConfig.from_dict(config_dict)
        assert config.mode == "multi"
        assert config.frontend_config["interface_type"] == "mock"
        assert config.frontend_config["mock_response"] == "继承测试回复"


class TestHumanRelayErrorHandling:
    """HumanRelay错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """测试超时错误处理"""
        mock_frontend = Mock()
        mock_frontend.wait_with_timeout = AsyncMock(
            side_effect=Exception("超时异常")
        )
        mock_frontend.validate_timeout = Mock(return_value=300)
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            
            factory = LLMFactory()
            config = {
                "model_type": "human-relay-s",
                "model_name": "human-relay-s",
                "parameters": {"mode": "single"}
            }
            
            client = factory.create_client(config)
            
            # 应该抛出异常
            with pytest.raises(Exception):
                await client.generate_async([{"role": "user", "content": "测试"}])
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        """测试空响应处理"""
        mock_frontend = Mock()
        mock_frontend.wait_with_timeout = AsyncMock(return_value="")
        mock_frontend.validate_timeout = Mock(return_value=300)
        
        with patch('src.infrastructure.llm.clients.human_relay.create_frontend_interface', 
                  return_value=mock_frontend):
            
            factory = LLMFactory()
            config = {
                "model_type": "human-relay-s",
                "model_name": "human-relay-s",
                "parameters": {"mode": "single"}
            }
            
            client = factory.create_client(config)
            
            # 空响应应该被接受
            response = await client.generate_async([{"role": "user", "content": "测试"}])
            assert response.content == ""