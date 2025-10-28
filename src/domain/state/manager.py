"""统一状态管理器实现"""

import json
import pickle
from typing import Any, Dict, Optional
import logging
from datetime import datetime

from .interfaces import IStateManager
from ...infrastructure.graph.state import AgentState


logger = logging.getLogger(__name__)


class StateManager(IStateManager):
    """统一状态管理器实现"""
    
    def __init__(self, serialization_format: str = "json"):
        """初始化状态管理器
        
        Args:
            serialization_format: 序列化格式，支持 "json" 或 "pickle"
        """
        self.serialization_format = serialization_format
    
    def serialize_state(self, state: AgentState) -> bytes:
        """序列化状态"""
        try:
            # 将AgentState转换为字典
            state_dict = self._agent_state_to_dict(state)
            
            if self.serialization_format == "json":
                return json.dumps(state_dict, ensure_ascii=False, default=self._json_serializer).encode('utf-8')
            elif self.serialization_format == "pickle":
                return pickle.dumps(state_dict)
            else:
                raise ValueError(f"不支持的序列化格式: {self.serialization_format}")
        except Exception as e:
            logger.error(f"序列化状态失败: {e}")
            raise

    def deserialize_state(self, data: bytes) -> AgentState:
        """反序列化状态"""
        try:
            if self.serialization_format == "json":
                state_dict = json.loads(data.decode('utf-8'))
            elif self.serialization_format == "pickle":
                state_dict = pickle.loads(data)
            else:
                raise ValueError(f"不支持的序列化格式: {self.serialization_format}")
            
            # 将字典转换回AgentState
            return self._dict_to_agent_state(state_dict)
        except Exception as e:
            logger.error(f"反序列化状态失败: {e}")
            raise

    def validate_state(self, state: AgentState) -> bool:
        """验证状态完整性"""
        try:
            # 检查必要的字段是否存在
            required_fields = ["messages", "tool_results", "current_step", "max_iterations", "iteration_count"]
            for field in required_fields:
                if field not in state:
                    logger.warning(f"状态中缺少必要字段: {field}")
                    return False
            
            # 检查字段类型
            if not isinstance(state.get("messages", []), list):
                logger.warning("消息字段必须是列表类型")
                return False
            
            if not isinstance(state.get("tool_results", []), list):
                logger.warning("工具结果字段必须是列表类型")
                return False
            
            if not isinstance(state.get("max_iterations", 0), int):
                logger.warning("最大迭代次数必须是整数类型")
                return False
            
            return True
        except Exception as e:
            logger.error(f"验证状态失败: {e}")
            return False

    def serialize_state_dict(self, state: Dict[str, Any]) -> bytes:
        """序列化状态字典"""
        try:
            if self.serialization_format == "json":
                return json.dumps(state, ensure_ascii=False, default=self._json_serializer).encode('utf-8')
            elif self.serialization_format == "pickle":
                return pickle.dumps(state)
            else:
                raise ValueError(f"不支持的序列化格式: {self.serialization_format}")
        except Exception as e:
            logger.error(f"序列化状态字典失败: {e}")
            raise

    def deserialize_state_dict(self, data: bytes) -> Dict[str, Any]:
        """反序列化状态字典"""
        try:
            if self.serialization_format == "json":
                return json.loads(data.decode('utf-8'))
            elif self.serialization_format == "pickle":
                return pickle.loads(data)
            else:
                raise ValueError(f"不支持的序列化格式: {self.serialization_format}")
        except Exception as e:
            logger.error(f"反序列化状态字典失败: {e}")
            raise

    def _agent_state_to_dict(self, state: AgentState) -> Dict[str, Any]:
        """将AgentState转换为字典"""
        # 直接返回状态字典，因为AgentState已经是TypedDict
        return dict(state)

    def _dict_to_agent_state(self, state_dict: Dict[str, Any]) -> AgentState:
        """将字典转换为AgentState"""
        # 确保所有必需字段都存在
        default_state: AgentState = {
            "messages": [],
            "tool_results": [],
            "current_step": "",
            "max_iterations": 10,
            "iteration_count": 0,
            "workflow_name": "",
            "start_time": None,
            "errors": [],
            "input": "",
            "output": None,
            "tool_calls": [],
            "complete": False,
            "metadata": {}
        }
        
        # 合并默认值和实际值
        result = default_state.copy()
        for key, value in state_dict.items():
            result[key] = value
        
        return result

    def _json_serializer(self, obj):
        """JSON序列化器，处理特殊类型"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)