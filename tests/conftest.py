"""pytest配置文件"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_config():
    """示例配置数据"""
    return {
        "log_level": "INFO",
        "log_outputs": [
            {
                "type": "console",
                "level": "INFO",
                "format": "text"
            }
        ],
        "secret_patterns": [
            "sk-[a-zA-Z0-9]{20,}",
            "\\w+@\\w+\\.\\w+"
        ],
        "env": "test",
        "debug": True
    }


@pytest.fixture
def sample_llm_config():
    """示例LLM配置数据"""
    return {
        "group": "openai_group",
        "model_type": "openai",
        "model_name": "gpt-4",
        "api_key": "${AGENT_OPENAI_KEY}",
        "parameters": {
            "temperature": 0.3,
            "top_p": 0.9
        }
    }