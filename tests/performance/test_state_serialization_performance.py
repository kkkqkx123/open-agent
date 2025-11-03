"""状态序列化性能测试

测试增强的状态序列化器的性能改进。
"""

import time
import json
import statistics
from typing import Dict, Any, List
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from src.infrastructure.graph.states import (
    BaseGraphState, WorkflowState,
    StateSerializer, create_optimized_state_manager,
    HumanMessage, AIMessage,
    create_base_state, create_workflow_state
)
from langchain_core.messages import HumanMessage as LCHumanMessage


class TestStateSerializationPerformance:
    """状态序列化性能测试类"""
    
    def setup_method(self) -> None:
        """设置测试方法"""
        # 创建测试数据
        self.test_states = self._create_test_states()
        
        # 创建序列化器
        self.basic_serializer = StateSerializer(max_cache_size=0)  # 禁用缓存
        self.enhanced_serializer = StateSerializer(max_cache_size=1000)  # 启用缓存
        self.optimized_manager = create_optimized_state_manager()
    
    def _create_test_states(self) -> List[Dict[str, Any]]:
        """创建测试状态数据"""
        states = []
        
        # 创建不同大小的状态
        for i in range(5):
            # 基础状态
            base_state = create_base_state(
                messages=[LCHumanMessage(content=f"Test message {j}") for j in range(10 * (i + 1))],
                current_step=f"step_{i}"
            )
            
            # Agent状态
            agent_state = create_workflow_state(
                workflow_id=f"workflow_{i}",
                workflow_name=f"Test Workflow {i}",
                input_text=f"Test input {i}",
                max_iterations=10
            )
            
            # Workflow状态
            workflow_state = create_workflow_state(
                workflow_id=f"workflow_{i}",
                workflow_name=f"Test Workflow {i}",
                input_text=f"Test workflow input {i}",
                max_iterations=5
            )
            
            states.extend([base_state, agent_state, workflow_state])
        
        return states
    
    def test_serialization_performance_comparison(self) -> None:
        """测试序列化性能对比"""
        print("\n=== 序列化性能对比测试 ===")
        
        # 测试基本序列化器
        basic_times = []
        for state in self.test_states:
            start_time = time.time()
            serialized = self.basic_serializer.serialize(state, enable_cache=False)
            end_time = time.time()
            basic_times.append(end_time - start_time)
        
        # 测试增强序列化器（无缓存）
        enhanced_no_cache_times = []
        for state in self.test_states:
            start_time = time.time()
            serialized = self.enhanced_serializer.serialize(state, enable_cache=False)
            end_time = time.time()
            enhanced_no_cache_times.append(end_time - start_time)
        
        # 测试增强序列化器（有缓存）
        enhanced_cache_times_1 = []  # 第一次（缓存未命中）
        for state in self.test_states:
            start_time = time.time()
            serialized = self.enhanced_serializer.serialize(state, enable_cache=True)
            end_time = time.time()
            enhanced_cache_times_1.append(end_time - start_time)
        
        enhanced_cache_times_2 = []  # 第二次（缓存命中）
        for state in self.test_states:
            start_time = time.time()
            serialized = self.enhanced_serializer.serialize(state, enable_cache=True)
            end_time = time.time()
            enhanced_cache_times_2.append(end_time - start_time)
        
        # 计算统计
        basic_avg = statistics.mean(basic_times)
        enhanced_no_cache_avg = statistics.mean(enhanced_no_cache_times)
        enhanced_cache_avg_1 = statistics.mean(enhanced_cache_times_1)
        enhanced_cache_avg_2 = statistics.mean(enhanced_cache_times_2)
        
        print(f"基本序列化器平均时间: {basic_avg:.6f}s")
        print(f"增强序列化器（无缓存）平均时间: {enhanced_no_cache_avg:.6f}s")
        print(f"增强序列化器（缓存未命中）平均时间: {enhanced_cache_avg_1:.6f}s")
        print(f"增强序列化器（缓存命中）平均时间: {enhanced_cache_avg_2:.6f}s")
        
        # 计算性能提升
        if basic_avg > 0:
            improvement_no_cache = (basic_avg - enhanced_no_cache_avg) / basic_avg * 100
            improvement_cache_hit = (basic_avg - enhanced_cache_avg_2) / basic_avg * 100
            
            print(f"无缓存性能提升: {improvement_no_cache:.2f}%")
            print(f"缓存命中性能提升: {improvement_cache_hit:.2f}%")
        
        # 验证正确性
        for state in self.test_states[:3]:  # 测试前3个状态
            basic_result = self.basic_serializer.serialize(state, enable_cache=False)
            enhanced_result = self.enhanced_serializer.serialize(state, enable_cache=False)
            
            # 反序列化后比较
            basic_restored = self.basic_serializer.deserialize(basic_result)
            enhanced_restored = self.enhanced_serializer.deserialize(enhanced_result)
            
            assert basic_restored == enhanced_restored, "序列化结果不一致"
        
        print("✓ 序列化正确性验证通过")
    
    def test_deserialization_performance(self) -> None:
        """测试反序列化性能"""
        print("\n=== 反序列化性能测试 ===")
        
        # 准备序列化数据
        serialized_data = []
        for state in self.test_states:
            serialized = self.basic_serializer.serialize(state, enable_cache=False)
            serialized_data.append(serialized)
        
        # 测试基本反序列化器
        basic_times = []
        for data in serialized_data:
            start_time = time.time()
            deserialized = self.basic_serializer.deserialize(data)
            end_time = time.time()
            basic_times.append(end_time - start_time)
        
        # 测试增强反序列化器
        enhanced_times = []
        for data in serialized_data:
            start_time = time.time()
            deserialized = self.enhanced_serializer.deserialize(data)
            end_time = time.time()
            enhanced_times.append(end_time - start_time)
        
        # 计算统计
        basic_avg = statistics.mean(basic_times)
        enhanced_avg = statistics.mean(enhanced_times)
        
        print(f"基本反序列化器平均时间: {basic_avg:.6f}s")
        print(f"增强反序列化器平均时间: {enhanced_avg:.6f}s")
        
        if basic_avg > 0:
            improvement = (basic_avg - enhanced_avg) / basic_avg * 100
            print(f"反序列化性能提升: {improvement:.2f}%")
    
    def test_diff_serialization_performance(self) -> None:
        """测试差异序列化性能"""
        print("\n=== 差异序列化性能测试 ===")
        
        # 创建状态序列
        state_sequence = []
        base_state = self.test_states[0].copy()
        state_sequence.append(base_state.copy())
        
        # 创建一系列状态更新
        for i in range(10):
            new_state = state_sequence[-1].copy()
            # 添加消息
            if "messages" in new_state:
                new_state["messages"].append(AIMessage(content=f"New message {i}"))
            # 更新其他字段
            new_state["current_step"] = f"step_{i}"
            new_state["iteration_count"] = i
            
            state_sequence.append(new_state)
        
        # 测试完整序列化
        full_serialization_times = []
        full_sizes = []
        for state in state_sequence[1:]:
            start_time = time.time()
            serialized = self.enhanced_serializer.serialize(state, enable_cache=False)
            end_time = time.time()
            full_serialization_times.append(end_time - start_time)
            full_sizes.append(len(serialized) if isinstance(serialized, str) else len(serialized))
        
        # 测试差异序列化
        diff_serialization_times = []
        diff_sizes = []
        for i in range(1, len(state_sequence)):
            old_state = state_sequence[i-1]
            new_state = state_sequence[i]
            
            start_time = time.time()
            diff_serialized = self.enhanced_serializer.serialize_diff(old_state, new_state)
            end_time = time.time()
            diff_serialization_times.append(end_time - start_time)
            diff_sizes.append(len(diff_serialized) if isinstance(diff_serialized, str) else len(diff_serialized))
        
        # 计算统计
        full_avg_time = statistics.mean(full_serialization_times)
        diff_avg_time = statistics.mean(diff_serialization_times)
        full_avg_size = statistics.mean(full_sizes)
        diff_avg_size = statistics.mean(diff_sizes)
        
        print(f"完整序列化平均时间: {full_avg_time:.6f}s")
        print(f"差异序列化平均时间: {diff_avg_time:.6f}s")
        print(f"完整序列化平均大小: {full_avg_size:.0f} bytes")
        print(f"差异序列化平均大小: {diff_avg_size:.0f} bytes")
        
        if full_avg_time > 0:
            time_improvement = (full_avg_time - diff_avg_time) / full_avg_time * 100
            size_improvement = (full_avg_size - diff_avg_size) / full_avg_size * 100
            
            print(f"差异序列化时间提升: {time_improvement:.2f}%")
            print(f"差异序列化大小提升: {size_improvement:.2f}%")
        
        # 验证差异序列化的正确性
        for i in range(1, len(state_sequence)):
            old_state = state_sequence[i-1]
            new_state = state_sequence[i]
            
            # 序列化差异
            diff_serialized = self.enhanced_serializer.serialize_diff(old_state, new_state)
            
            # 应用差异
            restored_state = self.enhanced_serializer.apply_diff(old_state, diff_serialized)
            
            assert restored_state == new_state, f"差异序列化验证失败在第{i}步"
        
        print("✓ 差异序列化正确性验证通过")
    
    def test_optimized_manager_performance(self) -> None:
        """测试优化状态管理器性能"""
        print("\n=== 优化状态管理器性能测试 ===")
        
        # 创建测试状态
        test_state = self.test_states[0].copy()
        state_id = "test_state"
        
        # 测试普通更新
        normal_update_times = []
        current_state = test_state.copy()
        
        for i in range(100):
            updates = {
                "current_step": f"step_{i}",
                "iteration_count": i,
                "messages": current_state.get("messages", []) + [AIMessage(content=f"Message {i}")]
            }
            
            start_time = time.time()
            new_state = current_state.copy()
            new_state.update(updates)
            end_time = time.time()
            
            normal_update_times.append(end_time - start_time)
            current_state = new_state
        
        # 测试优化管理器
        optimized_update_times = []
        manager = create_optimized_state_manager(enable_pooling=True)
        managed_state = manager.create_state(state_id, test_state.copy())
        
        for i in range(100):
            updates = {
                "current_step": f"step_{i}",
                "iteration_count": i,
                "messages": managed_state.get("messages", []) + [AIMessage(content=f"Message {i}")]
            }
            
            start_time = time.time()
            managed_state = manager.update_state(state_id, managed_state, updates)
            end_time = time.time()
            
            optimized_update_times.append(end_time - start_time)
        
        # 计算统计
        normal_avg = statistics.mean(normal_update_times)
        optimized_avg = statistics.mean(optimized_update_times)
        
        print(f"普通更新平均时间: {normal_avg:.6f}s")
        print(f"优化更新平均时间: {optimized_avg:.6f}s")
        
        if normal_avg > 0:
            improvement = (normal_avg - optimized_avg) / normal_avg * 100
            print(f"状态更新性能提升: {improvement:.2f}%")
        
        # 测试内存使用
        memory_stats = manager.get_memory_usage_stats()
        print(f"内存使用统计: {memory_stats}")
        
        performance_stats = manager.get_performance_stats()
        print(f"性能统计: {performance_stats}")
    
    def test_cache_performance(self) -> None:
        """测试缓存性能"""
        print("\n=== 缓存性能测试 ===")
        
        # 测试缓存命中率
        test_state = self.test_states[0]
        
        # 第一次序列化（缓存未命中）
        start_time = time.time()
        result1 = self.enhanced_serializer.serialize(test_state, enable_cache=True)
        time1 = time.time() - start_time
        
        # 第二次序列化（缓存命中）
        start_time = time.time()
        result2 = self.enhanced_serializer.serialize(test_state, enable_cache=True)
        time2 = time.time() - start_time
        
        # 第三次序列化（缓存命中）
        start_time = time.time()
        result3 = self.enhanced_serializer.serialize(test_state, enable_cache=True)
        time3 = time.time() - start_time
        
        print(f"第一次序列化时间（缓存未命中）: {time1:.6f}s")
        print(f"第二次序列化时间（缓存命中）: {time2:.6f}s")
        print(f"第三次序列化时间（缓存命中）: {time3:.6f}s")
        
        # 验证结果一致性
        assert result1 == result2 == result3, "缓存结果不一致"
        print("✓ 缓存一致性验证通过")
        
        # 获取缓存统计
        stats = self.enhanced_serializer.get_performance_stats()
        print(f"缓存统计: {stats['cache_stats']}")
    
    def test_large_state_performance(self) -> None:
        """测试大状态性能"""
        print("\n=== 大状态性能测试 ===")
        
        # 创建大状态
        large_state = create_workflow_state(
            workflow_id="large_workflow",
            workflow_name="Large Test Workflow",
            input_text="Large test input",
            max_iterations=100
        )
        
        # 添加大量消息
        large_state["messages"] = [
            HumanMessage(content=f"Large message {i}") if i % 2 == 0 else AIMessage(content=f"Large message {i}")
            for i in range(1000)
        ]
        
        # 添加大量图状态
        large_state["graph_states"] = {
            f"graph_{i}": create_workflow_state(
                workflow_id=f"workflow_{i}",
                workflow_name=f"Graph Workflow {i}",
                input_text=f"Graph {i} input",
                max_iterations=10
            )
            for i in range(50)
        }
        
        # 测试序列化性能
        start_time = time.time()
        serialized = self.enhanced_serializer.serialize(large_state, enable_cache=True)
        serialization_time = time.time() - start_time
        
        # 测试优化
        start_time = time.time()
        optimized = self.enhanced_serializer.optimize_state_for_storage(large_state)
        optimization_time = time.time() - start_time
        
        # 计算大小减少
        original_size = len(json.dumps(large_state, default=str))
        optimized_size = len(json.dumps(optimized, default=str))
        size_reduction = (original_size - optimized_size) / original_size * 100
        
        print(f"大状态序列化时间: {serialization_time:.6f}s")
        print(f"大状态优化时间: {optimization_time:.6f}s")
        print(f"大状态大小减少: {size_reduction:.2f}%")
        print(f"原始大小: {original_size} bytes")
        print(f"优化后大小: {optimized_size} bytes")


def run_performance_tests() -> None:
    """运行所有性能测试"""
    test = TestStateSerializationPerformance()
    test.setup_method()
    
    print("开始状态序列化性能测试...")
    
    test.test_serialization_performance_comparison()
    test.test_deserialization_performance()
    test.test_diff_serialization_performance()
    test.test_optimized_manager_performance()
    test.test_cache_performance()
    test.test_large_state_performance()
    
    print("\n=== 所有性能测试完成 ===")
    
    # 获取最终统计
    final_stats = test.enhanced_serializer.get_performance_stats()
    print(f"最终性能统计: {final_stats}")


if __name__ == "__main__":
    run_performance_tests()