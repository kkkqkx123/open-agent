"""CLI帮助文档模块"""

from rich.console import Console
from rich.markdown import Markdown


class HelpManager:
    """帮助管理器"""
    
    def __init__(self) -> None:
        self.console = Console()
        
    def show_main_help(self) -> None:
        """显示主帮助信息"""
        help_text = """
# 模块化代理框架

模块化代理框架是一个基于图工作流的多代理系统，支持多种LLM集成和灵活的工具系统。

## 主要命令

### 会话管理
- `session list` - 列出所有会话
- `session restore <session_id>` - 恢复指定会话
- `session destroy <session_id>` - 删除指定会话

### 配置管理
- `config check` - 检查配置和环境
- `version` - 显示版本信息

### 运行命令
- `run --workflow <workflow_config>` - 运行工作流
- `run --workflow <workflow_config> --tui` - 使用TUI界面运行

## 全局选项

- `--verbose, -v` - 启用详细输出
- `--config, -c <path>` - 指定配置文件路径

## 示例

```bash
# 检查环境
agent config check

# 列出所有会话
agent session list

# 运行工作流
agent run --workflow configs/workflows/example.yaml

# 使用TUI界面运行
agent run --workflow configs/workflows/example.yaml --tui

# 恢复会话
agent session restore <session_id>
```
"""
        
        markdown = Markdown(help_text)
        self.console.print(markdown)
    
    def show_command_help(self, command: str) -> None:
        """显示特定命令的帮助"""
        help_texts = {
            "session": """
# 会话管理命令

会话管理命令用于管理工作流会话，包括创建、恢复、列出和删除会话。

## 子命令

### session list
列出所有现有会话。

**选项:**
- `--format, -f` - 输出格式，支持 `table` 或 `json`，默认为 `table`

**示例:**
```bash
agent session list
agent session list --format json
```

### session restore <session_id>
恢复指定会话并继续交互。

**参数:**
- `session_id` - 要恢复的会话ID

**示例:**
```bash
agent session restore 12345678-1234-1234-1234-123456789abc
```

### session destroy <session_id>
删除指定会话。

**参数:**
- `session_id` - 要删除的会话ID

**选项:**
- `--confirm` - 跳过确认提示，直接删除

**示例:**
```bash
agent session destroy 12345678-1234-1234-1234-123456789abc
agent session destroy 12345678-1234-1234-1234-123456789abc --confirm
```
""",
            "config": """
# 配置管理命令

配置管理命令用于检查系统配置和环境。

## 子命令

### config check
检查系统环境和配置是否满足要求。

**选项:**
- `--format, -f` - 输出格式，支持 `table` 或 `json`，默认为 `table`
- `--output, -o` - 输出文件路径（仅JSON格式）

**示例:**
```bash
agent config check
agent config check --format json --output report.json
```
""",
            "run": """
# 运行命令

运行命令用于启动和执行工作流。

## 选项

- `--workflow, -w` - 工作流配置文件路径（必需）
- `--agent, -a` - Agent配置文件路径（可选）
- `--session, -s` - 会话ID，用于恢复现有会话（可选）
- `--tui` - 使用TUI界面而不是命令行界面

## 示例

```bash
# 运行新工作流
agent run --workflow configs/workflows/example.yaml

# 使用特定agent配置
agent run --workflow configs/workflows/example.yaml --agent configs/agents/assistant.yaml

# 恢复现有会话
agent run --session 12345678-1234-1234-1234-123456789abc

# 使用TUI界面
agent run --workflow configs/workflows/example.yaml --tui
```
""",
            "version": """
# 版本命令

显示框架的版本信息。

## 示例

```bash
agent version
```
"""
        }
        
        if command in help_texts:
            markdown = Markdown(help_texts[command])
            self.console.print(markdown)
        else:
            self.console.print(f"[red]未知命令: {command}[/red]")
            self.console.print("使用 `--help` 查看可用命令。")
    
    def show_error_help(self, error_type: str) -> None:
        """显示错误相关帮助"""
        error_helps = {
            "SessionNotFound": """
# 会话未找到错误

指定的会话ID不存在。

## 解决方案

1. 使用 `agent session list` 查看所有可用会话
2. 确保会话ID正确
3. 如果会话已被删除，需要创建新会话

## 相关命令

- `agent session list` - 列出所有会话
- `agent run --workflow <config>` - 创建新会话
""",
            "WorkflowNotFound": """
# 工作流未找到错误

指定的工作流配置文件不存在或无法加载。

## 解决方案

1. 检查工作流配置文件路径是否正确
2. 确保配置文件格式正确（YAML格式）
3. 检查配置文件内容是否符合规范

## 相关命令

- `agent config check` - 检查配置
""",
            "EnvironmentError": """
# 环境错误

系统环境不满足运行要求。

## 解决方案

1. 运行 `agent config check` 检查详细的环境信息
2. 确保Python版本满足要求（>= 3.13）
3. 安装缺失的依赖包

## 相关命令

- `agent config check` - 检查环境配置
"""
        }
        
        if error_type in error_helps:
            markdown = Markdown(error_helps[error_type])
            self.console.print(markdown)
        else:
            self.console.print(f"[red]未知错误类型: {error_type}[/red]")
            self.console.print("使用 `agent config check` 检查系统状态。")
    
    def show_quick_start(self) -> None:
        """显示快速开始指南"""
        quick_start_text = """
# 快速开始指南

## 1. 检查环境

首先检查系统环境是否满足要求：

```bash
agent config check
```

## 2. 运行工作流

使用预定义的工作流配置运行代理：

```bash
agent run --workflow configs/workflows/example.yaml
```

## 3. 使用TUI界面

如果更喜欢图形界面，可以使用TUI模式：

```bash
agent run --workflow configs/workflows/example.yaml --tui
```

## 4. 管理会话

查看所有会话：

```bash
agent session list
```

恢复之前的会话：

```bash
agent session restore <session_id>
```

## 5. 获取帮助

获取主帮助信息：

```bash
agent --help
```

获取特定命令的帮助：

```bash
agent session --help
agent config --help
```

## 更多信息

查看完整文档：`docs/` 目录
"""
        
        markdown = Markdown(quick_start_text)
        self.console.print(markdown)