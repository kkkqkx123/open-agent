"""内存优化工具

提供工作流执行过程中的内存优化功能。
"""

import gc
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def optimize_state_memory(state: Dict[str, Any], max_messages: int = 10, max_history: int = 20) -> Dict[str, Any]:
    """优化状态对象的内存使用
    
    Args:
        state: 状态字典
        max_messages: 最大消息数量
        max_history: 最大历史记录数量
        
    Returns:
        优化后的状态字典
    """
    optimized_state = state.copy()
    
    # 限制消息历史长度
    if "workflow_messages" in optimized_state:
        messages = optimized_state["workflow_messages"]
        if len(messages) > max_messages:
            optimized_state["workflow_messages"] = messages[-max_messages:]
            logger.debug(f"限制消息历史从 {len(messages)} 到 {max_messages}")
    
    # 限制任务历史长度
    if "task_history" in optimized_state:
        history = optimized_state["task_history"]
        if len(history) > max_history:
            optimized_state["task_history"] = history[-max_history:]
            logger.debug(f"限制任务历史从 {len(history)} 到 {max_history}")
    
    # 限制工具结果历史
    if "workflow_tool_results" in optimized_state:
        tool_results = optimized_state["workflow_tool_results"]
        if len(tool_results) > max_history:
            optimized_state["workflow_tool_results"] = tool_results[-max_history:]
            logger.debug(f"限制工具结果历史从 {len(tool_results)} 到 {max_history}")
    
    # 清理临时数据
    if "temp_data" in optimized_state:
        del optimized_state["temp_data"]
        logger.debug("清理临时数据")
    
    return optimized_state


def force_garbage_collection() -> None:
    """强制执行垃圾回收"""
    try:
        collected = gc.collect()
        if collected > 0:
            logger.info(f"垃圾回收清理了 {collected} 个对象")
    except Exception as e:
        logger.warning(f"垃圾回收失败: {e}")


def check_memory_usage(threshold_mb: int = 300) -> bool:
    """检查内存使用情况
    
    Args:
        threshold_mb: 内存阈值（MB）
        
    Returns:
        是否超过阈值
    """
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > threshold_mb:
            logger.warning(f"内存使用过高: {memory_mb:.2f}MB (阈值: {threshold_mb}MB)")
            return True
        
        logger.debug(f"当前内存使用: {memory_mb:.2f}MB")
        return False
    except ImportError:
        logger.warning("psutil 未安装，无法监控内存使用")
        return False
    except Exception as e:
        logger.warning(f"内存监控失败: {e}")
        return False


def cleanup_circular_references() -> None:
    """清理循环引用"""
    try:
        # 查找并清理循环引用
        gc.collect()
        
        # 获取所有无法回收的对象
        unreachable = gc.collect()
        if unreachable > 0:
            logger.info(f"清理了 {unreachable} 个不可达对象")
    except Exception as e:
        logger.warning(f"清理循环引用失败: {e}")


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, max_messages: int = 10, max_history: int = 20, memory_threshold_mb: int = 300):
        self.max_messages = max_messages
        self.max_history = max_history
        self.memory_threshold_mb = memory_threshold_mb
        self.execution_count = 0
    
    def optimize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """优化状态"""
        self.execution_count += 1
        
        # 每执行10次检查一次内存
        if self.execution_count % 10 == 0:
            if check_memory_usage(self.memory_threshold_mb):
                force_garbage_collection()
                cleanup_circular_references()
        
        return optimize_state_memory(state, self.max_messages, self.max_history)
    
    def reset(self) -> None:
        """重置优化器"""
        self.execution_count = 0
        force_garbage_collection()