"""配置系统核心测试"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

from src.config.config_system import ConfigSystem
from src.config.config_merger import ConfigMerger
from src.config.config_validator import ConfigValidator
from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.exceptions import ConfigurationError


class TestConfigSystem:
    """配置系统核心测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建临时目录和配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.configs_dir = Path(self.temp_dir) / "configs"
        self.configs_dir.mkdir()
        
        # 创建全局配置文件
        global_config = {
            "log_level": "INFO",
            "log_outputs": [
                {"type": "console", "level": "INFO", "format": "text"}
            ],
            "secret_patterns": ["sk-.*"],
            "env": "development",
            "debug": False,
            "env_prefix": "AGENT_",
            "hot_reload": True,
            "watch_interval": 5
        }
        
        with open(self.configs_dir / "global.yaml", 'w') as f:
            import yaml
            yaml.dump(global_config, f)
        
        # 创建LLM组配置文件
        llm_group_config = {
            "openai_group": {
                "base_url": "https://api.openai.com/v1",
                "headers": {
                    "User-Agent": "ModularAgent/1.0"
                },
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }
        
        llm_dir = self.configs_dir / "llms"
        llm_dir.mkdir()
        
        with open(llm_dir / "_group.yaml", 'w') as f:
            import yaml
            yaml.dump(llm_group_config, f)
        
        # 创建LLM个体配置文件
        llm_config = {
            "group": "openai_group",
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "${AGENT_OPENAI_KEY}",
            "parameters": {
                "temperature": 0.3,
                "top_p": 0.9
            }
        }
        
        with open(llm_dir / "gpt4.yaml", 'w') as f:
            import yaml
            yaml.dump(llm_config, f)
        
        # 创建Agent组配置文件
        agent_group_config = {
            "default_group": {
                "tool_sets": ["basic"],
                "system_prompt": "You are a helpful assistant.",
                "rules": ["be_helpful"],
                "user_command": "help"
            }
        }
        
        agents_dir = self.configs_dir / "agents"
        agents_dir.mkdir()
        
        with open(agents_dir / "_group.yaml", 'w') as f:
            import yaml
            yaml.dump(agent_group_config, f)
        
        # 创建Agent个体配置文件
        agent_config = {
            "group": "default_group",
            "name": "test_agent",
            "llm": "gpt4",
            "tools": ["search"],
            "max_iterations": 10,
            "timeout": 60,
            "retry_count": 3
        }
        
        with open(agents_dir / "test_agent.yaml", 'w') as f:
            import yaml
            yaml.dump(agent_config, f)
        
        # 初始化配置系统
        self.config_loader = YamlConfigLoader(str(self.configs_dir))
        self.config_merger = ConfigMerger()
        self.config_validator = ConfigValidator()
        
        self.config_system = ConfigSystem(
            config_loader=self.config_loader,
            config_merger=self.config_merger,
            config_validator=self.config_validator,
            base_path=str(self.configs_dir)
        )
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_global_config(self):
        """测试加载全局配置"""
        global_config = self.config_system.load_global_config()
        
        assert global_config.log_level == "INFO"
        assert global_config.env == "development"
        assert global_config.debug is False
        assert global_config.env_prefix == "AGENT_"
        assert global_config.hot_reload is True
        assert global_config.watch_interval == 5
        assert len(global_config.log_outputs) == 1
        assert len(global_config.secret_patterns) == 1
    
    def test_load_global_config_cached(self):
        """测试全局配置缓存"""
        # 第一次加载
        global_config1 = self.config_system.load_global_config()
        
        # 第二次加载应该使用缓存
        global_config2 = self.config_system.load_global_config()
        
        assert global_config1 is global_config2
    
    def test_load_llm_config(self):
        """测试加载LLM配置"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"
        
        llm_config = self.config_system.load_llm_config("gpt4")
        
        assert llm_config.group == "openai_group"
        assert llm_config.model_type == "openai"
        assert llm_config.model_name == "gpt-4"
        assert llm_config.api_key == "test_key"
        assert llm_config.base_url == "https://api.openai.com/v1"  # 继承自组配置
        assert llm_config.headers["User-Agent"] == "ModularAgent/1.0"  # 继承自组配置
        assert llm_config.parameters["temperature"] == 0.3  # 个体配置覆盖
        assert llm_config.parameters["max_tokens"] == 2000  # 继承自组配置
        assert llm_config.parameters["top_p"] == 0.9  # 个体配置新增
        
        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]
    
    def test_load_llm_config_cached(self):
        """测试LLM配置缓存"""
        os.environ["AGENT_OPENAI_KEY"] = "test_key"
        
        # 第一次加载
        llm_config1 = self.config_system.load_llm_config("gpt4")
        
        # 第二次加载应该使用缓存
        llm_config2 = self.config_system.load_llm_config("gpt4")
        
        assert llm_config1 is llm_config2
        
        del os.environ["AGENT_OPENAI_KEY"]
    
    def test_load_agent_config(self):
        """测试加载Agent配置"""
        agent_config = self.config_system.load_agent_config("test_agent")
        
        assert agent_config.group == "default_group"
        assert agent_config.name == "test_agent"
        assert agent_config.llm == "gpt4"
        assert agent_config.tool_sets == ["basic"]  # 继承自组配置
        assert agent_config.tools == ["search"]  # 个体配置
        assert agent_config.system_prompt == "You are a helpful assistant."  # 继承自组配置
        assert agent_config.rules == ["be_helpful"]  # 继承自组配置
        assert agent_config.user_command == "help"  # 继承自组配置
        assert agent_config.max_iterations == 10
        assert agent_config.timeout == 60
        assert agent_config.retry_count == 3
    
    def test_load_agent_config_cached(self):
        """测试Agent配置缓存"""
        # 第一次加载
        agent_config1 = self.config_system.load_agent_config("test_agent")
        
        # 第二次加载应该使用缓存
        agent_config2 = self.config_system.load_agent_config("test_agent")
        
        assert agent_config1 is agent_config2
    
    def test_reload_configs(self):
        """测试重新加载配置"""
        # 加载配置
        global_config1 = self.config_system.load_global_config()
        llm_config1 = self.config_system.load_llm_config("gpt4")
        agent_config1 = self.config_system.load_agent_config("test_agent")
        
        # 重新加载
        self.config_system.reload_configs()
        
        # 再次加载应该获取新的实例
        global_config2 = self.config_system.load_global_config()
        llm_config2 = self.config_system.load_llm_config("gpt4")
        agent_config2 = self.config_system.load_agent_config("test_agent")
        
        # 验证不是同一个实例（缓存已清除）
        assert global_config1 is not global_config2
        assert llm_config1 is not llm_config2
        assert agent_config1 is not agent_config2
        
        # 验证内容相同
        assert global_config1.log_level == global_config2.log_level
        assert llm_config1.model_name == llm_config2.model_name
        assert agent_config1.name == agent_config2.name
    
    def test_get_config_path(self):
        """测试获取配置路径"""
        path = self.config_system.get_config_path("llms", "gpt4")
        assert path == "llms/gpt4.yaml"
    
    def test_list_configs(self):
        """测试列出配置"""
        llm_configs = self.config_system.list_configs("llms")
        assert "gpt4" in llm_configs
        
        agent_configs = self.config_system.list_configs("agents")
        assert "test_agent" in agent_configs
        
        tool_configs = self.config_system.list_configs("tool-sets")
        assert tool_configs == []  # 没有工具配置
    
    def test_config_exists(self):
        """测试检查配置是否存在"""
        assert self.config_system.config_exists("llms", "gpt4")
        assert self.config_system.config_exists("agents", "test_agent")
        assert not self.config_system.config_exists("llms", "nonexistent")
        assert not self.config_system.config_exists("nonexistent_type", "config")
    
    def test_watch_for_changes(self):
        """测试监听配置变化"""
        callback_called = False
        callback_path = None
        callback_config = None
        
        def test_callback(path, config):
            nonlocal callback_called, callback_path, callback_config
            callback_called = True
            callback_path = path
            callback_config = config
        
        # 添加监听
        self.config_system.watch_for_changes(test_callback)
        
        # 模拟文件变化
        self.config_system._handle_file_change(str(self.configs_dir / "global.yaml"))
        
        # 验证回调被调用
        assert callback_called
        assert callback_path == "global.yaml"
        assert callback_config is not None
    
    def test_stop_watching(self):
        """测试停止监听配置变化"""
        callback_called = False
        
        def test_callback(path, config):
            nonlocal callback_called
            callback_called = True
        
        # 添加监听
        self.config_system.watch_for_changes(test_callback)
        
        # 停止监听
        self.config_system.stop_watching()
        
        # 模拟文件变化
        self.config_system._handle_file_change(str(self.configs_dir / "global.yaml"))
        
        # 验证回调未被调用（因为已停止监听）
        assert not callback_called
    
    def test_load_config_with_inheritance(self):
        """测试加载配置并处理继承"""
        config_data = self.config_system._load_config_with_inheritance("llms", "gpt4")
        
        # 验证继承结果
        assert config_data["group"] == "openai_group"
        assert config_data["model_type"] == "openai"
        assert config_data["model_name"] == "gpt-4"
        assert config_data["base_url"] == "https://api.openai.com/v1"  # 继承自组配置
        assert config_data["headers"]["User-Agent"] == "ModularAgent/1.0"  # 继承自组配置
        assert config_data["parameters"]["temperature"] == 0.3  # 个体配置覆盖
        assert config_data["parameters"]["max_tokens"] == 2000  # 继承自组配置
        assert config_data["parameters"]["top_p"] == 0.9  # 个体配置新增
    
    def test_load_config_with_inheritance_no_group(self):
        """测试加载配置（无组继承）"""
        # 创建无组继承的配置文件
        llm_config = {
            "model_type": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test_key"
        }
        
        with open(self.configs_dir / "llms" / "gpt35.yaml", 'w') as f:
            import yaml
            yaml.dump(llm_config, f)
        
        config_data = self.config_system._load_config_with_inheritance("llms", "gpt35")
        
        # 验证结果
        assert config_data["model_type"] == "openai"
        assert config_data["model_name"] == "gpt-3.5-turbo"
        assert config_data["api_key"] == "test_key"
        assert "group" not in config_data
    
    def test_load_config_with_inheritance_group_not_found(self):
        """测试加载配置（组不存在）"""
        # 创建引用不存在组的配置文件
        llm_config = {
            "group": "nonexistent_group",
            "model_type": "openai",
            "model_name": "gpt-3.5-turbo"
        }
        
        with open(self.configs_dir / "llms" / "invalid.yaml", 'w') as f:
            import yaml
            yaml.dump(llm_config, f)
        
        config_data = self.config_system._load_config_with_inheritance("llms", "invalid")
        
        # 验证结果（应该返回原配置）
        assert config_data["group"] == "nonexistent_group"
        assert config_data["model_type"] == "openai"
        assert config_data["model_name"] == "gpt-3.5-turbo"
    
    def test_get_env_resolver(self):
        """测试获取环境变量解析器"""
        env_resolver = self.config_system.get_env_resolver()
        
        assert env_resolver is not None
        assert env_resolver.prefix == "AGENT_"  # 来自全局配置
    
    def test_load_config_validation_error(self):
        """测试加载配置验证错误"""
        # 创建无效的LLM配置文件
        llm_config = {
            "model_type": "invalid_type",  # 无效类型
            "model_name": "gpt-4"
        }
        
        with open(self.configs_dir / "llms" / "invalid.yaml", 'w') as f:
            import yaml
            yaml.dump(llm_config, f)
        
        # 验证抛出配置错误
        with pytest.raises(ConfigurationError) as exc_info:
            self.config_system.load_llm_config("invalid")
        
        assert "验证失败" in str(exc_info.value)
    
    def test_load_config_file_not_found(self):
        """测试加载不存在的配置文件"""
        # 验证抛出配置错误
        with pytest.raises(ConfigurationError) as exc_info:
            self.config_system.load_llm_config("nonexistent")
        
        assert "not found" in str(exc_info.value)