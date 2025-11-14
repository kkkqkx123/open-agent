"""配置系统集成测试"""

import pytest
import tempfile
import os
import time
import threading
from pathlib import Path
from unittest.mock import Mock

from src.infrastructure.config.config_system import ConfigSystem
from infrastructure.config.core.merger import ConfigMerger
from infrastructure.config.utils.validator import ConfigValidator
from src.infrastructure.config.config_validator_tool import ConfigValidatorTool
from infrastructure.config.core.loader import YamlConfigLoader
from src.infrastructure.container import DependencyContainer
from src.infrastructure.exceptions import ConfigurationError


class TestConfigIntegration:
    """配置系统集成测试类"""

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
                {"type": "console", "level": "INFO", "format": "text"},
                {
                    "type": "file",
                    "level": "DEBUG",
                    "format": "json",
                    "path": "logs/agent.log",
                },
            ],
            "secret_patterns": ["sk-[a-zA-Z0-9]{20,}", "\\w+@\\w+\\.\\w+", "1\\d{10}"],
            "env": "development",
            "debug": True,
            "env_prefix": "AGENT_",
            "hot_reload": True,
            "watch_interval": 5,
        }

        with open(self.configs_dir / "global.yaml", "w") as f:
            import yaml

            yaml.dump(global_config, f)

        # 创建LLM组配置文件
        llm_group_config = {
            "openai_group": {
                "base_url": "https://api.openai.com/v1",
                "headers": {"User-Agent": "ModularAgent/1.0"},
                "parameters": {"temperature": 0.7, "max_tokens": 2000, "top_p": 1.0},
            },
            "gemini_group": {
                "base_url": "https://generativelanguage.googleapis.com/v1",
                "headers": {"User-Agent": "ModularAgent/1.0"},
                "parameters": {"temperature": 0.7, "max_tokens": 2048},
            },
        }

        llm_dir = self.configs_dir / "llms"
        llm_dir.mkdir()

        with open(llm_dir / "_group.yaml", "w") as f:
            import yaml

            yaml.dump(llm_group_config, f)

        # 创建LLM个体配置文件
        gpt4_config = {
            "group": "openai_group",
            "model_type": "openai",
            "model_name": "gpt-4",
            "api_key": "${AGENT_OPENAI_KEY}",
            "parameters": {"temperature": 0.3, "top_p": 0.9},
        }

        with open(llm_dir / "gpt4.yaml", "w") as f:
            import yaml

            yaml.dump(gpt4_config, f)

        gemini_config = {
            "group": "gemini_group",
            "model_type": "gemini",
            "model_name": "gemini-pro",
            "api_key": "${AGENT_GEMINI_KEY}",
            "parameters": {"temperature": 0.5},
        }

        with open(llm_dir / "gemini.yaml", "w") as f:
            import yaml

            yaml.dump(gemini_config, f)

        # 创建Agent组配置文件
        agent_group_config = {
            "default_group": {
                "tool_sets": ["basic"],
                "system_prompt": "You are a helpful assistant.",
                "rules": ["be_helpful", "be_accurate"],
                "user_command": "help",
            },
            "code_group": {
                "tool_sets": ["code_analysis", "file_operations"],
                "system_prompt": "You are a code analysis assistant.",
                "rules": ["analyze_code", "suggest_improvements"],
                "user_command": "analyze",
            },
        }

        agents_dir = self.configs_dir / "agents"
        agents_dir.mkdir()

        with open(agents_dir / "_group.yaml", "w") as f:
            import yaml

            yaml.dump(agent_group_config, f)

        # 创建Agent个体配置文件
        code_agent_config = {
            "group": "code_group",
            "name": "code_agent",
            "llm": "gpt4",
            "tools": ["search", "calculator"],
            "max_iterations": 15,
            "timeout": 120,
            "retry_count": 5,
        }

        with open(agents_dir / "code_agent.yaml", "w") as f:
            import yaml

            yaml.dump(code_agent_config, f)

        # 创建工具集组配置文件
        tool_group_config = {
            "basic_tools": {
                "tools": ["search", "calculator", "weather"],
                "timeout": 30,
                "max_retries": 3,
            },
            "code_analysis": {
                "tools": ["code_parser", "syntax_checker"],
                "timeout": 60,
                "max_retries": 2,
            },
        }

        tools_dir = self.configs_dir / "tool-sets"
        tools_dir.mkdir()

        with open(tools_dir / "_group.yaml", "w") as f:
            import yaml

            yaml.dump(tool_group_config, f)

        # 创建工具集个体配置文件
        advanced_tools_config = {
            "group": "basic_tools",
            "name": "advanced_tools",
            "tools": ["advanced_search", "data_analyzer"],
            "timeout": 45,
            "max_retries": 4,
            "enabled": True,
            "parallel": True,
        }

        with open(tools_dir / "advanced_tools.yaml", "w") as f:
            import yaml

            yaml.dump(advanced_tools_config, f)

        # 初始化配置系统
        self.config_loader = YamlConfigLoader(str(self.configs_dir))
        self.config_merger = ConfigMerger()
        self.config_validator = ConfigValidator()

        self.config_system = ConfigSystem(
            config_loader=self.config_loader,
            config_merger=self.config_merger,
            config_validator=self.config_validator,
            base_path=str(self.configs_dir),
        )

    def teardown_method(self):
        """测试后清理"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_complete_config_loading_workflow(self):
        """测试完整配置加载工作流"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_openai_key"
        os.environ["AGENT_GEMINI_KEY"] = "test_gemini_key"

        try:
            # 加载全局配置
            global_config = self.config_system.load_global_config()
            assert global_config.env == "development"
            assert global_config.debug is True
            assert len(global_config.log_outputs) == 2
            assert len(global_config.secret_patterns) == 3

            # 加载LLM配置
            gpt4_config = self.config_system.load_llm_config("gpt4")
            assert gpt4_config.model_type == "openai"
            assert gpt4_config.model_name == "gpt-4"
            assert gpt4_config.api_key == "test_openai_key"
            assert gpt4_config.base_url == "https://api.openai.com/v1"
            assert gpt4_config.parameters["temperature"] == 0.3
            assert gpt4_config.parameters["max_tokens"] == 2000
            assert gpt4_config.parameters["top_p"] == 0.9

            gemini_config = self.config_system.load_llm_config("gemini")
            assert gemini_config.model_type == "gemini"
            assert gemini_config.model_name == "gemini-pro"
            assert gemini_config.api_key == "test_gemini_key"
            assert (
                gemini_config.base_url == "https://generativelanguage.googleapis.com/v1"
            )
            assert gemini_config.parameters["temperature"] == 0.5
            assert gemini_config.parameters["max_tokens"] == 2048

            # 加载Agent配置
            code_agent_config = self.config_system.load_agent_config("code_agent")
            assert code_agent_config.name == "code_agent"
            assert code_agent_config.llm == "gpt4"
            assert code_agent_config.tool_sets == ["code_analysis", "file_operations"]
            assert code_agent_config.tools == ["search", "calculator"]
            assert (
                code_agent_config.system_prompt == "You are a code analysis assistant."
            )
            assert code_agent_config.rules == ["analyze_code", "suggest_improvements"]
            assert code_agent_config.user_command == "analyze"
            assert code_agent_config.max_iterations == 15
            assert code_agent_config.timeout == 120
            assert code_agent_config.retry_count == 5

            # 加载工具配置
            advanced_tools_config = self.config_system.load_tool_config(
                "advanced_tools"
            )
            assert advanced_tools_config.name == "advanced_tools"
            assert advanced_tools_config.tools == ["advanced_search", "data_analyzer"]
            assert advanced_tools_config.timeout == 45
            assert advanced_tools_config.max_retries == 4
            assert advanced_tools_config.enabled is True
            assert advanced_tools_config.parallel is True

        finally:
            # 清理环境变量
            if "AGENT_OPENAI_KEY" in os.environ:
                del os.environ["AGENT_OPENAI_KEY"]
            if "AGENT_GEMINI_KEY" in os.environ:
                del os.environ["AGENT_GEMINI_KEY"]

    def test_config_inheritance_complex_scenario(self):
        """测试复杂配置继承场景"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        try:
            # 加载GPT-4配置（继承自openai_group）
            gpt4_config = self.config_system.load_llm_config("gpt4")

            # 验证继承关系
            assert gpt4_config.group == "openai_group"
            assert gpt4_config.base_url == "https://api.openai.com/v1"  # 继承自组
            assert gpt4_config.headers["User-Agent"] == "ModularAgent/1.0"  # 继承自组
            assert gpt4_config.parameters["temperature"] == 0.3  # 个体覆盖
            assert gpt4_config.parameters["max_tokens"] == 2000  # 继承自组
            assert gpt4_config.parameters["top_p"] == 0.9  # 个体新增
            assert gpt4_config.parameters["top_p"] != 1.0  # 不是组的值

        finally:
            # 清理环境变量
            if "AGENT_OPENAI_KEY" in os.environ:
                del os.environ["AGENT_OPENAI_KEY"]

    def test_config_hot_reload(self):
        """测试配置热重载"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        try:
            # 加载初始配置
            gpt4_config1 = self.config_system.load_llm_config("gpt4")
            assert gpt4_config1.parameters["temperature"] == 0.3

            # 修改配置文件
            gpt4_config_path = self.configs_dir / "llms" / "gpt4.yaml"

            # 读取原配置
            with open(gpt4_config_path, "r") as f:
                import yaml

                config_data = yaml.safe_load(f)

            # 修改配置
            config_data["parameters"]["temperature"] = 0.8

            # 写回文件
            with open(gpt4_config_path, "w") as f:
                yaml.dump(config_data, f)

            # 等待文件系统处理
            time.sleep(0.1)

            # 重新加载配置
            self.config_system.reload_configs()
            gpt4_config2 = self.config_system.load_llm_config("gpt4")

            # 验证配置已更新
            assert gpt4_config2.parameters["temperature"] == 0.8

        finally:
            # 清理环境变量
            if "AGENT_OPENAI_KEY" in os.environ:
                del os.environ["AGENT_OPENAI_KEY"]

    def test_config_validation_tool_integration(self):
        """测试配置验证工具集成"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"
        os.environ["AGENT_GEMINI_KEY"] = "test_gemini_key"

        try:
            # 创建验证工具
            validator_tool = ConfigValidatorTool(str(self.configs_dir))

            # 验证所有配置
            result = validator_tool.validate_all()
            assert result  # 所有配置应该验证通过

            # 验证特定配置
            result = validator_tool.validate_config("global", "")
            assert result

            result = validator_tool.validate_config("llm", "gpt4")
            assert result

            result = validator_tool.validate_config("agent", "code_agent")
            assert result

            result = validator_tool.validate_config("tool", "advanced_tools")
            assert result

            # 列出配置
            validator_tool.list_configs()
            validator_tool.list_configs("llms")
            validator_tool.list_configs("agents")
            validator_tool.list_configs("tool-sets")

        finally:
            # 清理环境变量
            if "AGENT_OPENAI_KEY" in os.environ:
                del os.environ["AGENT_OPENAI_KEY"]

    def test_dependency_container_integration(self):
        """测试依赖注入容器集成"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"
        os.environ["AGENT_GEMINI_KEY"] = "test_gemini_key"

        try:
            # 创建依赖注入容器
            container = DependencyContainer()

            # 注册服务时使用正确的构造函数参数
            container.register_factory(
                YamlConfigLoader,
                lambda: YamlConfigLoader(str(self.configs_dir)),
                "default",
            )
            container.register(ConfigMerger, ConfigMerger, "default")
            container.register(ConfigValidator, ConfigValidator, "default")
            container.register(ConfigSystem, ConfigSystem, "default")

            # 获取服务
            config_loader = container.get(YamlConfigLoader)
            config_merger = container.get(ConfigMerger)
            config_validator = container.get(ConfigValidator)

            # 创建配置系统
            config_system = ConfigSystem(
                config_loader=config_loader,
                config_merger=config_merger,
                config_validator=config_validator,
                base_path=str(self.configs_dir),
            )

            # 测试配置加载
            global_config = config_system.load_global_config()
            assert global_config.env == "development"

            gpt4_config = config_system.load_llm_config("gpt4")
            assert gpt4_config.model_name == "gpt-4"

            code_agent_config = config_system.load_agent_config("code_agent")
            assert code_agent_config.name == "code_agent"

        finally:
            # 清理环境变量
            if "AGENT_OPENAI_KEY" in os.environ:
                del os.environ["AGENT_OPENAI_KEY"]

    def test_config_error_handling(self):
        """测试配置错误处理"""
        # 测试加载不存在的配置
        with pytest.raises(ConfigurationError):
            self.config_system.load_llm_config("nonexistent")

        # 创建无效配置文件
        invalid_config_path = self.configs_dir / "llms" / "invalid.yaml"
        with open(invalid_config_path, "w") as f:
            f.write("invalid: yaml: content:")

        # 测试加载无效配置
        with pytest.raises(ConfigurationError):
            self.config_system.load_llm_config("invalid")

        # 创建验证失败的配置文件
        invalid_config = {
            "model_type": "invalid_type",  # 无效类型
            "model_name": "gpt-4",
        }

        with open(self.configs_dir / "llms" / "validation_error.yaml", "w") as f:
            import yaml

            yaml.dump(invalid_config, f)

        # 测试验证失败
        with pytest.raises(ConfigurationError) as exc_info:
            self.config_system.load_llm_config("validation_error")

        assert "验证失败" in str(exc_info.value)

    def test_config_file_watching(self):
        """测试配置文件监听"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        try:
            # 创建回调函数
            callback_called = threading.Event()
            callback_path = None
            callback_config = None

            def test_callback(path, config):
                nonlocal callback_path, callback_config
                callback_path = path
                callback_config = config
                callback_called.set()

            # 添加监听
            self.config_system.watch_for_changes(test_callback)

            # 修改配置文件
            global_config_path = self.configs_dir / "global.yaml"

            # 读取原配置
            with open(global_config_path, "r") as f:
                import yaml

                config_data = yaml.safe_load(f)

            # 修改配置
            config_data["debug"] = not config_data["debug"]

            # 写回文件
            with open(global_config_path, "w") as f:
                yaml.dump(config_data, f)

            # 等待回调被调用
            assert callback_called.wait(timeout=2.0), "回调未被调用"

            # 验证回调参数
            assert callback_path == "global.yaml"
            assert callback_config is not None
            # 由于配置已经重新加载，缓存应该已经更新，所以值应该相同
            current_config = self.config_system.load_global_config()
            assert callback_config["debug"] == current_config.debug

        finally:
            # 停止监听
            self.config_system.stop_watching()

            # 清理环境变量
            if "AGENT_OPENAI_KEY" in os.environ:
                del os.environ["AGENT_OPENAI_KEY"]
