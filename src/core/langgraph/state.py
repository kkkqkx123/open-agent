"""LangGraph状态定义"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
import operator


class LangGraphState(TypedDict):
    """LangGraph状态定义 - 基础状态模式"""
    
    # 消息列表 - 使用operator.add支持自动合并
    messages: List[Any]
    
    # 当前执行步骤
    current_step: str
    
    # 执行结果
    results: Dict[str, Any]
    
    # 元数据
    metadata: Dict[str, Any]
    
    # 关联的Thread ID
    thread_id: str
    
    # 状态版本
    version: int
    
    # 创建时间
    created_at: datetime
    
    # 更新时间
    updated_at: datetime


class LangGraphCheckpointState(TypedDict):
    """LangGraph Checkpoint状态 - 用于时间旅行和分支"""
    
    # 基础状态
    base_state: LangGraphState
    
    # Checkpoint ID
    checkpoint_id: str
    
    # 父Checkpoint ID (用于分支追踪)
    parent_checkpoint_id: Optional[str]
    
    # 分支信息
    branch_info: Optional[Dict[str, Any]]
    
    # Checkpoint元数据
    checkpoint_metadata: Dict[str, Any]


class LangGraphThreadState(TypedDict):
    """LangGraph Thread状态 - 线程级别的状态管理"""
    
    # Thread ID
    thread_id: str
    
    # 关联的Graph ID
    graph_id: str
    
    # 当前状态
    current_state: LangGraphState
    
    # Checkpoint历史
    checkpoint_history: List[LangGraphCheckpointState]
    
    # 分支信息
    branches: Dict[str, Dict[str, Any]]
    
    # Thread元数据
    thread_metadata: Dict[str, Any]
    
    # Thread状态
    status: str  # ACTIVE, PAUSED, COMPLETED, FAILED, BRANCHED
    
    # 创建时间
    created_at: datetime
    
    # 最后更新时间
    updated_at: datetime


class LangGraphMergeState(TypedDict):
    """LangGraph合并状态 - 用于分支合并"""
    
    # 主线状态
    main_state: LangGraphState
    
    # 分支状态
    branch_state: LangGraphState
    
    # 基线状态 (三路合并)
    base_state: Optional[LangGraphState]
    
    # 合并策略
    merge_strategy: str
    
    # 冲突信息
    conflicts: List[Dict[str, Any]]
    
    # 合并结果
    merged_state: Optional[LangGraphState]
    
    # 合并元数据
    merge_metadata: Dict[str, Any]


# 状态更新函数
def create_initial_state(thread_id: str, graph_id: str) -> LangGraphState:
    """创建初始LangGraph状态"""
    now = datetime.now()
    return {
        "messages": [],
        "current_step": "start",
        "results": {},
        "metadata": {
            "graph_id": graph_id,
            "thread_id": thread_id
        },
        "thread_id": thread_id,
        "version": 1,
        "created_at": now,
        "updated_at": now
    }


def update_state_version(state: LangGraphState) -> LangGraphState:
    """更新状态版本"""
    state["version"] += 1
    state["updated_at"] = datetime.now()
    return state


def create_checkpoint_state(
    state: LangGraphState, 
    checkpoint_id: str,
    parent_checkpoint_id: Optional[str] = None
) -> LangGraphCheckpointState:
    """创建Checkpoint状态"""
    return {
        "base_state": state.copy(),
        "checkpoint_id": checkpoint_id,
        "parent_checkpoint_id": parent_checkpoint_id,
        "branch_info": None,
        "checkpoint_metadata": {
            "created_at": datetime.now(),
            "state_version": state["version"]
        }
    }


def create_thread_state(thread_id: str, graph_id: str) -> LangGraphThreadState:
    """创建Thread状态"""
    now = datetime.now()
    initial_state = create_initial_state(thread_id, graph_id)
    
    return {
        "thread_id": thread_id,
        "graph_id": graph_id,
        "current_state": initial_state,
        "checkpoint_history": [],
        "branches": {},
        "thread_metadata": {},
        "status": "ACTIVE",
        "created_at": now,
        "updated_at": now
    }