"""工作流构建器测试

测试工作流构建器的功能。
"""

import unittest
from unittest.mock import Mock, patch
import yaml
from pathlib import Path

from src.infrastructure.graph.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.builder import GraphBuilder
import io

class TestWorkflowBuilder(unittest.TestCase):
    """测试工作流构建器"""

    def setUp(self):
        """设置测试环境"""
        self.mock_node_registry = Mock()
        self.builder = GraphBuilder(node_registry=self.mock_node_registry)
        
        # 创建测试配置，包含状态模式
        self.test_config = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0.0",
            "entry_point": "start",
            "state_schema": {
                "name": "TestState",
                "fields": {
                    "messages": {
                        "type": "List[dict]",
                        "reducer": "append"
                    },
                    "current_step": {
                        "type": "str",
                        "default": "start"
                    }
                }
            },
            "nodes": {
                "start": {
                    "function": "test_function",
                    "type": "llm",
                    "config": {"model": "gpt-3.5-turbo"}
                },
                "end": {
                    "function": "end_function",
                    "type": "tool",
                    "config": {"tool_name": "calculator"}
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "end",
                    "type": "simple"
                }
            ]
        }

    def test_build_from_dict(self):
        """测试从字典构建"""
        config = WorkflowConfig.from_dict(self.test_config)
        graph = self.builder.build_graph(config)
        self.assertIsNotNone(graph)

    def test_build_from_yaml_content(self):
        """测试从YAML内容构建图"""
        yaml_content = yaml.dump(self.test_config)
        # 使用from_dict方法并通过yaml.safe_load解析YAML内容
        config_dict = yaml.safe_load(io.StringIO(yaml_content))
        config = WorkflowConfig.from_dict(config_dict)
        graph = self.builder.build_graph(config)
        self.assertIsNotNone(graph)

    def test_validate_valid_config(self):
        """测试验证有效配置"""
        config = WorkflowConfig.from_dict(self.test_config)
        errors = config.validate()
        self.assertEqual(len(errors), 0)

    def test_validate_invalid_config(self):
        """测试验证无效配置"""
        invalid_config = self.test_config.copy()
        invalid_config["name"] = ""  # 设置为空字符串而不是移除字段
        config = WorkflowConfig.from_dict(invalid_config)
        errors = config.validate()
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()