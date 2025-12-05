"""日志服务实现 - 重构后专注于业务逻辑"""

import threading
from typing import Any, Dict, List, Optional

from ...interfaces.logger import ILogger, IBaseHandler, ILogRedactor, ILoggerFactory, LogLevel


class LoggerService(ILogger):
    """日志服务实现 - 纯业务逻辑层
    
    重构后的LoggerService专注于业务逻辑，基础设施实现委托给注入的组件。
    """

    def __init__(
        self,
        name: str,
        infrastructure_logger: ILogger,
        config: Optional[Dict[str, Any]] = None,
    ):
        """初始化日志服务

        Args:
            name: 日志记录器名称
            infrastructure_logger: 基础设施层日志记录器
            config: 配置
        """
        self.name = name
        self._infra_logger = infrastructure_logger
        self._config = config or {}
        self._lock = threading.RLock()
        
        # 业务逻辑相关的配置
        self._enable_audit = self._config.get("enable_audit", False)
        self._audit_keywords = self._config.get("audit_keywords", ["login", "logout", "auth"])
        self._enable_business_filter = self._config.get("enable_business_filter", False)
        self._business_rules = self._config.get("business_rules", [])

    def debug(self, message: str, **kwargs: Any) -> None:
        """记录调试日志"""
        if self._should_log(LogLevel.DEBUG, message, **kwargs):
            self._infra_logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """记录信息日志"""
        if self._should_log(LogLevel.INFO, message, **kwargs):
            # 业务逻辑：审计检查
            if self._enable_audit and self._should_audit(message):
                self._audit_log(message, **kwargs)
            
            self._infra_logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """记录警告日志"""
        if self._should_log(LogLevel.WARNING, message, **kwargs):
            self._infra_logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """记录错误日志"""
        if self._should_log(LogLevel.ERROR, message, **kwargs):
            # 业务逻辑：错误分类和增强
            enhanced_kwargs = self._enhance_error_log(message, **kwargs)
            self._infra_logger.error(message, **enhanced_kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """记录严重错误日志"""
        if self._should_log(LogLevel.CRITICAL, message, **kwargs):
            # 业务逻辑：关键错误需要特殊处理
            enhanced_kwargs = self._enhance_critical_log(message, **kwargs)
            self._infra_logger.critical(message, **enhanced_kwargs)

    def set_level(self, level: LogLevel) -> None:
        """设置日志级别"""
        with self._lock:
            self._infra_logger.set_level(level)

    def add_handler(self, handler: IBaseHandler) -> None:
        """添加日志处理器"""
        with self._lock:
            self._infra_logger.add_handler(handler)

    def remove_handler(self, handler: IBaseHandler) -> None:
        """移除日志处理器"""
        with self._lock:
            self._infra_logger.remove_handler(handler)

    def set_redactor(self, redactor: ILogRedactor) -> None:
        """设置日志脱敏器"""
        with self._lock:
            self._infra_logger.set_redactor(redactor)

    def _should_log(self, level: LogLevel, message: str, **kwargs: Any) -> bool:
        """业务逻辑：判断是否应该记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外参数
            
        Returns:
            是否应该记录
        """
        # 基础级别检查委托给基础设施层
        # 这里可以添加业务级别的过滤逻辑
        
        if not self._enable_business_filter:
            return True
        
        # 业务规则过滤
        for rule in self._business_rules:
            if not self._apply_business_rule(rule, level, message, **kwargs):
                return False
        
        return True

    def _should_audit(self, message: str) -> bool:
        """业务逻辑：判断是否需要审计
        
        Args:
            message: 日志消息
            
        Returns:
            是否需要审计
        """
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self._audit_keywords)

    def _audit_log(self, message: str, **kwargs: Any) -> None:
        """业务逻辑：记录审计日志
        
        Args:
            message: 原始消息
            **kwargs: 额外参数
        """
        audit_record = {
            "audit_type": "business_operation",
            "original_message": message,
            "timestamp": kwargs.get("timestamp"),
            "user_id": kwargs.get("user_id"),
            "session_id": kwargs.get("session_id"),
            "ip_address": kwargs.get("ip_address"),
        }
        
        # 发送到专门的审计日志
        self._infra_logger.info(f"[AUDIT] {message}", **audit_record)

    def _enhance_error_log(self, message: str, **kwargs: Any) -> Dict[str, Any]:
        """业务逻辑：增强错误日志
        
        Args:
            message: 错误消息
            **kwargs: 额外参数
            
        Returns:
            增强后的参数
        """
        enhanced = kwargs.copy()
        
        # 错误分类
        if "database" in message.lower():
            enhanced["error_category"] = "database"
        elif "network" in message.lower():
            enhanced["error_category"] = "network"
        elif "auth" in message.lower():
            enhanced["error_category"] = "authentication"
        else:
            enhanced["error_category"] = "general"
        
        # 添加业务上下文
        enhanced["business_context"] = {
            "service": self.name,
            "environment": self._config.get("environment", "unknown"),
        }
        
        return enhanced

    def _enhance_critical_log(self, message: str, **kwargs: Any) -> Dict[str, Any]:
        """业务逻辑：增强关键错误日志
        
        Args:
            message: 错误消息
            **kwargs: 额外参数
            
        Returns:
            增强后的参数
        """
        enhanced = self._enhance_error_log(message, **kwargs)
        
        # 关键错误的特殊处理
        enhanced["severity"] = "critical"
        enhanced["requires_immediate_attention"] = True
        enhanced["escalation_level"] = self._determine_escalation_level(message, **kwargs)
        
        return enhanced

    def _apply_business_rule(
        self, 
        rule: Dict[str, Any], 
        level: LogLevel, 
        message: str, 
        **kwargs: Any
    ) -> bool:
        """应用业务规则
        
        Args:
            rule: 业务规则
            level: 日志级别
            message: 日志消息
            **kwargs: 额外参数
            
        Returns:
            是否通过规则
        """
        rule_type = rule.get("type")
        
        if rule_type == "level_filter":
            min_level = LogLevel[rule.get("min_level", "DEBUG")]
            return level.value >= min_level.value
        
        elif rule_type == "message_filter":
            keywords = rule.get("keywords", [])
            message_lower = message.lower()
            return any(keyword in message_lower for keyword in keywords)
        
        elif rule_type == "context_filter":
            context_key = rule.get("context_key")
            expected_value = rule.get("expected_value")
            if context_key is not None:
                return kwargs.get(context_key) == expected_value
            return True
        
        return True

    def _determine_escalation_level(self, message: str, **kwargs: Any) -> str:
        """确定升级级别
        
        Args:
            message: 错误消息
            **kwargs: 额外参数
            
        Returns:
            升级级别
        """
        if "security" in message.lower() or "breach" in message.lower():
            return "immediate"
        elif "data_loss" in message.lower():
            return "high"
        elif "service_down" in message.lower():
            return "medium"
        else:
            return "low"

    def get_business_metrics(self) -> Dict[str, Any]:
        """获取业务指标
        
        Returns:
            业务指标字典
        """
        return {
            "audit_enabled": self._enable_audit,
            "business_filter_enabled": self._enable_business_filter,
            "business_rules_count": len(self._business_rules),
            "service_name": self.name,
        }

    def update_business_config(self, config: Dict[str, Any]) -> None:
        """更新业务配置
        
        Args:
            config: 新的业务配置
        """
        with self._lock:
            self._config.update(config)
            self._enable_audit = config.get("enable_audit", self._enable_audit)
            self._audit_keywords = config.get("audit_keywords", self._audit_keywords)
            self._enable_business_filter = config.get("enable_business_filter", self._enable_business_filter)
            self._business_rules = config.get("business_rules", self._business_rules)


# 便捷函数，通过依赖注入创建
def create_logger_service(
    name: str,
    infrastructure_logger: Optional[ILogger] = None,
    config: Optional[Dict[str, Any]] = None,
) -> LoggerService:
    """创建日志服务的便捷函数
    
    注意：此函数主要用于测试和特殊情况，推荐通过依赖注入容器获取LoggerService。
    
    Args:
        name: 日志记录器名称
        infrastructure_logger: 基础设施层日志记录器（可选，如果未提供则创建简单实现）
        config: 配置
        
    Returns:
        日志服务实例
    """
    if infrastructure_logger is None:
        # 创建简单的基础设施层日志记录器用于测试
        class SimpleInfraLogger(ILogger):
            def __init__(self, name: str):
                self.name = name
                
            def debug(self, message: str, **kwargs: Any) -> None:
                print(f"[DEBUG] {message}")
                
            def info(self, message: str, **kwargs: Any) -> None:
                print(f"[INFO] {message}")
                
            def warning(self, message: str, **kwargs: Any) -> None:
                print(f"[WARNING] {message}")
                
            def error(self, message: str, **kwargs: Any) -> None:
                print(f"[ERROR] {message}")
                
            def critical(self, message: str, **kwargs: Any) -> None:
                print(f"[CRITICAL] {message}")
                
            def set_level(self, level: LogLevel) -> None:
                pass
                
            def add_handler(self, handler: IBaseHandler) -> None:
                pass
                
            def remove_handler(self, handler: IBaseHandler) -> None:
                pass
                
            def set_redactor(self, redactor: ILogRedactor) -> None:
                pass
        
        infrastructure_logger = SimpleInfraLogger(name)
    
    return LoggerService(name, infrastructure_logger, config)