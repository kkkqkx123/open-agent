"""Checkpoint应用层接口定义

定义checkpoint管理器的核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


# 注意：ICheckpointManager和ICheckpointPolicy已移动到domain层
# 应用层现在只包含特定于应用层的接口（如果有的话）