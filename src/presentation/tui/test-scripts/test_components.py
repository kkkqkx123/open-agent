"""TUI组件测试脚本

用于测试各个组件的功能和交互
"""

import asyncio
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live

from ..config import get_tui_config
from ..components import (
    SidebarComponent,
    LangGraphPanelComponent,
    MainContentComponent,
    InputPanel
)
from src.infrastructure.graph.state import WorkflowState, HumanMessage
from src.domain.tools.interfaces import ToolResult


class ComponentTester:
    """组件测试器"""
    
    def __init__(self) -> None:
        """初始化组件测试器"""
        self.console = Console()
        self.config = get_tui_config()
        
        # 创建组件
        self.sidebar = SidebarComponent(self.config)
        self.langgraph = LangGraphPanelComponent(self.config)
        self.main_content = MainContentComponent(self.config)
        self.input_panel = InputPanel(self.config)
        
        # 创建测试状态
        self.test_state = self._create_test_state()
    
    def _create_test_state(self) -> WorkflowState:
        """创建测试状态
        
        Returns:
            WorkflowState: 测试状态
        """
        state = WorkflowState()
        
        # 添加测试消息
        state.add_message(HumanMessage(content="你好，请介绍一下你自己"))
        state.add_message(HumanMessage(content="你能帮我做什么？"))
        
        # 添加测试工具结果
        state.tool_results.append(ToolResult(
            tool_name="calculator",
            success=True,
            result="2 + 2 = 4"
        ))
        state.tool_results.append(ToolResult(
            tool_name="search",
            success=True,
            result="找到了5个相关结果"
        ))
        
        # 设置其他属性
        state.current_step = "response_generation"
        state.iteration_count = 2
        state.max_iterations = 5
        
        return state
    
    def test_sidebar(self) -> None:
        """测试侧边栏组件"""
        self.console.print("\n[bold cyan]测试侧边栏组件[/bold cyan]")
        
        # 更新组件状态
        self.sidebar.update_from_state(self.test_state)
        
        # 更新Agent信息
        self.sidebar.agent_info.update_agent_info(
            name="测试Agent",
            model="gpt-4",
            tools=["calculator", "search", "weather"],
            status="运行中"
        )
        
        # 渲染组件
        panel = self.sidebar.render()
        self.console.print(panel)
    
    def test_langgraph_panel(self) -> None:
        """测试LangGraph面板组件"""
        self.console.print("\n[bold cyan]测试LangGraph面板组件[/bold cyan]")
        
        # 更新组件状态
        self.langgraph.update_from_state(
            state=self.test_state,
            current_node="response_generation",
            node_status="running"
        )
        
        # 设置Studio状态
        self.langgraph.set_studio_status(True, 8079)
        
        # 渲染组件
        panel = self.langgraph.render()
        self.console.print(panel)
    
    def test_main_content(self) -> None:
        """测试主内容区组件"""
        self.console.print("\n[bold cyan]测试主内容区组件[/bold cyan]")
        
        # 更新组件状态
        self.main_content.update_from_state(self.test_state)
        
        # 添加测试消息
        self.main_content.add_user_message("你好，请介绍一下你自己")
        self.main_content.add_assistant_message("你好！我是一个AI助手，可以帮助你处理各种任务。")
        
        # 测试流式输出
        self.main_content.start_stream()
        self.main_content.add_stream_content("正在生成回复...")
        self.main_content.add_stream_content("这是一个测试流式输出的示例。")
        self.main_content.end_stream()
        
        # 添加工具结果
        self.main_content.add_tool_result(ToolResult(
            tool_name="calculator",
            success=True,
            result={"expression": "2 + 2", "result": 4}
        ))
        
        # 渲染组件
        panel = self.main_content.render()
        self.console.print(panel)
    
    def test_input_panel(self) -> None:
        """测试输入面板组件"""
        self.console.print("\n[bold cyan]测试输入面板组件[/bold cyan]")
        
        # 设置提交回调来测试普通消息
        submitted_messages = []
        
        def mock_submit(text: str) -> None:
            """模拟提交回调"""
            submitted_messages.append(text)
            self.console.print(f"[green]✅ 消息已提交: {text}[/green]")
        
        def mock_command(cmd: str, args: list) -> None:
            """模拟命令回调"""
            self.console.print(f"[blue]🔧 命令已执行: {cmd} {args}[/blue]")
        
        self.input_panel.set_submit_callback(mock_submit)
        self.input_panel.set_command_callback(mock_command)
        
        # 测试命令处理
        commands = [
            "/help",
            "/history",
            "/clear",
            "普通消息输入",
            "line1\\",  # 测试多行输入
            "hello ",  # 测试空格结尾
            "line1\nline2"  # 测试包含换行符
        ]
        
        for cmd in commands:
            self.console.print(f"\n[dim]测试输入: {cmd}[/dim]")
            
            # 设置输入文本
            self.input_panel.input_buffer.set_text(cmd)
            
            # 渲染组件
            panel = self.input_panel.render()
            self.console.print(panel)
            
            # 处理输入
            result = self.input_panel.handle_key("enter")
            if result:
                self.console.print(f"[yellow]处理结果: {result}[/yellow]")
            
            # 检查输入缓冲区状态
            if not self.input_panel.input_buffer.is_empty():
                self.console.print(f"[dim]输入缓冲区内容: {self.input_panel.input_buffer.get_text()}[/dim]")
        
        # 显示提交的消息统计
        if submitted_messages:
            self.console.print(f"\n[green]总共提交了 {len(submitted_messages)} 条消息:[/green]")
            for i, msg in enumerate(submitted_messages, 1):
                self.console.print(f"  {i}. {msg}")
        else:
            self.console.print("\n[dim]没有提交任何消息[/dim]")
    
    def test_all_components(self) -> None:
        """测试所有组件"""
        self.console.print("[bold green]开始测试所有TUI组件[/bold green]")
        
        # 测试各个组件
        self.test_sidebar()
        self.test_langgraph_panel()
        self.test_main_content()
        self.test_input_panel()
        
        self.console.print("\n[bold green]所有组件测试完成[/bold green]")
    
    def test_integration(self) -> None:
        """测试组件集成"""
        self.console.print("\n[bold cyan]测试组件集成[/bold cyan]")
        
        # 创建布局
        layout = Layout()
        
        # 分割布局
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="input", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="sidebar", size=30),
            Layout(name="main"),
            Layout(name="langgraph", size=25)
        )
        
        # 更新所有组件
        self.sidebar.update_from_state(self.test_state)
        self.langgraph.update_from_state(self.test_state, "response_generation", "running")
        self.main_content.update_from_state(self.test_state)
        
        # 设置布局内容
        layout["header"].update(Panel(Text("TUI组件集成测试", style="bold cyan"), border_style="blue"))
        layout["sidebar"].update(self.sidebar.render())
        layout["main"].update(self.main_content.render())
        layout["langgraph"].update(self.langgraph.render())
        layout["input"].update(self.input_panel.render())
        
        # 显示布局
        self.console.print(layout)


def run_tests() -> None:
    """运行测试"""
    console = Console()
    
    console.print("[bold blue]TUI组件测试[/bold blue]")
    console.print("=" * 50)
    
    try:
        tester = ComponentTester()
        
        # 运行各项测试
        tester.test_all_components()
        tester.test_integration()
        
        console.print("\n[bold green]✅ 所有测试通过[/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ 测试失败: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    run_tests()