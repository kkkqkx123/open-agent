"""UI消息系统接口定义

定义UI消息系统的核心抽象，遵循领域层接口设计原则。
UI消息作为包装内部消息、对外呈现的组件，与LLM消息、图消息完全解耦。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

class IUIMessage(ABC):
    """UI消息接口
    
    定义所有UI消息类型的核心契约，专注于UI展示和用户交互。
    """
    
    @property
    @abstractmethod
    def message_id(self) -> str:
        """消息ID"""
        pass
    
    @property
    @abstractmethod
    def message_type(self) -> str:
        """消息类型"""
        pass
    
    @property
    @abstractmethod
    def display_content(self) -> str:
        """显示内容"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """元数据"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IUIMessage":
        """从字典创建实例"""
        pass


class IUIMessageRenderer(ABC):
    """UI消息渲染器接口
    
    定义UI消息渲染的契约。
    """
    
    @abstractmethod
    def render(self, message: IUIMessage) -> str:
        """渲染消息"""
        pass
    
    @abstractmethod
    def can_render(self, message_type: str) -> bool:
        """检查是否可以渲染指定类型的消息"""
        pass


class IUIMessageAdapter(ABC):
    """UI消息适配器接口
    
    定义内部消息与UI消息之间转换的契约。
    """
    
    @abstractmethod
    def to_ui_message(self, internal_message: Any) -> IUIMessage:
        """将内部消息转换为UI消息"""
        pass
    
    @abstractmethod
    def from_ui_message(self, ui_message: IUIMessage) -> Any:
        """将UI消息转换为内部消息"""
        pass
    
    @abstractmethod
    def can_adapt(self, message_type: str) -> bool:
        """检查是否可以适配指定类型的消息"""
        pass


class IUIMessageManager(ABC):
    """UI消息管理器接口
    
    定义UI消息管理的契约。
    """
    
    @abstractmethod
    def register_adapter(self, adapter: IUIMessageAdapter) -> None:
        """注册消息适配器"""
        pass
    
    @abstractmethod
    def register_renderer(self, message_type: str, renderer: IUIMessageRenderer) -> None:
        """注册消息渲染器"""
        pass
    
    @abstractmethod
    def convert_to_ui_message(self, internal_message: Any) -> Optional[IUIMessage]:
        """将内部消息转换为UI消息"""
        pass
    
    @abstractmethod
    def convert_from_ui_message(self, ui_message: IUIMessage, target_type: str) -> Optional[Any]:
        """将UI消息转换为内部消息"""
        pass
    
    @abstractmethod
    def add_message(self, ui_message: IUIMessage) -> None:
        """添加UI消息"""
        pass
    
    @abstractmethod
    def remove_message(self, message_id: str) -> bool:
        """移除UI消息"""
        pass
    
    @abstractmethod
    def get_message(self, message_id: str) -> Optional[IUIMessage]:
        """获取UI消息"""
        pass
    
    @abstractmethod
    def get_all_messages(self) -> List[IUIMessage]:
        """获取所有UI消息"""
        pass
    
    @abstractmethod
    def get_messages_by_type(self, message_type: str) -> List[IUIMessage]:
        """根据类型获取UI消息"""
        pass
    
    @abstractmethod
    def render_message(self, ui_message: IUIMessage) -> str:
        """渲染UI消息"""
        pass
    
    @abstractmethod
    def clear_messages(self) -> None:
        """清空所有消息"""
        pass


class IUIMessageController(ABC):
    """UI消息控制器接口
    
    定义UI消息控制的契约，负责协调UI消息与具体UI框架的交互。
    """
    
    @abstractmethod
    def process_internal_message(self, internal_message: Any) -> None:
        """处理内部消息"""
        pass
    
    @abstractmethod
    def process_user_input(self, input_text: str) -> None:
        """处理用户输入"""
        pass
    
    @abstractmethod
    def clear_all_messages(self) -> None:
        """清空所有消息"""
        pass
    
    @abstractmethod
    def get_message_history(self) -> List[Dict[str, Any]]:
        """获取消息历史"""
        pass
    
    @abstractmethod
    def display_ui_message(self, ui_message: IUIMessage) -> None:
        """显示UI消息"""
        pass