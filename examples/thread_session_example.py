"""Thread与Session重构后的使用示例

展示重构后的ThreadManager和SessionManager如何协同工作，
实现清晰的职责划分：Threads负责执行与LangGraph交互，Sessions负责用户交互追踪
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from src.infrastructure.di.thread_session_di_config import (
    ThreadSessionDIConfig,
    ThreadSessionFactory,
    create_development_stack,
    create_testing_stack
)
from application.sessions.manager import UserRequest, UserInteraction

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建开发环境组件栈
    components = create_development_stack(Path("./example_storage"))
    
    # 获取组件
    session_manager = components["session_manager"]
    thread_manager = components["thread_manager"]
    langgraph_adapter = components["langgraph_adapter"]
    
    try:
        # 1. 创建用户会话
        user_request = UserRequest(
            request_id="req_001",
            user_id="user_123",
            content="我需要分析一些数据并生成报告",
            metadata={"priority": "high", "category": "data_analysis"},
            timestamp=datetime.now()
        )
        
        session_id = await session_manager.create_session(user_request)
        print(f"创建会话成功: {session_id}")
        
        # 2. 协调多个Thread
        thread_configs = [
            {
                "name": "data_processing",
                "config_path": "configs/workflows/data_processing.yaml",
                "initial_state": {"data_source": "user_upload", "format": "csv"}
            },
            {
                "name": "analysis",
                "config_path": "configs/workflows/data_analysis.yaml",
                "initial_state": {"analysis_type": "statistical"}
            },
            {
                "name": "report_generation",
                "config_path": "configs/workflows/report_generation.yaml",
                "initial_state": {"format": "pdf", "template": "standard"}
            }
        ]
        
        thread_ids = await session_manager.coordinate_threads(session_id, thread_configs)
        print(f"协调Thread成功: {thread_ids}")
        
        # 3. 在会话中执行工作流
        print("\n--- 执行数据处理工作流 ---")
        data_processing_result = await session_manager.execute_workflow_in_session(
            session_id, 
            "data_processing",
            config={"batch_size": 1000}
        )
        print(f"数据处理结果: {data_processing_result}")
        
        # 4. 流式执行分析工作流
        print("\n--- 流式执行分析工作流 ---")
        async for state in session_manager.stream_workflow_in_session(
            session_id, 
            "analysis",
            config={"depth": "detailed"}
        ):
            print(f"分析中间状态: {state.get('current_step', 'unknown')}")
        
        # 5. 获取会话摘要
        session_summary = await session_manager.get_session_summary(session_id)
        print(f"\n会话摘要: {session_summary}")
        
        # 6. 获取交互历史
        interactions = await session_manager.get_interaction_history(session_id)
        print(f"\n交互历史 (共{len(interactions)}条):")
        for interaction in interactions[-5:]:  # 显示最后5条
            print(f"  [{interaction.timestamp}] {interaction.interaction_type}: {interaction.content}")
    
    finally:
        # 清理资源
        await thread_manager.clear_graph_cache()
        print("\n资源清理完成")


async def example_direct_thread_usage():
    """直接使用ThreadManager的示例"""
    print("\n=== 直接使用ThreadManager示例 ===")
    
    # 创建DI配置
    di_config = ThreadSessionDIConfig(use_memory_storage=True)
    
    # 创建ThreadManager
    thread_manager = di_config.create_thread_manager()
    
    try:
        # 1. 从配置创建Thread
        thread_id = await thread_manager.create_thread_from_config(
            "configs/workflows/simple_chat.yaml",
            metadata={"purpose": "example", "user": "demo"}
        )
        print(f"创建Thread成功: {thread_id}")
        
        # 2. 执行工作流
        initial_state = {
            "messages": [{"role": "user", "content": "你好，请介绍一下自己"}],
            "current_step": "greeting"
        }
        
        result = await thread_manager.execute_workflow(
            thread_id,
            config={"temperature": 0.7},
            initial_state=initial_state
        )
        print(f"工作流执行结果: {result}")
        
        # 3. 获取Thread状态
        current_state = await thread_manager.get_thread_state(thread_id)
        print(f"当前Thread状态: {current_state}")
        
        # 4. 创建Thread分支
        branch_thread_id = await thread_manager.fork_thread(
            thread_id,
            checkpoint_id="latest",  # 使用最新checkpoint
            branch_name="experimental_branch",
            metadata={"experiment": "try_different_temperature"}
        )
        print(f"创建分支Thread成功: {branch_thread_id}")
        
        # 5. 获取Thread历史
        history = await thread_manager.get_thread_history(thread_id, limit=5)
        print(f"Thread历史 (最近5条): {len(history)}条记录")
        
    finally:
        # 清理资源
        await thread_manager.clear_graph_cache()


async def example_session_interaction_tracking():
    """会话交互追踪示例"""
    print("\n=== 会话交互追踪示例 ===")
    
    # 使用工厂模式
    factory = ThreadSessionFactory(ThreadSessionDIConfig(use_memory_storage=True))
    session_manager = factory.get_session_manager()
    
    try:
        # 1. 创建会话
        user_request = UserRequest(
            request_id="req_002",
            user_id="user_456",
            content="帮我规划一个旅行计划",
            metadata={"destination": "日本", "duration": "7天"},
            timestamp=datetime.now()
        )
        
        session_id = await session_manager.create_session(user_request)
        print(f"创建会话成功: {session_id}")
        
        # 2. 手动追踪交互
        system_response = UserInteraction(
            interaction_id="int_001",
            session_id=session_id,
            thread_id=None,
            interaction_type="system_response",
            content="我来帮您规划日本7天旅行计划",
            metadata={"response_type": "acknowledgment"},
            timestamp=datetime.now()
        )
        await session_manager.track_user_interaction(session_id, system_response)
        
        # 3. 创建规划Thread
        thread_configs = [
            {
                "name": "travel_planning",
                "config_path": "configs/workflows/travel_planning.yaml",
                "initial_state": {
                    "destination": "日本",
                    "duration": 7,
                    "preferences": ["文化", "美食", "购物"]
                }
            }
        ]
        
        thread_ids = await session_manager.coordinate_threads(session_id, thread_configs)
        planning_thread_id = thread_ids["travel_planning"]
        
        # 4. 追踪用户反馈
        user_feedback = UserInteraction(
            interaction_id="int_002",
            session_id=session_id,
            thread_id=planning_thread_id,
            interaction_type="user_feedback",
            content="我希望多安排一些文化体验活动",
            metadata={"feedback_type": "preference_adjustment"},
            timestamp=datetime.now()
        )
        await session_manager.track_user_interaction(session_id, user_feedback)
        
        # 5. 执行规划工作流
        plan_result = await session_manager.execute_workflow_in_session(
            session_id,
            "travel_planning",
            config={"include_cultural_activities": True}
        )
        print(f"旅行规划结果: {plan_result}")
        
        # 6. 查看完整的交互历史
        interactions = await session_manager.get_interaction_history(session_id)
        print(f"\n完整交互历史:")
        for i, interaction in enumerate(interactions, 1):
            print(f"  {i}. [{interaction.interaction_type}] {interaction.content}")
        
    finally:
        # 清理资源
        factory.clear_cache()


async def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    # 创建测试环境组件栈
    components = create_testing_stack()
    session_manager = components["session_manager"]
    
    try:
        # 1. 创建会话
        user_request = UserRequest(
            request_id="req_003",
            user_id="user_789",
            content="测试错误处理",
            metadata={"test": True},
            timestamp=datetime.now()
        )
        
        session_id = await session_manager.create_session(user_request)
        print(f"创建会话成功: {session_id}")
        
        # 2. 尝试执行不存在的Thread
        try:
            await session_manager.execute_workflow_in_session(
                session_id,
                "nonexistent_thread"
            )
        except ValueError as e:
            print(f"捕获预期错误: {e}")
        
        # 3. 查看错误交互记录
        interactions = await session_manager.get_interaction_history(session_id)
        error_interactions = [i for i in interactions if "error" in i.interaction_type]
        print(f"错误交互记录: {len(error_interactions)}条")
        for interaction in error_interactions:
            print(f"  - {interaction.interaction_type}: {interaction.content}")
    
    finally:
        # 清理资源
        components["thread_manager"].clear_graph_cache()


async def main():
    """主函数"""
    print("Thread与Session重构后的使用示例")
    print("=" * 50)
    
    try:
        # 运行各种示例
        await example_basic_usage()
        await example_direct_thread_usage()
        await example_session_interaction_tracking()
        await example_error_handling()
        
        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())