"""基于SQLite的checkpoint存储实现

使用LangGraph的SqliteSaver，适合生产环境使用。
"""

import logging
import os
from typing import Dict, Any, Optional, List

from langgraph.checkpoint.sqlite import SqliteSaver

from ...domain.checkpoint.interfaces import ICheckpointSerializer
from ..config.service.checkpoint_service import CheckpointConfigService
from .types import CheckpointError, CheckpointStorageError
from .checkpoint_base_storage import CheckpointBaseStorage
from .langgraph_adapter import LangGraphAdapter

logger = logging.getLogger(__name__)


class SQLiteCheckpointStore(CheckpointBaseStorage):
    """基于SQLite的checkpoint存储实现
    
    使用LangGraph的SqliteSaver，支持持久化存储。
    """
    
    def __init__(self, sqlite_path: Optional[str] = None, serializer: Optional[ICheckpointSerializer] = None,
                 config_service: Optional[CheckpointConfigService] = None,
                 max_checkpoints_per_thread: int = 1000,
                 enable_performance_monitoring: bool = True):
        """初始化SQLite存储
        
        Args:
            sqlite_path: SQLite数据库路径（可选，如果未提供则从配置获取）
            serializer: 状态序列化器
            config_service: 配置服务实例
            max_checkpoints_per_thread: 每个线程最大checkpoint数量
            enable_performance_monitoring: 是否启用性能监控
        """
        super().__init__(
            serializer=serializer,
            max_checkpoints_per_thread=max_checkpoints_per_thread,
            enable_performance_monitoring=enable_performance_monitoring
        )
        
        self.config_service = config_service or CheckpointConfigService()
        
        # 获取数据库路径
        if sqlite_path:
            self.sqlite_path = sqlite_path
        else:
            self.sqlite_path = self.config_service.get_db_path()
        
        # 确保目录存在
        db_dir = os.path.dirname(self.sqlite_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # 保存连接字符串而不是checkpointer实例，因为SqliteSaver.from_conn_string返回的是上下文管理器
        self._conn_string = self.sqlite_path
        
        logger.info(f"SQLite checkpoint存储初始化: {self.sqlite_path}")
        
        # 使用LangGraph适配器
        self.langgraph_adapter = LangGraphAdapter(serializer=serializer)
    
    def _get_checkpointer(self) -> Any:
        """获取checkpointer实例（在with语句中使用）"""
        return SqliteSaver.from_conn_string(self._conn_string)
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        try:
            # 检查checkpoint数量限制
            thread_id = checkpoint_data['thread_id']
            current_count = await self.get_checkpoint_count(thread_id)
            if current_count >= self.max_checkpoints_per_thread:
                logger.warning(f"线程 {thread_id} 的checkpoint数量已达到最大限制 {self.max_checkpoints_per_thread}")
                # 清理旧的checkpoint
                await self.cleanup_old_checkpoints(thread_id, self.max_checkpoints_per_thread - 1)
            
            workflow_id = checkpoint_data['workflow_id']
            state = checkpoint_data['state_data']
            metadata = checkpoint_data.get('metadata', {})
            
            # 添加必要的元数据字段
            metadata['workflow_id'] = workflow_id
            metadata['state_data'] = state
            
            # 创建LangGraph配置
            config = self.langgraph_adapter.create_config(thread_id)
            
            # 创建LangGraph checkpoint
            langgraph_checkpoint = self.langgraph_adapter.create_checkpoint(state, workflow_id, metadata)
            
            # 使用上下文管理器保存checkpoint
            with self._get_checkpointer() as checkpointer:
                # 使用LangGraph的格式来保存
                checkpointer.put(config, langgraph_checkpoint, metadata, {})
            
            logger.debug(f"成功保存SQLite checkpoint，thread_id: {thread_id}, workflow_id: {workflow_id}")
            return True
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"保存SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"保存SQLite checkpoint失败: {e}")
    
    async def load_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据thread ID加载checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: 可选的checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据
        """
        try:
            config = self.langgraph_adapter.create_config(thread_id, checkpoint_id)
            
            # 使用上下文管理器获取checkpoint
            with self._get_checkpointer() as checkpointer:
                result = checkpointer.get(config)
            
            if result:
                from langgraph.checkpoint.base import CheckpointTuple
                # 检查result是否为CheckpointTuple
                if isinstance(result, CheckpointTuple):
                    # 是CheckpointTuple对象
                    langgraph_checkpoint = result.checkpoint
                    metadata = result.metadata
                else:
                    # 是字典格式或其他格式
                    langgraph_checkpoint = result
                    metadata = {}
                
                # 从metadata中获取workflow_id
                workflow_id = metadata.get('workflow_id', 'unknown')
                
                # 标准化metadata为字典格式
                normalized_metadata = self.metadata.normalize_metadata(metadata)
                
                return {
                    'id': langgraph_checkpoint.get('id') if isinstance(langgraph_checkpoint, dict) else None,
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': self.langgraph_adapter.extract_state(langgraph_checkpoint, metadata),
                    'metadata': normalized_metadata,
                    'created_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None,
                    'updated_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None
                }
            return None
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"加载SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"加载SQLite checkpoint失败: {e}")
    
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint list, sorted by creation time in descending order
        """
        try:
            config = self.langgraph_adapter.create_config(thread_id)
            
            # 使用上下文管理器列出checkpoint
            with self._get_checkpointer() as checkpointer:
                checkpoint_tuples = list(checkpointer.list(config))
            
            result = []
            for checkpoint_tuple in checkpoint_tuples:
                from langgraph.checkpoint.base import CheckpointTuple
                # 检查是否为CheckpointTuple
                if isinstance(checkpoint_tuple, CheckpointTuple):
                    langgraph_checkpoint = checkpoint_tuple.checkpoint
                    metadata = checkpoint_tuple.metadata
                else:
                    langgraph_checkpoint = checkpoint_tuple
                    metadata = {}
                
                workflow_id = metadata.get('workflow_id', 'unknown')
                normalized_metadata = self.metadata.normalize_metadata(metadata)
                
                result.append({
                    'id': langgraph_checkpoint.get('id') if isinstance(langgraph_checkpoint, dict) else None,
                    'thread_id': thread_id,
                    'workflow_id': workflow_id,
                    'state_data': self.langgraph_adapter.extract_state(langgraph_checkpoint, metadata),
                    'metadata': normalized_metadata,
                    'created_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None,
                    'updated_at': langgraph_checkpoint.get('ts') if isinstance(langgraph_checkpoint, dict) else None
                })
            
            # 按创建时间倒序排列
            result.sort(key=lambda x: x.get('created_at', '') or '', reverse=True)
            return result
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"列出SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"列出SQLite checkpoint失败: {e}")
    
    async def delete_by_thread(self, thread_id: str, checkpoint_id: Optional[str] = None) -> bool:
        """根据thread ID删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: Optional checkpoint ID, if None, delete all
            
        Returns:
            bool: Whether deletion was successful
        """
        try:
            if checkpoint_id:
                # SQLiteSaver不支持删除单个checkpoint
                # 我们通过重新保存除要删除的checkpoint之外的所有checkpoint来模拟
                checkpoints = await self.list_by_thread(thread_id)
                
                # 找到要保留的checkpoint（除要删除的之外）
                checkpoints_to_keep = []
                for checkpoint in checkpoints:
                    if checkpoint['id'] != checkpoint_id:
                        checkpoint_data = {
                            'thread_id': thread_id,
                            'workflow_id': checkpoint['workflow_id'],
                            'state_data': checkpoint['state_data'],
                            'metadata': checkpoint['metadata']
                        }
                        checkpoints_to_keep.append(checkpoint_data)
                
                # 删除整个会话
                config = self.langgraph_adapter.create_config(thread_id)
                with self._get_checkpointer() as checkpointer:
                    checkpointer.delete_thread(thread_id)
                
                # 重新保存需要保留的checkpoint
                for checkpoint_data in checkpoints_to_keep:
                    await self.save(checkpoint_data)
                
                return True
            else:
                # 删除整个会话的所有checkpoint
                config = self.langgraph_adapter.create_config(thread_id)
                with self._get_checkpointer() as checkpointer:
                    checkpointer.delete_thread(thread_id)
                return True
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"删除SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"删除SQLite checkpoint失败: {e}")
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """Clean up old checkpoints, keeping the latest max_count
        
        Args:
            thread_id: thread ID
            max_count: Maximum number to keep
            
        Returns:
            int: Number of deleted checkpoints
        """
        try:
            checkpoints = await self.list_by_thread(thread_id)
            if len(checkpoints) <= max_count:
                return 0
            
            # 保存需要保留的checkpoint
            checkpoints_to_keep = checkpoints[:max_count]
            
            # 获取需要保留的checkpoint数据
            checkpoints_data = []
            for checkpoint in checkpoints_to_keep:
                checkpoint_data = {
                    'thread_id': thread_id,
                    'workflow_id': checkpoint['workflow_id'],
                    'state_data': checkpoint['state_data'],
                    'metadata': checkpoint['metadata']
                }
                checkpoints_data.append(checkpoint_data)
            
            # 删除整个会话
            await self.delete_by_thread(thread_id)
            
            # 重新保存需要保留的checkpoint
            for checkpoint_data in checkpoints_data:
                await self.save(checkpoint_data)
            
            return len(checkpoints) - max_count
        except CheckpointError:
            raise
        except Exception as e:
            logger.error(f"清理旧SQLite checkpoint失败: {e}")
            raise CheckpointStorageError(f"清理旧SQLite checkpoint失败: {e}")
    
    def clear(self) -> None:
        """清除所有checkpoint（仅用于测试）"""
        try:
            # 由于SQLiteSaver没有直接的清除方法，我们可以通过删除数据库文件来实现
            import os
            if os.path.exists(self.sqlite_path):
                os.remove(self.sqlite_path)
                # 重新创建数据库
                db_dir = os.path.dirname(self.sqlite_path)
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
            logger.debug("SQLite checkpoint存储已清空")
        except Exception as e:
            logger.error(f"清空SQLite checkpoint存储失败: {e}")
            raise CheckpointStorageError(f"清空SQLite checkpoint存储失败: {e}")
    
    def get_langgraph_checkpointer(self) -> Any:
        """获取LangGraph原生的checkpointer
        
        Returns:
            LangGraph原生的checkpointer实例
        """
        return self._get_checkpointer()