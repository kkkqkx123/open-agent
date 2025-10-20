"""提示词管理模块集成测试"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory

from src.infrastructure.config_loader import YamlConfigLoader
from src.prompts.registry import PromptRegistry
from src.prompts.loader import PromptLoader
from src.prompts.injector import PromptInjector
from src.prompts.models import PromptConfig
from src.prompts.agent_state import AgentState, SystemMessage, HumanMessage


class TestPromptIntegration:
    """提示词管理模块集成测试类"""
    
    @pytest.fixture
    def temp_prompts_dir(self):
        """创建临时提示词目录"""
        with TemporaryDirectory() as temp_dir:
            prompts_dir = Path(temp_dir)
            
            # 创建系统提示词
            system_dir = prompts_dir / "system"
            system_dir.mkdir()
            
            # 简单系统提示词
            assistant_file = system_dir / "assistant.md"
            assistant_file.write_text("""---
description: 通用助手提示词
---
你是一个通用助手，负责解答用户问题。""", encoding='utf-8')
            
            # 复合系统提示词
            coder_dir = system_dir / "coder"
            coder_dir.mkdir()
            
            index_file = coder_dir / "index.md"
            index_file.write_text("""---
description: 代码生成专家
---
你是一个代码生成专家。""", encoding='utf-8')
            
            style_file = coder_dir / "01_code_style.md"
            style_file.write_text("""---
description: 代码风格
---
请遵循PEP8规范。""", encoding='utf-8')
            
            # 创建规则提示词
            rules_dir = prompts_dir / "rules"
            rules_dir.mkdir()
            
            safety_file = rules_dir / "safety.md"
            safety_file.write_text("""---
description: 安全规则
---
请遵循安全规则。""", encoding='utf-8')
            
            format_file = rules_dir / "format.md"
            format_file.write_text("""---
description: 格式规则
---
请遵循格式规则。""", encoding='utf-8')
            
            # 创建用户指令
            user_commands_dir = prompts_dir / "user_commands"
            user_commands_dir.mkdir()
            
            data_analysis_file = user_commands_dir / "data_analysis.md"
            data_analysis_file.write_text("""---
description: 数据分析指令
---
请分析提供的数据。""", encoding='utf-8')
            
            yield prompts_dir
    
    @pytest.fixture
    def temp_config_dir(self, temp_prompts_dir):
        """创建临时配置目录"""
        with TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # 创建提示词注册表配置
            prompts_config = config_dir / "prompts.yaml"
            prompts_config.write_text(f"""system:
  - name: assistant
    path: {temp_prompts_dir}/system/assistant.md
    description: 通用助手系统提示词
  - name: coder
    path: {temp_prompts_dir}/system/coder/
    description: 代码生成专家系统提示词
    is_composite: true

rules:
  - name: safety
    path: {temp_prompts_dir}/rules/safety.md
    description: 安全规则提示词
  - name: format
    path: {temp_prompts_dir}/rules/format.md
    description: 格式规则提示词

user_commands:
  - name: data_analysis
    path: {temp_prompts_dir}/user_commands/data_analysis.md
    description: 数据分析用户指令
""", encoding='utf-8')
            
            yield config_dir
    
    @pytest.fixture
    def config_loader(self, temp_config_dir):
        """创建配置加载器"""
        return YamlConfigLoader(str(temp_config_dir))
    
    @pytest.fixture
    def prompt_system(self, config_loader):
        """创建完整的提示词系统"""
        registry = PromptRegistry(config_loader)
        loader = PromptLoader(registry)
        injector = PromptInjector(loader)
        
        return registry, loader, injector
    
    def test_end_to_end_simple_prompt_injection(self, prompt_system):
        """测试端到端简单提示词注入"""
        registry, loader, injector = prompt_system
        
        # 验证注册表
        assert registry.validate_registry()
        
        # 创建配置
        config = PromptConfig(
            system_prompt="assistant",
            rules=["safety"],
            user_command="data_analysis"
        )
        
        # 注入提示词
        state = injector.inject_prompts(AgentState(), config)
        
        # 验证结果
        assert len(state.messages) == 3
        
        # 验证系统提示词
        assert isinstance(state.messages[0], SystemMessage)
        assert "通用助手" in state.messages[0].content
        
        # 验证规则提示词
        assert isinstance(state.messages[1], SystemMessage)
        assert "安全规则" in state.messages[1].content
        
        # 验证用户指令
        assert isinstance(state.messages[2], HumanMessage)
        assert "分析" in state.messages[2].content
    
    def test_end_to_end_composite_prompt_injection(self, prompt_system):
        """测试端到端复合提示词注入"""
        registry, loader, injector = prompt_system
        
        # 创建配置
        config = PromptConfig(
            system_prompt="coder",  # 复合提示词
            rules=["format"]
        )
        
        # 注入提示词
        state = injector.inject_prompts(AgentState(), config)
        
        # 验证结果
        assert len(state.messages) == 2
        
        # 验证复合系统提示词
        assert isinstance(state.messages[0], SystemMessage)
        content = state.messages[0].content
        assert "代码生成专家" in content
        assert "PEP8规范" in content
        assert "---" in content  # 分隔符应该存在
        
        # 验证规则提示词
        assert isinstance(state.messages[1], SystemMessage)
        assert "格式规则" in state.messages[1].content
    
    def test_caching_mechanism(self, prompt_system):
        """测试缓存机制"""
        registry, loader, injector = prompt_system
        
        # 第一次加载
        content1 = loader.load_prompt("system", "assistant")
        
        # 第二次加载（应该从缓存获取）
        content2 = loader.load_prompt("system", "assistant")
        
        assert content1 == content2
        assert len(loader._cache) > 0
        
        # 清空缓存
        loader.clear_cache()
        assert len(loader._cache) == 0
        
        # 再次加载（应该重新读取文件）
        content3 = loader.load_prompt("system", "assistant")
        assert content1 == content3
    
    def test_error_handling(self, prompt_system):
        """测试错误处理"""
        registry, loader, injector = prompt_system
        
        # 测试不存在的提示词
        with pytest.raises(ValueError, match="提示词不存在"):
            loader.load_prompt("system", "nonexistent")
        
        # 测试不存在的类别
        with pytest.raises(ValueError, match="不支持的提示词类别"):
            loader.load_prompt("invalid_category", "assistant")
        
        # 测试注入不存在的提示词
        config = PromptConfig(system_prompt="nonexistent")
        with pytest.raises(ValueError, match="注入系统提示词失败"):
            injector.inject_prompts(AgentState(), config)
    
    def test_prompt_ordering(self, prompt_system):
        """测试提示词顺序"""
        registry, loader, injector = prompt_system
        
        # 创建包含所有类型提示词的配置
        config = PromptConfig(
            system_prompt="assistant",
            rules=["safety", "format"],
            user_command="data_analysis"
        )
        
        # 注入提示词
        state = injector.inject_prompts(AgentState(), config)
        
        # 验证消息顺序
        assert len(state.messages) == 4
        
        # 系统提示词在最前面
        assert isinstance(state.messages[0], SystemMessage)
        assert "通用助手" in state.messages[0].content
        
        # 规则提示词在中间
        assert isinstance(state.messages[1], SystemMessage)
        assert "安全规则" in state.messages[1].content
        
        assert isinstance(state.messages[2], SystemMessage)
        assert "格式规则" in state.messages[2].content
        
        # 用户指令在最后
        assert isinstance(state.messages[3], HumanMessage)
        assert "分析" in state.messages[3].content
    
    def test_registry_operations(self, prompt_system):
        """测试注册表操作"""
        registry, loader, injector = prompt_system
        
        # 列出所有提示词
        system_prompts = registry.list_prompts("system")
        assert len(system_prompts) == 2
        assert any(p.name == "assistant" for p in system_prompts)
        assert any(p.name == "coder" for p in system_prompts)
        
        rules_prompts = registry.list_prompts("rules")
        assert len(rules_prompts) == 2
        
        user_commands = registry.list_prompts("user_commands")
        assert len(user_commands) == 1
        
        # 获取特定提示词元信息
        assistant_meta = registry.get_prompt_meta("system", "assistant")
        assert assistant_meta.name == "assistant"
        assert not assistant_meta.is_composite
        
        coder_meta = registry.get_prompt_meta("system", "coder")
        assert coder_meta.name == "coder"
        assert coder_meta.is_composite