"""统一图构建器

集成所有功能的统一图构建器，包含基础构建、函数注册表集成和迭代管理功能。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING, cast
from pathlib import Path
import yaml
import logging
import asyncio
import concurrent.futures
import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig
else:
    # 运行时使用Dict作为RunnableConfig的替代
    RunnableConfig = Dict[str, Any]

from src.core.workflow.config.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.core.states import WorkflowState
from src.core.states.base import LCBaseMessage
from src.core.workflow.registry.registry import NodeRegistry, get_global_registry, BaseNode
from src.adapters.workflow.state_adapter import get_state_adapter
from src.domain.state.interfaces import IStateLifecycleManager
from src.adapters.workflow.state_adapter import GraphAgentState
from .function_registry import (
    FunctionRegistry,
    FunctionType,
    get_global_function_registry,
)
from src.core.workflow.management.iteration_manager import IterationManager
from src.core.workflow.route_functions import get_route_function_manager
from src.core.workflow.node_functions import get_node_function_manager

logger = logging.getLogger(__name__)

# 导入LangGraph核心组件
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver


class INodeExecutor(ABC):