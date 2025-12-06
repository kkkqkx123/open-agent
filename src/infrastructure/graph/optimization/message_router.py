"""消息路由器

提供消息路由和分发功能。
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Union

from ..messaging.message_processor import Message, MessageFilter
from ..types import errors


class RouteRule:
    """路由规则"""
    
    def __init__(
        self,
        name: str,
        condition: Union[str, Callable[[Message], bool]],
        targets: Union[str, Sequence[str]],
        priority: int = 50,
    ) -> None:
        """初始化路由规则
        
        Args:
            name: 规则名称
            condition: 路由条件，可以是字符串表达式或可调用对象
            targets: 目标节点或节点列表
            priority: 优先级，数值越大优先级越高
        """
        self.name = name
        self.condition = condition
        self.targets = [targets] if isinstance(targets, str) else list(targets)
        self.priority = priority
    
    def matches(self, message: Message) -> bool:
        """检查消息是否匹配此规则
        
        Args:
            message: 消息
            
        Returns:
            是否匹配
        """
        if isinstance(self.condition, str):
            return self._evaluate_expression(message)
        else:
            return self.condition(message)
    
    def _evaluate_expression(self, message: Message) -> bool:
        """评估字符串表达式
        
        Args:
            message: 消息
            
        Returns:
            评估结果
        """
        # 简单的表达式评估，支持消息属性访问
        # 例如: "message.message_type == 'command' and message.sender == 'user'"
        
        # 创建安全的评估环境
        safe_dict = {
            "message": message,
            "type": type,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "len": len,
            "re": re,
        }
        
        try:
            # self.condition 必须是字符串，因为这个方法只在 isinstance(self.condition, str) 时被调用
            condition_str: str = self.condition  # type: ignore[assignment]
            return eval(condition_str, {"__builtins__": {}}, safe_dict)
        except Exception:
            return False


class MessageTypeRule(RouteRule):
    """消息类型路由规则"""
    
    def __init__(
        self,
        message_types: Union[str, Sequence[str]],
        targets: Union[str, Sequence[str]],
        priority: int = 50,
    ) -> None:
        """初始化消息类型路由规则
        
        Args:
            message_types: 消息类型或类型列表
            targets: 目标节点或节点列表
            priority: 优先级
        """
        if isinstance(message_types, str):
            condition = lambda msg: msg.message_type == message_types
        else:
            types_set = set(message_types)
            condition = lambda msg: msg.message_type in types_set
        
        super().__init__(
            name=f"message_type_{'_'.join(message_types) if isinstance(message_types, list) else message_types}",
            condition=condition,
            targets=targets,
            priority=priority,
        )


class SenderRule(RouteRule):
    """发送者路由规则"""
    
    def __init__(
        self,
        senders: Union[str, Sequence[str]],
        targets: Union[str, Sequence[str]],
        priority: int = 50,
    ) -> None:
        """初始化发送者路由规则
        
        Args:
            senders: 发送者或发送者列表
            targets: 目标节点或节点列表
            priority: 优先级
        """
        if isinstance(senders, str):
            condition = lambda msg: msg.sender == senders
        else:
            senders_set = set(senders)
            condition = lambda msg: msg.sender in senders_set
        
        super().__init__(
            name=f"sender_{'_'.join(senders) if isinstance(senders, list) else senders}",
            condition=condition,
            targets=targets,
            priority=priority,
        )


class RecipientRule(RouteRule):
    """接收者路由规则"""
    
    def __init__(
        self,
        recipients: Union[str, Sequence[str]],
        targets: Union[str, Sequence[str]],
        priority: int = 50,
    ) -> None:
        """初始化接收者路由规则
        
        Args:
            recipients: 接收者或接收者列表
            targets: 目标节点或节点列表
            priority: 优先级
        """
        if isinstance(recipients, str):
            condition = lambda msg: recipients in msg.recipients
        else:
            recipients_set = set(recipients)
            condition = lambda msg: any(r in msg.recipients for r in recipients_set)
        
        super().__init__(
            name=f"recipient_{'_'.join(recipients) if isinstance(recipients, list) else recipients}",
            condition=condition,
            targets=targets,
            priority=priority,
        )


class MetadataRule(RouteRule):
    """元数据路由规则"""
    
    def __init__(
        self,
        key: str,
        value: Any,
        targets: Union[str, Sequence[str]],
        priority: int = 50,
    ) -> None:
        """初始化元数据路由规则
        
        Args:
            key: 元数据键
            value: 元数据值
            targets: 目标节点或节点列表
            priority: 优先级
        """
        condition = lambda msg: msg.metadata.get(key) == value
        
        super().__init__(
            name=f"metadata_{key}_{value}",
            condition=condition,
            targets=targets,
            priority=priority,
        )


class MessageRouter:
    """消息路由器
    
    提供消息路由和分发功能。
    """
    
    def __init__(self) -> None:
        """初始化消息路由器"""
        self.routing_rules: List[RouteRule] = []
        self.filters: List[MessageFilter] = []
        self.default_targets: List[str] = []
        self.enable_fallback: bool = True
    
    def add_rule(self, rule: RouteRule) -> None:
        """添加路由规则
        
        Args:
            rule: 路由规则
        """
        self.routing_rules.append(rule)
        # 按优先级排序
        self.routing_rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_filter(self, filter_obj: MessageFilter) -> None:
        """添加消息过滤器
        
        Args:
            filter_obj: 消息过滤器
        """
        self.filters.append(filter_obj)
    
    def set_default_targets(self, targets: Union[str, Sequence[str]]) -> None:
        """设置默认目标
        
        Args:
            targets: 默认目标节点或节点列表
        """
        self.default_targets = [targets] if isinstance(targets, str) else list(targets)
    
    def enable_fallback_routing(self, enable: bool = True) -> None:
        """启用或禁用回退路由
        
        Args:
            enable: 是否启用回退路由
        """
        self.enable_fallback = enable
    
    def route_message(self, message: Message) -> List[str]:
        """路由消息
        
        Args:
            message: 消息
            
        Returns:
            目标节点列表
        """
        # 应用过滤器
        for filter_obj in self.filters:
            if not filter_obj.filter(message):
                return []
        
        # 查找匹配的路由规则
        for rule in self.routing_rules:
            if rule.matches(message):
                return rule.targets.copy()
        
        # 如果没有匹配的规则，使用默认目标
        if self.enable_fallback and self.default_targets:
            return self.default_targets.copy()
        
        return []
    
    def route_messages(self, messages: Sequence[Message]) -> Dict[str, List[str]]:
        """批量路由消息
        
        Args:
            messages: 消息列表
            
        Returns:
            消息ID到目标节点列表的映射
        """
        routing_result = {}
        for message in messages:
            targets = self.route_message(message)
            routing_result[message.id] = targets
        return routing_result
    
    def get_matching_rules(self, message: Message) -> List[RouteRule]:
        """获取匹配的规则
        
        Args:
            message: 消息
            
        Returns:
            匹配的规则列表
        """
        matching_rules = []
        for rule in self.routing_rules:
            if rule.matches(message):
                matching_rules.append(rule)
        return matching_rules
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除路由规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            是否成功移除
        """
        for i, rule in enumerate(self.routing_rules):
            if rule.name == rule_name:
                del self.routing_rules[i]
                return True
        return False
    
    def clear_rules(self) -> None:
        """清空所有路由规则"""
        self.routing_rules.clear()
    
    def clear_filters(self) -> None:
        """清空所有过滤器"""
        self.filters.clear()
    
    def get_rule_names(self) -> List[str]:
        """获取所有规则名称
        
        Returns:
            规则名称列表
        """
        return [rule.name for rule in self.routing_rules]
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息
        
        Returns:
            路由统计信息
        """
        return {
            "total_rules": len(self.routing_rules),
            "total_filters": len(self.filters),
            "default_targets": self.default_targets.copy(),
            "fallback_enabled": self.enable_fallback,
            "rule_priorities": {rule.name: rule.priority for rule in self.routing_rules},
        }