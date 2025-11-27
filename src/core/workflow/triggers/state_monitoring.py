"""状态监控触发器

提供工作流状态监控功能的触发器实现。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .monitoring_base import MonitoringTrigger, TriggerType

from src.interfaces.state.workflow import IWorkflowState


class WorkflowStateCaptureTrigger(MonitoringTrigger):
    """工作流状态信息捕获触发器
    
    捕获工作流状态信息，用于分析和调试。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化工作流状态捕获触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "capture_interval": 60.0,  # 捕获间隔（秒）
            "capture_on_state_change": True,  # 是否在状态变更时捕获
            "include_messages": True,  # 是否包含消息
            "include_tool_results": True,  # 是否包含工具结果
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._capture_interval = self._config["capture_interval"]
        self._capture_on_state_change = self._config["capture_on_state_change"]
        self._include_messages = self._config["include_messages"]
        self._include_tool_results = self._config["include_tool_results"]
        self._last_capture_time: Optional[datetime] = None
    
    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        if not self.can_trigger():
            return False
        
        now = datetime.now()
        
        # 检查是否在状态变更时捕获
        if self._capture_on_state_change:
            current_state = state.get("current_step", "")
            if current_state != self.get_current_state():
                self.update_state(current_state, state.to_dict())
                return True
        
        # 检查是否到了定期捕获时间
        if (self._last_capture_time and 
            (now - self._last_capture_time).total_seconds() < self._capture_interval):
            return False
        
        return True
    
    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        self._last_capture_time = datetime.now()
        
        # 捕获状态信息
        captured_data = {
            "timestamp": self._last_capture_time.isoformat(),
            "current_step": state.get("current_step", ""),
            "iteration_count": state.get("iteration_count", 0),
            "workflow_id": context.get("workflow_id", ""),
        }
        
        # 包含消息
        if self._include_messages:
            messages = state.get("messages", [])
            captured_data["messages_summary"] = {
                "total_count": len(messages),
                "last_message": messages[-1] if messages else None,
                "message_types": self._analyze_message_types(messages)
            }
        
        # 包含工具结果
        if self._include_tool_results:
            tool_results = state.get("tool_results", [])
            captured_data["tool_results_summary"] = {
                "total_count": len(tool_results),
                "success_count": sum(1 for r in tool_results if r.get("success", True)),
                "error_count": sum(1 for r in tool_results if not r.get("success", True)),
                "last_result": tool_results[-1] if tool_results else None
            }
        
        # 包含内存信息
        memory_info = self.check_memory_usage()
        if memory_info:
            captured_data["memory_info"] = {
                "process_memory_mb": memory_info.process_memory_mb,
                "system_memory_percent": memory_info.system_memory_percent
            }
        
        return {
            "captured_data": captured_data,
            "executed_at": datetime.now().isoformat(),
            "message": "工作流状态信息已捕获"
        }
    
    def _analyze_message_types(self, messages: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析消息类型
        
        Args:
            messages: 消息列表
            
        Returns:
            Dict[str, int]: 消息类型统计
        """
        type_counts = {}
        for message in messages:
            role = message.get("role", "unknown")
            type_counts[role] = type_counts.get(role, 0) + 1
        return type_counts


class WorkflowStateChangeTrigger(MonitoringTrigger):
    """工作流状态变更触发器
    
    监控工作流状态变更，当状态发生特定变化时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化工作流状态变更触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "monitored_transitions": [],  # 监控的状态转换列表 [{"from": "state1", "to": "state2"}]
            "monitor_all_changes": False,  # 是否监控所有状态变更
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.STATE, default_config)
        
        self._monitored_transitions = self._config["monitored_transitions"]
        self._monitor_all_changes = self._config["monitor_all_changes"]
    
    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        if not self.can_trigger():
            return False
        
        # 获取当前状态
        current_state = state.get("current_step", "")
        if not current_state:
            return False
        
        # 获取前一个状态
        previous_state = self.get_current_state()
        
        # 如果状态没有变化，不触发
        if current_state == previous_state:
            return False
        
        # 更新状态信息
        self.update_state(current_state, state.to_dict())
        
        # 检查是否需要监控此状态转换
        if self._monitor_all_changes:
            return True
        
        # 检查特定状态转换
        for transition in self._monitored_transitions:
            from_state = transition.get("from")
            to_state = transition.get("to")
            
            # 检查是否匹配转换
            from_match = (from_state is None or from_state == previous_state)
            to_match = (to_state is None or to_state == current_state)
            
            if from_match and to_match:
                return True
        
        return False
    
    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        current_state = state.get("current_step", "")
        previous_state = self._state_info.previous_state
        
        # 查找匹配的转换
        matched_transitions = []
        for transition in self._monitored_transitions:
            from_state = transition.get("from")
            to_state = transition.get("to")
            
            from_match = (from_state is None or from_state == previous_state)
            to_match = (to_state is None or to_state == current_state)
            
            if from_match and to_match:
                matched_transitions.append(transition)
        
        return {
            "previous_state": previous_state,
            "current_state": current_state,
            "matched_transitions": matched_transitions,
            "state_data": self._state_info.state_data,
            "transition_time": self._state_info.change_time.isoformat(),
            "executed_at": datetime.now().isoformat(),
            "message": f"工作流状态从 {previous_state} 变更为 {current_state}"
        }


class WorkflowErrorStateTrigger(MonitoringTrigger):
    """工作流错误状态触发器
    
    监控工作流错误状态，当出现错误时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化工作流错误状态触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "error_threshold": 1,  # 错误阈值
            "monitor_tool_errors": True,  # 是否监控工具错误
            "monitor_llm_errors": True,  # 是否监控LLM错误
            "monitor_system_errors": True,  # 是否监控系统错误
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._error_threshold = self._config["error_threshold"]
        self._monitor_tool_errors = self._config["monitor_tool_errors"]
        self._monitor_llm_errors = self._config["monitor_llm_errors"]
        self._monitor_system_errors = self._config["monitor_system_errors"]
    
    def evaluate(self, state: "IWorkflowState", context: Dict[str, Any]) -> bool:
        """评估是否应该触发
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        if not self.can_trigger():
            return False
        
        error_count = 0
        
        # 检查工具错误
        if self._monitor_tool_errors:
            tool_results = state.get("tool_results", [])
            error_count += sum(1 for result in tool_results if not result.get("success", True))
        
        # 检查LLM错误
        if self._monitor_llm_errors:
            messages = state.get("messages", [])
            error_count += sum(1 for msg in messages if msg.get("error"))
        
        # 检查系统错误
        if self._monitor_system_errors:
            system_errors = state.get("system_errors", [])
            error_count += len(system_errors)
        
        return error_count >= self._error_threshold
    
    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        error_summary = {
            "tool_errors": [],
            "llm_errors": [],
            "system_errors": []
        }
        
        # 收集工具错误
        if self._monitor_tool_errors:
            tool_results = state.get("tool_results", [])
            for result in tool_results:
                if not result.get("success", True):
                    error_summary["tool_errors"].append({
                        "tool_name": result.get("tool_name", "unknown"),
                        "error": result.get("error", "Unknown error"),
                        "timestamp": result.get("timestamp", datetime.now().isoformat())
                    })
        
        # 收集LLM错误
        if self._monitor_llm_errors:
            messages = state.get("messages", [])
            for msg in messages:
                if msg.get("error"):
                    error_summary["llm_errors"].append({
                        "model": msg.get("model", "unknown"),
                        "error": msg.get("error", "Unknown error"),
                        "timestamp": msg.get("timestamp", datetime.now().isoformat())
                    })
        
        # 收集系统错误
        if self._monitor_system_errors:
            system_errors = state.get("system_errors", [])
            for error in system_errors:
                error_summary["system_errors"].append({
                    "error_type": error.get("type", "unknown"),
                    "error": error.get("message", "Unknown error"),
                    "timestamp": error.get("timestamp", datetime.now().isoformat())
                })
        
        total_errors = (len(error_summary["tool_errors"]) + 
                       len(error_summary["llm_errors"]) + 
                       len(error_summary["system_errors"]))
        
        return {
            "error_summary": error_summary,
            "total_errors": total_errors,
            "error_threshold": self._error_threshold,
            "executed_at": datetime.now().isoformat(),
            "message": f"检测到 {total_errors} 个错误，超过阈值 {self._error_threshold}"
        }