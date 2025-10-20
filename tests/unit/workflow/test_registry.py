"""节点注册系统测试"""

import pytest
from src.workflow.registry import (
    NodeRegistry,
    BaseNode,
    NodeExecutionResult,
    register_node,
    get_node,
    get_global_registry
)
from src.prompts.agent_state import AgentState


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
        return {
            "type": "object",
            "properties": {
                "test_param": {"type": "string"}
            },
            "required": ["test_param"]
        }


class TestNodeRegistry:
    """节点注册表测试"""

    def test_register_node_class(self):
        """测试注册节点类"""
        registry = NodeRegistry()
        
        registry.register_node(MockNode)
        
        assert "mock_node" in registry.list_nodes()
        assert registry.get_node_class("mock_node") == MockNode

    def test_register_duplicate_node(self):
        """测试注册重复节点类型"""
        registry = NodeRegistry()
        
        registry.register_node(MockNode)
        
        with pytest.raises(ValueError, match="节点类型 'mock_node' 已存在"):
            registry.register_node(MockNode)

    def test_register_node_instance(self):
        """测试注册节点实例"""
        registry = NodeRegistry()
        node_instance = MockNode("custom_node")
        
        registry.register_node_instance(node_instance)
        
        assert "custom_node" in registry.list_nodes()
        assert registry.get_node_instance("custom_node") is node_instance

    def test_register_duplicate_node_instance(self):
        """测试注册重复节点实例"""
        registry = NodeRegistry()
        node_instance = MockNode("custom_node")
        
        registry.register_node_instance(node_instance)
        
        with pytest.raises(ValueError, match="节点实例 'custom_node' 已存在"):
            registry.register_node_instance(node_instance)

    def test_get_node_class_nonexistent(self):
        """测试获取不存在的节点类型"""
        registry = NodeRegistry()
        
        with pytest.raises(ValueError, match="未知的节点类型: nonexistent"):
            registry.get_node_class("nonexistent")

    def test_get_node_instance_class(self):
        """测试通过类获取节点实例"""
        registry = NodeRegistry()
        registry.register_node(MockNode)
        
        instance = registry.get_node_instance("mock_node")
        
        assert isinstance(instance, MockNode)
        assert instance.node_type == "mock_node"

    def test_get_node_instance_registered(self):
        """测试获取已注册的节点实例"""
        registry = NodeRegistry()
        node_instance = MockNode("custom_node")
        registry.register_node_instance(node_instance)
        
        instance = registry.get_node_instance("custom_node")
        
        assert instance is node_instance

    def test_get_node_schema(self):
        """测试获取节点配置Schema"""
        registry = NodeRegistry()
        registry.register_node(MockNode)
        
        schema = registry.get_node_schema("mock_node")
        
        assert schema["type"] == "object"
        assert "test_param" in schema["properties"]
        assert "test_param" in schema["required"]

    def test_validate_node_config_valid(self):
        """测试验证有效的节点配置"""
        registry = NodeRegistry()
        registry.register_node(MockNode)
        
        config = {"test_param": "value"}
        errors = registry.validate_node_config("mock_node", config)
        
        assert errors == []

    def test_validate_node_config_missing_required(self):
        """测试验证缺少必需字段的节点配置"""
        registry = NodeRegistry()
        registry.register_node(MockNode)
        
        config = {}
        errors = registry.validate_node_config("mock_node", config)
        
        assert "缺少必需字段: test_param" in errors

    def test_validate_node_config_wrong_type(self):
        """测试验证字段类型错误的节点配置"""
        registry = NodeRegistry()
        registry.register_node(MockNode)
        
        config = {"test_param": 123}  # 应该是字符串
        errors = registry.validate_node_config("mock_node", config)
        
        assert "字段 test_param 应为字符串类型" in errors

    def test_validate_node_config_nonexistent(self):
        """测试验证不存在的节点类型配置"""
        registry = NodeRegistry()
        
        errors = registry.validate_node_config("nonexistent", {})
        
        assert "未知的节点类型: nonexistent" in errors

    def test_clear_registry(self):
        """测试清除注册表"""
        registry = NodeRegistry()
        registry.register_node(MockNode)
        registry.register_node_instance(MockNode("custom"))
        
        assert len(registry.list_nodes()) == 2
        
        registry.clear()
        
        assert len(registry.list_nodes()) == 0


class TestGlobalRegistry:
    """全局注册表测试"""

    def test_get_global_registry(self):
        """测试获取全局注册表"""
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        
        assert registry1 is registry2

    def test_register_node_decorator(self):
        """测试节点注册装饰器"""
        @register_node("decorated_node")
        class DecoratedNode(BaseNode):
            @property
            def node_type(self) -> str:
                return "decorated_node"
            
            def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict:
                return {}
        
        registry = get_global_registry()
        
        assert "decorated_node" in registry.list_nodes()
        assert registry.get_node_class("decorated_node") == DecoratedNode

    def test_get_node_from_global_registry(self):
        """测试从全局注册表获取节点"""
        @register_node("global_test_node")
        class GlobalTestNode(BaseNode):
            @property
            def node_type(self) -> str:
                return "global_test_node"
            
            def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
                return NodeExecutionResult(state=state)
            
            def get_config_schema(self) -> dict:
                return {}
        
        node = get_node("global_test_node")
        
        assert isinstance(node, GlobalTestNode)
        assert node.node_type == "global_test_node"

    def test_get_node_nonexistent(self):
        """测试获取不存在的节点"""
        with pytest.raises(ValueError, match="未知的节点类型: nonexistent"):
            get_node("nonexistent")


class TestBaseNode:
    """基类节点测试"""

    def test_node_execution_result_creation(self):
        """测试节点执行结果创建"""
        state = AgentState()
        result = NodeExecutionResult(state=state)
        
        assert result.state is state
        assert result.next_node is None
        assert result.metadata == {}

    def test_node_execution_result_with_metadata(self):
        """测试带元数据的节点执行结果创建"""
        state = AgentState()
        metadata = {"test": "value"}
        result = NodeExecutionResult(
            state=state,
            next_node="next",
            metadata=metadata
        )
        
        assert result.state is state
        assert result.next_node == "next"
        assert result.metadata is metadata

    def test_base_node_validate_config_default(self):
        """测试基类节点默认配置验证"""
        node = MockNode()
        
        # 测试有效配置
        valid_config = {"test_param": "value"}
        errors = node.validate_config(valid_config)
        assert errors == []
        
        # 测试无效配置
        invalid_config = {}
        errors = node.validate_config(invalid_config)
        assert len(errors) > 0