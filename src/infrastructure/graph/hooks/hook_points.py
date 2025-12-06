"""Hook点定义

定义图执行过程中的关键Hook点。
"""

from enum import Enum

__all__ = ("HookPoint",)


class HookPoint(Enum):
    """图执行过程中的Hook点。"""
    
    # 图级别Hook
    BEFORE_COMPILE = "before_compile"
    """图编译前"""
    AFTER_COMPILE = "after_compile"
    """图编译后"""
    BEFORE_EXECUTION = "before_execution"
    """图执行前"""
    AFTER_EXECUTION = "after_execution"
    """图执行后"""
    BEFORE_DESTROY = "before_destroy"
    """图销毁前"""
    
    # 步骤级别Hook
    ON_STEP_START = "on_step_start"
    """步骤开始时"""
    ON_STEP_END = "on_step_end"
    """步骤结束时"""
    
    # 节点级别Hook
    BEFORE_NODE_EXECUTE = "before_node_execute"
    """节点执行前"""
    AFTER_NODE_EXECUTE = "after_node_execute"
    """节点执行后"""
    ON_NODE_ERROR = "on_node_error"
    """节点错误时"""
    
    # 检查点Hook
    BEFORE_CHECKPOINT = "before_checkpoint"
    """检查点保存前"""
    AFTER_CHECKPOINT = "after_checkpoint"
    """检查点保存后"""
    
    # 状态管理Hook
    BEFORE_STATE_UPDATE = "before_state_update"
    """状态更新前"""
    AFTER_STATE_UPDATE = "after_state_update"
    """状态更新后"""
    
    # 消息传递Hook
    BEFORE_MESSAGE_SEND = "before_message_send"
    """消息发送前"""
    AFTER_MESSAGE_SEND = "after_message_send"
    """消息发送后"""
    BEFORE_MESSAGE_RECEIVE = "before_message_receive"
    """消息接收前"""
    AFTER_MESSAGE_RECEIVE = "after_message_receive"
    """消息接收后"""