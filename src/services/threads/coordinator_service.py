"""线程协调器服务实现"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.core.threads.interfaces import IThreadCore
from src.core.threads.entities import ThreadStatus, Thread, ThreadMetadata
from src.interfaces.threads import IThreadCoordinatorService, IThreadRepository
from src.core.common.exceptions import ValidationError, StorageNotFoundError as EntityNotFoundError
from .repository_adapter import ThreadRepositoryAdapter


class ThreadCoordinatorService(IThreadCoordinatorService):
    """线程协调器业务服务实现"""
    
    def __init__(
        self,
        thread_core: IThreadCore,
        thread_repository: IThreadRepository
    ):
        self._thread_core = thread_core
        self._thread_repository = ThreadRepositoryAdapter(thread_repository)
        self._coordination_registry = {}  # 协调状态注册表
    
    async def coordinate_thread_creation(
        self,
        thread_config: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """协调线程创建"""
        coordination_id = f"coord_create_{datetime.now().timestamp()}"
        
        try:
            # 初始化协调状态
            self._coordination_registry[coordination_id] = {
                "status": "initiated",
                "step": "validation",
                "started_at": datetime.now(),
                "errors": []
            }
            
            # 步骤1: 验证配置
            validation_result = await self._validate_thread_config(thread_config)
            if not validation_result["valid"]:
                self._coordination_registry[coordination_id]["status"] = "failed"
                self._coordination_registry[coordination_id]["errors"].extend(
                    validation_result["errors"]
                )
                return {
                    "coordination_id": coordination_id,
                    "status": "failed",
                    "errors": validation_result["errors"]
                }
            
            self._coordination_registry[coordination_id]["step"] = "creation"
            
            # 步骤2: 创建线程
            try:
                thread_id = thread_config.get("thread_id") or str(uuid.uuid4())
                thread_data = self._thread_core.create_thread(
                    thread_id=thread_id,
                    graph_id=thread_config.get("graph_id"),
                    thread_type=thread_config.get("thread_type", "main"),
                    metadata=thread_config.get("metadata"),
                    config=thread_config.get("config")
                )
                
                # 保存线程
                thread = Thread.from_dict(thread_data)
                await self._thread_repository.save_thread(thread)
                
                self._coordination_registry[coordination_id]["thread_id"] = thread_id
            except Exception as e:
                self._coordination_registry[coordination_id]["status"] = "failed"
                self._coordination_registry[coordination_id]["errors"].append(str(e))
                return {
                    "coordination_id": coordination_id,
                    "status": "failed",
                    "errors": [str(e)]
                }
            
            self._coordination_registry[coordination_id]["step"] = "association"
            
            # 步骤3: 关联会话（如果提供）
            if session_context and "session_id" in session_context:
                try:
                    await self._thread_repository.associate_with_session(
                        thread_id,
                        session_context["session_id"]
                    )
                except Exception as e:
                    # 关联失败不视为致命错误
                    self._coordination_registry[coordination_id]["warnings"] = [str(e)]
            
            self._coordination_registry[coordination_id]["status"] = "completed"
            self._coordination_registry[coordination_id]["step"] = "finished"
            
            return {
                "coordination_id": coordination_id,
                "thread_id": thread_id,
                "status": "completed",
                "steps_completed": ["validation", "creation", "association"]
            }
            
        except Exception as e:
            # 确保coordination_id已定义
            if coordination_id in self._coordination_registry:
                self._coordination_registry[coordination_id]["status"] = "failed"
                self._coordination_registry[coordination_id]["errors"].append(str(e))
            
            return {
                "coordination_id": coordination_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def coordinate_thread_transition(
        self,
        thread_id: str,
        current_status: str,
        target_status: str,
        transition_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """协调线程状态转换"""
        coordination_id = f"coord_transition_{datetime.now().timestamp()}"
        
        try:
            # 验证线程存在
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 验证状态转换
            if not await self._can_transition(thread.status.value, target_status):
                raise ValidationError(
                    f"Invalid transition from {thread.status.value} to {target_status}"
                )
            
            # 执行状态转换
            success = thread.transition_to(ThreadStatus(target_status))
            
            if success:
                await self._thread_repository.update_thread(thread_id, thread)
            
            # 记录协调结果
            self._coordination_registry[coordination_id] = {
                "thread_id": thread_id,
                "transition": f"{current_status} -> {target_status}",
                "success": success,
                "timestamp": datetime.now()
            }
            
            return success
            
        except Exception as e:
            self._coordination_registry[coordination_id] = {
                "thread_id": thread_id,
                "transition": f"{current_status} -> {target_status}",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
            return False
    
    async def coordinate_checkpoint_creation(
        self,
        thread_id: str,
        checkpoint_config: Dict[str, Any],
        coordination_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """协调检查点创建"""
        coordination_id = f"coord_checkpoint_{datetime.now().timestamp()}"
        
        try:
            # 验证线程存在
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 验证线程状态
            if thread.status not in [ThreadStatus.ACTIVE, ThreadStatus.PAUSED]:
                raise ValidationError(f"Cannot create checkpoint in thread status: {thread.status}")
            
            # 这里简化处理，实际应用中可能需要调用检查点服务
            checkpoint_id = f"checkpoint_{datetime.now().timestamp()}"
            
            # 更新线程检查点计数
            thread.increment_checkpoint_count()
            await self._thread_repository.update_thread(thread_id, thread)
            
            # 记录协调结果
            self._coordination_registry[coordination_id] = {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "status": "created",
                "timestamp": datetime.now()
            }
            
            return checkpoint_id
            
        except Exception as e:
            self._coordination_registry[coordination_id] = {
                "thread_id": thread_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }
            raise
    
    async def coordinate_thread_recovery(
        self,
        thread_id: str,
        recovery_point: str,
        recovery_strategy: str = "latest_checkpoint"
    ) -> bool:
        """协调线程恢复"""
        coordination_id = f"coord_recovery_{datetime.now().timestamp()}"
        
        try:
            # 验证线程存在
            thread = await self._thread_repository.get_thread(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 验证恢复策略
            valid_strategies = ["latest_checkpoint", "specific_checkpoint", "initial_state"]
            if recovery_strategy not in valid_strategies:
                raise ValidationError(f"Unsupported recovery strategy: {recovery_strategy}")
            
            # 这里简化处理，实际应用中可能需要调用检查点服务进行恢复
            success = True  # 假设恢复成功
            
            if success:
                # 更新线程状态
                thread.status = ThreadStatus.ACTIVE
                thread.updated_at = datetime.now()
                await self._thread_repository.update_thread(thread_id, thread)
            
            # 记录协调结果
            self._coordination_registry[coordination_id] = {
                "thread_id": thread_id,
                "recovery_point": recovery_point,
                "strategy": recovery_strategy,
                "success": success,
                "timestamp": datetime.now()
            }
            
            return success
            
        except Exception as e:
            self._coordination_registry[coordination_id] = {
                "thread_id": thread_id,
                "recovery_point": recovery_point,
                "strategy": recovery_strategy,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now()
            }
            return False
    
    async def get_coordination_status(self, thread_id: str) -> Dict[str, Any]:
        """获取协调状态"""
        try:
            # 筛选与指定线程相关的协调记录
            thread_coordination = {
                k: v for k, v in self._coordination_registry.items()
                if v.get("thread_id") == thread_id
            }
            
            return {
                "thread_id": thread_id,
                "total_coordination_events": len(thread_coordination),
                "recent_events": list(thread_coordination.values())[-10:],  # 最近10个事件
                "status_summary": self._generate_status_summary(thread_coordination)
            }
            
        except Exception as e:
            return {
                "thread_id": thread_id,
                "error": str(e),
                "status": "unknown"
            }
    
    async def validate_coordination_integrity(self, thread_id: str) -> bool:
        """验证协调完整性"""
        try:
            # 获取线程的协调历史
            coordination_history = [
                v for k, v in self._coordination_registry.items()
                if v.get("thread_id") == thread_id
            ]
            
            if not coordination_history:
                return True  # 没有协调历史，视为完整
            
            # 检查最近的协调事件是否成功
            recent_events = sorted(
                coordination_history,
                key=lambda x: x.get("timestamp", datetime.min),
                reverse=True
            )
            
            # 如果有失败的协调事件，检查是否有后续的恢复事件
            for event in recent_events:
                if event.get("success") is False and not event.get("recovery_attempted"):
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def _validate_thread_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证线程配置"""
        errors = []
        
        # 基本字段验证
        if not config.get("thread_type"):
            errors.append("thread_type is required")
        
        if not config.get("status"):
            errors.append("status is required")
        else:
            try:
                ThreadStatus(config["status"])
            except ValueError:
                errors.append(f"Invalid status: {config['status']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _can_transition(self, current_status: str, target_status: str) -> bool:
        """检查状态转换是否有效"""
        try:
            current = ThreadStatus(current_status)
            target = ThreadStatus(target_status)
            
            # 定义有效的状态转换
            valid_transitions = {
                ThreadStatus.ACTIVE: [ThreadStatus.PAUSED, ThreadStatus.COMPLETED, ThreadStatus.FAILED, ThreadStatus.ARCHIVED, ThreadStatus.BRANCHED],
                ThreadStatus.PAUSED: [ThreadStatus.ACTIVE, ThreadStatus.COMPLETED, ThreadStatus.FAILED, ThreadStatus.ARCHIVED],
                ThreadStatus.COMPLETED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED],
                ThreadStatus.FAILED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED],
                ThreadStatus.ARCHIVED: [ThreadStatus.ACTIVE],
                ThreadStatus.BRANCHED: [ThreadStatus.ACTIVE, ThreadStatus.ARCHIVED]
            }
            
            return target in valid_transitions.get(current, [])
            
        except ValueError:
            return False
    
    def _generate_status_summary(self, coordination_history: Dict[str, Any]) -> Dict[str, Any]:
        """生成状态摘要"""
        if not coordination_history:
            return {"status": "no_history", "last_event": None}
        
        # 获取最近的事件
        recent_events = sorted(
            coordination_history.values(),
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=True
        )
        
        last_event = recent_events[0]
        
        return {
            "status": "healthy" if last_event.get("success", True) else "needs_attention",
            "last_event": {
                "type": last_event.get("transition") or last_event.get("checkpoint_id") or "unknown",
                "success": last_event.get("success", True),
                "timestamp": last_event.get("timestamp", datetime.now()).isoformat()
            }
        }