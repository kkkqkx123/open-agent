# HumanRelay LLM 测试指南

## 测试策略概述

HumanRelay LLM 的测试需要覆盖以下方面：
- 单元测试：核心功能测试
- 集成测试：与现有系统的集成
- 端到端测试：完整工作流测试
- 性能测试：响应时间和资源使用

## 单元测试

### 1. HumanRelay客户端测试

**文件位置**: `tests/unit/infrastructure/llm/test_human_relay.py`

```python
"""HumanRelay客户端单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.infrastructure.llm.clients.human_relay import HumanRelayClient
from src.infrastructure.llm.config import HumanRelayConfig
from src.infrastructure.llm.models import LLMResponse, TokenUsage


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
        return frontend
    
    @pytest.mark.asyncio
    async def test_single_turn_generate(self, mock_config, mock_frontend):
        """测试单轮对话模式"""
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface', 
                  return_value=mock_frontend):
            client = HumanRelayClient(mock_config)
            
            messages = [HumanMessage(content="测试消息")]
            parameters = {"temperature": 0.7}
            
            response = await client._single_turn_generate(messages, parameters)
            
            # 验证响应格式
            assert isinstance(response, LLMResponse)
            assert response.content == "Mock Web LLM response"
            assert response.model == "test-human-relay"
            
            # 验证前端调用
            mock_frontend.prompt_user.assert_called_once()
            call_args = mock_frontend.prompt_user.call_args
            assert call_args.kwargs['mode'] == 'single'
            assert '测试消息' in call_args.kwargs['prompt']
    
    @pytest.mark.asyncio
    async def test_multi_turn_generate(self, mock_config, mock_frontend):
        """测试多轮对话模式"""
        mock_config.mode = "multi"
        
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface', 
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
            
            # 验证前端调用参数
            calls = mock_frontend.prompt_user.call_args_list
            assert len(calls) == 2
            assert calls[1].kwargs['mode'] == 'multi'
            assert 'conversation_history' in calls[1].kwargs
    
    def test_conversation_history_management(self, mock_config):
        """测试对话历史管理"""
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface'):
            client = HumanRelayClient(mock_config)
            client.max_history_length = 3
            
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
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface'):
            client = HumanRelayClient(mock_config)
            
            messages = [
                HumanMessage(content="用户消息"),
                AIMessage(content="AI回复"),
                HumanMessage(content="最新消息")
            ]
            
            prompt = client._build_full_prompt(messages)
            
            assert "最新消息" in prompt
            assert "用户消息" in prompt  # 应该包含所有消息
    
    def test_prompt_building_multi_mode(self, mock_config):
        """测试多轮模式提示词构建"""
        mock_config.mode = "multi"
        
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface'):
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
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_config):
        """测试超时处理"""
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(side_effect=TimeoutError("前端超时"))
        
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface', 
                  return_value=mock_frontend):
            client = HumanRelayClient(mock_config)
            
            with pytest.raises(TimeoutError):
                await client._single_turn_generate([HumanMessage(content="测试")], {})
```

### 2. 前端接口测试

**文件位置**: `tests/unit/infrastructure/llm/test_frontend_interface.py`

```python
"""前端接口单元测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.infrastructure.llm.frontend_interface import FrontendInterface


class TestFrontendInterface:
    """前端接口测试类"""
    
    @pytest.fixture
    def tui_config(self):
        """TUI配置"""
        return {
            "interface_type": "tui",
            "tui_config": {
                "prompt_style": "highlight",
                "input_area_height": 10
            }
        }
    
    @pytest.fixture
    def web_config(self):
        """Web配置"""
        return {
            "interface_type": "web",
            "web_config": {
                "endpoint": "/api/human-relay",
                "websocket": True
            }
        }
    
    @pytest.mark.asyncio
    async def test_tui_interface(self, tui_config):
        """测试TUI接口"""
        with patch('src.infrastructure.llm.frontend_interface.HumanRelayPanel') as mock_panel:
            mock_panel_instance = Mock()
            mock_panel_instance.show_prompt = AsyncMock(return_value="TUI响应")
            mock_panel.return_value = mock_panel_instance
            
            interface = FrontendInterface(tui_config)
            response = await interface.prompt_user("测试提示词", "single")
            
            assert response == "TUI响应"
            mock_panel_instance.show_prompt.assert_called_once_with(
                "测试提示词", "single"
            )
    
    @pytest.mark.asyncio
    async def test_web_interface_not_implemented(self, web_config):
        """测试Web接口未实现"""
        interface = FrontendInterface(web_config)
        
        with pytest.raises(NotImplementedError):
            await interface.prompt_user("测试提示词", "single")
    
    def test_invalid_interface_type(self):
        """测试无效接口类型"""
        config = {"interface_type": "invalid"}
        
        with pytest.raises(ValueError):
            FrontendInterface(config)
```

## 集成测试

### 1. 工厂集成测试

**文件位置**: `tests/integration/test_human_relay_factory.py`

```python
"""HumanRelay工厂集成测试"""

import pytest
from src.infrastructure.llm.factory import LLMFactory
from src.infrastructure.llm.config import HumanRelayConfig


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
        assert client.mode == "multi"
        assert client.max_history_length == 100
    
    def test_config_validation(self):
        """测试配置验证"""
        factory = LLMFactory()
        
        # 无效配置应该抛出异常
        invalid_config = {
            "model_type": "human_relay",
            "model_name": "test",
            "parameters": {
                "mode": "invalid_mode"  # 无效模式
            }
        }
        
        with pytest.raises(ValueError):
            factory.create_client(invalid_config)
```

### 2. 配置加载测试

**文件位置**: `tests/integration/test_human_relay_config.py`

```python
"""HumanRelay配置加载测试"""

import pytest
import tempfile
import os
from src.infrastructure.config_loader import ConfigLoader


class TestHumanRelayConfig:
    """HumanRelay配置测试"""
    
    def test_config_loading_from_yaml(self):
        """测试从YAML加载配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
model_type: human_relay
model_name: test-human-relay
parameters:
  mode: single
  frontend_timeout: 300
human_relay_config:
  prompt_template: "自定义模板: {prompt}"
            """)
            config_file = f.name
        
        try:
            loader = ConfigLoader()
            config = loader.load_llm_config(config_file)
            
            assert config.model_type == "human_relay"
            assert config.parameters["mode"] == "single"
            assert "prompt_template" in config.human_relay_config
        finally:
            os.unlink(config_file)
    
    def test_config_inheritance(self):
        """测试配置继承"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as base_file:
            base_file.write("""
model_type: human_relay
parameters:
  mode: single
  frontend_timeout: 300
            """)
            base_config = base_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as child_file:
            child_file.write(f"""
inherits_from: "{base_config}"
model_name: custom-human-relay
parameters:
  frontend_timeout: 600  # 覆盖父配置
            """)
            child_config = child_file.name
        
        try:
            loader = ConfigLoader()
            config = loader.load_llm_config(child_config)
            
            assert config.model_type == "human_relay"
            assert config.model_name == "custom-human-relay"
            assert config.parameters["mode"] == "single"  # 继承
            assert config.parameters["frontend_timeout"] == 600  # 覆盖
        finally:
            os.unlink(base_config)
            os.unlink(child_config)
```

## 端到端测试

### 1. 完整工作流测试

**文件位置**: `tests/integration/test_human_relay_workflow.py`

```python
"""HumanRelay端到端工作流测试"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.infrastructure.llm.factory import get_global_factory


class TestHumanRelayWorkflow:
    """HumanRelay工作流测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_single_turn(self):
        """测试单轮模式端到端工作流"""
        # 模拟前端交互
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(return_value="Web LLM的回复内容")
        
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface', 
                  return_value=mock_frontend):
            
            # 创建客户端
            factory = get_global_factory()
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
            
            # 验证前端调用
            mock_frontend.prompt_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_end_to_end_multi_turn(self):
        """测试多轮模式端到端工作流"""
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(return_value="第二轮回复")
        
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface', 
                  return_value=mock_frontend):
            
            factory = get_global_factory()
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
            
            # 验证前端调用次数
            assert mock_frontend.prompt_user.call_count == 2
```

## 性能测试

### 1. 响应时间测试

**文件位置**: `tests/performance/test_human_relay_performance.py`

```python
"""HumanRelay性能测试"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from src.infrastructure.llm.factory import LLMFactory


class TestHumanRelayPerformance:
    """HumanRelay性能测试"""
    
    @pytest.mark.asyncio
    async def test_response_time_single_turn(self):
        """测试单轮模式响应时间"""
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(return_value="测试响应")
        
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface', 
                  return_value=mock_frontend):
            
            factory = LLMFactory()
            config = {
                "model_type": "human-relay-s",
                "model_name": "human-relay-s",
                "parameters": {"mode": "single"}
            }
            
            client = factory.create_client(config)
            
            start_time = time.time()
            await client.generate_async([{"role": "user", "content": "测试"}])
            end_time = time.time()
            
            response_time = end_time - start_time
            # 响应时间应该在合理范围内（主要取决于前端模拟）
            assert response_time < 1.0  # 1秒内完成
    
    @pytest.mark.asyncio
    async def test_memory_usage_multi_turn(self):
        """测试多轮模式内存使用"""
        mock_frontend = Mock()
        mock_frontend.prompt_user = AsyncMock(return_value="测试响应")
        
        with patch('src.infrastructure.llm.clients.human_relay.FrontendInterface', 
                  return_value=mock_frontend):
            
            factory = LLMFactory()
            config = {
                "model_type": "human-relay-m",
                "model_name": "human-relay-m",
                "parameters": {
                    "mode": "multi",
                    "max_history_length": 5  # 限制历史长度
                }
            }
            
            client = factory.create_client(config)
            
            # 生成超过限制的消息
            for i in range(10):
                await client.generate_async([{"role": "user", "content": f"消息{i}"}])
            
            # 验证历史长度不超过限制
            assert len(client.conversation_history) <= 5
```

## 测试运行命令

### 运行所有HumanRelay测试

```bash
# 运行单元测试
pytest tests/unit/infrastructure/llm/test_human_relay.py -v
pytest tests/unit/infrastructure/llm/test_frontend_interface.py -v

# 运行集成测试
pytest tests/integration/test_human_relay_factory.py -v
pytest tests/integration/test_human_relay_config.py -v
pytest tests/integration/test_human_relay_workflow.py -v

# 运行性能测试
pytest tests/performance/test_human_relay_performance.py -v

# 运行所有HumanRelay相关测试
pytest tests/ -k "human_relay" -v
```

### 测试覆盖率

```bash
# 生成测试覆盖率报告
pytest tests/ -k "human_relay" --cov=src.infrastructure.llm.clients.human_relay --cov-report=html
```

## 测试最佳实践

1. **模拟外部依赖**: 使用Mock对象模拟前端交互
2. **测试边界条件**: 包括超时、空输入、历史限制等
3. **验证配置**: 确保配置加载和验证正确
4. **性能基准**: 建立性能基准并监控回归
5. **集成测试**: 确保与现有系统正确集成

这些测试用例确保了HumanRelay LLM的可靠性和稳定性。