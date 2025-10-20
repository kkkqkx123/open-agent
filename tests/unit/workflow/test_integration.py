"""工作流系统集成测试"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import yaml

from src.workflow.manager import WorkflowManager
from src.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from src.workflow.registry import NodeRegistry, BaseNode, NodeExecutionResult
from src.prompts.agent_state import AgentState


class MockLLMNode(BaseNode):
    """模拟LLM节点"""
    
    @property
    def node_type(self) -> str:
        return "mock_llm_node"
    
    def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
        # 模拟添加消息
        mock_message = Mock()
        mock_message.content = "模拟LLM响应"
        state.add_message(mock_message)
        
        # 根据配置决定下一步
        next_node = config.get("next_node")
        
        return NodeExecutionResult(
            state=state,
            next_node=next_node
        )
    
    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "next_node": {"type": "string"}
            }
        }


class MockToolNode(BaseNode):
    """模拟工具节点"""
    
    @property
    def node_type(self) -> str:
        return "mock_tool_node"
    
    def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
        # 模拟工具执行结果
        from src.prompts.agent_state import ToolResult
        tool_result = ToolResult(
            tool_name="mock_tool",
            success=True,
            result="模拟工具执行结果"
        )
        state.tool_results.append(tool_result)
        
        return NodeExecutionResult(
            state=state,
            next_node="final"
        )
    
    def get_config_schema(self) -> dict:
        return {"type": "object", "properties": {}}


class TestWorkflowIntegration:
    """工作流系统集成测试"""

    def test_end_to_end_workflow_execution(self):
        """测试端到端工作流执行"""
        # 创建临时配置文件
        config_data = {
            "name": "integration_test_workflow",
            "description": "集成测试工作流",
            "nodes": {
                "start": {
                    "type": "mock_llm_node",
                    "config": {
                        "next_node": "tool"
                    }
                },
                "tool": {
                    "type": "mock_tool_node",
                    "config": {}
                },
                "final": {
                    "type": "mock_llm_node",
                    "config": {}
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "tool",
                    "type": "simple"
                },
                {
                    "from": "tool",
                    "to": "final",
                    "type": "simple"
                }
            ],
            "entry_point": "start"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 设置节点注册表
            node_registry = NodeRegistry()
            node_registry.register_node(MockLLMNode)
            node_registry.register_node(MockToolNode)
            
            # 创建工作流管理器
            manager = WorkflowManager(node_registry=node_registry)
            
            # 加载工作流
            workflow_id = manager.load_workflow(temp_path)
            
            # 验证工作流加载
            assert workflow_id is not None
            assert workflow_id in manager._workflows
            
            # 运行工作流
            initial_state = AgentState()
            result = manager.run_workflow(workflow_id, initial_state)
            
            # 验证执行结果
            assert isinstance(result, AgentState)
            assert len(result.messages) == 2  # start和final节点各添加一条消息
            assert len(result.tool_results) == 1  # tool节点添加了一个工具结果
            
            # 验证元数据更新
            metadata = manager.get_workflow_metadata(workflow_id)
            assert metadata["usage_count"] == 1
            assert "last_used" in metadata
            
        finally:
            Path(temp_path).unlink()

    def test_conditional_workflow_execution(self):
        """测试条件工作流执行"""
        # 创建临时配置文件
        config_data = {
            "name": "conditional_test_workflow",
            "description": "条件测试工作流",
            "nodes": {
                "analyze": {
                    "type": "mock_llm_node",
                    "config": {
                        "next_node": "tool"  # 模拟需要调用工具
                    }
                },
                "tool": {
                    "type": "mock_tool_node",
                    "config": {}
                },
                "final": {
                    "type": "mock_llm_node",
                    "config": {}
                }
            },
            "edges": [
                {
                    "from": "analyze",
                    "to": "tool",
                    "condition": "has_tool_calls",
                    "type": "conditional"
                },
                {
                    "from": "analyze",
                    "to": "final",
                    "condition": "no_tool_calls",
                    "type": "conditional"
                },
                {
                    "from": "tool",
                    "to": "final",
                    "type": "simple"
                }
            ],
            "entry_point": "analyze"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 设置节点注册表
            node_registry = NodeRegistry()
            node_registry.register_node(MockLLMNode)
            node_registry.register_node(MockToolNode)
            
            # 创建工作流管理器
            manager = WorkflowManager(node_registry=node_registry)
            
            # 加载工作流
            workflow_id = manager.load_workflow(temp_path)
            
            # 运行工作流
            initial_state = AgentState()
            result = manager.run_workflow(workflow_id, initial_state)
            
            # 验证执行结果
            assert isinstance(result, AgentState)
            assert len(result.messages) >= 2  # 至少有analyze和final节点的消息
            assert len(result.tool_results) == 1  # tool节点添加了一个工具结果
            
        finally:
            Path(temp_path).unlink()

    def test_workflow_error_handling(self):
        """测试工作流错误处理"""
        # 创建会抛出异常的节点
        class ErrorNode(BaseNode):
            @property
            def node_type(self) -> str:
                return "error_node"
            
            def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
                raise Exception("模拟节点执行错误")
            
            def get_config_schema(self) -> dict:
                return {"type": "object", "properties": {}}
        
        # 创建临时配置文件
        config_data = {
            "name": "error_test_workflow",
            "description": "错误测试工作流",
            "nodes": {
                "error": {
                    "type": "error_node",
                    "config": {}
                }
            },
            "edges": [],
            "entry_point": "error"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 设置节点注册表
            node_registry = NodeRegistry()
            node_registry.register_node(ErrorNode)
            
            # 创建工作流管理器
            manager = WorkflowManager(node_registry=node_registry)
            
            # 加载工作流
            workflow_id = manager.load_workflow(temp_path)
            
            # 运行工作流应该抛出异常
            with pytest.raises(Exception, match="模拟节点执行错误"):
                manager.run_workflow(workflow_id)
            
            # 验证错误被记录
            metadata = manager.get_workflow_metadata(workflow_id)
            assert "errors" in metadata
            assert len(metadata["errors"]) == 1
            assert "模拟节点执行错误" in metadata["errors"][0]["error_message"]
            
        finally:
            Path(temp_path).unlink()

    def test_workflow_reload(self):
        """测试工作流重新加载"""
        # 创建初始配置文件
        config_data_v1 = {
            "name": "reload_test_workflow",
            "description": "重新加载测试工作流",
            "version": "1.0",
            "nodes": {
                "start": {
                    "type": "mock_llm_node",
                    "config": {}
                }
            },
            "edges": [],
            "entry_point": "start"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data_v1, f)
            temp_path = f.name
        
        try:
            # 设置节点注册表
            node_registry = NodeRegistry()
            node_registry.register_node(MockLLMNode)
            
            # 创建工作流管理器
            manager = WorkflowManager(node_registry=node_registry)
            
            # 加载工作流
            workflow_id = manager.load_workflow(temp_path)
            
            # 验证初始版本
            config = manager.get_workflow_config(workflow_id)
            assert config.version == "1.0"
            
            # 更新配置文件
            config_data_v2 = {
                "name": "reload_test_workflow",
                "description": "重新加载测试工作流 - 更新版本",
                "version": "2.0",
                "nodes": {
                    "start": {
                        "type": "mock_llm_node",
                        "config": {}
                    },
                    "new_node": {
                        "type": "mock_tool_node",
                        "config": {}
                    }
                },
                "edges": [
                    {
                        "from": "start",
                        "to": "new_node",
                        "type": "simple"
                    }
                ],
                "entry_point": "start"
            }
            
            with open(temp_path, 'w') as f:
                yaml.dump(config_data_v2, f)
            
            # 重新加载工作流
            result = manager.reload_workflow(workflow_id)
            
            # 验证重新加载成功
            assert result is True
            
            # 验证新版本
            config = manager.get_workflow_config(workflow_id)
            assert config.version == "2.0"
            assert "new_node" in config.nodes
            assert len(config.edges) == 1
            
        finally:
            Path(temp_path).unlink()

    def test_workflow_unload(self):
        """测试工作流卸载"""
        # 创建临时配置文件
        config_data = {
            "name": "unload_test_workflow",
            "description": "卸载测试工作流",
            "nodes": {
                "start": {
                    "type": "mock_llm_node",
                    "config": {}
                }
            },
            "edges": [],
            "entry_point": "start"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 设置节点注册表
            node_registry = NodeRegistry()
            node_registry.register_node(MockLLMNode)
            
            # 创建工作流管理器
            manager = WorkflowManager(node_registry=node_registry)
            
            # 加载工作流
            workflow_id = manager.load_workflow(temp_path)
            
            # 验证工作流存在
            assert workflow_id in manager.list_workflows()
            assert manager.get_workflow_config(workflow_id) is not None
            
            # 卸载工作流
            result = manager.unload_workflow(workflow_id)
            
            # 验证卸载成功
            assert result is True
            assert workflow_id not in manager.list_workflows()
            assert manager.get_workflow_config(workflow_id) is None
            
        finally:
            Path(temp_path).unlink()

    def test_multiple_workflows_management(self):
        """测试多个工作流管理"""
        # 创建第一个工作流配置
        config_data1 = {
            "name": "workflow1",
            "description": "第一个工作流",
            "nodes": {
                "start": {
                    "type": "mock_llm_node",
                    "config": {}
                }
            },
            "edges": [],
            "entry_point": "start"
        }
        
        # 创建第二个工作流配置
        config_data2 = {
            "name": "workflow2",
            "description": "第二个工作流",
            "nodes": {
                "start": {
                    "type": "mock_tool_node",
                    "config": {}
                }
            },
            "edges": [],
            "entry_point": "start"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
            yaml.dump(config_data1, f1)
            yaml.dump(config_data2, f2)
            temp_path1 = f1.name
            temp_path2 = f2.name
        
        try:
            # 设置节点注册表
            node_registry = NodeRegistry()
            node_registry.register_node(MockLLMNode)
            node_registry.register_node(MockToolNode)
            
            # 创建工作流管理器
            manager = WorkflowManager(node_registry=node_registry)
            
            # 加载两个工作流
            workflow_id1 = manager.load_workflow(temp_path1)
            workflow_id2 = manager.load_workflow(temp_path2)
            
            # 验证两个工作流都存在
            workflows = manager.list_workflows()
            assert len(workflows) == 2
            assert workflow_id1 in workflows
            assert workflow_id2 in workflows
            
            # 验证工作流配置
            config1 = manager.get_workflow_config(workflow_id1)
            config2 = manager.get_workflow_config(workflow_id2)
            assert config1.name == "workflow1"
            assert config2.name == "workflow2"
            
            # 运行第一个工作流
            result1 = manager.run_workflow(workflow_id1)
            assert isinstance(result1, AgentState)
            
            # 运行第二个工作流
            result2 = manager.run_workflow(workflow_id2)
            assert isinstance(result2, AgentState)
            
            # 验证使用统计
            metadata1 = manager.get_workflow_metadata(workflow_id1)
            metadata2 = manager.get_workflow_metadata(workflow_id2)
            assert metadata1["usage_count"] == 1
            assert metadata2["usage_count"] == 1
            
        finally:
            Path(temp_path1).unlink()
            Path(temp_path2).unlink()