"""运行命令实现"""

import asyncio
from typing import Optional, Dict, Any, cast
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from ...infrastructure.container import get_global_container
from ...infrastructure.config.loader.file_config_loader import IConfigLoader
from src.application.sessions.manager import ISessionManager
from src.application.workflow.manager import IWorkflowManager
from src.infrastructure.graph.states import WorkflowState
from src.infrastructure.graph.adapters.state_adapter import StateAdapter


class RunCommand:
    """运行命令实现"""
    
    def __init__(self, config_path: Optional[str] = None, verbose: bool = False) -> None:
        self.config_path = config_path
        self.verbose = verbose
        self.console = Console()
        self.state_adapter = StateAdapter()
        
    def execute(self, workflow_config_path: str, agent_config_path: Optional[str], session_id: Optional[str]) -> None:
        """执行运行命令"""
        try:
            # 获取依赖服务
            container = get_global_container()
            session_manager = container.get(ISessionManager)  # type: ignore
            workflow_manager = container.get(IWorkflowManager)  # type: ignore
            
            if session_id:
                # 恢复现有会话
                self.console.print(f"[cyan]正在恢复会话 {session_id}...[/cyan]")
                workflow, graph_state = session_manager.restore_session(session_id)
                state = self.state_adapter.from_graph_state(cast(Dict[str, Any], graph_state))
                self.console.print(f"[green]会话 {session_id} 恢复成功[/green]")
            else:
                # 创建新会话
                self.console.print("[cyan]正在创建新会话...[/cyan]")
                
                # 加载agent配置
                agent_config = self._load_agent_config(agent_config_path)
                
                # 创建会话
                session_id = session_manager.create_session(
                    workflow_config_path=workflow_config_path,
                    agent_config=agent_config
                )
                
                # 获取工作流和初始状态
                workflow, graph_state = session_manager.restore_session(session_id)
                state = self.state_adapter.from_graph_state(cast(Dict[str, Any], graph_state))
                self.console.print(f"[green]新会话 {session_id} 创建成功[/green]")
            
            # 显示会话信息
            self._display_session_info(session_id, workflow_config_path)
            
            # 运行交互式循环
            self._run_interactive_loop(session_id, workflow, state, session_manager)
            
        except Exception as e:
            self.console.print(f"[red]执行失败: {e}[/red]")
            if self.verbose:
                import traceback
                self.console.print(traceback.format_exc())
            raise
    
    def _load_agent_config(self, agent_config_path: Optional[str]) -> Optional[Dict[str, Any]]:
        """加载agent配置"""
        if not agent_config_path:
            return None
            
        try:
            container = get_global_container()
            config_loader = container.get(IConfigLoader)  # type: ignore
            return config_loader.load(agent_config_path)
        except Exception as e:
            self.console.print(f"[yellow]警告: 无法加载agent配置 {agent_config_path}: {e}[/yellow]")
            return None
    
    def _display_session_info(self, session_id: str, workflow_config_path: str) -> None:
        """显示会话信息"""
        panel = Panel(
            f"[bold]会话ID:[/bold] {session_id}\n"
            f"[bold]工作流:[/bold] {workflow_config_path}\n"
            f"[bold]模式:[/bold] 命令行交互",
            title="[bold green]会话信息[/bold green]",
            border_style="green"
        )
        self.console.print(panel)
        # 移除额外的空行打印
    
    def _run_interactive_loop(self, session_id: str, workflow: Any, state: WorkflowState, session_manager: ISessionManager) -> None:
        """运行交互式循环"""
        self.console.print("[bold cyan]进入交互模式，输入 'exit' 或 'quit' 退出[/bold cyan]")
        self.console.print()
        
        while True:
            try:
                # 获取用户输入
                user_input = self.console.input("[bold blue]用户:[/bold blue] ")
                
                # 检查退出命令
                if user_input.lower() in ['exit', 'quit', '退出']:
                    self.console.print("[yellow]正在保存会话并退出...[/yellow]")
                    session_manager.save_session(session_id, workflow, state)
                    self.console.print("[green]会话已保存，再见！[/green]")
                    break
                
                # 添加用户消息到状态
                human_message = AgentMessage(content=user_input, role="human")
                state.add_message(human_message)
                
                # 执行工作流
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                    transient=True
                ) as progress:
                    task = progress.add_task("正在处理...", total=None)
                    
                    try:
                        # 异步执行工作流
                        result = asyncio.run(self._execute_workflow(workflow, state))
                        
                        if result:
                            state = result
                            progress.update(task, description="处理完成")
                            
                            # 显示AI回复
                            if state.messages:
                                last_message = state.messages[-1]
                                if hasattr(last_message, 'content'):
                                    content = getattr(last_message, 'content', '')
                                    self.console.print(f"[bold green]助手:[/bold green] {content}")
                        
                    except Exception as e:
                        progress.update(task, description="处理失败")
                        self.console.print(f"[red]处理失败: {e}[/red]")
                        if self.verbose:
                            import traceback
                            self.console.print(traceback.format_exc())
                
                # 保存会话状态
                graph_state = self.state_adapter.to_graph_state(state)
                session_manager.save_session(session_id, workflow, graph_state)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]正在保存会话并退出...[/yellow]")
                session_manager.save_session(session_id, workflow, state)
                self.console.print("[green]会话已保存，再见！[/green]")
                break
            except Exception as e:
                self.console.print(f"[red]错误: {e}[/red]")
                if self.verbose:
                    import traceback
                    self.console.print(traceback.format_exc())
    
    async def _execute_workflow(self, workflow: Any, state: WorkflowState) -> Optional[WorkflowState]:
        """异步执行工作流"""
        try:
            # 这里需要根据具体的工作流实现来调整
            # 假设工作流有async_run方法
            if hasattr(workflow, 'async_run') and callable(workflow.async_run):
                # 检查是否是协程函数
                import inspect
                if inspect.iscoroutinefunction(workflow.async_run):
                    result = await workflow.async_run(state)
                    return result  # type: ignore
                else:
                    # 如果不是协程函数，直接调用
                    result = workflow.async_run(state)
                    return result  # type: ignore
            elif hasattr(workflow, 'run') and callable(workflow.run):
                result = workflow.run(state)
                return result  # type: ignore
            else:
                self.console.print("[yellow]警告: 工作流没有可执行的run方法[/yellow]")
                return None
        except Exception as e:
            self.console.print(f"[red]工作流执行失败: {e}[/red]")
            raise