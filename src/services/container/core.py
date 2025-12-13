"""
临时容器核心模块 - 提供向后兼容性
"""

from src.infrastructure.container.bootstrap import ContainerBootstrap
from src.interfaces.container import IDependencyContainer

# 创建全局容器实例
_container = ContainerBootstrap.create_container({})

def get_container() -> IDependencyContainer:
    """获取全局容器实例"""
    return _container

# 创建容器实例
container = get_container()