"""工作流控制组件

包含工作流暂停/继续/终止功能和状态监控
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.tree import Tree

from ..config import TUIConfig
from ....interfaces.state.workflow import IWorkflowState as InfraWorkflowState


class WorkflowState(Enum):
    """工作流状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


class WorkflowController:
    """工作流控制器"""
    
    def __init__(self):
        self.state = WorkflowState.IDLE
        self.current_step = ""
        self.total_steps = 0
        self.completed_steps = 0
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
        self.error_message = ""
        self.execution_history: List[Dict[str, Any]] = []
        
        # 回调函数
        self.on_state_changed: Optional[Callable[[WorkflowState], None]] = None
        self.on_step_completed: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def set_state_changed_callback(self, callback: Callable[[WorkflowState], None]) -> None:
        """设置状态变化回调
        
        Args:
            callback: 回调函数
        """
        self.on_state_changed = callback
    
    def set_step_completed_callback(self, callback: Callable[[str], None]) -> None:
        """设置步骤完成回调
        
        Args:
            callback: 回调函数
        """
        self.on_step_completed = callback
    
    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """设置错误回调
        
        Args:
            callback: 回调函数
        """
        self.on_error = callback
    
    def start_workflow(self, total_steps: int = 0) -> None:
        """启动工作流
        
        Args:
            total_steps: 总步骤数
        """
        self.state = WorkflowState.RUNNING
        self.total_steps = total_steps
        self.completed_steps = 0
        self.start_time = datetime.now()
        self.pause_time = None
        self.error_message = ""
        self.execution_history = []
        
        if self.on_state_changed:
            self.on_state_changed(self.state)
    
    def pause_workflow(self) -> bool:
        """暂停工作流
        
        Returns:
            bool: 是否成功暂停
        """
        if self.state == WorkflowState.RUNNING:
            self.state = WorkflowState.PAUSED
            self.pause_time = datetime.now()
            
            # 记录暂停事件
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "event": "paused",
                "step": self.current_step,
                "completed_steps": self.completed_steps
            })
            
            if self.on_state_changed:
                self.on_state_changed(self.state)
            return True
        return False
    
    def resume_workflow(self) -> bool:
        """恢复工作流
        
        Returns:
            bool: 是否成功恢复
        """
        if self.state == WorkflowState.PAUSED:
            self.state = WorkflowState.RUNNING
            self.pause_time = None
            
            # 记录恢复事件
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "event": "resumed",
                "step": self.current_step,
                "completed_steps": self.completed_steps
            })
            
            if self.on_state_changed:
                self.on_state_changed(self.state)
            return True
        return False
    
    def stop_workflow(self) -> bool:
        """停止工作流
        
        Returns:
            bool: 是否成功停止
        """
        if self.state in [WorkflowState.RUNNING, WorkflowState.PAUSED]:
            self.state = WorkflowState.STOPPED
            
            # 记录停止事件
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "event": "stopped",
                "step": self.current_step,
                "completed_steps": self.completed_steps
            })
            
            if self.on_state_changed:
                self.on_state_changed(self.state)
            return True
        return False
    
    def complete_workflow(self) -> None:
        """完成工作流"""
        self.state = WorkflowState.COMPLETED
        
        # 记录完成事件
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": "completed",
            "step": self.current_step,
            "completed_steps": self.completed_steps
        })
        
        if self.on_state_changed:
            self.on_state_changed(self.state)
    
    def set_error(self, error_message: str) -> None:
        """设置错误状态
        
        Args:
            error_message: 错误消息
        """
        self.state = WorkflowState.ERROR
        self.error_message = error_message
        
        # 记录错误事件
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "step": self.current_step,
            "error": error_message
        })
        
        if self.on_error:
            self.on_error(error_message)
        if self.on_state_changed:
            self.on_state_changed(self.state)
    
    def update_step(self, step_name: str) -> None:
        """更新当前步骤
        
        Args:
            step_name: 步骤名称
        """
        self.current_step = step_name
        
        # 记录步骤开始
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": "step_started",
            "step": step_name
        })
    
    def complete_step(self) -> None:
        """完成当前步骤"""
        self.completed_steps += 1
        
        # 记录步骤完成
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "event": "step_completed",
            "step": self.current_step,
            "completed_steps": self.completed_steps
        })
        
        if self.on_step_completed:
            self.on_step_completed(self.current_step)
    
    def get_elapsed_time(self) -> float:
        """获取已用时间（秒）
        
        Returns:
            float: 已用时间
        """
        if not self.start_time:
            return 0.0
        
        end_time = self.pause_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比
        
        Returns:
            float: 进度百分比
        """
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100
    
    def get_state_text(self) -> str:
        """获取状态文本
        
        Returns:
            str: 状态文本
        """
        state_texts = {
            WorkflowState.IDLE: "空闲",
            WorkflowState.RUNNING: "运行中",
            WorkflowState.PAUSED: "已暂停",
            WorkflowState.COMPLETED: "已完成",
            WorkflowState.ERROR: "错误",
            WorkflowState.STOPPED: "已停止"
        }
        return state_texts.get(self.state, "未知")
    
    def get_state_style(self) -> str:
        """获取状态样式
        
        Returns:
            str: 状态样式
        """
        state_styles = {
            WorkflowState.IDLE: "dim",
            WorkflowState.RUNNING: "green",
            WorkflowState.PAUSED: "yellow",
            WorkflowState.COMPLETED: "blue",
            WorkflowState.ERROR: "red",
            WorkflowState.STOPPED: "orange3"
        }
        return state_styles.get(self.state, "white")


class WorkflowControlPanel:
    """工作流控制面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.controller = WorkflowController()
        
        # 设置控制器回调
        self.controller.set_state_changed_callback(self._on_state_changed)
        self.controller.set_step_completed_callback(self._on_step_completed)
        self.controller.set_error_callback(self._on_error)
        
        # 外部回调
        self.on_control_action: Optional[Callable[[str], None]] = None
    
    def set_control_action_callback(self, callback: Callable[[str], None]) -> None:
        """设置控制动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_control_action = callback
    
    def _on_state_changed(self, state: WorkflowState) -> None:
        """状态变化处理"""
        # 这里可以添加状态变化的UI更新逻辑
        pass
    
    def _on_step_completed(self, step_name: str) -> None:
        """步骤完成处理"""
        # 这里可以添加步骤完成的UI更新逻辑
        pass
    
    def _on_error(self, error_message: str) -> None:
        """错误处理"""
        # 这里可以添加错误的UI更新逻辑
        pass
    
    def handle_action(self, action: str) -> bool:
        """处理控制动作
        
        Args:
            action: 动作名称
            
        Returns:
            bool: 是否成功处理
        """
        if action == "start":
            self.controller.start_workflow()
        elif action == "pause":
            return self.controller.pause_workflow()
        elif action == "resume":
            return self.controller.resume_workflow()
        elif action == "stop":
            return self.controller.stop_workflow()
        elif action == "complete":
            self.controller.complete_workflow()
        else:
            return False
        
        if self.on_control_action:
            self.on_control_action(action)
        return True
    
    def update_from_agent_state(self, state: Optional[InfraWorkflowState]) -> None:
        """从工作流状态更新
        
        Args:
            state: Agent状态
        """
        if state:
            self.controller.update_step(state.get('current_step') or '')
            self.controller.completed_steps = state.get('iteration_count', 0)
            self.controller.total_steps = state.get('max_iterations', 0)
            
            # 根据迭代状态更新工作流状态
            if state.get('iteration_count', 0) >= state.get('max_iterations', 0):
                self.controller.complete_workflow()
            elif self.controller.state == WorkflowState.IDLE:
                self.controller.start_workflow(state.get('max_iterations', 0))
    
    def render(self) -> Panel:
        """渲染控制面板
        
        Returns:
            Panel: 控制面板
        """
        # 创建控制按钮表格
        control_table = Table(
            title="工作流控制",
            show_header=False,
            box=None,
            padding=0
        )
        control_table.add_column("按钮", style="bold")
        control_table.add_column("状态", style="dim")
        
        # 根据当前状态显示可用按钮
        if self.controller.state == WorkflowState.IDLE:
            control_table.add_row("[Start]", "启动工作流")
        elif self.controller.state == WorkflowState.RUNNING:
            control_table.add_row("[Pause]", "暂停工作流")
            control_table.add_row("[Stop]", "停止工作流")
        elif self.controller.state == WorkflowState.PAUSED:
            control_table.add_row("[Resume]", "恢复工作流")
            control_table.add_row("[Stop]", "停止工作流")
        elif self.controller.state in [WorkflowState.COMPLETED, WorkflowState.ERROR, WorkflowState.STOPPED]:
            control_table.add_row("[Restart]", "重新开始")
        
        # 创建状态信息
        status_text = Text()
        status_text.append("状态: ", style="bold")
        status_text.append(
            self.controller.get_state_text(),
            style=self.controller.get_state_style()
        )
        
        if self.controller.current_step:
            status_text.append(f"\\n当前步骤: {self.controller.current_step}")
        
        if self.controller.total_steps > 0:
            # 计算进度百分比
            percentage = (self.controller.completed_steps / self.controller.total_steps) * 100
            # 创建简单的进度条文本表示
            bar_width = 20
            filled_width = int(bar_width * self.controller.completed_steps / self.controller.total_steps)
            bar = "█" * filled_width + "░" * (bar_width - filled_width)
            
            status_text.append("\\n")
            status_text.append(f"进度: {bar} {percentage:.0f}% ({self.controller.completed_steps}/{self.controller.total_steps})")
        
        # 显示时间信息
        if self.controller.start_time:
            elapsed = self.controller.get_elapsed_time()
            minutes, seconds = divmod(int(elapsed), 60)
            status_text.append(f"\\n运行时间: {minutes}分{seconds}秒")
        
        # 显示错误信息
        if self.controller.state == WorkflowState.ERROR and self.controller.error_message:
            status_text.append(f"\\n错误: {self.controller.error_message}", style="red")
        
        # 组合内容
        content = Table.grid()
        content.add_column()
        content.add_row(control_table)
        content.add_row("")
        content.add_row(status_text)
        
        return Panel(
            content,
            title="工作流控制",
            border_style="cyan",
            padding=(1, 1)
        )