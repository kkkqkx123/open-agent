"""提示词注册表测试"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.infrastructure.config_loader import IConfigLoader
from src.domain.prompts.registry import PromptRegistry
from src.domain.prompts.models import PromptMeta


class TestPromptRegistry:
    """提示词注册表测试类"""
    
    @pytest.fixture
    def mock_config_loader(self):
        """模拟配置加载器"""
        config_loader = Mock(spec=IConfigLoader)
        config_loader.load.return_value = {
            "system": [
                {
                    "name": "assistant",
                    "path": "prompts/system/assistant.md",
                    "description": "通用助手系统提示词"
                },
                {
                    "name": "coder",
                    "path": "prompts/system/coder/",
                    "description": "代码生成专家系统提示词",
                    "is_composite": True
                }
            ],
            "rules": [
                {
                    "name": "safety",
                    "path": "prompts/rules/safety.md",
                    "description": "安全规则提示词"
                }
            ],
            "user_commands": [
                {
                    "name": "data_analysis",
                    "path": "prompts/user_commands/data_analysis.md",
                    "description": "数据分析用户指令"
                }
            ]
        }
        return config_loader
    
    @pytest.fixture
    def registry(self, mock_config_loader):
        """创建提示词注册表实例"""
        return PromptRegistry(mock_config_loader)
    
    def test_registry_loading(self, registry):
        """测试注册表加载"""
        # 验证系统提示词
        assistant_meta = registry.get_prompt_meta("system", "assistant")
        assert assistant_meta.name == "assistant"
        assert assistant_meta.category == "system"
        assert not assistant_meta.is_composite
        
        coder_meta = registry.get_prompt_meta("system", "coder")
        assert coder_meta.name == "coder"
        assert coder_meta.is_composite
        
        # 验证规则提示词
        safety_meta = registry.get_prompt_meta("rules", "safety")
        assert safety_meta.name == "safety"
        assert safety_meta.category == "rules"
        
        # 验证用户指令
        data_analysis_meta = registry.get_prompt_meta("user_commands", "data_analysis")
        assert data_analysis_meta.name == "data_analysis"
        assert data_analysis_meta.category == "user_commands"
    
    def test_list_prompts(self, registry):
        """测试列出提示词"""
        system_prompts = registry.list_prompts("system")
        assert len(system_prompts) == 2
        assert any(p.name == "assistant" for p in system_prompts)
        assert any(p.name == "coder" for p in system_prompts)
        
        rules_prompts = registry.list_prompts("rules")
        assert len(rules_prompts) == 1
        assert rules_prompts[0].name == "safety"
        
        user_commands = registry.list_prompts("user_commands")
        assert len(user_commands) == 1
        assert user_commands[0].name == "data_analysis"
    
    def test_register_prompt(self, registry):
        """测试注册提示词"""
        new_meta = PromptMeta(
            name="test_prompt",
            category="system",
            path=Path("test/path.md"),
            description="测试提示词"
        )
        
        registry.register_prompt("system", new_meta)
        
        # 验证注册成功
        retrieved_meta = registry.get_prompt_meta("system", "test_prompt")
        assert retrieved_meta.name == "test_prompt"
        assert retrieved_meta.description == "测试提示词"
    
    def test_duplicate_prompt(self, registry):
        """测试重复提示词检测"""
        new_meta = PromptMeta(
            name="assistant",  # 重名
            category="system",
            path=Path("test/path.md"),
            description="测试提示词"
        )
        
        with pytest.raises(ValueError, match="提示词名称重复"):
            registry.register_prompt("system", new_meta)
    
    def test_get_nonexistent_prompt(self, registry):
        """测试获取不存在的提示词"""
        with pytest.raises(ValueError, match="提示词不存在"):
            registry.get_prompt_meta("system", "nonexistent")
        
        with pytest.raises(ValueError, match="不支持的提示词类别"):
            registry.get_prompt_meta("invalid_category", "assistant")
    
    def test_validate_registry(self, registry):
        """测试验证注册表完整性"""
        with patch.object(Path, 'exists', return_value=True):
            assert registry.validate_registry() is True
        
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="提示词文件不存在"):
                registry.validate_registry()
    
    def test_config_load_error(self):
        """测试配置加载错误"""
        from src.infrastructure.exceptions import ConfigurationError
        
        config_loader = Mock(spec=IConfigLoader)
        config_loader.load.side_effect = ConfigurationError("配置加载失败")
        
        with pytest.raises(ConfigurationError, match="无法加载提示词注册表配置"):
            PromptRegistry(config_loader)
