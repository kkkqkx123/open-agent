"""模式匹配触发器

提供各种模式匹配功能的触发器实现。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .monitoring_base import MonitoringTrigger, TriggerType

from src.interfaces.state.workflow import IWorkflowState


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


class ToolOutputPatternTrigger(MonitoringTrigger):
    """工具输出模式匹配触发器
    
    监控工具输出，匹配特定模式时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化工具输出模式匹配触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "patterns": {},  # 模式字典
            "monitored_tools": [],  # 监控的工具列表，空列表表示监控所有工具
            "case_sensitive": False,  # 是否区分大小写
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.EVENT, default_config)
        
        self._case_sensitive = self._config["case_sensitive"]
        self._monitored_tools = set(self._config["monitored_tools"])
        self._processed_results: List[str] = []
    
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
        
        # 获取工具结果
        tool_results = state.get("tool_results", [])
        if not tool_results:
            return False
        
        # 检查最新的工具结果
        latest_result = tool_results[-1]
        tool_name = latest_result.get("tool_name", "")
        
        # 检查是否需要监控此工具
        if self._monitored_tools and tool_name not in self._monitored_tools:
            return False
        
        # 获取工具输出
        output_data = latest_result.get("output", "")
        if not output_data:
            return False
        
        # 将输出转换为字符串
        output_str = str(output_data)
        
        # 检查是否已处理过此输出
        result_key = f"{tool_name}:{output_str}"
        if result_key in self._processed_results:
            return False
        
        # 检查模式匹配
        for pattern_name in self._patterns:
            if self.match_pattern(pattern_name, output_str):
                self._processed_results.append(result_key)
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
        
        tool_results = state.get("tool_results", [])
        latest_result = tool_results[-1] if tool_results else {}
        tool_name = latest_result.get("tool_name", "")
        output_data = latest_result.get("output", "")
        output_str = str(output_data)
        
        # 找到匹配的模式
        matched_patterns = []
        for pattern_name in self._patterns:
            if self.match_pattern(pattern_name, output_str):
                matched_patterns.append(pattern_name)
        
        return {
            "tool_name": tool_name,
            "output_data": output_str,
            "matched_patterns": matched_patterns,
            "pattern_matches": {
                pattern_name: self._patterns[pattern_name].findall(output_str)
                for pattern_name in matched_patterns
            },
            "executed_at": datetime.now().isoformat(),
            "message": f"工具 {tool_name} 输出匹配模式: {', '.join(matched_patterns)}"
        }


class StatePatternTrigger(MonitoringTrigger):
    """状态模式匹配触发器
    
    监控工作流状态，匹配特定模式时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化状态模式匹配触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "state_patterns": {},  # 状态模式字典
            "data_patterns": {},  # 数据模式字典
            "case_sensitive": False,  # 是否区分大小写
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.STATE, default_config)
        
        self._case_sensitive = self._config["case_sensitive"]
        self._state_patterns = self._config["state_patterns"]
        self._data_patterns = self._config["data_patterns"]
        self._processed_states: List[str] = []
    
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
        
        # 检查是否已处理过此状态
        state_key = f"{current_state}:{hash(str(state))}"
        if state_key in self._processed_states:
            return False
        
        # 检查状态模式匹配
        for pattern_name, pattern in self._state_patterns.items():
            if self._match_text(pattern, current_state):
                self._processed_states.append(state_key)
                return True
        
        # 检查数据模式匹配
        for pattern_name, pattern in self._data_patterns.items():
            if self._match_state_data(pattern, state):
                self._processed_states.append(state_key)
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
        
        # 找到匹配的状态模式
        matched_state_patterns = []
        for pattern_name, pattern in self._state_patterns.items():
            if self._match_text(pattern, current_state):
                matched_state_patterns.append(pattern_name)
        
        # 找到匹配的数据模式
        matched_data_patterns = []
        for pattern_name, pattern in self._data_patterns.items():
            if self._match_state_data(pattern, state):
                matched_data_patterns.append(pattern_name)
        
        return {
            "current_state": current_state,
            "matched_state_patterns": matched_state_patterns,
            "matched_data_patterns": matched_data_patterns,
            "state_data": {
                key: state.get(key) for key in ["messages", "tool_results", "iteration_count"]
            },
            "executed_at": datetime.now().isoformat(),
            "message": f"状态 {current_state} 匹配模式"
        }
    
    def _match_text(self, pattern: str, text: str) -> bool:
        """匹配文本模式
        
        Args:
            pattern: 模式字符串
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        if not self._case_sensitive:
            pattern = pattern.lower()
            text = text.lower()
        
        return pattern in text
    
    def _match_state_data(self, pattern: str, state: "IWorkflowState") -> bool:
        """匹配状态数据模式
        
        Args:
            pattern: 模式字符串
            state: 工作流状态
            
        Returns:
            bool: 是否匹配
        """
        # 简单的状态数据匹配，可以根据需要扩展
        state_str = str(state)
        if not self._case_sensitive:
            pattern = pattern.lower()
            state_str = state_str.lower()
        
        return pattern in state_str