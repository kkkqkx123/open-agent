"""状态服务

提供状态数据的存储和管理服务。
"""

import time
from typing import Dict, Any, Optional, List, AsyncIterator
from src.interfaces.storage.base import IStorage
from src.interfaces.storage.exceptions import StorageError
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class StateService:
    """状态服务
    
    提供状态数据的存储、查询、更新和删除功能。
    """
    
    def __init__(self, storage: IStorage) -> None:
        """初始化状态服务
        
        Args:
            storage: 存储实例
        """
        self.storage = storage
        self.logger = get_logger(self.__class__.__name__)
    
    async def save_state(
        self,
        state_data: Dict[str, Any],
        state_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存状态
        
        Args:
            state_data: 状态数据
            state_id: 状态ID，None表示自动生成
            metadata: 元数据
            
        Returns:
            状态ID
            
        Raises:
            StorageError: 保存失败
        """
        try:
            # 准备数据
            data = state_data.copy()
            
            # 添加状态标识
            data["type"] = "state"
            
            # 设置状态ID
            if state_id:
                data["id"] = state_id
            
            # 添加元数据
            if metadata:
                data["metadata"] = metadata
            
            # 添加时间戳
            current_time = time.time()
            data["created_at"] = current_time
            data["updated_at"] = current_time
            
            # 保存状态
            result_id = await self.storage.save(data)
            
            self.logger.debug(f"状态保存成功，ID: {result_id}")
            return result_id
            
        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
            raise StorageError(f"Failed to save state: {e}")
    
    async def load_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """加载状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态数据，不存在则返回None
            
        Raises:
            StorageError: 加载失败
        """
        try:
            # 加载数据
            data = await self.storage.load(state_id)
            
            if data is None:
                return None
            
            # 验证数据类型
            if data.get("type") != "state":
                self.logger.warning(f"数据类型不匹配，期望'state'，实际'{data.get('type')}'")
                return None
            
            self.logger.debug(f"状态加载成功，ID: {state_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"加载状态失败: {e}")
            raise StorageError(f"Failed to load state {state_id}: {e}")
    
    async def update_state(
        self,
        state_id: str,
        updates: Dict[str, Any],
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新状态
        
        Args:
            state_id: 状态ID
            updates: 更新数据
            metadata_updates: 元数据更新
            
        Returns:
            是否更新成功
            
        Raises:
            StorageError: 更新失败
        """
        try:
            # 加载现有状态
            current_state = await self.load_state(state_id)
            if current_state is None:
                return False
            
            # 更新数据
            current_state.update(updates)
            current_state["updated_at"] = time.time()
            
            # 更新元数据
            if metadata_updates and "metadata" in current_state:
                current_metadata = current_state["metadata"].copy()
                current_metadata.update(metadata_updates)
                current_state["metadata"] = current_metadata
            
            # 保存更新
            result_id = await self.storage.save(current_state)
            
            success = result_id == state_id
            if success:
                self.logger.debug(f"状态更新成功，ID: {state_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
            raise StorageError(f"Failed to update state {state_id}: {e}")
    
    async def delete_state(self, state_id: str) -> bool:
        """删除状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            是否删除成功
            
        Raises:
            StorageError: 删除失败
        """
        try:
            # 验证状态存在
            state = await self.load_state(state_id)
            if state is None:
                return False
            
            # 删除状态
            result = await self.storage.delete(state_id)
            
            if result:
                self.logger.debug(f"状态删除成功，ID: {state_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"删除状态失败: {e}")
            raise StorageError(f"Failed to delete state {state_id}: {e}")
    
    async def list_states(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出状态
        
        Args:
            filters: 过滤条件
            limit: 限制数量
            
        Returns:
            状态列表
            
        Raises:
            StorageError: 查询失败
        """
        try:
            # 准备过滤条件
            query_filters = filters or {}
            query_filters["type"] = "state"
            
            # 查询状态
            states = await self.storage.list(query_filters, limit)
            
            self.logger.debug(f"列出状态成功，返回 {len(states)} 条记录")
            return states
            
        except Exception as e:
            self.logger.error(f"列出状态失败: {e}")
            raise StorageError(f"Failed to list states: {e}")
    
    async def query_states(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """查询状态
        
        Args:
            query: 查询语句
            params: 查询参数
            
        Returns:
            状态列表
            
        Raises:
            StorageError: 查询失败
        """
        try:
            # 执行查询
            all_results = await self.storage.query(query, params or {})
            
            # 过滤状态类型
            states = [
                result for result in all_results
                if result.get("type") == "state"
            ]
            
            self.logger.debug(f"查询状态成功，返回 {len(states)} 条记录")
            return states
            
        except Exception as e:
            self.logger.error(f"查询状态失败: {e}")
            raise StorageError(f"Failed to query states: {e}")
    
    async def count_states(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """计数状态
        
        Args:
            filters: 过滤条件
            
        Returns:
            状态数量
            
        Raises:
            StorageError: 计数失败
        """
        try:
            # 准备过滤条件
            query_filters = filters or {}
            query_filters["type"] = "state"
            
            # 计数
            count = await self.storage.count(query_filters)
            
            self.logger.debug(f"计数状态成功，数量: {count}")
            return count
            
        except Exception as e:
            self.logger.error(f"计数状态失败: {e}")
            raise StorageError(f"Failed to count states: {e}")
    
    async def state_exists(self, state_id: str) -> bool:
        """检查状态是否存在
        
        Args:
            state_id: 状态ID
            
        Returns:
            是否存在
            
        Raises:
            StorageError: 检查失败
        """
        try:
            # 检查存在
            exists = await self.storage.exists(state_id)
            
            if not exists:
                return False
            
            # 验证类型
            state = await self.load_state(state_id)
            return state is not None
            
        except Exception as e:
            self.logger.error(f"检查状态存在失败: {e}")
            raise StorageError(f"Failed to check state existence {state_id}: {e}")
    
    async def batch_save_states(self, states: List[Dict[str, Any]]) -> List[str]:
        """批量保存状态
        
        Args:
            states: 状态列表
            
        Returns:
            状态ID列表
            
        Raises:
            StorageError: 批量保存失败
        """
        try:
            # 准备数据
            prepared_states = []
            for state_data in states:
                data = state_data.copy()
                data["type"] = "state"
                
                # 添加时间戳
                current_time = time.time()
                data["created_at"] = current_time
                data["updated_at"] = current_time
                
                prepared_states.append(data)
            
            # 批量保存
            state_ids = await self.storage.batch_save(prepared_states)
            
            self.logger.debug(f"批量保存状态成功，保存了 {len(state_ids)} 条记录")
            return state_ids
            
        except Exception as e:
            self.logger.error(f"批量保存状态失败: {e}")
            raise StorageError(f"Failed to batch save states: {e}")
    
    async def batch_delete_states(self, state_ids: List[str]) -> int:
        """批量删除状态
        
        Args:
            state_ids: 状态ID列表
            
        Returns:
            删除的数量
            
        Raises:
            StorageError: 批量删除失败
        """
        try:
            # 验证所有状态都存在且类型正确
            valid_ids = []
            for state_id in state_ids:
                if await self.state_exists(state_id):
                    valid_ids.append(state_id)
            
            if not valid_ids:
                return 0
            
            # 批量删除
            count = await self.storage.batch_delete(valid_ids)
            
            self.logger.debug(f"批量删除状态成功，删除了 {count} 条记录")
            return count
            
        except Exception as e:
            self.logger.error(f"批量删除状态失败: {e}")
            raise StorageError(f"Failed to batch delete states: {e}")
    
    def stream_states(
        self,
        filters: Optional[Dict[str, Any]] = None,
        batch_size: int = 100
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """流式列出状态
        
        Args:
            filters: 过滤条件
            batch_size: 批次大小
            
        Yields:
            状态批次列表
        """
        # 准备过滤条件
        query_filters = filters or {}
        query_filters["type"] = "state"
        
        # 流式查询
        return self.storage.stream_list(query_filters, batch_size)
    
    async def get_state_metadata(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态元数据
        
        Args:
            state_id: 状态ID
            
        Returns:
            元数据字典，不存在则返回None
        """
        state = await self.load_state(state_id)
        if state is None:
            return None
        
        metadata: Dict[str, Any] = state.get("metadata", {})
        return metadata
    
    async def update_state_metadata(
        self,
        state_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """更新状态元数据
        
        Args:
            state_id: 状态ID
            metadata_updates: 元数据更新
            
        Returns:
            是否更新成功
        """
        return await self.update_state(state_id, {}, metadata_updates)
    
    async def get_states_by_metadata(
        self,
        metadata_filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根据元数据过滤状态
        
        Args:
            metadata_filters: 元数据过滤条件
            limit: 限制数量
            
        Returns:
            状态列表
        """
        # 获取所有状态
        all_states = await self.list_states(limit=limit)
        
        # 过滤元数据
        filtered_states = []
        for state in all_states:
            metadata = state.get("metadata", {})
            match = True
            
            for key, value in metadata_filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_states.append(state)
        
        return filtered_states
    
    async def get_recent_states(
        self,
        time_limit: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取最近的状态
        
        Args:
            time_limit: 时间限制（秒），None表示不限制
            limit: 数量限制
            
        Returns:
            状态列表
        """
        # 获取所有状态
        all_states = await self.list_states(limit=limit)
        
        # 时间过滤
        if time_limit is not None:
            current_time = time.time()
            cutoff_time = current_time - time_limit
            
            filtered_states = [
                state for state in all_states
                if state.get("created_at", 0) >= cutoff_time
            ]
        else:
            filtered_states = all_states
        
        # 按时间排序
        filtered_states.sort(
            key=lambda s: s.get("created_at", 0),
            reverse=True
        )
        
        return filtered_states
