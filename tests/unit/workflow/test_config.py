"""工作流配置模型测试"""

import pytest
from src.workflow.config import (
    WorkflowConfig,
    NodeConfig,
    EdgeConfig,
    StateSchemaConfig,
    EdgeType
)


class TestStateSchemaConfig:
    """状态模式配置测试"""

    def test_default_state_schema(self):
        """测试默认状态模式配置"""
        schema = StateSchemaConfig()
        
        assert schema.messages == "List[BaseMessage]"
        assert schema.tool_calls == "List[ToolCall]"
        assert schema.tool_results == "List[ToolResult]"
        assert schema.iteration_count == "int"
        assert schema.max_iterations == "int"
        assert schema.additional_fields == {}

    def test_state_schema_to_dict(self):
        """测试状态模式转换为字典"""
        schema = StateSchemaConfig(
            additional_fields={"custom_field": "str"}
        )
        
        result = schema.to_dict()
        
        assert result["messages"] == "List[BaseMessage]"
        assert result["custom_field"] == "str"


class TestNodeConfig:
    """节点配置测试"""

    def test_node_config_from_dict(self):
        """测试从字典创建节点配置"""
        data = {
            "type": "analysis_node",
            "config": {
                "llm_client": "openai-gpt4",
                "max_tokens": 2000
            },
            "description": "分析节点"
        }
        
        node_config = NodeConfig.from_dict(data)
        
        assert node_config.type == "analysis_node"
        assert node_config.config["llm_client"] == "openai-gpt4"
        assert node_config.config["max_tokens"] == 2000
        assert node_config.description == "分析节点"

    def test_node_config_from_dict_minimal(self):
        """测试从字典创建最小节点配置"""
        data = {
            "type": "tool_node"
        }
        
        node_config = NodeConfig.from_dict(data)
        
        assert node_config.type == "tool_node"
        assert node_config.config == {}
        assert node_config.description is None


class TestEdgeConfig:
    """边配置测试"""

    def test_edge_config_from_dict_simple(self):
        """测试从字典创建简单边配置"""
        data = {
            "from": "analyze",
            "to": "execute_tool",
            "type": "simple"
        }
        
        edge_config = EdgeConfig.from_dict(data)
        
        assert edge_config.from_node == "analyze"
        assert edge_config.to_node == "execute_tool"
        assert edge_config.type == EdgeType.SIMPLE
        assert edge_config.condition is None

    def test_edge_config_from_dict_conditional(self):
        """测试从字典创建条件边配置"""
        data = {
            "from": "analyze",
            "to": "execute_tool",
            "type": "conditional",
            "condition": "has_tool_calls"
        }
        
        edge_config = EdgeConfig.from_dict(data)
        
        assert edge_config.from_node == "analyze"
        assert edge_config.to_node == "execute_tool"
        assert edge_config.type == EdgeType.CONDITIONAL
        assert edge_config.condition == "has_tool_calls"

    def test_edge_config_to_dict(self):
        """测试边配置转换为字典"""
        edge_config = EdgeConfig(
            from_node="analyze",
            to_node="execute_tool",
            type=EdgeType.CONDITIONAL,
            condition="has_tool_calls"
        )
        
        result = edge_config.to_dict()
        
        assert result["from"] == "analyze"
        assert result["to"] == "execute_tool"
        assert result["type"] == "conditional"
        assert result["condition"] == "has_tool_calls"


class TestWorkflowConfig:
    """工作流配置测试"""

    def test_workflow_config_from_dict_minimal(self):
        """测试从字典创建最小工作流配置"""
        data = {
            "name": "test_workflow",
            "description": "测试工作流"
        }
        
        workflow_config = WorkflowConfig.from_dict(data)
        
        assert workflow_config.name == "test_workflow"
        assert workflow_config.description == "测试工作流"
        assert workflow_config.version == "1.0"
        assert workflow_config.nodes == {}
        assert workflow_config.edges == []
        assert workflow_config.entry_point is None

    def test_workflow_config_from_dict_complete(self):
        """测试从字典创建完整工作流配置"""
        data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "2.0",
            "state_schema": {
                "messages": "List[BaseMessage]",
                "custom_field": "str"
            },
            "nodes": {
                "analyze": {
                    "type": "analysis_node",
                    "config": {"llm_client": "openai-gpt4"}
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
        
        workflow_config = WorkflowConfig.from_dict(data)
        
        assert workflow_config.name == "test_workflow"
        assert workflow_config.description == "测试工作流"
        assert workflow_config.version == "2.0"
        assert workflow_config.state_schema.additional_fields["custom_field"] == "str"
        assert "analyze" in workflow_config.nodes
        assert len(workflow_config.edges) == 1
        assert workflow_config.entry_point == "analyze"

    def test_workflow_config_validate_valid(self):
        """测试验证有效的工作流配置"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "analyze": NodeConfig(type="analysis_node"),
                "execute_tool": NodeConfig(type="tool_node")
            },
            edges=[
                EdgeConfig(
                    from_node="analyze",
                    to_node="execute_tool",
                    type=EdgeType.CONDITIONAL,
                    condition="has_tool_calls"
                )
            ],
            entry_point="analyze"
        )
        
        errors = config.validate()
        assert errors == []

    def test_workflow_config_validate_missing_name(self):
        """测试验证缺少名称的工作流配置"""
        config = WorkflowConfig(
            name="",
            description="测试工作流"
        )
        
        errors = config.validate()
        assert "工作流名称不能为空" in errors

    def test_workflow_config_validate_missing_description(self):
        """测试验证缺少描述的工作流配置"""
        config = WorkflowConfig(
            name="test_workflow",
            description=""
        )
        
        errors = config.validate()
        assert "工作流描述不能为空" in errors

    def test_workflow_config_validate_missing_nodes(self):
        """测试验证缺少节点的工作流配置"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={}
        )
        
        errors = config.validate()
        assert "工作流必须至少包含一个节点" in errors

    def test_workflow_config_validate_invalid_edge_nodes(self):
        """测试验证边中节点不存在的工作流配置"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "analyze": NodeConfig(type="analysis_node")
            },
            edges=[
                EdgeConfig(
                    from_node="analyze",
                    to_node="nonexistent",
                    type=EdgeType.SIMPLE
                )
            ]
        )
        
        errors = config.validate()
        assert "边的目标节点 'nonexistent' 不存在" in errors

    def test_workflow_config_validate_conditional_edge_without_condition(self):
        """测试验证条件边缺少条件的工作流配置"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "analyze": NodeConfig(type="analysis_node"),
                "execute_tool": NodeConfig(type="tool_node")
            },
            edges=[
                EdgeConfig(
                    from_node="analyze",
                    to_node="execute_tool",
                    type=EdgeType.CONDITIONAL,
                    condition=None
                )
            ]
        )
        
        errors = config.validate()
        assert "条件边 'analyze' -> 'execute_tool' 缺少条件表达式" in errors

    def test_workflow_config_validate_invalid_entry_point(self):
        """测试验证入口点不存在的工作流配置"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            nodes={
                "analyze": NodeConfig(type="analysis_node")
            },
            entry_point="nonexistent"
        )
        
        errors = config.validate()
        assert "入口节点 'nonexistent' 不存在" in errors

    def test_workflow_config_to_dict(self):
        """测试工作流配置转换为字典"""
        config = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            version="2.0",
            nodes={
                "analyze": NodeConfig(
                    type="analysis_node",
                    config={"llm_client": "openai-gpt4"},
                    description="分析节点"
                )
            },
            edges=[
                EdgeConfig(
                    from_node="analyze",
                    to_node="execute_tool",
                    type=EdgeType.CONDITIONAL,
                    condition="has_tool_calls"
                )
            ],
            entry_point="analyze"
        )
        
        result = config.to_dict()
        
        assert result["name"] == "test_workflow"
        assert result["description"] == "测试工作流"
        assert result["version"] == "2.0"
        assert "analyze" in result["nodes"]
        assert len(result["edges"]) == 1
        assert result["entry_point"] == "analyze"
        assert result["nodes"]["analyze"]["description"] == "分析节点"