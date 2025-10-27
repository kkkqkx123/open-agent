"""工作流配置模型测试"""

import pytest
from src.infrastructure.graph.config import (
    GraphConfig as WorkflowConfig,
    NodeConfig,
    EdgeConfig,
    GraphStateConfig as StateSchemaConfig,
    EdgeType
)


class TestStateSchemaConfig:
    """状态模式配置测试"""