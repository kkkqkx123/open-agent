"""依赖分析CLI工具 - 用于静态分析DI容器依赖关系"""

from src.interfaces.dependency_injection import get_logger
import inspect
from typing import Type, TypeVar, Dict, Any, Set, List, Optional
from collections import defaultdict, deque
from pathlib import Path

logger = get_logger(__name__)

T = TypeVar('T')


class CircularDependency:
    """循环依赖表示"""
    
    def __init__(self, dependency_chain: List[Type], description: str):
        self.dependency_chain = dependency_chain
        self.description = description
    
    def __repr__(self) -> str:
        return self.description


class DependencyAnalysisResult:
    """依赖分析结果"""
    
    def __init__(
        self,
        dependency_graph: Dict[Type, Set[Type]],
        circular_dependencies: List[CircularDependency],
        max_dependency_depth: int,
        orphaned_services: List[Type]
    ):
        self.dependency_graph = dependency_graph
        self.circular_dependencies = circular_dependencies
        self.max_dependency_depth = max_dependency_depth
        self.orphaned_services = orphaned_services


class StaticDependencyAnalyzer:
    """静态依赖分析工具 - 无状态分析器
    
    用于分析DI容器配置和代码中的依赖关系。
    所有方法都是静态的，无需维护状态。
    """
    
    @staticmethod
    def build_dependency_graph(
        services: Dict[Type, Optional[Type]]
    ) -> Dict[Type, Set[Type]]:
        """从服务注册构建依赖图
        
        Args:
            services: 服务字典，key为接口，value为实现类
            
        Returns:
            依赖图：{服务: {依赖1, 依赖2, ...}}
        """
        graph: Dict[Type, Set[Type]] = defaultdict(set)
        
        for interface, implementation in services.items():
            if implementation is None:
                continue
            
            dependencies = StaticDependencyAnalyzer._extract_dependencies(implementation)
            graph[interface] = dependencies
        
        return dict(graph)
    
    @staticmethod
    def _extract_dependencies(impl_class: Type) -> Set[Type]:
        """从实现类的构造函数提取依赖
        
        Args:
            impl_class: 实现类
            
        Returns:
            依赖类型集合
        """
        dependencies: Set[Type] = set()
        
        try:
            sig = inspect.signature(impl_class.__init__)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # 获取参数类型注解
                if param.annotation != inspect.Parameter.empty:
                    dependencies.add(param.annotation)
        
        except Exception as e:
            logger.warning(f"无法提取依赖 {impl_class.__name__}: {e}")
        
        return dependencies
    
    @staticmethod
    def detect_circular_dependencies(
        graph: Dict[Type, Set[Type]]
    ) -> List[List[Type]]:
        """检测依赖图中的循环依赖
        
        Args:
            graph: 依赖图
            
        Returns:
            循环依赖列表，每个循环是一个类型列表
        """
        circular_deps: List[List[Type]] = []
        visited: Set[Type] = set()
        rec_stack: Set[Type] = set()
        path: List[Type] = []
        
        def dfs(service_type: Type) -> None:
            visited.add(service_type)
            rec_stack.add(service_type)
            path.append(service_type)
            
            for dependency in graph.get(service_type, set()):
                if dependency not in visited:
                    dfs(dependency)
                elif dependency in rec_stack:
                    # 找到循环依赖
                    cycle_start = path.index(dependency)
                    cycle = path[cycle_start:] + [dependency]
                    circular_deps.append(cycle)
                    logger.warning(
                        f"检测到循环依赖: {' -> '.join([t.__name__ for t in cycle])}"
                    )
            
            rec_stack.remove(service_type)
            path.pop()
        
        for service_type in graph:
            if service_type not in visited:
                dfs(service_type)
        
        return circular_deps
    
    @staticmethod
    def calculate_dependency_depth(
        graph: Dict[Type, Set[Type]],
        service_type: Type,
        cache: Optional[Dict[Type, int]] = None
    ) -> int:
        """计算服务的依赖深度
        
        Args:
            graph: 依赖图
            service_type: 服务类型
            cache: 缓存深度计算结果，避免重复计算
            
        Returns:
            依赖深度（0表示无依赖）
        """
        if cache is None:
            cache = {}
        
        if service_type in cache:
            return cache[service_type]
        
        if service_type not in graph or not graph[service_type]:
            cache[service_type] = 0
            return 0
        
        max_depth = 0
        for dependency in graph[service_type]:
            depth = StaticDependencyAnalyzer.calculate_dependency_depth(
                graph, dependency, cache
            )
            max_depth = max(max_depth, depth + 1)
        
        cache[service_type] = max_depth
        return max_depth
    
    @staticmethod
    def get_topological_order(graph: Dict[Type, Set[Type]]) -> List[Type]:
        """获取依赖的拓扑排序顺序
        
        使用Kahn算法
        
        Args:
            graph: 依赖图
            
        Returns:
            拓扑排序的服务类型列表
        """
        in_degree: Dict[Type, int] = defaultdict(int)
        all_services: Set[Type] = set()
        
        # 计算入度
        for service_type, dependencies in graph.items():
            all_services.add(service_type)
            for dep in dependencies:
                all_services.add(dep)
                in_degree[dep] += 1
            if service_type not in in_degree:
                in_degree[service_type] = 0
        
        # 找到入度为0的节点
        queue = deque([service for service in all_services if in_degree[service] == 0])
        result: List[Type] = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in graph.get(current, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有循环依赖
        if len(result) != len(all_services):
            logger.warning("存在循环依赖，无法完成拓扑排序")
        
        return result
    
    @staticmethod
    def analyze(graph: Dict[Type, Set[Type]]) -> Dict[str, Any]:
        """分析依赖图的统计信息
        
        Args:
            graph: 依赖图
            
        Returns:
            分析结果字典
        """
        total_services = len(graph)
        total_dependencies = sum(len(deps) for deps in graph.values())
        
        # 计算统计信息
        depth_cache: Dict[Type, int] = {}
        depth_stats: Dict[str, int] = {}
        max_depth = 0
        
        for service_type in graph:
            depth = StaticDependencyAnalyzer.calculate_dependency_depth(
                graph, service_type, depth_cache
            )
            depth_stats[service_type.__name__] = depth
            max_depth = max(max_depth, depth)
        
        # 检测循环依赖
        circular_deps = StaticDependencyAnalyzer.detect_circular_dependencies(graph)
        
        # 找出孤立服务（没有依赖也没有被依赖）
        all_services = set(graph.keys())
        dependent_services: Set[Type] = set()
        for deps in graph.values():
            dependent_services.update(deps)
        
        orphaned_services = all_services - dependent_services
        
        # 找出叶子节点（没有依赖的服务）
        leaf_services = [
            service for service, deps in graph.items()
            if not deps
        ]
        
        # 找出根节点（没有被依赖的服务）
        root_services = [
            service for service in all_services
            if service not in dependent_services
        ]
        
        return {
            "total_services": total_services,
            "total_dependencies": total_dependencies,
            "average_dependencies_per_service": (
                total_dependencies / total_services if total_services > 0 else 0
            ),
            "max_dependency_depth": max_depth,
            "circular_dependencies_count": len(circular_deps),
            "orphaned_services_count": len(orphaned_services),
            "leaf_services_count": len(leaf_services),
            "root_services_count": len(root_services),
            "depth_stats": depth_stats,
            "circular_dependencies": [
                [t.__name__ for t in cycle] for cycle in circular_deps
            ],
            "orphaned_services": [s.__name__ for s in orphaned_services],
            "leaf_services": [s.__name__ for s in leaf_services],
            "root_services": [s.__name__ for s in root_services],
        }
    
    @staticmethod
    def get_analysis_result(graph: Dict[Type, Set[Type]]) -> DependencyAnalysisResult:
        """获取完整的依赖分析结果
        
        Args:
            graph: 依赖图
            
        Returns:
            DependencyAnalysisResult对象
        """
        # 检测循环依赖
        circular_deps_raw = StaticDependencyAnalyzer.detect_circular_dependencies(graph)
        circular_dependencies = [
            CircularDependency(
                dependency_chain=cycle,
                description=f"循环依赖: {' -> '.join([t.__name__ for t in cycle])}"
            )
            for cycle in circular_deps_raw
        ]
        
        # 计算最大依赖深度
        max_depth = 0
        depth_cache: Dict[Type, int] = {}
        for service_type in graph:
            depth = StaticDependencyAnalyzer.calculate_dependency_depth(
                graph, service_type, depth_cache
            )
            max_depth = max(max_depth, depth)
        
        # 找出孤立服务
        all_services = set(graph.keys())
        dependent_services: Set[Type] = set()
        for deps in graph.values():
            dependent_services.update(deps)
        orphaned_services = list(all_services - dependent_services)
        
        return DependencyAnalysisResult(
            dependency_graph=graph,
            circular_dependencies=circular_dependencies,
            max_dependency_depth=max_depth,
            orphaned_services=orphaned_services
        )
    
    @staticmethod
    def get_dependency_chain(
        graph: Dict[Type, Set[Type]],
        service_type: Type
    ) -> List[Type]:
        """获取服务的依赖链
        
        Args:
            graph: 依赖图
            service_type: 服务类型
            
        Returns:
            依赖链列表
        """
        chain: List[Type] = []
        visited: Set[Type] = set()
        
        def build_chain(current_type: Type) -> None:
            if current_type in visited:
                return
            visited.add(current_type)
            chain.append(current_type)
            
            for dependency in graph.get(current_type, set()):
                build_chain(dependency)
        
        build_chain(service_type)
        return chain
    
    @staticmethod
    def get_dependents(
        graph: Dict[Type, Set[Type]],
        service_type: Type
    ) -> Set[Type]:
        """获取依赖此服务的所有服务（反向依赖）
        
        Args:
            graph: 依赖图
            service_type: 服务类型
            
        Returns:
            依赖此服务的服务集合
        """
        dependents: Set[Type] = set()
        
        for service, dependencies in graph.items():
            if service_type in dependencies:
                dependents.add(service)
        
        return dependents
    
    @staticmethod
    def generate_dot_diagram(graph: Dict[Type, Set[Type]]) -> str:
        """生成Graphviz DOT格式的依赖图
        
        用于可视化依赖关系
        
        Args:
            graph: 依赖图
            
        Returns:
            DOT格式字符串
        """
        lines = ["digraph DependencyGraph {"]
        lines.append("  rankdir=LR;")
        lines.append('  node [shape=box];')
        
        for service_type, dependencies in graph.items():
            service_name = service_type.__name__
            for dep in dependencies:
                dep_name = dep.__name__
                lines.append(f'  "{service_name}" -> "{dep_name}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    @staticmethod
    def export_analysis_to_dict(
        result: DependencyAnalysisResult
    ) -> Dict[str, Any]:
        """将分析结果导出为字典（便于JSON序列化）
        
        Args:
            result: 分析结果
            
        Returns:
            可序列化的字典
        """
        return {
            "dependency_graph": {
                service.__name__: [dep.__name__ for dep in deps]
                for service, deps in result.dependency_graph.items()
            },
            "circular_dependencies": [
                {
                    "chain": [t.__name__ for t in cd.dependency_chain],
                    "description": cd.description
                }
                for cd in result.circular_dependencies
            ],
            "max_dependency_depth": result.max_dependency_depth,
            "orphaned_services": [s.__name__ for s in result.orphaned_services],
        }
