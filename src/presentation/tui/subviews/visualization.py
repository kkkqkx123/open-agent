"""可视化调试子界面"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.columns import Columns
from rich.align import Align
from rich.box import Box

from .base import BaseSubview
from ..config import TUIConfig


class VisualizationSubview(BaseSubview):
    """可视化调试子界面
    
    包含工作流可视化、节点调试
    """
    
    def __init__(self, config: TUIConfig):
        """初始化可视化调试子界面
        
        Args:
            config: TUI配置
        """
        super().__init__(config)
        
        # 工作流数据
        self.workflow_data = {
            "nodes": [],
            "edges": [],
            "current_node": None,
            "execution_path": [],
            "node_states": {}
        }
        
        # 节点调试数据
        self.node_debug_data = {
            "selected_node": None,
            "node_input": {},
            "node_output": {},
            "node_metadata": {},
            "execution_time": 0.0
        }
        
        # 可视化设置
        self.visualization_settings = {
            "show_details": True,
            "show_execution_path": True,
            "auto_refresh": True,
            "refresh_interval": 1.0
        }
    
    def get_title(self) -> str:
        """获取子界面标题
        
        Returns:
            str: 子界面标题
        """
        return "🎨 可视化调试"
    
    def render(self) -> Panel:
        """渲染可视化调试子界面
        
        Returns:
            Panel: 子界面面板
        """
        # 创建主要内容
        content = self._create_main_content()
        
        # 创建面板
        panel = Panel(
            content,
            title=self.create_header(),
            border_style="cyan",
            subtitle=self.create_help_text()
        )
        
        return panel
    
    def _create_main_content(self) -> Columns:
        """创建主要内容区域
        
        Returns:
            Columns: 列布局
        """
        # 工作流可视化
        workflow_panel = self._create_workflow_panel()
        
        # 节点调试
        debug_panel = self._create_debug_panel()
        
        # 执行路径
        path_panel = self._create_execution_path_panel()
        
        # 组合布局
        return Columns([
            workflow_panel,
            debug_panel,
            path_panel
        ], equal=True)
    
    def _create_workflow_panel(self) -> Panel:
        """创建工作流可视化面板
        
        Returns:
            Panel: 工作流面板
        """
        if not self.workflow_data["nodes"]:
            return Panel(
                Text("暂无工作流数据", style="dim italic"),
                title="🔄 工作流可视化",
                border_style="dim"
            )
        
        # 创建工作流树形结构
        tree = Tree("工作流结构", style="bold cyan")
        
        # 添加节点
        nodes = self.workflow_data["nodes"]
        edges = self.workflow_data["edges"]
        current_node = self.workflow_data["current_node"]
        
        # 构建节点层次结构
        node_dict = {node["id"]: node for node in nodes}
        root_nodes = [node for node in nodes if not self._has_parent(node["id"], edges)]
        
        for root_node in root_nodes:
            self._add_node_to_tree(tree, root_node, node_dict, edges, current_node)
        
        return Panel(
            tree,
            title="🔄 工作流可视化",
            border_style="blue"
        )
    
    def _create_debug_panel(self) -> Panel:
        """创建节点调试面板
        
        Returns:
            Panel: 调试面板
        """
        selected_node = self.node_debug_data["selected_node"]
        
        if not selected_node:
            return Panel(
                Text("请选择一个节点进行调试", style="dim italic"),
                title="🐛 节点调试",
                border_style="dim"
            )
        
        # 创建调试信息表格
        table = Table(title=f"节点调试: {selected_node}", show_header=True, header_style="bold cyan")
        table.add_column("属性", style="bold")
        table.add_column("值", style="dim")
        
        # 节点基本信息
        debug_data = self.node_debug_data
        
        # 执行时间
        execution_time = debug_data["execution_time"]
        table.add_row("执行时间", f"{execution_time:.3f}s")
        
        # 节点输入
        node_input = debug_data["node_input"]
        if node_input:
            input_text = self._format_dict(node_input)
            table.add_row("输入", input_text)
        
        # 节点输出
        node_output = debug_data["node_output"]
        if node_output:
            output_text = self._format_dict(node_output)
            table.add_row("输出", output_text)
        
        # 节点元数据
        node_metadata = debug_data["node_metadata"]
        if node_metadata:
            metadata_text = self._format_dict(node_metadata)
            table.add_row("元数据", metadata_text)
        
        return Panel(
            table,
            title="🐛 节点调试",
            border_style="yellow"
        )
    
    def _create_execution_path_panel(self) -> Panel:
        """创建执行路径面板
        
        Returns:
            Panel: 执行路径面板
        """
        execution_path = self.workflow_data["execution_path"]
        
        if not execution_path:
            return Panel(
                Text("暂无执行路径", style="dim italic"),
                title="🛤️ 执行路径",
                border_style="dim"
            )
        
        # 创建执行路径表格
        table = Table(title="执行路径", show_header=True, header_style="bold cyan")
        table.add_column("步骤", style="bold", justify="right")
        table.add_column("节点", style="bold")
        table.add_column("状态", justify="center")
        table.add_column("时间", justify="right")
        table.add_column("耗时", justify="right")
        
        for i, step in enumerate(execution_path, 1):
            node_id = step.get("node_id", "unknown")
            status = step.get("status", "unknown")
            timestamp = step.get("timestamp", datetime.now())
            duration = step.get("duration", 0)
            
            # 格式化时间
            time_str = timestamp.strftime("%H:%M:%S")
            duration_str = f"{duration:.3f}s" if duration > 0 else "-"
            
            # 状态图标
            status_icon = self._get_status_icon(status)
            
            table.add_row(
                str(i),
                node_id,
                status_icon,
                time_str,
                duration_str
            )
        
        return Panel(
            table,
            title="🛤️ 执行路径",
            border_style="magenta"
        )
    
    def _has_parent(self, node_id: str, edges: List[Dict[str, Any]]) -> bool:
        """检查节点是否有父节点
        
        Args:
            node_id: 节点ID
            edges: 边列表
            
        Returns:
            bool: 是否有父节点
        """
        for edge in edges:
            if edge["target"] == node_id:
                return True
        return False
    
    def _add_node_to_tree(
        self,
        parent_tree: Tree,
        node: Dict[str, Any],
        node_dict: Dict[str, Dict[str, Any]],
        edges: List[Dict[str, Any]],
        current_node: Optional[str]
    ) -> None:
        """添加节点到树形结构
        
        Args:
            parent_tree: 父树
            node: 节点数据
            node_dict: 节点字典
            edges: 边列表
            current_node: 当前节点ID
        """
        node_id = node["id"]
        node_type = node.get("type", "unknown")
        node_status = self.workflow_data["node_states"].get(node_id, "idle")
        
        # 确定节点样式
        if node_id == current_node:
            style = "bold green"
            prefix = "🟢 "
        elif node_status == "running":
            style = "bold yellow"
            prefix = "🟡 "
        elif node_status == "completed":
            style = "green"
            prefix = "✅ "
        elif node_status == "failed":
            style = "red"
            prefix = "❌ "
        else:
            style = "dim"
            prefix = "⚪ "
        
        # 创建节点文本
        node_text = f"{prefix}{node_id} ({node_type})"
        
        # 添加节点到树
        node_tree = parent_tree.add(node_text, style=style)
        
        # 添加节点详情
        if self.visualization_settings["show_details"]:
            if "description" in node:
                node_tree.add(f"描述: {node['description']}", style="dim")
            
            if "parameters" in node:
                params_text = self._format_dict(node["parameters"])
                node_tree.add(f"参数: {params_text}", style="dim")
        
        # 递归添加子节点
        child_edges = [edge for edge in edges if edge["source"] == node_id]
        for edge in child_edges:
            child_node_id = edge["target"]
            if child_node_id in node_dict:
                child_node = node_dict[child_node_id]
                self._add_node_to_tree(node_tree, child_node, node_dict, edges, current_node)
    
    def _format_dict(self, data: Dict[str, Any], max_length: int = 50) -> str:
        """格式化字典数据
        
        Args:
            data: 字典数据
            max_length: 最大长度
            
        Returns:
            str: 格式化后的字符串
        """
        if not data:
            return "空"
        
        # 简化显示
        items = []
        for key, value in list(data.items())[:3]:  # 只显示前3个键值对
            if isinstance(value, str) and len(value) > 20:
                value = value[:17] + "..."
            items.append(f"{key}={value}")
        
        result = ", ".join(items)
        
        # 如果数据太多，添加省略号
        if len(data) > 3:
            result += "..."
        
        # 限制总长度
        if len(result) > max_length:
            result = result[:max_length-3] + "..."
        
        return result
    
    def _get_status_icon(self, status: str) -> str:
        """获取状态图标
        
        Args:
            status: 状态
            
        Returns:
            str: 状态图标
        """
        icons = {
            "idle": "⚪",
            "running": "🟡",
            "completed": "✅",
            "failed": "❌",
            "pending": "⏳",
            "skipped": "⏭️"
        }
        return icons.get(status, "❓")
    
    def update_workflow_data(self, data: Dict[str, Any]) -> None:
        """更新工作流数据
        
        Args:
            data: 工作流数据
        """
        self.workflow_data.update(data)
    
    def update_node_debug_data(self, data: Dict[str, Any]) -> None:
        """更新节点调试数据
        
        Args:
            data: 节点调试数据
        """
        self.node_debug_data.update(data)
    
    def select_node(self, node_id: str) -> None:
        """选择节点进行调试
        
        Args:
            node_id: 节点ID
        """
        self.node_debug_data["selected_node"] = node_id
        
        # 这里可以添加获取节点详细信息的逻辑
        # 例如：从工作流数据中获取节点的输入、输出等
        self._load_node_debug_info(node_id)
    
    def _load_node_debug_info(self, node_id: str) -> None:
        """加载节点调试信息
        
        Args:
            node_id: 节点ID
        """
        # 从工作流数据中查找节点
        nodes = self.workflow_data["nodes"]
        node = next((n for n in nodes if n["id"] == node_id), None)
        
        if node:
            # 更新节点调试数据
            self.node_debug_data["node_metadata"] = {
                "type": node.get("type", "unknown"),
                "description": node.get("description", ""),
                "parameters": node.get("parameters", {})
            }
    
    def handle_key(self, key: str) -> bool:
        """处理键盘输入
        
        Args:
            key: 按键
            
        Returns:
            bool: True表示已处理，False表示需要传递到上层
        """
        if key == "escape":
            return True
        
        # 可以添加其他快捷键处理
        if key == "d":
            # 切换详细信息显示
            self.visualization_settings["show_details"] = not self.visualization_settings["show_details"]
            return True
        
        if key == "p":
            # 切换执行路径显示
            self.visualization_settings["show_execution_path"] = not self.visualization_settings["show_execution_path"]
            return True
        
        if key == "r":
            # 刷新数据
            self._refresh_data()
            return True
        
        return super().handle_key(key)
    
    def _refresh_data(self) -> None:
        """刷新数据"""
        # 这里可以添加数据刷新逻辑
        # 例如：重新获取工作流状态、节点信息等
        pass