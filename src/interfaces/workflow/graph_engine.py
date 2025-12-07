"""图引擎接口定义

定义了图执行引擎的核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator, Awaitable

from .graph import IGraph, INode, IEdge


class IGraphEngine(ABC):
    """图执行引擎接口
    
    负责图的编译、执行和流式处理。
    """
    
    @abstractmethod
    async def compile(self, config: Dict[str, Any]) -> Any:
        """编译图
        
        Args:
            config: 编译配置
            
        Returns:
            编译后的图
        """
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行图
        
        Args:
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def stream(self, input_data: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """流式执行图
        
        Args:
            input_data: 输入数据
            
        Yields:
            执行事件
        """
        pass
    
    @abstractmethod
    def add_node(self, name: str, func: Any, **kwargs) -> 'IGraphEngine':
        """添加节点
        
        Args:
            name: 节点名称
            func: 节点函数
            **kwargs: 额外参数
            
        Returns:
            自身实例，支持链式调用
        """
        pass
    
    @abstractmethod
    def add_edge(self, start: str, end: str) -> 'IGraphEngine':
        """添加边
        
        Args:
            start: 起始节点
            end: 目标节点
            
        Returns:
            自身实例，支持链式调用
        """
        pass
    
    @abstractmethod
    def add_conditional_edges(
        self,
        source: str,
        path: Any,
        path_map: Optional[Dict] = None
    ) -> 'IGraphEngine':
        """添加条件边
        
        Args:
            source: 源节点
            path: 路径函数
            path_map: 路径映射
            
        Returns:
            自身实例，支持链式调用
        """
        pass
    
    @abstractmethod
    def set_entry_point(self, node_name: str) -> 'IGraphEngine':
        """设置入口点
        
        Args:
            node_name: 入口节点名称
            
        Returns:
            自身实例，支持链式调用
        """
        pass
    
    @abstractmethod
    def set_finish_point(self, node_name: str) -> 'IGraphEngine':
        """设置结束点
        
        Args:
            node_name: 结束节点名称
            
        Returns:
            自身实例，支持链式调用
        """
        pass
    
    @abstractmethod
    def get_node(self, name: str) -> Optional[Any]:
        """获取节点
        
        Args:
            name: 节点名称
            
        Returns:
            节点函数（如果存在）
        """
        pass
    
    @abstractmethod
    def get_nodes(self) -> Dict[str, Any]:
        """获取所有节点
        
        Returns:
            节点字典
        """
        pass
    
    @abstractmethod
    def get_edges(self) -> List[Dict[str, Any]]:
        """获取所有边
        
        Returns:
            边列表
        """
        pass
    
    @abstractmethod
    def get_conditional_edges(self) -> List[Dict[str, Any]]:
        """获取所有条件边
        
        Returns:
            条件边列表
        """
        pass
    
    @abstractmethod
    def get_graph_info(self) -> Dict[str, Any]:
        """获取图信息
        
        Returns:
            图信息字典
        """
        pass
    
    @abstractmethod
    async def destroy(self) -> None:
        """销毁图，释放资源"""
        pass


class IGraphBuilder(ABC):
    """图构建器接口
    
    负责图的构建和配置。
    """
    
    @abstractmethod
    def create_graph(self, config: Dict[str, Any]) -> IGraph:
        """创建图
        
        Args:
            config: 图配置
            
        Returns:
            图实例
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置
        
        Args:
            config: 配置
            
        Returns:
            验证错误列表
        """
        pass
    
    @abstractmethod
    def add_node(self, node: INode) -> 'IGraphBuilder':
        """添加节点
        
        Args:
            node: 节点实例
            
        Returns:
            自身实例，支持链式调用
        """
        pass
    
    @abstractmethod
    def add_edge(self, edge: IEdge) -> 'IGraphBuilder':
        """添加边
        
        Args:
            edge: 边实例
            
        Returns:
            自身实例，支持链式调用
        """
        pass
    
    @abstractmethod
    def build(self) -> IGraph:
        """构建图
        
        Returns:
            构建完成的图
        """
        pass