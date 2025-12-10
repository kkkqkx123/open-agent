"""运行命令实现"""

import asyncio
from typing import Optional, Dict, Any, cast
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from src.services.container import get_global_container
from src.interfaces.config import IConfigLoader
from src.interfaces.sessions import ISessionService
from src.core.sessions.entities import UserRequestEntity, UserInteractionEntity
from src.interfaces.workflow.services import IWorkflowManager
from src.core.state import WorkflowState
from src.interfaces.state import IState
from src.interfaces.state.workflow import IWorkflowState
from src.services.workflow.state_converter import WorkflowStateConverter
from src.infrastructure.messages.types import HumanMessage, AIMessage
from datetime import datetime
import uuid


class RunCommand:
    """运行命令实现"""
    
    def __init__(self, config_path: Optional[str] = None, verbose: bool = False) -> None:
        self.config_path = config_path
        self.verbose = verbose
        self.console = Console()
        self.state_adapter = WorkflowStateConverter()
        
    def execute(self, workflow_config_path: str, agent_config_path: Optional[str], session_id: Optional[str]) -> None:
        """执行运行命令"""
        try:
            # 获取依赖服务
            container = get_global_container()
            session_manager = container.get(ISessionService)  # type: ignore
            workflow_manager = container.get(IWorkflowManager)  # type: ignore
            
            if session_id:
                # 恢复现有会话
                self.console.print(f"[cyan]正在恢复会话 {session_id}...[/cyan]")
                asyncio.run(self._restore_and_run(session_id, session_manager, workflow_manager))
            else:
                # 创建新会话
                self.console.print("[cyan]正在创建新会话...[/cyan]")
                asyncio.run(self._create_and_run(workflow_config_path, agent_config_path, session_manager, workflow_manager))
            
        except Exception as e:
            self.console.print(f"[red]执行失败: {e}[/red]")
            if self.verbose:
                import traceback
                self.console.print(traceback.format_exc())
            raise
    
    async def _create_and_run(
        self, 
        workflow_config_path: str, 
        agent_config_path: Optional[str],
        session_manager: ISessionService,
        workflow_manager: IWorkflowManager
    ) -> None:
        """创建会话并运行"""
        # 创建用户请求
        user_request = UserRequestEntity(
            request_id=f"request_{uuid.uuid4().hex[:8]}",
            user_id=None,
            content=f"创建会话: {workflow_config_path}",
            metadata={
                "workflow_config_path": workflow_config_path,
                "agent_config_path": agent_config_path
            },
            timestamp=datetime.now()
        )
        
        # 创建会话
        session_id = await session_manager.create_session(user_request)
        self.console.print(f"[green]新会话 {session_id} 创建成功[/green]")
        
        # 显示会话信息
        self._display_session_info(session_id, workflow_config_path)
        
        # 运行交互式循环
        await self._run_interactive_loop(session_id, session_manager, workflow_manager)
    
    async def _restore_and_run(
        self,
        session_id: str,
        session_manager: ISessionService,
        workflow_manager: IWorkflowManager
    ) -> None:
        """恢复会话并运行"""
        # 获取会话信息
        session_context = await session_manager.get_session_context(session_id)
        if not session_context:
            self.console.print(f"[red]会话不存在: {session_id}[/red]")
            return
        
        self.console.print(f"[green]会话 {session_id} 恢复成功[/green]")
        
        # 显示会话信息
        self._display_session_info(session_id, "已恢复的会话")
        
        # 运行交互式循环
        await self._run_interactive_loop(session_id, session_manager, workflow_manager)
    
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
    
    async def _run_interactive_loop(
        self, 
        session_id: str, 
        session_manager: ISessionService,
        workflow_manager: IWorkflowManager
    ) -> None:
        """运行交互式循环"""
        self.console.print("[bold cyan]进入交互模式，输入 'exit' 或 'quit' 退出[/bold cyan]")
        self.console.print()
        
        # 初始化状态
        from src.core.state import WorkflowState
        initial_state = WorkflowState()
        
        while True:
            try:
                # 获取用户输入
                user_input = self.console.input("[bold blue]用户:[/bold blue] ")
                
                # 检查退出命令
                if user_input.lower() in ['exit', 'quit', '退出']:
                    self.console.print("[yellow]正在保存会话并退出...[/yellow]")
                    # 追踪用户交互
                    interaction = UserInteractionEntity(
                        interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                        session_id=session_id,
                        thread_id=None,
                        interaction_type="session_exit",
                        content="用户退出会话",
                        metadata={},
                        timestamp=datetime.now()
                    )
                    await session_manager.track_user_interaction(session_id, interaction)
                    self.console.print("[green]会话已保存，再见！[/green]")
                    break
                
                # 添加用户消息到状态
                human_message = HumanMessage(content=user_input)
                # WorkflowState 实现了 add_message 方法，但接口中定义为属性
                # 这里我们直接使用实现的方法
                initial_state.add_message(human_message)
                
                # 追踪用户输入交互
                user_interaction = UserInteractionEntity(
                    interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    thread_id=None,
                    interaction_type="user_input",
                    content=user_input,
                    metadata={},
                    timestamp=datetime.now()
                )
                await session_manager.track_user_interaction(session_id, user_interaction)
                
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
                        result = await self._execute_workflow(cast(IWorkflowState, initial_state), workflow_manager)
                        
                        if result:
                            initial_state = result
                            progress.update(task, description="处理完成")
                            
                            # 显示AI回复
                            messages = initial_state.get_messages()  # 使用方法访问
                            if messages:
                                last_message = initial_state.get_last_message()
                                if hasattr(last_message, 'content'):
                                    content = getattr(last_message, 'content', '')
                                    self.console.print(f"[bold green]助手:[/bold green] {content}")
                                    
                                    # 追踪AI响应交互
                                    ai_interaction = UserInteractionEntity(
                                        interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                                        session_id=session_id,
                                        thread_id=None,
                                        interaction_type="ai_response",
                                        content=content,
                                        metadata={},
                                        timestamp=datetime.now()
                                    )
                                    await session_manager.track_user_interaction(session_id, ai_interaction)
                        
                    except Exception as e:
                        progress.update(task, description="处理失败")
                        self.console.print(f"[red]处理失败: {e}[/red]")
                        if self.verbose:
                            import traceback
                            self.console.print(traceback.format_exc())
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]正在保存会话并退出...[/yellow]")
                # 追踪中断交互
                interrupt_interaction = UserInteractionEntity(
                    interaction_id=f"interaction_{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    thread_id=None,
                    interaction_type="session_interrupt",
                    content="用户中断会话",
                    metadata={},
                    timestamp=datetime.now()
                )
                await session_manager.track_user_interaction(session_id, interrupt_interaction)
                self.console.print("[green]会话已保存，再见！[/green]")
                break
            except Exception as e:
                self.console.print(f"[red]错误: {e}[/red]")
                if self.verbose:
                    import traceback
                    self.console.print(traceback.format_exc())
    
    async def _execute_workflow(
        self,
        state: IWorkflowState,
        workflow_manager: IWorkflowManager
    ) -> Optional[IWorkflowState]:
        """异步执行工作流"""
        try:
            # 将适配器状态转换为图状态
            # 直接使用状态，不需要转换
            graph_state = state
            
            # 使用workflow_manager异步运行工作流
            # 获取第一个可用的工作流ID
            workflows = workflow_manager.list_workflows()
            if workflows:
                workflow_id = workflows[0]["id"] if isinstance(workflows[0], dict) else workflows[0]
                # 执行工作流
                result_state = workflow_manager.execute_workflow(
                    workflow_id=workflow_id,
                    initial_state=graph_state
                )
                if result_state:
                    # 将结果转换回适配器状态（处理接口返回的类型）
                    return result_state
            
            # 如果没有可用的工作流，直接返回当前状态
            return graph_state
            
        except Exception as e:
            self.console.print(f"[red]工作流执行失败: {e}[/red]")
            raise