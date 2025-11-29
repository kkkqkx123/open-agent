"""LangGraph适配器 - 统一LangGraph交互接口

提供符合LangGraph最佳实践的统一交互接口，负责：
1. LangGraph图的创建和管理
2. 工作流执行和流式处理
3. Checkpoint状态管理
4. 错误处理和恢复
"""

from typing import Dict, Any, Optional, List, AsyncGenerator, Union, TYPE_CHECKING, cast
from datetime import datetime
import logging
import asyncio
from abc import ABC, abstractmethod
import inspect

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.pregel import Pregel
from langchain_core.messages import BaseMessage

from src.interfaces.state.workflow import IWorkflowState as WorkflowState
from src.interfaces.workflow.core import IWorkflow
from src.core.workflow.graph.registry import get_global_registry
from src.core.workflow.config.config import GraphConfig
from src.core.workflow.graph.builder.graph_builder import GraphBuilder
from src.interfaces.state import IStateLifecycleManager

if TYPE_CHECKING:
    from src.services.workflow.graph_cache import GraphCache

logger = logging.getLogger(__name__)


class ILangGraphAdapter(ABC):
    """LangGraph适配器接口"""
    
    @abstractmethod
    async def create_graph(self, config: GraphConfig) -> Pregel:
        """创建LangGraph图"""
        pass
    
    @abstractmethod
    async def execute_graph(
        self,
        graph: Pregel,
        thread_id: str,
        config: Optional[RunnableConfig] = None
    ) -> WorkflowState:
        """执行LangGraph图"""
        pass
    
    @abstractmethod
    async def stream_graph(  # type: ignore[override]
        self,
        graph: Pregel,
        thread_id: str,
        config: Optional[RunnableConfig] = None
    ) -> AsyncGenerator[WorkflowState, None]:
        """流式执行LangGraph图"""
        pass
    
    @abstractmethod
    async def save_checkpoint(
        self, 
        thread_id: str, 
        state: WorkflowState, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存checkpoint"""
        pass
    
    @abstractmethod
    async def load_checkpoint(
        self, 
        thread_id: str, 
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """加载checkpoint"""
        pass
    
    @abstractmethod
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出所有checkpoint"""
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        pass


class LangGraphAdapter(ILangGraphAdapter):
    """LangGraph适配器实现"""
    
    def __init__(
        self,
        checkpoint_saver: Optional[BaseCheckpointSaver] = None,
        graph_builder: Optional[GraphBuilder] = None,
        state_manager: Optional[IStateLifecycleManager] = None,
        use_memory_checkpoint: bool = False,
        graph_cache: Optional["GraphCache"] = None,  # 使用外部缓存
        node_registry=None,  # 兼容性参数
        function_registry=None  # 兼容性参数
    ):
        """初始化LangGraph适配器
        
        Args:
            checkpoint_saver: Checkpoint保存器
            graph_builder: 图构建器
            state_manager: 状态管理器
            use_memory_checkpoint: 是否使用内存checkpoint
            graph_cache: 外部图缓存实例
            node_registry: 节点注册表（兼容性参数）
            function_registry: 函数注册表（兼容性参数）
        """
        self.checkpoint_saver = checkpoint_saver or self._create_default_checkpoint_saver(use_memory_checkpoint)
        self.graph_builder = graph_builder or self._create_default_graph_builder()
        self.state_manager = state_manager
        
        # 保存兼容性参数
        self.node_registry = node_registry
        self.function_registry = function_registry
        
        # 使用外部缓存或内部简单缓存
        if graph_cache:
            self._graph_cache = graph_cache  # type: ignore
            self._external_cache = True
        else:
            self._graph_cache: Dict[str, Pregel] = {}
            self._external_cache = False
        
        logger.info("LangGraphAdapter初始化完成")
    
    def _create_default_checkpoint_saver(self, use_memory: bool) -> BaseCheckpointSaver:
        """创建默认checkpoint保存器"""
        if use_memory:
            logger.info("使用内存checkpoint保存器")
            return InMemorySaver()
        else:
            logger.info("使用SQLite checkpoint保存器")
            import sqlite3
        conn = sqlite3.connect(":memory:")
        return SqliteSaver(conn)
    
    def _create_default_graph_builder(self) -> GraphBuilder:
        """创建默认图构建器"""
        from src.core.workflow.graph.builder.base import GraphBuilder
        node_registry = get_global_registry()
        return cast(GraphBuilder, GraphBuilder())
    
    async def create_graph(self, config: GraphConfig) -> Pregel:
        """创建LangGraph图
        
        Args:
            config: 图配置
            
        Returns:
            StateGraph: 构建好的LangGraph图
        """
        try:
            # 检查缓存
            cached_graph = self._get_cached_graph(config)
            if cached_graph:
                logger.debug(f"从缓存获取图: {config.name}")
                return cached_graph
            
            # 构建图
            logger.info(f"开始构建LangGraph图: {config.name}")
            graph = await self.graph_builder.build_graph(config)
            
            # 编译图（添加checkpoint支持）- 检查是否已经编译
            if hasattr(graph, 'compile') and not hasattr(graph, 'invoke'):
                # 未编译的图，需要编译
                compiled_graph = graph.compile(checkpointer=self.checkpoint_saver)
            else:
                # 已经编译的图，直接使用
                compiled_graph = graph
            
            # 缓存图
            self._cache_graph(config, compiled_graph)
            
            logger.info(f"LangGraph图构建完成: {config.name}")
            return compiled_graph
            
        except Exception as e:
            logger.error(f"创建LangGraph图失败: {config.name}, error: {e}")
            raise
    
    def create_graph_sync(self, config: GraphConfig) -> Pregel:
        """同步创建LangGraph图
        
        Args:
            config: 图配置
            
        Returns:
            StateGraph: 构建好的LangGraph图
        """
        try:
            # 检查缓存
            cached_graph = self._get_cached_graph(config)
            if cached_graph:
                logger.debug(f"从缓存获取图: {config.name}")
                return cached_graph
            
            # 构建图（同步方式）
            logger.info(f"开始构建LangGraph图: {config.name}")
            graph = self.graph_builder.build_graph(config)
            
            # 编译图（添加checkpoint支持）- 检查是否已经编译
            if hasattr(graph, 'compile') and not hasattr(graph, 'invoke'):
                # 未编译的图，需要编译
                compiled_graph = graph.compile(checkpointer=self.checkpoint_saver)
            else:
                # 已经编译的图，直接使用
                compiled_graph = graph
            
            # 缓存图
            self._cache_graph(config, compiled_graph)
            
            logger.info(f"LangGraph图构建完成: {config.name}")
            return compiled_graph
            
        except Exception as e:
            logger.error(f"创建LangGraph图失败: {config.name}, error: {e}")
            raise
    
    def _get_cached_graph(self, config: GraphConfig) -> Optional[Pregel]:
        """获取缓存的图"""
        if self._external_cache:
            # 使用外部缓存（GraphCache）
            from src.services.workflow.graph_cache import calculate_config_hash
            config_dict = config.to_dict() if hasattr(config, 'to_dict') else config.__dict__
            config_hash = calculate_config_hash(config_dict)
            return self._graph_cache.get_graph(config_hash)  # type: ignore
        else:
            # 使用内部简单缓存
            cache_key = self._generate_graph_cache_key(config)
            return self._graph_cache.get(cache_key)
    
    def _cache_graph(self, config: GraphConfig, graph: Pregel) -> None:
        """缓存图"""
        if self._external_cache:
            # 使用外部缓存（GraphCache）
            from src.services.workflow.graph_cache import calculate_config_hash
            config_dict = config.to_dict() if hasattr(config, 'to_dict') else config.__dict__
            config_hash = calculate_config_hash(config_dict)
            self._graph_cache.cache_graph(config_hash, graph, config_dict)  # type: ignore
        else:
            # 使用内部简单缓存
            cache_key = self._generate_graph_cache_key(config)
            self._graph_cache[cache_key] = graph
    
    async def execute_graph(
    self,
    graph: Pregel,
    thread_id: str,
    config: Optional[RunnableConfig] = None
    ) -> WorkflowState:
        """执行LangGraph图
        
        Args:
            graph: LangGraph图
            thread_id: 线程ID
            config: 运行配置
            
        Returns:
            WorkflowState: 执行结果状态
        """
        try:
            # 准备运行配置
            run_config = self._prepare_run_config(thread_id, config)
            
            logger.info(f"开始执行LangGraph图: thread_id={thread_id}")
            
            # 执行图
            result = await graph.ainvoke(run_config) if hasattr(graph, 'ainvoke') else graph.invoke(run_config)
            
            logger.info(f"LangGraph图执行完成: thread_id={thread_id}")
            return cast(WorkflowState, result)
            
        except Exception as e:
            logger.error(f"执行LangGraph图失败: thread_id={thread_id}, error: {e}")
            raise
    
    async def stream_graph(  # type: ignore[override]
    self,
    graph: Pregel,
    thread_id: str,
    config: Optional[RunnableConfig] = None
    ) -> AsyncGenerator[WorkflowState, None]:
        """流式执行LangGraph图
        
        Args:
            graph: LangGraph图
            thread_id: 线程ID
            config: 运行配置
            
        Yields:
            WorkflowState: 中间状态
        """
        try:
            # 准备运行配置
            run_config = self._prepare_run_config(thread_id, config)
            
            logger.info(f"开始流式执行LangGraph图: thread_id={thread_id}")
            
            # 流式执行图
            async for state in graph.astream(run_config) if hasattr(graph, 'astream') else graph.stream(run_config):  # type: ignore
                yield state
            
            logger.info(f"LangGraph图流式执行完成: thread_id={thread_id}")
            
        except Exception as e:
            logger.error(f"流式执行LangGraph图失败: thread_id={thread_id}, error: {e}")
            raise
    
    async def save_checkpoint(
        self, 
        thread_id: str, 
        state: WorkflowState, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存checkpoint
        
        Args:
            thread_id: 线程ID
            state: 工作流状态
            metadata: 元数据
            
        Returns:
            str: checkpoint ID
        """
        try:
            import time
            import uuid
            import inspect
            
            # 生成checkpoint ID和时间戳
            checkpoint_id = str(uuid.uuid4())
            timestamp = time.time()
            
            # 创建符合LangGraph标准的checkpoint结构
            checkpoint = {
                "v": 1,  # checkpoint版本
                "ts": timestamp,  # 时间戳
                "id": checkpoint_id,  # checkpoint ID
                "channel_values": {
                    "state": state  # 直接存储状态对象
                },
                "channel_versions": {
                    "state": timestamp  # 使用相同的时间戳作为版本
                },
                "versions_seen": {
                    "state": timestamp
                }
            }
            
            # 创建配置，包含必要的checkpoint命名空间
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": ""  # 添加必要的checkpoint命名空间
                }
            }
            
            # 保存checkpoint - 处理同步和异步put方法
            if hasattr(self.checkpoint_saver, 'put'):
                # 检查put方法是否是异步的
                put_method = getattr(self.checkpoint_saver, 'put')
                if inspect.iscoroutinefunction(put_method):
                    # 异步方法
                    success = await put_method(
                        config=config,
                        checkpoint=checkpoint,
                        metadata=metadata or {},
                        new_versions={}
                    )
                else:
                    # 同步方法
                    success = put_method(
                        config=config,
                        checkpoint=checkpoint,
                        metadata=metadata or {},
                        new_versions={}
                    )
            else:
                logger.warning("Checkpoint保存器不支持put操作")
                success = False
            
            if success:
                logger.info(f"成功保存checkpoint: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
                return checkpoint_id
            else:
                raise RuntimeError("保存checkpoint失败")
                
        except Exception as e:
            logger.error(f"保存checkpoint失败: thread_id={thread_id}, error: {e}")
            raise
    
    async def load_checkpoint(
        self, 
        thread_id: str, 
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """加载checkpoint
        
        Args:
            thread_id: 线程ID
            checkpoint_id: checkpoint ID，None表示最新
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据
        """
        try:
            # 准备查询配置
            config = {"configurable": {"thread_id": thread_id}}
            
            # 获取checkpoint - 处理同步和异步get方法
            if hasattr(self.checkpoint_saver, 'get'):
                get_method = getattr(self.checkpoint_saver, 'get')
                if inspect.iscoroutinefunction(get_method):
                    # 异步方法
                    checkpoint = await get_method(config)
                else:
                    # 同步方法
                    checkpoint = get_method(config)
            else:
                logger.warning("Checkpoint保存器不支持get操作，返回None")
                checkpoint = None
            
            if checkpoint:
                logger.info(f"Checkpoint加载成功: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
            else:
                logger.warning(f"Checkpoint不存在: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
            
            return checkpoint
            
        except Exception as e:
            logger.error(f"加载checkpoint失败: thread_id={thread_id}, error: {e}")
            return None
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出所有checkpoint
        
        Args:
            thread_id: 线程ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表
        """
        try:
            # 准备查询配置
            config = {"configurable": {"thread_id": thread_id}}
            
            # 获取checkpoint列表 - 处理同步和异步list方法
            if hasattr(self.checkpoint_saver, 'list'):
                list_method = getattr(self.checkpoint_saver, 'list')
                if inspect.iscoroutinefunction(list_method):
                    # 异步方法
                    checkpoints = await list_method(config)
                else:
                    # 同步方法
                    checkpoints = list_method(config)
            else:
                logger.warning("Checkpoint保存器不支持列出操作，返回空列表")
                checkpoints = []
            
            checkpoint_list = list(checkpoints) if checkpoints else []
            logger.info(f"获取checkpoint列表成功: thread_id={thread_id}, count={len(checkpoint_list)}")
            return checkpoint_list
            
        except Exception as e:
            logger.error(f"获取checkpoint列表失败: thread_id={thread_id}, error: {e}")
            return []
    
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            thread_id: 线程ID
            checkpoint_id: checkpoint ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 准备删除配置
            config = {"configurable": {"thread_id": thread_id}}
            
            # 删除checkpoint - 处理同步和异步delete方法
            if hasattr(self.checkpoint_saver, 'delete'):
                delete_method = getattr(self.checkpoint_saver, 'delete')
                if inspect.iscoroutinefunction(delete_method):
                    # 异步方法
                    success = await delete_method(config, checkpoint_id)
                else:
                    # 同步方法
                    success = delete_method(config, checkpoint_id)
            else:
                logger.warning("Checkpoint保存器不支持删除操作，返回False")
                success = False
            
            if success:
                logger.info(f"Checkpoint删除成功: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
            else:
                logger.warning(f"Checkpoint删除失败: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除checkpoint失败: thread_id={thread_id}, checkpoint_id={checkpoint_id}, error: {e}")
            return False
    
    def _prepare_run_config(self, thread_id: str, config: Optional[RunnableConfig] = None) -> RunnableConfig:
        """准备运行配置
        
        Args:
            thread_id: 线程ID
            config: 用户配置
            
        Returns:
            RunnableConfig: 完整的运行配置
        """
        run_config = config or {}
        
        # 确保configurable字段存在
        if "configurable" not in run_config:
            run_config["configurable"] = {}
        
        # 设置thread_id
        run_config["configurable"]["thread_id"] = thread_id
        
        return run_config
    
    def _generate_graph_cache_key(self, config: GraphConfig) -> str:
        """生成图缓存键
        
        Args:
            config: 图配置
            
        Returns:
            str: 缓存键
        """
        # 使用配置名称和版本生成缓存键
        key_parts = [config.name, str(config.version or "latest")]
        return "_".join(key_parts)
    
    async def clear_graph_cache(self) -> None:
        """清空图缓存"""
        if self._external_cache:
            self._graph_cache.clear()
        else:
            self._graph_cache.clear()
        logger.info("图缓存已清空")
    
    def clear_graph_cache_sync(self) -> None:
        """同步清空图缓存"""
        if self._external_cache:
            self._graph_cache.clear()
        else:
            self._graph_cache.clear()
        logger.info("图缓存已清空")
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        if self._external_cache:
            return self._graph_cache.get_cache_stats()  # type: ignore
        else:
            return {
                "graph_cache_size": len(self._graph_cache),
                "cached_graphs": list(self._graph_cache.keys()),
                "cache_type": "internal"
            }
    
    def get_cache_info_sync(self) -> Dict[str, Any]:
        """同步获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        if self._external_cache:
            return self._graph_cache.get_cache_stats()  # type: ignore
        else:
            return {
                "graph_cache_size": len(self._graph_cache),
                "cached_graphs": list(self._graph_cache.keys()),
                "cache_type": "internal"
            }
    
    def get_graph_builder(self):
        """获取底层图构建器（用于高级配置）"""
        return self.graph_builder
    
    def create_workflow_sync(self, config: Dict[str, Any]) -> IWorkflow:
        """同步创建完整的工作流实例（Services层专用接口）"""
        try:
            # 创建GraphConfig
            from src.core.workflow.config.config import GraphConfig
            graph_config = GraphConfig.from_dict(config)
            
            # 创建图
            compiled_graph = self.create_graph_sync(graph_config)
            
            # 创建工作流实例
            from src.core.workflow.workflow_instance import Workflow
            workflow_id = config.get("workflow_id") or config.get("id")
            if not workflow_id:
                raise ValueError("workflow_id 是必需的")
            
            name = config.get("name", workflow_id)
            workflow = Workflow(workflow_id, name)
            
            # 设置图 - 使用类型转换避免类型检查问题
            workflow.set_graph(compiled_graph)  # type: ignore
            
            # 设置其他属性
            if "entry_point" in config:
                workflow.set_entry_point(config["entry_point"])
            if "metadata" in config:
                workflow.metadata = config["metadata"]
                
            return workflow
            
        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            raise
    
    def validate_and_build_sync(self, config: Dict[str, Any]) -> IWorkflow:
        """同步验证配置并构建工作流（集成验证逻辑）"""
        # 延迟导入验证器
        from src.core.workflow.graph.builder.validator import WorkflowConfigValidator
        validator = WorkflowConfigValidator()
        
        # 验证配置
        from src.core.workflow.config.config import GraphConfig
        graph_config = GraphConfig.from_dict(config)
        result = validator.validate_config(graph_config)
        
        if result.has_errors():
            raise ValueError(f"配置验证失败: {result.errors}")
        
        # 构建工作流
        return self.create_workflow_sync(config)