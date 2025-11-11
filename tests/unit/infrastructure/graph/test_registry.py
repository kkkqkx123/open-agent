"""图状态单元测试"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass

from src.infrastructure.graph.registry import (
    NodeExecutionResult,
    BaseNode,
    NodeRegistry,
    get_global_registry,
    register_node,
    register_node_instance,
    get_node,
    node
)
from src.infrastructure.graph.states import WorkflowState


class TestNodeExecutionResult:
    """节点执行结果测试"""

    def test_init_with_defaults(self) -> None:
        """测试使用默认值初始化"""
        state = Mock(spec=WorkflowState)
        result = NodeExecutionResult(state=state)
        assert result.state == state
        assert result.next_node is None
        assert result.metadata == {}

    def test_init_with_all_params(self) -> None:
        """测试使用所有参数初始化"""
        state = Mock(spec=WorkflowState)
        result = NodeExecutionResult(
            state=state,
            next_node="next_node",
            metadata={"key": "value"}
        )
        assert result.state == state
        assert result.next_node == "next_node"
        assert result.metadata == {"key": "value"}

    def test_post_init(self) -> None:
        """测试后初始化"""
        state = Mock(spec=WorkflowState)
        result = NodeExecutionResult(state=state, metadata={})
        assert result.metadata == {}


class TestBaseNode:
    """节点基类测试"""

    def test_abstract_methods(self) -> None:
        """测试抽象方法"""
        # 确保基类是抽象的
        with pytest.raises(TypeError):
            BaseNode()  # type: ignore

    def test_node_type_property(self) -> None:
        """测试节点类型属性"""
        # 检查属性是否为抽象的
        assert hasattr(BaseNode, 'node_type')
        assert BaseNode.node_type.__isabstractmethod__  # type: ignore

    def test_execute_method(self) -> None:
        """测试执行方法"""
        # 检查方法是否为抽象的
        assert hasattr(BaseNode, 'execute')
        assert BaseNode.execute.__isabstractmethod__  # type: ignore

    def test_get_config_schema_method(self) -> None:
        """测试获取配置模式方法"""
        # 检查方法是否为抽象的
        assert hasattr(BaseNode, 'get_config_schema')
        assert BaseNode.get_config_schema.__isabstractmethod__  # type: ignore

    def test_validate_config_default(self) -> None:
        """测试默认配置验证"""
        # 创建模拟子类
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "mock_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {
                    "required": ["required_field"],
                    "properties": {
                        "required_field": {"type": "string"},
                        "optional_field": {"type": "integer"}
                    }
                }
        
        node = MockNode()
        
        # 测试缺少必需字段
        errors = node.validate_config({})
        assert len(errors) == 1
        assert "缺少必需字段: required_field" in errors
        
        # 测试字段类型错误
        errors = node.validate_config({"required_field": 123, "optional_field": "string"})
        assert len(errors) == 2
        assert "字段 required_field 应为字符串类型" in errors
        assert "字段 optional_field 应为整数类型" in errors
        
        # 测试正确配置
        errors = node.validate_config({"required_field": "test", "optional_field": 42})
        assert errors == []


class TestNodeRegistry:
    """节点注册表测试"""

    @pytest.fixture
    def registry(self) -> NodeRegistry:
        """创建节点注册表实例"""
        return NodeRegistry()

    def test_init(self, registry: NodeRegistry) -> None:
        """测试初始化"""
        assert registry._nodes == {}
        assert registry._node_instances == {}

    def test_register_node_success(self, registry: NodeRegistry) -> None:
        """测试成功注册节点类型"""
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "mock_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 注册节点
        registry.register_node(MockNode)
        
        # 验证
        assert "mock_node" in registry._nodes
        assert registry._nodes["mock_node"] == MockNode

    def test_register_node_none(self, registry: NodeRegistry) -> None:
        """测试注册None节点"""
        with pytest.raises(ValueError, match="节点类不能为None"):
            registry.register_node(None)  # type: ignore

    def test_register_node_missing_node_type(self, registry: NodeRegistry) -> None:
        """测试注册缺少node_type属性的节点"""
        # 创建缺少node_type属性的节点类
        class InvalidNode(BaseNode):
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        with pytest.raises(ValueError, match="获取节点类型失败"):
            registry.register_node(InvalidNode)  # type: ignore

    def test_register_node_duplicate(self, registry: NodeRegistry) -> None:
        """测试注册重复节点类型"""
        # 创建模拟节点类
        class MockNode1(BaseNode):
            @property
            def node_type(self):
                return "duplicate_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        class MockNode2(BaseNode):
            @property
            def node_type(self):
                return "duplicate_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 注册第一个节点
        registry.register_node(MockNode1)
        
        # 尝试注册重复节点
        with pytest.raises(ValueError, match="节点类型 'duplicate_node' 已存在"):
            registry.register_node(MockNode2)

    def test_register_node_instance_success(self, registry: NodeRegistry) -> None:
        """测试成功注册节点实例"""
        # 创建模拟节点实例
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "mock_instance_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        node_instance = MockNode()
        
        # 注册节点实例
        registry.register_node_instance(node_instance)
        
        # 验证
        assert "mock_instance_node" in registry._node_instances
        assert registry._node_instances["mock_instance_node"] == node_instance

    def test_register_node_instance_none(self, registry: NodeRegistry) -> None:
        """测试注册None节点实例"""
        with pytest.raises(ValueError, match="节点实例不能为None"):
            registry.register_node_instance(None)  # type: ignore

    def test_register_node_instance_missing_node_type(self, registry: NodeRegistry) -> None:
        """测试注册缺少node_type属性的节点实例"""
        # 创建缺少node_type属性的节点实例
        class InvalidNode(BaseNode):
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 使用Mock来创建一个可以实例化的节点实例
        node_instance = Mock(spec=BaseNode)
        # 移除node_type属性来模拟缺少node_type的情况
        delattr(node_instance, 'node_type')
        
        with pytest.raises(ValueError, match="节点实例缺少 node_type 属性"):
            registry.register_node_instance(node_instance)

    def test_register_node_instance_duplicate(self, registry: NodeRegistry) -> None:
        """测试注册重复节点实例"""
        # 创建模拟节点实例
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "duplicate_instance_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        node_instance1 = MockNode()
        node_instance2 = MockNode()
        
        # 注册第一个节点实例
        registry.register_node_instance(node_instance1)
        
        # 尝试注册重复节点实例
        with pytest.raises(ValueError, match="节点实例 'duplicate_instance_node' 已存在"):
            registry.register_node_instance(node_instance2)

    def test_get_node_class_success(self, registry: NodeRegistry) -> None:
        """测试成功获取节点类型"""
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "existing_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 注册节点
        registry.register_node(MockNode)
        
        # 获取节点类
        node_class = registry.get_node_class("existing_node")
        
        # 验证
        assert node_class == MockNode

    def test_get_node_class_not_found(self, registry: NodeRegistry) -> None:
        """测试获取不存在的节点类型"""
        with pytest.raises(ValueError, match="未知的节点类型: nonexistent_node"):
            registry.get_node_class("nonexistent_node")

    def test_get_node_instance_registered_instance(self, registry: NodeRegistry) -> None:
        """测试获取已注册的节点实例"""
        # 创建模拟节点实例
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "registered_instance_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        node_instance = MockNode()
        
        # 注册节点实例
        registry.register_node_instance(node_instance)
        
        # 获取节点实例
        result = registry.get_node_instance("registered_instance_node")
        
        # 验证
        assert result == node_instance

    def test_get_node_instance_new_instance(self, registry: NodeRegistry) -> None:
        """测试获取新创建的节点实例"""
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "new_instance_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 注册节点类
        registry.register_node(MockNode)
        
        # 获取节点实例（应该创建新实例）
        result = registry.get_node_instance("new_instance_node")
        
        # 验证
        assert isinstance(result, MockNode)

    def test_get_node_instance_not_found(self, registry: NodeRegistry) -> None:
        """测试获取不存在的节点实例"""
        with pytest.raises(ValueError, match="未知的节点类型: nonexistent_node"):
            registry.get_node_instance("nonexistent_node")

    def test_list_nodes(self, registry: NodeRegistry) -> None:
        """测试列出所有注册的节点类型"""
        # 创建模拟节点类和实例
        class MockNode1(BaseNode):
            @property
            def node_type(self):
                return "node1"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        class MockNode2(BaseNode):
            @property
            def node_type(self):
                return "node2"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        class MockNode3(BaseNode):
            @property
            def node_type(self):
                return "node3"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        node_instance = MockNode3()
        
        # 注册节点类和实例
        registry.register_node(MockNode1)
        registry.register_node(MockNode2)
        registry.register_node_instance(node_instance)
        
        # 列出节点
        nodes = registry.list_nodes()
        
        # 验证
        assert len(nodes) == 3
        assert "node1" in nodes
        assert "node2" in nodes
        assert "node3" in nodes

    def test_get_node_schema_success(self, registry: NodeRegistry) -> None:
        """测试成功获取节点配置模式"""
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "schema_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {"type": "object", "properties": {"test": {"type": "string"}}}

        # 注册节点
        registry.register_node(MockNode)
        
        # 获取配置模式
        schema = registry.get_node_schema("schema_node")
        
        # 验证
        assert schema == {"type": "object", "properties": {"test": {"type": "string"}}}

    def test_get_node_schema_not_found(self, registry: NodeRegistry) -> None:
        """测试获取不存在节点的配置模式"""
        with pytest.raises(ValueError):
            registry.get_node_schema("nonexistent_node")

    def test_validate_node_config_success(self, registry: NodeRegistry) -> None:
        """测试成功验证节点配置"""
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "validation_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {
                    "required": ["required_field"],
                    "properties": {
                        "required_field": {"type": "string"}
                    }
                }

        # 注册节点
        registry.register_node(MockNode)
        
        # 验证配置
        errors = registry.validate_node_config("validation_node", {"required_field": "test"})
        
        # 验证
        assert errors == []

    def test_validate_node_config_not_found(self, registry: NodeRegistry) -> None:
        """测试验证不存在节点的配置"""
        errors = registry.validate_node_config("nonexistent_node", {})
        assert len(errors) == 1

    def test_clear(self, registry: NodeRegistry) -> None:
        """测试清除所有注册的节点"""
        # 创建模拟节点类和实例
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "clear_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        node_instance = MockNode()
        
        # 注册节点类和实例
        registry.register_node(MockNode)
        registry.register_node_instance(node_instance)
        
        # 验证注册
        assert len(registry._nodes) == 1
        assert len(registry._node_instances) == 1
        
        # 清除
        registry.clear()
        
        # 验证清除
        assert registry._nodes == {}
        assert registry._node_instances == {}


class TestGlobalRegistryFunctions:
    """全局注册表函数测试"""

    def test_get_global_registry(self) -> None:
        """测试获取全局注册表"""
        # 重置全局注册表
        import src.infrastructure.graph.registry
        src.infrastructure.graph.registry._global_registry = None
        
        # 获取全局注册表
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        
        # 验证
        assert isinstance(registry1, NodeRegistry)
        assert registry1 is registry2  # 应该是单例

    def test_register_node_global(self) -> None:
        """测试全局注册节点"""
        # 重置全局注册表
        import src.infrastructure.graph.registry
        src.infrastructure.graph.registry._global_registry = None
        
        # 创建模拟节点类
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "global_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 全局注册节点
        register_node(MockNode)
        
        # 验证
        registry = get_global_registry()
        assert "global_node" in registry._nodes

    def test_register_node_instance_global(self) -> None:
        """测试全局注册节点实例"""
        # 重置全局注册表
        import src.infrastructure.graph.registry
        src.infrastructure.graph.registry._global_registry = None
        
        # 创建模拟节点实例
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "global_instance_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        node_instance = MockNode()
        
        # 全局注册节点实例
        register_node_instance(node_instance)
        
        # 验证
        registry = get_global_registry()
        assert "global_instance_node" in registry._node_instances

    def test_get_node_global(self) -> None:
        """测试全局获取节点"""
        # 重置全局注册表
        import src.infrastructure.graph.registry
        src.infrastructure.graph.registry._global_registry = None
        
        # 创建模拟节点实例
        class MockNode(BaseNode):
            @property
            def node_type(self):
                return "get_global_node"
            
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        node_instance = MockNode()
        
        # 全局注册节点实例
        register_node_instance(node_instance)
        
        # 全局获取节点
        result = get_node("get_global_node")
        
        # 验证
        assert result == node_instance


class TestNodeDecorator:
    """节点装饰器测试"""

    def test_node_decorator(self) -> None:
        """测试节点装饰器"""
        # 使用装饰器
        @node("decorated_node")
        class OriginalNode(BaseNode):
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 验证装饰后的类
        assert hasattr(OriginalNode, 'node_type')
        assert OriginalNode().node_type == "decorated_node"  # type: ignore
        
        # 验证方法仍然存在
        assert hasattr(OriginalNode, 'execute')
        assert hasattr(OriginalNode, 'get_config_schema')

    def test_node_decorator_registers_node(self) -> None:
        """测试节点装饰器自动注册节点"""
        # 重置全局注册表
        import src.infrastructure.graph.registry
        src.infrastructure.graph.registry._global_registry = None
        
        # 使用装饰器
        @node("auto_registered_node")
        class AutoRegisteredNode(BaseNode):
            def execute(self, state: WorkflowState, config: dict[str, Any]) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict[str, Any]:
                return {}

        # 验证节点已注册到全局注册表
        registry = get_global_registry()
        assert "auto_registered_node" in registry._nodes
        assert registry._nodes["auto_registered_node"] == AutoRegisteredNode
