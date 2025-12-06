"""基础设施层图组件验证脚本

用于验证所有组件的集成和功能。
"""

import asyncio
from typing import Any

from . import StateGraphEngine, ExecutionEngine, CheckpointManager, HookSystem
from .checkpoint import MemoryCheckpointSaver
from .optimization import ResourceManager, ResourceLimits
from .hooks import HookPoint, HookContext
from .types import START, END


async def validate_component_integration() -> dict[str, Any]:
    """验证组件集成。
    
    Returns:
        验证结果字典
    """
    results = {
        "state_graph_engine": False,
        "execution_engine": False,
        "checkpoint_manager": False,
        "hook_system": False,
        "resource_manager": False,
        "integration": False
    }
    
    try:
        # 1. 验证StateGraphEngine
        print("验证StateGraphEngine...")
        
        # 定义状态模式
        class TestState:
            def __init__(self, messages: list | None = None, counter: int = 0):
                self.messages = messages or []
                self.counter = counter
        
        # 创建状态图引擎
        state_graph = StateGraphEngine(TestState)
        state_graph.add_node("start", lambda state: {"counter": state["counter"] + 1})
        state_graph.add_node("end", lambda state: {"messages": state["messages"] + ["done"]})
        state_graph.add_edge("start", "end")
        state_graph.set_entry_point("start")
        
        # 设置Hook系统
        hook_system = HookSystem()
        state_graph.set_hook_system(hook_system)
        
        # 编译图
        compiled_graph = await state_graph.compile()  # type: ignore[assignment]
        
        results["state_graph_engine"] = True
        print("✓ StateGraphEngine验证通过")
        
        # 2. 验证ExecutionEngine
        print("验证ExecutionEngine...")
        
        execution_engine = ExecutionEngine(compiled_graph)
        execution_engine.set_hook_system(hook_system)
        
        # 执行图
        input_data = {"messages": [], "counter": 0}
        result = await execution_engine.invoke(input_data)
        
        assert result["counter"] == 1
        results["execution_engine"] = True
        print("✓ ExecutionEngine验证通过")
        
        # 3. 验证CheckpointManager
        print("验证CheckpointManager...")
        
        memory_saver = MemoryCheckpointSaver()
        checkpoint_manager = CheckpointManager(memory_saver)
        checkpoint_manager.set_hook_system(hook_system)
        
        # 设置资源管理器
        resource_limits = ResourceLimits(max_active_graphs=10)
        resource_manager = ResourceManager(resource_limits)
        checkpoint_manager.set_resource_manager(resource_manager)
        
        # 保存检查点
        config = {
            "configurable": {
                "thread_id": "test_thread",
                "checkpoint_ns": "",
                "checkpoint_id": "test_checkpoint"
            }
        }
        
        from .checkpoint.base import Checkpoint, CheckpointMetadata
        checkpoint = Checkpoint(
            id="test_checkpoint",
            ts="2024-01-01T00:00:00",
            channel_values=result,
            channel_versions={},
            versions_seen={}
        )
        metadata = CheckpointMetadata(source="test", step=1, parents={})
        
        checkpoint_id = await checkpoint_manager.save_checkpoint(config, checkpoint, metadata)
        
        # 加载检查点
        loaded_checkpoint = await checkpoint_manager.load_checkpoint(config)
        
        assert loaded_checkpoint is not None
        assert loaded_checkpoint.id == "test_checkpoint"
        results["checkpoint_manager"] = True
        print("✓ CheckpointManager验证通过")
        
        # 4. 验证Hook系统
        print("验证Hook系统...")
        
        # 注册测试Hook
        from .hooks import IHookPlugin
        
        class TestHook(IHookPlugin):
            def __init__(self, name: str):
                self._name = name
                self.executed = False
            
            @property
            def name(self) -> str:
                return self._name
            
            @property
            def priority(self) -> int:
                return 50
            
            async def execute(self, context: HookContext) -> Any:
                self.executed = True
                return f"Hook {self._name} executed"
        
        test_hook = TestHook("test")
        hook_system.register_hook(HookPoint.BEFORE_EXECUTION, test_hook)
        
        # 执行Hook
        hook_result = await hook_system.execute_hooks(HookPoint.BEFORE_EXECUTION, HookContext(
            hook_point=HookPoint.BEFORE_EXECUTION,
            graph_id="test_graph"
        ))
        
        assert hook_result.success
        assert test_hook.executed
        results["hook_system"] = True
        print("✓ Hook系统验证通过")
        
        # 5. 验证ResourceManager
        print("验证ResourceManager...")
        
        # 注册图资源
        resource_manager.register_graph("test_graph", compiled_graph)
        
        # 监控资源
        usage = resource_manager.monitor_resources()
        
        assert usage.active_graphs == 1
        results["resource_manager"] = True
        print("✓ ResourceManager验证通过")
        
        # 6. 验证集成
        print("验证组件集成...")
        
        # 清理资源
        resource_manager.destroy_graph("test_graph")
        await state_graph.destroy()
        
        # 验证清理后的状态
        usage_after_cleanup = resource_manager.monitor_resources()
        assert usage_after_cleanup.active_graphs == 0
        
        results["integration"] = True
        print("✓ 组件集成验证通过")
        
    except Exception as e:
        print(f"✗ 验证失败: {str(e)}")
        results["error"] = str(e)  # type: ignore[assignment]
    
    return results


def print_validation_results(results: dict[str, Any]) -> None:
    """打印验证结果。
    
    Args:
        results: 验证结果
    """
    print("\n" + "="*50)
    print("基础设施层图组件验证结果")
    print("="*50)
    
    for component, status in results.items():
        if component == "error":
            print(f"错误: {status}")
        else:
            status_icon = "✓" if status else "✗"
            print(f"{component}: {status_icon}")
    
    print("="*50)
    
    # 计算成功率
    passed = sum(1 for k, v in results.items() if k != "error" and v)
    total = sum(1 for k in results.keys() if k != "error")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"总体成功率: {success_rate:.1f}% ({passed}/{total})")
    
    print("="*50)


if __name__ == "__main__":
    """运行验证脚本。"""
    print("开始验证基础设施层图组件...")
    
    async def main():
        results = await validate_component_integration()
        print_validation_results(results)
    
    asyncio.run(main())