"""节点调试界面组件

包含节点状态检查、断点设置、变量查看和执行控制功能
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
import json

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.syntax import Syntax
from rich.columns import Columns
from rich.layout import Layout

from ..config import TUIConfig
from ....interfaces.state.workflow import IWorkflowState as WorkflowState


class DebugMode(Enum):
    """调试模式枚举"""
    OFF = "off"
    STEP = "step"
    BREAKPOINT = "breakpoint"
    TRACE = "trace"


class Breakpoint:
    """断点"""
    
    def __init__(self, node_id: str, condition: Optional[str] = None, enabled: bool = True):
        self.node_id = node_id
        self.condition = condition
        self.enabled = enabled
        self.hit_count = 0
        self.created_at = datetime.now()
    
    def should_break(self, context: Dict[str, Any]) -> bool:
        """检查是否应该断点
        
        Args:
            context: 执行上下文
            
        Returns:
            bool: 是否应该断点
        """
        if not self.enabled:
            return False
        
        self.hit_count += 1
        
        if not self.condition:
            return True
        
        # 简单的条件评估（实际应用中可能需要更安全的表达式评估）
        try:
            return eval(self.condition, {}, context)
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 断点信息字典
        """
        return {
            "node_id": self.node_id,
            "condition": self.condition,
            "enabled": self.enabled,
            "hit_count": self.hit_count,
            "created_at": self.created_at.isoformat()
        }


class DebugContext:
    """调试上下文"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.call_stack: List[Dict[str, Any]] = []
        self.messages: List[Dict[str, Any]] = []
        self.current_node: Optional[str] = None
        self.step_count = 0
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量
        
        Args:
            name: 变量名
            value: 变量值
        """
        self.variables[name] = value
    
    def get_variable(self, name: str) -> Any:
        """获取变量
        
        Args:
            name: 变量名
            
        Returns:
            Any: 变量值
        """
        return self.variables.get(name)
    
    def push_call(self, node_id: str, function: str, args: Dict[str, Any]) -> None:
        """推入调用栈
        
        Args:
            node_id: 节点ID
            function: 函数名
            args: 参数
        """
        self.call_stack.append({
            "node_id": node_id,
            "function": function,
            "args": args,
            "timestamp": datetime.now().isoformat()
        })
    
    def pop_call(self) -> Optional[Dict[str, Any]]:
        """弹出调用栈
        
        Returns:
            Optional[Dict[str, Any]]: 调用信息
        """
        return self.call_stack.pop() if self.call_stack else None
    
    def add_message(self, level: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """添加调试消息
        
        Args:
            level: 消息级别
            message: 消息内容
            data: 附加数据
        """
        self.messages.append({
            "level": level,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制消息数量
        if len(self.messages) > 1000:
            self.messages = self.messages[-500:]


class NodeDebugger:
    """节点调试器"""
    
    def __init__(self):
        self.mode = DebugMode.OFF
        self.breakpoints: Dict[str, Breakpoint] = {}
        self.context = DebugContext()
        self.is_paused = False
        self.pause_reason = ""
        self.step_over = False
        self.step_into = False
        
        # 回调函数
        self.on_breakpoint_hit: Optional[Callable[[str, Breakpoint], None]] = None
        self.on_debug_message: Optional[Callable[[str, str], None]] = None
    
    def set_breakpoint_hit_callback(self, callback: Callable[[str, Breakpoint], None]) -> None:
        """设置断点命中回调
        
        Args:
            callback: 回调函数
        """
        self.on_breakpoint_hit = callback
    
    def set_debug_message_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置调试消息回调
        
        Args:
            callback: 回调函数
        """
        self.on_debug_message = callback
    
    def set_mode(self, mode: DebugMode) -> None:
        """设置调试模式
        
        Args:
            mode: 调试模式
        """
        self.mode = mode
        self.context.add_message("info", f"调试模式切换为: {mode.value}")
    
    def add_breakpoint(self, node_id: str, condition: Optional[str] = None) -> str:
        """添加断点
        
        Args:
            node_id: 节点ID
            condition: 断点条件
            
        Returns:
            str: 断点ID
        """
        breakpoint_id = f"bp_{node_id}_{len(self.breakpoints)}"
        breakpoint = Breakpoint(node_id, condition)
        self.breakpoints[breakpoint_id] = breakpoint
        
        self.context.add_message("info", f"添加断点: {node_id}")
        return breakpoint_id
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点
        
        Args:
            breakpoint_id: 断点ID
            
        Returns:
            bool: 是否成功移除
        """
        if breakpoint_id in self.breakpoints:
            breakpoint = self.breakpoints[breakpoint_id]
            del self.breakpoints[breakpoint_id]
            self.context.add_message("info", f"移除断点: {breakpoint.node_id}")
            return True
        return False
    
    def toggle_breakpoint(self, breakpoint_id: str) -> bool:
        """切换断点状态
        
        Args:
            breakpoint_id: 断点ID
            
        Returns:
            bool: 是否成功切换
        """
        if breakpoint_id in self.breakpoints:
            breakpoint = self.breakpoints[breakpoint_id]
            breakpoint.enabled = not breakpoint.enabled
            status = "启用" if breakpoint.enabled else "禁用"
            self.context.add_message("info", f"断点 {breakpoint.node_id} 已{status}")
            return True
        return False
    
    def check_breakpoints(self, node_id: str) -> Optional[Breakpoint]:
        """检查断点
        
        Args:
            node_id: 节点ID
            
        Returns:
            Optional[Breakpoint]: 命中的断点
        """
        for breakpoint in self.breakpoints.values():
            if breakpoint.node_id == node_id and breakpoint.should_break(self.context.variables):
                if self.on_breakpoint_hit:
                    self.on_breakpoint_hit(node_id, breakpoint)
                return breakpoint
        return None
    
    def pause_execution(self, reason: str = "手动暂停") -> None:
        """暂停执行
        
        Args:
            reason: 暂停原因
        """
        self.is_paused = True
        self.pause_reason = reason
        self.context.add_message("warning", f"执行暂停: {reason}")
    
    def resume_execution(self) -> None:
        """恢复执行"""
        self.is_paused = False
        self.pause_reason = ""
        self.context.add_message("info", "执行已恢复")
    
    def step_execution(self, step_type: str = "over") -> None:
        """单步执行
        
        Args:
            step_type: 步骤类型 (over, into, out)
        """
        if step_type == "over":
            self.step_over = True
        elif step_type == "into":
            self.step_into = True
        
        self.resume_execution()
        self.context.add_message("info", f"单步执行: {step_type}")
    
    def enter_node(self, node_id: str, context_data: Optional[Dict[str, Any]] = None) -> bool:
        """进入节点
        
        Args:
            node_id: 节点ID
            context_data: 上下文数据
            
        Returns:
            bool: 是否应该暂停
        """
        self.context.current_node = node_id
        self.context.step_count += 1
        
        if context_data:
            self.context.variables.update(context_data)
        
        # 检查断点
        hit_breakpoint = self.check_breakpoints(node_id)
        if hit_breakpoint:
            self.pause_execution(f"断点命中: {node_id}")
            return True
        
        # 检查单步执行
        if self.mode == DebugMode.STEP and (self.step_over or self.step_into):
            self.pause_execution(f"单步执行: {node_id}")
            self.step_over = False
            self.step_into = False
            return True
        
        # 检查跟踪模式
        if self.mode == DebugMode.TRACE:
            self.context.add_message("debug", f"进入节点: {node_id}")
        
        return self.is_paused
    
    def exit_node(self, node_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """退出节点
        
        Args:
            node_id: 节点ID
            result: 执行结果
        """
        if result:
            self.context.set_variable(f"{node_id}_result", result)
        
        self.context.add_message("debug", f"退出节点: {node_id}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息
        
        Returns:
            Dict[str, Any]: 调试信息
        """
        return {
            "mode": self.mode.value,
            "is_paused": self.is_paused,
            "pause_reason": self.pause_reason,
            "current_node": self.context.current_node,
            "step_count": self.context.step_count,
            "breakpoint_count": len(self.breakpoints),
            "variable_count": len(self.context.variables),
            "message_count": len(self.context.messages)
        }


class NodeDebuggerPanel:
    """节点调试面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.debugger = NodeDebugger()
        self.show_variables = True
        self.show_call_stack = False
        self.show_messages = False
        self.selected_breakpoint: Optional[str] = None
        
        # 设置回调
        self.debugger.set_breakpoint_hit_callback(self._on_breakpoint_hit)
        self.debugger.set_debug_message_callback(self._on_debug_message)
        
        # 外部回调
        self.on_debug_action: Optional[Callable[[str, Any], None]] = None
    
    def set_debug_action_callback(self, callback: Callable[[str, Any], None]) -> None:
        """设置调试动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_debug_action = callback
    
    def _on_breakpoint_hit(self, node_id: str, breakpoint: Breakpoint) -> None:
        """断点命中处理
        
        Args:
            node_id: 节点ID
            breakpoint: 断点
        """
        if self.on_debug_action:
            self.on_debug_action("breakpoint_hit", {
                "node_id": node_id,
                "breakpoint": breakpoint.to_dict()
            })
    
    def _on_debug_message(self, level: str, message: str) -> None:
        """调试消息处理
        
        Args:
            level: 消息级别
            message: 消息内容
        """
        if self.on_debug_action:
            self.on_debug_action("debug_message", {
                "level": level,
                "message": message
            })
    
    def set_mode(self, mode: DebugMode) -> None:
        """设置调试模式
        
        Args:
            mode: 调试模式
        """
        self.debugger.set_mode(mode)
    
    def add_breakpoint(self, node_id: str, condition: Optional[str] = None) -> Optional[str]:
        """添加断点
        
        Args:
            node_id: 节点ID
            condition: 断点条件
            
        Returns:
            Optional[str]: 断点ID
        """
        return self.debugger.add_breakpoint(node_id, condition)
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点
        
        Args:
            breakpoint_id: 断点ID
            
        Returns:
            bool: 是否成功移除
        """
        return self.debugger.remove_breakpoint(breakpoint_id)
    
    def toggle_breakpoint(self, breakpoint_id: str) -> bool:
        """切换断点状态
        
        Args:
            breakpoint_id: 断点ID
            
        Returns:
            bool: 是否成功切换
        """
        return self.debugger.toggle_breakpoint(breakpoint_id)
    
    def pause_execution(self) -> None:
        """暂停执行"""
        self.debugger.pause_execution()
    
    def resume_execution(self) -> None:
        """恢复执行"""
        self.debugger.resume_execution()
    
    def step_over(self) -> None:
        """单步跳过"""
        self.debugger.step_execution("over")
    
    def step_into(self) -> None:
        """单步进入"""
        self.debugger.step_execution("into")
    
    def toggle_variables(self) -> None:
        """切换变量显示"""
        self.show_variables = not self.show_variables
    
    def toggle_call_stack(self) -> None:
        """切换调用栈显示"""
        self.show_call_stack = not self.show_call_stack
    
    def toggle_messages(self) -> None:
        """切换消息显示"""
        self.show_messages = not self.show_messages
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "d":
            self.set_mode(DebugMode.OFF)
        elif key == "s":
            self.set_mode(DebugMode.STEP)
        elif key == "b":
            self.set_mode(DebugMode.BREAKPOINT)
        elif key == "t":
            self.set_mode(DebugMode.TRACE)
        elif key == "p":
            self.pause_execution()
        elif key == "r":
            self.resume_execution()
        elif key == "o":
            self.step_over()
        elif key == "i":
            self.step_into()
        elif key == "v":
            self.toggle_variables()
        elif key == "c":
            self.toggle_call_stack()
        elif key == "m":
            self.toggle_messages()
        elif key == "a":
            # 添加断点到当前节点
            if self.debugger.context.current_node:
                bp_id = self.add_breakpoint(self.debugger.context.current_node)
                if bp_id:
                    return f"BREAKPOINT_ADDED:{bp_id}"
        
        return None
    
    def render(self) -> Panel:
        """渲染调试面板
        
        Returns:
            Panel: 调试面板
        """
        debug_info = self.debugger.get_debug_info()
        
        # 创建布局
        layout = Layout()
        
        # 顶部：调试控制
        control_content = self._render_control_panel(debug_info)
        
        # 底部：详细信息
        if self.show_variables or self.show_call_stack or self.show_messages:
            layout.split_row(
                Layout(name="variables"),
                Layout(name="call_stack"),
                Layout(name="messages")
            )
            
            # 设置布局可见性
            layout["variables"].visible = self.show_variables
            layout["call_stack"].visible = self.show_call_stack
            layout["messages"].visible = self.show_messages
            
            if self.show_variables:
                layout["variables"].update(self._render_variables())
            if self.show_call_stack:
                layout["call_stack"].update(self._render_call_stack())
            if self.show_messages:
                layout["messages"].update(self._render_messages())
            
            # 组合内容
            content = Table.grid()
            content.add_row(control_content)
            content.add_row("")
            content.add_row(layout)
        else:
            content = control_content
        
        return Panel(
            content,
            title="节点调试器 (D=关闭, S=单步, B=断点, T=跟踪, P=暂停, R=恢复, O=跳过, I=进入)",
            border_style="yellow",
            padding=(1, 1)
        )
    
    def _render_control_panel(self, debug_info: Dict[str, Any]) -> Table:
        """渲染控制面板
        
        Args:
            debug_info: 调试信息
            
        Returns:
            Table: 控制面板表格
        """
        table = Table.grid()
        table.add_column()
        
        # 调试状态
        status_text = Text()
        status_text.append("调试状态: ", style="bold")
        
        mode_styles = {
            DebugMode.OFF.value: "dim",
            DebugMode.STEP.value: "cyan",
            DebugMode.BREAKPOINT.value: "yellow",
            DebugMode.TRACE.value: "magenta"
        }
        
        mode_style = mode_styles.get(debug_info["mode"], "white")
        status_text.append(debug_info["mode"].upper(), style=mode_style)
        
        if debug_info["is_paused"]:
            status_text.append(f" (暂停: {debug_info['pause_reason']})", style="red")
        
        status_text.append(f"\\n当前节点: {debug_info['current_node'] or '无'}")
        status_text.append(f"\\n执行步数: {debug_info['step_count']}")
        status_text.append(f"\\n断点数量: {debug_info['breakpoint_count']}")
        status_text.append(f"\\n变量数量: {debug_info['variable_count']}")
        
        table.add_row(status_text)
        
        return table
    
    def _render_variables(self) -> Table:
        """渲染变量面板
        
        Returns:
            Table: 变量面板表格
        """
        table = Table(
            title="变量",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("名称", style="bold")
        table.add_column("值", style="white")
        table.add_column("类型", style="dim")
        
        for name, value in self.debugger.context.variables.items():
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            
            type_str = type(value).__name__
            
            table.add_row(name, value_str, type_str)
        
        return table
    
    def _render_call_stack(self) -> Table:
        """渲染调用栈面板
        
        Returns:
            Table: 调用栈面板表格
        """
        table = Table(
            title="调用栈",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("节点", style="bold")
        table.add_column("函数", style="green")
        table.add_column("时间", style="dim")
        
        for call in reversed(self.debugger.context.call_stack[-10:]):  # 显示最近10个
            time_str = call["timestamp"][-8:]  # 只显示时间部分
            table.add_row(call["node_id"], call["function"], time_str)
        
        return table
    
    def _render_messages(self) -> Table:
        """渲染消息面板
        
        Returns:
            Table: 消息面板表格
        """
        table = Table(
            title="调试消息",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        table.add_column("级别", style="bold")
        table.add_column("消息", style="white")
        table.add_column("时间", style="dim")
        
        level_styles = {
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "debug": "dim"
        }
        
        for message in reversed(self.debugger.context.messages[-20:]):  # 显示最近20条
            level = message["level"]
            level_style = level_styles.get(level, "white")
            time_str = message["timestamp"][-8:]  # 只显示时间部分
            
            # 截断长消息
            msg_text = message["message"]
            if len(msg_text) > 30:
                msg_text = msg_text[:27] + "..."
            
            table.add_row(
                f"[{level_style}]{level.upper()}[/{level_style}]",
                msg_text,
                time_str
            )
        
        return table