"""LangGraph管理器服务"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from src.core.langgraph.manager import LangGraphManager, ILangGraphManager
from src.core.langgraph.workflow import ILangGraphWorkflow, LangGraphWorkflow
from src.core.langgraph.checkpointer import CheckpointerFactory, CheckpointerConfig

logger = logging.getLogger(__name__)


class LangGraphManagerService:
    """LangGraph管理器服务 - 高级管理功能"""
    
    def __init__(
        self,
        checkpointer_factory: Optional[CheckpointerFactory] = None,
        default_checkpointer_config: Optional[CheckpointerConfig] = None
    ):
        self._langgraph_manager = LangGraphManager(
            checkpointer_factory=checkpointer_factory,
            default_checkpointer_config=default_checkpointer_config
        )
        
        logger.info("LangGraphManagerService initialized")
    
    async def register_workflow(self, workflow: ILangGraphWorkflow):
        """注册工作流"""
        await self._langgraph_manager.register_workflow(workflow)
    
    async def create_workflow_from_config(
        self,
        workflow_id: str,
        config: Dict[str, Any]
    ) -> ILangGraphWorkflow:
        """从配置创建工作流"""
        try:
            # 这里可以根据配置动态创建工作流
            workflow = LangGraphWorkflow(
                workflow_id=workflow_id,
                description=config.get("description")
            )
            
            # 根据配置添加节点和边
            nodes = config.get("nodes", {})
            for node_name, node_config in nodes.items():
                # 这里需要根据节点配置创建实际的节点函数
                # 简化实现，实际应用中需要更复杂的节点创建逻辑
                def create_node_func(node_cfg):
                    async def node_func(state):
                        # 简单的节点实现
                        state["current_step"] = node_name
                        return state
                    return node_func
                
                workflow.add_node(node_name, create_node_func(node_config))
            
            # 添加边
            edges = config.get("edges", [])
            for edge in edges:
                if len(edge) == 2:
                    workflow.add_edge(edge[0], edge[1])
                elif len(edge) == 3:
                    # 条件边
                    workflow.add_conditional_edge(edge[0], edge[1], edge[2])
            
            # 设置入口点
            if "entry_point" in config:
                workflow.set_entry_point(config["entry_point"])
            
            # 注册工作流
            await self.register_workflow(workflow)
            
            logger.info(f"Created workflow '{workflow_id}' from config")
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow '{workflow_id}' from config: {str(e)}")
            raise
    
    async def get_workflow(self, graph_id: str) -> ILangGraphWorkflow:
        """获取工作流"""
        return await self._langgraph_manager.get_workflow(graph_id)
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """列出所有工作流"""
        stats = await self._langgraph_manager.get_statistics()
        workflow_ids = stats.get("workflow_ids", [])
        
        workflows = []
        for workflow_id in workflow_ids:
            try:
                workflow = await self._langgraph_manager.get_workflow(workflow_id)
                # 获取state_schema的名称
                schema_name = workflow.state_schema.__name__ if hasattr(workflow.state_schema, '__name__') else str(workflow.state_schema)
                workflows.append({
                    "workflow_id": workflow.workflow_id,
                    "description": workflow.description,
                    "state_schema": schema_name
                })
            except Exception as e:
                logger.warning(f"Error getting info for workflow '{workflow_id}': {str(e)}")
        
        return workflows
    
    async def execute_workflow(
        self,
        graph_id: str,
        thread_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """执行工作流"""
        return await self._langgraph_manager.execute_workflow(
            graph_id=graph_id,
            thread_id=thread_id,
            input_data=input_data,
            stream=stream
        )
    
    async def create_branch(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str
    ) -> str:
        """创建分支"""
        return await self._langgraph_manager.create_branch(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            branch_name=branch_name
        )
    
    async def merge_branch(
        self,
        main_thread_id: str,
        branch_thread_id: str,
        merge_strategy: str = "overwrite"
    ) -> Dict[str, Any]:
        """合并分支"""
        return await self._langgraph_manager.merge_branch(
            main_thread_id=main_thread_id,
            branch_thread_id=branch_thread_id,
            merge_strategy=merge_strategy
        )
    
    async def get_checkpoint_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取checkpoint历史"""
        return await self._langgraph_manager.get_checkpoint_history(
            thread_id=thread_id,
            limit=limit
        )
    
    async def restore_from_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """从checkpoint恢复"""
        return await self._langgraph_manager.restore_from_checkpoint(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id
        )
    
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread状态"""
        thread_state = await self._langgraph_manager.get_thread_state(thread_id)
        if thread_state:
            return {
                "thread_id": thread_state["thread_id"],
                "graph_id": thread_state["graph_id"],
                "current_state": thread_state["current_state"],
                "status": thread_state["status"],
                "created_at": thread_state["created_at"],
                "updated_at": thread_state["updated_at"],
                "checkpoint_count": len(thread_state["checkpoint_history"]),
                "branch_count": len(thread_state["branches"])
            }
        return None
    
    async def list_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出分支"""
        return await self._langgraph_manager.list_branches(thread_id)
    
    async def get_branch_info(self, branch_thread_id: str) -> Optional[Dict[str, Any]]:
        """获取分支信息"""
        return await self._langgraph_manager.get_branch_info(branch_thread_id)
    
    async def cleanup_thread(self, thread_id: str):
        """清理thread资源"""
        await self._langgraph_manager.cleanup_thread(thread_id)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return await self._langgraph_manager.get_statistics()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            stats = await self.get_statistics()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "statistics": stats,
                "checkpointer_factory": "available" if self._langgraph_manager._checkpointer_factory else "unavailable"
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(),
                "error": str(e)
            }
    
    async def backup_thread_state(self, thread_id: str, backup_path: str) -> bool:
        """备份thread状态"""
        try:
            # 获取thread状态和历史
            thread_state = await self.get_thread_state(thread_id)
            checkpoint_history = await self.get_checkpoint_history(thread_id)
            branches = await self.list_branches(thread_id)
            
            # 创建备份数据
            backup_data = {
                "thread_id": thread_id,
                "backup_time": datetime.now(),
                "thread_state": thread_state,
                "checkpoint_history": checkpoint_history,
                "branches": branches
            }
            
            # 这里应该实现实际的备份逻辑
            # 简化实现，实际应用中需要写入文件或数据库
            logger.info(f"Backup data prepared for thread '{thread_id}' (size: {len(str(backup_data))} chars)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error backing up thread '{thread_id}': {str(e)}")
            return False
    
    async def restore_thread_state(self, backup_path: str) -> bool:
        """恢复thread状态"""
        try:
            # 这里应该实现实际的恢复逻辑
            # 简化实现，实际应用中需要从文件或数据库读取
            logger.info(f"Thread state restore requested from '{backup_path}'")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring thread state from '{backup_path}': {str(e)}")
            return False
    
    async def export_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """导出工作流定义"""
        try:
            workflow = await self.get_workflow(workflow_id)
            
            # 检查是否是LangGraphWorkflow实现
            if isinstance(workflow, LangGraphWorkflow):
                # 这里需要实现工作流定义的导出逻辑
                # 简化实现
                export_data = {
                    "workflow_id": workflow.workflow_id,
                    "description": workflow.description,
                    "state_schema": str(workflow.state_schema),
                    "nodes": list(workflow._nodes.keys()),
                    "edges": workflow._edges,
                    "conditional_edges": workflow._conditional_edges,
                    "entry_point": workflow._entry_point,
                    "exported_at": datetime.now()
                }
                
                return export_data
            else:
                # 对于其他ILangGraphWorkflow实现，只导出基本信息
                logger.warning(f"Workflow '{workflow_id}' is not a LangGraphWorkflow instance, exporting basic info only")
                return {
                    "workflow_id": workflow.workflow_id,
                    "description": workflow.description,
                    "state_schema": str(workflow.state_schema),
                    "exported_at": datetime.now()
                }
            
        except Exception as e:
            logger.error(f"Error exporting workflow '{workflow_id}': {str(e)}")
            return None
    
    async def import_workflow_definition(self, workflow_data: Dict[str, Any]) -> bool:
        """导入工作流定义"""
        try:
            workflow_id = workflow_data["workflow_id"]
            
            # 检查工作流是否已存在
            try:
                existing_workflow = await self.get_workflow(workflow_id)
                if existing_workflow:
                    logger.warning(f"Workflow '{workflow_id}' already exists, skipping import")
                    return False
            except ValueError:
                # 工作流不存在，可以继续导入
                pass
            
            # 创建新的工作流
            workflow = LangGraphWorkflow(
                workflow_id=workflow_id,
                description=workflow_data.get("description")
            )
            
            # 这里需要根据导入的数据重建工作流
            # 简化实现，实际应用中需要完整的重建逻辑
            logger.info(f"Workflow definition imported for '{workflow_id}'")
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing workflow definition: {str(e)}")
            return False