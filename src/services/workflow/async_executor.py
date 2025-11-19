"""
异步工作流执行器实现
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable, Union, cast
from abc import ABC, abstractmethod

from src.core.workflow.config.config import GraphConfig
from src.core.workflow.states import WorkflowState, update_state_with_message, BaseMessage, LCBaseMessage, AIMessage
from core.workflow.graph.nodes.registry import NodeRegistry, get_global_registry
from src.services.workflow.state_converter import WorkflowStateConverter
from src.infrastructure.async_utils.event_loop_manager import AsyncLock, AsyncContextManager
from typing import TYPE_CHECKING

from src.core.llm.interfaces import ILLMClient
from src.core.tools.executor import IToolExecutor

logger = logging.getLogger(__name__)


class IAsyncNodeExecutor(ABC):
    """异步节点执行器接口"""
    
    @abstractmethod
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行节点逻辑"""
        pass