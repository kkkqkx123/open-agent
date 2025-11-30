"""错误处理框架使用示例"""

import sys
import os
import time
from typing import Any, Dict, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.common.error_management import (
    ErrorHandlingRegistry,
    ErrorCategory,
    ErrorSeverity,
    BaseErrorHandler,
    operation_with_retry,
    operation_with_fallback,
    safe_execution,
    register_error_handler,
    handle_error
)
from src.core.common.exceptions import ConfigError, StorageError


# 示例1：自定义错误处理器
class ConfigErrorHandler(BaseErrorHandler):
    """配置错误处理器"""
    
    def __init__(self):
        super().__init__(ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH)
    
    def can_handle(self, error: Exception) -> bool:
        """只处理配置相关的错误"""
        return isinstance(error, ConfigError)
    
    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """处理配置错误"""
        print(f"配置错误处理: {error}")
        # 这里可以实现具体的错误恢复逻辑
        # 例如：重新加载配置、使用默认配置等


class StorageErrorHandler(BaseErrorHandler):
    """存储错误处理器"""
    
    def __init__(self):
        super().__init__(ErrorCategory.STORAGE, ErrorSeverity.HIGH)
    
    def can_handle(self, error: Exception) -> bool:
        """只处理存储相关的错误"""
        return isinstance(error, StorageError)
    
    def handle(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """处理存储错误"""
        print(f"存储错误处理: {error}")
        # 这里可以实现具体的错误恢复逻辑
        # 例如：切换到备用存储、重试操作等


# 示例2：使用标准错误处理模式
def unreliable_operation() -> str:
    """不可靠的操作（模拟失败）"""
    if time.time() % 2 == 0:
        raise IOError("模拟IO错误")
    return "操作成功"


def fallback_operation() -> str:
    """降级操作"""
    return "降级操作成功"


def validation_operation() -> str:
    """需要验证的操作"""
    # 模拟验证失败
    raise ValueError("验证失败")


def main():
    """主演示函数"""
    print("=== 错误处理框架演示 ===")
    
    # 1. 注册错误处理器
    print("\n1. 注册错误处理器")
    config_handler = ConfigErrorHandler()
    storage_handler = StorageErrorHandler()
    
    register_error_handler(ConfigError, config_handler)
    register_error_handler(StorageError, storage_handler)
    
    # 2. 使用标准错误处理模式
    print("\n2. 使用带重试的操作模式")
    try:
        result = operation_with_retry(
            unreliable_operation,
            max_retries=3,
            backoff_factor=1.5
        )
        print(f"重试操作结果: {result}")
    except Exception as e:
        print(f"重试操作失败: {e}")
    
    print("\n3. 使用带降级的操作模式")
    try:
        result = operation_with_fallback(
            unreliable_operation,
            fallback_operation
        )
        print(f"降级操作结果: {result}")
    except Exception as e:
        print(f"降级操作失败: {e}")
    
    print("\n4. 使用安全执行模式")
    try:
        result = safe_execution(
            validation_operation,
            context={"operation": "validation_test"}
        )
        print(f"安全执行结果: {result}")
    except Exception as e:
        print(f"安全执行失败: {e}")
    
    # 3. 使用统一错误处理
    print("\n5. 使用统一错误处理")
    try:
        # 模拟配置错误
        raise ConfigError("配置文件不存在", "/path/to/config.yaml")
    except Exception as e:
        handle_error(e, context={"module": "config_loader"})
    
    try:
        # 模拟存储错误
        raise StorageError("数据库连接失败")
    except Exception as e:
        handle_error(e, context={"module": "storage_manager"})
    
    # 4. 获取注册表实例并查看状态
    print("\n6. 查看错误处理注册表状态")
    registry = ErrorHandlingRegistry()
    print(f"已注册处理器数量: {len(registry.handlers)}")
    print(f"已注册恢复策略数量: {len(registry.recovery_strategies)}")
    print(f"已注册错误映射数量: {len(registry.error_mappings)}")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()