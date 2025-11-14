"""配置加载器单元测试"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

from infrastructure.config.core.loader import YamlConfigLoader, ConfigFileHandler
from src.infrastructure.exceptions import ConfigurationError


class TestYamlConfigLoader:
    """YAML配置加载器测试"""

    def test_load_valid_yaml(self, test_config: Any) -> None:
        """测试加载有效YAML配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.yaml"

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            loader = YamlConfigLoader(temp_dir)
            config = loader.load("test.yaml")

            assert config["log_level"] == "INFO"
            assert len(config["log_outputs"]) == 1
            assert config["env"] == "test"

    def test_load_nonexistent_file(self) -> None:
        """测试加载不存在的文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = YamlConfigLoader(temp_dir)

            with pytest.raises(
                ConfigurationError, match="Configuration file not found"
            ):
                loader.load("nonexistent.yaml")

    def test_load_invalid_yaml(self) -> None:
        """测试加载无效YAML"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid.yaml"

            with open(config_path, "w", encoding="utf-8") as f:
                f.write("invalid: yaml: content: [")

            loader = YamlConfigLoader(temp_dir)

            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                loader.load("invalid.yaml")

    def test_resolve_env_vars(self) -> None:
        """测试环境变量解析"""
        os.environ["TEST_API_KEY"] = "secret_key"
        os.environ["TEST_PORT"] = "8000"

        try:
            loader = YamlConfigLoader()

            # 测试简单环境变量
            config = {"api_key": "${TEST_API_KEY}"}
            resolved = loader.resolve_env_vars(config)
            assert resolved["api_key"] == "secret_key"

            # 测试带默认值的环境变量
            config = {"port": "${TEST_PORT:9000}"}
            resolved = loader.resolve_env_vars(config)
            assert resolved["port"] == "8000"

            # 测试不存在的环境变量（使用默认值）
            config = {"timeout": "${NONEXISTENT_VAR:30}"}
            resolved = loader.resolve_env_vars(config)
            assert resolved["timeout"] == "30"

            # 测试不存在的环境变量（无默认值）
            config = {"missing": "${NONEXISTENT_VAR}"}
            with pytest.raises(
                ConfigurationError, match="Environment variable not found"
            ):
                loader.resolve_env_vars(config)

        finally:
            # 清理环境变量
            if "TEST_API_KEY" in os.environ:
                del os.environ["TEST_API_KEY"]
            if "TEST_PORT" in os.environ:
                del os.environ["TEST_PORT"]

    def test_resolve_nested_env_vars(self) -> None:
        """测试嵌套环境变量解析"""
        os.environ["TEST_HOST"] = "localhost"
        os.environ["TEST_PORT"] = "8000"

        try:
            loader = YamlConfigLoader()

            config = {
                "server": {
                    "host": "${TEST_HOST}",
                    "port": "${TEST_PORT}",
                    "endpoints": [
                        "http://${TEST_HOST}:${TEST_PORT}/api",
                        {
                            "path": "/health",
                            "url": "http://${TEST_HOST}:${TEST_PORT}/health",
                        },
                    ],
                }
            }

            resolved = loader.resolve_env_vars(config)

            assert resolved["server"]["host"] == "localhost"
            assert resolved["server"]["port"] == "8000"
            assert resolved["server"]["endpoints"][0] == "http://localhost:8000/api"
            assert (
                resolved["server"]["endpoints"][1]["url"]
                == "http://localhost:8000/health"
            )

        finally:
            # 清理环境变量
            if "TEST_HOST" in os.environ:
                del os.environ["TEST_HOST"]
            if "TEST_PORT" in os.environ:
                del os.environ["TEST_PORT"]

    def test_config_caching(self, test_config: Any) -> None:
        """测试配置缓存"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.yaml"

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            loader = YamlConfigLoader(temp_dir)

            # 第一次加载
            config1 = loader.load("test.yaml")

            # 第二次加载应该使用缓存
            config2 = loader.load("test.yaml")

            assert config1 is config2

    def test_reload(self, test_config: Any) -> None:
        """测试重新加载配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.yaml"

            # 创建初始配置
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            loader = YamlConfigLoader(temp_dir)
            config1 = loader.load("test.yaml")

            # 修改配置文件
            updated_config = test_config.copy()
            updated_config["log_level"] = "DEBUG"

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(updated_config, f)

            # 重新加载
            loader.reload()
            config2 = loader.load("test.yaml")

            assert config1["log_level"] == "INFO"
            assert config2["log_level"] == "DEBUG"

    def test_watch_for_changes(self, test_config: Any) -> None:
        """测试配置文件变化监听"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.yaml"

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            loader = YamlConfigLoader(temp_dir)

            # 模拟回调函数
            callback = MagicMock()
            loader.watch_for_changes(callback)

            # 模拟文件变化
            updated_config = test_config.copy()
            updated_config["log_level"] = "DEBUG"

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(updated_config, f)

            # 手动触发文件变化处理
            # 直接调用处理器的手动触发方法
            for observer in loader._observers:
                for watch, handlers in observer._handlers.items():
                    for handler in handlers:
                        if isinstance(handler, ConfigFileHandler):
                            handler.trigger_manual(str(config_path))
                            break

            # 验证回调被调用
            callback.assert_called()
            args, kwargs = callback.call_args
            assert args[0] == "test.yaml"
            assert args[1]["log_level"] == "DEBUG"

    def test_get_cached_config(self, test_config: Any) -> None:
        """测试获取缓存配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.yaml"

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            loader = YamlConfigLoader(temp_dir)

            # 加载配置
            loader.load("test.yaml")

            # 获取缓存配置
            cached_config = loader.get_cached_config("test.yaml")

            assert cached_config is not None
            assert cached_config["log_level"] == "INFO"

            # 获取不存在的缓存配置
            nonexistent = loader.get_cached_config("nonexistent.yaml")
            assert nonexistent is None

    def test_clear_cache(self, test_config: Any) -> None:
        """测试清除缓存"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test.yaml"

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(test_config, f)

            loader = YamlConfigLoader(temp_dir)

            # 加载配置
            loader.load("test.yaml")

            # 验证缓存存在
            assert loader.get_cached_config("test.yaml") is not None

            # 清除缓存
            loader.clear_cache()

            # 验证缓存已清除
            assert loader.get_cached_config("test.yaml") is None

    def test_validate_config_structure(self) -> None:
        """测试配置结构验证"""
        loader = YamlConfigLoader()

        # 有效配置
        valid_config = {
            "log_level": "INFO",
            "log_outputs": [{"type": "console"}],
            "env": "test",
        }

        result = loader.validate_config_structure(
            valid_config, ["log_level", "log_outputs"]
        )
        assert result.is_pass()

        # 无效配置（缺少必需字段）
        invalid_config = {"log_outputs": [{"type": "console"}]}

        result = loader.validate_config_structure(
            invalid_config, ["log_level", "log_outputs"]
        )
        assert result.is_error()
        assert "log_level" in result.details["missing_keys"]

    def test_stop_watching(self) -> None:
        """测试停止监听"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = YamlConfigLoader(temp_dir)

            # 开始监听
            callback = MagicMock()
            loader.watch_for_changes(callback)

            # 验证观察者已创建
            assert len(loader._observers) > 0

            # 停止监听
            loader.stop_watching()

            # 验证观察者已清除
            assert len(loader._observers) == 0
            assert len(loader._callbacks) == 0
