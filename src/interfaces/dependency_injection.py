"""
临时依赖注入模块 - 提供向后兼容性
"""

def get_logger(name: str):
    """获取日志记录器"""
    from src.infrastructure.container.bootstrap import ContainerBootstrap
    from src.interfaces.logger import ILogger
    
    # 创建一个简单的容器实例
    container = ContainerBootstrap.create_container({})
    
    # 获取日志服务
    logger = container.get(ILogger)
    return logger