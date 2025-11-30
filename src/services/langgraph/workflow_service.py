"""LangGraph工作流服务"""

from typing import Any, Dict, List, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from src.core.langgraph.manager import LangGraphManager, ILangGraphManager
from src.core.langgraph.workflow import ILangGraphWorkflow, LangGraphWorkflow
from src.core.langgraph.checkpointer import CheckpointerFactory, CheckpointerConfig
from src.core.threads.entities import Thread, ThreadStatus
from src.interfaces.threads.service import IThreadService
from src.interfaces.threads.storage import IThreadRepository

logger = logging.getLogger(__name__)


class ILangGraphWorkflowService(ABC):
    """LangGraph工作流服务接口"""
    
    @abstractmethod
    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        pass
    
    @abstractmethod
    def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        pass
    
    @abstractmethod
    async def register_workflow(self, workflow: ILangGraphWorkflow) -> None:
        """注册工作流"""
        pass


class LangGraphWorkflowService(ILangGraphWorkflowService):
    """LangGraph工作流服务实现"""
    
    def __init__(
        self,
        langgraph_manager: ILangGraphManager,
        thread_repository: IThreadRepository,
        thread_service: Optional[IThreadService] = None,
        checkpointer_factory: Optional[CheckpointerFactory] = None
    ):
        self._langgraph_manager = langgraph_manager
        self._thread_repository = thread_repository
        self._thread_service = thread_service
        self._checkpointer_factory = checkpointer_factory
        
        logger.info("LangGraphWorkflowService initialized")
    
    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流"""
        thread: Optional[Thread] = None
        try:
            # 获取Thread实体
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValueError(f"Thread '{thread_id}' not found")
            
            # 验证Thread状态
            if thread.status not in [ThreadStatus.ACTIVE, ThreadStatus.PAUSED]:
                raise ValueError(f"Thread '{thread_id}' is in '{thread.status}' state, cannot execute workflow")
            
            # 准备执行配置
            execution_config = self._prepare_execution_config(thread, config)
            
            # 执行LangGraph工作流
            logger.info(f"Executing workflow for thread '{thread_id}' with graph_id '{thread.graph_id}'")
            
            result = await self._langgraph_manager.execute_workflow(
                graph_id=thread.graph_id or "",
                thread_id=thread_id,
                input_data=initial_state,
                stream=False
            )
            
            # 同步状态到Thread
            await self._sync_state_to_thread(thread, result)
            
            # 更新Thread状态
            if result.get("current_step") == "completed":
                thread.transition_to(ThreadStatus.COMPLETED)
            elif result.get("current_step") == "error":
                thread.transition_to(ThreadStatus.FAILED)
            
            await self._thread_repository.update(thread)
            
            logger.info(f"Workflow execution completed for thread '{thread_id}'")
            return result
            
        except Exception as e:
            logger.error(f"Error executing workflow for thread '{thread_id}': {str(e)}")
            
            # 更新Thread状态为失败
            if thread is not None:
                thread.transition_to(ThreadStatus.FAILED)
                await self._thread_repository.update(thread)
            
            raise
    
    def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        return self._stream_workflow_impl(thread_id, config, initial_state)
    
    async def _stream_workflow_impl(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """内部流式执行工作流实现"""
        thread: Optional[Thread] = None
        try:
            # 获取Thread实体
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValueError(f"Thread '{thread_id}' not found")
            
            # 验证Thread状态
            if thread.status not in [ThreadStatus.ACTIVE, ThreadStatus.PAUSED]:
                raise ValueError(f"Thread '{thread_id}' is in '{thread.status}' state, cannot execute workflow")
            
            # 准备执行配置
            execution_config = self._prepare_execution_config(thread, config)
            
            # 流式执行LangGraph工作流
            logger.info(f"Streaming workflow for thread '{thread_id}' with graph_id '{thread.graph_id}'")
            
            result = self._langgraph_manager.execute_workflow(
                graph_id=thread.graph_id or "",
                thread_id=thread_id,
                input_data=initial_state,
                stream=True
            )
            
            async for chunk in result:  # type: ignore
                # 同步状态到Thread
                await self._sync_state_to_thread(thread, chunk)
                await self._thread_repository.update(thread)
                
                yield chunk
            
            # 检查最终状态
            final_state = await self._langgraph_manager.get_thread_state(thread_id)
            if final_state and final_state.get("current_step") == "completed":
                thread.transition_to(ThreadStatus.COMPLETED)
            elif final_state and final_state.get("current_step") == "error":
                thread.transition_to(ThreadStatus.FAILED)
            
            await self._thread_repository.update(thread)
            
            logger.info(f"Workflow streaming completed for thread '{thread_id}'")
            
        except Exception as e:
            logger.error(f"Error streaming workflow for thread '{thread_id}': {str(e)}")
            
            # 更新Thread状态为失败
            if thread is not None:
                thread.transition_to(ThreadStatus.FAILED)
                await self._thread_repository.update(thread)
            
            raise
    
    async def register_workflow(self, workflow: ILangGraphWorkflow):
        """注册工作流"""
        try:
            await self._langgraph_manager.register_workflow(workflow)
            logger.info(f"Registered workflow: {workflow.workflow_id}")
        except Exception as e:
            logger.error(f"Error registering workflow '{workflow.workflow_id}': {str(e)}")
            raise
    
    async def pause_workflow(self, thread_id: str) -> bool:
        """暂停工作流执行"""
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValueError(f"Thread '{thread_id}' not found")
            
            if thread.status != ThreadStatus.ACTIVE:
                logger.warning(f"Thread '{thread_id}' is not active, cannot pause")
                return False
            
            # 转换状态为暂停
            if thread.transition_to(ThreadStatus.PAUSED):
                await self._thread_repository.update(thread)
                logger.info(f"Paused workflow for thread '{thread_id}'")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error pausing workflow for thread '{thread_id}': {str(e)}")
            raise
    
    async def resume_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """恢复工作流执行"""
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValueError(f"Thread '{thread_id}' not found")
            
            if thread.status != ThreadStatus.PAUSED:
                raise ValueError(f"Thread '{thread_id}' is not paused, cannot resume")
            
            # 转换状态为活跃
            if not thread.transition_to(ThreadStatus.ACTIVE):
                raise ValueError(f"Cannot transition thread '{thread_id}' to active state")
            
            await self._thread_repository.update(thread)
            
            # 继续执行工作流
            return await self.execute_workflow(thread_id, config)
            
        except Exception as e:
            logger.error(f"Error resuming workflow for thread '{thread_id}': {str(e)}")
            raise
    
    async def get_workflow_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        try:
            state = await self._langgraph_manager.get_thread_state(thread_id)
            # Cast result for type compatibility
            return state  # type: ignore
        except Exception as e:
            logger.error(f"Error getting workflow state for thread '{thread_id}': {str(e)}")
            return None
    
    async def get_workflow_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取工作流执行历史"""
        try:
            return await self._langgraph_manager.get_checkpoint_history(thread_id, limit)
        except Exception as e:
            logger.error(f"Error getting workflow history for thread '{thread_id}': {str(e)}")
            return []
    
    def _prepare_execution_config(
        self, 
        thread: Thread, 
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """准备执行配置"""
        # 基础配置
        execution_config = {
            "configurable": {
                "thread_id": thread.langgraph_thread_id or thread.id,
                "graph_id": thread.graph_id
            }
        }
        
        # 合并用户配置
        if config:
            execution_config.update(config)
        
        # 合并Thread配置
        if thread.config:
            execution_config.update(thread.config)
        
        return execution_config
    
    async def _sync_state_to_thread(self, thread: Thread, langgraph_state: Dict[str, Any]):
        """同步LangGraph状态到Thread"""
        try:
            # 更新Thread状态
            thread.sync_with_langgraph_state(langgraph_state)
            
            # 更新LangGraph特定字段
            if "checkpoint_id" in langgraph_state:
                thread.update_langgraph_checkpoint(langgraph_state["checkpoint_id"])
            
            # 更新消息计数
            if "messages" in langgraph_state:
                thread.message_count = len(langgraph_state["messages"])
            
            # 更新元数据
            if "metadata" in langgraph_state:
                thread.metadata.custom_data.update(langgraph_state["metadata"])
            
        except Exception as e:
            logger.error(f"Error syncing state to thread '{thread.id}': {str(e)}")
            # 不抛出异常，避免影响主流程
    
    async def cleanup_thread_resources(self, thread_id: str):
        """清理Thread相关资源"""
        try:
            await self._langgraph_manager.cleanup_thread(thread_id)
            logger.info(f"Cleaned up LangGraph resources for thread '{thread_id}'")
        except Exception as e:
            logger.error(f"Error cleaning up resources for thread '{thread_id}': {str(e)}")
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """获取工作流统计信息"""
        try:
            return await self._langgraph_manager.get_statistics()
        except Exception as e:
            logger.error(f"Error getting workflow statistics: {str(e)}")
            return {}