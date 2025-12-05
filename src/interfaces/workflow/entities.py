"""工作流实体接口定义

定义工作流管理中使用的实体接口，遵循分层架构原则。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..common_domain import ISerializable


class IWorkflowState(ISerializable, ABC):
    """工作流状态接口
    
    定义工作流状态的基本契约，用于跨层传递工作流状态数据。
    """
    
    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass
    
    @property
    @abstractmethod
    def execution_id(self) -> str:
        """执行ID"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """状态"""
        pass
    
    @property
    @abstractmethod
    def data(self) -> Dict[str, Any]:
        """状态数据"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """更新时间"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass
    
    @property
    @abstractmethod
    def messages(self) -> List[Any]:
        """消息列表"""
        pass
    
    @abstractmethod
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        pass
    
    @abstractmethod
    def set_data(self, key: str, value: Any) -> None:
        """设置数据"""
        pass
    
    @abstractmethod
    def update_data(self, updates: Dict[str, Any]) -> None:
        """更新数据"""
        pass
    
    @abstractmethod
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        pass
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        pass
    
    @abstractmethod
    def get_id(self) -> Optional[str]:
        """获取状态ID"""
        pass
    
    @abstractmethod
    def set_id(self, id: str) -> None:
        """设置状态ID"""
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """检查是否完成"""
        pass
    
    @abstractmethod
    def mark_complete(self) -> None:
        """标记为完成"""
        pass
    
    @abstractmethod
    def add_message(self, message: Any) -> None:
        """添加消息"""
        pass
    
    @abstractmethod
    def get_messages(self) -> List[Any]:
        """获取消息列表"""
        pass
    
    @abstractmethod
    def get_last_message(self) -> Any:
        """获取最后一条消息"""
        pass
    
    @abstractmethod
    def copy(self) -> 'IWorkflowState':
        """创建深拷贝"""
        pass


class IExecutionResult(ISerializable, ABC):
    """执行结果接口
    
    定义执行结果的基本契约。
    """
    
    @property
    @abstractmethod
    def success(self) -> bool:
        """是否成功"""
        pass
    
    @property
    @abstractmethod
    def state(self) -> IWorkflowState:
        """工作流状态"""
        pass
    
    @property
    @abstractmethod
    def error(self) -> Optional[str]:
        """错误信息"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass


class IWorkflow(ISerializable, ABC):
    """工作流接口
    
    定义工作流的基本契约。
    """
    
    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工作流名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """工作流描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """版本"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """更新时间"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass


class IWorkflowExecution(ISerializable, ABC):
    """工作流执行接口
    
    定义工作流执行的基本契约。
    """
    
    @property
    @abstractmethod
    def execution_id(self) -> str:
        """执行ID"""
        pass
    
    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """执行状态"""
        pass
    
    @property
    @abstractmethod
    def started_at(self) -> datetime:
        """开始时间"""
        pass
    
    @property
    @abstractmethod
    def completed_at(self) -> Optional[datetime]:
        """完成时间"""
        pass
    
    @property
    @abstractmethod
    def error(self) -> Optional[str]:
        """错误信息"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass


class INodeExecution(ISerializable, ABC):
    """节点执行接口
    
    定义节点执行的基本契约。
    """
    
    @property
    @abstractmethod
    def execution_id(self) -> str:
        """执行ID"""
        pass
    
    @property
    @abstractmethod
    def node_id(self) -> str:
        """节点ID"""
        pass
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """节点类型"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """执行状态"""
        pass
    
    @property
    @abstractmethod
    def started_at(self) -> datetime:
        """开始时间"""
        pass
    
    @property
    @abstractmethod
    def completed_at(self) -> Optional[datetime]:
        """完成时间"""
        pass
    
    @property
    @abstractmethod
    def input_state(self) -> Optional[IWorkflowState]:
        """输入状态"""
        pass
    
    @property
    @abstractmethod
    def output_state(self) -> Optional[IWorkflowState]:
        """输出状态"""
        pass
    
    @property
    @abstractmethod
    def error(self) -> Optional[str]:
        """错误信息"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass


class IWorkflowMetadata(ISerializable, ABC):
    """工作流元数据接口
    
    定义工作流元数据的基本契约。
    """
    
    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工作流名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """工作流描述"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """版本"""
        pass
    
    @property
    @abstractmethod
    def author(self) -> Optional[str]:
        """作者"""
        pass
    
    @property
    @abstractmethod
    def tags(self) -> List[str]:
        """标签"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """参数"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """创建时间"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """更新时间"""
        pass