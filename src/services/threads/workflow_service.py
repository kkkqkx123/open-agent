"""工作流执行服务"""

from typing import AsyncGenerator, Dict, Any, Optional, List
import logging
from datetime import datetime

from interfaces.state import IWorkflowState as WorkflowState
from src.interfaces.threads.storage import IThreadRepository
from src.core.threads.entities import Thread, ThreadStatus
from src.core.common.exceptions import ValidationError, StorageNotFoundError as EntityNotFoundError

logger = logging.getLogger(__name__)


class WorkflowThreadService:
    """工作流执行服务"""
    
    def __init__(
        self,
        thread_repository: IThreadRepository
    ):
        """初始化工作流服务
        
        Args:
            thread_repository: 线程仓储接口
        """
        self._thread_repository = thread_repository
    
    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """执行工作流
        
        Args:
            thread_id: Thread ID
            config: 运行配置
            initial_state: 初始状态
            
        Returns:
            执行结果
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 验证线程状态
            if thread.status not in [ThreadStatus.ACTIVE, ThreadStatus.PAUSED]:
                raise ValidationError(f"Cannot execute workflow on thread with status {thread.status.value}")
            
            # 更新线程状态为执行中（如果需要）
            # 这里简化处理，实际应该有执行中状态
            logger.info(f"Starting workflow execution for thread {thread_id}")
            
            # TODO: 实际的工作流执行逻辑
            # 这里需要与工作流引擎集成
            # 目前返回模拟结果
            
            # 模拟执行结果
            result_state = {
                "thread_id": thread_id,
                "status": "completed",
                "result": "Workflow executed successfully",
                "execution_time": 0.1,
                "steps_executed": 1
            }
            
            # 更新线程统计
            thread.increment_message_count()
            await self._thread_repository.update(thread)
            
            logger.info(f"Workflow execution completed for thread {thread_id}")
            
            # 返回工作流状态对象
            # 这里需要根据实际的WorkflowState接口来创建对象
            # 暂时返回模拟对象
            return MockWorkflowState(result_state)
            
        except Exception as e:
            logger.error(f"Failed to execute workflow for thread {thread_id}: {e}")
            raise ValidationError(f"Failed to execute workflow: {str(e)}")
    
    async def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流
        
        Args:
            thread_id: Thread ID
            config: 运行配置
            initial_state: 初始状态
            
        Yields:
            中间状态
        """
        try:
            # 验证线程存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise EntityNotFoundError(f"Thread {thread_id} not found")
            
            # 验证线程状态
            if thread.status not in [ThreadStatus.ACTIVE, ThreadStatus.PAUSED]:
                raise ValidationError(f"Cannot stream workflow on thread with status {thread.status.value}")
            
            logger.info(f"Starting workflow streaming for thread {thread_id}")
            
            # TODO: 实际的流式工作流执行逻辑
            # 这里需要与工作流引擎集成
            # 目前返回模拟流式结果
            
            # 模拟流式执行步骤
            steps: List[Dict[str, Any]] = [
                {"step": 1, "status": "starting", "message": "Initializing workflow"},
                {"step": 2, "status": "running", "message": "Processing nodes"},
                {"step": 3, "status": "running", "message": "Executing actions"},
                {"step": 4, "status": "completing", "message": "Finalizing results"},
                {"step": 5, "status": "completed", "message": "Workflow completed"}
            ]
            
            for step in steps:
                # 添加时间戳和线程ID
                step_value = step.get("step", 0)
                if isinstance(step_value, (int, float, str)):
                    progress = int(step_value) * 20
                else:
                    progress = 0
                    
                step.update({
                    "thread_id": thread_id,
                    "timestamp": "2024-01-01T00:00:00Z",  # 模拟时间戳
                    "progress": progress  # 进度百分比
                })
                
                yield step
                
                # 模拟处理延迟
                import asyncio
                await asyncio.sleep(0.1)
            
            # 更新线程统计
            thread.increment_message_count()
            await self._thread_repository.update(thread)
            
            logger.info(f"Workflow streaming completed for thread {thread_id}")
            
        except Exception as e:
            logger.error(f"Failed to stream workflow for thread {thread_id}: {e}")
            raise ValidationError(f"Failed to stream workflow: {str(e)}")


class MockWorkflowState(WorkflowState):
    """模拟工作流状态对象
    
    TODO: 替换为实际的WorkflowState实现
    """
    
    def __init__(self, state_data: Dict[str, Any]):
        self._state_data = state_data.copy()
        self._messages: List[Any] = []
        self._fields = state_data.copy()
        self._metadata: Dict[str, Any] = {}
        self._id = state_data.get("thread_id", "")
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._complete = state_data.get("status") == "completed"
    
    # IState 接口实现
    def get_data(self, key: str, default: Any = None) -> Any:
        """从状态中获取数据"""
        return self._state_data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """在状态中设置数据"""
        self._state_data[key] = value
        self._updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """从状态中获取元数据"""
        return self._metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """在状态中设置元数据"""
        self._metadata[key] = value
        self._updated_at = datetime.now()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self._id if self._id else None
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._id = id
        self._updated_at = datetime.now()
    
    def get_created_at(self) -> datetime:
        """获取创建时间戳"""
        return self._created_at
    
    def get_updated_at(self) -> datetime:
        """获取最后更新时间戳"""
        return self._updated_at
    
    def is_complete(self) -> bool:
        """检查状态是否完成"""
        return self._complete
    
    def mark_complete(self) -> None:
        """将状态标记为完成"""
        self._complete = True
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典表示"""
        result = self._state_data.copy()
        result.update({
            "id": self._id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "complete": self._complete,
            "metadata": self._metadata.copy(),
            "messages": [str(msg) for msg in self._messages],
            "fields": self._fields.copy()
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockWorkflowState':
        """从字典创建状态实例"""
        instance = cls(data)
        instance._id = data.get("id", "")
        instance._complete = data.get("complete", False)
        instance._metadata = data.get("metadata", {}).copy()
        instance._fields = data.get("fields", {}).copy()
        if "created_at" in data:
            instance._created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            instance._updated_at = datetime.fromisoformat(data["updated_at"])
        return instance
    
    # IWorkflowState 接口实现
    @property
    def messages(self) -> List[Any]:
        """消息列表"""
        return self._messages.copy()
    
    @property
    def fields(self) -> Dict[str, Any]:
        """字段字典"""
        return self._fields.copy()
    
    @property
    def values(self) -> Dict[str, Any]:
        """状态值字典"""
        return self._state_data.copy()
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        return self._fields.get(key, default)
    
    def set_field(self, key: str, value: Any) -> WorkflowState:
        """创建包含新字段值的状态"""
        new_state = MockWorkflowState(self._state_data)
        new_state._fields = self._fields.copy()
        new_state._fields[key] = value
        new_state._messages = self._messages.copy()
        new_state._metadata = self._metadata.copy()
        new_state._id = self._id
        new_state._created_at = self._created_at
        new_state._updated_at = datetime.now()
        new_state._complete = self._complete
        return new_state
    
    def with_messages(self, messages: List[Any]) -> WorkflowState:
        """创建包含新消息的状态"""
        new_state = MockWorkflowState(self._state_data)
        new_state._fields = self._fields.copy()
        new_state._messages = messages.copy()
        new_state._metadata = self._metadata.copy()
        new_state._id = self._id
        new_state._created_at = self._created_at
        new_state._updated_at = datetime.now()
        new_state._complete = self._complete
        return new_state
    
    def with_metadata(self, metadata: Dict[str, Any]) -> WorkflowState:
        """创建包含新元数据的状态"""
        new_state = MockWorkflowState(self._state_data)
        new_state._fields = self._fields.copy()
        new_state._messages = self._messages.copy()
        new_state._metadata = metadata.copy()
        new_state._id = self._id
        new_state._created_at = self._created_at
        new_state._updated_at = datetime.now()
        new_state._complete = self._complete
        return new_state
    
    def add_message(self, message: Any) -> None:
        """添加消息"""
        self._messages.append(message)
        self._updated_at = datetime.now()
    
    def get_messages(self) -> List[Any]:
        """获取消息列表"""
        return self._messages.copy()
    
    def get_last_message(self) -> Any | None:
        """获取最后一条消息"""
        return self._messages[-1] if self._messages else None
    
    def copy(self) -> WorkflowState:
        """创建状态的深拷贝"""
        new_state = MockWorkflowState(self._state_data)
        new_state._fields = self._fields.copy()
        new_state._messages = self._messages.copy()
        new_state._metadata = self._metadata.copy()
        new_state._id = self._id
        new_state._created_at = self._created_at
        new_state._updated_at = datetime.now()
        new_state._complete = self._complete
        return new_state
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值（字典式访问）"""
        return self._state_data.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """设置状态值"""
        self._state_data[key] = value
        self._updated_at = datetime.now()
    
    # 保留原有的属性方法以保持兼容性
    @property
    def thread_id(self) -> str:
        """线程ID"""
        return str(self._state_data.get("thread_id", ""))
    
    @property
    def status(self) -> str:
        """状态"""
        return str(self._state_data.get("status", "unknown"))
    
    @property
    def result(self) -> Any:
        """结果"""
        return self._state_data.get("result")
    
    @property
    def execution_time(self) -> float:
        """执行时间"""
        return float(self._state_data.get("execution_time", 0.0))
    
    @property
    def steps_executed(self) -> int:
        """执行的步骤数"""
        return int(self._state_data.get("steps_executed", 0))