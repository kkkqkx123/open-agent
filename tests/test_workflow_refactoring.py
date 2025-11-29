"""测试工作流重构后的组件

验证新的协调器和重构后的WorkflowInstance是否正常工作。
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# 导入重构后的组件
from src.core.workflow.orchestration.workflow_instance_coordinator import WorkflowInstanceCoordinator
from src.core.workflow.orchestration.workflow_registry_coordinator import WorkflowRegistryCoordinator
from src.core.workflow.workflow_instance_refactored import WorkflowInstance

# 导入测试用的模拟组件
from src.core.workflow.workflow_instance import Workflow


class MockWorkflow:
    """模拟工作流类"""
    
    def __init__(self, workflow_id: str, name: str):
        self.workflow_id = workflow_id
        self.name = name
        self.config = Mock()
        self.config.name = name
        self.config.nodes = {}
        self.config.edges = []
        self.config.entry_point = "__start__"
    
    def validate(self) -> list:
        return []


class MockWorkflowState:
    """模拟工作流状态"""
    
    def __init__(self, workflow_id: str, values: Dict[str, Any] = None):
        self.workflow_id = workflow_id
        self.values = values or {}


class TestWorkflowInstanceCoordinator:
    """测试工作流实例协调器"""
    
    def test_init(self):
        """测试初始化"""
        workflow = MockWorkflow("test_wf", "Test Workflow")
        coordinator = WorkflowInstanceCoordinator(workflow)
        
        assert coordinator.workflow == workflow
        assert coordinator.executor is not None
        assert coordinator.execution_manager is not None
        assert coordinator.validator is not None
        assert coordinator.next_nodes_resolver is not None
        assert len(coordinator._active_executions) == 0
    
    def test_validate_workflow(self):
        """测试工作流验证"""
        workflow = MockWorkflow("test_wf", "Test Workflow")
        coordinator = WorkflowInstanceCoordinator(workflow)
        
        # 测试基本验证
        errors = coordinator.validate_workflow()
        assert isinstance(errors, list)
    
    def test_get_coordinator_stats(self):
        """测试获取协调器统计信息"""
        workflow = MockWorkflow("test_wf", "Test Workflow")
        coordinator = WorkflowInstanceCoordinator(workflow)
        
        stats = coordinator.get_coordinator_stats()
        assert stats["workflow_id"] == "test_wf"
        assert stats["workflow_name"] == "Test Workflow"
        assert stats["active_executions"] == 0
        assert stats["total_executions"] == 0
        assert isinstance(stats["execution_ids"], list)


class TestWorkflowRegistryCoordinator:
    """测试工作流注册表协调器"""
    
    def test_init(self):
        """测试初始化"""
        coordinator = WorkflowRegistryCoordinator()
        
        assert coordinator._registry is not None
        assert len(coordinator._coordinators) == 0
    
    def test_register_workflow(self):
        """测试注册工作流"""
        coordinator = WorkflowRegistryCoordinator()
        workflow = MockWorkflow("test_wf", "Test Workflow")
        
        coordinator.register_workflow("test_wf", workflow)
        
        assert coordinator.get_workflow("test_wf") == workflow
        assert "test_wf" in coordinator._coordinators
        assert isinstance(coordinator._coordinators["test_wf"], WorkflowInstanceCoordinator)
    
    def test_create_workflow_coordinator(self):
        """测试创建工作流协调器"""
        coordinator = WorkflowRegistryCoordinator()
        workflow = MockWorkflow("test_wf", "Test Workflow")
        
        # 先注册工作流
        coordinator.register_workflow("test_wf", workflow)
        
        # 创建协调器
        instance_coordinator = coordinator.create_workflow_coordinator("test_wf")
        
        assert isinstance(instance_coordinator, WorkflowInstanceCoordinator)
        assert instance_coordinator.workflow == workflow
    
    def test_list_workflows(self):
        """测试列出工作流"""
        coordinator = WorkflowRegistryCoordinator()
        workflow1 = MockWorkflow("test_wf1", "Test Workflow 1")
        workflow2 = MockWorkflow("test_wf2", "Test Workflow 2")
        
        coordinator.register_workflow("test_wf1", workflow1)
        coordinator.register_workflow("test_wf2", workflow2)
        
        workflows = coordinator.list_workflows()
        assert len(workflows) == 2
        assert workflows[0]["workflow_id"] in ["test_wf1", "test_wf2"]
        assert workflows[1]["workflow_id"] in ["test_wf1", "test_wf2"]
    
    def test_delete_workflow(self):
        """测试删除工作流"""
        coordinator = WorkflowRegistryCoordinator()
        workflow = MockWorkflow("test_wf", "Test Workflow")
        
        coordinator.register_workflow("test_wf", workflow)
        assert coordinator.get_workflow("test_wf") is not None
        
        result = coordinator.delete_workflow("test_wf")
        assert result is True
        assert coordinator.get_workflow("test_wf") is None
        assert "test_wf" not in coordinator._coordinators
    
    def test_get_registry_stats(self):
        """测试获取注册表统计信息"""
        coordinator = WorkflowRegistryCoordinator()
        workflow1 = MockWorkflow("test_wf1", "Test Workflow 1")
        workflow2 = MockWorkflow("test_wf2", "Test Workflow 2")
        
        coordinator.register_workflow("test_wf1", workflow1)
        coordinator.register_workflow("test_wf2", workflow2)
        
        stats = coordinator.get_registry_stats()
        assert stats["registered_workflows"] == 2
        assert stats["active_coordinators"] == 2
        assert stats["total_active_executions"] == 0
        assert stats["total_executions"] == 0
        assert "test_wf1" in stats["workflow_ids"]
        assert "test_wf2" in stats["workflow_ids"]


class TestWorkflowInstanceRefactored:
    """测试重构后的工作流实例"""
    
    def test_init_with_coordinators(self):
        """测试使用协调器初始化"""
        # 创建模拟配置
        mock_config = Mock()
        mock_config.name = "test_wf"
        mock_config.description = "Test Workflow"
        mock_config.nodes = {}
        mock_config.edges = []
        mock_config.entry_point = "__start__"
        
        # 创建模拟编译图
        mock_graph = Mock()
        mock_graph.invoke = Mock(return_value={"result": "success"})
        
        # 创建工作流实例
        workflow = WorkflowInstance(
            config=mock_config,
            compiled_graph=mock_graph,
            use_coordinators=True
        )
        
        assert workflow.config == mock_config
        assert workflow.compiled_graph == mock_graph
        assert workflow.use_coordinators is True
        assert workflow.workflow_id == "test_wf"
        assert workflow.name == "test_wf"
    
    def test_init_without_coordinators(self):
        """测试不使用协调器初始化"""
        # 创建模拟配置
        mock_config = Mock()
        mock_config.name = "test_wf"
        mock_config.description = "Test Workflow"
        mock_config.nodes = {}
        mock_config.edges = []
        mock_config.entry_point = "__start__"
        
        # 创建模拟编译图
        mock_graph = Mock()
        mock_graph.invoke = Mock(return_value={"result": "success"})
        
        # 创建工作流实例
        workflow = WorkflowInstance(
            config=mock_config,
            compiled_graph=mock_graph,
            use_coordinators=False
        )
        
        assert workflow.config == mock_config
        assert workflow.compiled_graph == mock_graph
        assert workflow.use_coordinators is False
        assert workflow.workflow_id == "test_wf"
    
    def test_get_visualization(self):
        """测试获取可视化数据"""
        # 创建模拟配置
        mock_config = Mock()
        mock_config.name = "test_wf"
        mock_config.description = "Test Workflow"
        mock_config.nodes = {"node1": Mock()}
        mock_config.edges = []
        mock_config.entry_point = "__start__"
        
        # 创建模拟编译图
        mock_graph = Mock()
        mock_graph.invoke = Mock(return_value={"result": "success"})
        mock_graph.ainvoke = Mock(return_value={"result": "success"})
        mock_graph.stream = Mock(return_value=[{"step": "1"}])
        mock_graph.astream = Mock(return_value=[{"step": "1"}])
        
        # 创建工作流实例
        workflow = WorkflowInstance(
            config=mock_config,
            compiled_graph=mock_graph,
            use_coordinators=True
        )
        
        visualization = workflow.get_visualization()
        
        assert visualization["name"] == "test_wf"
        assert visualization["description"] == "Test Workflow"
        assert visualization["use_coordinators"] is True
        assert "metadata" in visualization
        assert visualization["metadata"]["supports_async"] is True
        assert visualization["metadata"]["supports_stream"] is True
        assert visualization["metadata"]["supports_async_stream"] is True
    
    def test_get_metadata(self):
        """测试获取元数据"""
        # 创建模拟配置
        mock_config = Mock()
        mock_config.name = "test_wf"
        mock_config.description = "Test Workflow"
        mock_config.nodes = {"node1": Mock()}
        mock_config.edges = []
        mock_config.entry_point = "__start__"
        
        # 创建模拟编译图
        mock_graph = Mock()
        mock_graph.invoke = Mock(return_value={"result": "success"})
        mock_graph.ainvoke = Mock(return_value={"result": "success"})
        mock_graph.stream = Mock(return_value=[{"step": "1"}])
        mock_graph.astream = Mock(return_value=[{"step": "1"}])
        
        # 创建工作流实例
        workflow = WorkflowInstance(
            config=mock_config,
            compiled_graph=mock_graph,
            use_coordinators=True
        )
        
        metadata = workflow.get_metadata()
        
        assert metadata["name"] == "test_wf"
        assert metadata["description"] == "Test Workflow"
        assert metadata["capabilities"]["use_coordinators"] is True
        assert metadata["config"]["node_count"] == 1
        assert metadata["config"]["edge_count"] == 0
    
    def test_validate(self):
        """测试验证"""
        # 创建模拟配置
        mock_config = Mock()
        mock_config.name = "test_wf"
        mock_config.description = "Test Workflow"
        mock_config.nodes = {"node1": Mock()}
        mock_config.edges = []
        mock_config.entry_point = "__start__"
        
        # 创建模拟编译图
        mock_graph = Mock()
        mock_graph.invoke = Mock(return_value={"result": "success"})
        
        # 创建工作流实例
        workflow = WorkflowInstance(
            config=mock_config,
            compiled_graph=mock_graph,
            use_coordinators=True
        )
        
        errors = workflow.validate()
        assert isinstance(errors, list)
    
    def test_repr(self):
        """测试字符串表示"""
        # 创建模拟配置
        mock_config = Mock()
        mock_config.name = "test_wf"
        mock_config.description = "Test Workflow"
        mock_config.nodes = {"node1": Mock()}
        mock_config.edges = []
        mock_config.entry_point = "__start__"
        
        # 创建模拟编译图
        mock_graph = Mock()
        mock_graph.invoke = Mock(return_value={"result": "success"})
        
        # 创建工作流实例
        workflow = WorkflowInstance(
            config=mock_config,
            compiled_graph=mock_graph,
            use_coordinators=True
        )
        
        repr_str = repr(workflow)
        assert "WorkflowInstanceRefactored" in repr_str
        assert "test_wf" in repr_str
        assert "use_coordinators=True" in repr_str


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])