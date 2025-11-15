"""工作流接口定义

定义工作流相关的接口，实现依赖倒置。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncGenerator, Generator, Type

from src.infrastructure.graph.config import GraphConfig, WorkflowConfig
from src.infrastructure.graph.states import WorkflowState


class IWorkflowManager(ABC):
    """工作流管理器接口"""

    @abstractmethod
    def load_workflow(self, config_path: str) -> str:
        """加载工作流配置

        Args:
            config_path: 配置文件路径

        Returns:
            str: 工作流ID
        """
        pass

    @abstractmethod
    def create_workflow(self, workflow_id: str) -> Any:
        """创建工作流实例

        Args:
            workflow_id: 工作流ID

        Returns:
            Any: 工作流实例
        """
        pass

    @abstractmethod
    def run_workflow(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> WorkflowState:
        """运行工作流

        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            event_collector: 可选的事件收集器
            **kwargs: 其他参数

        Returns:
            WorkflowState: 最终状态
        """
        pass

    @abstractmethod
    async def run_workflow_async(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> WorkflowState:
        """异步运行工作流

        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            event_collector: 可选的事件收集器
            **kwargs: 其他参数

        Returns:
            WorkflowState: 最终状态
        """
        pass

    @abstractmethod
    def stream_workflow(
        self,
        workflow_id: str,
        initial_state: Optional[WorkflowState] = None,
        event_collector: Optional[Any] = None,
        **kwargs: Any
    ) -> Generator[WorkflowState, None, None]:
        """流式运行工作流

        Args:
            workflow_id: 工作流ID
            initial_state: 初始状态
            event_collector: 可选的事件收集器
            **kwargs: 其他参数

        Yields:
            WorkflowState: 中间状态
        """
        pass

    @abstractmethod
    def list_workflows(self) -> List[str]:
        """列出所有已加载的工作流

        Returns:
            List[str]: 工作流ID列表
        """
        pass

    @abstractmethod
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置

        Args:
            workflow_id: 工作流ID

        Returns:
            Optional[WorkflowConfig]: 工作流配置
        """
        pass

    @abstractmethod
    def unload_workflow(self, workflow_id: str) -> bool:
        """卸载工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            bool: 是否成功卸载
        """
        pass

    @abstractmethod
    def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流可视化数据

        Args:
            workflow_id: 工作流ID

        Returns:
            Dict[str, Any]: 可视化数据
        """
        pass

    @abstractmethod
    def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流配置摘要（名称、版本、校验指纹等）

        Args:
            workflow_id: 工作流ID

        Returns:
            Dict[str, Any]: 工作流摘要信息
        """
        pass


class IWorkflowBuilder(ABC):
    """工作流构建器接口"""

    @abstractmethod
    def build_graph(self, config: GraphConfig) -> Any:
        """构建图

        Args:
            config: 工作流配置

        Returns:
            Any: 图实例
        """
        pass

    @abstractmethod
    def load_workflow_config(self, config_path: str) -> GraphConfig:
        """加载工作流配置

        Args:
            config_path: 配置文件路径

        Returns:
            GraphConfig: 工作流配置
        """
        pass

    @abstractmethod
    def validate_config(self, config: GraphConfig) -> List[str]:
        """验证配置

        Args:
            config: 工作流配置

        Returns:
            List[str]: 验证错误列表
        """
        pass


class IEventCollector(ABC):
    """事件收集器接口"""

    @abstractmethod
    def collect_workflow_start(self, workflow_name: str, config: Dict[str, Any]) -> None:
        """收集工作流开始事件

        Args:
            workflow_name: 工作流名称
            config: 工作流配置
        """
        pass

    @abstractmethod
    def collect_workflow_end(self, workflow_name: str, result: Dict[str, Any]) -> None:
        """收集工作流结束事件

        Args:
            workflow_name: 工作流名称
            result: 执行结果
        """
        pass

    @abstractmethod
    def collect_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """收集错误事件

        Args:
            error: 错误信息
            context: 上下文信息
        """
        pass


class IWorkflowExecutor(ABC):
    """工作流执行器接口"""

    @abstractmethod
    def execute(
        self,
        workflow: Any,
        initial_state: WorkflowState,
        **kwargs: Any
    ) -> WorkflowState:
        """执行工作流

        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            **kwargs: 其他参数

        Returns:
            WorkflowState: 最终状态
        """
        pass

    @abstractmethod
    async def execute_async(
        self,
        workflow: Any,
        initial_state: WorkflowState,
        **kwargs: Any
    ) -> WorkflowState:
        """异步执行工作流

        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            **kwargs: 其他参数

        Returns:
            WorkflowState: 最终状态
        """
        pass

    @abstractmethod
    def stream_execute(
        self,
        workflow: Any,
        initial_state: WorkflowState,
        **kwargs: Any
    ) -> Generator[WorkflowState, None, None]:
        """流式执行工作流

        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            **kwargs: 其他参数

        Yields:
            WorkflowState: 中间状态
        """
        pass


class IWorkflowTemplate(ABC):
    """工作流模板接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """模板名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """模板描述"""
        pass

    @abstractmethod
    def create_template(self, config: Dict[str, Any]) -> GraphConfig:
        """创建模板实例

        Args:
            config: 配置参数

        Returns:
            GraphConfig: 工作流配置
        """
        pass

    @abstractmethod
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数定义

        Returns:
            List[Dict[str, Any]]: 参数定义列表
        """
        pass

    @abstractmethod
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数

        Args:
            config: 参数配置

        Returns:
            List[str]: 验证错误列表
        """
        pass


class IWorkflowTemplateRegistry(ABC):
    """工作流模板注册表接口"""

    @abstractmethod
    def register_template(self, template: IWorkflowTemplate) -> None:
        """注册模板

        Args:
            template: 模板实例
        """
        pass

    @abstractmethod
    def get_template(self, name: str) -> Optional[IWorkflowTemplate]:
        """获取模板

        Args:
            name: 模板名称

        Returns:
            Optional[IWorkflowTemplate]: 模板实例，如果不存在则返回None
        """
        pass


class IWorkflowFactory(ABC):
    """工作流工厂接口"""

    @abstractmethod
    def create_workflow(self, config: Union[GraphConfig, WorkflowConfig]) -> Any:
        """创建工作流实例

        Args:
            config: 工作流配置

        Returns:
            工作流实例
        """
        pass

    @abstractmethod
    def register_workflow_type(self, workflow_type: str, workflow_class: Type) -> None:
        """注册工作流类型
        
        Args:
            workflow_type: 工作流类型名称
            workflow_class: 工作流类
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> list:
        """获取支持的工作流类型列表
        
        Returns:
            list: 工作流类型列表
        """
        pass

    @abstractmethod
    def load_workflow_config(self, config_path: str) -> Union[GraphConfig, WorkflowConfig]:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            GraphConfig: 工作流配置
        """
        pass