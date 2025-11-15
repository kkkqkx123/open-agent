"""Thread领域服务实现

提供Thread核心业务逻辑的实现，遵循DDD领域服务模式。
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from .interfaces import IThreadDomainService
from .models import Thread
from ...infrastructure.graph.config import GraphConfig

logger = logging.getLogger(__name__)


class ThreadDomainService(IThreadDomainService):
    """Thread领域服务实现
    
    负责Thread的核心业务逻辑，包括创建、验证等。
    """
    
    def __init__(self):
        """初始化Thread领域服务"""
        logger.info("ThreadDomainService初始化完成")
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> Thread:
        """创建新的Thread实体
        
        Args:
            graph_id: 关联的图ID
            metadata: Thread元数据
            
        Returns:
            创建的Thread实体
        """
        try:
            # 生成Thread ID
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
            
            # 创建Thread实体
            thread = Thread(
                thread_id=thread_id,
                graph_id=graph_id,
                status="active",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=metadata or {}
            )
            
            logger.info(f"创建Thread实体成功: {thread_id}, graph_id: {graph_id}")
            return thread
            
        except Exception as e:
            logger.error(f"创建Thread实体失败: {e}")
            raise RuntimeError(f"创建Thread实体失败: {e}")
    
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> Thread:
        """从配置文件创建Thread实体
        
        Args:
            config_path: 配置文件路径
            metadata: Thread元数据
            
        Returns:
            创建的Thread实体
        """
        try:
            # 加载图配置
            graph_config = await self._load_graph_config(config_path)
            graph_id = graph_config.name
            
            # 创建Thread实体
            thread_metadata = metadata or {}
            thread_metadata.update({
                "config_path": config_path,
                "config_version": graph_config.version or "latest"
            })
            
            thread = await self.create_thread(graph_id, thread_metadata)
            
            logger.info(f"从配置创建Thread实体成功: {thread.thread_id}, config_path: {config_path}")
            return thread
            
        except Exception as e:
            logger.error(f"从配置创建Thread实体失败: {e}")
            raise RuntimeError(f"从配置创建Thread实体失败: {e}")
    
    async def fork_thread(
        self, 
        source_thread: Thread, 
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Thread:
        """从指定checkpoint创建thread分支
        
        Args:
            source_thread: 源Thread实体
            checkpoint_id: 检查点ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            新的Thread实体
        """
        try:
            # 生成新Thread ID
            new_thread_id = f"thread_{uuid.uuid4().hex[:8]}"
            
            # 创建分支元数据
            branch_metadata = {
                "branch_name": branch_name,
                "source_thread_id": source_thread.thread_id,
                "source_checkpoint_id": checkpoint_id,
                "branch_type": "fork",
                **(metadata or {})
            }
            
            # 创建新Thread实体
            new_thread = Thread(
                thread_id=new_thread_id,
                graph_id=source_thread.graph_id,
                status="active",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=branch_metadata
            )
            
            logger.info(f"创建Thread分支成功: {new_thread_id}, 源Thread: {source_thread.thread_id}")
            return new_thread
            
        except Exception as e:
            logger.error(f"创建Thread分支失败: {e}")
            raise RuntimeError(f"创建Thread分支失败: {e}")
    
    async def validate_thread_state(self, thread: Thread, state: Dict[str, Any]) -> bool:
        """验证Thread状态的有效性
        
        Args:
            thread: Thread实体
            state: 状态数据
            
        Returns:
            状态是否有效
        """
        try:
            # 基本验证
            if not isinstance(state, dict):
                logger.warning(f"Thread状态无效: {thread.thread_id}, 状态不是字典类型")
                return False
            
            # 检查Thread是否处于可更新状态
            if thread.status == "error":
                logger.warning(f"Thread处于错误状态，不允许更新: {thread.thread_id}")
                return False
            
            if thread.status == "completed":
                logger.warning(f"Thread已完成，不允许更新: {thread.thread_id}")
                return False
            
            # 可以添加更多业务规则验证
            # 例如：状态字段格式验证、必需字段检查等
            
            logger.debug(f"Thread状态验证通过: {thread.thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"验证Thread状态失败: {thread.thread_id}, error: {e}")
            return False
    
    async def _load_graph_config(self, config_path: str) -> GraphConfig:
        """加载图配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            图配置
        """
        # 这里应该使用配置加载器，暂时简化实现
        # TODO: 集成CentralizedConfigManager
        try:
            # 简化实现，实际应该从配置文件加载
            return GraphConfig(
                name=f"graph_from_{config_path}",
                version="1.0",
                description=f"Graph loaded from {config_path}"
            )
        except Exception as e:
            logger.error(f"加载图配置失败: {config_path}, error: {e}")
            raise RuntimeError(f"加载图配置失败: {e}")