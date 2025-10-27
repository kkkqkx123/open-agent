# Session层LangGraph Thread集成实现示例

## 核心实现代码

### 1. Checkpoint数据模型

```python
# src/application/sessions/checkpoint.py
"""Checkpoint数据模型和存储"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import uuid
from datetime import datetime


@dataclass
class Checkpoint:
    """Checkpoint数据类"""
    thread_id: str
    checkpoint_id: str
    values: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    
    @classmethod
    def create(cls, thread_id: str, values: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> "Checkpoint":
        """创建新的checkpoint"""
        return cls(
            thread_id=thread_id,
            checkpoint_id=str(uuid.uuid4()),
            values=values or {},
            metadata=metadata or {},
            created_at=datetime.now().isoformat()
        )


class CheckpointStore:
    """Checkpoint存储实现"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, checkpoint: Checkpoint) -> str:
        """保存checkpoint"""
        thread_dir = self.storage_path / checkpoint.thread_id
        thread_dir.mkdir(exist_ok=True)
        
        checkpoint_file = thread_dir / f"{checkpoint.checkpoint_id}.json"
        temp_file = checkpoint_file.with_suffix(".tmp")
        
        try:
            # 原子性写入
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "thread_id": checkpoint.thread_id,
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "values": checkpoint.values,
                    "metadata": checkpoint.metadata,
                    "created_at": checkpoint.created_at
                }, f, ensure_ascii=False, indent=2)
            
            temp_file.replace(checkpoint_file)
            return checkpoint.checkpoint_id
            
        except Exception:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Checkpoint]:
        """获取checkpoint"""
        checkpoint_file = self.storage_path / thread_id / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Checkpoint(
                thread_id=data["thread_id"],
                checkpoint_id=data["checkpoint_id"],
                values=data["values"],
                metadata=data["metadata"],
                created_at=data["created_at"]
            )
        except Exception:
            return None
    
    def list_checkpoints(self, thread_id: str) -> List[Checkpoint]:
        """列出thread的所有checkpoints"""
        thread_dir = self.storage_path / thread_id
        if not thread_dir.exists():
            return []
        
        checkpoints = []
        for checkpoint_file in thread_dir.glob("*.json"):
            try:
                checkpoint = self.get_checkpoint(thread_id, checkpoint_file.stem)
                if checkpoint:
                    checkpoints.append(checkpoint)
            except Exception:
                continue
        
        # 按创建时间排序
        checkpoints.sort(key=lambda x: x.created_at)
        return checkpoints
    
    def get_latest_checkpoint(self, thread_id: str) -> Optional[Checkpoint]:
        """获取最新的checkpoint"""
        checkpoints = self.list_checkpoints(thread_id)
        if not checkpoints:
            return None
        return checkpoints[-1]  # 最后一个是最新的
```

### 2. Thread元数据管理

```python
# src/application/sessions/thread_metadata.py
"""Thread元数据管理"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json


class ThreadMetadataStore:
    """Thread元数据存储"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """保存thread元数据"""
        metadata_file = self.storage_path / f"{thread_id}.json"
        temp_file = metadata_file.with_suffix(".tmp")
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            temp_file.replace(metadata_file)
            return True
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    def get_metadata(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread元数据"""
        metadata_file = self.storage_path / f"{thread_id}.json"
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def update_metadata(self, thread_id: str, updates: Dict[str, Any]) -> bool:
        """更新thread元数据"""
        current_metadata = self.get_metadata(thread_id) or {}
        current_metadata.update(updates)
        return self.save_metadata(thread_id, current_metadata)
    
    def list_threads(self) -> List[Dict[str, Any]]:
        """列出所有threads"""
        threads = []
        for metadata_file in self.storage_path.glob("*.json"):
            try:
                metadata = self.get_metadata(metadata_file.stem)
                if metadata:
                    threads.append(metadata)
            except Exception:
                continue
        
        return threads
```

### 3. 扩展的Session管理器

```python
# src/application/sessions/langgraph_session_manager.py
"""支持LangGraph Thread的Session管理器"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import uuid
from datetime import datetime
import logging

from .manager import SessionManager
from .checkpoint import Checkpoint, CheckpointStore
from .thread_metadata import ThreadMetadataStore

logger = logging.getLogger(__name__)


class LangGraphSessionManager(SessionManager):
    """扩展的Session管理器，支持LangGraph Thread功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 初始化checkpoint和metadata存储
        checkpoint_path = self.storage_path / "checkpoints"
        metadata_path = self.storage_path / "threads"
        
        self.checkpoint_store = CheckpointStore(checkpoint_path)
        self.thread_metadata_store = ThreadMetadataStore(metadata_path)
    
    def create_thread(self, graph_id: str, initial_state: Optional[Dict[str, Any]] = None) -> str:
        """创建LangGraph Thread"""
        # 生成thread_id（兼容现有session_id格式）
        thread_id = self._generate_thread_id(graph_id)
        
        # 创建初始checkpoint
        checkpoint = Checkpoint.create(
            thread_id=thread_id,
            values=initial_state or {},
            metadata={
                "graph_id": graph_id,
                "created_at": datetime.now().isoformat(),
                "source": "thread_creation",
                "step": 0
            }
        )
        
        # 保存checkpoint
        checkpoint_id = self.checkpoint_store.save_checkpoint(checkpoint)
        
        # 保存thread元数据
        thread_metadata = {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat(),
            "latest_checkpoint": checkpoint_id,
            "checkpoint_count": 1,
            "status": "idle",
            "total_steps": 0
        }
        self.thread_metadata_store.save_metadata(thread_id, thread_metadata)
        
        logger.info(f"创建Thread成功: {thread_id}, graph_id: {graph_id}")
        return thread_id
    
    def get_thread_state(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """获取Thread状态"""
        if checkpoint_id:
            checkpoint = self.checkpoint_store.get_checkpoint(thread_id, checkpoint_id)
        else:
            # 获取最新checkpoint
            checkpoint = self.checkpoint_store.get_latest_checkpoint(thread_id)
        
        if not checkpoint:
            raise ValueError(f"Thread {thread_id} 不存在或没有checkpoint")
        
        return {
            "values": checkpoint.values,
            "config": {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint.checkpoint_id
                }
            },
            "metadata": checkpoint.metadata
        }
    
    def update_thread_state(self, thread_id: str, values: Dict[str, Any], 
                           checkpoint_id: Optional[str] = None) -> str:
        """更新Thread状态"""
        # 获取基础状态
        if checkpoint_id:
            base_checkpoint = self.checkpoint_store.get_checkpoint(thread_id, checkpoint_id)
        else:
            base_checkpoint = self.checkpoint_store.get_latest_checkpoint(thread_id)
        
        if not base_checkpoint:
            raise ValueError(f"Thread {thread_id} 不存在")
        
        # 创建新checkpoint（基于基础状态）
        new_values = {**base_checkpoint.values, **values}
        
        new_checkpoint = Checkpoint.create(
            thread_id=thread_id,
            values=new_values,
            metadata={
                **base_checkpoint.metadata,
                "updated_at": datetime.now().isoformat(),
                "source": "state_update",
                "step": base_checkpoint.metadata.get("step", 0) + 1,
                "parent_checkpoint": base_checkpoint.checkpoint_id
            }
        )
        
        # 保存新checkpoint
        new_checkpoint_id = self.checkpoint_store.save_checkpoint(new_checkpoint)
        
        # 更新thread元数据
        self.thread_metadata_store.update_metadata(thread_id, {
            "latest_checkpoint": new_checkpoint_id,
            "checkpoint_count": self.checkpoint_store.list_checkpoints(thread_id),
            "total_steps": new_checkpoint.metadata.get("step", 0),
            "updated_at": datetime.now().isoformat()
        })
        
        return new_checkpoint_id
    
    def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取Thread历史"""
        checkpoints = self.checkpoint_store.list_checkpoints(thread_id)
        return [
            {
                "checkpoint_id": cp.checkpoint_id,
                "values": cp.values,
                "metadata": cp.metadata,
                "created_at": cp.created_at
            }
            for cp in checkpoints
        ]
    
    def copy_thread(self, thread_id: str) -> str:
        """复制Thread"""
        source_metadata = self.thread_metadata_store.get_metadata(thread_id)
        if not source_metadata:
            raise ValueError(f"源Thread {thread_id} 不存在")
        
        # 创建新thread
        new_thread_id = self._generate_thread_id(source_metadata["graph_id"])
        
        # 复制最新的checkpoint
        latest_checkpoint = self.checkpoint_store.get_latest_checkpoint(thread_id)
        if latest_checkpoint:
            new_checkpoint = Checkpoint.create(
                thread_id=new_thread_id,
                values=latest_checkpoint.values,
                metadata={
                    **latest_checkpoint.metadata,
                    "source": "thread_copy",
                    "copied_from": thread_id,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            new_checkpoint_id = self.checkpoint_store.save_checkpoint(new_checkpoint)
            
            # 保存新thread元数据
            new_metadata = {
                **source_metadata,
                "thread_id": new_thread_id,
                "latest_checkpoint": new_checkpoint_id,
                "checkpoint_count": 1,
                "copied_from": thread_id,
                "created_at": datetime.now().isoformat()
            }
            self.thread_metadata_store.save_metadata(new_thread_id, new_metadata)
        
        return new_thread_id
    
    def search_threads(self, status: Optional[str] = None, 
                       metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """搜索Threads"""
        all_threads = self.thread_metadata_store.list_threads()
        results = []
        
        for thread_metadata in all_threads:
            # 状态过滤
            if status and thread_metadata.get("status") != status:
                continue
            
            # 元数据过滤
            if metadata_filter:
                match = True
                for key, value in metadata_filter.items():
                    if thread_metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(thread_metadata)
        
        return results
    
    def _generate_thread_id(self, graph_id: str) -> str:
        """生成thread_id"""
        # 使用与session_id相同的格式，但添加thread前缀
        base_session_id = super()._generate_session_id(graph_id)
        return f"thread-{base_session_id}"
```

### 4. LangGraph SDK适配器实现

```python
# src/application/sessions/langgraph_adapter.py
"""LangGraph SDK适配器"""

from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
from datetime import datetime


class LangGraphSDKAdapter:
    """LangGraph SDK适配器，提供与LangGraph SDK兼容的接口"""
    
    def __init__(self, session_manager: LangGraphSessionManager):
        self.session_manager = session_manager
    
    async def threads_create(self, graph_id: str, supersteps: Optional[List] = None) -> Dict[str, Any]:
        """模拟LangGraph SDK的threads.create方法"""
        # 创建初始状态
        initial_state = {}
        if supersteps:
            # 处理supersteps中的初始状态
            for step in supersteps:
                for update in step.get("updates", []):
                    if update.get("as_node") == "__start__":
                        initial_state.update(update.get("values", {}))
        
        thread_id = self.session_manager.create_thread(graph_id, initial_state)
        
        # 应用剩余的supersteps
        if supersteps:
            for i, step in enumerate(supersteps):
                if i == 0:  # 跳过第一个（初始状态）
                    continue
                for update in step.get("updates", []):
                    values = update.get("values", {})
                    self.session_manager.update_thread_state(thread_id, values)
        
        return {
            "thread_id": thread_id,
            "graph_id": graph_id,
            "created_at": datetime.now().isoformat()
        }
    
    async def threads_get_state(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """模拟LangGraph SDK的threads.get_state方法"""
        return self.session_manager.get_thread_state(thread_id, checkpoint_id)
    
    async def threads_update_state(self, thread_id: str, values: Dict[str, Any], 
                                  checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """模拟LangGraph SDK的threads.update_state方法"""
        new_checkpoint_id = self.session_manager.update_thread_state(thread_id, values, checkpoint_id)
        
        return {
            "thread_id": thread_id,
            "checkpoint_id": new_checkpoint_id,
            "config": {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_id": new_checkpoint_id
                }
            }
        }
    
    async def threads_copy(self, thread_id: str) -> Dict[str, Any]:
        """模拟LangGraph SDK的threads.copy方法"""
        new_thread_id = self.session_manager.copy_thread(thread_id)
        
        return {
            "thread_id": new_thread_id,
            "copied_from": thread_id,
            "created_at": datetime.now().isoformat()
        }
    
    async def threads_search(self, status: Optional[str] = None, 
                            metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """模拟LangGraph SDK的threads.search方法"""
        return self.session_manager.search_threads(status, metadata)
```

### 5. 使用示例

```python
# 示例代码：如何使用扩展的Session管理器

def demo_langgraph_integration():
    """演示LangGraph集成功能"""
    
    # 初始化扩展的Session管理器
    from src.application.sessions.langgraph_session_manager import LangGraphSessionManager
    from src.application.sessions.langgraph_adapter import LangGraphSDKAdapter
    
    # 创建管理器实例
    session_manager = LangGraphSessionManager(...)  # 传入必要的依赖
    
    # 创建SDK适配器
    sdk_adapter = LangGraphSDKAdapter(session_manager)
    
    # 1. 创建Thread（LangGraph风格）
    thread_info = asyncio.run(sdk_adapter.threads_create("agent"))
    thread_id = thread_info["thread_id"]
    print(f"创建Thread: {thread_id}")
    
    # 2. 获取Thread状态
    state = asyncio.run(sdk_adapter.threads_get_state(thread_id))
    print(f"Thread状态: {state}")
    
    # 3. 更新Thread状态（模拟工作流执行）
    new_state = {
        "messages": [{"role": "human", "content": "Hello"}],
        "current_step": "process_input"
    }
    updated = asyncio.run(sdk_adapter.threads_update_state(thread_id, new_state))
    print(f"状态更新: {updated}")
    
    # 4. 获取历史
    history = session_manager.get_thread_history(thread_id)
    print(f"历史记录: {len(history)} 个checkpoints")
    
    # 5. 搜索Threads
    threads = asyncio.run(sdk_adapter.threads_search(status="idle"))
    print(f"找到 {len(threads)} 个空闲Threads")
    
    # 6. 与现有Session系统兼容
    # 可以继续使用原有的Session接口
    session_id = session_manager.create_session("configs/workflows/base_workflow.yaml")
    print(f"兼容创建Session: {session_id}")

if __name__ == "__main__":
    demo_langgraph_integration()
```

## 实施建议

### 1. 渐进式迁移策略
- 首先实现基础Checkpoint功能
- 然后添加Thread元数据管理
- 最后实现SDK适配器

### 2. 测试策略
- 单元测试：每个组件单独测试
- 集成测试：验证Session-Thread交互
- 兼容性测试：确保现有功能不受影响

### 3. 性能考虑
- Checkpoint文件使用增量存储
- 实现checkpoint缓存机制
- 支持批量操作优化

这个实现方案提供了完整的LangGraph Thread功能，同时保持了与现有Session系统的完全兼容性。