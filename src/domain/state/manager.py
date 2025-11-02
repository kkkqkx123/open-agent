"""统一状态管理器实现"""

import json
import pickle
from typing import Any, Dict, Optional
import logging
from datetime import datetime

from .interfaces import IStateManager
from ...infrastructure.graph.state import WorkflowState


logger = logging.getLogger(__name__)


class StateManager(IStateManager):
    """统一状态管理器实现"""
    
    def __init__(self, serialization_format: str = "json"):
        """初始化状态管理器
        
        Args:
            serialization_format: 序列化格式，支持 "json" 或 "pickle"
        """
        self.serialization_format = serialization_format
        self._states = {}
    
    def serialize_agent_state(self, state: WorkflowState) -> bytes:
        """序列化WorkflowState"""
        try:
            # 将WorkflowState转换为字典
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

    def deserialize_agent_state(self, data: bytes) -> WorkflowState:
        """反序列化WorkflowState"""
        try:
            if self.serialization_format == "json":
                state_dict = json.loads(data.decode('utf-8'))
            elif self.serialization_format == "pickle":
                state_dict = pickle.loads(data)
            else:
                raise ValueError(f"不支持的序列化格式: {self.serialization_format}")
            
            # 将字典转换回WorkflowState
            return self._dict_to_agent_state(state_dict)
        except Exception as e:
            logger.error(f"反序列化状态失败: {e}")
            raise

    # 重写接口方法以确保兼容性
    def serialize_state(self, state: Dict[str, Any]) -> str:
        """序列化状态（新接口）"""
        try:
            if self.serialization_format == "json":
                return json.dumps(state, ensure_ascii=False, default=self._json_serializer)
            elif self.serialization_format == "pickle":
                import base64
                pickled_data = pickle.dumps(state)
                return base64.b64encode(pickled_data).decode('utf-8')
            else:
                raise ValueError(f"不支持的序列化格式: {self.serialization_format}")
        except Exception as e:
            logger.error(f"序列化状态失败: {e}")
            raise

    def deserialize_state(self, serialized_data: str) -> Dict[str, Any]:
        """反序列化状态（新接口）"""
        try:
            if self.serialization_format == "json":
                return json.loads(serialized_data)
            elif self.serialization_format == "pickle":
                import base64
                pickled_data = base64.b64decode(serialized_data.encode('utf-8'))
                return pickle.loads(pickled_data)
            else:
                raise ValueError(f"不支持的序列化格式: {self.serialization_format}")
        except Exception as e:
            logger.error(f"反序列化状态失败: {e}")
            raise

    def validate_state(self, state: WorkflowState) -> bool:
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

    def _agent_state_to_dict(self, state: WorkflowState) -> Dict[str, Any]:
        """将WorkflowState转换为字典"""
        # 直接返回状态字典，因为WorkflowState已经是TypedDict
        return dict(state)

    def _dict_to_agent_state(self, state_dict: Dict[str, Any]) -> WorkflowState:
        """将字典转换为WorkflowState"""
        # 确保所有必需字段都存在
        default_state: WorkflowState = {
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

    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态"""
        self._states[state_id] = initial_state.copy()
        return self._states[state_id]

    def update_state(self, state_id: str, current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态"""
        # 合并更新到当前状态
        updated_state = current_state.copy()
        updated_state.update(updates)
        
        # 保存更新后的状态
        self._states[state_id] = updated_state
        return updated_state

    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态"""
        return self._states.get(state_id)

    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个状态的差异"""
        diff = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged": {}
        }
        
        # 检查在state1中但不在state2中的键
        for key in state1:
            if key not in state2:
                diff["removed"][key] = state1[key]
            elif state1[key] != state2[key]:
                diff["modified"][key] = {
                    "old": state1[key],
                    "new": state2[key]
                }
            else:
                diff["unchanged"][key] = state1[key]
        
        # 检查在state2中但不在state1中的键
        for key in state2:
            if key not in state1:
                diff["added"][key] = state2[key]
        
        return diff