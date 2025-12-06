"""基础线程管理服务"""

import uuid
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime

from typing import TYPE_CHECKING
from src.core.threads.interfaces import IThreadCore
from src.core.threads.entities import Thread, ThreadStatus, ThreadType, ThreadMetadata
from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.storage.exceptions import StorageValidationError as ValidationError, StorageNotFoundError as EntityNotFoundError
from .base_service import BaseThreadService

if TYPE_CHECKING:
    from src.core.threads.checkpoints.domain_service import ThreadCheckpointDomainService


class BasicThreadService(BaseThreadService):
    """基础线程管理服务"""
    
    def __init__(
        self,
        thread_core: IThreadCore,
        thread_repository: IThreadRepository,
        checkpoint_domain_service: Optional['ThreadCheckpointDomainService'] = None
    ):
        """初始化基础线程服务
        
        Args:
            thread_core: 线程核心接口
            thread_repository: 线程仓储接口
            checkpoint_domain_service: 检查点领域服务
        """
        super().__init__(thread_repository)
        self._thread_core = thread_core
        self._checkpoint_domain_service = checkpoint_domain_service
    
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread
        
        Args:
            graph_id: 关联的图ID
            metadata: Thread元数据
            
        Returns:
            创建的Thread ID
        """
        try:
            self._log_operation("create_thread", metadata=metadata)
            
            # 生成线程ID
            thread_id = str(uuid.uuid4())
            
            # 创建线程实体
            thread_data = self._thread_core.create_thread(
                thread_id=thread_id,
                graph_id=graph_id,
                thread_type=ThreadType.MAIN,
                metadata=metadata or {}
            )
            
            thread = Thread.from_dict(thread_data)
            
            # 保存线程
            success = await self._thread_repository.create(thread)
            if not success:
                raise ValidationError("Failed to create thread")
            
            return thread_id
            
        except Exception as e:
            self._handle_exception(e, "create thread")
            raise
    
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """从配置文件创建Thread
        
        Args:
            config_path: 配置文件路径
            metadata: Thread元数据
            
        Returns:
            创建的Thread ID
        """
        try:
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 从配置中获取图ID
            graph_id = config.get('graph_id')
            if not graph_id:
                raise ValidationError("Config file must contain 'graph_id'")
            
            # 合并元数据
            config_metadata = config.get('metadata', {})
            if metadata:
                config_metadata.update(metadata)
            
            # 创建线程
            thread_id = await self.create_thread(graph_id, config_metadata)
            
            # 更新线程配置
            thread = await self._thread_repository.get(thread_id)
            if thread:
                thread._config = config
                thread.update_timestamp()
                await self._thread_repository.update(thread)
            
            return thread_id
            
        except FileNotFoundError:
            raise ValidationError(f"Config file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid config file format: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Failed to create thread from config: {str(e)}")
    
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread信息，如果不存在则返回None
        """
        try:
            self._log_operation("get_thread_info", thread_id)
            
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return None
            
            return {
                "id": thread.id,
                "status": thread.status,
                "type": thread.type,
                "graph_id": thread.graph_id,
                "parent_thread_id": thread.parent_thread_id,
                "source_checkpoint_id": thread.source_checkpoint_id,
                "created_at": thread.created_at.isoformat(),
                "updated_at": thread.updated_at.isoformat(),
                "metadata": thread.metadata,
                "config": thread.config,
                "message_count": thread.message_count,
                "checkpoint_count": thread.checkpoint_count,
                "branch_count": thread.branch_count
            }
            
        except Exception as e:
            self._handle_exception(e, "get thread info")
            return None
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态
        
        Args:
            thread_id: Thread ID
            status: 新状态
            
        Returns:
            更新是否成功
        """
        try:
            self._log_operation("update_thread_status", thread_id, status=status)
            
            thread = await self._validate_thread_exists(thread_id)
            
            # 验证状态
            try:
                new_status = ThreadStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}")
            
            # 检查状态转换是否有效
            if not thread.can_transition_to(new_status):
                raise ValidationError(f"Cannot transition from {thread.status} to {status}")
            
            # 更新状态
            thread.transition_to(new_status)
            success = await self._thread_repository.update(thread)
            
            return success
            
        except Exception as e:
            self._handle_exception(e, "update thread status")
            return False
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除是否成功
        """
        try:
            self._log_operation("delete_thread", thread_id)
            
            # 检查线程是否存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return False
            
            # 执行删除
            return await self._thread_repository.delete(thread_id)
            
        except Exception as e:
            self._handle_exception(e, "delete thread")
            return False
    
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads
        
        Args:
            filters: 过滤条件
            limit: 返回结果数量限制
            
        Returns:
            Thread信息列表
        """
        try:
            if filters:
                # 使用过滤条件搜索
                threads = await self._thread_repository.search_with_filters(filters, limit)
            else:
                # 获取所有线程
                threads = await self._thread_repository.search("", limit=1000)  # 限制最大数量
            
            # 转换为字典格式
            result: List[Dict[str, Any]] = []
            for thread in threads:
                thread_info: Dict[str, Any] = {
                    "id": thread.id,
                    "status": thread.status,
                    "type": thread.type,
                    "graph_id": thread.graph_id,
                    "created_at": thread.created_at.isoformat(),
                    "updated_at": thread.updated_at.isoformat(),
                    "message_count": thread.message_count,
                    "checkpoint_count": thread.checkpoint_count,
                    "branch_count": thread.branch_count
                }
                
                # 添加元数据信息
                metadata = thread.metadata
                if metadata.get("title"):
                    thread_info["title"] = metadata["title"]
                if metadata.get("tags"):
                    thread_info["tags"] = metadata["tags"]
                
                result.append(thread_info)
            
            return result
            
        except Exception as e:
            raise ValidationError(f"Failed to list threads: {str(e)}")
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread是否存在
        """
        try:
            return await self._thread_repository.exists(thread_id)
        except Exception:
            return False
    
    async def validate_thread_state(self, thread_id: str) -> bool:
        """验证Thread状态
        
        Args:
            thread_id: 线程ID
            
        Returns:
            状态有效返回True，无效返回False
        """
        try:
            self._log_operation("validate_thread_state", thread_id)
            
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return False
            
            # 基本状态验证
            if thread.status not in ThreadStatus:
                return False
            
            # 计数器验证
            if thread.message_count < 0 or thread.checkpoint_count < 0 or thread.branch_count < 0:
                return False
            
            # 时间戳验证
            if thread.updated_at < thread.created_at:
                return False
            
            return True
        except Exception:
            return False
    
    async def can_transition_to_status(self, thread_id: str, new_status: str) -> bool:
        """检查是否可以转换到指定状态
        
        Args:
            thread_id: 线程ID
            new_status: 目标状态
            
        Returns:
            可以转换返回True，否则返回False
        """
        try:
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                return False
            
            try:
                target_status = ThreadStatus(new_status)
            except ValueError:
                return False
            
            return thread.can_transition_to(target_status)
        except Exception:
            return False
    
    async def get_thread_statistics(self) -> Dict[str, Any]:
        """获取Thread统计信息
        
        Returns:
            统计信息字典
        """
        try:
            return await self._thread_repository.get_statistics()
        except Exception as e:
            raise ValidationError(f"Failed to get thread statistics: {str(e)}")
    
    async def search_threads(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """搜索Threads
        
        Args:
            filters: 过滤条件
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            搜索结果列表
        """
        try:
            threads = await self._thread_repository.search_with_filters(
                filters or {}, limit, offset
            )
            
            # 转换为字典格式
            result = []
            for thread in threads:
                thread_info = {
                    "id": thread.id,
                    "status": thread.status,
                    "type": thread.type,
                    "graph_id": thread.graph_id,
                    "created_at": thread.created_at.isoformat(),
                    "updated_at": thread.updated_at.isoformat(),
                    "message_count": thread.message_count,
                    "checkpoint_count": thread.checkpoint_count,
                    "branch_count": thread.branch_count
                }
                result.append(thread_info)
            
            return result
            
        except Exception as e:
            raise ValidationError(f"Failed to search threads: {str(e)}")
    
    async def list_threads_by_type(self, thread_type: str) -> List[Dict[str, Any]]:
        """按类型列线程
        
        Args:
            thread_type: 线程类型
            
        Returns:
            线程列表
        """
        try:
            # 验证线程类型
            try:
                type_enum = ThreadType(thread_type)
            except ValueError:
                raise ValidationError(f"Invalid thread type: {thread_type}")
            
            threads = await self._thread_repository.list_by_type(type_enum)
            
            # 转换为字典格式
            result = []
            for thread in threads:
                thread_info = {
                    "id": thread.id,
                    "status": thread.status,
                    "type": thread.type,
                    "graph_id": thread.graph_id,
                    "created_at": thread.created_at.isoformat(),
                    "updated_at": thread.updated_at.isoformat(),
                    "message_count": thread.message_count,
                    "checkpoint_count": thread.checkpoint_count,
                    "branch_count": thread.branch_count
                }
                result.append(thread_info)
            
            return result
            
        except Exception as e:
            raise ValidationError(f"Failed to list threads by type: {str(e)}")
    
    # === 核心业务方法 ===
    
    async def rollback_thread(self, thread_id: str, checkpoint_id: str) -> bool:
        """回滚Thread到指定检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            回滚是否成功
        """
        try:
            self._log_operation("rollback_thread", thread_id, checkpoint_id=checkpoint_id)
            
            # 验证线程存在
            thread = await self._validate_thread_exists(thread_id)
            
            # 验证检查点服务存在
            if not self._checkpoint_domain_service:
                raise ValidationError("Checkpoint service not available")
            
            # 从检查点服务获取状态
            state_data = await self._checkpoint_domain_service.restore_from_checkpoint(checkpoint_id)
            if not state_data:
                raise ValidationError(f"Checkpoint {checkpoint_id} not found or invalid")
            
            # 使用核心服务更新线程状态
            thread_dict = thread.to_dict()
            self._thread_core.update_thread_state(thread_dict, state_data)
            
            # 从更新后的字典创建新线程对象
            updated_thread = Thread.from_dict(thread_dict)
            
            # 保存更新后的线程
            success = await self._thread_repository.update(updated_thread)
            
            return success
            
        except Exception as e:
            self._handle_exception(e, "rollback thread")
            return False