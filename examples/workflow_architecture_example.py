"""工作流架构使用示例

展示如何使用重构后的依赖注入架构。
"""

import logging
from typing import Dict, Any

# 导入容器和服务工厂
from src.services.container import get_global_container
from src.services.workflow import (
    WorkflowServiceFactory,
    create_workflow_service_factory,
    WorkflowOrchestrator,
    create_workflow_orchestrator
)

# 导入工作流相关接口和实现
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.core import IWorkflow
from src.core.workflow.config.config import GraphConfig

logger = logging.getLogger(__name__)


def setup_workflow_services():
    """设置工作流服务
    
    演示如何配置依赖注入容器和工作流服务。
    """
    # 获取全局容器
    container = get_global_container()
    
    # 创建服务工厂
    service_factory = create_workflow_service_factory(container)
    
    # 注册工作流服务
    service_factory.register_workflow_services(
        environment="development",
        config={
            "enable_debug": True,
            "max_execution_time": 300
        }
    )
    
    # 验证服务配置
    errors = service_factory.validate_service_configuration()
    if errors:
        logger.error(f"服务配置验证失败: {errors}")
        raise ValueError(f"服务配置验证失败: {errors}")
    
    logger.info("工作流服务设置完成")
    return container, service_factory


def example_workflow_creation():
    """示例：创建工作流
    
    演示如何使用依赖注入架构创建工作流。
    """
    # 设置服务
    container, service_factory = setup_workflow_services()
    
    # 获取工作流协调器
    workflow_coordinator = container.get(IWorkflowCoordinator)
    
    # 创建工作流配置
    workflow_config = {
        "name": "example_workflow",
        "description": "示例工作流",
        "nodes": {
            "start": {
                "type": "start_node",
                "name": "开始",
                "function_name": "start_function"
            },
            "process": {
                "type": "llm_node",
                "name": "处理",
                "function_name": "llm_function",
                "config": {
                    "system_prompt": "你是一个智能助手",
                    "max_tokens": 1000
                }
            },
            "end": {
                "type": "end_node",
                "name": "结束",
                "function_name": "end_function"
            }
        },
        "edges": [
            {
                "id": "edge_1",
                "from": "start",
                "to": "process",
                "type": "simple"
            },
            {
                "id": "edge_2",
                "from": "process",
                "to": "end",
                "type": "simple"
            }
        ],
        "entry_point": "start"
    }
    
    # 创建工作流配置对象
    config = GraphConfig.from_dict(workflow_config)
    
    # 创建工作流
    workflow = workflow_coordinator.create_workflow(config)
    
    logger.info(f"创建工作流成功: {workflow.name}")
    return workflow


def example_workflow_execution():
    """示例：执行工作流
    
    演示如何使用编排器执行工作流，包含业务逻辑。
    """
    # 设置服务
    container, service_factory = setup_workflow_services()
    
    # 获取工作流协调器
    workflow_coordinator = container.get(IWorkflowCoordinator)
    
    # 创建工作流编排器
    orchestrator = create_workflow_orchestrator(workflow_coordinator)
    
    # 工作流配置
    workflow_config = {
        "name": "chat_workflow",
        "description": "聊天工作流",
        "type": "chat",
        "nodes": {
            "start": {
                "type": "start_node",
                "name": "开始"
            },
            "llm": {
                "type": "llm_node",
                "name": "LLM处理",
                "config": {
                    "system_prompt": "你是一个智能助手",
                    "max_tokens": 1000
                }
            },
            "end": {
                "type": "end_node",
                "name": "结束"
            }
        },
        "edges": [
            {
                "from": "start",
                "to": "llm",
                "type": "simple"
            },
            {
                "from": "llm",
                "to": "end",
                "type": "simple"
            }
        ],
        "entry_point": "start"
    }
    
    # 业务上下文
    business_context = {
        "environment": "development",
        "user_id": "user123",
        "user_role": "user",
        "variables": {
            "session_id": "session_456",
            "locale": "zh-CN"
        }
    }
    
    # 执行工作流（包含业务逻辑）
    try:
        result = orchestrator.orchestrate_workflow_execution(
            workflow_config=workflow_config,
            business_context=business_context
        )
        
        logger.info(f"工作流执行成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        raise


def example_workflow_validation():
    """示例：验证工作流
    
    演示如何使用编排器验证工作流配置。
    """
    # 设置服务
    container, service_factory = setup_workflow_services()
    
    # 获取工作流协调器
    workflow_coordinator = container.get(IWorkflowCoordinator)
    
    # 创建工作流编排器
    orchestrator = create_workflow_orchestrator(workflow_coordinator)
    
    # 工作流配置
    workflow_config = {
        "name": "invalid_workflow",
        "description": "无效的工作流",
        "type": "admin_workflow",  # 这个类型对访客用户是受限的
        "nodes": {},  # 空节点列表
        "edges": [],
        "entry_point": "start"  # 引用不存在的节点
    }
    
    # 业务上下文（访客用户）
    business_context = {
        "environment": "development",
        "user_id": "guest123",
        "user_role": "guest",
        "resource_limits": {
            "max_nodes": 10
        }
    }
    
    # 验证工作流配置
    errors = orchestrator.validate_workflow_with_business_rules(
        workflow_config=workflow_config,
        business_context=business_context
    )
    
    if errors:
        logger.warning(f"工作流验证失败: {errors}")
    else:
        logger.info("工作流验证通过")
    
    return errors


def example_service_stats():
    """示例：获取服务统计信息
    
    演示如何获取服务配置和运行统计。
    """
    # 设置服务
    container, service_factory = setup_workflow_services()
    
    # 获取服务配置统计
    stats = service_factory.get_service_configuration_stats()
    
    logger.info("服务配置统计:")
    logger.info(f"  注册服务数量: {stats['registered_services']}")
    logger.info(f"  容器配置有效: {stats['container_valid']}")
    
    if 'workflow_registry' in stats:
        registry_stats = stats['workflow_registry']
        logger.info("工作流注册表统计:")
        logger.info(f"  节点类型: {registry_stats['node_types']}")
        logger.info(f"  边类型: {registry_stats['edge_types']}")
        logger.info(f"  节点函数: {registry_stats['node_functions']}")
        logger.info(f"  路由函数: {registry_stats['route_functions']}")
    
    return stats


def main():
    """主函数 - 运行所有示例"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("开始工作流架构示例")
    
    try:
        # 示例1：创建工作流
        logger.info("\n=== 示例1：创建工作流 ===")
        workflow = example_workflow_creation()
        
        # 示例2：执行工作流
        logger.info("\n=== 示例2：执行工作流 ===")
        result = example_workflow_execution()
        
        # 示例3：验证工作流
        logger.info("\n=== 示例3：验证工作流 ===")
        errors = example_workflow_validation()
        
        # 示例4：获取服务统计
        logger.info("\n=== 示例4：获取服务统计 ===")
        stats = example_service_stats()
        
        logger.info("\n所有示例执行完成")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise


if __name__ == "__main__":
    main()