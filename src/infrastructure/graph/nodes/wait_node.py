"""等待节点

负责在工作流中暂停执行，等待外部干预或超时处理。
支持多种超时处理策略和配置选项。
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from ..registry import BaseNode, NodeExecutionResult, node
from src.domain.agent.state import AgentState, AgentMessage
from src.infrastructure.graph.adapters import get_state_adapter, get_message_adapter


class TimeoutStrategy(Enum):
    """超时处理策略枚举"""
    CONTINUE_WAITING = "continue_waiting"  # 给出提示后继续等待
    CACHE_AND_EXIT = "cache_and_exit"      # 保留进度的缓存，结束任务
    LLM_CONTINUE = "llm_continue"          # 通过提示词要求LLM继续之前的任务


@dataclass
class WaitState:
    """等待状态数据"""
    start_time: float
    is_waiting: bool = True
    timeout_occurred: bool = False
    wait_message: str = ""
    cached_state: Optional[Dict[str, Any]] = None


@node("wait_node")
class WaitNode(BaseNode):
    """等待节点 - 支持超时机制和多种处理策略"""

    def __init__(self) -> None:
        """初始化等待节点"""
        self._active_waits: Dict[str, WaitState] = {}
        self._timeout_handlers: Dict[TimeoutStrategy, Callable] = {}
        self._init_timeout_handlers()

    def _init_timeout_handlers(self) -> None:
        """初始化超时处理器"""
        self._timeout_handlers = {
            TimeoutStrategy.CONTINUE_WAITING: self._handle_continue_waiting,
            TimeoutStrategy.CACHE_AND_EXIT: self._handle_cache_and_exit,
            TimeoutStrategy.LLM_CONTINUE: self._handle_llm_continue,
        }

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "wait_node"

    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行等待逻辑

        Args:
            state: 当前Agent状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 获取配置参数
        timeout_enabled = config.get("timeout_enabled", True)
        timeout_seconds = config.get("timeout_seconds", 300)  # 默认5分钟
        timeout_strategy = TimeoutStrategy(config.get("timeout_strategy", "continue_waiting"))
        wait_message = config.get("wait_message", "等待人工审核中...")
        auto_resume_key = config.get("auto_resume_key", "human_review_result")
        
        # 生成唯一的等待ID
        wait_id = f"{state.agent_id}_{int(time.time())}"
        
        # 检查是否已经有等待状态
        existing_wait = self._get_existing_wait(state)
        if existing_wait:
            # 已有等待状态，检查是否需要处理
            return self._handle_existing_wait(state, existing_wait, config)
        
        # 检查是否已经有外部输入（如人工审核结果）
        if self._has_external_input(state, auto_resume_key):
            return self._resume_from_external_input(state, config)
        
        # 创建新的等待状态
        wait_state = WaitState(
            start_time=time.time(),
            wait_message=wait_message
        )
        self._active_waits[wait_id] = wait_state
        
        # 添加等待消息到状态
        wait_msg = AgentMessage(
            content=f"⏳ {wait_message}",
            role='system'
        )
        state.messages.append(wait_msg)
        
        # 设置等待标志
        state.is_waiting = True
        state.wait_start_time = wait_state.start_time
        
        # 如果启用超时，设置超时处理
        if timeout_enabled:
            self._setup_timeout_handler(wait_id, timeout_seconds, timeout_strategy, state, config)
        
        # 返回等待结果
        return NodeExecutionResult(
            state=state,
            next_node="__wait__",  # 特殊标记，表示需要暂停
            metadata={
                "wait_id": wait_id,
                "is_waiting": True,
                "timeout_enabled": timeout_enabled,
                "timeout_seconds": timeout_seconds,
                "timeout_strategy": timeout_strategy.value,
                "wait_message": wait_message
            }
        )

    def _get_existing_wait(self, state: AgentState) -> Optional[WaitState]:
        """获取现有的等待状态"""
        if hasattr(state, 'wait_start_time') and state.wait_start_time is not None:
            for wait_state in self._active_waits.values():
                if abs(wait_state.start_time - state.wait_start_time) < 1.0:  # 1秒误差范围
                    return wait_state
        return None

    def _handle_existing_wait(self, state: AgentState, wait_state: WaitState, config: Dict[str, Any]) -> NodeExecutionResult:
        """处理现有的等待状态"""
        # 检查是否有外部输入
        auto_resume_key = config.get("auto_resume_key", "human_review_result")
        if self._has_external_input(state, auto_resume_key):
            return self._resume_from_external_input(state, config)
        
        # 检查是否超时
        timeout_seconds = config.get("timeout_seconds", 300)
        if time.time() - wait_state.start_time > timeout_seconds:
            wait_state.timeout_occurred = True
            timeout_strategy = TimeoutStrategy(config.get("timeout_strategy", "continue_waiting"))
            return self._timeout_handlers[timeout_strategy](state, wait_state, config)
        
        # 继续等待
        return NodeExecutionResult(
            state=state,
            next_node="__wait__",
            metadata={
                "is_waiting": True,
                "wait_elapsed": time.time() - wait_state.start_time
            }
        )

    def _has_external_input(self, state: AgentState, key: str) -> bool:
        """检查是否有外部输入"""
        # 首先检查直接属性
        if hasattr(state, key) and getattr(state, key) is not None:
            return True
        # 然后检查custom_fields中的动态属性
        return key in state.custom_fields and state.custom_fields[key] is not None

    def _resume_from_external_input(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """从外部输入恢复执行"""
        # 清除等待状态
        if hasattr(state, 'is_waiting'):
            state.is_waiting = False
        
        # 添加恢复消息
        auto_resume_key = config.get("auto_resume_key", "human_review_result")
        # 首先尝试从直接属性获取，然后从custom_fields获取
        if hasattr(state, auto_resume_key):
            resume_value = getattr(state, auto_resume_key)
        else:
            resume_value = state.custom_fields.get(auto_resume_key)
        
        resume_msg = AgentMessage(
            content=f"✅ 收到外部输入，恢复执行: {resume_value}",
            role='system'
        )
        state.messages.append(resume_msg)
        
        # 确定下一步
        next_node = self._determine_next_node_from_input(state, config)
        
        return NodeExecutionResult(
            state=state,
            next_node=next_node,
            metadata={
                "is_waiting": False,
                "resumed_by": auto_resume_key,
                "resume_value": resume_value
            }
        )

    def _determine_next_node_from_input(self, state: AgentState, config: Dict[str, Any]) -> str:
        """根据外部输入确定下一步节点"""
        auto_resume_key = config.get("auto_resume_key", "human_review_result")
        # 首先尝试从直接属性获取，然后从custom_fields获取
        if hasattr(state, auto_resume_key):
            resume_value = getattr(state, auto_resume_key)
        else:
            resume_value = state.custom_fields.get(auto_resume_key)
        
        # 检查配置中的路由规则
        routing_rules = config.get("routing_rules", {})
        if resume_value in routing_rules:
            return routing_rules[resume_value]
        
        # 默认路由逻辑
        if auto_resume_key == "human_review_result":
            if resume_value == "approved":
                return "final_answer"
            elif resume_value == "rejected":
                return "analyze"
            elif resume_value == "modify":
                return "modify_result"
        
        # 默认返回配置的next_node或继续
        return config.get("default_next_node", "final_answer")

    def _setup_timeout_handler(self, wait_id: str, timeout_seconds: int, strategy: TimeoutStrategy, 
                              state: AgentState, config: Dict[str, Any]) -> None:
        """设置超时处理器"""
        def timeout_handler():
            time.sleep(timeout_seconds)
            if wait_id in self._active_waits:
                wait_state = self._active_waits[wait_id]
                if not wait_state.timeout_occurred:
                    wait_state.timeout_occurred = True
                    # 这里可以添加超时通知逻辑
                    print(f"等待节点 {wait_id} 超时，策略: {strategy.value}")
        
        # 在后台线程中运行超时处理
        timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
        timeout_thread.start()

    def _handle_continue_waiting(self, state: AgentState, wait_state: WaitState, config: Dict[str, Any]) -> NodeExecutionResult:
        """处理继续等待策略"""
        # 添加超时提示消息
        timeout_msg = AgentMessage(
            content=f"⚠️ 等待超时 ({config.get('timeout_seconds', 300)}秒)，继续等待...",
            role='system'
        )
        state.messages.append(timeout_msg)
        
        # 重置等待时间
        wait_state.start_time = time.time()
        wait_state.timeout_occurred = False
        
        return NodeExecutionResult(
            state=state,
            next_node="__wait__",
            metadata={
                "is_waiting": True,
                "timeout_handled": True,
                "strategy": "continue_waiting"
            }
        )

    def _handle_cache_and_exit(self, state: AgentState, wait_state: WaitState, config: Dict[str, Any]) -> NodeExecutionResult:
        """处理缓存并退出策略"""
        # 缓存当前状态
        wait_state.cached_state = {
            "messages": [msg.__dict__ if hasattr(msg, '__dict__') else str(msg) for msg in state.messages],
            "agent_id": state.agent_id,
            "current_task": getattr(state, 'current_task', ''),
            "context": getattr(state, 'context', {}),
        }
        
        # 添加退出消息
        exit_msg = AgentMessage(
            content=f"💾 等待超时，状态已缓存，任务暂停。可稍后恢复执行。",
            role='system'
        )
        state.messages.append(exit_msg)
        
        # 清除等待状态
        if hasattr(state, 'is_waiting'):
            state.is_waiting = False
        
        return NodeExecutionResult(
            state=state,
            next_node="__exit__",  # 特殊标记，表示退出
            metadata={
                "is_waiting": False,
                "timeout_handled": True,
                "strategy": "cache_and_exit",
                "cached": True
            }
        )

    def _handle_llm_continue(self, state: AgentState, wait_state: WaitState, config: Dict[str, Any]) -> NodeExecutionResult:
        """处理LLM继续策略"""
        # 添加超时提示消息
        timeout_msg = AgentMessage(
            content=f"⚠️ 等待超时，将自动继续之前的任务。",
            role='system'
        )
        state.messages.append(timeout_msg)
        
        # 清除等待状态
        if hasattr(state, 'is_waiting'):
            state.is_waiting = False
        
        # 设置自动继续标志
        state.auto_continue = True
        state.continue_reason = "timeout"
        
        return NodeExecutionResult(
            state=state,
            next_node=config.get("continue_node", "analyze"),  # 默认回到分析节点
            metadata={
                "is_waiting": False,
                "timeout_handled": True,
                "strategy": "llm_continue",
                "auto_continue": True
            }
        )

    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "timeout_enabled": {
                    "type": "boolean",
                    "description": "是否启用超时机制",
                    "default": True
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 300,
                    "minimum": 1
                },
                "timeout_strategy": {
                    "type": "string",
                    "description": "超时处理策略",
                    "enum": ["continue_waiting", "cache_and_exit", "llm_continue"],
                    "default": "continue_waiting"
                },
                "wait_message": {
                    "type": "string",
                    "description": "等待时显示的消息",
                    "default": "等待人工审核中..."
                },
                "auto_resume_key": {
                    "type": "string",
                    "description": "自动恢复的状态键名",
                    "default": "human_review_result"
                },
                "routing_rules": {
                    "type": "object",
                    "description": "基于外部输入的路由规则",
                    "default": {}
                },
                "default_next_node": {
                    "type": "string",
                    "description": "默认的下一个节点",
                    "default": "final_answer"
                },
                "continue_node": {
                    "type": "string",
                    "description": "LLM继续策略时的目标节点",
                    "default": "analyze"
                }
            },
            "required": []
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证节点配置"""
        errors = super().validate_config(config)
        
        # 验证超时策略
        strategy = config.get("timeout_strategy", "continue_waiting")
        if strategy not in [s.value for s in TimeoutStrategy]:
            errors.append(f"无效的超时策略: {strategy}")
        
        # 验证超时时间
        timeout_seconds = config.get("timeout_seconds", 300)
        if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
            errors.append("timeout_seconds 必须是正整数")
        
        # 验证路由规则
        routing_rules = config.get("routing_rules", {})
        if not isinstance(routing_rules, dict):
            errors.append("routing_rules 必须是对象类型")
        
        return errors

    def get_cached_state(self, wait_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的状态"""
        if wait_id in self._active_waits:
            wait_state = self._active_waits[wait_id]
            return wait_state.cached_state
        return None

    def clear_wait_state(self, wait_id: str) -> bool:
        """清除等待状态"""
        if wait_id in self._active_waits:
            del self._active_waits[wait_id]
            return True
        return False

    def list_active_waits(self) -> List[str]:
        """列出所有活跃的等待ID"""
        return list(self._active_waits.keys())