"""计时触发器

提供各种计时功能的触发器实现。
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .monitoring_base import MonitoringTrigger, TriggerType

from src.interfaces.state.workflow import IWorkflowState


class ToolExecutionTimingTrigger(MonitoringTrigger):
    """工具执行过程计时触发器
    
    监控工具执行过程的耗时，当执行时间超过阈值时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化工具执行计时触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "timeout_threshold": 30.0,  # 超时阈值（秒）
            "warning_threshold": 10.0,  # 警告阈值（秒）
            "monitor_all_tools": True,  # 是否监控所有工具
            "monitored_tools": [],  # 特定监控的工具列表
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._timeout_threshold = self._config["timeout_threshold"]
        self._warning_threshold = self._config["warning_threshold"]
        self._monitor_all_tools = self._config["monitor_all_tools"]
        self._monitored_tools = set(self._config["monitored_tools"])
    
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
        
        # 检查工具执行结果
        tool_results = state.get("tool_results", [])
        if not tool_results:
            return False
        
        # 检查最新的工具执行结果
        latest_result = tool_results[-1]
        tool_name = latest_result.get("tool_name", "")
        
        # 检查是否需要监控此工具
        if not self._should_monitor_tool(tool_name):
            return False
        
        # 检查是否有执行时间信息
        execution_time = latest_result.get("execution_time")
        if execution_time is None:
            # 如果没有执行时间信息，尝试从上下文中获取
            execution_time = self._get_execution_time_from_context(tool_name, context)
        
        if execution_time is None:
            return False
        
        # 检查是否超过阈值
        return execution_time >= self._timeout_threshold
    
    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        tool_results = state.get("tool_results", [])
        latest_result = tool_results[-1] if tool_results else {}
        tool_name = latest_result.get("tool_name", "")
        execution_time = latest_result.get("execution_time") or self._get_execution_time_from_context(tool_name, context)
        
        # 确定警告级别
        warning_level = "timeout" if execution_time >= self._timeout_threshold else "warning"
        
        return {
            "tool_name": tool_name,
            "execution_time": execution_time,
            "warning_level": warning_level,
            "thresholds": {
                "warning": self._warning_threshold,
                "timeout": self._timeout_threshold
            },
            "executed_at": datetime.now().isoformat(),
            "message": f"工具 {tool_name} 执行时间 {execution_time:.2f}s 超过 {warning_level} 阈值"
        }
    
    def _should_monitor_tool(self, tool_name: str) -> bool:
        """检查是否应该监控指定工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否应该监控
        """
        if self._monitor_all_tools:
            return True
        return tool_name in self._monitored_tools
    
    def _get_execution_time_from_context(self, tool_name: str, context: Dict[str, Any]) -> Optional[float]:
        """从上下文中获取工具执行时间
        
        Args:
            tool_name: 工具名称
            context: 上下文信息
            
        Returns:
            Optional[float]: 执行时间（秒）
        """
        timing_info = context.get("timing_info", {})
        tool_timing = timing_info.get(tool_name)
        
        if tool_timing:
            return tool_timing.get("duration")
        
        return None


class LLMResponseTimingTrigger(MonitoringTrigger):
    """LLM响应计时触发器
    
    监控LLM响应时间，当响应时间超过阈值时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化LLM响应计时触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "timeout_threshold": 60.0,  # 超时阈值（秒）
            "warning_threshold": 20.0,  # 警告阈值（秒）
            "monitor_all_models": True,  # 是否监控所有模型
            "monitored_models": [],  # 特定监控的模型列表
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._timeout_threshold = self._config["timeout_threshold"]
        self._warning_threshold = self._config["warning_threshold"]
        self._monitor_all_models = self._config["monitor_all_models"]
        self._monitored_models = set(self._config["monitored_models"])
    
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
        
        # 检查LLM响应
        messages = state.get("messages", [])
        if not messages:
            return False
        
        # 检查最新的消息
        latest_message = messages[-1]
        if latest_message.get("role") != "assistant":
            return False
        
        # 获取模型信息
        model = latest_message.get("model", "")
        if not self._should_monitor_model(model):
            return False
        
        # 检查响应时间
        response_time = latest_message.get("response_time")
        if response_time is None:
            # 尝试从上下文中获取
            response_time = self._get_response_time_from_context(model, context)
        
        if response_time is None:
            return False
        
        # 检查是否超过阈值
        return response_time >= self._timeout_threshold
    
    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        messages = state.get("messages", [])
        latest_message = messages[-1] if messages else {}
        model = latest_message.get("model", "")
        response_time = latest_message.get("response_time") or self._get_response_time_from_context(model, context)
        
        # 确定警告级别
        warning_level = "timeout" if response_time >= self._timeout_threshold else "warning"
        
        return {
            "model": model,
            "response_time": response_time,
            "warning_level": warning_level,
            "thresholds": {
                "warning": self._warning_threshold,
                "timeout": self._timeout_threshold
            },
            "executed_at": datetime.now().isoformat(),
            "message": f"模型 {model} 响应时间 {response_time:.2f}s 超过 {warning_level} 阈值"
        }
    
    def _should_monitor_model(self, model: str) -> bool:
        """检查是否应该监控指定模型
        
        Args:
            model: 模型名称
            
        Returns:
            bool: 是否应该监控
        """
        if self._monitor_all_models:
            return True
        return model in self._monitored_models
    
    def _get_response_time_from_context(self, model: str, context: Dict[str, Any]) -> Optional[float]:
        """从上下文中获取模型响应时间
        
        Args:
            model: 模型名称
            context: 上下文信息
            
        Returns:
            Optional[float]: 响应时间（秒）
        """
        timing_info = context.get("llm_timing_info", {})
        model_timing = timing_info.get(model)
        
        if model_timing:
            return model_timing.get("duration")
        
        return None


class WorkflowStateTimingTrigger(MonitoringTrigger):
    """工作流状态切换计时触发器
    
    监控工作流状态切换后的时间，用于检查工作流是否被阻塞。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化工作流状态计时触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "stall_threshold": 300.0,  # 停滞阈值（秒）
            "warning_threshold": 120.0,  # 警告阈值（秒）
            "monitored_states": [],  # 特定监控的状态列表，空列表表示监控所有状态
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.STATE, default_config)
        
        self._stall_threshold = self._config["stall_threshold"]
        self._warning_threshold = self._config["warning_threshold"]
        self._monitored_states = set(self._config["monitored_states"])
    
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
        
        # 检查是否需要监控此状态
        if self._monitored_states and current_state not in self._monitored_states:
            return False
        
        # 更新状态信息
        self.update_state(current_state, state.to_dict())
        
        # 检查状态持续时间
        time_since_change = self.get_time_since_last_state_change()
        if time_since_change is None:
            return False
        
        # 检查是否超过停滞阈值
        return time_since_change >= self._stall_threshold
    
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
        time_since_change = self.get_time_since_last_state_change() or 0
        
        # 确定警告级别
        warning_level = "stall" if time_since_change >= self._stall_threshold else "warning"
        
        return {
            "current_state": current_state,
            "time_in_state": time_since_change,
            "warning_level": warning_level,
            "thresholds": {
                "warning": self._warning_threshold,
                "stall": self._stall_threshold
            },
            "state_history": [
                {
                    "state": info.current_state,
                    "change_time": info.change_time.isoformat(),
                    "duration": (datetime.now() - info.change_time).total_seconds()
                }
                for info in self.get_state_history(5)
            ],
            "executed_at": datetime.now().isoformat(),
            "message": f"工作流在状态 {current_state} 停滞 {time_since_change:.2f}s 超过 {warning_level} 阈值"
        }