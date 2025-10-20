"""工作流节点自动发现模块

提供自动发现和注册工作流节点的功能。
"""

import importlib
import inspect
from typing import List, Type, Dict, Any, Optional
from pathlib import Path

from .registry import BaseNode, get_global_registry, NodeRegistry


class NodeDiscovery:
    """节点发现器"""
    
    def __init__(self, registry: Optional[NodeRegistry] = None) -> None:
        """初始化节点发现器
        
        Args:
            registry: 节点注册表，如果为None则使用全局注册表
        """
        self.registry = registry or get_global_registry()
    
    def discover_nodes_from_package(self, package_path: str) -> List[Type[BaseNode]]:
        """从包中发现节点类
        
        Args:
            package_path: 包路径，如 "src.workflow.nodes"
            
        Returns:
            List[Type[BaseNode]]: 发现的节点类列表
        """
        discovered_nodes: List[Type[BaseNode]] = []
        
        try:
            # 导入包
            package = importlib.import_module(package_path)
            
            # 获取包路径
            package_file = getattr(package, '__file__', None)
            if not package_file:
                return discovered_nodes
                
            package_dir = Path(package_file).parent
            
            # 遍历包中的所有模块
            for module_file in package_dir.glob("*.py"):
                if module_file.name.startswith("_"):
                    continue
                    
                module_name = module_file.stem
                full_module_name = f"{package_path}.{module_name}"
                
                try:
                    # 导入模块
                    module = importlib.import_module(full_module_name)
                    
                    # 查找模块中的节点类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseNode) and 
                            obj is not BaseNode and 
                            obj.__module__ == full_module_name):
                            discovered_nodes.append(obj)
                            
                except ImportError as e:
                    print(f"无法导入模块 {full_module_name}: {e}")
                    continue
                    
        except ImportError as e:
            print(f"无法导入包 {package_path}: {e}")
            
        return discovered_nodes
    
    def register_discovered_nodes(self, nodes: List[Type[BaseNode]]) -> Dict[str, bool]:
        """注册发现的节点
        
        Args:
            nodes: 要注册的节点类列表
            
        Returns:
            Dict[str, bool]: 注册结果，键为节点类型，值为是否成功注册
        """
        results = {}
        
        for node_class in nodes:
            node_type = None
            try:
                # 获取节点类型
                # 通过实例化临时对象来获取node_type属性的值
                temp_instance = object.__new__(node_class)
                try:
                    node_type = temp_instance.node_type
                except (AttributeError, NotImplementedError):
                    # 如果无法获取node_type，则使用类名
                    node_type = node_class.__name__.lower().replace('node', '')
                
                # 注册节点
                self.registry.register_node(node_class)
                results[node_type] = True
                
            except Exception as e:
                print(f"注册节点 {node_class.__name__} 失败: {e}")
                # 确保node_type在异常处理中已定义
                if node_type is None:
                    node_type = getattr(node_class, '__name__', 'unknown').lower().replace('node', '')
                results[node_type] = False
                
        return results
    
    def auto_discover_and_register(self, package_paths: List[str]) -> Dict[str, Any]:
        """自动发现并注册节点
        
        Args:
            package_paths: 要搜索的包路径列表
            
        Returns:
            Dict[str, Any]: 发现和注册结果
        """
        results: Dict[str, Any] = {
            "discovered": {},
            "registered": {},
            "failed": []
        }
        
        for package_path in package_paths:
            # 发现节点
            discovered_nodes = self.discover_nodes_from_package(package_path)
            results["discovered"][package_path] = [node.__name__ for node in discovered_nodes]
            
            # 注册节点
            registration_results = self.register_discovered_nodes(discovered_nodes)
            results["registered"][package_path] = registration_results
            
            # 记录失败的注册
            for node_type, success in registration_results.items():
                if not success:
                    results["failed"].append({
                        "package": package_path,
                        "node_type": node_type
                    })
        
        return results


def auto_register_nodes(package_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """自动注册节点的便捷函数
    
    Args:
        package_paths: 要搜索的包路径列表，如果为None则使用默认路径
        
    Returns:
        Dict[str, Any]: 注册结果
    """
    if package_paths is None:
        package_paths = [
            "src.workflow.nodes",
        ]
    
    discovery = NodeDiscovery()
    return discovery.auto_discover_and_register(package_paths)


def register_builtin_nodes() -> None:
    """注册内置节点"""
    # 导入所有内置节点模块，确保装饰器注册生效
    try:
        from .nodes.analysis_node import AnalysisNode
        from .nodes.tool_node import ToolNode
        from .nodes.llm_node import LLMNode
        from .nodes.condition_node import ConditionNode
    except ImportError as e:
        print(f"导入内置节点失败: {e}")