"""工作流可视化器

专注于工作流图形化展示和图表导出
"""

from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger
from datetime import datetime
import math
import random
import json

from src.core.workflow.graph_entities import GraphConfig
from src.interfaces.workflow.exceptions import WorkflowError
from src.interfaces.workflow.visualization import IWorkflowVisualizer

logger = get_logger(__name__)


class WorkflowVisualizer(IWorkflowVisualizer):
    """工作流可视化器实现
    
    专注于：
    - 工作流图形化展示
    - 多格式图表导出
    - 布局算法优化
    """
    
    def __init__(self):
        """初始化可视化器"""
        self.layout_engines = {
            "hierarchical": self._hierarchical_layout,
            "force_directed": self._force_directed_layout,
            "circular": self._circular_layout
        }
        
        logger.info("WorkflowVisualizer初始化完成")
    
    def generate_visualization(self, config: GraphConfig, layout: str = "hierarchical") -> Dict[str, Any]:
        """生成可视化数据
        
        Args:
            config: 工作流配置
            layout: 布局算法
            
        Returns:
            Dict[str, Any]: 可视化数据
        """
        try:
            # 选择布局引擎
            layout_engine = self.layout_engines.get(layout, self._hierarchical_layout)
            
            # 生成节点数据
            nodes = self._generate_nodes(config)
            
            # 生成边数据
            edges = self._generate_edges(config)
            
            # 应用布局算法
            positioned_nodes = layout_engine(nodes, edges)
            
            # 确定实际使用的布局
            actual_layout = layout if layout in self.layout_engines else "hierarchical"
            
            # 生成可视化数据
            visualization = {
                "workflow_id": config.name,
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "layout": actual_layout,
                "nodes": positioned_nodes,
                "edges": edges,
                "entry_point": config.entry_point,
                "generated_at": datetime.now().isoformat(),
                "statistics": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "node_types": self._count_node_types(nodes),
                    "edge_types": self._count_edge_types(edges)
                }
            }
            
            logger.info(f"工作流可视化生成成功: {config.name}")
            return visualization
            
        except Exception as e:
            logger.error(f"生成工作流可视化失败: {config.name}, error: {e}")
            raise WorkflowError(f"生成工作流可视化失败: {str(e)}")
    
    def export_diagram(self, config: GraphConfig, format: str = "json") -> bytes:
        """导出图表
        
        Args:
            config: 工作流配置
            format: 导出格式 (json, svg, png, mermaid)
            
        Returns:
            bytes: 图表数据
        """
        visualization = self.generate_visualization(config)
        
        if format == "json":
            return json.dumps(visualization, indent=2, ensure_ascii=False).encode('utf-8')
        
        elif format == "mermaid":
            return self._export_mermaid(visualization).encode('utf-8')
        
        elif format == "svg":
            return self._export_svg(visualization)
        
        elif format == "png":
            return self._export_png(visualization)
        
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _generate_nodes(self, config: GraphConfig) -> List[Dict[str, Any]]:
        """生成节点数据"""
        nodes = []
        for node_id, node_config in config.nodes.items():
            nodes.append({
                "id": node_id,
                "type": node_config.function_name,
                "label": node_config.description or node_config.function_name,
                "config": node_config.config,
                "position": {"x": 0, "y": 0},  # 将由布局算法设置
                "size": self._get_node_size(node_config.function_name),
                "style": self._get_node_style(node_config.function_name),
                "metadata": {
                    "description": node_config.description,
                    "category": self._get_node_category(node_config.function_name)
                }
            })
        return nodes
    
    def _generate_edges(self, config: GraphConfig) -> List[Dict[str, Any]]:
        """生成边数据"""
        edges = []
        for edge in config.edges:
            edges.append({
                "id": f"{edge.from_node}_{edge.to_node}",
                "from": edge.from_node,
                "to": edge.to_node,
                "type": edge.type.value,
                "label": edge.description or "",
                "condition": edge.condition,
                "style": self._get_edge_style(edge.type.value),
                "metadata": {
                    "description": edge.description
                }
            })
        return edges
    
    def _hierarchical_layout(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """层次布局算法"""
        # 简化实现：按层次排列节点
        levels = self._calculate_hierarchy_levels(nodes, edges)
        
        positioned_nodes = []
        level_height = 150
        node_width = 200
        
        for level, node_ids in enumerate(levels):
            for i, node_id in enumerate(node_ids):
                node = next(n for n in nodes if n["id"] == node_id)
                node["position"] = {
                    "x": (i - len(node_ids) / 2) * node_width + node_width / 2,
                    "y": level * level_height
                }
                positioned_nodes.append(node)
        
        return positioned_nodes
    
    def _force_directed_layout(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """力导向布局算法"""
        # 简化实现：随机分布
        positioned_nodes = []
        center_x, center_y = 400, 300
        radius = 200
        
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            node["position"] = {
                "x": center_x + radius * math.cos(angle),
                "y": center_y + radius * math.sin(angle)
            }
            positioned_nodes.append(node)
        
        return positioned_nodes
    
    def _circular_layout(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """圆形布局算法"""
        positioned_nodes = []
        center_x, center_y = 400, 300
        radius = min(300, 50 * len(nodes))
        
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            node["position"] = {
                "x": center_x + radius * math.cos(angle),
                "y": center_y + radius * math.sin(angle)
            }
            positioned_nodes.append(node)
        
        return positioned_nodes
    
    def _calculate_hierarchy_levels(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[List[str]]:
        """计算层次级别"""
        # 简化实现：基于边的连接关系计算层次
        entry_points = [n["id"] for n in nodes if n.get("is_entry", False)]
        if not entry_points:
            entry_points = [nodes[0]["id"]] if nodes else []
        
        levels = []
        visited = set()
        current_level = entry_points.copy()
        
        while current_level:
            levels.append(current_level.copy())
            visited.update(current_level)
            
            next_level = []
            for node_id in current_level:
                # 找到所有从当前节点出发的边
                outgoing_edges = [e for e in edges if e["from"] == node_id]
                for edge in outgoing_edges:
                    if edge["to"] not in visited and edge["to"] not in next_level:
                        next_level.append(edge["to"])
            
            current_level = next_level
        
        # 添加未访问的节点
        unvisited = [n["id"] for n in nodes if n["id"] not in visited]
        if unvisited:
            levels.append(unvisited)
        
        return levels
    
    def _get_node_size(self, node_type: str) -> Dict[str, int]:
        """获取节点大小"""
        size_map = {
            "llm_node": {"width": 120, "height": 80},
            "tool_node": {"width": 100, "height": 60},
            "condition_node": {"width": 80, "height": 80},
            "start_node": {"width": 60, "height": 60},
            "end_node": {"width": 60, "height": 60}
        }
        return size_map.get(node_type, {"width": 100, "height": 60})
    
    def _get_node_style(self, node_type: str) -> Dict[str, Any]:
        """获取节点样式"""
        style_map = {
            "llm_node": {
                "fill": "#e1f5fe",
                "stroke": "#0288d1",
                "stroke_width": 2
            },
            "tool_node": {
                "fill": "#f3e5f5",
                "stroke": "#7b1fa2",
                "stroke_width": 2
            },
            "condition_node": {
                "fill": "#fff3e0",
                "stroke": "#f57c00",
                "stroke_width": 2
            },
            "start_node": {
                "fill": "#e8f5e8",
                "stroke": "#4caf50",
                "stroke_width": 2
            },
            "end_node": {
                "fill": "#ffebee",
                "stroke": "#f44336",
                "stroke_width": 2
            }
        }
        return style_map.get(node_type, {
            "fill": "#f5f5f5",
            "stroke": "#9e9e9e",
            "stroke_width": 1
        })
    
    def _get_edge_style(self, edge_type: str) -> Dict[str, Any]:
        """获取边样式"""
        style_map = {
            "normal": {
                "stroke": "#666",
                "stroke_width": 2,
                "arrow": True
            },
            "conditional": {
                "stroke": "#ff9800",
                "stroke_width": 2,
                "arrow": True,
                "dash_array": "5,5"
            },
            "error": {
                "stroke": "#f44336",
                "stroke_width": 2,
                "arrow": True
            }
        }
        return style_map.get(edge_type, {
            "stroke": "#666",
            "stroke_width": 2,
            "arrow": True
        })
    
    def _get_node_category(self, node_type: str) -> str:
        """获取节点分类"""
        category_map = {
            "llm_node": "ai",
            "tool_node": "tool",
            "condition_node": "control",
            "start_node": "control",
            "end_node": "control"
        }
        return category_map.get(node_type, "unknown")
    
    def _count_node_types(self, nodes: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计节点类型"""
        counts = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts
    
    def _count_edge_types(self, edges: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计边类型"""
        counts = {}
        for edge in edges:
            edge_type = edge.get("type", "unknown")
            counts[edge_type] = counts.get(edge_type, 0) + 1
        return counts
    
    def _export_mermaid(self, visualization: Dict[str, Any]) -> str:
        """导出为Mermaid格式"""
        # 简化实现
        mermaid = "graph TD\n"
        for node in visualization.get("nodes", []):
            node_id = node["id"]
            label = node.get("label", node_id)
            mermaid += f"    {node_id}[{label}]\n"
        
        for edge in visualization.get("edges", []):
            from_node = edge["from"]
            to_node = edge["to"]
            label = edge.get("label", "")
            if label:
                mermaid += f"    {from_node} -->|{label}| {to_node}\n"
            else:
                mermaid += f"    {from_node} --> {to_node}\n"
        
        return mermaid
    
    def _export_svg(self, visualization: Dict[str, Any]) -> bytes:
        """导出为SVG格式"""
        # 简化实现，返回空的SVG
        svg = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="50%" y="50%" font-family="Arial" font-size="20" text-anchor="middle" fill="#000000">
    SVG export not fully implemented
  </text>
</svg>"""
        return svg.encode('utf-8')
    
    def _export_png(self, visualization: Dict[str, Any]) -> bytes:
        """导出为PNG格式"""
        # 简化实现，返回空的PNG数据
        return b"PNG export not implemented"