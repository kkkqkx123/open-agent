"""静态依赖分析工具单元测试"""

import pytest
from typing import Type, Optional, Dict, Any

from src.adapters.cli.dependency_analyzer_tool import (
    StaticDependencyAnalyzer,
    DependencyAnalysisResult,
    CircularDependency
)


# 测试用例的模型类

class ServiceA:
    """无依赖的服务"""
    pass


class ServiceB:
    """依赖 ServiceA"""
    def __init__(self, a: ServiceA):
        self.a = a


class ServiceC:
    """依赖 ServiceB"""
    def __init__(self, b: ServiceB):
        self.b = b


class ServiceCircular1:
    """循环依赖：Circular1 -> Circular2 -> Circular1"""
    def __init__(self, c2: Optional['ServiceCircular2'] = None):
        self.c2 = c2


class ServiceCircular2:
    """循环依赖：Circular2 -> Circular1 -> Circular2"""
    def __init__(self, c1: Optional[ServiceCircular1] = None):
        self.c1 = c1


class TestBuildDependencyGraph:
    """测试构建依赖图"""
    
    def test_simple_dependency_chain(self):
        """测试简单的依赖链"""
        services = {
            ServiceA: ServiceA,
            ServiceB: ServiceB,
            ServiceC: ServiceC,
        }
        
        graph = StaticDependencyAnalyzer.build_dependency_graph(services)
        
        assert ServiceA in graph
        assert ServiceB in graph
        assert ServiceC in graph
        
        # ServiceA 无依赖
        assert len(graph[ServiceA]) == 0
        
        # ServiceB 依赖 ServiceA
        assert ServiceA in graph[ServiceB]
        
        # ServiceC 依赖 ServiceB
        assert ServiceB in graph[ServiceC]
    
    def test_none_implementation(self):
        """测试实现为None的情况"""
        services = {
            ServiceA: None,
            ServiceB: ServiceB,
        }
        
        graph = StaticDependencyAnalyzer.build_dependency_graph(services)
        
        # ServiceA 不应该在图中
        assert ServiceA not in graph
        # ServiceB 应该在图中
        assert ServiceB in graph


class TestDetectCircularDependencies:
    """测试循环依赖检测"""
    
    def test_no_circular_dependencies(self):
        """测试没有循环依赖的情况"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            ServiceC: {ServiceB},
        }
        
        circular = StaticDependencyAnalyzer.detect_circular_dependencies(graph)
        assert len(circular) == 0
    
    def test_self_dependency(self):
        """测试自依赖"""
        graph = {
            ServiceA: {ServiceA},
        }
        
        circular = StaticDependencyAnalyzer.detect_circular_dependencies(graph)
        assert len(circular) == 1
        assert circular[0][0] == ServiceA
        assert circular[0][-1] == ServiceA


class TestCalculateDependencyDepth:
    """测试依赖深度计算"""
    
    def test_no_dependencies(self):
        """测试无依赖的服务"""
        graph = {ServiceA: set()}
        depth = StaticDependencyAnalyzer.calculate_dependency_depth(graph, ServiceA)
        assert depth == 0
    
    def test_simple_chain_depth(self):
        """测试简单链的深度"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            ServiceC: {ServiceB},
        }
        
        depth_a = StaticDependencyAnalyzer.calculate_dependency_depth(graph, ServiceA)
        depth_b = StaticDependencyAnalyzer.calculate_dependency_depth(graph, ServiceB)
        depth_c = StaticDependencyAnalyzer.calculate_dependency_depth(graph, ServiceC)
        
        assert depth_a == 0
        assert depth_b == 1
        assert depth_c == 2
    
    def test_cache_usage(self):
        """测试缓存机制"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            ServiceC: {ServiceB},
        }
        
        cache: Dict[Type, int] = {}
        
        # 第一次计算
        depth = StaticDependencyAnalyzer.calculate_dependency_depth(
            graph, ServiceC, cache
        )
        assert depth == 2
        assert len(cache) > 0
        
        # 第二次应该从缓存获取
        depth2 = StaticDependencyAnalyzer.calculate_dependency_depth(
            graph, ServiceC, cache
        )
        assert depth2 == 2


class TestTopologicalOrder:
    """测试拓扑排序"""
    
    def test_simple_topological_order(self):
        """测试简单的拓扑排序"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            ServiceC: {ServiceB},
        }
        
        order = StaticDependencyAnalyzer.get_topological_order(graph)
        
        # 检查顺序是否合理：A 应该在 B 之前，B 应该在 C 之前
        a_index = order.index(ServiceA)
        b_index = order.index(ServiceB)
        c_index = order.index(ServiceC)
        
        assert a_index < b_index < c_index


class TestAnalyze:
    """测试分析函数"""
    
    def test_analyze_simple_graph(self):
        """测试简单图的分析"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            ServiceC: {ServiceB},
        }
        
        result = StaticDependencyAnalyzer.analyze(graph)
        
        assert result['total_services'] == 3
        assert result['total_dependencies'] == 2
        assert result['max_dependency_depth'] == 2
        assert result['circular_dependencies_count'] == 0
    
    def test_analyze_with_orphaned_services(self):
        """测试包含孤立服务的分析"""
        class IsolatedService:
            pass
        
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            IsolatedService: set(),  # 孤立服务
        }
        
        result = StaticDependencyAnalyzer.analyze(graph)
        
        assert 'IsolatedService' in result['orphaned_services']


class TestGetDependencyChain:
    """测试获取依赖链"""
    
    def test_simple_dependency_chain(self):
        """测试简单依赖链"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            ServiceC: {ServiceB},
        }
        
        chain = StaticDependencyAnalyzer.get_dependency_chain(graph, ServiceC)
        
        # 链应该包含 C -> B -> A
        assert ServiceC in chain
        assert ServiceB in chain
        assert ServiceA in chain


class TestGetDependents:
    """测试获取反向依赖"""
    
    def test_simple_dependents(self):
        """测试简单的反向依赖"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
            ServiceC: {ServiceA},
        }
        
        dependents = StaticDependencyAnalyzer.get_dependents(graph, ServiceA)
        
        # ServiceB 和 ServiceC 都依赖 ServiceA
        assert ServiceB in dependents
        assert ServiceC in dependents


class TestGenerateDotDiagram:
    """测试生成DOT图"""
    
    def test_dot_diagram_generation(self):
        """测试DOT格式生成"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
        }
        
        dot = StaticDependencyAnalyzer.generate_dot_diagram(graph)
        
        assert 'digraph DependencyGraph' in dot
        assert 'ServiceA' in dot
        assert 'ServiceB' in dot
        assert '->' in dot


class TestExportAnalysisToDict:
    """测试导出分析结果"""
    
    def test_export_to_dict(self):
        """测试导出为可序列化字典"""
        result = DependencyAnalysisResult(
            dependency_graph={
                ServiceA: set(),
                ServiceB: {ServiceA},
            },
            circular_dependencies=[],
            max_dependency_depth=1,
            orphaned_services=[]
        )
        
        exported = StaticDependencyAnalyzer.export_analysis_to_dict(result)
        
        assert 'dependency_graph' in exported
        assert 'circular_dependencies' in exported
        assert 'max_dependency_depth' in exported
        assert exported['max_dependency_depth'] == 1


class TestGetAnalysisResult:
    """测试获取完整分析结果"""
    
    def test_analysis_result_structure(self):
        """测试分析结果的结构"""
        graph = {
            ServiceA: set(),
            ServiceB: {ServiceA},
        }
        
        result = StaticDependencyAnalyzer.get_analysis_result(graph)
        
        assert isinstance(result, DependencyAnalysisResult)
        assert result.dependency_graph == graph
        assert isinstance(result.circular_dependencies, list)
        assert isinstance(result.max_dependency_depth, int)
        assert isinstance(result.orphaned_services, list)


# 集成测试
class TestIntegration:
    """集成测试"""
    
    def test_full_analysis_workflow(self):
        """测试完整的分析工作流"""
        # 定义服务
        services = {
            ServiceA: ServiceA,
            ServiceB: ServiceB,
            ServiceC: ServiceC,
        }
        
        # 构建图
        graph = StaticDependencyAnalyzer.build_dependency_graph(services)
        
        # 检测循环依赖
        circular = StaticDependencyAnalyzer.detect_circular_dependencies(graph)
        assert len(circular) == 0
        
        # 获取拓扑排序
        order = StaticDependencyAnalyzer.get_topological_order(graph)
        assert len(order) == 3
        
        # 分析
        analysis = StaticDependencyAnalyzer.analyze(graph)
        assert analysis['max_dependency_depth'] == 2
        
        # 获取完整结果
        result = StaticDependencyAnalyzer.get_analysis_result(graph)
        assert not result.circular_dependencies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
