"""Test workflow architecture migration.

This module tests the new workflow architecture to ensure all components
are properly integrated and functioning as expected.
"""

import pytest
from typing import Dict, Any

# Test core imports
from src.core.workflow import Workflow, WorkflowState
from src.core.workflow.interfaces import IWorkflow, IWorkflowState

# Test graph sub-module imports
from src.core.workflow.graph import (
    GraphBuilder, BaseNode, LLMNode, ToolNode,
    BaseEdge, SimpleEdge, ConditionalEdge
)

# Test execution sub-module imports
from src.core.workflow.execution import (
    WorkflowExecutor, AsyncWorkflowExecutor, StreamingWorkflowExecutor
)

# Test plugin sub-module imports
from src.core.workflow.plugins import (
    PluginManager, PluginRegistry, BasePlugin
)

# Test service layer imports
from src.services.workflow import (
    WorkflowManager, WorkflowFactory, WorkflowExecutor as ServiceExecutor,
    WorkflowOrchestrator, WorkflowRegistry
)

# Test adapter layer imports
from src.adapters.workflow import (
    WorkflowVisualizer
)

# Test services layer imports
from src.services.workflow.langgraph_builder import LangGraphBuilder
from services.workflow.execution.async_executor import AsyncWorkflowExecutor


class TestWorkflowArchitecture:
    """Test the new workflow architecture."""
    
    def test_core_workflow_creation(self):
        """Test core workflow creation."""
        workflow = Workflow("test-workflow", "Test Workflow")
        
        assert workflow.workflow_id == "test-workflow"
        assert workflow.name == "Test Workflow"
        assert isinstance(workflow, IWorkflow)
    
    def test_workflow_state_creation(self):
        """Test workflow state creation."""
        state = WorkflowState()
        
        assert isinstance(state, IWorkflowState)
        assert state.messages == []
        assert state.values == {}
        assert state.metadata == {}
        assert state.iteration_count == 0
    
    def test_graph_builder_creation(self):
        """Test graph builder creation."""
        builder = GraphBuilder()
        
        assert builder is not None
    
    def test_node_creation(self):
        """Test node creation."""
        # Test base node
        base_node = BaseNode("test-node")
        assert base_node.node_id == "test-node"
        
        # Test LLM node
        llm_node = LLMNode("llm-node")
        assert llm_node.node_id == "llm-node"
        
        # Test tool node
        tool_node = ToolNode("tool-node")
        assert tool_node.node_id == "tool-node"
    
    def test_edge_creation(self):
        """Test edge creation."""
        # Test simple edge
        simple_edge = SimpleEdge("node1", "node2")
        assert simple_edge.source == "node1"
        assert simple_edge.target == "node2"
        
        # Test conditional edge
        conditional_edge = ConditionalEdge("node1", "node2", lambda x: True)
        assert conditional_edge.source == "node1"
        assert conditional_edge.target == "node2"
    
    def test_execution_engines(self):
        """Test execution engines."""
        # Test workflow executor
        executor = WorkflowExecutor()
        assert executor is not None
        
        # Test async workflow executor
        async_executor = AsyncWorkflowExecutor()
        assert async_executor is not None
        
        # Test streaming workflow executor
        streaming_executor = StreamingWorkflowExecutor()
        assert streaming_executor is not None
    
    def test_plugin_system(self):
        """Test plugin system."""
        # Test plugin registry
        registry = PluginRegistry()
        assert registry is not None
        
        # Test plugin manager
        manager = PluginManager(registry)
        assert manager is not None
        
        # Test base plugin
        plugin = BasePlugin("test-plugin")
        assert plugin.plugin_id == "test-plugin"
    
    def test_service_layer(self):
        """Test service layer components."""
        # Test workflow registry
        registry = WorkflowRegistry()
        assert registry is not None
        
        # Test workflow factory
        factory = WorkflowFactory(registry)
        assert factory is not None
        
        # Test workflow executor
        executor = ServiceExecutor()
        assert executor is not None
        
        # Test workflow orchestrator
        orchestrator = WorkflowOrchestrator()
        assert orchestrator is not None
        
        # Test workflow manager
        manager = WorkflowManager(orchestrator, executor, registry)
        assert manager is not None
    
    def test_adapter_layer(self):
        """Test adapter layer components."""
        # Test LangGraph adapter
        langgraph_adapter = LangGraphAdapter()
        assert langgraph_adapter is not None
        
        # Test async adapter
        async_adapter = AsyncAdapter()
        assert async_adapter is not None
    
    def test_workflow_configuration(self):
        """Test workflow configuration."""
        config = {
            "workflow_id": "test-workflow",
            "name": "Test Workflow",
            "nodes": [
                {
                    "node_id": "start",
                    "node_type": "start_node",
                    "config": {}
                },
                {
                    "node_id": "llm",
                    "node_type": "llm_node",
                    "config": {
                        "model": "gpt-3.5-turbo",
                        "prompt": "Hello, world!"
                    }
                },
                {
                    "node_id": "end",
                    "node_type": "end_node",
                    "config": {}
                }
            ],
            "edges": [
                {
                    "source": "start",
                    "target": "llm",
                    "edge_type": "simple_edge"
                },
                {
                    "source": "llm",
                    "target": "end",
                    "edge_type": "simple_edge"
                }
            ],
            "entry_point": "start"
        }
        
        # Test workflow creation from config
        workflow = Workflow("test-workflow", "Test Workflow")
        
        # Add nodes
        for node_config in config["nodes"]:
            workflow.add_node(node_config)
        
        # Add edges
        for edge_config in config["edges"]:
            workflow.add_edge(edge_config)
        
        # Set entry point
        workflow.set_entry_point(config["entry_point"])
        
        assert workflow.workflow_id == "test-workflow"
        assert workflow.name == "Test Workflow"
    
    def test_workflow_state_operations(self):
        """Test workflow state operations."""
        state = WorkflowState()
        
        # Test adding messages
        from src.core.workflow.states import HumanMessage, AIMessage
        
        human_msg = HumanMessage(content="Hello")
        ai_msg = AIMessage(content="Hi there!")
        
        state.add_message(human_msg)
        state.add_message(ai_msg)
        
        assert len(state.messages) == 2
        
        # Test updating values
        state.update_value("test_key", "test_value")
        assert state.get_value("test_key") == "test_value"
        
        # Test iteration count
        state.increment_iteration()
        assert state.iteration_count == 1
        
        # Test execution history
        state.add_execution_record({"node": "test", "result": "success"})
        assert len(state.execution_history) == 1
        
        # Test to_dict
        state_dict = state.to_dict()
        assert "messages" in state_dict
        assert "values" in state_dict
        assert "metadata" in state_dict
        assert "iteration_count" in state_dict


if __name__ == "__main__":
    pytest.main([__file__])