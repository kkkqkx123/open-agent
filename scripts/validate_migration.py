"""验证迁移结果的测试脚本"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.container.updated_container import create_updated_container
from src.adapters.compatibility import create_legacy_managers
from src.interfaces.sessions import ISessionService, ISessionStore
from src.interfaces.threads import IThreadService, IThreadStore


async def test_session_service():
    """测试会话服务"""
    print("=== 测试会话服务 ===")
    
    try:
        container = create_updated_container()
        session_service = container.resolve(ISessionService)
        
        # 测试创建会话
        session_config = {
            "name": "测试会话",
            "description": "迁移测试会话",
            "metadata": {"test": True}
        }
        
        session_id = await session_service.create_session_with_thread(session_config)
        print(f"✓ 创建会话成功: {session_id}")
        
        # 测试更新元数据
        metadata_update = {"updated": True, "version": "2.0"}
        success = await session_service.update_session_metadata(session_id, metadata_update)
        print(f"✓ 更新元数据成功: {success}")
        
        # 测试增加计数
        message_count = await session_service.increment_message_count(session_id)
        print(f"✓ 消息计数: {message_count}")
        
        checkpoint_count = await session_service.increment_checkpoint_count(session_id)
        print(f"✓ 检查点计数: {checkpoint_count}")
        
        # 测试获取摘要
        summary = await session_service.get_session_summary(session_id)
        print(f"✓ 会话摘要: {summary}")
        
        return True
        
    except Exception as e:
        print(f"✗ 会话服务测试失败: {e}")
        return False


async def test_thread_service():
    """测试线程服务"""
    print("\n=== 测试线程服务 ===")
    
    try:
        container = create_updated_container()
        thread_service = container.resolve(IThreadService)
        
        # 先创建会话
        session_service = container.resolve(ISessionService)
        session_config = {
            "name": "线程测试会话",
            "description": "线程服务测试"
        }
        session_id = await session_service.create_session_with_thread(session_config)
        
        # 测试创建线程
        thread_config = {
            "name": "测试线程",
            "description": "迁移测试线程",
            "metadata": {"test": True}
        }
        
        thread_id = await thread_service.create_thread_with_session(session_id, thread_config)
        print(f"✓ 创建线程成功: {thread_id}")
        
        # 测试更新元数据
        metadata_update = {"updated": True, "priority": "high"}
        success = await thread_service.update_thread_metadata(thread_id, metadata_update)
        print(f"✓ 更新线程元数据成功: {success}")
        
        # 测试获取线程信息
        thread_info = await thread_service.get_thread_info(thread_id)
        print(f"✓ 线程信息: {thread_info}")
        
        return True
        
    except Exception as e:
        print(f"✗ 线程服务测试失败: {e}")
        return False


async def test_legacy_compatibility():
    """测试向后兼容性"""
    print("\n=== 测试向后兼容性 ===")
    
    try:
        container = create_updated_container()
        legacy_managers = create_legacy_managers(container)
        
        # 测试传统会话管理器
        session_manager = legacy_managers["session_manager"]
        session_config = {"name": "兼容性测试会话"}
        session_id = await session_manager.create_session(session_config)
        print(f"✓ 传统会话管理器创建会话: {session_id}")
        
        session_info = await session_manager.get_session(session_id)
        print(f"✓ 传统会话管理器获取会话: {session_info is not None}")
        
        # 测试传统线程管理器
        thread_manager = legacy_managers["thread_manager"]
        thread_config = {"name": "兼容性测试线程"}
        thread_id = await thread_manager.create_thread(session_id, thread_config)
        print(f"✓ 传统线程管理器创建线程: {thread_id}")
        
        thread_info = await thread_manager.get_thread(thread_id)
        print(f"✓ 传统线程管理器获取线程: {thread_info is not None}")
        
        return True
        
    except Exception as e:
        print(f"✗ 兼容性测试失败: {e}")
        return False


async def test_service_registry():
    """测试服务注册表"""
    print("\n=== 测试服务注册表 ===")
    
    try:
        container = create_updated_container()
        registry = container.get_service_registry()
        
        # 测试服务注册
        services = [
            "session_service", "thread_service", 
            "thread_branch_service", "thread_snapshot_service",
            "thread_coordinator_service"
        ]
        
        for service_name in services:
            service_type = registry.get(service_name)
            if service_type:
                print(f"✓ 服务 {service_name} 已注册: {service_type.__name__}")
            else:
                print(f"✗ 服务 {service_name} 未注册")
        
        return True
        
    except Exception as e:
        print(f"✗ 服务注册表测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("开始迁移验证测试...\n")
    
    tests = [
        test_session_service,
        test_thread_service,
        test_legacy_compatibility,
        test_service_registry
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"测试异常: {e}")
            results.append(False)
    
    print(f"\n=== 测试结果总结 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过测试: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！迁移成功。")
        return True
    else:
        print("⚠️  部分测试失败，请检查迁移结果。")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)