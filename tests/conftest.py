"""pytest配置文件"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "log_level": "INFO",
        "log_outputs": [{"type": "console", "level": "INFO", "format": "text"}],
        "secret_patterns": ["sk-[a-zA-Z0-9]{20,}", "\\w+@\\w+\\.\\w+", "1\\d{10}"],
        "env": "test",
        "debug": False,
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 设置环境变量
    import os

    os.environ["AGENT_TEST_MODE"] = "true"

    yield

    # 清理环境变量
    if "AGENT_TEST_MODE" in os.environ:
        del os.environ["AGENT_TEST_MODE"]
