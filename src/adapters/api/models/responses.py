"""响应模型"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str = Field(..., description="会话ID")
    workflow_config_path: str = Field(..., description="工作流配置文件路径")
    workflow_id: str = Field(..., description="工作流ID")
    status: str = Field(..., description="会话状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    agent_config: Optional[Dict[str, Any]] = Field(None, description="Agent配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "workflow_config_path": "configs/workflows/react.yaml",
                "workflow_id": "react_20241022_174800_1f73e8",
                "status": "active",
                "created_at": "2024-10-22T17:48:00Z",
                "updated_at": "2024-10-22T17:48:30Z",
                "agent_config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                "metadata": {
                    "notes": "测试会话"
                }
            }
        }


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionResponse] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    has_next: bool = Field(..., description="是否有下一页")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "react-251022-174800-1f73e8",
                        "workflow_config_path": "configs/workflows/react.yaml",
                        "workflow_id": "react_20241022_174800_1f73e8",
                        "status": "active",
                        "created_at": "2024-10-22T17:48:00Z",
                        "updated_at": "2024-10-22T17:48:30Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "has_next": False
            }
        }


class SessionHistoryResponse(BaseModel):
    """会话历史响应"""
    session_id: str = Field(..., description="会话ID")
    history: List[Dict[str, Any]] = Field(..., description="历史记录")
    total: int = Field(..., description="总记录数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "history": [
                    {
                        "record_id": "msg_123",
                        "timestamp": "2024-10-22T17:48:00Z",
                        "record_type": "message",
                        "message_type": "user",
                        "content": "你好"
                    }
                ],
                "total": 1
            }
        }


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: Optional[str] = Field(None, description="版本号")
    config_path: Optional[str] = Field(None, description="配置文件路径")
    loaded_at: Optional[datetime] = Field(None, description="加载时间")
    last_used: Optional[datetime] = Field(None, description="最后使用时间")
    usage_count: int = Field(0, description="使用次数")
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="节点列表")
    edges: Optional[List[Dict[str, Any]]] = Field(None, description="边列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "react_20241022_174800_1f73e8",
                "name": "React工作流",
                "description": "基于React模式的工作流",
                "version": "1.0.0",
                "config_path": "configs/workflows/react.yaml",
                "loaded_at": "2024-10-22T17:48:00Z",
                "last_used": "2024-10-22T18:30:00Z",
                "usage_count": 5,
                "nodes": [
                    {
                        "id": "think",
                        "type": "llm_node",
                        "name": "思考节点"
                    }
                ],
                "edges": [
                    {
                        "from": "think",
                        "to": "act",
                        "type": "simple_edge"
                    }
                ]
            }
        }


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    workflows: List[WorkflowResponse] = Field(..., description="工作流列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    has_next: bool = Field(..., description="是否有下一页")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflows": [
                    {
                        "workflow_id": "react_20241022_174800_1f73e8",
                        "name": "React工作流",
                        "description": "基于React模式的工作流",
                        "version": "1.0.0",
                        "loaded_at": "2024-10-22T17:48:00Z",
                        "usage_count": 5
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "has_next": False
            }
        }


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    execution_id: str = Field(..., description="执行ID")
    workflow_id: str = Field(..., description="工作流ID")
    status: str = Field(..., description="执行状态")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec_123456",
                "workflow_id": "react_20241022_174800_1f73e8",
                "status": "completed",
                "started_at": "2024-10-22T17:48:00Z",
                "completed_at": "2024-10-22T17:50:30Z",
                "result": {
                    "final_answer": "这是问题的答案"
                }
            }
        }


class PerformanceMetricsResponse(BaseModel):
    """性能指标响应"""
    session_id: Optional[str] = Field(None, description="会话ID")
    avg_response_time: float = Field(..., description="平均响应时间(ms)")
    max_response_time: float = Field(..., description="最大响应时间(ms)")
    min_response_time: float = Field(..., description="最小响应时间(ms)")
    total_requests: int = Field(..., description="总请求数")
    success_rate: float = Field(..., description="成功率(%)")
    error_rate: float = Field(..., description="错误率(%)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "avg_response_time": 1200.5,
                "max_response_time": 5000.0,
                "min_response_time": 200.0,
                "total_requests": 150,
                "success_rate": 95.5,
                "error_rate": 4.5
            }
        }


class StateResponse(BaseModel):
    """状态响应"""
    state_id: str = Field(..., description="状态ID")
    state: Dict[str, Any] = Field(..., description="状态数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "state_id": "state_123456",
                "state": {
                    "messages": [{"role": "user", "content": "你好"}],
                    "tool_results": [],
                    "current_step": 0
                },
                "created_at": "2024-10-22T17:48:00Z",
                "updated_at": "2024-10-22T17:50:30Z",
                "metadata": {
                    "version": "1.0",
                    "thread_id": "thread_123"
                }
            }
        }


class StateListResponse(BaseModel):
    """状态列表响应"""
    states: List[StateResponse] = Field(..., description="状态列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    has_next: bool = Field(..., description="是否有下一页")
    
    class Config:
        json_schema_extra = {
            "example": {
                "states": [
                    {
                        "state_id": "state_123456",
                        "state": {
                            "messages": [{"role": "user", "content": "你好"}],
                            "tool_results": [],
                            "current_step": 0
                        },
                        "created_at": "2024-10-22T17:48:00Z",
                        "updated_at": "2024-10-22T17:50:30Z",
                        "metadata": {
                            "version": "1.0",
                            "thread_id": "thread_123"
                        }
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "has_next": False
            }
        }


class StateValidationResponse(BaseModel):
    """状态验证响应"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": False,
                "errors": ["缺少必需的messages字段"],
                "warnings": ["tool_results字段为空列表"]
            }
        }


class StateSnapshotResponse(BaseModel):
    """状态快照响应"""
    snapshot_id: str = Field(..., description="快照ID")
    state_id: str = Field(..., description="状态ID")
    description: str = Field(..., description="快照描述")
    created_at: datetime = Field(..., description="创建时间")
    snapshot_data: Dict[str, Any] = Field(..., description="快照数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "snapshot_id": "snapshot_123456",
                "state_id": "state_123456",
                "description": "处理用户问候语后的状态",
                "created_at": "2024-10-22T17:50:30Z",
                "snapshot_data": {
                    "messages": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}],
                    "tool_results": [],
                    "current_step": 1
                }
            }
        }


class StateSnapshotListResponse(BaseModel):
    """状态快照列表响应"""
    snapshots: List[StateSnapshotResponse] = Field(..., description="快照列表")
    total: int = Field(..., description="总数")
    state_id: str = Field(..., description="状态ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "snapshots": [
                    {
                        "snapshot_id": "snapshot_123456",
                        "state_id": "state_123456",
                        "description": "处理用户问候语后的状态",
                        "created_at": "2024-10-22T17:50:30Z",
                        "snapshot_data": {
                            "messages": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}],
                            "tool_results": [],
                            "current_step": 1
                        }
                    }
                ],
                "total": 1,
                "state_id": "state_123456"
            }
        }


class StateHistoryEntry(BaseModel):
    """状态历史条目"""
    history_id: str = Field(..., description="历史记录ID")
    thread_id: str = Field(..., description="线程ID")
    state_id: str = Field(..., description="状态ID")
    action: str = Field(..., description="操作类型")
    old_state: Dict[str, Any] = Field(..., description="旧状态")
    new_state: Dict[str, Any] = Field(..., description="新状态")
    timestamp: datetime = Field(..., description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "history_id": "history_123456",
                "thread_id": "thread_123456",
                "state_id": "state_123456",
                "action": "update",
                "old_state": {
                    "messages": [{"role": "user", "content": "你好"}],
                    "current_step": 0
                },
                "new_state": {
                    "messages": [
                        {"role": "user", "content": "你好"},
                        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
                    ],
                    "current_step": 1
                },
                "timestamp": "2024-10-22T17:50:30Z",
                "metadata": {
                    "operation": "message_processing"
                }
            }
        }


class StateHistoryResponse(BaseModel):
    """状态历史响应"""
    state_id: str = Field(..., description="状态ID")
    history: List[StateHistoryEntry] = Field(..., description="历史记录列表")
    total: int = Field(..., description="总数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "state_id": "state_123456",
                "history": [
                    {
                        "history_id": "history_123456",
                        "thread_id": "thread_123456",
                        "state_id": "state_123456",
                        "action": "update",
                        "old_state": {
                            "messages": [{"role": "user", "content": "你好"}],
                            "current_step": 0
                        },
                        "new_state": {
                            "messages": [
                                {"role": "user", "content": "你好"},
                                {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
                            ],
                            "current_step": 1
                        },
                        "timestamp": "2024-10-22T17:50:30Z",
                        "metadata": {
                            "operation": "message_processing"
                        }
                    }
                ],
                "total": 1
            }
        }


class TokenStatisticsResponse(BaseModel):
    """Token统计响应"""
    session_id: str = Field(..., description="会话ID")
    total_tokens: int = Field(..., description="总Token数")
    prompt_tokens: int = Field(..., description="输入Token数")
    completion_tokens: int = Field(..., description="输出Token数")
    model_usage: Dict[str, int] = Field(..., description="按模型分类的使用量")
    estimated_cost: float = Field(..., description="估算成本")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "total_tokens": 1500,
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "model_usage": {
                    "gpt-3.5-turbo": 1500
                },
                "estimated_cost": 0.003
            }
        }


class CostStatisticsResponse(BaseModel):
    """成本统计响应"""
    session_id: str = Field(..., description="会话ID")
    total_cost: float = Field(..., description="总成本")
    cost_by_model: Dict[str, float] = Field(..., description="按模型分类的成本")
    cost_by_time: List[Dict[str, Any]] = Field(..., description="按时间分类的成本")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "total_cost": 0.005,
                "cost_by_model": {
                    "gpt-3.5-turbo": 0.003,
                    "gpt-4": 0.002
                },
                "cost_by_time": [
                    {
                        "date": "2024-10-22",
                        "cost": 0.005
                    }
                ]
            }
        }


class ErrorStatisticsResponse(BaseModel):
    """错误统计响应"""
    session_id: Optional[str] = Field(None, description="会话ID")
    total_errors: int = Field(..., description="总错误数")
    error_by_type: Dict[str, int] = Field(..., description="按类型分类的错误")
    error_by_time: List[Dict[str, Any]] = Field(..., description="按时间分类的错误")
    recent_errors: List[Dict[str, Any]] = Field(..., description="最近的错误")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "total_errors": 2,
                "error_by_type": {
                    "APIError": 1,
                    "TimeoutError": 1
                },
                "error_by_time": [
                    {
                        "date": "2024-10-22",
                        "count": 2
                    }
                ],
                "recent_errors": [
                    {
                        "error_id": "err_123",
                        "error_type": "APIError",
                        "error_message": "API调用失败",
                        "timestamp": "2024-10-22T17:50:00Z"
                    }
                ]
            }
        }


class HistoryResponse(BaseModel):
    """历史响应"""
    session_id: str = Field(..., description="会话ID")
    records: List[Dict[str, Any]] = Field(..., description="历史记录")
    total: int = Field(..., description="总记录数")
    limit: int = Field(..., description="限制数量")
    offset: int = Field(..., description="偏移量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "records": [
                    {
                        "record_id": "msg_123",
                        "timestamp": "2024-10-22T17:48:00Z",
                        "record_type": "message",
                        "message_type": "user",
                        "content": "你好"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }


class SearchResponse(BaseModel):
    """搜索响应"""
    session_id: str = Field(..., description="会话ID")
    query: str = Field(..., description="搜索查询")
    results: List[Dict[str, Any]] = Field(..., description="搜索结果")
    total: int = Field(..., description="总结果数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "react-251022-174800-1f73e8",
                "query": "错误",
                "results": [
                    {
                        "record_id": "msg_123",
                        "timestamp": "2024-10-22T17:48:00Z",
                        "record_type": "message",
                        "content": "发生了一个错误"
                    }
                ],
                "total": 1
            }
        }


class BookmarkResponse(BaseModel):
    """书签响应"""
    bookmark_id: str = Field(..., description="书签ID")
    session_id: str = Field(..., description="会话ID")
    message_id: str = Field(..., description="消息ID")
    note: Optional[str] = Field(None, description="书签备注")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bookmark_id": "bookmark_123",
                "session_id": "react-251022-174800-1f73e8",
                "message_id": "msg_123456",
                "note": "重要的回答",
                "created_at": "2024-10-22T17:50:00Z"
            }
        }


class ConfigResponse(BaseModel):
    """配置响应"""
    key: str = Field(..., description="配置键")
    value: Any = Field(..., description="配置值")
    config_type: str = Field(..., description="配置类型")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "default_model",
                "value": "gpt-4",
                "config_type": "llm",
                "updated_at": "2024-10-22T17:50:00Z"
            }
        }


class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {
                    "id": "123"
                },
                "timestamp": "2024-10-22T17:50:00Z"
            }
        }


class ThreadResponse(BaseModel):
    """Thread响应"""
    thread_id: str = Field(..., description="Thread ID")
    graph_id: str = Field(..., description="关联的图ID")
    status: str = Field(..., description="Thread状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    branch_name: Optional[str] = Field(None, description="分支名称")

    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "thread_123456",
                "graph_id": "graph_789",
                "status": "active",
                "created_at": "2024-10-22T17:48:00Z",
                "updated_at": "2024-10-22T17:48:30Z",
                "metadata": {
                    "notes": "测试Thread"
                },
                "branch_name": "main"
            }
        }


class ThreadListResponse(BaseModel):
    """Thread列表响应"""
    threads: List[ThreadResponse] = Field(..., description="Thread列表")
    total: int = Field(..., description="总数")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

    class Config:
        json_schema_extra = {
            "example": {
                "threads": [
                    {
                        "thread_id": "thread_123456",
                        "graph_id": "graph_789",
                        "status": "active",
                        "created_at": "2024-10-22T17:48:00Z",
                        "updated_at": "2024-10-22T17:48:30Z",
                        "metadata": {
                            "notes": "测试Thread"
                        },
                        "branch_name": "main"
                    }
                ],
                "total": 1,
                "timestamp": "2024-10-22T17:50:00Z"
            }
        }


class OperationResponse(BaseModel):
    """操作响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "timestamp": "2024-10-22T17:50:00Z"
            }
        }