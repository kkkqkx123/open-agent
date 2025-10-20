"""侧边栏组件

包含Agent信息显示、工作流状态监控和指标统计展示
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align

from src.prompts.agent_state import AgentState
from ..config import TUIConfig


class AgentInfoSection:
    """Agent信息显示组件"""
    
    def __init__(self):
        self.agent_name = "默认Agent"
        self.agent_model = "gpt-3.5-turbo"
        self.agent_tools = []
        self.agent_status = "就绪"
    
    def update_agent_info(self, name: str, model: str, tools: List[str], status: str = "就绪") -> None:
        """更新Agent信息
        
        Args:
            name: Agent名称
            model: 模型名称
            tools: 工具列表
            status: Agent状态
        """
        self.agent_name = name
        self.agent_model = model
        self.agent_tools = tools
        self.agent_status = status
    
    def render(self) -> Tree:
        """渲染Agent信息
        
        Returns:
            Tree: Agent信息树形结构
        """
        tree = Tree("🤖 Agent信息", style="bold cyan")
        
        # 基本信息
        basic_info = tree.add("📋 基本信息")
        basic_info.add(f"名称: {self.agent_name}")
        basic_info.add(f"模型: {self.agent_model}")
        basic_info.add(f"状态: {self._get_status_text(self.agent_status)}")
        
        # 工具信息
        if self.agent_tools:
            tools_info = tree.add("🔧 可用工具")
            for tool in self.agent_tools[:5]:  # 最多显示5个工具
                tools_info.add(f"• {tool}")
            if len(self.agent_tools) > 5:
                tools_info.add(f"... 还有 {len(self.agent_tools) - 5} 个工具")
        else:
            tree.add("🔧 无可用工具")
        
        return tree
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本
        
        Args:
            status: 状态字符串
            
        Returns:
            str: 带样式的状态文本
        """
        status_styles = {
            "就绪": "green",
            "运行中": "yellow",
            "忙碌": "orange3",
            "错误": "red",
            "离线": "dim"
        }
        style = status_styles.get(status, "white")
        return f"[{style}]{status}[/{style}]"


class WorkflowStatusSection:
    """工作流状态监控组件"""
    
    def __init__(self):
        self.workflow_name = "未加载"
        self.current_node = "无"
        self.execution_path: List[str] = []
        self.workflow_status = "未启动"
        self.iteration_count = 0
        self.max_iterations = 10
    
    def update_workflow_status(
        self,
        name: str,
        current_node: str,
        execution_path: List[str],
        status: str,
        iteration_count: int = 0,
        max_iterations: int = 10
    ) -> None:
        """更新工作流状态
        
        Args:
            name: 工作流名称
            current_node: 当前节点
            execution_path: 执行路径
            status: 工作流状态
            iteration_count: 当前迭代次数
            max_iterations: 最大迭代次数
        """
        self.workflow_name = name
        self.current_node = current_node
        self.execution_path = execution_path
        self.workflow_status = status
        self.iteration_count = iteration_count
        self.max_iterations = max_iterations
    
    def render(self) -> Tree:
        """渲染工作流状态
        
        Returns:
            Tree: 工作流状态树形结构
        """
        tree = Tree("⚙️ 工作流状态", style="bold green")
        
        # 基本信息
        basic_info = tree.add("📊 基本信息")
        basic_info.add(f"名称: {self.workflow_name}")
        basic_info.add(f"状态: {self._get_status_text(self.workflow_status)}")
        
        # 执行信息
        if self.workflow_status != "未启动":
            exec_info = tree.add("🔄 执行信息")
            exec_info.add(f"当前节点: {self.current_node}")
            
            # 迭代进度
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            )
            progress.add_task(
                "迭代进度",
                completed=self.iteration_count,
                total=self.max_iterations
            )
            exec_info.add(progress)
            
            # 执行路径
            if self.execution_path:
                path_info = tree.add("🛤️ 执行路径")
                # 显示最近5个节点
                recent_path = self.execution_path[-5:]
                for i, node in enumerate(recent_path):
                    if i == len(recent_path) - 1:  # 当前节点
                        path_info.add(f"→ {node}", style="bold yellow")
                    else:
                        path_info.add(f"  {node}")
        
        return tree
    
    def _get_status_text(self, status: str) -> str:
        """获取状态文本
        
        Args:
            status: 状态字符串
            
        Returns:
            str: 带样式的状态文本
        """
        status_styles = {
            "未启动": "dim",
            "运行中": "green",
            "暂停": "yellow",
            "完成": "blue",
            "错误": "red",
            "停止": "orange3"
        }
        style = status_styles.get(status, "white")
        return f"[{style}]{status}[/{style}]"


class MetricsSection:
    """指标统计展示组件"""
    
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.successful_tools = 0
        self.failed_tools = 0
        self.session_duration = 0
        self.message_count = 0
        self.start_time: Optional[datetime] = None
    
    def update_metrics(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        successful_tools: int = 0,
        failed_tools: int = 0,
        message_count: int = 0
    ) -> None:
        """更新指标
        
        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数
            successful_tools: 成功工具调用数
            failed_tools: 失败工具调用数
            message_count: 消息数量
        """
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.successful_tools = successful_tools
        self.failed_tools = failed_tools
        self.message_count = message_count
        
        if not self.start_time:
            self.start_time = datetime.now()
    
    def render(self) -> Tree:
        """渲染指标统计
        
        Returns:
            Tree: 指标统计树形结构
        """
        tree = Tree("📈 指标统计", style="bold magenta")
        
        # Token使用情况
        token_info = tree.add("🔤 Token使用")
        token_info.add(f"输入: {self.input_tokens:,}")
        token_info.add(f"输出: {self.output_tokens:,}")
        token_info.add(f"总计: {self.input_tokens + self.output_tokens:,}")
        
        # 工具调用情况
        tool_info = tree.add("🔧 工具调用")
        tool_info.add(f"成功: [green]{self.successful_tools}[/green]")
        tool_info.add(f"失败: [red]{self.failed_tools}[/red]")
        total_tools = self.successful_tools + self.failed_tools
        if total_tools > 0:
            success_rate = (self.successful_tools / total_tools) * 100
            tool_info.add(f"成功率: {success_rate:.1f}%")
        
        # 会话信息
        session_info = tree.add("💬 会话信息")
        session_info.add(f"消息数: {self.message_count}")
        
        # 计算会话时长
        if self.start_time:
            duration = datetime.now() - self.start_time
            minutes, seconds = divmod(int(duration.total_seconds()), 60)
            session_info.add(f"时长: {minutes}分{seconds}秒")
        
        return tree


class SidebarComponent:
    """侧边栏组件
    
    包含Agent信息显示、工作流状态监控和指标统计展示
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        """初始化侧边栏组件
        
        Args:
            config: TUI配置
        """
        self.config = config
        self.agent_info = AgentInfoSection()
        self.workflow_status = WorkflowStatusSection()
        self.metrics = MetricsSection()
    
    def update_from_state(self, state: Optional[AgentState] = None) -> None:
        """从Agent状态更新组件
        
        Args:
            state: Agent状态
        """
        if state:
            # 更新指标
            self.metrics.update_metrics(
                message_count=len(state.messages),
                successful_tools=sum(1 for result in state.tool_results if result.success),
                failed_tools=sum(1 for result in state.tool_results if not result.success)
            )
            
            # 更新工作流状态
            self.workflow_status.update_workflow_status(
                name="当前工作流",
                current_node=getattr(state, 'current_step', '未知'),
                execution_path=getattr(state, 'execution_path', []),
                status="运行中" if state.iteration_count < state.max_iterations else "完成",
                iteration_count=state.iteration_count,
                max_iterations=state.max_iterations
            )
    
    def render(self) -> Panel:
        """渲染侧边栏
        
        Returns:
            Panel: 侧边栏面板
        """
        # 创建内容组
        content_tree = Tree("状态面板", style="bold", guide_style="dim")
        
        # 添加各个部分
        agent_tree = self.agent_info.render()
        workflow_tree = self.workflow_status.render()
        metrics_tree = self.metrics.render()
        
        # 将子树添加到主树
        content_tree.add(agent_tree)
        content_tree.add(workflow_tree)
        content_tree.add(metrics_tree)
        
        # 创建面板
        panel = Panel(
            content_tree,
            title="状态面板",
            border_style="blue" if self.config else "blue",
            padding=(0, 1)
        )
        
        return panel