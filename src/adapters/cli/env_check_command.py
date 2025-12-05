"""环境检查命令行工具"""

import click
import json
from typing import Tuple
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .architecture_command import ArchitectureCommand
from .environment import IEnvironmentChecker, EnvironmentChecker
from .check_result import CheckResult
from typing import Optional


class EnvironmentCheckCommand:
    """环境检查命令"""

    def __init__(self, checker: Optional[IEnvironmentChecker] = None):
        self.checker = checker or EnvironmentChecker()
        # 确保checker是EnvironmentChecker实例
        env_checker = self.checker if isinstance(self.checker, EnvironmentChecker) else EnvironmentChecker()
        self.arch_command = ArchitectureCommand(env_checker=env_checker)
        self.console = Console()

    def run(
        self, format_type: str = "table", output_file: Optional[str] = None
    ) -> None:
        """运行环境检查"""
        # 委托给ArchitectureCommand执行环境检查
        self.arch_command.run_env_check(format_type=format_type, output_file=output_file)

    def _print_table_report(self, results: list[CheckResult]) -> None:
        """打印表格格式报告"""
        # 创建汇总表格
        summary_table = Table(title="Environment Check Summary")
        summary_table.add_column("Status", style="bold")
        summary_table.add_column("Count", justify="right")

        pass_count = len([r for r in results if r.is_pass()])
        warning_count = len([r for r in results if r.is_warning()])
        error_count = len([r for r in results if r.is_error()])

        summary_table.add_row("[green]PASS[/green]", str(pass_count))
        summary_table.add_row("[yellow]WARNING[/yellow]", str(warning_count))
        summary_table.add_row("[red]ERROR[/red]", str(error_count))
        summary_table.add_row("TOTAL", str(len(results)))

        self.console.print(summary_table)
        self.console.print()

        # 创建详细结果表格
        details_table = Table(title="Environment Check Details")
        details_table.add_column("Component", style="cyan")
        details_table.add_column("Status", style="bold")
        details_table.add_column("Message")

        for result in results:
            status_color = {"PASS": "green", "WARNING": "yellow", "ERROR": "red"}.get(
                result.status, "white"
            )

            details_table.add_row(
                result.component,
                f"[{status_color}]{result.status}[/{status_color}]",
                result.message,
            )

        self.console.print(details_table)

        # 如果有错误或警告，显示详细信息
        warnings_and_errors = [r for r in results if not r.is_pass()]
        if warnings_and_errors:
            self.console.print("\n[bold]Warnings and Errors:[/bold]")
            for result in warnings_and_errors:
                color = "yellow" if result.is_warning() else "red"
                panel = Panel(
                    result.message,
                    title=f"[{color}]{result.component}[/{color}]",
                    border_style=color,
                )
                self.console.print(panel)

    def _print_json_report(
        self, report: Dict[str, Any], output_file: Optional[str] = None
    ) -> None:
        """打印JSON格式报告"""
        json_output = json.dumps(report, indent=2)

        if output_file:
            with open(output_file, "w") as f:
                f.write(json_output)
            self.console.print(f"Report saved to {output_file}")
        else:
            self.console.print(json_output)


# Click命令行接口
@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file (only for JSON format)"
)
@click.option(
    "--python-version", type=str, help='Minimum Python version (e.g., "3.13.0")'
)
def check_env(format: str, output: str, python_version: str) -> None:
    """Check the environment for required dependencies and configuration."""

    # 创建环境检查器
    if python_version:
        parts = python_version.split(".")
        if len(parts) < 3:
            parts += ["0"] * (3 - len(parts))
        version_tuple = (int(parts[0]), int(parts[1]), int(parts[2]))
        checker = EnvironmentChecker(min_python_version=version_tuple)
    else:
        checker = EnvironmentChecker()

    # 创建并运行命令
    command = EnvironmentCheckCommand(checker)
    command.run(format_type=format, output_file=output)


if __name__ == "__main__":
    check_env()