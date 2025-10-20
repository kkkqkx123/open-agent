"""工作流配置测试

测试工作流配置模型的创建、验证和序列化功能。
"""

import pytest
import yaml
from pathlib import Path

from src.workflow.config import (
    WorkflowConfig,
    NodeConfig,
    EdgeConfig,
    StateSchemaConfig,
    EdgeType
)


class TestWorkflowConfig:
    """工作流配置测试类"""

    def test_workflow_config_creation(self) -> None:
        """测试工作流配置创建"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0"
        )
        
        assert config.name == "test_workflow"
        assert config.description == "测试工作流"
        assert config.version == "1.0"
        assert isinstance(config.state_schema, StateSchemaConfig)
        assert isinstance(config.nodes, dict)
        assert isinstance(config.edges, list)

    def test_workflow_config_from_dict(self) -> None:
        """测试从字典创建工作流配置"""
        data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "1.0",
            "state_schema": {
                "messages": "List[BaseMessage]",
                "tool_calls": "List[ToolCall]",
                "tool_results": "List[ToolResult]",
                "iteration_count": "int",
                "max_iterations": "int"
            },
            "nodes": {
                "analyze": {
                    "type": "analysis_node",
                    "config": {
                        "llm_client": "openai-gpt4",
                        "max_tokens": 2000
                    }
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "analyze",
                    "type": "simple"
                }
            ],
            "entry_point": "analyze"
        }
        
        config = WorkflowConfig.from_dict(data)
        
        assert config.name == "test_workflow"
        assert config.description == "测试工作流"
        assert config.version == "1.0"
        assert config.entry_point == "analyze"
        assert "analyze" in config.nodes
        assert len(config.edges) == 1
        assert config.edges[0].from_node == "start"
        assert config.edges[0].to_node == "analyze"

    def test_workflow_config_to_dict(self) -> None:
        """测试工作流配置转换为字典"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0"
        )
        
        # 添加节点
        config.nodes["analyze"] = NodeConfig(
            type="analysis_node",
            config={"llm_client": "openai-gpt4"},
            description="分析节点"
        )
        
        # 添加边
        config.edges.append(EdgeConfig(
            from_node="start",
            to_node="analyze",
            type=EdgeType.SIMPLE
        ))
        
        config.entry_point = "analyze"
        
        data = config.to_dict()
        
        assert data["name"] == "test_workflow"
        assert data["description"] == "测试工作流"
        assert data["version"] == "1.0"
        assert data["entry_point"] == "analyze"
        assert "analyze" in data["nodes"]
        assert data["nodes"]["analyze"]["type"] == "analysis_node"
        assert len(data["edges"]) == 1

    def test_workflow_config_validation(self) -> None:
        """测试工作流配置验证"""
        # 有效配置
        valid_config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0"
        )
        valid_config.nodes["analyze"] = NodeConfig(
            type="analysis_node",
            config={"llm_client": "openai-gpt4"}
        )
        valid_config.edges.append(EdgeConfig(
            from_node="start",
            to_node="analyze",
            type=EdgeType.SIMPLE
        ))
        
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # 无效配置 - 缺少名称
        invalid_config = WorkflowConfig(
            name="",
            description="测试工作流",
            version="1.0"
        )
        
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert any("名称不能为空" in error for error in errors)
        
        # 无效配置 - 缺少节点
        invalid_config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0"
        )
        
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert any("必须至少包含一个节点" in error for error in errors)
        
        # 无效配置 - 边引用不存在的节点
        invalid_config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0"
        )
        invalid_config.nodes["analyze"] = NodeConfig(
            type="analysis_node",
            config={"llm_client": "openai-gpt4"}
        )
        invalid_config.edges.append(EdgeConfig(
            from_node="start",
            to_node="nonexistent",
            type=EdgeType.SIMPLE
        ))
        
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert any("起始节点 'start' 不存在" in error for error in errors)

    def test_node_config_creation(self) -> None:
        """测试节点配置创建"""
        config = NodeConfig(
            type="analysis_node",
            config={"llm_client": "openai-gpt4"},
            description="分析节点"
        )
        
        assert config.type == "analysis_node"
        assert config.config["llm_client"] == "openai-gpt4"
        assert config.description == "分析节点"

    def test_node_config_from_dict(self) -> None:
        """测试从字典创建节点配置"""
        data = {
            "type": "analysis_node",
            "config": {
                "llm_client": "openai-gpt4",
                "max_tokens": 2000
            },
            "description": "分析节点"
        }
        
        config = NodeConfig.from_dict(data)
        
        assert config.type == "analysis_node"
        assert config.config["llm_client"] == "openai-gpt4"
        assert config.config["max_tokens"] == 2000
        assert config.description == "分析节点"

    def test_edge_config_creation(self) -> None:
        """测试边配置创建"""
        config = EdgeConfig(
            from_node="start",
            to_node="analyze",
            type=EdgeType.SIMPLE,
            description="开始到分析"
        )
        
        assert config.from_node == "start"
        assert config.to_node == "analyze"
        assert config.type == EdgeType.SIMPLE
        assert config.description == "开始到分析"

    def test_edge_config_from_dict(self) -> None:
        """测试从字典创建边配置"""
        data = {
            "from": "start",
            "to": "analyze",
            "type": "simple",
            "description": "开始到分析"
        }
        
        config = EdgeConfig.from_dict(data)
        
        assert config.from_node == "start"
        assert config.to_node == "analyze"
        assert config.type == EdgeType.SIMPLE
        assert config.description == "开始到分析"

    def test_edge_config_to_dict(self) -> None:
        """测试边配置转换为字典"""
        config = EdgeConfig(
            from_node="start",
            to_node="analyze",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls",
            description="条件边"
        )
        
        data = config.to_dict()
        
        assert data["from"] == "start"
        assert data["to"] == "analyze"
        assert data["type"] == "conditional"
        assert data["condition"] == "has_tool_calls"
        assert data["description"] == "条件边"

    def test_state_schema_config(self) -> None:
        """测试状态模式配置"""
        config = StateSchemaConfig()
        
        assert config.messages == "List[BaseMessage]"
        assert config.tool_calls == "List[ToolCall]"
        assert config.tool_results == "List[ToolResult]"
        assert config.iteration_count == "int"
        assert config.max_iterations == "int"
        
        # 测试自定义字段
        config.additional_fields["custom_field"] = "str"
        
        data = config.to_dict()
        assert "custom_field" in data
        assert data["custom_field"] == "str"

    def test_workflow_config_yaml_serialization(self, tmp_path: Path) -> None:
        """测试工作流配置YAML序列化"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="1.0"
        )
        
        # 添加节点
        config.nodes["analyze"] = NodeConfig(
            type="analysis_node",
            config={"llm_client": "openai-gpt4"},
            description="分析节点"
        )
        
        # 添加边
        config.edges.append(EdgeConfig(
            from_node="start",
            to_node="analyze",
            type=EdgeType.SIMPLE
        ))
        
        config.entry_point = "analyze"
        
        # 保存到YAML文件
        yaml_file = tmp_path / "test_workflow.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, allow_unicode=True)
        
        # 从YAML文件加载
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        loaded_config = WorkflowConfig.from_dict(data)
        
        assert loaded_config.name == config.name
        assert loaded_config.description == config.description
        assert loaded_config.version == config.version
        assert loaded_config.entry_point == config.entry_point
        assert len(loaded_config.nodes) == len(config.nodes)
        assert len(loaded_config.edges) == len(config.edges)

    def test_conditional_edge_validation(self) -> None:
        """测试条件边验证"""
        # 有效条件边
        valid_edge = EdgeConfig(
            from_node="analyze",
            to_node="execute_tool",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls"
        )
        
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        config.nodes["analyze"] = NodeConfig(type="analysis_node", config={})
        config.nodes["execute_tool"] = NodeConfig(type="tool_node", config={})
        config.edges.append(valid_edge)
        
        errors = config.validate()
        assert len(errors) == 0
        
        # 无效条件边 - 缺少条件
        invalid_edge = EdgeConfig(
            from_node="analyze",
            to_node="execute_tool",
            type=EdgeType.CONDITIONAL
        )
        
        config.edges[0] = invalid_edge
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("缺少条件表达式" in error for error in errors)