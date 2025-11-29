"""监控触发器实现

提供各种监控功能的触发器实现。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import re

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


class UserInputPatternTrigger(MonitoringTrigger):
    """用户输入模式匹配触发器
    
    监控用户输入，匹配特定模式时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化用户输入模式匹配触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "patterns": {},  # 模式字典
            "case_sensitive": False,  # 是否区分大小写
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.EVENT, default_config)
        
        self._case_sensitive = self._config["case_sensitive"]
        self._processed_messages: List[str] = []
    
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
        
        # 获取用户消息
        messages = state.get("messages", [])
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        
        if not user_messages:
            return False
        
        # 检查最新的用户消息
        latest_user_message = user_messages[-1]
        message_content = latest_user_message.get("content", "")
        
        # 检查是否已处理过此消息
        if message_content in self._processed_messages:
            return False
        
        # 检查模式匹配
        for pattern_name in self._patterns:
            if self.match_pattern(pattern_name, message_content):
                self._processed_messages.append(message_content)
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
        
        messages = state.get("messages", [])
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        latest_user_message = user_messages[-1] if user_messages else {}
        message_content = latest_user_message.get("content", "")
        
        # 找到匹配的模式
        matched_patterns = []
        for pattern_name in self._patterns:
            if self.match_pattern(pattern_name, message_content):
                matched_patterns.append(pattern_name)
        
        return {
            "message_content": message_content,
            "matched_patterns": matched_patterns,
            "pattern_matches": {
                pattern_name: self._patterns[pattern_name].findall(message_content)
                for pattern_name in matched_patterns
            },
            "executed_at": datetime.now().isoformat(),
            "message": f"用户输入匹配模式: {', '.join(matched_patterns)}"
        }


class LLMOutputPatternTrigger(MonitoringTrigger):
    """LLM输出模式匹配触发器
    
    监控LLM输出，匹配特定模式时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化LLM输出模式匹配触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "patterns": {},  # 模式字典
            "case_sensitive": False,  # 是否区分大小写
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.EVENT, default_config)
        
        self._case_sensitive = self._config["case_sensitive"]
        self._processed_messages: List[str] = []
    
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
        
        # 获取LLM消息
        messages = state.get("messages", [])
        llm_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        
        if not llm_messages:
            return False
        
        # 检查最新的LLM消息
        latest_llm_message = llm_messages[-1]
        message_content = latest_llm_message.get("content", "")
        
        # 检查是否已处理过此消息
        if message_content in self._processed_messages:
            return False
        
        # 检查模式匹配
        for pattern_name in self._patterns:
            if self.match_pattern(pattern_name, message_content):
                self._processed_messages.append(message_content)
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
        
        messages = state.get("messages", [])
        llm_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        latest_llm_message = llm_messages[-1] if llm_messages else {}
        message_content = latest_llm_message.get("content", "")
        model = latest_llm_message.get("model", "")
        
        # 找到匹配的模式
        matched_patterns = []
        for pattern_name in self._patterns:
            if self.match_pattern(pattern_name, message_content):
                matched_patterns.append(pattern_name)
        
        return {
            "model": model,
            "message_content": message_content,
            "matched_patterns": matched_patterns,
            "pattern_matches": {
                pattern_name: self._patterns[pattern_name].findall(message_content)
                for pattern_name in matched_patterns
            },
            "executed_at": datetime.now().isoformat(),
            "message": f"LLM输出匹配模式: {', '.join(matched_patterns)}"
        }


class MemoryMonitoringTrigger(MonitoringTrigger):
    """内存监控触发器
    
    监控内存使用情况，当超过阈值时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化内存监控触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "memory_threshold_mb": 1024,  # 内存阈值（MB）
            "system_memory_threshold_percent": 90,  # 系统内存阈值（百分比）
            "check_interval": 60,  # 检查间隔（秒）
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._memory_threshold_mb = self._config["memory_threshold_mb"]
        self._system_memory_threshold_percent = self._config["system_memory_threshold_percent"]
        self._check_interval = self._config["check_interval"]
    
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
        
        # 检查内存使用情况
        memory_info = self.check_memory_usage()
        if not memory_info:
            return False
        
        # 检查是否超过阈值
        return (memory_info.process_memory_mb > self._memory_threshold_mb or
                memory_info.system_memory_percent > self._system_memory_threshold_percent)
    
    def execute(self, state: "IWorkflowState", context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        memory_info = self.check_memory_usage()
        if not memory_info:
            return {
                "error": "无法获取内存信息",
                "executed_at": datetime.now().isoformat()
            }
        
        # 确定警告类型
        warning_types = []
        if memory_info.process_memory_mb > self._memory_threshold_mb:
            warning_types.append("process_memory")
        if memory_info.system_memory_percent > self._system_memory_threshold_percent:
            warning_types.append("system_memory")
        
        return {
            "process_memory_mb": memory_info.process_memory_mb,
            "system_memory_mb": memory_info.system_memory_mb,
            "process_memory_percent": memory_info.process_memory_percent,
            "system_memory_percent": memory_info.system_memory_percent,
            "thresholds": {
                "process_memory_mb": self._memory_threshold_mb,
                "system_memory_percent": self._system_memory_threshold_percent
            },
            "warning_types": warning_types,
            "memory_trend": self._get_memory_trend(),
            "executed_at": datetime.now().isoformat(),
            "message": f"内存使用超过阈值: {', '.join(warning_types)}"
        }
    
    def _get_memory_trend(self) -> Dict[str, Any]:
        """获取内存使用趋势
        
        Returns:
            Dict[str, Any]: 内存趋势信息
        """
        history = self.get_memory_history(10)
        if len(history) < 2:
            return {"trend": "insufficient_data"}
        
        # 计算趋势
        recent = history[-5:] if len(history) >= 5 else history
        process_memory_trend = recent[-1].process_memory_mb - recent[0].process_memory_mb
        system_memory_trend = recent[-1].system_memory_percent - recent[0].system_memory_percent
        
        return {
            "trend": "increasing" if process_memory_trend > 0 else "decreasing",
            "process_memory_change_mb": process_memory_trend,
            "system_memory_change_percent": system_memory_trend,
            "sample_count": len(recent)
        }