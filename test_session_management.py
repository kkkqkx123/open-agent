#!/usr/bin/env python3
"""会话管理功能测试脚本"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.container import get_global_container
from src.sessions.manager import ISessionManager
from src.presentation.tui.session_handler import SessionHandler
from src.presentation.tui.state_manager import StateManager
from src.prompts.agent_state import AgentState, HumanMessage


async def test_session_creation():
    """测试会话创建"""
    print("🧪 测试会话创建...")
    
    try:
        # 获取依赖容器
        container = get_global_container()
        
        # 设置必要的服务
        from src.infrastructure.config_loader import YamlConfigLoader, IConfigLoader
        from src.sessions.store import FileSessionStore
        from src.workflow.manager import WorkflowManager
        from src.sessions.git_manager import GitManager, create_git_manager
        from src.sessions.manager import SessionManager
        
        # 注册配置加载器
        if not container.has_service(IConfigLoader):
            config_loader = YamlConfigLoader()
            container.register_instance(IConfigLoader, config_loader)
        
        # 注册会话存储
        if not container.has_service(FileSessionStore):
            from pathlib import Path
            session_store = FileSessionStore(Path("./test_sessions"))
            container.register_instance(FileSessionStore, session_store)
        
        # 注册Git管理器
        if not container.has_service(GitManager):
            git_manager = create_git_manager(use_mock=True)
            container.register_instance(GitManager, git_manager)
        
        # 注册工作流管理器
        if not container.has_service(WorkflowManager):
            workflow_manager = WorkflowManager(container.get(IConfigLoader))
            container.register_instance(WorkflowManager, workflow_manager)
        
        # 注册会话管理器
        if not container.has_service(ISessionManager):
            session_manager = SessionManager(
                workflow_manager=container.get(WorkflowManager),
                session_store=container.get(FileSessionStore),
                git_manager=container.get(GitManager)
            )
            container.register_instance(ISessionManager, session_manager)
        
        # 创建会话处理器和状态管理器
        session_handler = SessionHandler(container.get(ISessionManager))
        state_manager = StateManager(container.get(ISessionManager))
        
        # 测试创建会话
        workflow_config = "configs/workflows/react.yaml"
        session_id = session_handler.create_session(workflow_config, {})
        
        if session_id:
            print(f"✅ 会话创建成功: {session_id[:8]}...")
            
            # 测试加载会话
            result = session_handler.load_session(session_id)
            if result:
                workflow, state = result
                print(f"✅ 会话加载成功: {type(workflow).__name__}, {type(state).__name__}")
                
                # 更新状态管理器
                state_manager.session_id = session_id
                state_manager.current_workflow = workflow
                state_manager.current_state = state
                
                # 添加一些测试消息
                state_manager.add_user_message("测试用户消息")
                state_manager.add_assistant_message("测试助手回复")
                state_manager.add_system_message("测试系统消息")
                
                print(f"✅ 消息历史创建: {len(state_manager.message_history)} 条消息")
                
                # 测试保存会话
                save_success = session_handler.save_session(session_id, workflow, state)
                if save_success:
                    print("✅ 会话保存成功")
                    
                    # 测试会话列表
                    sessions = session_handler.list_sessions()
                    print(f"✅ 会话列表获取成功: {len(sessions)} 个会话")
                    
                    # 测试会话信息
                    session_info = session_handler.get_session_info(session_id)
                    if session_info:
                        print(f"✅ 会话信息获取成功: {session_info.get('workflow_config_path', '未知')}")
                    
                    return True
                else:
                    print("❌ 会话保存失败")
                    return False
            else:
                print("❌ 会话加载失败")
                return False
        else:
            print("❌ 会话创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_session_switching():
    """测试会话切换"""
    print("\n🧪 测试会话切换...")
    
    try:
        # 获取依赖容器
        container = get_global_container()
        session_manager = container.get(ISessionManager)
        
        # 创建多个会话
        session_ids = []
        for i in range(3):
            workflow_config = "configs/workflows/react.yaml"
            session_id = session_manager.create_session(workflow_config, {})
            if session_id:
                session_ids.append(session_id)
                print(f"✅ 创建会话 {i+1}: {session_id[:8]}...")
        
        if len(session_ids) >= 2:
            # 测试切换会话
            session_handler = SessionHandler(session_manager)
            state_manager = StateManager(session_manager)
            
            # 切换到第一个会话
            result = session_handler.load_session(session_ids[0])
            if result:
                workflow, state = result
                state_manager.session_id = session_ids[0]
                state_manager.current_workflow = workflow
                state_manager.current_state = state
                state_manager.add_user_message(f"会话 {session_ids[0][:8]}... 的消息")
                print(f"✅ 切换到会话: {session_ids[0][:8]}...")
                
                # 保存当前会话
                session_handler.save_session(session_ids[0], workflow, state)
                
                # 切换到第二个会话
                result = session_handler.load_session(session_ids[1])
                if result:
                    workflow, state = result
                    state_manager.session_id = session_ids[1]
                    state_manager.current_workflow = workflow
                    state_manager.current_state = state
                    state_manager.add_user_message(f"会话 {session_ids[1][:8]}... 的消息")
                    print(f"✅ 切换到会话: {session_ids[1][:8]}...")
                    
                    # 再次切换回第一个会话
                    result = session_handler.load_session(session_ids[0])
                    if result:
                        workflow, state = result
                        state_manager.session_id = session_ids[0]
                        state_manager.current_workflow = workflow
                        state_manager.current_state = state
                        
                        # 检查消息历史是否保持
                        if len(state_manager.message_history) > 0:
                            print(f"✅ 会话状态保持成功: {len(state_manager.message_history)} 条消息")
                            return True
                        else:
                            print("❌ 会话状态保持失败: 消息历史丢失")
                            return False
                    else:
                        print("❌ 切换回第一个会话失败")
                        return False
                else:
                    print("❌ 切换到第二个会话失败")
                    return False
            else:
                print("❌ 初始会话加载失败")
                return False
        else:
            print("❌ 创建的会话数量不足")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_session_deletion():
    """测试会话删除"""
    print("\n🧪 测试会话删除...")
    
    try:
        # 获取依赖容器
        container = get_global_container()
        session_manager = container.get(ISessionManager)
        session_handler = SessionHandler(session_manager)
        
        # 创建测试会话
        workflow_config = "configs/workflows/react.yaml"
        session_id = session_handler.create_session(workflow_config, {})
        
        if session_id:
            print(f"✅ 创建测试会话: {session_id[:8]}...")
            
            # 验证会话存在
            exists = session_handler.session_exists(session_id)
            if exists:
                print("✅ 会话存在验证成功")
                
                # 删除会话
                delete_success = session_handler.delete_session(session_id)
                if delete_success:
                    print("✅ 会话删除成功")
                    
                    # 验证会话不存在
                    exists_after = session_handler.session_exists(session_id)
                    if not exists_after:
                        print("✅ 会话不存在验证成功")
                        return True
                    else:
                        print("❌ 会话仍然存在")
                        return False
                else:
                    print("❌ 会话删除失败")
                    return False
            else:
                print("❌ 会话不存在验证失败")
                return False
        else:
            print("❌ 创建测试会话失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🚀 开始会话管理功能测试\n")
    
    # 运行所有测试
    tests = [
        test_session_creation,
        test_session_switching,
        test_session_deletion
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    # 输出测试结果
    print("\n📊 测试结果汇总:")
    print(f"总测试数: {len(tests)}")
    print(f"成功数: {sum(results)}")
    print(f"失败数: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 所有测试通过！会话管理功能正常工作。")
        return 0
    else:
        print("❌ 部分测试失败，请检查相关功能。")
        return 1


if __name__ == "__main__":
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)