"""请求模型"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    workflow_config_path: str = Field(..., description="工作流配置文件路径")
    agent_config: Optional[Dict[str, Any]] = Field(None, description="Agent配置")
    initial_state: Optional[Dict[str, Any]] = Field(None, description="初始状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_config_path": "configs/workflows/example.yaml",
                "agent_config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7
                },
                "initial_state": {
                    "messages": [],
                    "tool_results": []
                }
            }
        }


class SessionUpdateRequest(BaseModel):
    """更新会话请求"""
    status: Optional[str] = Field(None, description="会话状态")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "paused",
                "metadata": {
                    "notes": "用户暂停的会话"
                }
            }
        }


class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: Optional[str] = Field("1.0.0", description="版本号")
    config_path: Optional[str] = Field(None, description="配置文件路径")
    config_data: Optional[Dict[str, Any]] = Field(None, description="配置数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "示例工作流",
                "description": "这是一个示例工作流",
                "version": "1.0.0",
                "config_path": "configs/workflows/example.yaml",
                "config_data": {
                    "nodes": [],
                    "edges": []
                }
            }
        }


class WorkflowUpdateRequest(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = Field(None, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    version: Optional[str] = Field(None, description="版本号")
    config_data: Optional[Dict[str, Any]] = Field(None, description="配置数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "更新后的工作流名称",
                "description": "更新后的描述"
            }
        }


class WorkflowRunRequest(BaseModel):
    """运行工作流请求"""
    initial_state: Optional[Dict[str, Any]] = Field(None, description="初始状态")
    parameters: Optional[Dict[str, Any]] = Field(None, description="运行参数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "initial_state": {
                    "messages": [{"role": "user", "content": "你好"}]
                },
                "parameters": {
                    "max_iterations": 10,
                    "timeout": 300
                }
            }
        }


class HistorySearchRequest(BaseModel):
    """历史搜索请求"""
    query: str = Field(..., description="搜索关键词")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    record_types: Optional[List[str]] = Field(None, description="记录类型")
    limit: int = Field(100, ge=1, le=1000, description="结果数量限制")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "错误",
                "start_time": "2024-10-01T00:00:00Z",
                "end_time": "2024-10-31T23:59:59Z",
                "record_types": ["message", "error"],
                "limit": 50
            }
        }


class BookmarkCreateRequest(BaseModel):
    """创建书签请求"""
    message_id: str = Field(..., description="消息ID")
    note: Optional[str] = Field(None, description="书签备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123456",
                "note": "重要的回答"
            }
        }


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    key: str = Field(..., description="配置键")
    value: Any = Field(..., description="配置值")
    config_type: str = Field(..., description="配置类型")
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "default_model",
                "value": "gpt-4",
                "config_type": "llm"
            }
        }