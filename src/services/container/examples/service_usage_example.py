"""
服务层使用容器的示例

展示如何在服务层中使用新的依赖注入容器架构。
"""

from typing import Dict, Any, Optional
from src.infrastructure.container.bootstrap import ContainerBootstrap
from src.interfaces.logger import ILogger
from src.interfaces.config import IConfigLoader
from src.interfaces.workflow import IWorkflowService
from src.interfaces.storage import IStorageService
from src.interfaces.llm import ILLMService
from src.interfaces.sessions import ISessionService
from src.interfaces.threads import IThreadService
from src.interfaces.prompts import IPromptLoader
from src.interfaces.history import IHistoryManager
from src.interfaces.config import IConfigValidator


class ServiceUsageExample:
    """服务使用示例类"""
    
    def __init__(self, container):
        """初始化示例
        
        Args:
            container: 依赖注入容器
        """
        self._container = container
    
    def example_basic_service_usage(self) -> None:
        """基本服务使用示例"""
        # 获取日志服务
        logger = self._container.get(ILogger)
        logger.info("开始基本服务使用示例")
        
        # 获取配置服务
        config_loader = self._container.get(IConfigLoader)
        app_config = config_loader.load_config("app")
        logger.info(f"加载应用配置: {app_config}")
        
        # 获取存储服务
        storage_service = self._container.get(IStorageService)
        # 使用存储服务...
        
        # 获取LLM服务
        llm_service = self._container.get(ILLMService)
        # 使用LLM服务...
        
        logger.info("基本服务使用示例完成")
    
    def example_workflow_service_usage(self) -> None:
        """工作流服务使用示例"""
        logger = self._container.get(ILogger)
        logger.info("开始工作流服务使用示例")
        
        # 获取工作流服务
        workflow_service = self._container.get(IWorkflowService)
        
        # 执行工作流
        workflow_id = "example_workflow"
        input_data = {"message": "Hello, World!"}
        
        try:
            result = workflow_service.execute_workflow(workflow_id, input_data)
            logger.info(f"工作流执行结果: {result}")
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
        
        logger.info("工作流服务使用示例完成")
    
    def example_session_service_usage(self) -> None:
        """会话服务使用示例"""
        logger = self._container.get(ILogger)
        logger.info("开始会话服务使用示例")
        
        # 获取会话服务
        session_service = self._container.get(ISessionService)
        
        # 创建会话
        from src.core.sessions.entities import UserRequestEntity
        from datetime import datetime
        
        user_request = UserRequestEntity(
            request_id="example_request",
            user_id="example_user",
            content="创建示例会话",
            metadata={"example": True},
            timestamp=datetime.now()
        )
        
        try:
            session_id = session_service.create_session(user_request)
            logger.info(f"创建会话成功: {session_id}")
            
            # 获取会话信息
            session_info = session_service.get_session_info(session_id)
            logger.info(f"会话信息: {session_info}")
        except Exception as e:
            logger.error(f"会话操作失败: {e}")
        
        logger.info("会话服务使用示例完成")
    
    def example_thread_service_usage(self) -> None:
        """线程服务使用示例"""
        logger = self._container.get(ILogger)
        logger.info("开始线程服务使用示例")
        
        # 获取线程服务
        thread_service = self._container.get(IThreadService)
        
        # 创建线程
        graph_id = "example_graph"
        metadata = {"example": True}
        
        try:
            thread_id = thread_service.create_thread(graph_id, metadata)
            logger.info(f"创建线程成功: {thread_id}")
            
            # 获取线程信息
            thread_info = thread_service.get_thread_info(thread_id)
            logger.info(f"线程信息: {thread_info}")
        except Exception as e:
            logger.error(f"线程操作失败: {e}")
        
        logger.info("线程服务使用示例完成")
    
    def example_history_service_usage(self) -> None:
        """历史服务使用示例"""
        logger = self._container.get(ILogger)
        logger.info("开始历史服务使用示例")
        
        # 获取历史管理器
        history_manager = self._container.get(IHistoryManager)
        
        # 获取历史统计
        try:
            session_id = "example_session"
            token_stats = history_manager.get_token_statistics(session_id)
            logger.info(f"Token统计: {token_stats}")
            
            cost_stats = history_manager.get_cost_statistics(session_id)
            logger.info(f"成本统计: {cost_stats}")
        except Exception as e:
            logger.error(f"历史操作失败: {e}")
        
        logger.info("历史服务使用示例完成")
    
    def example_service_composition(self) -> None:
        """服务组合使用示例"""
        logger = self._container.get(ILogger)
        logger.info("开始服务组合使用示例")
        
        # 获取多个服务
        session_service = self._container.get(ISessionService)
        thread_service = self._container.get(IThreadService)
        workflow_service = self._container.get(IWorkflowService)
        history_manager = self._container.get(IHistoryManager)
        
        try:
            # 创建会话
            from src.core.sessions.entities import UserRequestEntity
            from datetime import datetime
            
            user_request = UserRequestEntity(
                request_id="composition_request",
                user_id="example_user",
                content="服务组合示例",
                metadata={"composition": True},
                timestamp=datetime.now()
            )
            
            session_id = session_service.create_session(user_request)
            logger.info(f"创建会话: {session_id}")
            
            # 创建线程
            thread_id = thread_service.create_thread("example_graph", {"session_id": session_id})
            logger.info(f"创建线程: {thread_id}")
            
            # 执行工作流
            result = workflow_service.execute_workflow("example_workflow", {"thread_id": thread_id})
            logger.info(f"工作流结果: {result}")
            
            # 记录历史
            # 这里应该通过历史管理器记录操作，简化处理
            logger.info("服务组合示例完成")
            
        except Exception as e:
            logger.error(f"服务组合操作失败: {e}")
        
        logger.info("服务组合使用示例完成")


def main():
    """主函数 - 演示容器使用"""
    # 创建配置
    config = {
        "log_level": "INFO",
        "database_url": "postgresql://localhost:5432/app",
        "history": {
            "enable_async_batching": True,
            "batch_size": 10,
            "batch_timeout": 1.0
        }
    }
    
    # 创建容器
    container = ContainerBootstrap.create_container(config)
    
    # 创建使用示例
    example = ServiceUsageExample(container)
    
    # 运行各种示例
    example.example_basic_service_usage()
    example.example_workflow_service_usage()
    example.example_session_service_usage()
    example.example_thread_service_usage()
    example.example_history_service_usage()
    example.example_service_composition()


if __name__ == "__main__":
    main()