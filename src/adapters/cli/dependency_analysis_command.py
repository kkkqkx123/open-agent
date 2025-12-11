"""依赖分析命令 - CLI接口"""

import json
from src.interfaces.dependency_injection import get_logger
from pathlib import Path
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from src.adapters.cli.dependency_analyzer_tool import (
    StaticDependencyAnalyzer,
    DependencyAnalysisResult
)

logger = get_logger(__name__)


class IDependencyAnalysisCommand(ABC):
    """依赖分析命令接口"""
    
    @abstractmethod
    def analyze_container_file(self, file_path: str) -> Dict[str, Any]:
        """分析容器配置文件"""
        pass
    
    @abstractmethod
    def check_circular_dependencies(self) -> bool:
        """检查是否存在循环依赖"""
        pass
    
    @abstractmethod
    def generate_report(self, output_format: str = "text") -> str:
        """生成分析报告"""
        pass


class DependencyAnalysisCommand:
    """依赖分析命令实现"""
    
    def __init__(self):
        self._analysis_result: Optional[DependencyAnalysisResult] = None
        self._graph: Dict[type, set] = {}
    
    def analyze_services(self, services_dict: Dict[type, Optional[type]]) -> None:
        """分析服务依赖关系
        
        Args:
            services_dict: 服务字典，key为接口，value为实现类或None
        """
        self._graph = StaticDependencyAnalyzer.build_dependency_graph(services_dict)
        self._analysis_result = StaticDependencyAnalyzer.get_analysis_result(self._graph)
        logger.info(f"依赖分析完成: {len(self._graph)}个服务")
    
    def analyze_container_file(self, file_path: str) -> Dict[str, Any]:
        """分析容器配置文件（需要从文件中提取服务信息）
        
        Args:
            file_path: 容器配置文件路径
            
        Returns:
            分析结果字典
        """
        # 注：这是一个占位符实现
        # 实际实现需要解析容器配置文件并提取服务信息
        logger.warning(f"从文件分析容器配置: {file_path}")
        return {}
    
    def check_circular_dependencies(self) -> bool:
        """检查是否存在循环依赖
        
        Returns:
            如果存在循环依赖返回True，否则返回False
        """
        if not self._analysis_result:
            return False
        return len(self._analysis_result.circular_dependencies) > 0
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """获取循环依赖列表
        
        Returns:
            循环依赖列表，每个循环是类型名称列表
        """
        if not self._analysis_result:
            return []
        
        return [
            [t.__name__ for t in cd.dependency_chain]
            for cd in self._analysis_result.circular_dependencies
        ]
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计信息
        
        Returns:
            统计信息字典
        """
        if not self._graph:
            return {}
        
        return StaticDependencyAnalyzer.analyze(self._graph)
    
    def get_dependency_depth(self, service_type: type) -> int:
        """获取服务的依赖深度
        
        Args:
            service_type: 服务类型
            
        Returns:
            依赖深度
        """
        return StaticDependencyAnalyzer.calculate_dependency_depth(
            self._graph, service_type
        )
    
    def get_topological_order(self) -> List[type]:
        """获取依赖的拓扑排序顺序
        
        Returns:
            排序后的服务类型列表
        """
        return StaticDependencyAnalyzer.get_topological_order(self._graph)
    
    def generate_text_report(self) -> str:
        """生成文本格式的分析报告
        
        Returns:
            格式化的文本报告
        """
        if not self._analysis_result:
            return "未执行任何分析"
        
        lines = [
            "=" * 80,
            "依赖关系分析报告",
            "=" * 80,
        ]
        
        # 统计信息
        stats = self.get_analysis_stats()
        lines.extend([
            "",
            "【统计信息】",
            f"  总服务数: {stats.get('total_services', 0)}",
            f"  总依赖数: {stats.get('total_dependencies', 0)}",
            f"  平均依赖数: {stats.get('average_dependencies_per_service', 0):.2f}",
            f"  最大依赖深度: {stats.get('max_dependency_depth', 0)}",
        ])
        
        # 循环依赖检测
        circular_deps = self.get_circular_dependencies()
        lines.extend([
            "",
            "【循环依赖检测】",
            f"  发现{len(circular_deps)}个循环依赖",
        ])
        
        if circular_deps:
            for i, cycle in enumerate(circular_deps, 1):
                lines.append(f"    {i}. {' -> '.join(cycle)}")
        
        # 孤立服务
        if self._analysis_result.orphaned_services:
            lines.extend([
                "",
                "【孤立服务】",
                f"  发现{len(self._analysis_result.orphaned_services)}个孤立服务",
            ])
            for service in self._analysis_result.orphaned_services:
                lines.append(f"    - {service.__name__}")
        
        # 叶子节点
        leaf_services = stats.get('leaf_services', [])
        if leaf_services:
            lines.extend([
                "",
                "【叶子节点（无依赖的服务）】",
                f"  发现{len(leaf_services)}个叶子节点",
            ])
            for service_name in leaf_services[:10]:  # 只显示前10个
                lines.append(f"    - {service_name}")
            if len(leaf_services) > 10:
                lines.append(f"    ... 还有{len(leaf_services) - 10}个")
        
        # 根节点
        root_services = stats.get('root_services', [])
        if root_services:
            lines.extend([
                "",
                "【根节点（无被依赖的服务）】",
                f"  发现{len(root_services)}个根节点",
            ])
            for service_name in root_services[:10]:  # 只显示前10个
                lines.append(f"    - {service_name}")
            if len(root_services) > 10:
                lines.append(f"    ... 还有{len(root_services) - 10}个")
        
        lines.extend([
            "",
            "=" * 80,
        ])
        
        return "\n".join(lines)
    
    def generate_json_report(self) -> str:
        """生成JSON格式的分析报告
        
        Returns:
            JSON格式的报告字符串
        """
        if not self._analysis_result:
            return json.dumps({"error": "未执行任何分析"})
        
        report = {
            "stats": self.get_analysis_stats(),
            "circular_dependencies": self.get_circular_dependencies(),
            "orphaned_services": [
                s.__name__ for s in self._analysis_result.orphaned_services
            ],
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def generate_dot_diagram(self) -> str:
        """生成Graphviz DOT格式的依赖图
        
        Returns:
            DOT格式字符串
        """
        return StaticDependencyAnalyzer.generate_dot_diagram(self._graph)
    
    def export_report(self, output_path: str, format: str = "json") -> None:
        """将报告导出到文件
        
        Args:
            output_path: 输出文件路径
            format: 输出格式 (json, text, dot)
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            content = self.generate_json_report()
        elif format == "text":
            content = self.generate_text_report()
        elif format == "dot":
            content = self.generate_dot_diagram()
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        path.write_text(content, encoding="utf-8")
        logger.info(f"报告已导出到: {output_path}")
