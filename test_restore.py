import asyncio
import sys
sys.path.append('src')

from application.checkpoint.manager import CheckpointManager, CheckpointConfig
from infrastructure.checkpoint.memory_store import MemoryCheckpointStore
from infrastructure.serialization.base import Serializer
from infrastructure.checkpoint.serialization import CheckpointSerializer

async def test_restore():
    # 创建管理器
    config = CheckpointConfig(
        enabled=True,
        storage_type='memory',
        auto_save=True,
        save_interval=2,
        max_checkpoints=5
    )
    
    base_serializer = Serializer()
    serializer = CheckpointSerializer(base_serializer)
    store = MemoryCheckpointStore(serializer)
    manager = CheckpointManager(store, config)
    
    # 创建测试状态
    class MockState:
        def __init__(self):
            self.messages = [{'role': 'user', 'content': 'hello'}]
            self.current_step = 'analysis'
            self.iteration_count = 1
    
    state = MockState()
    
    # 创建checkpoint
    checkpoint_id = await manager.create_checkpoint(
        'session-1', 'workflow-1', state, {'node': 'analysis'}
    )
    print(f'Created checkpoint: {checkpoint_id}')
    
    # 获取checkpoint
    checkpoint = await manager.get_checkpoint('session-1', checkpoint_id)
    print(f'Got checkpoint: {checkpoint}')
    print(f'State data in checkpoint: {checkpoint.get("state_data") if checkpoint else None}')
    
    # 恢复状态
    restored_state = await manager.restore_from_checkpoint('session-1', checkpoint_id)
    print(f'Restored state: {restored_state}')
    print(f'Type of restored state: {type(restored_state)}')
    
    if restored_state:
        print(f'Has messages attr: {hasattr(restored_state, "messages")}')
        print(f'Has current_step attr: {hasattr(restored_state, "current_step")}')
        if hasattr(restored_state, 'messages'):
            print(f'Messages: {restored_state.messages}')

if __name__ == '__main__':
    asyncio.run(test_restore())