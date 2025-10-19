"""
ToolManager单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.tools.manager import ToolManager
from src.tools.config import (
    NativeToolConfig,
    MCPToolConfig,
    BuiltinToolConfig,
    ToolSetConfig,
)
from src.tools.types.builtin_tool import BuiltinTool


class TestToolManager:
    """ToolManager测试类"""

    def setup_method(self):
        """测试前设置"""
        self.mock_config_loader = Mock()
        self.mock_logger = Mock()
        self.tool_manager = ToolManager(self.mock_config_loader, self.mock_logger)

    def test_initialization(self):
        """测试初始化"""
        assert self.tool_manager.config_loader == self.mock_config_loader
        assert self.tool_manager.logger == self.mock_logger
        assert self.tool_manager._loaded is False
        assert len(self.tool_manager._tools) == 0
        assert len(self.tool_manager._tool_sets) == 0

    @patch("src.tools.manager.Path")
    def test_load_tools_no_config_dir(self, mock_path):
        """测试没有配置目录的情况"""
        mock_path.return_value.exists.return_value = False

        tools = self.tool_manager.load_tools()

        assert len(tools) == 0
        assert self.tool_manager._loaded is True
        self.mock_logger.warning.assert_called_with("工具配置目录不存在: configs/tools")

    @patch("src.tools.manager.Path")
    def test_load_tools_with_configs(self, mock_path):
        """测试加载工具配置"""
        # 模拟配置目录存在
        mock_config_dir = Mock()
        mock_path.return_value = mock_config_dir
        mock_config_dir.exists.return_value = True

        # 模拟配置文件
        mock_config_file = Mock()
        mock_config_dir.glob.return_value = [mock_config_file]

        # 模拟配置数据
        native_config_data = {
            "name": "test_native_tool",
            "tool_type": "native",
            "description": "测试原生工具",
            "api_url": "https://api.example.com",
            "parameters_schema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        }

        builtin_config_data = {
            "name": "test_builtin_tool",
            "tool_type": "builtin",
            "description": "测试内置工具",
            "function_path": "test_module:test_function",
            "parameters_schema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        }

        # 模拟配置加载
        self.mock_config_loader.load_yaml.side_effect = [
            native_config_data,
            builtin_config_data,
        ]

        # 模拟内置函数加载
        def mock_load_function(path):
            if path == "test_module:test_function":

                def test_function(param1: str):
                    return f"结果: {param1}"

                return test_function
            raise ValueError(f"未知路径: {path}")

        with patch.object(
            self.tool_manager,
            "_load_function_from_path",
            side_effect=mock_load_function,
        ):
            # 模拟工具集配置目录不存在
            with patch("src.tools.manager.Path") as mock_tool_sets_path:
                mock_tool_sets_dir = Mock()
                mock_tool_sets_path.return_value = mock_tool_sets_dir
                mock_tool_sets_dir.exists.return_value = False

                tools = self.tool_manager.load_tools()

                assert len(tools) == 2
                assert "test_native_tool" in self.tool_manager._tools
                assert "test_builtin_tool" in self.tool_manager._tools
                assert self.tool_manager._loaded is True

    def test_parse_tool_config_native(self):
        """测试解析原生工具配置"""
        config_data = {
            "name": "test_tool",
            "tool_type": "native",
            "description": "测试工具",
            "api_url": "https://api.example.com",
            "parameters_schema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        }

        config = self.tool_manager._parse_tool_config(config_data)

        assert isinstance(config, NativeToolConfig)
        assert config.name == "test_tool"
        assert config.tool_type == "native"
        assert config.api_url == "https://api.example.com"

    def test_parse_tool_config_mcp(self):
        """测试解析MCP工具配置"""
        config_data = {
            "name": "test_tool",
            "tool_type": "mcp",
            "description": "测试工具",
            "mcp_server_url": "https://mcp.example.com",
            "parameters_schema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        }

        config = self.tool_manager._parse_tool_config(config_data)

        assert isinstance(config, MCPToolConfig)
        assert config.name == "test_tool"
        assert config.tool_type == "mcp"
        assert config.mcp_server_url == "https://mcp.example.com"

    def test_parse_tool_config_builtin(self):
        """测试解析内置工具配置"""
        config_data = {
            "name": "test_tool",
            "tool_type": "builtin",
            "description": "测试工具",
            "function_path": "test_module:test_function",
            "parameters_schema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        }

        config = self.tool_manager._parse_tool_config(config_data)

        assert isinstance(config, BuiltinToolConfig)
        assert config.name == "test_tool"
        assert config.tool_type == "builtin"
        assert config.function_path == "test_module:test_function"

    def test_parse_tool_config_invalid_type(self):
        """测试解析无效工具类型"""
        config_data = {
            "name": "test_tool",
            "tool_type": "invalid",
            "description": "测试工具",
            "parameters_schema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        }

        with pytest.raises(ValueError, match="未知的工具类型: invalid"):
            self.tool_manager._parse_tool_config(config_data)

    def test_create_tool_native(self):
        """测试创建原生工具"""
        config = NativeToolConfig(
            name="test_tool",
            tool_type="native",
            description="测试工具",
            api_url="https://api.example.com",
            parameters_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        tool = self.tool_manager._create_tool(config)

        assert tool.name == "test_tool"
        assert tool.description == "测试工具"

    def test_create_tool_builtin(self):
        """测试创建内置工具"""

        def test_function(param1: str):
            return f"结果: {param1}"

        config = BuiltinToolConfig(
            name="test_tool",
            tool_type="builtin",
            description="测试工具",
            function_path="test_module:test_function",
            parameters_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        with patch.object(
            self.tool_manager, "_load_function_from_path", return_value=test_function
        ):
            tool = self.tool_manager._create_tool(config)

            assert isinstance(tool, BuiltinTool)
            assert tool.name == "test_tool"
            assert tool.description == "测试工具"

    def test_load_function_from_path(self):
        """测试从路径加载函数"""

        def test_function(param1: str):
            return f"结果: {param1}"

        with patch("src.tools.manager.importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_module.test_function = test_function
            mock_import.return_value = mock_module

            func = self.tool_manager._load_function_from_path(
                "test_module:test_function"
            )

            assert func == test_function
            mock_import.assert_called_once_with("test_module")

    def test_load_function_from_path_invalid(self):
        """测试从无效路径加载函数"""
        with pytest.raises(ValueError, match="加载函数失败"):
            self.tool_manager._load_function_from_path("invalid_path")

    def test_load_tool_sets(self):
        """测试加载工具集配置"""
        # 模拟工具集配置目录存在
        with patch("src.tools.manager.Path") as mock_path:
            mock_config_dir = Mock()
            mock_path.return_value = mock_config_dir
            mock_config_dir.exists.return_value = True

            # 模拟配置文件
            mock_config_file = Mock()
            mock_config_dir.glob.return_value = [mock_config_file]

            # 模拟配置数据
            tool_set_config_data = {
                "name": "test_tool_set",
                "description": "测试工具集",
                "tools": ["tool1", "tool2"],
                "enabled": True,
            }

            self.mock_config_loader.load_yaml.return_value = tool_set_config_data

            self.tool_manager._load_tool_sets()

            assert "test_tool_set" in self.tool_manager._tool_sets
            assert self.tool_manager._tool_sets["test_tool_set"].tools == [
                "tool1",
                "tool2",
            ]

    def test_get_tool(self):
        """测试获取工具"""
        # 添加一个工具到管理器
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        self.tool_manager._tools["test_tool"] = mock_tool

        # 测试获取存在的工具
        tool = self.tool_manager.get_tool("test_tool")
        assert tool == mock_tool

        # 测试获取不存在的工具
        with pytest.raises(ValueError, match="工具不存在: nonexistent_tool"):
            self.tool_manager.get_tool("nonexistent_tool")

    def test_get_tool_set(self):
        """测试获取工具集"""
        # 添加一个工具集到管理器
        mock_tool_set_config = Mock()
        mock_tool_set_config.name = "test_tool_set"
        mock_tool_set_config.tools = ["tool1", "tool2"]
        self.tool_manager._tool_sets["test_tool_set"] = mock_tool_set_config

        # 添加工具到管理器
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        self.tool_manager._tools["tool1"] = mock_tool1
        self.tool_manager._tools["tool2"] = mock_tool2

        # 测试获取存在的工具集
        tools = self.tool_manager.get_tool_set("test_tool_set")
        assert len(tools) == 2
        assert mock_tool1 in tools
        assert mock_tool2 in tools

        # 测试获取不存在的工具集
        with pytest.raises(ValueError, match="工具集不存在: nonexistent_tool_set"):
            self.tool_manager.get_tool_set("nonexistent_tool_set")

    def test_register_tool(self):
        """测试注册工具"""
        mock_tool = Mock()
        mock_tool.name = "test_tool"

        # 测试注册新工具
        self.tool_manager.register_tool(mock_tool)
        assert "test_tool" in self.tool_manager._tools
        assert self.tool_manager._tools["test_tool"] == mock_tool

        # 测试注册重复工具
        with pytest.raises(ValueError, match="工具名称已存在: test_tool"):
            self.tool_manager.register_tool(mock_tool)

    def test_list_tools(self):
        """测试列出工具"""
        # 添加工具到管理器
        self.tool_manager._tools["tool1"] = Mock()
        self.tool_manager._tools["tool2"] = Mock()

        tools = self.tool_manager.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_list_tool_sets(self):
        """测试列出工具集"""
        # 添加工具集到管理器
        self.tool_manager._tool_sets["tool_set1"] = Mock()
        self.tool_manager._tool_sets["tool_set2"] = Mock()

        tool_sets = self.tool_manager.list_tool_sets()
        assert len(tool_sets) == 2
        assert "tool_set1" in tool_sets
        assert "tool_set2" in tool_sets

    def test_reload_tools(self):
        """测试重新加载工具"""
        # 添加一些工具和工具集
        self.tool_manager._tools["tool1"] = Mock()
        self.tool_manager._tool_sets["tool_set1"] = Mock()
        self.tool_manager._loaded = True

        # 模拟加载工具
        with patch.object(self.tool_manager, "load_tools", return_value=[Mock()]):
            tools = self.tool_manager.reload_tools()

            assert len(self.tool_manager._tools) == 1
            assert len(self.tool_manager._tool_sets) == 0
            assert self.tool_manager._loaded is True

    def test_get_tool_info(self):
        """测试获取工具信息"""
        # 添加一个工具到管理器
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.to_dict.return_value = {
            "name": "test_tool",
            "description": "测试工具",
        }
        self.tool_manager._tools["test_tool"] = mock_tool

        info = self.tool_manager.get_tool_info("test_tool")
        assert info["name"] == "test_tool"
        assert info["description"] == "测试工具"

    def test_get_tool_set_info(self):
        """测试获取工具集信息"""
        # 添加一个工具集到管理器
        mock_tool_set_config = Mock()
        mock_tool_set_config.name = "test_tool_set"
        mock_tool_set_config.description = "测试工具集"
        mock_tool_set_config.tools = ["tool1"]
        mock_tool_set_config.enabled = True
        mock_tool_set_config.metadata = {}
        self.tool_manager._tool_sets["test_tool_set"] = mock_tool_set_config

        # 添加工具到管理器
        mock_tool = Mock()
        mock_tool.name = "tool1"
        mock_tool.to_dict.return_value = {"name": "tool1", "description": "工具1"}
        self.tool_manager._tools["tool1"] = mock_tool

        info = self.tool_manager.get_tool_set_info("test_tool_set")
        assert info["name"] == "test_tool_set"
        assert info["description"] == "测试工具集"
        assert len(info["tools"]) == 1
        assert info["tools"][0]["name"] == "tool1"
