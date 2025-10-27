"""简单边单元测试"""

import pytest
from typing import Any, Dict, Optional, Set

from src.infrastructure.graph.edges.simple_edge import SimpleEdge
from src.infrastructure.graph.config import EdgeConfig, EdgeType


class TestSimpleEdge:
    """简单边测试"""

    def test_init(self):
        """测试初始化"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node2"
        )
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.description is None

    def test_init_with_description(self):
        """测试带描述初始化"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node2",
            description="测试简单边"
        )
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.description == "测试简单边"

    def test_from_config_success(self):
        """测试从配置创建成功"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.SIMPLE,
            description="测试简单边"
        )
        
        edge = SimpleEdge.from_config(config)
        
        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.description == "测试简单边"

    def test_from_config_wrong_type(self):
        """测试从错误类型的配置创建"""
        config = EdgeConfig(
            from_node="node1",
            to_node="node2",
            type=EdgeType.CONDITIONAL
        )
        
        with pytest.raises(ValueError, match="配置类型不匹配"):
            SimpleEdge.from_config(config)

    def test_to_config(self):
        """测试转换为配置"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node2",
            description="测试简单边"
        )
        
        config = edge.to_config()
        
        assert isinstance(config, EdgeConfig)
        assert config.from_node == "node1"
        assert config.to_node == "node2"
        assert config.type == EdgeType.SIMPLE
        assert config.description == "测试简单边"

    def test_validate_success(self):
        """测试验证成功"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node2"
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert errors == []

    def test_validate_from_node_not_exists(self):
        """测试验证起始节点不存在"""
        edge = SimpleEdge(
            from_node="node3",
            to_node="node2"
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "起始节点 'node3' 不存在" in errors

    def test_validate_to_node_not_exists(self):
        """测试验证目标节点不存在"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node3"
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "目标节点 'node3' 不存在" in errors

    def test_validate_self_loop(self):
        """测试验证自循环"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node1"
        )
        
        node_names = {"node1", "node2"}
        errors = edge.validate(node_names)
        assert len(errors) == 1
        assert "不允许节点自循环" in errors

    def test_str_representation(self):
        """测试字符串表示"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node2"
        )
        
        result = str(edge)
        assert result == "SimpleEdge(node1 -> node2)"

    def test_repr_representation(self):
        """测试详细字符串表示"""
        edge = SimpleEdge(
            from_node="node1",
            to_node="node2",
            description="测试简单边"
        )
        
        result = repr(edge)
        assert "SimpleEdge" in result
        assert "from_node='node1'" in result
        assert "to_node='node2'" in result
        assert "(测试简单边)" in result