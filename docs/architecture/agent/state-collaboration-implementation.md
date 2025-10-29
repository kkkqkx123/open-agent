# 状态管理器与适配器协作实现方案

## 核心问题

当前状态系统缺少状态管理器与适配器之间的有效协作机制，导致：
- 状态验证功能不完整
- 缺少状态快照管理
- 缺乏状态历史追踪

## 实现目标

1. **状态验证**：在状态转换前后进行完整性验证
2. **快照管理**：支持状态保存和恢复
3. **历史追踪**：记录状态变化历史
4. **性能优化**：确保协作机制不影响系统性能

## 核心实现方案

### 1. 增强状态管理器接口

**文件**: `src/domain/state/interfaces.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

class IStateCollaborationManager(ABC):
    """状态协作管理器接口"""
    
    @abstractmethod
    def validate_domain_state(self, domain_state: Any) -> List[str]:
        """验证域层状态完整性"""
        pass
    
    @abstractmethod
    def create_snapshot(self, domain_state: Any, description: str = "") -> str:
        """创建状态快照"""
        pass
    
    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> Optional[Any]:
        """恢复状态快照"""
        pass
    
    @abstractmethod
    def record_state_change(self, agent_id: str, action: str, 
                          old_state: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """记录状态变化"""
        pass
```

### 2. 协作适配器实现

**文件**: `src/infrastructure/graph/adapters/collaboration_adapter.py`

```python
from typing import Dict, Any, List
from src.domain.agent.state import AgentState as DomainAgentState
from src.infrastructure.graph.adapters.state_adapter import StateAdapter
from src.domain.state.interfaces import IStateCollaborationManager

class CollaborationStateAdapter:
    """协作状态适配器"""
    
    def __init__(self, collaboration_manager: IStateCollaborationManager):
        self.state_adapter = StateAdapter()
        self.collaboration_manager = collaboration_manager
    
    def execute_with_collaboration(self, graph_state: Dict[str, Any]) -> Dict[str, Any]:
        """带协作机制的状态转换"""
        # 1. 转换为域状态
        domain_state = self.state_adapter.from_graph_state(graph_state)
        
        # 2. 状态验证
        validation_errors = self._validate_state(domain_state)
        
        # 3. 记录状态变化开始
        snapshot_id = self._create_pre_execution_snapshot(domain_state)
        
        # 4. 执行业务逻辑（由具体节点实现）
        # 这里domain_state会被节点修改
        
        # 5. 记录状态变化结束
        self._record_state_completion(domain_state, snapshot_id, validation_errors)
        
        # 6. 转换回图状态
        result_state = self.state_adapter.to_graph_state(domain_state)
        
        # 7. 添加协作元数据
        return self._add_collaboration_metadata(result_state, snapshot_id, validation_errors)
    
    def _validate_state(self, domain_state: DomainAgentState) -> List[str]:
        """状态验证"""
        return self.collaboration_manager.validate_domain_state(domain_state)
    
    def _create_pre_execution_snapshot(self, domain_state: DomainAgentState) -> str:
        """创建执行前快照"""
        return self.collaboration_manager.create_snapshot(
            domain_state, "pre_execution"
        )
    
    def _record_state_completion(self, domain_state: DomainAgentState, 
                               snapshot_id: str, validation_errors: List[str]):
        """记录状态完成"""
        # 可以在这里添加完成后的处理逻辑
        pass
    
    def _add_collaboration_metadata(self, graph_state: Dict[str, Any], 
                                  snapshot_id: str, validation_errors: List[str]) -> Dict[str, Any]:
        """添加协作元数据"""
        if "metadata" not in graph_state:
            graph_state["metadata"] = {}
        
        graph_state["metadata"].update({
            "collaboration_snapshot_id": snapshot_id,
            "validation_errors": validation_errors,
            "collaboration_timestamp": datetime.now().isoformat()
        })
        
        return graph_state
```

### 3. 简单快照管理器

**文件**: `src/infrastructure/state/simple_snapshot_manager.py`

```python
import pickle
import zlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

class SimpleSnapshotManager:
    """简单快照管理器"""
    
    def __init__(self, max_snapshots: int = 100):
        self.max_snapshots = max_snapshots
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.agent_snapshots: Dict[str, List[str]] = {}
    
    def create_snapshot(self, domain_state: Any, description: str = "") -> str:
        """创建快照"""
        snapshot_id = str(uuid.uuid4())
        agent_id = getattr(domain_state, 'agent_id', 'unknown')
        
        # 序列化状态
        state_dict = domain_state.to_dict() if hasattr(domain_state, 'to_dict') else vars(domain_state)
        compressed_data = zlib.compress(pickle.dumps(state_dict))
        
        snapshot = {
            "snapshot_id": snapshot_id,
            "agent_id": agent_id,
            "timestamp": datetime.now(),
            "description": description,
            "compressed_data": compressed_data,
            "size_bytes": len(compressed_data)
        }
        
        # 保存快照
        self.snapshots[snapshot_id] = snapshot
        
        # 管理Agent的快照列表
        if agent_id not in self.agent_snapshots:
            self.agent_snapshots[agent_id] = []
        
        self.agent_snapshots[agent_id].append(snapshot_id)
        
        # 清理旧快照
        self._cleanup_old_snapshots(agent_id)
        
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[Any]:
        """恢复快照"""
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            return None
        
        # 解压缩和反序列化
        decompressed_data = zlib.decompress(snapshot["compressed_data"])
        state_dict = pickle.loads(decompressed_data)
        
        return state_dict
    
    def _cleanup_old_snapshots(self, agent_id: str):
        """清理旧快照"""
        if agent_id in self.agent_snapshots:
            snapshots = self.agent_snapshots[agent_id]
            if len(snapshots) > self.max_snapshots:
                # 删除最旧的快照
                oldest_snapshot_id = snapshots.pop(0)
                if oldest_snapshot_id in self.snapshots:
                    del self.snapshots[oldest_snapshot_id]
```

### 4. 集成到现有系统

#### 4.1 修改图构建器

**文件**: `src/infrastructure/graph/builder.py`

```python
class CollaborationNodeExecutor(INodeExecutor):
    """协作节点执行器"""
    
    def __init__(self, node_instance, collaboration_manager: IStateCollaborationManager):
        self.node = node_instance
        self.collaboration_adapter = CollaborationStateAdapter(collaboration_manager)
    
    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """执行节点逻辑，集成协作功能"""
        return self.collaboration_adapter.execute_with_collaboration(state)
```

#### 4.2 依赖注入配置

**文件**: `src/infrastructure/di_config.py`

```python
def configure_state_collaboration(container):
    """配置状态协作服务"""
    
    # 注册快照管理器
    container.register_singleton(SimpleSnapshotManager, SimpleSnapshotManager)
    
    # 注册协作管理器
    container.register_singleton(
        IStateCollaborationManager, 
        lambda c: EnhancedStateManager(c.get(SimpleSnapshotManager))
    )
```

## 部署策略

### 阶段一：最小可行实现
1. 实现基础协作适配器
2. 添加简单快照管理
3. 集成到测试环境

### 阶段二：功能完善
1. 添加状态验证逻辑
2. 实现历史记录功能
3. 性能优化

### 阶段三：生产部署
1. 全面测试
2. 性能基准测试
3. 逐步替换现有实现

## 性能考虑

### 优化措施
1. **异步快照**：非关键快照操作使用异步处理
2. **增量快照**：只保存状态变化部分
3. **内存缓存**：缓存常用快照
4. **压缩算法**：使用高效的数据压缩

### 监控指标
1. 快照创建时间
2. 状态验证耗时
3. 内存使用情况
4. 存储空间占用

## 测试计划

### 单元测试
- 协作适配器功能测试
- 快照管理测试
- 状态验证测试

### 集成测试
- 端到端工作流测试
- 性能基准测试
- 错误处理测试

### 负载测试
- 高并发状态操作
- 大状态对象处理
- 长时间运行稳定性

## 总结

本实现方案提供了状态管理器与适配器协作的完整解决方案，通过分阶段实施可以确保系统的稳定性和性能。核心优势包括：

1. **模块化设计**：各组件职责清晰
2. **向后兼容**：不影响现有功能
3. **性能优化**：考虑实际使用场景
4. **易于扩展**：支持未来功能增强