"""
容器引导器单元测试
"""

import pytest
from src.infrastructure.container.bootstrap import ContainerBootstrap
from src.interfaces.container.core import IDependencyContainer

def test_create_container():
    """测试创建容器"""
    config = {
        "log_level": "INFO",
        "database_url": "postgresql://localhost:5432/app"
    }
    
    # 创建容器
    container = ContainerBootstrap.create_container(config)
    
    # 验证容器类型
    assert container is not None
    assert isinstance(container, IDependencyContainer)
    
    # 验证容器有基本服务
    assert container.has_service(type)  # 容器本身应该可以获取

def test_create_container_with_empty_config():
    """测试使用空配置创建容器"""
    config = {}
    
    # 创建容器
    container = ContainerBootstrap.create_container(config)
    
    # 验证容器类型
    assert container is not None
    assert isinstance(container, IDependencyContainer)