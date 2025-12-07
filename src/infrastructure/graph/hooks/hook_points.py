"""Hook点定义

定义图执行过程中的关键Hook点。
"""

# 从接口层导入HookPoint，保持一致性
from src.interfaces.workflow.hooks import HookPoint

__all__ = ("HookPoint",)

# 重新导出接口层的HookPoint，确保一致性
# 这样可以避免两个不同的HookPoint定义导致的冲突