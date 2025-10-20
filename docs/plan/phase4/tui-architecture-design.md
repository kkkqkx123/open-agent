# TUI界面架构设计

## 1. 架构概述

TUI界面采用分层架构，基于rich和click框架，提供模块化的组件设计和清晰的职责分离。

## 2. 核心组件设计

### 2.1 CLI命令层 (`src/presentation/cli/`)
```python
# commands.py
@click.group()
def cli():
    """Modular Agent Framework CLI"""

@cli.command()
def run():
    """启动TUI交互界面"""
    from src.presentation.tui.tui_manager import TUIManager
    manager = TUIManager()
    asyncio.run(manager.start())

@cli.group()
def session():
    """会话管理命令"""

@session.command()
@click.argument('session_id')
def restore(session_id):
    """恢复指定会话"""

@cli.command()
def studio():
    """启动LangGraph Studio服务器"""
```

### 2.2 TUI管理器 (`src/presentation/tui/tui_manager.py`)
```python
class TUIManager:
    def __init__(self):
        self.layout = LayoutManager()
        self.input_handler = InputHandler()
        self.session_handler = SessionHandler()
        self.workflow_handler = WorkflowHandler()
    
    async def start(self):
        """启动TUI界面"""
        await self._setup_layout()
        await self._event_loop()
    
    async def _setup_layout(self):
        """初始化界面布局"""
        self.layout.create_layout(
            header=HeaderComponent(),
            sidebar=SidebarComponent(),
            main=MainContentComponent(),
            input_panel=InputPanelComponent(),
            langgraph_panel=LangGraphPanelComponent()
        )
    
    async def _event_loop(self):
        """主事件循环"""
        while True:
            await self._process_events()
            await self._refresh_ui()
```

### 2.3 布局管理器 (`src/presentation/tui/layout.py`)
```python
class LayoutManager:
    def create_layout(self, **components):
        """创建响应式布局"""
        self.layout = Layout()
        
        # 标题栏 (5%)
        self.layout.split(
            Layout(name="header", size=1),
            Layout(ratio=1, name="main")
        )
        
        # 主区域分割
        self.layout["main"].split_row(
            Layout(name="sidebar", ratio=1),      # 25%
            Layout(name="content", ratio=3),       # 75%
            Layout(name="langgraph", size=10)     # LangGraph面板
        )
        
        # 内容区域分割
        self.layout["content"].split(
            Layout(name="main_content", ratio=4),  # 80%
            Layout(name="input_panel", size=3)     # 20%
        )
```

## 3. 组件详细设计

### 3.1 侧边栏组件 (`src/presentation/tui/components/sidebar.py`)
```python
class SidebarComponent:
    def __init__(self):
        self.agent_info = AgentInfoSection()
        self.workflow_status = WorkflowStatusSection()
        self.metrics = MetricsSection()
    
    def render(self) -> Panel:
        """渲染侧边栏"""
        sections = [
            self.agent_info.render(),
            self.workflow_status.render(),
            self.metrics.render()
        ]
        return Panel(
            Group(*sections),
            title="状态面板",
            border_style="blue"
        )

class AgentInfoSection:
    def render(self) -> Text:
        """Agent信息显示"""
        info = Text()
        info.append("Agent: ", style="bold")
        info.append(f"{current_agent.name}\n")
        info.append("Model: ", style="bold")
        info.append(f"{current_agent.model}\n")
        info.append("Tools: ", style="bold")
        info.append(f"{len(current_agent.tools)} tools")
        return info

class WorkflowStatusSection:
    def render(self) -> Text:
        """工作流状态显示"""
        status = Text()
        if workflow_state:
            status.append("当前节点: ", style="bold")
            status.append(f"{workflow_state.current_node}\n")
            status.append("执行路径: ", style="bold")
            status.append(f"{' → '.join(workflow_state.execution_path[-3:])}")
        return status

class MetricsSection:
    def render(self) -> Text:
        """指标统计显示"""
        metrics = Text()
        metrics.append("Token使用: ", style="bold")
        metrics.append(f"输入:{metrics.input_tokens} | 输出:{metrics.output_tokens}\n")
        metrics.append("工具调用: ", style="bold")
        metrics.append(f"成功:{metrics.successful_tools} | 失败:{metrics.failed_tools}\n")
        metrics.append("会话时长: ", style="bold")
        metrics.append(f"{metrics.session_duration}")
        return metrics
```

### 3.2 主内容区组件 (`src/presentation/tui/components/main_content.py`)
```python
class MainContentComponent:
    def __init__(self):
        self.history = ConversationHistory()
        self.stream_output = StreamOutput()
        self.tool_results = ToolResults()
    
    def render(self) -> Panel:
        """渲染主内容区"""
        content = Group(
            self.history.render(),
            self.stream_output.render(),
            self.tool_results.render()
        )
        return Panel(content, title="会话内容")

class ConversationHistory:
    def render(self) -> Text:
        """会话历史显示"""
        history = Text()
        for message in session_history:
            if message.role == "user":
                history.append("👤 ", style="green")
            else:
                history.append("🤖 ", style="blue")
            history.append(f"{message.content}\n\n")
        return history

class StreamOutput:
    def render(self) -> Text:
        """流式输出显示"""
        output = Text()
        if current_stream:
            output.append(current_stream.content)
        return output

class ToolResults:
    def render(self) -> Panel:
        """工具调用结果显示"""
        if not tool_results:
            return Text("无工具调用")
        
        results = []
        for result in tool_results:
            panel = Panel(
                result.details,
                title=f"工具: {result.tool_name}",
                subtitle=f"状态: {'✅' if result.success else '❌'}"
            )
            results.append(panel)
        
        return Group(*results)
```

### 3.3 输入面板组件 (`src/presentation/tui/components/input_panel.py`)
```python
class InputPanelComponent:
    def __init__(self):
        self.input_buffer = ""
        self.history = InputHistory()
        self.current_index = 0
    
    def render(self) -> Panel:
        """渲染输入面板"""
        return Panel(
            self._get_input_display(),
            title="输入",
            border_style="green"
        )
    
    def _get_input_display(self) -> Text:
        """获取输入显示"""
        display = Text()
        if self.input_buffer:
            display.append(self.input_buffer)
        else:
            display.append("请输入消息...", style="dim")
        return display
    
    async def handle_key(self, key: str) -> Optional[str]:
        """处理键盘输入"""
        if key == "enter":
            return self._submit_input()
        elif key == "up":
            self._navigate_history(-1)
        elif key == "down":
            self._navigate_history(1)
        elif key == "backspace":
            self.input_buffer = self.input_buffer[:-1]
        else:
            self.input_buffer += key
        return None
```

### 3.4 LangGraph状态面板 (`src/presentation/tui/components/langgraph_panel.py`)
```python
class LangGraphPanelComponent:
    def render(self) -> Panel:
        """渲染LangGraph状态面板"""
        content = Group(
            self._render_current_node(),
            self._render_execution_path(),
            self._render_state_snapshot(),
            self._render_studio_link()
        )
        return Panel(content, title="LangGraph状态")

    def _render_current_node(self) -> Text:
        """显示当前节点"""
        text = Text()
        text.append("当前节点: ", style="bold")
        if workflow_state.current_node:
            text.append(workflow_state.current_node, style="cyan")
        else:
            text.append("未运行", style="dim")
        return text

    def _render_execution_path(self) -> Text:
        """显示执行路径"""
        text = Text()
        text.append("执行路径: ", style="bold")
        if workflow_state.execution_path:
            path = " → ".join(workflow_state.execution_path[-5:])
            text.append(path)
        else:
            text.append("无历史", style="dim")
        return text

    def _render_state_snapshot(self) -> Text:
        """显示状态快照"""
        text = Text()
        text.append("状态变量: ", style="bold")
        if workflow_state.state:
            variables = list(workflow_state.state.keys())[:3]
            text.append(f"{len(variables)}个变量")
        else:
            text.append("无状态", style="dim")
        return text

    def _render_studio_link(self) -> Text:
        """显示Studio链接"""
        text = Text()
        text.append("Studio: ", style="bold")
        if studio_server.running:
            text.append(f"http://localhost:{studio_server.port}", style="underline blue")
            text.append(" ↩", style="bold")
        else:
            text.append("未启动", style="dim")
        return text
```

## 4. 事件处理设计

### 4.1 输入处理器 (`src/presentation/tui/handlers/input_handler.py`)
```python
class InputHandler:
    async def process_input(self, input_text: str) -> None:
        """处理用户输入"""
        if input_text.startswith('/'):
            await self._handle_command(input_text)
        else:
            await self._handle_message(input_text)
    
    async def _handle_command(self, command: str) -> None:
        """处理命令"""
        cmd, *args = command[1:].split()
        if cmd == "help":
            self._show_help()
        elif cmd == "clear":
            self._clear_history()
        elif cmd == "exit":
            self._exit_tui()
        elif cmd == "pause":
            await self._pause_workflow()
        elif cmd == "resume":
            await self._resume_workflow()
        elif cmd == "stop":
            await self._stop_workflow()
    
    async def _handle_message(self, message: str) -> None:
        """处理普通消息"""
        await agent_core.process_message(message)
```

### 4.2 会话处理器 (`src/presentation/tui/handlers/session_handler.py`)
```python
class SessionHandler:
    async def list_sessions(self) -> List[SessionInfo]:
        """列出所有会话"""
        return await session_manager.list_sessions()
    
    async def restore_session(self, session_id: str) -> None:
        """恢复会话"""
        session = await session_manager.get_session(session_id)
        await self._load_session_data(session)
    
    async def create_session(self, agent_config: str) -> None:
        """创建新会话"""
        session = await session_manager.create_session(agent_config)
        await self._load_session_data(session)
```

### 4.3 工作流处理器 (`src/presentation/tui/handlers/workflow_handler.py`)
```python
class WorkflowHandler:
    async def pause_workflow(self) -> None:
        """暂停工作流"""
        await langgraph_manager.pause()
        self._update_workflow_status("paused")
    
    async def resume_workflow(self) -> None:
        """继续工作流"""
        await langgraph_manager.resume()
        self._update_workflow_status("running")
    
    async def stop_workflow(self) -> None:
        """终止工作流"""
        await langgraph_manager.stop()
        self._update_workflow_status("stopped")
    
    def _update_workflow_status(self, status: str) -> None:
        """更新工作流状态"""
        self.workflow_status = status
        self.layout.refresh()
```

## 5. 配置集成

### 5.1 TUI配置模型
```python
# src/presentation/config.py
class TUIConfig(BaseModel):
    show_thought: bool = True
    show_langgraph_panel: bool = True
    studio_port: int = 8079
    color_scheme: str = "default"
    min_width: int = 80
    min_height: int = 24
    
    @classmethod
    def from_global_config(cls) -> "TUIConfig":
        config = config_loader.get_global_config()
        tui_config = config.get("tui", {})
        return cls(**tui_config)
```

## 6. 错误处理设计

### 6.1 TUI错误处理器
```python
class TUIErrorHandler:
    def handle_error(self, error: Exception) -> None:
        """处理TUI错误"""
        if isinstance(error, LayoutError):
            self._handle_layout_error(error)
        elif isinstance(error, InputError):
            self._handle_input_error(error)
        elif isinstance(error, WorkflowError):
            self._handle_workflow_error(error)
        else:
            self._handle_generic_error(error)
    
    def _handle_layout_error(self, error: LayoutError) -> None:
        """处理布局错误"""
        self.show_error("布局错误", f"请调整终端大小: {error}")
    
    def _handle_input_error(self, error: InputError) -> None:
        """处理输入错误"""
        self.show_error("输入错误", f"无效输入: {error}")
    
    def show_error(self, title: str, message: str) -> None:
        """显示错误信息"""
        error_panel = Panel(
            Text(message, style="red"),
            title=title,
            border_style="red"
        )
        self.layout.show_overlay(error_panel)
```

---
*架构设计版本: V1.0*
*更新时间: 2025-10-20*