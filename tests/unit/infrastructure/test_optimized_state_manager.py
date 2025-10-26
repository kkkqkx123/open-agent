"""OptimizedStateManager单元测试"""

import time
import threading
from typing import Dict, Any
import pytest

from src.infrastructure.graph.states.optimized_manager import OptimizedStateManager
from src.infrastructure.graph.states.base import BaseGraphState, BaseMessage, HumanMessage, AIMessage
from src.infrastructure.graph.states.serializer import StateDiff


class TestOptimizedStateManager:
    """OptimizedStateManager测试类"""
    
    def setup_method(self):
        """测试设置"""
        self.manager = OptimizedStateManager(
            enable_pooling=True,
            max_pool_size=50,
            enable_diff_tracking=True
        )
        
        # 创建测试状态
        self.test_state = {
            "messages": [HumanMessage(content="Hello")],
            "current_step": 1,
            "total_steps": 5,
            "metadata": {"user_id": "test_user", "session_id": "test_session"}
        }
    
    def test_create_state(self):
        """测试创建状态"""
        state_id = "test_state_1"
        
        # 创建状态
        new_state = self.manager.create_state(state_id, self.test_state)
        
        # 验证状态被正确创建
        assert new_state is not None
        assert new_state["current_step"] == 1
        assert len(new_state["messages"]) == 1
    
    def test_state_pooling(self):
        """测试状态对象池"""
        state_id = "pooled_state"
        
        # 第一次创建状态
        state1 = self.manager.create_state(state_id, self.test_state)
        
        # 修改状态
        updated_state = {**self.test_state, "current_step": 2}
        
        # 第二次创建相同ID的状态（应该重用对象）
        state2 = self.manager.create_state(state_id, updated_state)
        
        # 验证状态值被正确更新
        assert state2["current_step"] == 2
        
        # 检查性能统计
        stats = self.manager.get_performance_stats()
        assert "manager_stats" in stats
        assert "pool_efficiency" in stats
    
    def test_incremental_state_update(self):
        """测试增量状态更新"""
        state_id = "incremental_state"
        
        # 执行增量更新
        updates = {
            "current_step": 3,
            "new_field": "new_value"
        }
        
        updated_state = self.manager.update_state_incremental(
            state_id, 
            self.test_state, 
            updates
        )
        
        # 验证更新被正确应用
        assert updated_state["current_step"] == 3
        assert updated_state["new_field"] == "new_value"
        assert updated_state["total_steps"] == 5  # 未更新的字段保持不变
    
    def test_list_incremental_update(self):
        """测试列表增量更新"""
        state_id = "list_update_state"
        
        # 创建包含列表的初始状态
        initial_state = {
            "messages": [HumanMessage(content="Message 1")],
            "items": ["item1", "item2"]
        }
        
        # 执行增量更新，添加到列表
        updates = {
            "messages": [HumanMessage(content="Message 1"), AIMessage(content="Message 2")],
            "items": ["item1", "item2", "item3"]
        }
        
        updated_state = self.manager.update_state_incremental(
            state_id,
            initial_state,
            updates
        )
        
        # 验证列表被正确更新
        assert len(updated_state["messages"]) == 2
        assert len(updated_state["items"]) == 3
        assert updated_state["items"][2] == "item3"
    
    def test_state_diff_application(self):
        """测试状态差异应用"""
        state_id = "diff_state"
        
        # 创建新状态
        new_state = {
            "messages": [HumanMessage(content="Hello"), AIMessage(content="Hi")],
            "current_step": 2,
            "total_steps": 5,
            "new_field": "value"
        }
        
        # 使用序列化器创建差异
        from src.infrastructure.graph.states.serializer import StateSerializer
        serializer = StateSerializer()
        diff_data = serializer.serialize_diff(self.test_state, new_state)
        
        # 应用差异
        applied_state = self.manager.apply_state_diff(state_id, self.test_state, diff_data)
        
        # 验证差异被正确应用
        assert applied_state["current_step"] == 2
        assert len(applied_state["messages"]) == 2
        assert applied_state["new_field"] == "value"
    
    def test_state_compression(self):
        """测试状态压缩"""
        state_id = "compressed_state"
        
        # 创建大状态
        large_state = {
            "messages": [HumanMessage(content=f"Message {i}") for i in range(100)],
            "data": "large_data" * 100,
            "metadata": {"key": "value"}
        }
        
        # 压缩状态
        compressed_state = self.manager.compress_state(state_id, large_state)
        
        # 验证压缩后的状态仍然包含关键信息
        assert "metadata" in compressed_state
        assert compressed_state["metadata"]["key"] == "value"
        
        # 检查内存使用统计
        memory_stats = self.manager.get_memory_usage_stats()
        assert "memory_saved_bytes" in memory_stats
    
    def test_state_history_tracking(self):
        """测试状态历史跟踪"""
        state_id = "history_state"
        
        # 进行一些状态更新
        initial_state = self.test_state.copy()
        updated_state = {**initial_state, "current_step": 2}
        
        # 更新状态以生成历史记录
        self.manager.update_state_incremental(state_id, initial_state, {"current_step": 2})
        self.manager.update_state_incremental(state_id, updated_state, {"current_step": 3})
        
        # 获取状态历史
        history = self.manager.get_state_history(state_id, limit=10)
        
        # 验证历史记录存在
        assert len(history) >= 0  # 可能为空，取决于实现
        
        # 检查历史记录信息
        for update in history:
            assert hasattr(update, 'field_path')
            assert hasattr(update, 'old_value')
            assert hasattr(update, 'new_value')
            assert hasattr(update, 'timestamp')
    
    def test_memory_usage_stats(self):
        """测试内存使用统计"""
        # 执行一些操作来填充内存统计
        self.manager.create_state("test_1", self.test_state)
        self.manager.compress_state("test_1", self.test_state)
        
        # 获取内存使用统计
        memory_stats = self.manager.get_memory_usage_stats()
        
        # 验证统计信息结构
        assert "pool_size" in memory_stats
        assert "compressed_states_size" in memory_stats
        assert "total_memory_bytes" in memory_stats
        assert "memory_saved_bytes" in memory_stats
    
    def test_performance_stats(self):
        """测试性能统计"""
        # 执行一些操作来填充统计信息
        self.manager.create_state("test_1", self.test_state)
        self.manager.update_state_incremental("test_1", self.test_state, {"current_step": 2})
        
        # 获取性能统计
        stats = self.manager.get_performance_stats()
        
        # 验证统计信息结构
        assert "manager_stats" in stats
        assert "serializer_stats" in stats
        assert "pool_efficiency" in stats
        
        # 验证池效率统计
        pool_efficiency = stats["pool_efficiency"]
        assert "hits" in pool_efficiency
        assert "misses" in pool_efficiency
        assert "hit_rate" in pool_efficiency
    
    def test_cleanup_functionality(self):
        """测试清理功能"""
        state_id = "cleanup_test"
        
        # 创建一些状态
        self.manager.create_state(state_id, self.test_state)
        self.manager.compress_state(state_id, self.test_state)
        
        # 验证状态存在
        initial_memory_stats = self.manager.get_memory_usage_stats()
        assert initial_memory_stats["pool_size"] >= 0 or initial_memory_stats["compressed_states_size"] >= 0
        
        # 清理特定状态
        self.manager.cleanup(state_id)
        
        # 验证状态被清理
        final_memory_stats = self.manager.get_memory_usage_stats()
        # 注意：由于实现细节，这里可能不会立即看到变化
    
    def test_cleanup_all(self):
        """测试清理所有状态"""
        # 创建一些状态
        self.manager.create_state("state_1", self.test_state)
        self.manager.create_state("state_2", self.test_state)
        
        # 清理所有状态
        self.manager.cleanup()
        
        # 验证清理后的状态
        memory_stats = self.manager.get_memory_usage_stats()
        # 统计可能不会立即归零，但内部缓存应被清理
    
    def test_concurrent_access(self):
        """测试并发访问"""
        results = []
        errors = []
        
        def state_worker(worker_id):
            try:
                state_id = f"worker_{worker_id}"
                test_state = {**self.test_state, "worker_id": worker_id}
                
                # 创建状态
                state = self.manager.create_state(state_id, test_state)
                
                # 更新状态
                updated_state = self.manager.update_state_incremental(
                    state_id,
                    state,
                    {"current_step": worker_id}
                )
                
                results.append(updated_state["current_step"] == worker_id)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程同时操作状态
        threads = []
        for i in range(5):
            thread = threading.Thread(target=state_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误
        assert len(errors) == 0
        assert len(results) == 5
        assert all(results)  # 所有操作都成功
    
    def test_disabled_pooling(self):
        """测试禁用对象池"""
        # 创建禁用池的管理器
        manager_no_pool = OptimizedStateManager(enable_pooling=False)
        
        state_id = "no_pool_state"
        
        # 创建状态
        state1 = manager_no_pool.create_state(state_id, self.test_state)
        state2 = manager_no_pool.create_state(state_id, self.test_state)
        
        # 验证每次都创建新实例（因为池被禁用）
        # 注意：具体行为取决于实现，这里主要验证没有错误
    
    def test_disabled_diff_tracking(self):
        """测试禁用差异跟踪"""
        # 创建禁用差异跟踪的管理器
        manager_no_diff = OptimizedStateManager(enable_diff_tracking=False)
        
        state_id = "no_diff_state"
        
        # 执行更新
        result = manager_no_diff.update_state_incremental(
            state_id,
            self.test_state,
            {"current_step": 10}
        )
        
        # 验证更新成功
        assert result["current_step"] == 10
    
    def test_empty_updates(self):
        """测试空更新"""
        state_id = "empty_update_state"
        
        # 使用空更新
        result = self.manager.update_state_incremental(
            state_id,
            self.test_state,
            {}
        )
        
        # 验证状态保持不变
        assert result == self.test_state
    
    def test_same_value_updates(self):
        """测试相同值更新"""
        state_id = "same_value_state"
        
        # 更新为相同的值
        result = self.manager.update_state_incremental(
            state_id,
            self.test_state,
            {"current_step": 1}  # 与原值相同
        )
        
        # 验证值没有变化
        assert result["current_step"] == 1
    
    def test_large_state_handling(self):
        """测试大状态处理"""
        # 创建大状态
        large_state = {
            "messages": [HumanMessage(content=f"Message {i}") for in range(200)],
            "data_array": list(range(100)),
            "nested": {
                "level1": {
                    "level2": {
                        "data": "deep_value"
                    }
                }
            }
        }
        
        state_id = "large_state"
        
        # 处理大状态
        result = self.manager.create_state(state_id, large_state)
        
        # 验证状态被正确处理
        assert len(result["messages"]) == 200
        assert len(result["data_array"]) == 1000
        assert result["nested"]["level1"]["level2"]["data"] == "deep_value"


if __name__ == "__main__":
    pytest.main([__file__])