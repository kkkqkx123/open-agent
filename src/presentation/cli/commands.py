"""CLI命令框架"""

import click
from typing import Optional
from pathlib import Path
from rich.console import Console

from src.infrastructure.container import get_global_container
from src.infrastructure.config_loader import IConfigLoader
from src.application.sessions.manager import ISessionManager
from src.infrastructure.env_check_command import EnvironmentCheckCommand
from .error_handler import handle_cli_error, handle_cli_warning, handle_cli_success, handle_cli_info
from .help import HelpManager


# 创建CLI组
cli = click.Group(name="模块化代理框架", help="模块化代理框架命令行工具")
console = Console()
help_manager = HelpManager()


@cli.group()
def session() -> None:
    """会话管理命令"""
    pass


@session.command("list")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="输出格式")
@click.pass_context
def session_list(ctx: click.Context, format: str) -> None:
    """列出所有会话"""
    try:
        container = get_global_container()
        session_manager = container.get(ISessionManager)
        
        sessions = session_manager.list_sessions()
        
        if format == "table":
            _print_sessions_table(sessions)
        else:
            import json
            console.print(json.dumps(sessions, indent=2, ensure_ascii=False))
            
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "检查配置时发生错误")


@session.command("restore")
@click.argument("session_id")
@click.pass_context
def session_restore(ctx: click.Context, session_id: str) -> None:
    """恢复指定会话"""
    try:
        container = get_global_container()
        session_manager = container.get(ISessionManager)
        
        # 检查会话是否存在
        session_data = session_manager.get_session(session_id)
        if not session_data:
            console.print(f"[red]会话 {session_id} 不存在[/red]")
            raise click.ClickException(f"会话 {session_id} 不存在")
        
        console.print(f"[green]正在恢复会话 {session_id}...[/green]")
        
        # 恢复会话
        workflow, state = session_manager.restore_session(session_id)
        
        console.print(f"[green]会话 {session_id} 恢复成功[/green]")
        console.print(f"工作流: {session_data['metadata']['workflow_config_path']}")
        console.print(f"创建时间: {session_data['metadata']['created_at']}")
        
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "检查配置时发生错误")


@session.command("destroy")
@click.argument("session_id")
@click.option("--confirm", is_flag=True, help="确认删除")
@click.pass_context
def session_destroy(ctx: click.Context, session_id: str, confirm: bool) -> None:
    """删除指定会话"""
    try:
        container = get_global_container()
        session_manager = container.get(ISessionManager)
        
        # 检查会话是否存在
        session_data = session_manager.get_session(session_id)
        if not session_data:
            console.print(f"[red]会话 {session_id} 不存在[/red]")
            raise click.ClickException(f"会话 {session_id} 不存在")
        
        # 确认删除
        if not confirm:
            if not click.confirm(f"确定要删除会话 {session_id} 吗？此操作不可撤销。"):
                console.print("操作已取消")
                return
        
        # 删除会话
        success = session_manager.delete_session(session_id)
        
        if success:
            console.print(f"[green]会话 {session_id} 删除成功[/green]")
        else:
            console.print(f"[red]会话 {session_id} 删除失败[/red]")
            raise click.ClickException(f"会话 {session_id} 删除失败")
            
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "检查配置时发生错误")


@cli.group()
def config() -> None:
    """配置管理命令"""
    pass


@config.command("check")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="输出格式")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（仅JSON格式）")
@click.pass_context
def config_check(ctx: click.Context, format: str, output: Optional[str]) -> None:
    """检查配置和环境"""
    try:
        command = EnvironmentCheckCommand()
        command.run(format_type=format, output_file=output)
        
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "检查配置时发生错误")


@cli.command("version")
@click.pass_context
def version(ctx: click.Context) -> None:
    """显示版本信息"""
    try:
        # 从pyproject.toml读取版本信息
        from pathlib import Path
        
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        
        # 尝试使用tomllib (Python 3.11+) 或 tomli
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
        except ImportError:
            try:
                import tomli
                with open(pyproject_path, "rb") as f:
                    data = tomli.load(f)
            except ImportError:
                # 如果都没有，使用简单的字符串解析
                version = "unknown"
                name = "modular-agent"
                console.print(f"[bold cyan]{name}[/bold cyan] version [bold green]{version}[/bold green]")
                return
        
        version = data.get("project", {}).get("version", "unknown")
        name = data.get("project", {}).get("name", "modular-agent")
        
        console.print(f"[bold cyan]{name}[/bold cyan] version [bold green]{version}[/bold green]")
        
    except Exception as e:
        handle_cli_warning(f"无法读取版本信息: {e}", "获取版本信息时发生错误")
        console.print("版本: unknown")


def _print_sessions_table(sessions: list) -> None:
    """打印会话表格"""
    from rich.table import Table
    from rich.text import Text
    
    table = Table(title="会话列表")
    table.add_column("会话ID", style="cyan", no_wrap=True)
    table.add_column("工作流", style="magenta")
    table.add_column("状态", style="green")
    table.add_column("创建时间", style="blue")
    table.add_column("更新时间", style="yellow")
    
    if not sessions:
        table.add_row("无会话", "", "", "", "")
    else:
        for session in sessions:
            metadata = session.get("metadata", {})
            session_id = metadata.get("session_id", "unknown")[:8] + "..."
            workflow = metadata.get("workflow_config_path", "unknown")
            status = metadata.get("status", "unknown")
            created_at = metadata.get("created_at", "unknown")
            updated_at = metadata.get("updated_at", "unknown")
            
            # 格式化时间显示
            if created_at != "unknown":
                created_at = created_at.replace("T", " ").split(".")[0]
            if updated_at != "unknown":
                updated_at = updated_at.replace("T", " ").split(".")[0]
            
            table.add_row(session_id, workflow, status, created_at, updated_at)
    
    console.print(table)


def setup_container(config_path: Optional[str] = None) -> None:
    """设置依赖注入容器"""
    from ...infrastructure.container import DependencyContainer
    from ...infrastructure.config_loader import YamlConfigLoader
    from src.application.sessions.manager import SessionManager
    from src.domain.sessions.store import FileSessionStore
    from src.application.workflow.manager import WorkflowManager
    from src.application.sessions.git_manager import GitManager
    
    container = get_global_container()
    
    # 注册配置加载器
    if not container.has_service(IConfigLoader):
        config_loader = YamlConfigLoader()
        container.register_instance(IConfigLoader, config_loader)
    
    # 注册配置系统服务
    from ...infrastructure.config import (
        IConfigSystem, ConfigSystem, IConfigMerger, ConfigMerger, 
        IConfigValidator, ConfigValidator
    )
    
    # 注册配置合并器
    if not container.has_service(IConfigMerger):
        config_merger = ConfigMerger()
        container.register_instance(IConfigMerger, config_merger)
    
    # 注册配置验证器
    if not container.has_service(IConfigValidator):
        config_validator = ConfigValidator()
        container.register_instance(IConfigValidator, config_validator)
    
    # 注册配置系统
    if not container.has_service(IConfigSystem):
        config_system = ConfigSystem(
            config_loader=container.get(IConfigLoader),
            config_merger=container.get(IConfigMerger),
            config_validator=container.get(IConfigValidator)
        )
        container.register_instance(IConfigSystem, config_system)
    
    # 注册会话存储
    if not container.has_service(FileSessionStore):
        from pathlib import Path
        session_store = FileSessionStore(Path("./sessions"))
        container.register_instance(FileSessionStore, session_store)
    
    # 注册Git管理器
    if not container.has_service(GitManager):
        from src.application.sessions.git_manager import create_git_manager
        git_manager = create_git_manager(use_mock=True)  # 使用模拟管理器避免Git依赖
        container.register_instance(GitManager, git_manager)
    
    # 注册工作流管理器
    if not container.has_service(WorkflowManager):
        workflow_manager = WorkflowManager(container.get(IConfigLoader))
        container.register_instance(WorkflowManager, workflow_manager)
    
    # 注册会话管理器 - 确保所有依赖都已注册
    if not container.has_service(ISessionManager):
        # 确保依赖服务已注册
        if not container.has_service(WorkflowManager):
            workflow_manager = WorkflowManager(container.get(IConfigLoader))
            container.register_instance(WorkflowManager, workflow_manager)
        if not container.has_service(FileSessionStore):
            from pathlib import Path
            session_store = FileSessionStore(Path("./sessions"))
            container.register_instance(FileSessionStore, session_store)
        if not container.has_service(GitManager):
            from src.application.sessions.git_manager import create_git_manager
            git_manager = create_git_manager(use_mock=True)
            container.register_instance(GitManager, git_manager)
            
        session_manager = SessionManager(
            workflow_manager=container.get(WorkflowManager),
            session_store=container.get(FileSessionStore),
            git_manager=container.get(GitManager)
        )
        container.register_instance(ISessionManager, session_manager)


# 自动设置容器
setup_container()
@cli.command("help")
@click.argument("command", required=False)
@click.pass_context
def help_command(ctx: click.Context, command: Optional[str]) -> None:
    """显示帮助信息"""
    if command:
        help_manager.show_command_help(command)
    else:
        help_manager.show_main_help()


@cli.command("run")
@click.option(
    "--config", 
    type=click.Path(exists=True, path_type=Path), 
    help="指定TUI配置文件路径"
)
@click.pass_context
def run(ctx: click.Context, config: Optional[Path] = None) -> None:
    """启动TUI交互界面"""
    try:
        from ..tui.app import TUIApp
        app = TUIApp(config)
        app.run()
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "启动TUI界面失败")


@cli.command("quickstart")
@click.pass_context
def quickstart(ctx: click.Context) -> None:
    """显示快速开始指南"""
    help_manager.show_quick_start()

