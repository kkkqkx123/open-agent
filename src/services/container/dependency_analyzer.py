"""依赖分析器实现"""

import logging
import threading
import inspect
from typing import Type, TypeVar, Dict, Any, Set, List, Optional
from collections import defaultdict, deque

from src.interfaces.container import (
    IDependencyAnalyzer,
    IDependencyContainer,
    CircularDependency,
    DependencyAnalysisResult
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyAnalyzer(IDependencyAnalyzer):
    """依赖分析器实现"""
    
    def __init__(self):
        self._dependency_graph: Dict[Type, Set[Type]] = defaultdict(set)
        self._reverse_dependency_graph: Dict[Type, Set[Type]] = defaultdict(set)
        self._dependency_depth: Dict[Type, int] = {}
        self._lock = threading.RLock()
        
        logger.debug("DependencyAnalyzer初始化完成")
    
    def add_dependency(self, service_type: Type, dependency_type: Type) -> None:
        """添加依赖关系"""
        with self._lock:
            self._dependency_graph[service_type].add(dependency_type)
            self._reverse_dependency_graph[dependency_type].add(service_type)
            
            # 清除深度缓存
            if service_type in self._dependency_depth:
                del self._dependency_depth[service_type]
            
            logger.debug(f"添加依赖关系: {service_type.__name__} -> {dependency_type.__name__}")
    
    def get_dependencies(self, service_type: Type) -> Set[Type]:
        """获取服务的依赖"""
        with self._lock:
            return self._dependency_graph.get(service_type, set()).copy()
    
    def get_dependents(self, service_type: Type) -> Set[Type]:
        """获取依赖此服务的服务"""
        with self._lock:
            return self._reverse_dependency_graph.get(service_type, set()).copy()
    
    def detect_circular_dependencies(self) -> List[List[Type]]:
        """检测循环依赖"""
        with self._lock:
            circular_deps = []
            visited = set()
            rec_stack = set()
            path = []
            
            for service_type in self._dependency_graph:
                if service_type not in visited:
                    self._dfs_detect_cycles(
                        service_type, visited, rec_stack, path, circular_deps
                    )
            
            return circular_deps
    
    def _dfs_detect_cycles(
        self, 
        service_type: Type, 
        visited: Set[Type], 
        rec_stack: Set[Type],
        path: List[Type],
        circular_deps: List[List[Type]]
    ) -> None:
        """DFS检测循环依赖"""
        visited.add(service_type)
        rec_stack.add(service_type)
        path.append(service_type)
        
        for dependency in self._dependency_graph.get(service_type, set()):
            if dependency not in visited:
                self._dfs_detect_cycles(dependency, visited, rec_stack, path, circular_deps)
            elif dependency in rec_stack:
                # 找到循环依赖
                cycle_start = path.index(dependency)
                cycle = path[cycle_start:] + [dependency]
                circular_deps.append(cycle)
                logger.warning(f"检测到循环依赖: {' -> '.join([t.__name__ for t in cycle])}")
        
        rec_stack.remove(service_type)
        path.pop()
    
    def calculate_dependency_depth(self, service_type: Type) -> int:
        """计算依赖深度"""
        with self._lock:
            if service_type in self._dependency_depth:
                return self._dependency_depth[service_type]
            
            if service_type not in self._dependency_graph or not self._dependency_graph[service_type]:
                self._dependency_depth[service_type] = 0
                return 0
            
            max_depth = 0
            for dependency in self._dependency_graph[service_type]:
                depth = self.calculate_dependency_depth(dependency)
                max_depth = max(max_depth, depth + 1)
            
            self._dependency_depth[service_type] = max_depth
            return max_depth
    
    def analyze(self) -> Dict[str, Any]:
        """分析依赖关系"""
        with self._lock:
            total_services = len(self._dependency_graph)
            total_dependencies = sum(len(deps) for deps in self._dependency_graph.values())
            
            # 计算统计信息
            depth_stats = {}
            for service_type in self._dependency_graph:
                depth = self.calculate_dependency_depth(service_type)
                depth_stats[service_type.__name__] = depth
            
            # 检测循环依赖
            circular_deps = self.detect_circular_dependencies()
            
            # 找出孤立服务（没有依赖也没有被依赖）
            all_services = set(self._dependency_graph.keys())
            dependent_services = set()
            for deps in self._dependency_graph.values():
                dependent_services.update(deps)
            
            orphaned_services = all_services - dependent_services
            
            # 找出叶子节点（没有依赖的服务）
            leaf_services = [
                service for service, deps in self._dependency_graph.items()
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
                "average_dependencies_per_service": total_dependencies / total_services if total_services > 0 else 0,
                "max_dependency_depth": max(depth_stats.values()) if depth_stats else 0,
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
                "root_services": [s.__name__ for s in root_services]
            }
    
    def update_from_implementation(self, interface: Type, implementation: Type) -> None:
        """从实现类更新依赖关系"""
        with self._lock:
            try:
                # 分析构造函数参数
                sig = inspect.signature(implementation.__init__)
                dependencies = set()
                
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    
                    # 获取参数类型注解
                    if param.annotation != inspect.Parameter.empty:
                        dependencies.add(param.annotation)
                
                # 更新依赖关系
                if interface in self._dependency_graph:
                    # 清除旧的依赖关系
                    old_deps = self._dependency_graph[interface].copy()
                    for old_dep in old_deps:
                        self._reverse_dependency_graph[old_dep].discard(interface)
                
                # 添加新的依赖关系
                self._dependency_graph[interface] = dependencies
                for dep in dependencies:
                    self._reverse_dependency_graph[dep].add(interface)
                
                # 清除深度缓存
                if interface in self._dependency_depth:
                    del self._dependency_depth[interface]
                
                logger.debug(f"从实现类更新依赖关系: {interface.__name__} -> {implementation.__name__}")
                
            except Exception as e:
                logger.error(f"更新依赖关系失败: {e}")
    
    def get_dependency_chain(self, service_type: Type) -> List[Type]:
        """获取依赖链"""
        with self._lock:
            chain = []
            visited = set()
            
            def build_chain(current_type: Type) -> None:
                if current_type in visited:
                    return
                visited.add(current_type)
                chain.append(current_type)
                
                for dependency in self._dependency_graph.get(current_type, set()):
                    build_chain(dependency)
            
            build_chain(service_type)
            return chain
    
    def get_topological_order(self) -> List[Type]:
        """获取拓扑排序顺序"""
        with self._lock:
            # Kahn算法
            in_degree = defaultdict(int)
            all_services = set()
            
            # 计算入度
            for service_type, dependencies in self._dependency_graph.items():
                all_services.add(service_type)
                for dep in dependencies:
                    all_services.add(dep)
                    in_degree[dep] += 1
                if service_type not in in_degree:
                    in_degree[service_type] = 0
            
            # 找到入度为0的节点
            queue = deque([service for service in all_services if in_degree[service] == 0])
            result = []
            
            while queue:
                current = queue.popleft()
                result.append(current)
                
                for neighbor in self._dependency_graph.get(current, set()):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            # 检查是否有循环依赖
            if len(result) != len(all_services):
                logger.warning("存在循环依赖，无法完成拓扑排序")
            
            return result
    
    def get_analysis_result(self) -> DependencyAnalysisResult:
        """获取完整的依赖分析结果"""
        with self._lock:
            # 构建依赖图
            dependency_graph = {
                service: deps.copy() 
                for service, deps in self._dependency_graph.items()
            }
            
            # 检测循环依赖
            circular_deps_raw = self.detect_circular_dependencies()
            circular_dependencies = [
                CircularDependency(
                    dependency_chain=cycle,
                    description=f"循环依赖: {' -> '.join([t.__name__ for t in cycle])}"
                )
                for cycle in circular_deps_raw
            ]
            
            # 计算最大依赖深度
            max_depth = 0
            for service_type in self._dependency_graph:
                depth = self.calculate_dependency_depth(service_type)
                max_depth = max(max_depth, depth)
            
            # 找出孤立服务
            all_services = set(self._dependency_graph.keys())
            dependent_services = set()
            for deps in self._dependency_graph.values():
                dependent_services.update(deps)
            orphaned_services = list(all_services - dependent_services)
            
            return DependencyAnalysisResult(
                dependency_graph=dependency_graph,
                circular_dependencies=circular_dependencies,
                max_dependency_depth=max_depth,
                orphaned_services=orphaned_services
            )
    
    def clear(self) -> None:
        """清除所有依赖关系"""
        with self._lock:
            self._dependency_graph.clear()
            self._reverse_dependency_graph.clear()
            self._dependency_depth.clear()
            logger.debug("依赖关系已清除")
    
    def remove_dependency(self, service_type: Type, dependency_type: Type) -> None:
        """移除依赖关系"""
        with self._lock:
            if service_type in self._dependency_graph:
                self._dependency_graph[service_type].discard(dependency_type)
            
            if dependency_type in self._reverse_dependency_graph:
                self._reverse_dependency_graph[dependency_type].discard(service_type)
            
            # 清除深度缓存
            if service_type in self._dependency_depth:
                del self._dependency_depth[service_type]
            
            logger.debug(f"移除依赖关系: {service_type.__name__} -> {dependency_type.__name__}")
    
    def remove_service(self, service_type: Type) -> None:
        """移除服务及其所有依赖关系"""
        with self._lock:
            # 移除作为依赖的关系
            if service_type in self._reverse_dependency_graph:
                for dependent in self._reverse_dependency_graph[service_type]:
                    self._dependency_graph[dependent].discard(service_type)
            
            # 移除服务本身
            self._dependency_graph.pop(service_type, None)
            self._reverse_dependency_graph.pop(service_type, None)
            self._dependency_depth.pop(service_type, None)
            
            logger.debug(f"移除服务及其依赖关系: {service_type.__name__}")