"""工作流管理器测试"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import yaml

from src.application.workflow.manager import WorkflowManager, IWorkflowManager
from src.domain.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from src.application.workflow.registry import NodeRegistry, BaseNode, NodeExecutionResult
from src.domain.prompts.agent_state import AgentState


class MockNode(BaseNode):
    """模拟节点类"""
    
    def __init__(self, node_type: str = "mock_node"):
        self._node_type = node_type
    
    @property
    def node_type(self) -> str:
        return self._node_type
    
    def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
        return NodeExecutionResult(state=state)
    
    def get_config_schema(self) -> dict:
        return {"type": "object", "properties": {}}


class TestWorkflowManager:
    """工作流管理器测试"""

    def test_init_with_default_components(self):
        """测试使用默认组件初始化"""
        manager = WorkflowManager()
        
        assert manager.node_registry is not None
        assert manager.workflow_builder is not None
        assert manager.config_loader is None
        assert manager._workflows == {}
        assert manager._workflow_configs == {}
        assert manager._workflow_metadata == {}

    def test_init_with_custom_components(self):
        """测试使用自定义组件初始化"""
        config_loader = Mock()
        node_registry = NodeRegistry()
        workflow_builder = Mock()
        
        manager = WorkflowManager(
            config_loader=config_loader,
            node_registry=node_registry,
            workflow_builder=workflow_builder
        )
        
        assert manager.config_loader is config_loader
        assert manager.node_registry is node_registry
        assert manager.workflow_builder is workflow_builder

    def test_load_workflow_success(self):
        """测试成功加载工作流"""
        # 创建临时配置文件
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "nodes": {
                "analyze": {
                    "type": "mock_node"
                }
            },
            "edges": [
                {
                    "from": "start",
                    "to": "analyze",
                    "type": "simple"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 模拟工作流构建器
            mock_workflow = Mock()
            mock_workflow_builder = Mock()
            mock_workflow_builder.load_workflow_config.return_value = WorkflowConfig.from_dict(config_data)
            mock_workflow_builder.build_workflow.return_value = mock_workflow
            
            # 创建管理器
            node_registry = NodeRegistry()
            node_registry.register_node(MockNode)
            
            manager = WorkflowManager(
                node_registry=node_registry,
                workflow_builder=mock_workflow_builder
            )
            
            # 加载工作流
            workflow_id = manager.load_workflow(temp_path)
            
            # 验证结果
            assert workflow_id is not None
            assert workflow_id in manager._workflows
            assert workflow_id in manager._workflow_configs
            assert workflow_id in manager._workflow_metadata
            
            # 验证元数据
            metadata = manager._workflow_metadata[workflow_id]
            assert metadata["name"] == "test_workflow"
            assert metadata["description"] == "测试工作流"
            assert "loaded_at" in metadata
            assert metadata["usage_count"] == 0
            
        finally:
            Path(temp_path).unlink()

    def test_load_workflow_file_not_found(self):
        """测试加载不存在的工作流文件"""
        manager = WorkflowManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load_workflow("nonexistent.yaml")

    def test_create_workflow_success(self):
        """测试成功创建工作流实例"""
        manager = WorkflowManager()
        
        # 添加模拟工作流
        workflow_id = "test_workflow_id"
        mock_workflow = Mock()
        manager._workflows[workflow_id] = mock_workflow
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        manager._workflow_metadata[workflow_id] = {
            "usage_count": 0
        }
        
        # 创建工作流实例
        result = manager.create_workflow(workflow_id)
        
        assert result is mock_workflow
        
        # 验证使用统计更新
        assert manager._workflow_metadata[workflow_id]["usage_count"] == 1
        assert "last_used" in manager._workflow_metadata[workflow_id]

    def test_create_workflow_not_found(self):
        """测试创建不存在的工作流实例"""
        manager = WorkflowManager()
        
        with pytest.raises(ValueError, match="工作流 'nonexistent' 不存在"):
            manager.create_workflow("nonexistent")

    @patch('src.workflow.manager.WorkflowManager.create_workflow')
    def test_run_workflow_success(self, mock_create_workflow):
        """测试成功运行工作流"""
        # 模拟工作流
        mock_workflow = Mock()
        mock_workflow.invoke.return_value = AgentState()
        mock_create_workflow.return_value = mock_workflow
        
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流",
            additional_config={"max_iterations": 5}
        )
        
        # 运行工作流
        initial_state = AgentState()
        result = manager.run_workflow(workflow_id, initial_state)
        
        # 验证结果
        assert isinstance(result, AgentState)
        mock_create_workflow.assert_called_once_with(workflow_id)
        mock_workflow.invoke.assert_called_once()

    @patch('src.workflow.manager.WorkflowManager.create_workflow')
    def test_run_workflow_without_initial_state(self, mock_create_workflow):
        """测试不提供初始状态运行工作流"""
        # 模拟工作流
        mock_workflow = Mock()
        mock_workflow.invoke.return_value = AgentState()
        mock_create_workflow.return_value = mock_workflow
        
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        # 运行工作流（不提供初始状态）
        result = manager.run_workflow(workflow_id)
        
        # 验证结果
        assert isinstance(result, AgentState)
        mock_workflow.invoke.assert_called_once()
        
        # 验证传递给invoke的参数是AgentState实例
        call_args = mock_workflow.invoke.call_args[0]
        assert isinstance(call_args[0], AgentState)

    @patch('src.workflow.manager.WorkflowManager.create_workflow')
    def test_run_workflow_error(self, mock_create_workflow):
        """测试运行工作流时发生错误"""
        # 模拟工作流抛出异常
        mock_workflow = Mock()
        mock_workflow.invoke.side_effect = Exception("测试错误")
        mock_create_workflow.return_value = mock_workflow
        
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        # 添加工作流元数据（这是修复的关键）
        manager._workflow_metadata[workflow_id] = {
            "name": "test_workflow",
            "description": "测试工作流",
            "usage_count": 0
        }
        
        # 运行工作流应该抛出异常
        with pytest.raises(Exception, match="测试错误"):
            manager.run_workflow(workflow_id)
        
        # 验证错误被记录
        metadata = manager._workflow_metadata[workflow_id]
        assert "errors" in metadata
        assert len(metadata["errors"]) == 1
        assert metadata["errors"][0]["error_message"] == "测试错误"

    @pytest.mark.asyncio
    @patch('src.workflow.manager.WorkflowManager.create_workflow')
    async def test_run_workflow_async_success(self, mock_create_workflow):
        """测试异步成功运行工作流"""
        # 模拟异步工作流
        mock_workflow = AsyncMock()
        mock_workflow.ainvoke.return_value = AgentState()
        mock_create_workflow.return_value = mock_workflow
        
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        # 异步运行工作流
        result = await manager.run_workflow_async(workflow_id)
        
        # 验证结果
        assert isinstance(result, AgentState)
        mock_create_workflow.assert_called_once_with(workflow_id)
        mock_workflow.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.workflow.manager.WorkflowManager.create_workflow')
    async def test_run_workflow_async_fallback_to_sync(self, mock_create_workflow):
        """测试异步运行工作流时回退到同步方式"""
        # 模拟不支持异步的工作流
        mock_workflow = Mock()
        mock_workflow.invoke.return_value = AgentState()
        # 模拟没有ainvoke方法
        del mock_workflow.ainvoke
        mock_create_workflow.return_value = mock_workflow
        
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        # 异步运行工作流
        result = await manager.run_workflow_async(workflow_id)
        
        # 验证结果
        assert isinstance(result, AgentState)
        mock_workflow.invoke.assert_called_once()

    @patch('src.workflow.manager.WorkflowManager.create_workflow')
    def test_stream_workflow_success(self, mock_create_workflow):
        """测试成功流式运行工作流"""
        # 模拟支持流式的工作流
        mock_workflow = Mock()
        mock_workflow.stream.return_value = [AgentState(), AgentState()]
        mock_create_workflow.return_value = mock_workflow
        
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        # 流式运行工作流
        results = list(manager.stream_workflow(workflow_id))
        
        # 验证结果
        assert len(results) == 2
        assert all(isinstance(r, AgentState) for r in results)
        mock_workflow.stream.assert_called_once()

    @patch('src.workflow.manager.WorkflowManager.create_workflow')
    def test_stream_workflow_fallback_to_invoke(self, mock_create_workflow):
        """测试流式运行工作流时回退到invoke方式"""
        # 模拟不支持流式的工作流
        mock_workflow = Mock()
        mock_workflow.invoke.return_value = AgentState()
        # 模拟没有stream方法
        del mock_workflow.stream
        mock_create_workflow.return_value = mock_workflow
        
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        
        # 流式运行工作流
        results = list(manager.stream_workflow(workflow_id))
        
        # 验证结果
        assert len(results) == 1
        assert isinstance(results[0], AgentState)
        mock_workflow.invoke.assert_called_once()

    def test_list_workflows(self):
        """测试列出工作流"""
        manager = WorkflowManager()
        
        # 添加工作流
        manager._workflows["workflow1"] = Mock()
        manager._workflows["workflow2"] = Mock()
        
        workflows = manager.list_workflows()
        
        assert len(workflows) == 2
        assert "workflow1" in workflows
        assert "workflow2" in workflows

    def test_get_workflow_config(self):
        """测试获取工作流配置"""
        manager = WorkflowManager()
        
        # 添加工作流配置
        workflow_id = "test_workflow_id"
        config = WorkflowConfig(name="test_workflow", description="测试工作流")
        manager._workflow_configs[workflow_id] = config
        
        # 获取配置
        result = manager.get_workflow_config(workflow_id)
        
        assert result is config

    def test_get_workflow_config_not_found(self):
        """测试获取不存在的工作流配置"""
        manager = WorkflowManager()
        
        result = manager.get_workflow_config("nonexistent")
        
        assert result is None

    def test_unload_workflow_success(self):
        """测试成功卸载工作流"""
        manager = WorkflowManager()
        
        # 添加工作流
        workflow_id = "test_workflow_id"
        manager._workflows[workflow_id] = Mock()
        manager._workflow_configs[workflow_id] = Mock()
        manager._workflow_metadata[workflow_id] = Mock()
        
        # 卸载工作流
        result = manager.unload_workflow(workflow_id)
        
        assert result is True
        assert workflow_id not in manager._workflows
        assert workflow_id not in manager._workflow_configs
        assert workflow_id not in manager._workflow_metadata

    def test_unload_workflow_not_found(self):
        """测试卸载不存在的工作流"""
        manager = WorkflowManager()
        
        result = manager.unload_workflow("nonexistent")
        
        assert result is False

    def test_get_workflow_metadata(self):
        """测试获取工作流元数据"""
        manager = WorkflowManager()
        
        # 添加工作流元数据
        workflow_id = "test_workflow_id"
        metadata = {"name": "test_workflow"}
        manager._workflow_metadata[workflow_id] = metadata
        
        # 获取元数据
        result = manager.get_workflow_metadata(workflow_id)
        
        assert result is metadata

    def test_get_workflow_metadata_not_found(self):
        """测试获取不存在的工作流元数据"""
        manager = WorkflowManager()
        
        result = manager.get_workflow_metadata("nonexistent")
        
        assert result is None

    def test_reload_workflow_success(self):
        """测试成功重新加载工作流"""
        # 创建临时配置文件
        config_data = {
            "name": "test_workflow",
            "description": "测试工作流",
            "version": "2.0"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # 模拟工作流构建器
            mock_workflow = Mock()
            mock_workflow_builder = Mock()
            mock_workflow_builder.load_workflow_config.return_value = WorkflowConfig.from_dict(config_data)
            mock_workflow_builder.build_workflow.return_value = mock_workflow
            
            manager = WorkflowManager(workflow_builder=mock_workflow_builder)
            
            # 添加工作流
            workflow_id = "test_workflow_id"
            manager._workflows[workflow_id] = Mock()
            manager._workflow_configs[workflow_id] = WorkflowConfig(
                name="test_workflow",
                description="测试工作流",
                version="1.0"
            )
            manager._workflow_metadata[workflow_id] = {
                "config_path": temp_path,
                "version": "1.0"
            }
            
            # 重新加载工作流
            result = manager.reload_workflow(workflow_id)
            
            assert result is True
            assert manager._workflow_configs[workflow_id].version == "2.0"
            assert manager._workflow_metadata[workflow_id]["version"] == "2.0"
            
        finally:
            Path(temp_path).unlink()

    def test_reload_workflow_not_found(self):
        """测试重新加载不存在的工作流"""
        manager = WorkflowManager()
        
        result = manager.reload_workflow("nonexistent")
        
        assert result is False

    def test_reload_workflow_no_config_path(self):
        """测试重新加载没有配置路径的工作流"""
        manager = WorkflowManager()
        
        # 添加工作流（没有配置路径）
        workflow_id = "test_workflow_id"
        manager._workflow_configs[workflow_id] = WorkflowConfig(
            name="test_workflow",
            description="测试工作流"
        )
        manager._workflow_metadata[workflow_id] = {}
        
        result = manager.reload_workflow(workflow_id)
        
        assert result is False

    def test_generate_workflow_id(self):
        """测试生成工作流ID"""
        manager = WorkflowManager()
        
        workflow_id = manager._generate_workflow_id("test_workflow")
        
        assert workflow_id.startswith("test_workflow_")
        assert len(workflow_id) > len("test_workflow_")

    def test_log_workflow_error(self):
        """测试记录工作流错误"""
        manager = WorkflowManager()
        
        # 添加工作流元数据
        workflow_id = "test_workflow_id"
        manager._workflow_metadata[workflow_id] = {}
        
        # 记录错误
        error = Exception("测试错误")
        manager._log_workflow_error(workflow_id, error)
        
        # 验证错误被记录
        metadata = manager._workflow_metadata[workflow_id]
        assert "errors" in metadata
        assert len(metadata["errors"]) == 1
        assert metadata["errors"][0]["error_type"] == "Exception"
        assert metadata["errors"][0]["error_message"] == "测试错误"
