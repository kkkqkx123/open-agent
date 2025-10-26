"""工作流可视化模块

提供LangGraph Studio集成和工作流可视化功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import subprocess
import time
import threading
from datetime import datetime

from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.builder import WorkflowBuilder


class IWorkflowVisualizer(ABC):
    """工作流可视化器接口"""

    @abstractmethod
    def visualize_workflow(self, workflow_config: WorkflowConfig) -> str:
        """可视化工作流配置

        Args:
            workflow_config: 工作流配置

        Returns:
            str: 可视化URL或标识符
        """
        pass

    @abstractmethod
    def start_studio(self, port: int = 8079) -> bool:
        """启动LangGraph Studio

        Args:
            port: Studio端口

        Returns:
            bool: 是否成功启动
        """
        pass

    @abstractmethod
    def stop_studio(self) -> bool:
        """停止LangGraph Studio

        Returns:
            bool: 是否成功停止
        """
        pass

    @abstractmethod
    def is_studio_running(self) -> bool:
        """检查Studio是否正在运行

        Returns:
            bool: Studio是否正在运行
        """
        pass

    @abstractmethod
    def get_studio_url(self, port: int = 8079) -> str:
        """获取Studio URL

        Args:
            port: Studio端口

        Returns:
            str: Studio URL
        """
        pass


class LangGraphStudioVisualizer(IWorkflowVisualizer):
    """LangGraph Studio可视化器实现"""

    def __init__(self, studio_port: int = 8079) -> None:
        """初始化可视化器

        Args:
            studio_port: Studio端口
        """
        from subprocess import Popen
        self.studio_port = studio_port
        self.studio_process: Optional[Popen[str]] = None
        self._studio_thread = None
        self._temp_dir = Path("./temp_visualizations")
        self._temp_dir.mkdir(exist_ok=True)

    def visualize_workflow(self, workflow_config: WorkflowConfig) -> str:
        """可视化工作流配置"""
        try:
            # 生成工作流图数据
            graph_data = self._generate_graph_data(workflow_config)
            
            # 保存到临时文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            graph_file = self._temp_dir / f"{workflow_config.name}_{timestamp}.json"
            
            with open(graph_file, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            
            # 确保Studio正在运行
            if not self.is_studio_running():
                self.start_studio(self.studio_port)
            
            # 返回Studio URL
            return f"http://localhost:{self.studio_port}/?graph={graph_file.name}"
            
        except Exception as e:
            raise RuntimeError(f"可视化工作流失败: {e}")

    def start_studio(self, port: int = 8079) -> bool:
        """启动LangGraph Studio"""
        try:
            if self.is_studio_running():
                return True
            
            # 检查langgraph-studio是否安装
            try:
                subprocess.run(["langgraph-studio", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                raise RuntimeError("langgraph-studio未安装，请运行: pip install langgraph-studio")
            
            # 启动Studio
            cmd = ["langgraph-studio", "--port", str(port), "--host", "0.0.0.0"]
            self.studio_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待Studio启动
            for _ in range(30):  # 最多等待30秒
                if self.is_studio_running():
                    return True
                time.sleep(1)
            
            # 如果超时，停止进程
            self.stop_studio()
            return False
            
        except Exception:
            return False

    def stop_studio(self) -> bool:
        """停止LangGraph Studio"""
        try:
            if self.studio_process:
                self.studio_process.terminate()
                self.studio_process.wait(timeout=5)
                self.studio_process = None
                return True
            return False
        except Exception:
            try:
                if self.studio_process:
                    self.studio_process.kill()
                    self.studio_process = None
                return True
            except Exception:
                return False

    def is_studio_running(self) -> bool:
        """检查Studio是否正在运行"""
        if not self.studio_process:
            return False
        
        # 检查进程是否还在运行
        return self.studio_process.poll() is None

    def get_studio_url(self, port: int = 8079) -> str:
        """获取Studio URL"""
        return f"http://localhost:{port}"

    def _generate_graph_data(self, config: WorkflowConfig) -> Dict[str, Any]:
        """生成图数据"""
        nodes = []
        edges = []
        
        # 生成节点数据
        for node_name, node_config in config.nodes.items():
            node_data = {
                "id": node_name,
                "type": node_config.function_name,
                "config": node_config.config,
                "metadata": {
                    "description": node_config.description
                }
            }
            
            # 添加节点特定的元数据
            metadata = node_data["metadata"]
            if isinstance(metadata, dict):
                if node_config.function_name == "analysis_node":
                    metadata["category"] = "analysis"
                    metadata["color"] = "#4CAF50"
                elif node_config.function_name == "tool_node":
                    metadata["category"] = "tool"
                    metadata["color"] = "#2196F3"
                elif node_config.function_name == "llm_node":
                    metadata["category"] = "llm"
                    metadata["color"] = "#FF9800"
                elif node_config.function_name == "condition_node":
                    metadata["category"] = "condition"
                    metadata["color"] = "#9C27B0"
                else:
                    metadata["category"] = "custom"
                    metadata["color"] = "#607D8B"
            
            nodes.append(node_data)
        
        # 生成边数据
        for edge_config in config.edges:
            edge_data = {
                "id": f"{edge_config.from_node}_{edge_config.to_node}",
                "source": edge_config.from_node,
                "target": edge_config.to_node,
                "type": edge_config.type.value,
                "condition": edge_config.condition,
                "metadata": {
                    "description": edge_config.description or ""
                }
            }
            
            # 添加边特定的元数据
            metadata = edge_data["metadata"]  # type: ignore
            if isinstance(metadata, dict):
                if edge_config.type.value == "conditional":
                    metadata["style"] = "dashed"
                    metadata["color"] = "#F44336"
                else:
                    metadata["style"] = "solid"
                    metadata["color"] = "#795548"
            
            edges.append(edge_data)
        
        # 生成完整的图数据
        graph_data = {
            "metadata": {
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "created_at": datetime.now().isoformat(),
                "entry_point": config.entry_point
            },
            "nodes": nodes,
            "edges": edges,
            "layout": {
                "direction": "TB",  # Top to Bottom
                "spacing": 100,
                "padding": 50
            }
        }
        
        return graph_data

    def export_graph_image(self, workflow_config: WorkflowConfig, output_path: Path, format: str = "png") -> bool:
        """导出工作流图图像

        Args:
            workflow_config: 工作流配置
            output_path: 输出路径
            format: 图像格式，支持 "png", "svg", "pdf"

        Returns:
            bool: 是否成功导出
        """
        try:
            # 生成图数据
            graph_data = self._generate_graph_data(workflow_config)
            
            # 使用graphviz生成图像（如果可用）
            try:
                import graphviz
                
                # 创建有向图
                dot = graphviz.Digraph(
                    comment=workflow_config.name,
                    format=format,
                    engine='dot'
                )
                
                # 添加节点
                for node in graph_data["nodes"]:
                    label = f"{node['id']}\\n({node['type']})"
                    dot.node(
                        node['id'],
                        label=label,
                        color=node['metadata'].get('color', 'black'),
                        shape='box'
                    )
                
                # 添加边
                for edge in graph_data["edges"]:
                    label = edge.get('condition', '')
                    if edge['metadata'].get('style') == 'dashed':
                        dot.edge(
                            edge['source'],
                            edge['target'],
                            label=label,
                            style='dashed',
                            color=edge['metadata'].get('color', 'black')
                        )
                    else:
                        dot.edge(
                            edge['source'],
                            edge['target'],
                            label=label,
                            color=edge['metadata'].get('color', 'black')
                        )
                
                # 渲染图像
                dot.render(str(output_path.with_suffix('')), cleanup=True)
                return True
                
            except ImportError:
                # 如果graphviz不可用，尝试使用其他方法
                return self._export_graph_with_mermaid(graph_data, output_path, format)
                
        except Exception:
            return False

    def _export_graph_with_mermaid(self, graph_data: Dict[str, Any], output_path: Path, format: str) -> bool:
        """使用Mermaid导出图"""
        try:
            # 生成Mermaid代码
            mermaid_code = self._generate_mermaid_code(graph_data)
            
            if format == "svg":
                # 使用mermaid-cli生成SVG
                try:
                    subprocess.run([
                        "mmdc",
                        "-i", "-",
                        "-o", str(output_path)
                    ], input=mermaid_code, text=True, check=True)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
            
            # 如果无法生成图像，保存Mermaid代码
            mermaid_file = output_path.with_suffix('.mmd')
            with open(mermaid_file, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            
            return False
            
        except Exception:
            return False

    def _generate_mermaid_code(self, graph_data: Dict[str, Any]) -> str:
        """生成Mermaid代码"""
        lines = ["graph TD"]
        
        # 添加节点
        for node in graph_data["nodes"]:
            node_id = node["id"]
            node_label = f"{node['id']}\\n({node['type']})"
            lines.append(f'    {node_id}["{node_label}"]')
        
        # 添加边
        for edge in graph_data["edges"]:
            source = edge["source"]
            target = edge["target"]
            label = edge.get("condition", "")
            
            if edge["metadata"].get("style") == "dashed":
                line = f'    {source} -.->|"{label}"| {target}'
            else:
                line = f'    {source} -->|"{label}"| {target}'
            
            lines.append(line)
        
        return "\n".join(lines)


class MockWorkflowVisualizer(IWorkflowVisualizer):
    """模拟工作流可视化器（用于测试）"""

    def __init__(self) -> None:
        """初始化模拟可视化器"""
        self._studio_running = False

    def visualize_workflow(self, workflow_config: WorkflowConfig) -> str:
        """可视化工作流配置"""
        return f"mock://visualization/{workflow_config.name}"

    def start_studio(self, port: int = 8079) -> bool:
        """启动LangGraph Studio"""
        self._studio_running = True
        return True

    def stop_studio(self) -> bool:
        """停止LangGraph Studio"""
        self._studio_running = False
        return True

    def is_studio_running(self) -> bool:
        """检查Studio是否正在运行"""
        return self._studio_running

    def get_studio_url(self, port: int = 8079) -> str:
        """获取Studio URL"""
        return f"mock://localhost:{port}"


def create_visualizer(use_mock: bool = False, studio_port: int = 8079) -> IWorkflowVisualizer:
    """创建工作流可视化器

    Args:
        use_mock: 是否使用模拟可视化器
        studio_port: Studio端口

    Returns:
        IWorkflowVisualizer: 工作流可视化器实例
    """
    if use_mock:
        return MockWorkflowVisualizer()
    else:
        return LangGraphStudioVisualizer(studio_port)