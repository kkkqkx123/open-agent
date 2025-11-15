"""Provider-based配置系统测试"""

import unittest
import tempfile
import os
from pathlib import Path
import yaml

from src.infrastructure.config.config_system import ConfigSystem
from infrastructure.config.processor.merger import ConfigMerger
from infrastructure.config.processor.validator import ConfigValidator
from infrastructure.config.loader.file_config_loader import FileConfigLoader
from src.infrastructure.exceptions import ConfigurationError


class TestProviderConfigSystem(unittest.TestCase):
    """Provider-based配置系统测试类"""

    def setUp(self):
        """测试前设置"""
        # 创建临时目录和配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.configs_dir = Path(self.temp_dir) / "configs"
        self.configs_dir.mkdir()

        # 创建全局配置文件
        global_config = {
            "log_level": "INFO",
            "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
            "secret_patterns": ["sk-.*"],
            "env": "development",
            "debug": False,
            "env_prefix": "AGENT_",
            "hot_reload": True,
            "watch_interval": 5,
        }

        with open(self.configs_dir / "global.yaml", "w") as f:
            yaml.dump(global_config, f)

        # 创建LLM组配置文件
        llm_group_config = {
            "openai_group": {
                "base_url": "https://api.openai.com/v1",
                "headers": {"User-Agent": "ModularAgent/1.0"},
                "parameters": {"temperature": 0.7, "max_tokens": 200},
            }
        }

        llm_dir = self.configs_dir / "llms"
        llm_dir.mkdir()

        with open(llm_dir / "_group.yaml", "w") as f:
            yaml.dump(llm_group_config, f)

        # 创建provider目录结构
        openai_provider_dir = llm_dir / "provider" / "openai"
        openai_provider_dir.mkdir(parents=True)
        
        anthropic_provider_dir = llm_dir / "provider" / "anthropic"
        anthropic_provider_dir.mkdir(parents=True)
        
        gemini_provider_dir = llm_dir / "provider" / "gemini"
        gemini_provider_dir.mkdir(parents=True)

        # 创建provider common配置文件
        openai_common_config = {
            "model_type": "openai",
            "provider": "openai",
            "supports_caching": False,
            "default_parameters": {
                "temperature": 0.7,
                "max_tokens": 200,
                "timeout": 30
            },
            "cache_config": {
                "ttl_seconds": 1800,
                "max_size": 500
            },
            "fallback_config": {
                "enabled": True,
                "max_attempts": 3
            }
        }

        anthropic_common_config = {
            "model_type": "anthropic",
            "provider": "anthropic",
            "supports_caching": True,
            "default_parameters": {
                "temperature": 0.5,
                "max_tokens": 4000,
                "timeout": 60
            },
            "cache_config": {
                "ttl_seconds": 3600,
                "max_size": 1000
            },
            "fallback_config": {
                "enabled": True,
                "max_attempts": 5
            }
        }

        gemini_common_config = {
            "model_type": "gemini",
            "provider": "gemini",
            "supports_caching": True,
            "default_parameters": {
                "temperature": 0.6,
                "max_tokens": 3000,
                "timeout": 45
            },
            "cache_config": {
                "ttl_seconds": 7200,
                "max_size": 800
            },
            "fallback_config": {
                "enabled": True,
                "max_attempts": 4
            }
        }

        with open(openai_provider_dir / "common.yaml", "w") as f:
            yaml.dump(openai_common_config, f)

        with open(anthropic_provider_dir / "common.yaml", "w") as f:
            yaml.dump(anthropic_common_config, f)

        with open(gemini_provider_dir / "common.yaml", "w") as f:
            yaml.dump(gemini_common_config, f)

        # 创建具体的provider配置文件
        openai_gpt4_config = {
            "model_name": "gpt-4",
            "api_key": "${AGENT_OPENAI_KEY}",
            "parameters": {
                "temperature": 0.3,  # 覆盖common配置
            },
            "supports_caching": False,  # 覆盖common配置
            "cache_config": {
                "ttl_seconds": 3600  # 部分覆盖common配置
            }
        }

        anthropic_claude_config = {
            "model_name": "claude-3-sonnet-20240229",
            "api_key": "${AGENT_ANTHROPIC_KEY}",
            "parameters": {
                "temperature": 0.4,  # 覆盖common配置
            },
            "supports_caching": True,  # 保持common配置
            "fallback_models": ["claude-3-opus-20240229"]
        }

        gemini_pro_config = {
            "model_name": "gemini-1.5-pro",
            "api_key": "${AGENT_GEMINI_KEY}",
            "parameters": {
                "temperature": 0.5,  # 覆盖common配置
            },
            "supports_caching": True,  # 保持common配置
            "cache_config": {
                "max_size": 1200  # 部分覆盖common配置
            }
        }

        with open(openai_provider_dir / "openai-gpt4.yaml", "w") as f:
            yaml.dump(openai_gpt4_config, f)

        with open(anthropic_provider_dir / "claude-sonnet.yaml", "w") as f:
            yaml.dump(anthropic_claude_config, f)

        with open(gemini_provider_dir / "gemini-pro.yaml", "w") as f:
            yaml.dump(gemini_pro_config, f)

        # 创建Agent配置
        agents_dir = self.configs_dir / "agents"
        agents_dir.mkdir()

        # 创建Agent组配置文件
        agent_group_config = {
            "default_group": {
                "tool_sets": ["basic"],
                "system_prompt": "You are a helpful assistant.",
                "rules": ["be_helpful"],
                "user_command": "help",
            }
        }

        with open(agents_dir / "_group.yaml", "w") as f:
            yaml.dump(agent_group_config, f)

        # 创建Agent个体配置文件
        agent_config = {
            "group": "default_group",
            "name": "test_agent",
            "llm": "openai-gpt4",  # 引用provider配置
            "tools": ["search"],
            "max_iterations": 10,
            "timeout": 60,
            "retry_count": 3,
        }

        with open(agents_dir / "test_agent.yaml", "w") as f:
            yaml.dump(agent_config, f)

        # 初始化配置系统
        self.config_loader = FileConfigLoader(str(self.configs_dir))
        self.config_merger = ConfigMerger()
        self.config_validator = ConfigValidator()

        self.config_system = ConfigSystem(
            config_loader=self.config_loader,
            config_merger=self.config_merger,
            config_validator=self.config_validator,
            base_path=str(self.configs_dir),
        )

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_provider_config_openai(self):
        """测试加载OpenAI provider配置"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_openai_key"

        llm_config = self.config_system.load_llm_config("openai-gpt4")

        # 验证基础配置
        self.assertEqual(llm_config.model_type, "openai")
        self.assertEqual(llm_config.model_name, "gpt-4")
        self.assertEqual(llm_config.api_key, "test_openai_key")
        self.assertEqual(llm_config.provider, "openai")

        # 验证参数合并 - 个体配置覆盖common配置
        self.assertEqual(llm_config.get_parameter("temperature"), 0.3)  # 个体配置覆盖common配置
        self.assertEqual(llm_config.get_parameter("max_tokens"), 200)  # common配置（没有组配置）
        self.assertEqual(llm_config.get_parameter("timeout"), 30)  # common配置

        # 验证缓存配置 - 个体配置覆盖common配置
        self.assertFalse(llm_config.supports_caching)  # 个体配置覆盖
        self.assertEqual(llm_config.get_cache_config("ttl_seconds"), 3600)  # 个体配置
        self.assertEqual(llm_config.get_cache_config("max_size"), 500)  # common配置

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]

    def test_load_provider_config_anthropic(self):
        """测试加载Anthropic provider配置"""
        # 设置环境变量
        os.environ["AGENT_ANTHROPIC_KEY"] = "test_anthropic_key"

        llm_config = self.config_system.load_llm_config("claude-sonnet")

        # 验证基础配置
        self.assertEqual(llm_config.model_type, "anthropic")
        self.assertEqual(llm_config.model_name, "claude-3-sonnet-20240229")
        self.assertEqual(llm_config.api_key, "test_anthropic_key")
        self.assertEqual(llm_config.provider, "anthropic")

        # 验证参数合并
        self.assertEqual(llm_config.get_parameter("temperature"), 0.4)  # 个体配置
        self.assertEqual(llm_config.get_parameter("max_tokens"), 4000)  # common配置
        self.assertEqual(llm_config.get_parameter("timeout"), 60)  # common配置

        # 验证缓存配置
        self.assertTrue(llm_config.supports_caching)  # common配置
        self.assertEqual(llm_config.get_cache_config("ttl_seconds"), 3600)  # common配置
        self.assertEqual(llm_config.get_cache_config("max_size"), 1000)  # common配置

        # 验证降级配置
        self.assertTrue(llm_config.is_fallback_enabled())
        self.assertEqual(llm_config.get_fallback_models(), ["claude-3-opus-20240229"])
        self.assertEqual(llm_config.get_max_fallback_attempts(), 5)

        # 清理环境变量
        del os.environ["AGENT_ANTHROPIC_KEY"]

    def test_load_provider_config_gemini(self):
        """测试加载Gemini provider配置"""
        # 设置环境变量
        os.environ["AGENT_GEMINI_KEY"] = "test_gemini_key"

        llm_config = self.config_system.load_llm_config("gemini-pro")

        # 验证基础配置
        self.assertEqual(llm_config.model_type, "gemini")
        self.assertEqual(llm_config.model_name, "gemini-1.5-pro")
        self.assertEqual(llm_config.api_key, "test_gemini_key")
        self.assertEqual(llm_config.provider, "gemini")

        # 验证参数合并
        self.assertEqual(llm_config.get_parameter("temperature"), 0.5)  # 个体配置
        self.assertEqual(llm_config.get_parameter("max_tokens"), 3000)  # common配置
        self.assertEqual(llm_config.get_parameter("timeout"), 45)  # common配置

        # 验证缓存配置 - 部分覆盖
        self.assertTrue(llm_config.supports_caching)  # common配置
        self.assertEqual(llm_config.get_cache_config("ttl_seconds"), 7200)  # common配置
        self.assertEqual(llm_config.get_cache_config("max_size"), 1200)  # 个体配置覆盖

        # 清理环境变量
        del os.environ["AGENT_GEMINI_KEY"]

    def test_provider_config_with_group_inheritance(self):
        """测试provider配置与组配置继承"""
        # 创建一个同时有provider配置和组配置的LLM配置
        llm_config_with_group = {
            "group": "openai_group",  # 继承组配置
            "model_name": "gpt-4-turbo",
            "api_key": "${AGENT_OPENAI_KEY}",
            "parameters": {
                "temperature": 0.2,  # 覆盖provider common和组配置
            }
        }

        # 创建配置文件
        openai_provider_dir = self.configs_dir / "llms" / "provider" / "openai"
        with open(openai_provider_dir / "openai-gpt4-turbo.yaml", "w") as f:
            yaml.dump(llm_config_with_group, f)

        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        llm_config = self.config_system.load_llm_config("openai-gpt4-turbo")

        # 验证多层继承：组配置 -> provider common配置 -> 个体配置
        self.assertEqual(llm_config.model_type, "openai")  # provider common配置
        self.assertEqual(llm_config.model_name, "gpt-4-turbo")
        self.assertEqual(llm_config.api_key, "test_key")
        self.assertEqual(llm_config.provider, "openai")  # provider common配置

        # 验证参数：个体配置 + provider common配置 + 组配置
        self.assertEqual(llm_config.get_parameter("temperature"), 0.2)  # 个体配置
        self.assertEqual(llm_config.get_parameter("max_tokens"), 200)  # provider common配置（覆盖组配置）
        self.assertEqual(llm_config.get_parameter("timeout"), 30)  # provider common配置
        # 组配置中的参数也应该存在
        self.assertEqual(llm_config.base_url, "https://api.openai.com/v1")  # 组配置
        self.assertEqual(llm_config.headers["User-Agent"], "ModularAgent/1.0")  # 组配置

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]

    def test_provider_config_list_and_exists(self):
        """测试provider配置的列出和存在检查"""
        # 验证配置存在
        self.assertTrue(self.config_system.config_exists("llms", "openai-gpt4"))
        self.assertTrue(self.config_system.config_exists("llms", "claude-sonnet"))
        self.assertTrue(self.config_system.config_exists("llms", "gemini-pro"))
        self.assertFalse(self.config_system.config_exists("llms", "nonexistent"))

        # 验证配置列表包含provider配置
        llm_configs = self.config_system.list_configs("llms")
        self.assertIn("openai-gpt4", llm_configs)
        self.assertIn("claude-sonnet", llm_configs)
        self.assertIn("gemini-pro", llm_configs)

    def test_provider_config_cache_functionality(self):
        """测试provider配置的缓存功能"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        # 第一次加载
        llm_config1 = self.config_system.load_llm_config("openai-gpt4")

        # 第二次加载应该使用缓存
        llm_config2 = self.config_system.load_llm_config("openai-gpt4")

        # 验证是同一个实例（缓存生效）
        self.assertIs(llm_config1, llm_config2)

        # 验证配置内容正确
        self.assertEqual(llm_config1.model_name, "gpt-4")
        self.assertEqual(llm_config1.provider, "openai")
        self.assertFalse(llm_config1.supports_caching)

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]

    def test_provider_config_reload(self):
        """测试provider配置的重新加载"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        # 加载配置
        llm_config1 = self.config_system.load_llm_config("openai-gpt4")

        # 重新加载
        self.config_system.reload_configs()

        # 再次加载应该获取新实例
        llm_config2 = self.config_system.load_llm_config("openai-gpt4")

        # 验证不是同一个实例（缓存已清除）
        self.assertIsNot(llm_config1, llm_config2)

        # 验证内容相同
        self.assertEqual(llm_config1.model_name, llm_config2.model_name)
        self.assertEqual(llm_config1.provider, llm_config2.provider)
        self.assertEqual(llm_config1.supports_caching, llm_config2.supports_caching)

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]

    def test_load_agent_config_with_provider_llm(self):
        """测试加载引用provider配置的Agent配置"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        agent_config = self.config_system.load_agent_config("test_agent")

        # 验证Agent配置正确加载
        self.assertEqual(agent_config.name, "test_agent")
        self.assertEqual(agent_config.llm, "openai-gpt4")  # 引用provider配置
        self.assertEqual(agent_config.tools, ["search"])
        self.assertEqual(agent_config.max_iterations, 10)

        # 验证Agent配置继承了组配置
        self.assertEqual(agent_config.tool_sets, ["basic"])
        self.assertEqual(agent_config.system_prompt, "You are a helpful assistant.")
        self.assertEqual(agent_config.rules, ["be_helpful"])
        self.assertEqual(agent_config.user_command, "help")

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]

    def test_provider_config_different_caching_support(self):
        """测试不同provider的缓存支持差异"""
        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_openai_key"
        os.environ["AGENT_ANTHROPIC_KEY"] = "test_anthropic_key"
        os.environ["AGENT_GEMINI_KEY"] = "test_gemini_key"

        # 加载不同provider的配置
        openai_config = self.config_system.load_llm_config("openai-gpt4")
        anthropic_config = self.config_system.load_llm_config("claude-sonnet")
        gemini_config = self.config_system.load_llm_config("gemini-pro")

        # 验证缓存支持的差异
        # OpenAI配置：个体配置覆盖，不支持缓存
        self.assertFalse(openai_config.supports_caching)
        # Anthropic配置：使用common配置，支持缓存
        self.assertTrue(anthropic_config.supports_caching)
        # Gemini配置：使用common配置，支持缓存
        self.assertTrue(gemini_config.supports_caching)

        # 验证不同provider的缓存TL也不同
        self.assertEqual(openai_config.get_cache_ttl(), 3600)  # 个体配置
        self.assertEqual(anthropic_config.get_cache_ttl(), 3600)  # common配置
        self.assertEqual(gemini_config.get_cache_ttl(), 7200)  # common配置

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]
        del os.environ["AGENT_ANTHROPIC_KEY"]
        del os.environ["AGENT_GEMINI_KEY"]

    def test_provider_config_fallback_settings(self):
        """测试provider配置的降级设置"""
        # 设置环境变量
        os.environ["AGENT_ANTHROPIC_KEY"] = "test_key"

        anthropic_config = self.config_system.load_llm_config("claude-sonnet")

        # 验证降级设置
        self.assertTrue(anthropic_config.is_fallback_enabled())
        self.assertEqual(anthropic_config.get_fallback_models(), ["claude-3-opus-20240229"])
        self.assertEqual(anthropic_config.get_max_fallback_attempts(), 5)

        # 验证默认降级设置（OpenAI）
        os.environ["AGENT_OPENAI_KEY"] = "test_key"
        openai_config = self.config_system.load_llm_config("openai-gpt4")
        
        self.assertTrue(openai_config.is_fallback_enabled())  # 默认值
        self.assertEqual(openai_config.get_fallback_models(), [])  # 默认值
        self.assertEqual(openai_config.get_max_fallback_attempts(), 3)  # common配置

        # 清理环境变量
        del os.environ["AGENT_ANTHROPIC_KEY"]
        del os.environ["AGENT_OPENAI_KEY"]

    def test_provider_config_metadata_merge(self):
        """测试provider配置的元数据合并"""
        # 创建一个带有元数据的配置
        config_with_metadata = {
            "model_name": "gpt-4-meta",
            "api_key": "${AGENT_OPENAI_KEY}",
            "metadata": {
                "version": "v1",
                "region": "us-east-1",
                "custom_field": "value"
            }
        }

        openai_provider_dir = self.configs_dir / "llms" / "provider" / "openai"
        with open(openai_provider_dir / "openai-gpt4-meta.yaml", "w") as f:
            yaml.dump(config_with_metadata, f)

        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        llm_config = self.config_system.load_llm_config("openai-gpt4-meta")

        # 验证元数据合并
        self.assertEqual(llm_config.get_metadata("version"), "v1")
        self.assertEqual(llm_config.get_metadata("region"), "us-east-1")
        self.assertEqual(llm_config.get_metadata("custom_field"), "value")
        # common配置中的元数据也应该存在
        self.assertEqual(llm_config.get_metadata("version", "default"), "v1")

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]

    def test_provider_config_backward_compatibility(self):
        """测试provider配置与传统配置的向后兼容性"""
        # 创建传统的非provider配置
        traditional_config = {
            "model_type": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "${AGENT_OPENAI_KEY}",
            "parameters": {"temperature": 0.8},
            "supports_caching": False
        }

        llm_dir = self.configs_dir / "llms"
        with open(llm_dir / "gpt35.yaml", "w") as f:
            yaml.dump(traditional_config, f)

        # 设置环境变量
        os.environ["AGENT_OPENAI_KEY"] = "test_key"

        # 验证传统配置仍然可以正常加载
        traditional_llm_config = self.config_system.load_llm_config("gpt35")

        self.assertEqual(traditional_llm_config.model_type, "openai")
        self.assertEqual(traditional_llm_config.model_name, "gpt-3.5-turbo")
        self.assertEqual(traditional_llm_config.api_key, "test_key")
        self.assertFalse(traditional_llm_config.supports_caching)
        self.assertEqual(traditional_llm_config.get_parameter("temperature"), 0.8)

        # 验证provider配置和传统配置都可以加载
        provider_llm_config = self.config_system.load_llm_config("openai-gpt4")
        self.assertEqual(provider_llm_config.model_name, "gpt-4")
        self.assertEqual(provider_llm_config.provider, "openai")

        # 清理环境变量
        del os.environ["AGENT_OPENAI_KEY"]


if __name__ == '__main__':
    unittest.main()
