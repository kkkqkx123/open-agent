"""工作流实体

定义工作流系统的数据实体。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.state import IWorkflowState
from src.interfaces.workflow.entities import (
    IWorkflow, IWorkflowExecution, INodeExecution,
    IWorkflowState as IWorkflowStateInterface, IExecutionResult, IWorkflowMetadata
)


class Workflow(IWorkflow):
    """工作流实体"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化工作流实体"""
        self._workflow_id = workflow_id
        self._name = name
        self._description = description
        self._version = version
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._metadata = metadata or {}

    # 实现IWorkflow接口的属性
    @property
    def workflow_id(self) -> str:
        """工作流ID"""
        return self._workflow_id

    @property
    def name(self) -> str:
        """工作流名称"""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """工作流描述"""
        return self._description

    @property
    def version(self) -> str:
        """版本"""
        return self._version

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]) -> None:
        """设置元数据"""
        self._metadata = value
        self._updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self._workflow_id,
            "name": self._name,
            "description": self._description,
            "version": self._version,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "metadata": self._metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """从字典创建实例"""
        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None,
            metadata=data.get("metadata", {})
        )


class WorkflowExecution(IWorkflowExecution):
    """工作流执行实体"""
    
    def __init__(
        self,
        execution_id: str,
        workflow_id: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化工作流执行实体"""
        self._execution_id = execution_id
        self._workflow_id = workflow_id
        self._status = status
        self._started_at = started_at
        self._completed_at = completed_at
        self._error = error
        self._metadata = metadata or {}

    # 实现IWorkflowExecution接口的属性
    @property
    def execution_id(self) -> str:
        """执行ID"""
        return self._execution_id

    @property
    def workflow_id(self) -> str:
        """工作流ID"""
        return self._workflow_id

    @property
    def status(self) -> str:
        """执行状态"""
        return self._status

    @property
    def started_at(self) -> datetime:
        """开始时间"""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """完成时间"""
        return self._completed_at

    @property
    def error(self) -> Optional[str]:
        """错误信息"""
        return self._error

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "execution_id": self._execution_id,
            "workflow_id": self._workflow_id,
            "status": self._status,
            "started_at": self._started_at.isoformat(),
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "error": self._error,
            "metadata": self._metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowExecution':
        """从字典创建实例"""
        return cls(
            execution_id=data["execution_id"],
            workflow_id=data["workflow_id"],
            status=data["status"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )


class NodeExecution(INodeExecution):
    """节点执行实体"""
    
    def __init__(
        self,
        execution_id: str,
        node_id: str,
        node_type: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        input_state: Optional[IWorkflowStateInterface] = None,
        output_state: Optional[IWorkflowStateInterface] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化节点执行实体"""
        self._execution_id = execution_id
        self._node_id = node_id
        self._node_type = node_type
        self._status = status
        self._started_at = started_at
        self._completed_at = completed_at
        self._input_state = input_state
        self._output_state = output_state
        self._error = error
        self._metadata = metadata or {}

    # 实现INodeExecution接口的属性
    @property
    def execution_id(self) -> str:
        """执行ID"""
        return self._execution_id

    @property
    def node_id(self) -> str:
        """节点ID"""
        return self._node_id

    @property
    def node_type(self) -> str:
        """节点类型"""
        return self._node_type

    @property
    def status(self) -> str:
        """执行状态"""
        return self._status

    @property
    def started_at(self) -> datetime:
        """开始时间"""
        return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """完成时间"""
        return self._completed_at

    @property
    def input_state(self) -> Optional[IWorkflowStateInterface]:
        """输入状态"""
        return self._input_state

    @property
    def output_state(self) -> Optional[IWorkflowStateInterface]:
        """输出状态"""
        return self._output_state

    @property
    def error(self) -> Optional[str]:
        """错误信息"""
        return self._error

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "execution_id": self._execution_id,
            "node_id": self._node_id,
            "node_type": self._node_type,
            "status": self._status,
            "started_at": self._started_at.isoformat(),
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "input_state": self._input_state.to_dict() if self._input_state else None,
            "output_state": self._output_state.to_dict() if self._output_state else None,
            "error": self._error,
            "metadata": self._metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeExecution':
        """从字典创建实例"""
        # 注意：这里需要根据实际情况重建IWorkflowStateInterface对象
        input_state = None
        output_state = None
        if data.get("input_state"):
            # 这里需要根据实际的WorkflowState实现来重建对象
            pass
        if data.get("output_state"):
            # 这里需要根据实际的WorkflowState实现来重建对象
            pass
            
        return cls(
            execution_id=data["execution_id"],
            node_id=data["node_id"],
            node_type=data["node_type"],
            status=data["status"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            input_state=input_state,
            output_state=output_state,
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )


class WorkflowState(IWorkflowStateInterface):
    """工作流状态实体"""
    
    def __init__(
        self,
        workflow_id: str,
        execution_id: str,
        status: str = "running",
        data: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Any]] = None,
        state_id: Optional[str] = None,
        is_complete: bool = False
    ):
        """初始化工作流状态实体"""
        self._workflow_id = workflow_id
        self._execution_id = execution_id
        self._status = status
        self._data = data or {}
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._metadata = metadata or {}
        self._messages = messages or []
        self._state_id = state_id
        self._is_complete = is_complete

    # 实现IWorkflowStateInterface接口的属性
    @property
    def workflow_id(self) -> str:
        """工作流ID"""
        return self._workflow_id

    @property
    def execution_id(self) -> str:
        """执行ID"""
        return self._execution_id

    @property
    def status(self) -> str:
        """状态"""
        return self._status

    @property
    def data(self) -> Dict[str, Any]:
        """状态数据"""
        return self._data

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    @property
    def messages(self) -> List[Any]:
        """消息列表"""
        return self._messages

    # 实现IWorkflowStateInterface接口的方法
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        return self._data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置数据"""
        self._data[key] = value
        self._updated_at = datetime.now()
    
    def update_data(self, updates: Dict[str, Any]) -> None:
        """更新数据"""
        self._data.update(updates)
        self._updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value
        self._updated_at = datetime.now()
    
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        return self._state_id or self._execution_id
    
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        self._state_id = id
    
    def get_created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at
    
    def get_updated_at(self) -> datetime:
        """获取更新时间"""
        return self._updated_at
    
    def is_complete(self) -> bool:
        """检查是否完成"""
        return self._is_complete
    
    def mark_complete(self) -> None:
        """标记为完成"""
        self._is_complete = True
        self._updated_at = datetime.now()
    
    def add_message(self, message: Any) -> None:
        """添加消息"""
        self._messages.append(message)
        self._updated_at = datetime.now()
    
    def get_messages(self) -> List[Any]:
        """获取消息列表"""
        return self._messages.copy()
    
    def get_last_message(self) -> Any:
        """获取最后一条消息"""
        return self._messages[-1] if self._messages else None
    
    def copy(self) -> 'WorkflowState':
        """创建深拷贝"""
        return WorkflowState(
            workflow_id=self._workflow_id,
            execution_id=self._execution_id,
            status=self._status,
            data=self._data.copy(),
            created_at=self._created_at,
            updated_at=self._updated_at,
            metadata=self._metadata.copy(),
            messages=self._messages.copy(),
            state_id=self._state_id,
            is_complete=self._is_complete
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'workflow_id': self._workflow_id,
            'execution_id': self._execution_id,
            'status': self._status,
            'data': self._data,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'metadata': self._metadata,
            'messages': self._messages,
            'state_id': self._state_id,
            'is_complete': self._is_complete
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """从字典创建实例"""
        return cls(
            workflow_id=data['workflow_id'],
            execution_id=data['execution_id'],
            status=data.get('status', 'running'),
            data=data.get('data', {}),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now(),
            metadata=data.get('metadata', {}),
            messages=data.get('messages', []),
            state_id=data.get('state_id'),
            is_complete=data.get('is_complete', False)
        )


class ExecutionResult(IExecutionResult):
    """执行结果实体"""
    
    def __init__(
        self,
        success: bool,
        state: IWorkflowStateInterface,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """初始化执行结果实体"""
        self._success = success
        self._state = state
        self._error = error
        self._metadata = metadata or {}

    # 实现IExecutionResult接口的属性
    @property
    def success(self) -> bool:
        """是否成功"""
        return self._success

    @property
    def state(self) -> IWorkflowStateInterface:
        """工作流状态"""
        return self._state

    @property
    def error(self) -> Optional[str]:
        """错误信息"""
        return self._error

    @property
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        return self._metadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self._success,
            'state': self._state.to_dict() if self._state else None,
            'error': self._error,
            'metadata': self._metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionResult':
        """从字典创建实例"""
        # 注意：这里需要根据实际情况重建IWorkflowStateInterface对象
        state: Optional[IWorkflowStateInterface] = None
        if data.get("state"):
            state = WorkflowState.from_dict(data["state"])
            
        if state is None:
            raise ValueError("state is required for ExecutionResult")
            
        return cls(
            success=data["success"],
            state=state,
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )


class WorkflowMetadata(IWorkflowMetadata):
    """工作流元数据"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """初始化工作流元数据"""
        self._workflow_id = workflow_id
        self._name = name
        self._description = description
        self._version = version
        self._author = author
        self._tags = tags or []
        self._parameters = parameters or {}
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

    # 实现IWorkflowMetadata接口的属性
    @property
    def workflow_id(self) -> str:
        """工作流ID"""
        return self._workflow_id

    @property
    def name(self) -> str:
        """工作流名称"""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """工作流描述"""
        return self._description

    @property
    def version(self) -> str:
        """版本"""
        return self._version

    @property
    def author(self) -> Optional[str]:
        """作者"""
        return self._author

    @property
    def tags(self) -> List[str]:
        """标签"""
        return self._tags

    @property
    def parameters(self) -> Dict[str, Any]:
        """参数"""
        return self._parameters

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """更新时间"""
        return self._updated_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'workflow_id': self._workflow_id,
            'name': self._name,
            'description': self._description,
            'version': self._version,
            'author': self._author,
            'tags': self._tags,
            'parameters': self._parameters,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowMetadata':
        """从字典创建实例"""
        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            author=data.get("author"),
            tags=data.get("tags", []),
            parameters=data.get("parameters", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None
        )