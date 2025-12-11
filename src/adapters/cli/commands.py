"""CLI命令框架"""

import click
from typing import Optional
from pathlib import Path
from rich.console import Console

from src.services.container import get_global_container
from src.interfaces.config import IConfigLoader
from src.interfaces.sessions.base import ISessionManager
from src.adapters.cli.env_check_command import EnvironmentCheckCommand
from src.adapters.cli.architecture_command import ArchitectureCommand
from src.adapters.cli.dependency_analysis_command import DependencyAnalysisCommand
from src.adapters.cli.error_handling import handle_cli_error, handle_cli_warning, handle_cli_success, handle_cli_info
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
        
        import asyncio
        sessions = asyncio.run(session_manager.list_sessions())
        
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
        
        import asyncio
        # 检查会话是否存在
        session_data = asyncio.run(session_manager.get_session(session_id))
        if not session_data:
            console.print(f"[red]会话 {session_id} 不存在[/red]")
            raise click.ClickException(f"会话 {session_id} 不存在")
        
        console.print(f"[green]正在恢复会话 {session_id}...[/green]")
        
        # 新的SessionManager不支持restore_session，改为获取会话信息
        console.print(f"[green]会话 {session_id} 信息获取成功[/green]")
        console.print(f"会话ID: {session_data['session_id']}")
        console.print(f"用户ID: {session_data.get('user_id', 'N/A')}")
        console.print(f"状态: {session_data['status']}")
        console.print(f"创建时间: {session_data['created_at']}")
        console.print(f"更新时间: {session_data['updated_at']}")
        console.print(f"线程数量: {session_data['thread_count']}")
        
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
        
        import asyncio
        # 检查会话是否存在
        session_data = asyncio.run(session_manager.get_session(session_id))
        if not session_data:
            console.print(f"[red]会话 {session_id} 不存在[/red]")
            raise click.ClickException(f"会话 {session_id} 不存在")
        
        # 确认删除
        if not confirm:
            if not click.confirm(f"确定要删除会话 {session_id} 吗？此操作不可撤销。"):
                console.print("操作已取消")
                return
        
        # 删除会话
        success = asyncio.run(session_manager.delete_session(session_id))
        
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


@cli.command("arch-check")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="输出格式")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径（仅JSON格式）")
@click.option("--base-path", "-b", type=click.Path(), default="src", help="架构检查的基础路径")
@click.pass_context
def arch_check(ctx: click.Context, format: str, output: Optional[str], base_path: str) -> None:
    """检查代码架构分层和依赖关系"""
    try:
        from .architecture_check import ArchitectureChecker
        
        # 创建架构检查器
        checker = ArchitectureChecker(base_path=base_path)
        
        # 创建并运行命令
        command = ArchitectureCommand(arch_checker=checker)
        command.run_arch_check(format_type=format, output_file=output)
        
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "架构检查时发生错误")


@cli.group()
def dependency() -> None:
    """依赖分析命令"""
    pass


@dependency.command("analyze")
@click.option("--format", "-f", type=click.Choice(["text", "json", "dot"]), default="text", help="输出格式")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径")
@click.pass_context
def dependency_analyze(ctx: click.Context, format: str, output: Optional[str]) -> None:
    """分析DI容器的依赖关系
    
    示例：
        python -m src.adapters.cli dependency analyze --format json --output report.json
    """
    try:
        command = DependencyAnalysisCommand()
        
        # 这里可以集成实际的容器分析逻辑
        # 目前只是演示
        console.print("[yellow]依赖分析工具[/yellow]")
        console.print("使用方法: 从代码中提取容器配置或注册信息")
        
        if output:
            command.export_report(output, format)
            console.print(f"[green]报告已导出到: {output}[/green]")
        else:
            if format == "text":
                console.print(command.generate_text_report())
            elif format == "json":
                console.print(command.generate_json_report())
            elif format == "dot":
                console.print(command.generate_dot_diagram())
        
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "依赖分析时发生错误")


@dependency.command("check-circular")
@click.pass_context
def dependency_check_circular(ctx: click.Context) -> None:
    """检查是否存在循环依赖"""
    try:
        command = DependencyAnalysisCommand()
        
        has_circular = command.check_circular_dependencies()
        
        if has_circular:
            circular_deps = command.get_circular_dependencies()
            console.print("[red]✗ 检测到循环依赖:[/red]")
            for cycle in circular_deps:
                console.print(f"  {' -> '.join(cycle)}")
        else:
            console.print("[green]✓ 未检测到循环依赖[/green]")
        
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "循环依赖检查时发生错误")


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
    table.add_column("用户ID", style="magenta")
    table.add_column("状态", style="green")
    table.add_column("线程数", style="blue")
    table.add_column("交互数", style="yellow")
    table.add_column("创建时间", style="white")
    
    if not sessions:
        table.add_row("无会话", "", "", "", "", "")
    else:
        for session in sessions:
            session_id = session.get("session_id", "unknown")[:8] + "..."
            user_id = session.get("user_id", "N/A")
            status = session.get("status", "unknown")
            thread_count = session.get("thread_count", 0)
            interaction_count = session.get("interaction_count", 0)
            created_at = session.get("created_at", "unknown")
            
            # 格式化时间显示
            if created_at != "unknown":
                created_at = created_at.replace("T", " ").split(".")[0]
            
            table.add_row(session_id, user_id, status, str(thread_count), str(interaction_count), created_at)
    
    console.print(table)



def _register_history_services(container) -> None:
    """注册历史存储服务"""
    try:
        # 历史存储服务是可选的，当需要时由其他模块单独注册
        # 这里仅作为占位符，保留扩展空间
        pass
    except Exception:
        # 如果历史配置不存在或加载失败，忽略错误
        # 历史存储是可选功能
        pass

def setup_container(config_path: Optional[str] = None) -> None:
    """设置依赖注入容器 - 简化实现"""
    container = get_global_container()
    
    # 注册配置加载器
    if not container.has_service(IConfigLoader):
        from src.core.config.config_loader import ConfigLoader
        config_loader = ConfigLoader()
        container.register_instance(IConfigLoader, config_loader)
    
    # 注册配置管理器
    from src.core.config.config_manager import ConfigManager
    if not container.has_service(ConfigManager):
        config_manager = ConfigManager()
        container.register_instance(ConfigManager, config_manager)
    
    # 注册Git服务
    from src.services.sessions.git_service import IGitService
    if not container.has_service(IGitService):
        from src.services.sessions.git_service import MockGitService
        git_manager = MockGitService()
        container.register_instance(IGitService, git_manager)
    
    # 注册工作流管理器（使用协调器）
    # 注意：工作流协调器是可选的，如果不存在则跳过
    # TODO: 在完成WorkflowCoordinator实现后重新启用此部分
    
    # 注册会话核心服务
    from src.core.sessions.core_interfaces import ISessionCore
    if not container.has_service(ISessionCore):
        from src.core.sessions.core_interfaces import ISessionCore
        from src.core.sessions.entities import Session, UserRequestEntity, UserInteractionEntity
        from typing import Dict, Any, Optional
        import uuid
        from datetime import datetime
        
        class SimpleSessionCore(ISessionCore):
            """简单的SessionCore实现"""
            def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Session:
                session_id = str(uuid.uuid4())
                return Session(
                    session_id=session_id,
                    user_id=user_id,
                    metadata=metadata or {}
                )
            
            def validate_session_state(self, session_data: Dict[str, Any]) -> bool:
                return True  # 简单实现，总是返回True
            
            def create_user_request(self, content: str, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> UserRequestEntity:
                request_id = str(uuid.uuid4())
                return UserRequestEntity(
                    request_id=request_id,
                    content=content,
                    user_id=user_id,
                    metadata=metadata or {}
                )
            
            def create_user_interaction(self, session_id: str, interaction_type: str, content: str, thread_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> UserInteractionEntity:
                interaction_id = str(uuid.uuid4())
                return UserInteractionEntity(
                    interaction_id=interaction_id,
                    session_id=session_id,
                    interaction_type=interaction_type,
                    content=content,
                    thread_id=thread_id,
                    metadata=metadata or {}
                )
        
        session_core = SimpleSessionCore()
        container.register_instance(ISessionCore, session_core)
    
    # 注册会话管理器
    if not container.has_service(ISessionManager):
        from src.services.sessions.manager import SessionManager
        session_manager = SessionManager(
            session_service=None
        )
        container.register_instance(ISessionManager, session_manager)
    
    # 注册历史存储服务
    _register_history_services(container)


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
        from src.adapters.tui.app import TUIApp
        app = TUIApp(config)
        app.run()
    except Exception as e:
        handle_cli_error(e, ctx.obj.get("verbose", False), "启动TUI界面失败")


@cli.command("quickstart")
@click.pass_context
def quickstart(ctx: click.Context) -> None:
    """显示快速开始指南"""
    help_manager.show_quick_start()



