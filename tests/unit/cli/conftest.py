"""CLI测试配置和共享fixture"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, Any, Generator

from src.infrastructure import TestContainer
from src.presentation.cli.error_handler import CLIErrorHandler
from src.presentation.cli.help import HelpManager
from src.presentation.cli.run_command import RunCommand
from src.prompts.agent_state import AgentState


@pytest.fixture(scope="session")
def cli_test_config() -> Dict[str, Any]:
    """CLI测试配置"""
    return {
        "log_level": "INFO",
        "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
        "secret_patterns": ["sk-[a-zA-Z0-9]{20,}", "\\w+@\\w+\\.\\w+", "1\\d{10}"],
        "env": "test",
        "debug": False,
        "cli": {
            "default_format": "table",
            "max_sessions_display": 50,
            "confirm_destructive": True
        }
    }


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """临时目录fixture"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_config_file(temp_dir: str) -> str:
    """临时配置文件fixture"""
    config_path = os.path.join(temp_dir, "test_config.yaml")
    with open(config_path, "w") as f:
        f.write("""
name: test_config
version: 1.0
settings:
  log_level: INFO
  debug: false
""")
    return config_path


@pytest.fixture
def temp_workflow_file(temp_dir: str) -> str:
    """临时工作流文件fixture"""
    workflow_path = os.path.join(temp_dir, "test_workflow.yaml")
    with open(workflow_path, "w") as f:
        f.write("""
name: test_workflow
description: 测试工作流
steps:
  - name: step1
    type: test
    config:
      param1: value1
""")
    return workflow_path


@pytest.fixture
def temp_agent_file(temp_dir: str) -> str:
    """临时代理配置文件fixture"""
    agent_path = os.path.join(temp_dir, "test_agent.yaml")
    with open(agent_path, "w") as f:
        f.write("""
name: test_agent
type: assistant
model: gpt-3.5-turbo
settings:
  temperature: 0.7
  max_tokens: 1000
""")
    return agent_path


@pytest.fixture
def mock_session_data() -> Dict[str, Any]:
    """模拟会话数据fixture"""
    return {
        "session_id": "test-session-12345678",
        "metadata": {
            "session_id": "test-session-12345678",
            "workflow_config_path": "test_workflow.yaml",
            "agent_config_path": "test_agent.yaml",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T01:00:00.000Z",
            "status": "active",
            "user_id": "test_user"
        },
        "state": {
            "messages": [],
            "current_step": 0,
            "variables": {}
        }
    }


@pytest.fixture
def mock_agent_state() -> AgentState:
    """模拟代理状态fixture"""
    state = AgentState()
    state.session_id = "test-session-12345678"
    state.workflow_id = "test_workflow"
    state.current_step = 0
    return state


@pytest.fixture
def cli_error_handler() -> CLIErrorHandler:
    """CLI错误处理器fixture"""
    return CLIErrorHandler(verbose=False)


@pytest.fixture
def cli_error_handler_verbose() -> CLIErrorHandler:
    """详细模式CLI错误处理器fixture"""
    return CLIErrorHandler(verbose=True)


@pytest.fixture
def help_manager() -> HelpManager:
    """帮助管理器fixture"""
    return HelpManager()


@pytest.fixture
def run_command() -> RunCommand:
    """运行命令fixture"""
    return RunCommand(config_path=None, verbose=False)


@pytest.fixture
def run_command_verbose() -> RunCommand:
    """详细模式运行命令fixture"""
    return RunCommand(config_path="test_config.yaml", verbose=True)


@pytest.fixture
def test_container() -> Generator[TestContainer, None, None]:
    """测试容器fixture"""
    with TestContainer() as container:
        container.setup_basic_configs()
        yield container


@pytest.fixture
def mock_session_manager():
    """模拟会话管理器fixture"""
    manager = Mock()
    manager.list_sessions.return_value = []
    manager.get_session.return_value = None
    manager.create_session.return_value = "test-session-123"
    manager.restore_session.return_value = (Mock(), Mock())
    manager.delete_session.return_value = True
    manager.save_session.return_value = None
    return manager


@pytest.fixture
def mock_workflow_manager():
    """模拟工作流管理器fixture"""
    manager = Mock()
    manager.load_workflow.return_value = Mock()
    manager.validate_workflow.return_value = True
    return manager


@pytest.fixture
def mock_config_loader():
    """模拟配置加载器fixture"""
    loader = Mock()
    loader.load.return_value = {"name": "test_config"}
    loader.validate.return_value = True
    return loader


@pytest.fixture
def mock_console():
    """模拟控制台fixture"""
    console = Mock()
    console.print.return_value = None
    console.input.return_value = "test input"
    return console


@pytest.fixture
def sample_sessions_list():
    """示例会话列表fixture"""
    return [
        {
            "metadata": {
                "session_id": "session-1",
                "workflow_config_path": "workflow1.yaml",
                "created_at": "2023-01-01T00:00:00.000Z",
                "updated_at": "2023-01-01T01:00:00.000Z",
                "status": "active"
            }
        },
        {
            "metadata": {
                "session_id": "session-2",
                "workflow_config_path": "workflow2.yaml",
                "created_at": "2023-01-02T00:00:00.000Z",
                "updated_at": "2023-01-02T01:00:00.000Z",
                "status": "completed"
            }
        }
    ]


@pytest.fixture(autouse=True)
def setup_cli_test_environment() -> Generator[None, None, None]:
    """设置CLI测试环境"""
    # 设置环境变量
    os.environ["AGENT_TEST_MODE"] = "true"
    os.environ["AGENT_CLI_TEST"] = "true"
    
    yield
    
    # 清理环境变量
    if "AGENT_TEST_MODE" in os.environ:
        del os.environ["AGENT_TEST_MODE"]
    if "AGENT_CLI_TEST" in os.environ:
        del os.environ["AGENT_CLI_TEST"]


@pytest.fixture
def mock_pyproject_toml(temp_dir: str) -> str:
    """模拟pyproject.toml文件fixture"""
    pyproject_path = os.path.join(temp_dir, "pyproject.toml")
    with open(pyproject_path, "w") as f:
        f.write("""
[project]
name = "modular-agent"
version = "0.1.0"
description = "模块化代理框架"
""")
    return pyproject_path


@pytest.fixture
def mock_git_manager():
    """模拟Git管理器fixture"""
    manager = Mock()
    manager.init_repo.return_value = True
    manager.commit.return_value = "commit_hash"
    manager.get_status.return_value = {"clean": True}
    return manager


@pytest.fixture
def mock_file_session_store():
    """模拟文件会话存储fixture"""
    store = Mock()
    store.save.return_value = True
    store.load.return_value = {}
    store.delete.return_value = True
    store.list.return_value = []
    return store


@pytest.fixture
def cli_runner():
    """CLI运行器fixture"""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_tui_app():
    """模拟TUI应用fixture"""
    app = Mock()
    app.run.return_value = None
    return app


# 测试数据生成器
@pytest.fixture
def generate_test_session_data():
    """生成测试会话数据的函数"""
    def _generate(session_id: str, status: str = "active") -> Dict[str, Any]:
        return {
            "metadata": {
                "session_id": session_id,
                "workflow_config_path": f"workflow_{session_id}.yaml",
                "created_at": "2023-01-01T00:00:00.000Z",
                "updated_at": "2023-01-01T01:00:00.000Z",
                "status": status
            }
        }
    return _generate


@pytest.fixture
def generate_test_error():
    """生成测试错误的函数"""
    def _generate(error_type: str, message: str) -> Exception:
        if error_type == "FileNotFoundError":
            return FileNotFoundError(message)
        elif error_type == "ValueError":
            return ValueError(message)
        elif error_type == "RuntimeError":
            return RuntimeError(message)
        else:
            return Exception(message)
    return _generate