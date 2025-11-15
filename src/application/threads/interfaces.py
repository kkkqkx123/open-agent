"""Thread应用服务接口定义

包含Thread应用层服务的接口，负责编排业务流程和协调领域对象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime

from ...infrastructure.graph.states import WorkflowState


class IThreadService(ABC):
    """Thread应用服务接口
    
    负责Thread的应用层逻辑，包括工作流执行、状态管理、分支和快照等。
    """
    
    # === Thread生命周期管理 ===
    
    @abstractmethod
    async def create_thread(self, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新的Thread
        
        Args:
            graph_id: 关联的图ID
            metadata: Thread元数据
            
        Returns:
            创建的Thread ID
        """
        pass
    
    @abstractmethod
    async def create_thread_from_config(self, config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """从配置文件创建Thread
        
        Args:
            config_path: 配置文件路径
            metadata: Thread元数据
            
        Returns:
            创建的Thread ID
        """
        pass
    
    @abstractmethod
    async def get_thread_info(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread信息
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread信息，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新Thread状态
        
        Args:
            thread_id: Thread ID
            status: 新状态
            
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    async def update_thread_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """更新Thread元数据
        
        Args:
            thread_id: Thread ID
            metadata: 要更新的元数据
            
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """删除Thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    async def list_threads(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出Threads
        
        Args:
            filters: 过滤条件
            limit: 返回结果数量限制
            
        Returns:
            Thread信息列表
        """
        pass
    
    @abstractmethod
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread是否存在
        """
        pass
    
    # === 工作流执行 ===
    
    @abstractmethod
    async def execute_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """执行工作流
        
        Args:
            thread_id: Thread ID
            config: 运行配置
            initial_state: 初始状态
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    async def stream_workflow(
        self,
        thread_id: str,
        config: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流
        
        Args:
            thread_id: Thread ID
            config: 运行配置
            initial_state: 初始状态
            
        Yields:
            中间状态
        """
        pass
    
    # === 状态管理 ===
    
    @abstractmethod
    async def get_thread_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread状态
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread状态，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_thread_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """更新Thread状态
        
        Args:
            thread_id: Thread ID
            state: 新状态
            
        Returns:
            更新是否成功
        """
        pass
    
    # === 分支管理 ===
    
    @abstractmethod
    async def create_branch(
        self,
        thread_id: str,
        checkpoint_id: str,
        branch_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建Thread分支
        
        Args:
            thread_id: 源Thread ID
            checkpoint_id: 检查点ID
            branch_name: 分支名称
            metadata: 分支元数据
            
        Returns:
            新分支的Thread ID
        """
        pass
    
    @abstractmethod
    async def get_thread_branches(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取Thread的所有分支
        
        Args:
            thread_id: Thread ID
            
        Returns:
            分支信息列表
        """
        pass
    
    @abstractmethod
    async def merge_branch(
        self,
        target_thread_id: str,
        source_thread_id: str,
        merge_strategy: str = "latest"
    ) -> bool:
        """合并分支到目标Thread
        
        Args:
            target_thread_id: 目标Thread ID
            source_thread_id: 源Thread ID（分支）
            merge_strategy: 合并策略
            
        Returns:
            合并是否成功
        """
        pass
    
    # === 快照管理 ===
    
    @abstractmethod
    async def create_snapshot(
        self,
        thread_id: str,
        snapshot_name: str,
        description: Optional[str] = None
    ) -> str:
        """创建Thread快照
        
        Args:
            thread_id: Thread ID
            snapshot_name: 快照名称
            description: 快照描述
            
        Returns:
            快照ID
        """
        pass
    
    @abstractmethod
    async def restore_snapshot(
        self,
        thread_id: str,
        snapshot_id: str
    ) -> bool:
        """从快照恢复Thread状态
        
        Args:
            thread_id: Thread ID
            snapshot_id: 快照ID
            
        Returns:
            恢复是否成功
        """
        pass
    
    @abstractmethod
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            删除是否成功
        """
        pass
    
    # === 回滚管理 ===
    
    @abstractmethod
    async def rollback_thread(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> bool:
        """回滚Thread到指定检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            回滚是否成功
        """
        pass
    
    # === 查询和搜索 ===
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_thread_statistics(self) -> Dict[str, Any]:
        """获取Thread统计信息
        
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    async def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取Thread历史记录
        
        Args:
            thread_id: Thread ID
            limit: 记录数量限制
            
        Returns:
            历史记录列表
        """
        pass
    
    # === 协作管理 ===
    
    @abstractmethod
    async def share_thread_state(
        self,
        source_thread_id: str,
        target_thread_id: str,
        checkpoint_id: str,
        permissions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """共享Thread状态到其他Thread
        
        Args:
            source_thread_id: 源Thread ID
            target_thread_id: 目标Thread ID
            checkpoint_id: 检查点ID
            permissions: 权限配置
            
        Returns:
            共享是否成功
        """
        pass
    
    @abstractmethod
    async def create_shared_session(
        self,
        thread_ids: List[str],
        session_config: Dict[str, Any]
    ) -> str:
        """创建共享会话
        
        Args:
            thread_ids: Thread ID列表
            session_config: 会话配置
            
        Returns:
            共享会话ID
        """
        pass
    
    @abstractmethod
    async def sync_thread_states(
        self,
        thread_ids: List[str],
        sync_strategy: str = "bidirectional"
    ) -> bool:
        """同步多个Thread状态
        
        Args:
            thread_ids: Thread ID列表
            sync_strategy: 同步策略
            
        Returns:
            同步是否成功
        """
        pass