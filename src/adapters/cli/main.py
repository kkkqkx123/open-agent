"""CLI主入口文件"""

import click
from typing import Optional

from . import commands
from src.adapters.tui.app import TUIApp


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="启用详细输出")
@click.option("--config", "-c", type=click.Path(), help="指定配置文件路径")
@click.pass_context
def main(ctx: click.Context, verbose: bool, config: Optional[str]) -> None:
    """模块化代理框架命令行工具"""
    # 确保上下文对象存在
    ctx.ensure_object(dict)
    
    # 存储全局选项
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config


@main.command()
@click.option("--workflow", "-w", required=True, help="工作流配置文件路径")
@click.option("--agent", "-a", help="Agent配置文件路径")
@click.option("--session", "-s", help="会话ID（用于恢复会话）")
@click.option("--tui", is_flag=True, help="使用TUI界面")
@click.pass_context
def run(ctx: click.Context, workflow: str, agent: Optional[str], session: Optional[str], tui: bool) -> None:
    """运行代理工作流"""
    if tui:
        # 启动TUI界面
        app = TUIApp()
        app.run()
    else:
        # 命令行模式运行
        from .run_command import RunCommand
        cmd = RunCommand(ctx.obj.get("config"), ctx.obj.get("verbose"))
        cmd.execute(workflow, agent, session)


if __name__ == "__main__":
    commands.cli()