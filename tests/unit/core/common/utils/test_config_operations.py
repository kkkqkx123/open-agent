"""ConfigOperations单元测试"""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.core.common.utils.config_operations import ConfigOperations
from src.core.config.config_manager import ConfigManager
from src.core.common.exceptions.config import ConfigError as ConfigurationError


class TestConfigOperations:
    """ConfigOperations测试类"""

    def setup_method(self):
        """测试前准备"""
        # 创建模拟的ConfigManager
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.config_operations = ConfigOperations(self.mock_config_manager)

    def test_init(self):
        """测试初始化"""
        assert self.config_operations._config_manager == self.mock_config_manager

    def test_export_config_snapshot(self):
        """测试导出配置快照"""
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_file:
            output_path = temp_file.name

        try:
            # 模拟配置数据
            global_config = {"env": "test", "debug": True}
            llm_config = {"model": "gpt-3.5", "api_key": "test_key"}
            tool_config = {"name": "calculator", "enabled": True}

            # 配置mock返回值
            self.mock_config_manager.load_config.side_effect = [
                global_config,  # global config
                llm_config,     # llm config
                tool_config     # tool config
            ]
            self.mock_config_manager.list_config_files.side_effect = [
                ["llm_config.yaml"],  # llm config files
                ["tool_config.yaml"]  # tool config files
            ]

            # 执行导出
            self.config_operations.export_config_snapshot(output_path)

            # 验证文件内容
            with open(output_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)

            assert "timestamp" in exported_data
            assert "configs" in exported_data
            assert "global" in exported_data["configs"]
            assert exported_data["configs"]["global"] == global_config
            assert "llms" in exported_data["configs"]
            assert "tools" in exported_data["configs"]

        finally:
            # 清理临时文件
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_export_config_snapshot_error(self):
        """测试导出配置快照时发生错误"""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(ConfigurationError, match="导出配置快照失败"):
                self.config_operations.export_config_snapshot("/invalid/path")

    def test_get_config_summary(self):
        """测试获取配置摘要"""
        # 模拟配置数据
        global_config = {"env": "dev", "debug": False}
        self.mock_config_manager.load_config.return_value = global_config
        self.mock_config_manager.list_config_files.side_effect = [
            ["config1.yaml", "config2.yaml"],  # llm configs
            ["tool1.yaml", "tool2.yaml", "tool3.yaml"]  # tool configs
        ]

        summary = self.config_operations.get_config_summary()

        assert "timestamp" in summary
        assert "config_counts" in summary
        assert summary["config_counts"]["llms"] == 2
        assert summary["config_counts"]["tools"] == 3
        assert summary["environment"] == "dev"
        assert summary["debug"] == False

    def test_validate_all_configs(self):
        """测试验证所有配置"""
        # 模拟配置加载成功的情况
        self.mock_config_manager.load_config.side_effect = [
            {"global": "config"},  # global config - success
            {"llm": "config"},     # llm config - success
            {"tool": "config"}     # tool config - success
        ]
        self.mock_config_manager.list_config_files.side_effect = [
            ["llm_config.yaml"],  # llm config files
            ["tool_config.yaml"]  # tool config files
        ]

        results = self.config_operations.validate_all_configs()

        assert "timestamp" in results
        assert "validations" in results
        assert results["validations"]["global"]["status"] == "valid"
        assert results["validations"]["llms"]["llm_config"]["status"] == "valid"
        assert results["validations"]["tools"]["tool_config"]["status"] == "valid"

    def test_validate_all_configs_with_error(self):
        """测试验证配置时包含错误"""
        # 模拟部分配置加载失败
        self.mock_config_manager.load_config.side_effect = [
            {"global": "config"},  # global config - success
            ConfigurationError("Invalid LLM config"),  # llm config - error
            {"tool": "config"}     # tool config - success
        ]
        self.mock_config_manager.list_config_files.side_effect = [
            ["llm_config.yaml"],  # llm config files
            ["tool_config.yaml"]  # tool config files
        ]

        results = self.config_operations.validate_all_configs()

        assert results["validations"]["global"]["status"] == "valid"
        assert results["validations"]["llms"]["llm_config"]["status"] == "invalid"
        assert "error" in results["validations"]["llms"]["llm_config"]

    def test_get_config_dependencies(self):
        """测试获取配置依赖关系"""
        # 模拟配置数据
        llm_config_with_deps = {"group": "openai", "token_counter": "gpt-4"}
        tool_config_with_deps = {"group": "builtin"}

        self.mock_config_manager.load_config.side_effect = [
            llm_config_with_deps,  # llm config
            tool_config_with_deps  # tool config
        ]
        self.mock_config_manager.list_config_files.side_effect = [
            ["llm_config.yaml"],  # llm config files
            ["tool_config.yaml"]  # tool config files
        ]

        dependencies = self.config_operations.get_config_dependencies()

        assert "timestamp" in dependencies
        assert "dependencies" in dependencies
        assert "llms" in dependencies["dependencies"]
        assert "tools" in dependencies["dependencies"]
        assert "group:openai" in dependencies["dependencies"]["llms"]["llm_config"]
        assert "token_counter:gpt-4" in dependencies["dependencies"]["llms"]["llm_config"]
        assert "group:builtin" in dependencies["dependencies"]["tools"]["tool_config"]

    def test_backup_all_configs(self):
        """测试备份所有配置"""
        with patch.object(self.config_operations, 'export_config_snapshot') as mock_export:
            mock_export.return_value = "/backup/path/config_backup_20231201_123456.json"

            backup_path = self.config_operations.backup_all_configs("test_backup_dir")

            mock_export.assert_called_once()
            assert backup_path == "/backup/path/config_backup_20231201_123456.json"

    def test_restore_configs_from_backup(self):
        """测试从备份恢复配置"""
        # 创建临时备份文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            backup_data = {
                "timestamp": "2023-12-01T12:00:00",
                "configs": {"test": "data"}
            }
            json.dump(backup_data, temp_file)
            backup_file = temp_file.name

        try:
            # 由于恢复功能目前只是打印信息，我们测试它不会抛出异常
            result = self.config_operations.restore_configs_from_backup(backup_file)
            assert result is True

        finally:
            # 清理临时文件
            if os.path.exists(backup_file):
                os.unlink(backup_file)

    def test_restore_configs_from_backup_error(self):
        """测试从备份恢复配置时发生错误"""
        result = self.config_operations.restore_configs_from_backup("/nonexistent/file.json")
        assert result is False

    def test_compare_configs(self):
        """测试比较两个配置"""
        config1 = {"param1": "value1", "param2": "value2"}
        config2 = {"param1": "value1", "param2": "different_value", "param3": "new_value"}

        self.mock_config_manager.load_config.side_effect = [config1, config2]

        comparison = self.config_operations.compare_configs("llms", "config1", "config2")

        assert comparison["config_type"] == "llms"
        assert comparison["config1"] == "config1"
        assert comparison["config2"] == "config2"
        assert "differences" in comparison
        # param2应该被标记为已更改
        assert "param2" in comparison["differences"]
        assert comparison["differences"]["param2"]["status"] == "changed"
        # param3应该被标记为新增
        assert "param3" in comparison["differences"]
        assert comparison["differences"]["param3"]["status"] == "added"

    def test_compare_configs_identical(self):
        """测试比较相同配置"""
        config = {"param1": "value1", "param2": "value2"}

        self.mock_config_manager.load_config.side_effect = [config, config]

        comparison = self.config_operations.compare_configs("tool-sets", "config1", "config2")

        assert comparison["identical"] is True
        assert len(comparison["differences"]) == 0

    def test_compare_configs_invalid_type(self):
        """测试不支持的配置类型"""
        with pytest.raises(ValueError, match="不支持的配置类型"):
            self.config_operations.compare_configs("invalid_type", "config1", "config2")

    def test_compare_configs_error(self):
        """测试比较配置时发生错误"""
        self.mock_config_manager.load_config.side_effect = Exception("Load error")

        comparison = self.config_operations.compare_configs("llms", "config1", "config2")

        assert "error" in comparison
        assert comparison["error"] == "Load error"

    def test_to_dict_with_dict(self):
        """测试_to_dict方法处理字典"""
        result = ConfigOperations._to_dict({"key": "value"})
        assert result == {"key": "value"}

    def test_to_dict_with_obj_with_dict_method(self):
        """测试_to_dict方法处理有dict方法的对象"""
        class MockObj:
            def dict(self):
                return {"attr": "value"}

        result = ConfigOperations._to_dict(MockObj())
        assert result == {"attr": "value"}

    def test_to_dict_with_obj_with_dict_attr(self):
        """测试_to_dict方法处理有__dict__属性的对象"""
        class MockObj:
            def __init__(self):
                self.attr = "value"

        obj = MockObj()
        result = ConfigOperations._to_dict(obj)
        assert result == {"attr": "value"}

    def test_to_dict_with_other_type(self):
        """测试_to_dict方法处理其他类型"""
        result = ConfigOperations._to_dict("string")
        assert result == "string"

        result = ConfigOperations._to_dict(123)
        assert result == 123