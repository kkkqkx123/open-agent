"""实时工作流可视化组件

包含工作流节点可视化、执行路径跟踪和状态监控功能
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from enum import Enum
import asyncio

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.layout import Layout
from rich.columns import Columns

from ..config import TUIConfig
from ....interfaces.state.workflow import IWorkflowState as WorkflowState


class NodeType(Enum):
    """节点类型枚举"""
    START = "start"
    PROCESS = "process"
    DECISION = "decision"
    TOOL = "tool"
    END = "end"
    ERROR = "error"


class NodeStatus(Enum):
    """节点状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowNode:
    """工作流节点"""
    
    def __init__(
        self,
        node_id: str,
        name: str,
        node_type: NodeType,
        position: Tuple[int, int] = (0, 0),
        description: str = ""
    ):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self.position = position
        self.description = description
        self.status = NodeStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: float = 0.0
        self.error_message = ""
        self.input_data: Dict[str, Any] = {}
        self.output_data: Dict[str, Any] = {}
        self.children: List[str] = []
        self.parents: List[str] = []
    
    def start_execution(self) -> None:
        """开始执行"""
        self.status = NodeStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete_execution(self, output_data: Optional[Dict[str, Any]] = None) -> None:
        """完成执行"""
        self.status = NodeStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        if output_data:
            self.output_data.update(output_data)
    
    def fail_execution(self, error_message: str) -> None:
        """执行失败"""
        self.status = NodeStatus.FAILED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.error_message = error_message
    
    def get_status_style(self) -> str:
        """获取状态样式
        
        Returns:
            str: 样式字符串
        """
        styles = {
            NodeStatus.IDLE: "dim",
            NodeStatus.RUNNING: "yellow",
            NodeStatus.COMPLETED: "green",
            NodeStatus.FAILED: "red",
            NodeStatus.SKIPPED: "blue"
        }
        return styles.get(self.status, "white")
    
    def get_type_symbol(self) -> str:
        """获取类型符号
        
        Returns:
            str: 类型符号
        """
        symbols = {
            NodeType.START: "🚀",
            NodeType.PROCESS: "⚙️",
            NodeType.DECISION: "🔀",
            NodeType.TOOL: "🔧",
            NodeType.END: "🏁",
            NodeType.ERROR: "❌"
        }
        return symbols.get(self.node_type, "📦")


class WorkflowGraph:
    """工作流图"""
    
    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[Tuple[str, str]] = []
        self.current_path: List[str] = []
        self.execution_history: List[Dict[str, Any]] = []
    
    def add_node(self, node: WorkflowNode) -> None:
        """添加节点
        
        Args:
            node: 工作流节点
        """
        self.nodes[node.node_id] = node
    
    def add_edge(self, from_node: str, to_node: str) -> None:
        """添加边
        
        Args:
            from_node: 源节点ID
            to_node: 目标节点ID
        """
        self.edges.append((from_node, to_node))
        
        # 更新节点的父子关系
        if from_node in self.nodes:
            self.nodes[from_node].children.append(to_node)
        if to_node in self.nodes:
            self.nodes[to_node].parents.append(from_node)
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """获取节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            Optional[WorkflowNode]: 节点对象
        """
        return self.nodes.get(node_id)
    
    def update_current_path(self, path: List[str]) -> None:
        """更新当前执行路径
        
        Args:
            path: 执行路径
        """
        self.current_path = path
        
        # 记录路径变化
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "path": path.copy(),
            "event": "path_updated"
        })
    
    def start_node(self, node_id: str) -> None:
        """开始执行节点
        
        Args:
            node_id: 节点ID
        """
        node = self.get_node(node_id)
        if node:
            node.start_execution()
            
            # 记录节点开始
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "node_id": node_id,
                "event": "node_started"
            })
    
    def complete_node(self, node_id: str, output_data: Optional[Dict[str, Any]] = None) -> None:
        """完成节点执行
        
        Args:
            node_id: 节点ID
            output_data: 输出数据
        """
        node = self.get_node(node_id)
        if node:
            node.complete_execution(output_data)
            
            # 记录节点完成
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "node_id": node_id,
                "event": "node_completed",
                "duration": node.duration
            })
    
    def fail_node(self, node_id: str, error_message: str) -> None:
        """节点执行失败
        
        Args:
            node_id: 节点ID
            error_message: 错误消息
        """
        node = self.get_node(node_id)
        if node:
            node.fail_execution(error_message)
            
            # 记录节点失败
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "node_id": node_id,
                "event": "node_failed",
                "error": error_message
            })
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_nodes = len(self.nodes)
        completed_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.COMPLETED])
        failed_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.FAILED])
        running_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.RUNNING])
        
        total_duration = sum(n.duration for n in self.nodes.values() if n.duration > 0)
        
        return {
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "failed_nodes": failed_nodes,
            "running_nodes": running_nodes,
            "completion_rate": (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0,
            "total_duration": total_duration,
            "current_path_length": len(self.current_path)
        }


class WorkflowVisualizer:
    """工作流可视化器"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.graph = WorkflowGraph()
        self.auto_refresh = True
        self.refresh_interval = 1.0
        self.show_details = False
        self.selected_node: Optional[str] = None
        
        # 创建默认工作流
        self._create_default_workflow()
    
    def _create_default_workflow(self) -> None:
        """创建默认工作流"""
        # 创建节点
        start_node = WorkflowNode("start", "开始", NodeType.START, (0, 0))
        input_node = WorkflowNode("input", "输入处理", NodeType.PROCESS, (2, 0))
        think_node = WorkflowNode("think", "思考分析", NodeType.PROCESS, (4, 0))
        tool_node = WorkflowNode("tool", "工具调用", NodeType.TOOL, (6, 0))
        decision_node = WorkflowNode("decision", "决策判断", NodeType.DECISION, (8, 0))
        output_node = WorkflowNode("output", "输出结果", NodeType.PROCESS, (10, 0))
        end_node = WorkflowNode("end", "结束", NodeType.END, (12, 0))
        
        # 添加节点到图
        for node in [start_node, input_node, think_node, tool_node, decision_node, output_node, end_node]:
            self.graph.add_node(node)
        
        # 添加边
        edges = [
            ("start", "input"),
            ("input", "think"),
            ("think", "tool"),
            ("tool", "decision"),
            ("decision", "output"),
            ("output", "end")
        ]
        
        for from_node, to_node in edges:
            self.graph.add_edge(from_node, to_node)
    
    def update_from_agent_state(self, state: Optional[WorkflowState]) -> None:
        """从工作流状态更新
        
        Args:
            state: Agent状态
        """
        if not state:
            return
        
        # 更新当前路径
        current_step = state.get('current_step') if state else None
        if current_step:
            # 简单的路径映射
            step_mapping = {
                "input": "input",
                "think": "think",
                "tool_call": "tool",
                "decision": "decision",
                "output": "output"
            }
            
            node_id = step_mapping.get(current_step, current_step)
            if node_id and node_id not in self.graph.current_path:
                self.graph.current_path.append(node_id)
                self.graph.start_node(node_id)
        
        # 更新节点状态
        for node_id in self.graph.current_path:
            node = self.graph.get_node(node_id)
            if node and node.status == NodeStatus.RUNNING:
                # 如果是最后一步，标记为完成
                if node_id == self.graph.current_path[-1]:
                    self.graph.complete_node(node_id)
    
    def toggle_details(self) -> None:
        """切换详情显示"""
        self.show_details = not self.show_details
    
    def select_node(self, node_id: str) -> None:
        """选择节点
        
        Args:
            node_id: 节点ID
        """
        if node_id in self.graph.nodes:
            self.selected_node = node_id
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "d":
            self.toggle_details()
        elif key == "r":
            self._reset_workflow()
        elif key == "left":
            self._navigate_nodes(-1)
        elif key == "right":
            self._navigate_nodes(1)
        
        return None
    
    def _reset_workflow(self) -> None:
        """重置工作流"""
        for node in self.graph.nodes.values():
            node.status = NodeStatus.IDLE
            node.start_time = None
            node.end_time = None
            node.duration = 0.0
            node.error_message = ""
        
        self.graph.current_path = []
        self.graph.execution_history = []
    
    def _navigate_nodes(self, direction: int) -> None:
        """导航节点
        
        Args:
            direction: 方向 (-1=左, 1=右)
        """
        node_ids = list(self.graph.nodes.keys())
        if not node_ids:
            return
        
        if self.selected_node is None:
            self.selected_node = node_ids[0]
        else:
            try:
                current_index = node_ids.index(self.selected_node)
                new_index = (current_index + direction) % len(node_ids)
                self.selected_node = node_ids[new_index]
            except ValueError:
                self.selected_node = node_ids[0]
    
    def render(self) -> Panel:
        """渲染可视化面板
        
        Returns:
            Panel: 可视化面板
        """
        # 创建布局
        layout = Layout()
        
        if self.show_details:
            # 详细视图：上下分割
            layout.split_column(
                Layout(name="graph", ratio=2),
                Layout(name="details", ratio=1)
            )
            
            # 渲染图和详情
            graph_content = self._render_graph()
            details_content = self._render_details()
            
            layout["graph"].update(graph_content)
            layout["details"].update(details_content)
            
            content = layout
        else:
            # 简单视图：只显示图
            content = self._render_graph()
        
        return Panel(
            content,
            title="工作流可视化 (D=详情, R=重置, ←→=导航)",
            border_style="magenta",
            padding=(1, 1)
        )
    
    def _render_graph(self) -> Table:
        """渲染工作流图
        
        Returns:
            Table: 工作流图表格
        """
        table = Table(show_header=False, box=None, padding=0)
        table.add_column()
        
        # 创建节点行
        node_row = Text()
        
        # 按位置排序节点
        sorted_nodes = sorted(
            self.graph.nodes.values(),
            key=lambda n: n.position[0]
        )
        
        for i, node in enumerate(sorted_nodes):
            # 节点符号和状态
            symbol = node.get_type_symbol()
            status_style = node.get_status_style()
            
            # 高亮当前路径中的节点
            if node.node_id in self.graph.current_path:
                node_row.append(f"[{status_style} bold]{symbol}[/{status_style} bold]")
            elif node.node_id == self.selected_node:
                node_row.append(f"[{status_style} reverse]{symbol}[/{status_style} reverse]")
            else:
                node_row.append(f"[{status_style}]{symbol}[/{status_style}]")
            
            # 节点名称
            node_row.append(f" {node.name}")
            
            # 添加连接箭头
            if i < len(sorted_nodes) - 1:
                next_node = sorted_nodes[i + 1]
                if (node.node_id, next_node.node_id) in self.graph.edges:
                    node_row.append(" → ")
                else:
                    node_row.append("   ")
        
        table.add_row(node_row)
        
        # 添加状态行
        status_row = Text()
        for i, node in enumerate(sorted_nodes):
            status_text = node.status.value.upper()
            status_style = node.get_status_style()
            
            status_row.append(f"[{status_style}]{status_text[:3]}[/{status_style}]")
            
            if i < len(sorted_nodes) - 1:
                status_row.append("   ")
        
        table.add_row("")
        table.add_row(status_row)
        
        # 添加统计信息
        stats = self.graph.get_statistics()
        stats_text = Text()
        stats_text.append(f"节点: {stats['completed_nodes']}/{stats['total_nodes']} ")
        stats_text.append(f"完成率: {stats['completion_rate']:.1f}% ")
        stats_text.append(f"总耗时: {stats['total_duration']:.1f}s")
        
        table.add_row("")
        table.add_row(stats_text)
        
        return table
    
    def _render_details(self) -> Table:
        """渲染详细信息
        
        Returns:
            Table: 详细信息表格
        """
        table = Table(
            title="节点详情",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("属性", style="bold")
        table.add_column("值", style="white")
        
        if self.selected_node and self.selected_node in self.graph.nodes:
            node = self.graph.nodes[self.selected_node]
            
            table.add_row("节点ID", node.node_id)
            table.add_row("名称", node.name)
            table.add_row("类型", node.node_type.value)
            table.add_row("状态", f"[{node.get_status_style()}]{node.status.value}[/{node.get_status_style()}]")
            
            if node.start_time:
                table.add_row("开始时间", node.start_time.strftime("%H:%M:%S"))
            
            if node.end_time:
                table.add_row("结束时间", node.end_time.strftime("%H:%M:%S"))
            
            if node.duration > 0:
                table.add_row("执行时长", f"{node.duration:.2f}秒")
            
            if node.error_message:
                table.add_row("错误信息", f"[red]{node.error_message}[/red]")
            
            if node.description:
                table.add_row("描述", node.description)
        else:
            table.add_row("提示", "请选择一个节点查看详情")
        
        return table