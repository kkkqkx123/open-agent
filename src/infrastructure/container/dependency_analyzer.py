"""依赖分析器实现"""

import threading
from typing import Type, Set, List, Dict, Any, Optional
from inspect import signature

from ..container_interfaces import IDependencyAnalyzer


class DependencyAnalyzer(IDependencyAnalyzer):
    """依赖分析器实现"""
    
    def __init__(self):
        """初始化依赖分析器"""
        self._dependency_graph: Dict[Type, Set[Type]] = {}
        self._lock = threading.RLock()
    
    def add_dependency(self, service_type: Type, dependency_type: Type) -> None:
        """添加依赖关系
        
        Args:
            service_type: 服务类型
            dependency_type: 依赖类型
        """
        with self._lock:
            if service_type not in self._dependency_graph:
                self._dependency_graph[service_type] = set()
            self._dependency_graph[service_type].add(dependency_type)
    
    def get_dependencies(self, service_type: Type) -> Set[Type]:
        """获取服务的依赖
        
        Args:
            service_type: 服务类型
            
        Returns:
            依赖类型集合
        """
        with self._lock:
            return self._dependency_graph.get(service_type, set()).copy()
    
    def detect_circular_dependencies(self) -> List[List[Type]]:
        """检测循环依赖
        
        Returns:
            循环依赖列表
        """
        with self._lock:
            visited = set()
            rec_stack = set()
            cycles = []
            
            def dfs(node: Type, path: List[Type]) -> None:
                if node in rec_stack:
                    # 找到循环
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:] + [node]
                    cycles.append(cycle)
                    return
                
                if node in visited:
                    return
                
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in self._dependency_graph.get(node, []):
                    dfs(neighbor, path + [node])
                
                rec_stack.remove(node)
            
            for node in self._dependency_graph:
                if node not in visited:
                    dfs(node, [])
            
            return cycles
    
    def calculate_dependency_depth(self, service_type: Type) -> int:
        """计算依赖深度
        
        Args:
            service_type: 服务类型
            
        Returns:
            依赖深度
        """
        with self._lock:
            return self._calculate_dependency_depth_recursive(service_type, set())
    
    def _calculate_dependency_depth_recursive(self, service_type: Type, visited: Set[Type]) -> int:
        """递归计算依赖深度
        
        Args:
            service_type: 服务类型
            visited: 已访问的服务集合
            
        Returns:
            依赖深度
        """
        if service_type in visited:
            return 0  # 避免循环
        
        visited.add(service_type)
        
        dependencies = self._dependency_graph.get(service_type, [])
        if not dependencies:
            return 0
        
        max_depth = 0
        for dep in dependencies:
            depth = self._calculate_dependency_depth_recursive(dep, visited.copy())
            max_depth = max(max_depth, depth)
        
        return max_depth + 1
    
    def analyze(self, all_services: Optional[List[Type]] = None) -> Dict[str, Any]:
        """分析依赖关系
        
        Args:
            all_services: 所有注册的服务列表（可选）
            
        Returns:
            分析结果
        """
        with self._lock:
            # 检测循环依赖
            circular_deps = self.detect_circular_dependencies()
            
            # 计算依赖深度
            dependency_depths = {}
            for service_type in self._dependency_graph:
                dependency_depths[service_type] = self.calculate_dependency_depth(service_type)
            
            # 找出根服务（没有依赖的服务）
            root_services = [
                service_type for service_type in self._dependency_graph
                if not self._dependency_graph[service_type]
            ]
            
            # 计算总服务数
            if all_services is not None:
                total_services = len(all_services)
            else:
                total_services = len(self._dependency_graph)
            
            return {
                "circular_dependencies": circular_deps,
                "dependency_depths": dependency_depths,
                "root_services": root_services,
                "total_services": total_services
            }
    
    def update_from_implementation(self, interface: Type, implementation: Type) -> None:
        """从实现类更新依赖关系
        
        Args:
            interface: 接口类型
            implementation: 实现类型
        """
        try:
            # 分析实现类的依赖
            sig = signature(implementation.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param.annotation == param.empty:
                    continue
                
                dependency_type = param.annotation
                if isinstance(dependency_type, str):
                    # 跳过字符串类型注解，因为我们无法解析它们
                    continue
                
                if isinstance(dependency_type, type):
                    self.add_dependency(interface, dependency_type)
        except Exception:
            # 如果无法分析构造函数，跳过
            pass