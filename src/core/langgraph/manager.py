"""LangGraph管理器 - 核心管理类"""

from typing import Any, Dict, List, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import asyncio
import uuid

from .workflow import ILangGraphWorkflow, LangGraphWorkflow
from .checkpointer import CheckpointerFactory, CheckpointerManager, CheckpointerConfig
from .state import (
    LangGraphState,
    LangGraphThreadState,
    LangGraphCheckpointState,
    LangGraphMergeState,
    create_initial_state,
    create_checkpoint_state,
    create_thread_state
)

logger = logging.getLogger(__name__)


class ILangGraphManager(ABC):
    """LangGraph管理器接口"""
    
    @abstractmethod
    async def register_workflow(self, workflow: ILangGraphWorkflow) -> None:
        """注册工作流"""
        pass
    
    @abstractmethod
    async def get_workflow(self, graph_id: str) -> ILangGraphWorkflow:
        """获取LangGraph工作流"""
        pass
    
    @abstractmethod
    async def execute_workflow(
        self,
        graph_id: str,
        thread_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """执行工作流"""
        pass
    
    @abstractmethod
    async def create_branch(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str
    ) -> str:
        """创建LangGraph分支"""
        pass
    
    @abstractmethod
    async def get_checkpoint_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取checkpoint历史"""
        pass
    
    @abstractmethod
    async def restore_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """从checkpoint恢复"""
        pass
    
    @abstractmethod
    async def merge_branch(
        self,
        main_thread_id: str,
        branch_thread_id: str,
        merge_strategy: str = "overwrite"
    ) -> Dict[str, Any]:
        """合并分支到主线"""
        pass
    
    @abstractmethod
    async def get_thread_state(self, thread_id: str) -> Optional[LangGraphThreadState]:
        """获取thread状态"""
        pass
    
    @abstractmethod
    async def get_branch_info(self, branch_thread_id: str) -> Optional[Dict[str, Any]]:
        """获取分支信息"""
        pass
    
    @abstractmethod
    async def cleanup_thread(self, thread_id: str) -> None:
        """清理thread资源"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        pass


class LangGraphManager(ILangGraphManager):
    """LangGraph管理器实现"""
    
    def __init__(
        self,
        checkpointer_factory: Optional[CheckpointerFactory] = None,
        default_checkpointer_config: Optional[CheckpointerConfig] = None
    ):
        self._checkpointer_factory = checkpointer_factory or CheckpointerFactory(default_checkpointer_config)
        self._checkpointer_manager = CheckpointerManager(self._checkpointer_factory)
        
        # 工作流缓存
        self._workflows: Dict[str, ILangGraphWorkflow] = {}
        self._compiled_workflows: Dict[str, Any] = {}
        
        # Thread状态缓存
        self._thread_states: Dict[str, LangGraphThreadState] = {}
        
        # 分支管理
        self._branches: Dict[str, Dict[str, Any]] = {}
        
        logger.info("LangGraphManager initialized")
    
    async def register_workflow(self, workflow: ILangGraphWorkflow):
        """注册工作流"""
        workflow_id = workflow.workflow_id
        self._workflows[workflow_id] = workflow
        
        # 编译工作流
        checkpointer = await self._checkpointer_manager.get_checkpointer_for_thread(f"workflow_{workflow_id}")
        compiled_workflow = await workflow.compile(checkpointer)
        self._compiled_workflows[workflow_id] = compiled_workflow
        
        logger.info(f"Registered and compiled workflow: {workflow_id}")
    
    async def get_workflow(self, graph_id: str) -> ILangGraphWorkflow:
        """获取LangGraph工作流"""
        if graph_id not in self._workflows:
            raise ValueError(f"Workflow '{graph_id}' not found. Available workflows: {list(self._workflows.keys())}")
        
        return self._workflows[graph_id]
    
    async def get_compiled_workflow(self, graph_id: str, thread_id: str) -> Any:
        """获取编译后的工作流（特定thread）"""
        if graph_id not in self._compiled_workflows:
            await self.get_workflow(graph_id)  # 这会触发编译
        
        # 为特定thread获取专用的checkpointer
        checkpointer = await self._checkpointer_manager.get_checkpointer_for_thread(thread_id)
        
        # 重新编译以使用thread专用的checkpointer
        workflow = self._workflows[graph_id]
        return await workflow.compile(checkpointer)
    
    async def execute_workflow(
        self,
        graph_id: str,
        thread_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """执行工作流"""
        try:
            # 获取编译后的工作流
            compiled_workflow = await self.get_compiled_workflow(graph_id, thread_id)
            
            # 准备配置
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "graph_id": graph_id
                }
            }
            
            # 初始化thread状态
            if thread_id not in self._thread_states:
                self._thread_states[thread_id] = create_thread_state(thread_id, graph_id)
            
            # 执行工作流
            if stream:
                return self._stream_execute_workflow(compiled_workflow, input_data or {}, config)
            else:
                return await self._invoke_execute_workflow(compiled_workflow, input_data or {}, config)
                
        except Exception as e:
            logger.error(f"Error executing workflow '{graph_id}' for thread '{thread_id}': {str(e)}")
            raise
    
    async def _invoke_execute_workflow(
        self, 
        compiled_workflow: Any, 
        input_data: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """同步执行工作流"""
        thread_id = config["configurable"]["thread_id"]
        logger.info(f"Executing workflow for thread: {thread_id}")
        
        result = await compiled_workflow.ainvoke(input_data, config)
        
        # 更新thread状态
        if thread_id in self._thread_states:
            self._thread_states[thread_id]["current_state"] = result
            self._thread_states[thread_id]["updated_at"] = datetime.now()
        
        return result
    
    async def _stream_execute_workflow(
        self, 
        compiled_workflow: Any, 
        input_data: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        thread_id = config["configurable"]["thread_id"]
        logger.info(f"Streaming workflow for thread: {thread_id}")
        
        async for chunk in compiled_workflow.astream(input_data, config):
            yield chunk
            
            # 更新thread状态
            if thread_id in self._thread_states:
                self._thread_states[thread_id]["current_state"] = chunk
                self._thread_states[thread_id]["updated_at"] = datetime.now()
    
    async def create_branch(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str
    ) -> str:
        """创建LangGraph分支"""
        try:
            # 生成分支thread ID
            branch_thread_id = f"{thread_id}_branch_{branch_name}_{uuid.uuid4().hex[:8]}"
            
            # 获取原始thread状态
            if thread_id not in self._thread_states:
                raise ValueError(f"Thread '{thread_id}' not found")
            
            original_thread_state = self._thread_states[thread_id]
            
            # 创建分支专用的checkpoint
            branch_checkpointer = await self._checkpointer_manager.create_branch_checkpointer(
                thread_id, branch_thread_id, checkpoint_id
            )
            
            # 创建分支thread状态
            branch_thread_state = create_thread_state(branch_thread_id, original_thread_state["graph_id"])
            
            # 复制checkpoint状态
            if checkpoint_id:
                # 这里需要从checkpoint恢复状态到分支
                logger.info(f"Creating branch '{branch_name}' from checkpoint '{checkpoint_id}'")
            
            # 保存分支信息
            self._thread_states[branch_thread_id] = branch_thread_state
            self._branches[branch_thread_id] = {
                "parent_thread_id": thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_name": branch_name,
                "created_at": datetime.now(),
                "status": "ACTIVE"
            }
            
            logger.info(f"Created branch '{branch_name}' with thread ID: {branch_thread_id}")
            return branch_thread_id
            
        except Exception as e:
            logger.error(f"Error creating branch '{branch_name}' from thread '{thread_id}': {str(e)}")
            raise
    
    async def get_checkpoint_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取checkpoint历史"""
        try:
            checkpointer = await self._checkpointer_manager.get_checkpointer_for_thread(thread_id)
            
            # 获取checkpoint历史
            history = await self._checkpointer_manager.get_checkpoint_history(thread_id, limit)
            
            # 转换为标准格式
            formatted_history = []
            for checkpoint in history:
                formatted_history.append({
                    "checkpoint_id": checkpoint.get("checkpoint_id"),
                    "thread_id": thread_id,
                    "step": checkpoint.get("step", 0),
                    "timestamp": checkpoint.get("timestamp", datetime.now()),
                    "state_data": checkpoint.get("state", {}),
                    "metadata": checkpoint.get("metadata", {})
                })
            
            return formatted_history
            
        except Exception as e:
            logger.error(f"Error getting checkpoint history for thread '{thread_id}': {str(e)}")
            return []
    
    async def restore_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """从checkpoint恢复"""
        try:
            # 获取编译后的工作流
            if thread_id not in self._thread_states:
                raise ValueError(f"Thread '{thread_id}' not found")
            
            thread_state = self._thread_states[thread_id]
            graph_id = thread_state["graph_id"]
            compiled_workflow = await self.get_compiled_workflow(graph_id, thread_id)
            
            # 准备恢复配置
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "graph_id": graph_id,
                    "checkpoint_id": checkpoint_id
                }
            }
            
            # 从checkpoint恢复状态
            if hasattr(compiled_workflow, 'get_state'):
                state_info = await compiled_workflow.get_state(config)
                
                # 更新thread状态
                self._thread_states[thread_id]["current_state"] = state_info.values
                self._thread_states[thread_id]["updated_at"] = datetime.now()
                
                logger.info(f"Restored thread '{thread_id}' from checkpoint '{checkpoint_id}'")
                return state_info.values
            else:
                raise NotImplementedError("Checkpoint restoration not supported by this workflow")
                
        except Exception as e:
            logger.error(f"Error restoring thread '{thread_id}' from checkpoint '{checkpoint_id}': {str(e)}")
            raise
    
    async def merge_branch(
        self,
        main_thread_id: str,
        branch_thread_id: str,
        merge_strategy: str = "overwrite"
    ) -> Dict[str, Any]:
        """合并分支到主线"""
        try:
            # 验证分支存在
            if branch_thread_id not in self._branches:
                raise ValueError(f"Branch '{branch_thread_id}' not found")
            
            if main_thread_id not in self._thread_states:
                raise ValueError(f"Main thread '{main_thread_id}' not found")
            
            branch_info = self._branches[branch_thread_id]
            main_thread_state = self._thread_states[main_thread_id]
            branch_thread_state = self._thread_states[branch_thread_id]
            
            # 执行合并
            if merge_strategy == "overwrite":
                # 覆盖策略：直接用分支状态覆盖主线状态
                main_thread_state["current_state"] = branch_thread_state["current_state"].copy()
            elif merge_strategy == "merge":
                # 合并策略：智能合并
                merged_state = await self._merge_states(
                    main_thread_state["current_state"],
                    branch_thread_state["current_state"],
                    merge_strategy
                )
                main_thread_state["current_state"] = merged_state
            else:
                raise ValueError(f"Unsupported merge strategy: {merge_strategy}")
            
            # 更新时间戳
            main_thread_state["updated_at"] = datetime.now()
            
            # 标记分支为已合并
            self._branches[branch_thread_id]["status"] = "MERGED"
            self._branches[branch_thread_id]["merged_at"] = datetime.now()
            self._branches[branch_thread_id]["merged_into"] = main_thread_id
            
            # 合并checkpoint
            await self._checkpointer_manager.merge_checkpoints(
                main_thread_id, branch_thread_id, merge_strategy
            )
            
            logger.info(f"Merged branch '{branch_thread_id}' into main thread '{main_thread_id}' using '{merge_strategy}' strategy")
            
            return {
                "success": True,
                "main_thread_id": main_thread_id,
                "branch_thread_id": branch_thread_id,
                "merge_strategy": merge_strategy,
                "merged_at": datetime.now(),
                "merged_state": main_thread_state["current_state"]
            }
            
        except Exception as e:
            logger.error(f"Error merging branch '{branch_thread_id}' into main thread '{main_thread_id}': {str(e)}")
            raise
    
    async def _merge_states(
        self,
        main_state: Any,
        branch_state: Any,
        merge_strategy: str
    ) -> Any:
        """合并两个状态"""
        if merge_strategy == "overwrite":
            if isinstance(branch_state, dict):
                return branch_state.copy()
            return branch_state
        
        elif merge_strategy == "merge":
            # 简单的合并策略：合并所有键，分支值优先
            if isinstance(main_state, dict) and isinstance(branch_state, dict):
                merged_state = main_state.copy()
                merged_state.update(branch_state)
                return merged_state
            return branch_state
        
        else:
            raise ValueError(f"Unsupported merge strategy: {merge_strategy}")
    
    async def get_thread_state(self, thread_id: str) -> Optional[LangGraphThreadState]:
        """获取thread状态"""
        return self._thread_states.get(thread_id)
    
    async def get_branch_info(self, branch_thread_id: str) -> Optional[Dict[str, Any]]:
        """获取分支信息"""
        return self._branches.get(branch_thread_id)
    
    async def list_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有分支"""
        branches = []
        for branch_id, branch_info in self._branches.items():
            if branch_info.get("parent_thread_id") == thread_id:
                branches.append({
                    "branch_thread_id": branch_id,
                    **branch_info
                })
        return branches
    
    async def cleanup_thread(self, thread_id: str):
        """清理thread资源"""
        try:
            # 清理checkpoint
            await self._checkpointer_manager.cleanup_checkpointer(thread_id)
            
            # 清理thread状态
            if thread_id in self._thread_states:
                del self._thread_states[thread_id]
            
            # 清理相关分支
            branches_to_remove = []
            for branch_id, branch_info in self._branches.items():
                if branch_info.get("parent_thread_id") == thread_id or branch_id == thread_id:
                    branches_to_remove.append(branch_id)
            
            for branch_id in branches_to_remove:
                await self._checkpointer_manager.cleanup_checkpointer(branch_id)
                del self._branches[branch_id]
            
            logger.info(f"Cleaned up resources for thread: {thread_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up thread '{thread_id}': {str(e)}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            "total_workflows": len(self._workflows),
            "total_threads": len(self._thread_states),
            "total_branches": len(self._branches),
            "active_branches": len([b for b in self._branches.values() if b.get("status") == "ACTIVE"]),
            "merged_branches": len([b for b in self._branches.values() if b.get("status") == "MERGED"]),
            "workflow_ids": list(self._workflows.keys()),
            "thread_ids": list(self._thread_states.keys())
        }